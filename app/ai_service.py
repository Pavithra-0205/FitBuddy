import json
import logging
from typing import Any
from pydantic import BaseModel
from .config import Settings

logger = logging.getLogger(__name__)


class AIServiceError(RuntimeError):
    pass


class AIService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None
        if settings.gemini_api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=settings.gemini_api_key)
            except ImportError as exc:
                raise AIServiceError("The google-genai package is not installed. Run: pip install -r requirements.txt") from exc

    def _generate_structured(self, model: str, prompt: str, schema: type[BaseModel]) -> BaseModel:
        if not self.client:
            raise AIServiceError("Gemini API key is not configured.")
        try:
            from google.genai import types
            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.6,
                    max_output_tokens=7000,
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
            if getattr(response, "parsed", None) is not None:
                parsed = response.parsed
                return parsed if isinstance(parsed, schema) else schema.model_validate(parsed)
            text = getattr(response, "text", None)
            if not text:
                raise AIServiceError("Gemini returned an empty response.")
            return schema.model_validate_json(text)
        except Exception as exc:
            logger.exception("Gemini generation failed")
            raise AIServiceError(str(exc)) from exc

    def generate_workout(self, user: Any, schema: type[BaseModel]) -> BaseModel:
        prompt = f"""
You are FitBuddy, a careful fitness-planning assistant.
Create a personalized 7-day workout plan for:
Name: {user.name}
Age: {user.age}
Weight: {user.weight} kg
Goal: {user.goal}
Intensity: {user.intensity}
Experience: {user.experience_level}
Training days per week: {user.days_per_week}

Requirements:
- Return exactly 7 days.
- Respect the requested training-day count; use recovery/rest days for the remaining days.
- Training days need warm-up, exercises with sets/reps or duration, and cooldown.
- Include sensible rest intervals and gradual progression.
- Avoid extreme volume and medical claims.
- Do not diagnose injuries or medical conditions.
- Include a brief safety note telling the user to stop for concerning pain or symptoms.
- Follow the JSON schema exactly.
"""
        return self._generate_structured(self.settings.gemini_workout_model, prompt, schema)

    def generate_nutrition(self, user: Any, schema: type[BaseModel]) -> BaseModel:
        prompt = f"""
You are FitBuddy's nutrition and recovery assistant.
Give concise, practical general guidance for:
Goal: {user.goal}
Age: {user.age}
Weight: {user.weight} kg
Intensity: {user.intensity}
Experience: {user.experience_level}

Provide one nutrition tip, one hydration suggestion, and one recovery suggestion.
Avoid medical claims, extreme dieting, and rigid calorie prescriptions. Follow the JSON schema exactly.
"""
        return self._generate_structured(self.settings.gemini_nutrition_model, prompt, schema)

    def update_workout(self, user: Any, original_plan: Any, feedback: str, schema: type[BaseModel]) -> BaseModel:
        original_json = original_plan.model_dump_json(indent=2) if isinstance(original_plan, BaseModel) else json.dumps(original_plan, indent=2)
        prompt = f"""
You are updating a FitBuddy 7-day workout plan.
User: {user.name}, age {user.age}, weight {user.weight} kg, goal {user.goal}, intensity {user.intensity}, experience {user.experience_level}, training days/week {user.days_per_week}.

User feedback:
{feedback}

Original plan:
{original_json}

Revise the plan to address the feedback while preserving the user's goal, intensity, experience level, and exactly 7 days.
Do not blindly follow unsafe requests. Keep exercise guidance general and practical. Do not diagnose or treat medical conditions.
Follow the JSON schema exactly.
"""
        return self._generate_structured(self.settings.gemini_workout_model, prompt, schema)


def demo_workout(user: Any):
    from .schemas import WorkoutDay, WorkoutPlanResponse
    focuses = ["Full Body", "Upper Body", "Lower Body", "Cardio & Core", "Full Body", "Mobility", "Recovery"]
    days = []
    for i in range(7):
        if i < user.days_per_week:
            days.append(WorkoutDay(
                day=f"Day {i + 1}", focus=focuses[i % 6],
                warm_up=["5 minutes easy walking", "Dynamic arm and leg movements"],
                exercises=["Bodyweight squat — 3 × 10", "Incline push-up — 3 × 8–12", "Glute bridge — 3 × 12", "Plank — 3 × 20–30 sec"],
                cooldown=["3–5 minutes easy walking", "Gentle full-body stretching"],
                rest_note="Rest about 60–90 seconds between sets."
            ))
        else:
            days.append(WorkoutDay(day=f"Day {i + 1}", focus="Recovery / Rest", exercises=["Easy walking or comfortable mobility for 10–20 minutes"], rest_note="Prioritize sleep, hydration, and recovery."))
    return WorkoutPlanResponse(
        title="FitBuddy Demo 7-Day Plan",
        overview="Demo plan generated locally because live Gemini generation was unavailable.",
        days=days,
        safety_note="Demo only. Adjust exercises to your ability and stop if you experience concerning pain or symptoms."
    )


def demo_nutrition(user: Any):
    from .schemas import NutritionTipResponse
    return NutritionTipResponse(
        tip=f"For {user.goal}, build balanced meals around protein-rich foods, vegetables or fruit, and suitable whole-food carbohydrates.",
        hydration="Drink water regularly and increase fluids around exercise, especially in hot weather.",
        recovery="Aim for consistent sleep and include easier days so your body can recover."
    )
