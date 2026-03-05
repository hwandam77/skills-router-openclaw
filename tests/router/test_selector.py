from src.router.selector import select_for_task, select_top_k


def test_select_top_k():
    ranked = [{"skill_id": "a", "score": 0.9}, {"skill_id": "b", "score": 0.8}]
    out = select_top_k(ranked, 1)
    assert len(out) == 1
    assert out[0]["skill_id"] == "a"


def test_select_for_task_composite():
    ranked = [
        {"skill_id": "a", "score": 0.9},
        {"skill_id": "b", "score": 0.8},
        {"skill_id": "c", "score": 0.7},
        {"skill_id": "d", "score": 0.6},
    ]
    out = select_for_task(ranked, "composite")
    assert [x["skill_id"] for x in out] == ["a", "b", "c"]
