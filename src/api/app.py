from __future__ import annotations

import json
from uuid import uuid4
from pathlib import Path
from fastapi import FastAPI, HTTPException

from src.config import REGISTRY_PATH, SKILLS_ROOT, RUN_DB_PATH
from src.registry.inventory import write_inventory
from src.registry.enricher import enrich_skills
from src.router.filter_engine import RouterContext as FilterContext, filter_candidates
from src.router.selector import select_for_task
from src.router.scoring_engine import rank_skills
from src.router.vector_adapter import get_default_backend, compute_vector_scores
from src.router.intent_match import compute_intent_match
from src.policy.policy_engine import PolicyContext, enforce_policy
from src.router.types import RouterContext, PlanResponse, ExecuteResponse, RunStatus
from src.storage.run_store import RunStore

app = FastAPI(title='Skill Router v1 API', version='0.2.0')
store = RunStore(RUN_DB_PATH)
SKILLS: list[dict] = []
_vector_backend = None  # initialized at startup


def _reload_registry() -> int:
    global SKILLS
    if not REGISTRY_PATH.exists():
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        inv_tmp = REGISTRY_PATH.parent / 'skill_inventory.json'
        write_inventory(SKILLS_ROOT, inv_tmp)
        SKILLS = enrich_skills(json.loads(inv_tmp.read_text(encoding='utf-8')))
        REGISTRY_PATH.write_text(json.dumps(SKILLS, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    else:
        SKILLS = json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))
    return len(SKILLS)


@app.on_event('startup')
def on_startup():
    global _vector_backend
    _reload_registry()
    _vector_backend = get_default_backend()


@app.get('/router/health')
def router_health():
    return {'ok': True, 'service': 'skill-router-v1', 'skills': len(SKILLS), 'registry': str(REGISTRY_PATH)}


@app.post('/router/reload')
def router_reload():
    count = _reload_registry()
    return {'ok': True, 'skills': count}


@app.post('/router/plan', response_model=PlanResponse)
def router_plan(ctx: RouterContext):
    run_id = str(uuid4())

    filtered, rejected = filter_candidates(
        SKILLS,
        FilterContext(
            available_tools=ctx.available_tools,
            approval_token=ctx.approval_token,
        ),
    )

    allowed, policy_blocked = enforce_policy(filtered, PolicyContext(approval_token=ctx.approval_token))
    rejected = rejected + policy_blocked

    docs = {s['skill_id']: f"{s['skill_id']} {' '.join(s.get('intents', []))} {s.get('domain','')}" for s in allowed}
    vec = compute_vector_scores(ctx.user_intent, docs, backend=_vector_backend)

    feature_map = {
        s['skill_id']: {
            'intent_match': compute_intent_match(ctx.user_intent, s),
            'vector_similarity': vec.get(s['skill_id'], 0.0),
            'quality_score': s.get('quality_score', 0.5),
            'policy_fit': 1.0,
            'latency_fit': 1.0,
            'cost_fit': 1.0,
        }
        for s in allowed
    }
    ranked = rank_skills(allowed, feature_map, has_approval=bool(ctx.approval_token))

    # anti-bias: avoid always selecting same head skill when scores are near-tied
    if len(ranked) > 1 and abs(ranked[0]['score'] - ranked[1]['score']) < 0.02:
        ranked[0], ranked[1] = ranked[1], ranked[0]

    selected = select_for_task(ranked, ctx.task_type)

    status = RunStatus(
        run_id=run_id,
        status='accepted',
        selected_skills=[s['skill_id'] for s in selected],
        rejected=rejected,
    )
    store.upsert(run_id, status.status, status.selected_skills, status.rejected)

    return PlanResponse(
        run_id=run_id,
        selected_skills=status.selected_skills,
        shortlisted_skills=[r['skill_id'] for r in ranked],
        rejected=rejected,
    )


@app.post('/router/execute', response_model=ExecuteResponse)
def router_execute(ctx: RouterContext):
    plan = router_plan(ctx)
    status = 'done' if plan.selected_skills else 'failed'
    prev = store.get(plan.run_id) or {'selected_skills': [], 'rejected': []}
    store.upsert(plan.run_id, status, prev.get('selected_skills', []), prev.get('rejected', []))
    return ExecuteResponse(run_id=plan.run_id, status=status)


@app.get('/router/runs/{run_id}', response_model=RunStatus)
def router_run_status(run_id: str):
    run = store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail='run not found')
    return RunStatus(**run)
