"""Deterministic, network-free NyxNight itinerary planner."""

from __future__ import annotations

from datetime import time

from nyxnight.models import PlanRequest, PlanResponse, Stop, clock_minutes, window_minutes


def _clock(total: int) -> str:
    total %= 24 * 60
    return f"{total // 60:02d}:{total % 60:02d}"


def _costs(budget: float) -> list[float]:
    target = min(max(budget, 0.0) * 0.9, 135.0)
    first = round(target * 0.46, 2)
    second = round(target * 0.36, 2)
    third = round(max(target - first - second, 0.0), 2)
    return [first, second, third]


def create_plan(request: PlanRequest) -> PlanResponse:
    duration = window_minutes(request.start_time, request.end_time)
    start = clock_minutes(request.start_time)
    transit = 12
    active = duration - 2 * transit
    first_duration = active * 38 // 100
    second_duration = active * 39 // 100
    third_duration = active - first_duration - second_duration

    first_start = start
    first_end = first_start + first_duration
    second_start = first_end + transit
    second_end = second_start + second_duration
    third_start = second_end + transit
    third_end = third_start + third_duration
    costs = _costs(request.budget_per_person)

    stops = [
        Stop(
            name=f"Crail Table — {request.city}",
            category="Dinner",
            start_time=_clock(first_start),
            end_time=_clock(first_end),
            estimated_cost_per_person=costs[0],
            reason=f"A grounded opening meal tuned for a {request.vibe} night.",
            verification_note="Illustrative venue concept; verify hours and availability directly.",
        ),
        Stop(
            name="After-Dark Feature",
            category="Experience",
            start_time=_clock(second_start),
            end_time=_clock(second_end),
            estimated_cost_per_person=costs[1],
            reason="The longest block carries the night's main shared experience.",
            verification_note=(
                "Verify the real event, accessibility, and ticket terms before booking."
            ),
        ),
        Stop(
            name="Midnight Ember",
            category="Dessert / nightcap",
            start_time=_clock(third_start),
            end_time=_clock(third_end),
            estimated_cost_per_person=costs[2],
            reason="A low-pressure final stop closes the route without rushing.",
            verification_note="Verify closing time and dietary options directly.",
        ),
    ]
    total = round(sum(stop.estimated_cost_per_person for stop in stops), 2)
    return PlanResponse(
        title=f"NyxNight in {request.city}",
        summary=(
            f"A deterministic {duration}-minute, three-stop {request.vibe} plan "
            f"for {request.party_size}."
        ),
        city=request.city,
        date=request.date,
        estimated_total_per_person=total,
        stops=stops,
        transit_notes=[
            "Twelve minutes are reserved between each stop.",
            "Keep the route geographically compact when replacing concepts with real venues.",
        ],
        caveats=[
            "Demo mode uses illustrative venue concepts and performs no network lookup.",
            "Verify hours, prices, accessibility, and reservations before leaving.",
        ],
    )


def sample_request() -> PlanRequest:
    from datetime import date

    return PlanRequest(
        city="Chicago",
        date=date.today(),
        party_size=2,
        budget_per_person=120,
        vibe="warm live-jazz",
        start_time=time(18, 0),
        end_time=time(23, 30),
    )
