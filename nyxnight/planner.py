"""Deterministic, network-free NyxNight itinerary planner."""

from __future__ import annotations

from datetime import time
from urllib.parse import urlencode

from pydantic import HttpUrl

from nyxnight.models import (
    PlanRequest,
    PlanResponse,
    Stop,
    StopAction,
    clock_minutes,
    window_minutes,
)


def _clock(total: int) -> str:
    total %= 24 * 60
    return f"{total // 60:02d}:{total % 60:02d}"


def _costs(budget: float) -> list[float]:
    target = min(max(budget, 0.0) * 0.9, 135.0)
    first = round(target * 0.46, 2)
    second = round(target * 0.36, 2)
    third = round(max(target - first - second, 0.0), 2)
    return [first, second, third]


def _display_city(value: str) -> str:
    if value.islower() or value.isupper():
        return value.title()
    return value


def _search_url(query: str) -> HttpUrl:
    return HttpUrl(f"https://www.google.com/search?{urlencode({'q': query})}")


def _maps_url(query: str) -> HttpUrl:
    return HttpUrl(f"https://www.google.com/maps/search/?{urlencode({'api': 1, 'query': query})}")


def _feature_for(vibe: str) -> tuple[str, str, str]:
    normalized = vibe.casefold()
    profiles = (
        (("jazz",), "Live-Jazz Feature", "live jazz", "Find live jazz"),
        (("comedy",), "Comedy Feature", "live comedy", "Find comedy"),
        (("theater", "theatre", "stage"), "Stage Feature", "live theater", "Find a show"),
        (("dance", "dancing", "club"), "Dance Feature", "dancing", "Find a dance floor"),
        (("gallery", "museum", "art"), "Gallery Feature", "evening art", "Find evening art"),
        (
            ("film", "cinema", "movie"),
            "Late-Screen Feature",
            "independent cinema",
            "Find a screening",
        ),
        (("music", "concert", "band"), "Live-Music Feature", "live music", "Find live music"),
    )
    for keywords, title, search_phrase, action_label in profiles:
        if any(keyword in normalized for keyword in keywords):
            return title, search_phrase, action_label
    return "After-Dark Feature", vibe, "Find the main event"


def create_plan(request: PlanRequest) -> PlanResponse:
    city = _display_city(request.city)
    feature_title, feature_query, feature_action = _feature_for(request.vibe)
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
            name=f"Opening Table — {city}",
            category="Dinner",
            start_time=_clock(first_start),
            end_time=_clock(first_end),
            estimated_cost_per_person=costs[0],
            reason=(
                f"Start with dinner near the {feature_query} so the route stays compact "
                f"and the {request.vibe} mood begins immediately."
            ),
            verification_note=(
                "Search results are current handoffs, not reservations; verify hours, "
                "distance, price, and availability."
            ),
            action=StopAction(
                label="Find a table",
                url=_maps_url(f"dinner near {feature_query} {city}"),
            ),
        ),
        Stop(
            name=f"{feature_title} — {city}",
            category="Experience",
            start_time=_clock(second_start),
            end_time=_clock(second_end),
            estimated_cost_per_person=costs[1],
            reason=(
                f"Give the longest block to {feature_query}; this search includes "
                "your city and date instead of inventing an event."
            ),
            verification_note=(
                "Search results can change; verify the event date, accessibility, venue, "
                "and ticket terms before booking."
            ),
            action=StopAction(
                label=feature_action,
                url=_search_url(f"{feature_query} {city} {request.date.isoformat()} tickets"),
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
            action=StopAction(
                label="Find a closing stop",
                url=_maps_url(f"dessert or late-night drinks {city}"),
            ),
        ),
    ]
    total = round(sum(stop.estimated_cost_per_person for stop in stops), 2)
    return PlanResponse(
        title=f"NyxNight in {city}",
        summary=(
            f"A {duration}-minute, three-stop {request.vibe} route for "
            f"{request.party_size}, with live search handoffs for real places."
        ),
        city=city,
        date=request.date,
        estimated_total_per_person=total,
        stops=stops,
        transit_notes=[
            "Twelve minutes are reserved between each stop.",
            "Keep the selected dinner and feature in the same neighborhood when possible.",
        ],
        caveats=[
            "Route shaping is local; search links contact Google only when you open them.",
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
