import tomllib
from datetime import date, time
from pathlib import Path

import pytest
from pydantic import ValidationError

import nyxnight
from nyxnight.models import PlanRequest
from nyxnight.planner import create_plan


def request(**changes: object) -> PlanRequest:
    values: dict[str, object] = {
        "city": "Chicago",
        "date": date(2027, 10, 17),
        "party_size": 2,
        "budget_per_person": 120,
        "vibe": "warm live-jazz",
        "start_time": time(18, 0),
        "end_time": time(23, 30),
    }
    values.update(changes)
    return PlanRequest.model_validate(values)


def test_deterministic_budget_and_exact_bounds() -> None:
    plan_request = request()
    first = create_plan(plan_request)
    second = create_plan(plan_request)
    assert first == second
    assert first.stops[0].start_time == "18:00"
    assert first.stops[-1].end_time == "23:30"
    assert first.estimated_total_per_person <= 120
    assert round(sum(stop.estimated_cost_per_person for stop in first.stops), 2) == (
        first.estimated_total_per_person
    )
    assert all("verify" in stop.verification_note.casefold() for stop in first.stops)


def test_zero_budget_and_overnight_window() -> None:
    plan = create_plan(
        request(
            budget_per_person=0,
            start_time=time(22, 0),
            end_time=time(1, 0),
        )
    )
    assert plan.estimated_total_per_person == 0
    assert plan.stops[0].start_time == "22:00"
    assert plan.stops[-1].end_time == "01:00"


def test_short_window_rejected() -> None:
    with pytest.raises(ValidationError):
        request(start_time=time(18, 0), end_time=time(19, 0))


def test_generated_application_has_no_adk_runtime_dependency() -> None:
    package_root = Path(nyxnight.__file__).resolve().parent
    assert all("google.adk" not in path.read_text() for path in package_root.rglob("*.py"))
    project = tomllib.loads((package_root.parent / "pyproject.toml").read_text())
    dependencies = project["project"]["dependencies"]
    assert not any("adk" in dependency.casefold() for dependency in dependencies)
