# AGENTS.md - CareCompass

Guidelines for AI coding agents working in this repository.

## Project Overview

CareCompass is a holistic health companion web application featuring:
- **MediChat**: Gemini AI-powered medical assistant chatbot
- **Healthcare Finder**: Real-time geolocation-based hospital/pharmacy/clinic finder
- **Meal Planner**: Recipe search with diet filters and calorie tracking

**Stack**: Python 3.10+, FastAPI, HTMX, Alpine.js, Pico CSS, Vercel

---

## Build/Run Commands

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Locally (Development)
```bash
cd /home/nino/repos/CareCompass
uvicorn api.index:app --reload --port 8000
```

### Deploy to Vercel
```bash
vercel deploy
```

---

## Testing

**No test framework is currently configured.**

If adding tests, use pytest:
```bash
# Install pytest
pip install pytest pytest-cov pytest-asyncio

# Run all tests
pytest

# Run single test file
pytest tests/test_services.py

# Run single test function
pytest tests/test_services.py::test_gemini_chat

# Run with coverage
pytest --cov=api --cov-report=term-missing
```

---

## Linting/Formatting

```bash
# Install tools
pip install ruff black isort

# Format code
black api/
isort api/

# Lint code
ruff check api/

# Fix auto-fixable issues
ruff check api/ --fix
```

---

## Project Structure

```
CareCompass/
├── api/
│   ├── index.py              # FastAPI app + routes
│   └── services/
│       ├── __init__.py
│       ├── gemini.py         # Gemini AI chat service
│       ├── overpass.py       # OpenStreetMap healthcare finder
│       └── spoonacular.py    # Recipe/meal planning API
├── templates/
│   ├── base.html             # Layout (Pico CSS, HTMX, Alpine.js)
│   ├── index.html            # Landing page
│   ├── chat.html             # MediChat page
│   ├── nearby.html           # Healthcare finder page
│   ├── meals.html            # Meal planner page
│   └── partials/
│       ├── chat_messages.html
│       ├── places_list.html
│       ├── recipe_cards.html
│       ├── meal_plan.html
│       └── calorie_tracker.html
├── static/
│   └── css/
│       └── custom.css
├── requirements.txt
├── vercel.json
├── .env.example
└── AGENTS.md
```

---

## Code Style Guidelines

### Import Order
Follow PEP 8 import ordering:
```python
# 1. Standard library
import os
from pathlib import Path

# 2. Third-party packages
from fastapi import FastAPI, Request
import httpx

# 3. Local modules
from services import gemini, overpass
```

### Naming Conventions
| Element | Convention | Example |
|---------|------------|---------|
| Functions | snake_case | `find_nearby_healthcare()` |
| Variables | snake_case | `user_input`, `recipe_details` |
| Constants | UPPER_SNAKE | `OVERPASS_URL`, `DIET_TYPES` |
| Module files | snake_case | `spoonacular.py` |
| Route handlers | descriptive | `search_recipes()`, `send_message()` |

### Type Hints
All functions must have type hints:
```python
async def search_recipes(
    query: str = "",
    diet: Optional[str] = None,
    max_results: int = 6,
) -> list[dict]:
    ...
```

### Docstrings
Use Google-style docstrings:
```python
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the distance between two points on Earth.

    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point

    Returns:
        Distance in kilometers
    """
```

### Error Handling
- Use specific exception types
- Return graceful fallbacks for API failures
- Log errors for debugging

```python
try:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()
except httpx.TimeoutException:
    print("API timeout")
    return []
except httpx.HTTPStatusError as e:
    print(f"HTTP error: {e.response.status_code}")
    return []
```

### HTMX Patterns
- Return HTML fragments from API endpoints, not JSON
- Use `hx-target` to specify where content goes
- Use `hx-swap="innerHTML"` for replacing content

```python
@app.post("/api/chat", response_class=HTMLResponse)
async def send_message(request: Request, message: str = Form(...)):
    # Process message...
    return templates.TemplateResponse("partials/chat_messages.html", {...})
```

---

## Environment Variables

Required in `.env` file (see `.env.example`):
```
GEMINI_API_KEY=your_gemini_api_key
SPOONACULAR_API_KEY=your_spoonacular_api_key
SESSION_SECRET=random_secret_for_cookies
```

For Vercel deployment, set these in the Vercel dashboard under Environment Variables.

---

## External APIs

| API | Purpose | Free Tier |
|-----|---------|-----------|
| Google Gemini | Medical chatbot | 1M tokens/day |
| Overpass API | Healthcare locations | Unlimited (rate-limited) |
| Spoonacular | Recipes & nutrition | 150 points/day |

---

## Adding New Features

### New Page
1. Create route in `api/index.py`
2. Create template in `templates/`
3. Add link to `templates/base.html` nav

### New API Service
1. Create `api/services/new_service.py`
2. Import in `api/index.py`
3. Create route handlers

### New Partial Template
1. Create in `templates/partials/`
2. Use with HTMX: `hx-target="#element-id"`
