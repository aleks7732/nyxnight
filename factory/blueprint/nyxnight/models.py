"""Validated NyxNight request and response models."""

from __future__ import annotations

from datetime import date, time

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


def clock_minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def window_minutes(start: time, end: time) -> int:
    start_value = clock_minutes(start)
    end_value = clock_minutes(end)
    if end_value <= start_value:
        end_value += 24 * 60
    return end_value - start_value


class PlanRequest(BaseModel):
    city: str = Field(min_length=1, max_length=100)
    date: date
    party_size: int = Field(ge=1, le=20)
    budget_per_person: float = Field(ge=0, le=10_000)
    vibe: str = Field(min_length=1, max_length=160)
    start_time: time = time(18, 0)
    end_time: time = time(23, 30)

    @field_validator("city", "vibe")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must contain non-whitespace text")
        return cleaned

    @model_validator(mode="after")
    def validate_window(self) -> PlanRequest:
        duration = window_minutes(self.start_time, self.end_time)
        if duration < 90 or duration > 720:
            raise ValueError("time window must be between 90 minutes and 12 hours")
        return self


class StopAction(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    url: HttpUrl


class Stop(BaseModel):
    name: str
    category: str
    start_time: str
    end_time: str
    estimated_cost_per_person: float = Field(ge=0)
    reason: str
    verification_note: str
    action: StopAction


class PlanResponse(BaseModel):
    title: str
    summary: str
    city: str
    date: date
    mode: str = "demo"
    estimated_total_per_person: float = Field(ge=0)
    stops: list[Stop] = Field(min_length=3, max_length=3)
    transit_notes: list[str]
    caveats: list[str]
