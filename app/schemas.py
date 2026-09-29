from typing import Literal
from pydantic import BaseModel, Field, field_validator

Goal = Literal["weight loss", "muscle gain", "general wellness", "flexibility"]
Intensity = Literal["low", "medium", "high"]
ExperienceLevel = Literal["beginner", "intermediate", "advanced"]


class UserInput(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    user_id: str = Field(min_length=2, max_length=50)
    age: int = Field(ge=13, le=100)
    weight: float = Field(gt=20, le=300)
    goal: Goal
    intensity: Intensity
    experience_level: ExperienceLevel = "beginner"
    days_per_week: int = Field(default=3, ge=1, le=7)

    @field_validator("name", "user_id")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty.")
        return value


class FeedbackRequest(BaseModel):
    user_id: str = Field(min_length=2, max_length=50)
    feedback: str = Field(min_length=3, max_length=2000)


class WorkoutDay(BaseModel):
    day: str
    focus: str
    warm_up: list[str] = Field(default_factory=list)
    exercises: list[str] = Field(default_factory=list)
    cooldown: list[str] = Field(default_factory=list)
    rest_note: str = ""


class WorkoutPlanResponse(BaseModel):
    title: str
    overview: str
    days: list[WorkoutDay] = Field(min_length=7, max_length=7)
    safety_note: str


class NutritionTipResponse(BaseModel):
    tip: str
    hydration: str
    recovery: str


class GenerationResponse(BaseModel):
    user: UserInput
    plan: WorkoutPlanResponse
    nutrition: NutritionTipResponse
    message: str


class FeedbackResponse(BaseModel):
    user_id: str
    updated_plan: WorkoutPlanResponse
    message: str
