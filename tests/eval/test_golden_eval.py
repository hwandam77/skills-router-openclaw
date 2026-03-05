from pathlib import Path
from src.eval.golden_runner import GoldenCase, evaluate_precision, write_golden_report
from src.eval.weekly_tuning import build_weekly_tuning_report


def test_golden_precision_and_report(tmp_path: Path):
    cases = [
        GoldenCase("t1", "a", "a"),
        GoldenCase("t2", "b", "x"),
    ]
    p = evaluate_precision(cases)
    assert p == 0.5
    out = tmp_path / "golden.md"
    write_golden_report(out, cases)
    assert out.exists()


def test_weekly_tuning_report(tmp_path: Path):
    out = tmp_path / "weekly.md"
    build_weekly_tuning_report(out, {"fail_rate": 0.25, "retry_rate": 0.1, "p95_latency_ms": 900})
    assert out.exists()
