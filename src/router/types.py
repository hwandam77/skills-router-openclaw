from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal['user', 'assistant']
    content: str


class BudgetConstraints(BaseModel):
    max_steps: Optional[int] = Field(default=10, ge=1)
    max_time_ms: Optional[int] = Field(default=30000, ge=100)
    latency_class: Optional[Literal['fast', 'normal', 'slow']] = 'normal'
    cost_class: Optional[Literal['low', 'normal', 'high']] = 'normal'


class RouterContext(BaseModel):
    user_intent: str
    conversation_history: List[Message] = []
    available_tools: List[str] = []
    budget_constraints: Optional[BudgetConstraints] = None
    approval_token: Optional[str] = None
    mode: Literal['normal', 'shadow'] = 'normal'
    task_type: Literal['simple', 'composite'] = 'simple'


class PlanResponse(BaseModel):
    run_id: str
    selected_skills: List[str]
    shortlisted_skills: List[str]
    rejected: List[dict]


class ExecuteResponse(BaseModel):
    run_id: str
    status: Literal['accepted', 'running', 'done', 'failed']


class RunStatus(BaseModel):
    run_id: str
    status: Literal['accepted', 'running', 'done', 'failed']
    selected_skills: List[str] = []
    rejected: List[dict] = []
