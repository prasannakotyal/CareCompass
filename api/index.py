"""CareCompass - FastAPI Application."""

import json
import os
import secrets
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeSerializer

from api.services import gemini, overpass, spoonacular

# Load environment variables
load_dotenv()

# Get base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize FastAPI app
app = FastAPI(
    title="CareCompass",
    description="Your holistic health companion",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Session serializer for storing chat history in cookies
SESSION_SECRET = os.environ.get("SESSION_SECRET", secrets.token_hex(32))
serializer = URLSafeSerializer(SESSION_SECRET)


def get_session_data(request: Request, key: str, default=None):
    """Get data from session cookie."""
    cookie_value = request.cookies.get(f"session_{key}")
    if cookie_value:
        try:
            return serializer.loads(cookie_value)
        except Exception:
            return default
    return default


def set_session_cookie(response, key: str, value):
    """Set session cookie with serialized data."""
    serialized = serializer.dumps(value)
    response.set_cookie(
        key=f"session_{key}",
        value=serialized,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=86400,  # 24 hours
    )


# =============================================================================
# Page Routes
# =============================================================================


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Landing page with links to all features."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """MediChat page."""
    history = get_session_data(request, "chat_history", [])
    if not history:
        history = [
            {
                "role": "assistant",
                "content": "Hello! I'm MediChat, your medical assistant. How can I help you today?",
            }
        ]

    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "history": history,
            "is_configured": gemini.is_configured(),
        },
    )


@app.get("/nearby", response_class=HTMLResponse)
async def nearby_page(request: Request):
    """Healthcare finder page."""
    return templates.TemplateResponse(
        "nearby.html",
        {
            "request": request,
            "amenity_types": overpass.get_amenity_types(),
        },
    )


@app.get("/meals", response_class=HTMLResponse)
async def meals_page(request: Request):
    """Meal planner page."""
    # Get tracked calories from session
    tracked_meals = get_session_data(request, "tracked_meals", [])
    total_calories = sum(m.get("calories", 0) for m in tracked_meals)

    return templates.TemplateResponse(
        "meals.html",
        {
            "request": request,
            "diet_types": spoonacular.get_diet_types(),
            "is_configured": spoonacular.is_configured(),
            "tracked_meals": tracked_meals,
            "total_calories": total_calories,
        },
    )


# =============================================================================
# API Routes - Chat
# =============================================================================


@app.post("/api/chat", response_class=HTMLResponse)
async def send_message(request: Request, message: str = Form(...)):
    """Send a message to MediChat (non-streaming fallback)."""
    # Get existing history
    history = get_session_data(request, "chat_history", [])

    # Add user message
    history.append({"role": "user", "content": message})

    # Get AI response
    response_text = gemini.chat(
        message, history[:-1]
    )  # Don't include current message in history
    history.append({"role": "assistant", "content": response_text})

    # Keep only last 20 messages to prevent cookie size issues
    if len(history) > 20:
        history = history[-20:]

    # Create response with updated cookie
    response = templates.TemplateResponse(
        "partials/chat_messages.html",
        {
            "request": request,
            "history": history,
        },
    )
    set_session_cookie(response, "chat_history", history)

    return response


@app.post("/api/chat/stream")
async def send_message_stream(request: Request, message: str = Form(...)):
    """Stream a chat response via Server-Sent Events."""
    # Get existing history
    history = get_session_data(request, "chat_history", [])

    async def generate_sse():
        """Generate SSE events from Gemini stream."""
        full_response = ""

        try:
            async for chunk in gemini.chat_stream(message, history):
                full_response += chunk
                # Send chunk as SSE event
                data = json.dumps({"chunk": chunk})
                yield f"data: {data}\n\n"

            # Send completion event with full response
            data = json.dumps({"done": True, "full_response": full_response})
            yield f"data: {data}\n\n"

        except Exception as e:
            print(f"Streaming error: {e}")
            error_msg = "I'm sorry, but I'm currently unable to process your request."
            data = json.dumps({"chunk": error_msg, "done": True, "error": True})
            yield f"data: {data}\n\n"

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@app.post("/api/chat/save", response_class=HTMLResponse)
async def save_chat(
    request: Request,
    user_message: str = Form(...),
    assistant_message: str = Form(...),
):
    """Save chat messages to session after streaming completes."""
    # Get existing history
    history = get_session_data(request, "chat_history", [])

    # Add both messages
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": assistant_message})

    # Keep only last 20 messages
    if len(history) > 20:
        history = history[-20:]

    # Return empty response with updated cookie
    response = HTMLResponse(content="", status_code=200)
    set_session_cookie(response, "chat_history", history)

    return response


@app.post("/api/chat/clear", response_class=HTMLResponse)
async def clear_chat(request: Request):
    """Clear chat history."""
    initial_history = [
        {
            "role": "assistant",
            "content": "Hello! I'm MediChat, your medical assistant. How can I help you today?",
        }
    ]

    response = templates.TemplateResponse(
        "partials/chat_messages.html",
        {
            "request": request,
            "history": initial_history,
        },
    )
    set_session_cookie(response, "chat_history", initial_history)

    return response


# =============================================================================
# API Routes - Nearby Healthcare
# =============================================================================


@app.get("/api/nearby", response_class=HTMLResponse)
async def find_nearby(
    request: Request,
    lat: float = Query(...),
    lon: float = Query(...),
    radius: int = Query(5000),
    types: str = Query("hospital,pharmacy,clinic"),
):
    """Find nearby healthcare facilities."""
    # Parse amenity types
    amenity_filter = [t.strip() for t in types.split(",") if t.strip()]

    # Search for places
    places = await overpass.find_nearby_healthcare(
        lat=lat,
        lon=lon,
        radius=radius,
        amenity_filter=amenity_filter if amenity_filter else None,
    )

    return templates.TemplateResponse(
        "partials/places_list.html",
        {
            "request": request,
            "places": places,
            "user_lat": lat,
            "user_lon": lon,
        },
    )


# =============================================================================
# API Routes - Meal Planner
# =============================================================================


@app.get("/api/recipes", response_class=HTMLResponse)
async def search_recipes(
    request: Request,
    query: str = Query(""),
    diet: str = Query("none"),
):
    """Search for recipes."""
    recipes = await spoonacular.search_recipes(
        query=query,
        diet=diet if diet != "none" else None,
        max_results=6,
    )

    return templates.TemplateResponse(
        "partials/recipe_cards.html",
        {
            "request": request,
            "recipes": recipes,
        },
    )


@app.get("/api/mealplan", response_class=HTMLResponse)
async def get_meal_plan(
    request: Request,
    calories: int = Query(2000),
    diet: str = Query("none"),
):
    """Generate a daily meal plan."""
    meal_plan = await spoonacular.generate_meal_plan(
        target_calories=calories,
        diet=diet if diet != "none" else None,
        timeframe="day",
    )

    return templates.TemplateResponse(
        "partials/meal_plan.html",
        {
            "request": request,
            "meal_plan": meal_plan,
        },
    )


@app.post("/api/meals/track", response_class=HTMLResponse)
async def track_meal(
    request: Request,
    title: str = Form(...),
    calories: int = Form(...),
):
    """Add a meal to calorie tracker."""
    tracked_meals = get_session_data(request, "tracked_meals", [])

    tracked_meals.append(
        {
            "title": title,
            "calories": calories,
        }
    )

    total_calories = sum(m.get("calories", 0) for m in tracked_meals)

    response = templates.TemplateResponse(
        "partials/calorie_tracker.html",
        {
            "request": request,
            "tracked_meals": tracked_meals,
            "total_calories": total_calories,
        },
    )
    set_session_cookie(response, "tracked_meals", tracked_meals)

    return response


@app.post("/api/meals/clear", response_class=HTMLResponse)
async def clear_tracked_meals(request: Request):
    """Clear tracked meals."""
    response = templates.TemplateResponse(
        "partials/calorie_tracker.html",
        {
            "request": request,
            "tracked_meals": [],
            "total_calories": 0,
        },
    )
    set_session_cookie(response, "tracked_meals", [])

    return response


# =============================================================================
# Health Check
# =============================================================================


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "gemini_configured": gemini.is_configured(),
        "spoonacular_configured": spoonacular.is_configured(),
    }
