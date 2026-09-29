from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .ai_service import AIServiceError, demo_nutrition, demo_workout
from .config import get_settings
from .crud import get_all_plans, get_all_users, get_latest_plan, get_user, save_or_update_user, save_plan, update_plan
from .database import get_db
from .schemas import FeedbackRequest, FeedbackResponse, GenerationResponse, NutritionTipResponse, UserInput, WorkoutPlanResponse

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _ai_service():
    from .ai_service import AIService
    return AIService(get_settings())


def _context(user, plan, nutrition, message):
    return {"user": user, "plan": plan, "nutrition": nutrition, "message": message}


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"app_name": get_settings().app_name})


@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout_form(request: Request, name: str = Form(...), user_id: str = Form(...), age: int = Form(...), weight: float = Form(...), goal: str = Form(...), intensity: str = Form(...), experience_level: str = Form("beginner"), days_per_week: int = Form(3), db: Session = Depends(get_db)):
    try:
        user = UserInput(name=name, user_id=user_id, age=age, weight=weight, goal=goal, intensity=intensity, experience_level=experience_level, days_per_week=days_per_week)
    except Exception as exc:
        return templates.TemplateResponse(request=request, name="index.html", context={"app_name": get_settings().app_name, "error": str(exc)}, status_code=422)
    service = _ai_service()
    try:
        plan = service.generate_workout(user, WorkoutPlanResponse)
        nutrition = service.generate_nutrition(user, NutritionTipResponse)
        message = "Your personalized AI plan is ready."
    except AIServiceError as exc:
        if not get_settings().allow_ai_fallback:
            return templates.TemplateResponse(request=request, name="index.html", context={"app_name": get_settings().app_name, "error": f"Gemini error: {exc}"}, status_code=503)
        plan, nutrition = demo_workout(user), demo_nutrition(user)
        message = "Demo mode: live Gemini generation was unavailable, so a local sample plan was shown."
    save_or_update_user(db, user)
    save_plan(db, user.user_id, plan.model_dump_json(indent=2), nutrition.model_dump_json(indent=2))
    return templates.TemplateResponse(request=request, name="result.html", context=_context(user, plan, nutrition, message))


@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback_form(request: Request, user_id: str = Form(...), feedback: str = Form(...), db: Session = Depends(get_db)):
    payload = FeedbackRequest(user_id=user_id, feedback=feedback)
    db_user, latest = get_user(db, payload.user_id), get_latest_plan(db, payload.user_id)
    if not db_user or not latest:
        raise HTTPException(status_code=404, detail="User or workout plan not found.")
    user = UserInput(name=db_user.name, user_id=db_user.user_id, age=db_user.age, weight=db_user.weight, goal=db_user.goal, intensity=db_user.intensity, experience_level=db_user.experience_level, days_per_week=db_user.days_per_week)
    original = WorkoutPlanResponse.model_validate_json(latest.updated_plan or latest.original_plan)
    service = _ai_service()
    try:
        updated = service.update_workout(user, original, payload.feedback, WorkoutPlanResponse)
        message = "Your plan has been updated based on your feedback."
    except AIServiceError as exc:
        if not get_settings().allow_ai_fallback:
            raise HTTPException(status_code=503, detail=f"Gemini error: {exc}") from exc
        updated = demo_workout(user)
        message = "Demo mode: live Gemini update was unavailable, so a local sample revision was shown."
    update_plan(db, user.user_id, updated.model_dump_json(indent=2), payload.feedback)
    nutrition = NutritionTipResponse.model_validate_json(latest.nutrition_tip)
    return templates.TemplateResponse(request=request, name="result.html", context=_context(user, updated, nutrition, message))


@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request, db: Session = Depends(get_db)):
    users, plans = get_all_users(db), get_all_plans(db)
    plans_by_user = {}
    for plan in plans:
        plans_by_user.setdefault(plan.user_id, plan)
    return templates.TemplateResponse(request=request, name="all_users.html", context={"users": users, "plans_by_user": plans_by_user, "app_name": get_settings().app_name})


@router.get("/health")
@router.get("/api/health")
def health():
    settings = get_settings()
    return {"status": "ok", "app": settings.app_name, "gemini_configured": bool(settings.gemini_api_key)}


@router.post("/api/generate-workout", response_model=GenerationResponse)
def api_generate_workout(user: UserInput, db: Session = Depends(get_db)):
    service = _ai_service()
    try:
        plan = service.generate_workout(user, WorkoutPlanResponse)
        nutrition = service.generate_nutrition(user, NutritionTipResponse)
        message = "AI plan generated successfully."
    except AIServiceError as exc:
        if not get_settings().allow_ai_fallback:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        plan, nutrition = demo_workout(user), demo_nutrition(user)
        message = "Demo fallback plan returned because Gemini was unavailable."
    save_or_update_user(db, user)
    save_plan(db, user.user_id, plan.model_dump_json(indent=2), nutrition.model_dump_json(indent=2))
    return GenerationResponse(user=user, plan=plan, nutrition=nutrition, message=message)


@router.post("/api/submit-feedback", response_model=FeedbackResponse)
def api_submit_feedback(payload: FeedbackRequest, db: Session = Depends(get_db)):
    db_user, latest = get_user(db, payload.user_id), get_latest_plan(db, payload.user_id)
    if not db_user or not latest:
        raise HTTPException(status_code=404, detail="User or workout plan not found.")
    user = UserInput(name=db_user.name, user_id=db_user.user_id, age=db_user.age, weight=db_user.weight, goal=db_user.goal, intensity=db_user.intensity, experience_level=db_user.experience_level, days_per_week=db_user.days_per_week)
    original = WorkoutPlanResponse.model_validate_json(latest.updated_plan or latest.original_plan)
    service = _ai_service()
    try:
        updated = service.update_workout(user, original, payload.feedback, WorkoutPlanResponse)
        message = "Plan updated successfully."
    except AIServiceError as exc:
        if not get_settings().allow_ai_fallback:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        updated = demo_workout(user)
        message = "Demo fallback update returned because Gemini was unavailable."
    update_plan(db, user.user_id, updated.model_dump_json(indent=2), payload.feedback)
    return FeedbackResponse(user_id=user.user_id, updated_plan=updated, message=message)


@router.get("/api/users")
def api_users(db: Session = Depends(get_db)):
    users, plans = get_all_users(db), get_all_plans(db)
    plans_by_user = {}
    for plan in plans:
        plans_by_user.setdefault(plan.user_id, plan)
    return {"users": [{"user_id": u.user_id, "name": u.name, "age": u.age, "weight": u.weight, "goal": u.goal, "intensity": u.intensity, "experience_level": u.experience_level, "days_per_week": u.days_per_week, "created_at": u.created_at.isoformat(), "has_updated_plan": bool(plans_by_user.get(u.user_id) and plans_by_user[u.user_id].updated_plan)} for u in users]}
