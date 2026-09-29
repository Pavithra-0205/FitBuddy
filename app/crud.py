from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import User, WorkoutPlan


def get_user(db: Session, user_id: str) -> User | None:
    return db.scalar(select(User).where(User.user_id == user_id))


def save_or_update_user(db: Session, data) -> User:
    user = get_user(db, data.user_id)
    if user is None:
        user = User(user_id=data.user_id)
    user.name = data.name
    user.age = data.age
    user.weight = data.weight
    user.goal = data.goal
    user.intensity = data.intensity
    user.experience_level = data.experience_level
    user.days_per_week = data.days_per_week
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def save_plan(db: Session, user_id: str, original_plan: str, nutrition_tip: str) -> WorkoutPlan:
    plan = WorkoutPlan(user_id=user_id, original_plan=original_plan, nutrition_tip=nutrition_tip)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get_latest_plan(db: Session, user_id: str) -> WorkoutPlan | None:
    return db.scalar(select(WorkoutPlan).where(WorkoutPlan.user_id == user_id).order_by(WorkoutPlan.created_at.desc()))


def update_plan(db: Session, user_id: str, updated_plan: str, feedback: str) -> WorkoutPlan | None:
    plan = get_latest_plan(db, user_id)
    if plan is None:
        return None
    plan.updated_plan = updated_plan
    plan.feedback = feedback
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get_all_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc())).all())


def get_all_plans(db: Session) -> list[WorkoutPlan]:
    return list(db.scalars(select(WorkoutPlan).order_by(WorkoutPlan.created_at.desc())).all())
