from __future__ import annotations

import json

from agent.report_generator import ReportGenerator
from tests.helpers import build_sample_report


def test_report_generator_writes_all_outputs(tmp_path) -> None:
    report = build_sample_report()
    generated = ReportGenerator(tmp_path).generate(report)

    assert generated["json"].exists()
    assert generated["markdown"].exists()
    assert generated["summary"].exists()

    payload = json.loads(generated["json"].read_text(encoding="utf-8"))
    assert payload["snapshot"]["repository"]["name"] == "ToDoList"
    assert payload["health_score"]["score"] == 76
