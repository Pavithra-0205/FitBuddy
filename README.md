# FitBuddy — AI Fitness Plan Generator

FitBuddy is a FastAPI + Jinja2 + SQLite web application that uses Google's Gemini API to generate personalized 7-day workout plans, nutrition/recovery tips, and feedback-based plan revisions.

## Features
- Personalized 7-day workout plan generation
- User profile: name, user ID, age, weight, goal, intensity, experience, days/week
- Gemini-powered nutrition/recovery tip
- Feedback loop that revises the original plan
- SQLite persistence through SQLAlchemy
- Admin dashboard at `/view-all-users`
- JSON API endpoints
- Responsive frontend
- Health endpoint and automated tests
- Optional local AI fallback for UI testing without an API key

## Architecture

```text
Browser -> FastAPI -> Jinja2 templates
                 -> AI service (Google GenAI SDK)
                 -> SQLAlchemy -> SQLite
```

## Documentation alignment

The supplied project document describes Gemini 1.5 Pro + Gemini Flash and the older `google-generativeai` package. This implementation keeps the same functional architecture but uses Google's current `google-genai` SDK and configurable model names. The defaults are in `.env.example`, so you can change models without editing Python code.

The website does **not** generate its own images with AI. Put your own fitness image at `static/images/fitness-bg.jpg`; the UI falls back to a gradient if it is absent.

## Windows / VS Code setup

### 1. Create and activate a virtual environment

PowerShell:
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Command Prompt:
```bat
py -3 -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Gemini
Copy `.env.example` to `.env` and set:
```env
GEMINI_API_KEY=YOUR_REAL_KEY
```

### 4. Run
```bash
uvicorn app.main:app --reload
```

Open:
- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc
- http://127.0.0.1:8000/view-all-users
- http://127.0.0.1:8000/health

### 5. Test
```bash
pytest -q
```

The tests use a temporary SQLite database and mock/fallback AI behavior, so a Gemini API key is not required for the test suite.

## Browser test checklist
1. Open the homepage.
2. Fill in name, user ID, age, weight, goal, intensity, experience, and days/week.
3. Click **Generate My Plan**.
4. Confirm the 7-day plan and nutrition/recovery card appear.
5. Submit feedback such as `Add more cardio and one extra recovery day.`
6. Confirm the revised plan appears.
7. Open `/view-all-users` and verify the stored original and updated plans.

## API test
Use `/docs` to test:
- `GET /api/health`
- `POST /api/generate-workout`
- `POST /api/submit-feedback`
- `GET /api/users`

Example request:
```json
{
  "name": "Alex",
  "user_id": "FB1001",
  "age": 20,
  "weight": 65,
  "goal": "muscle gain",
  "intensity": "medium",
  "experience_level": "beginner",
  "days_per_week": 4
}
```

## Your own images
Put images in `static/images/`. Recommended:
- `fitness-bg.jpg` — main page background
- `logo.png` — optional future logo
- `hero.jpg` — optional future hero image

## Safety
FitBuddy provides general educational fitness guidance. It is not a medical service. Users should adapt exercise to their abilities and seek professional advice where appropriate.


## Supplied FitBuddy image

The provided `fit.jpeg` image is already integrated into `static/images/fit.jpeg`. It appears in the navigation branding and the home-page hero section. No AI image generation is required.
