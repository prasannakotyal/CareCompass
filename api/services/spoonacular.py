"""Spoonacular API service for meal planning and recipes."""

import os
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

SPOONACULAR_BASE_URL = "https://api.spoonacular.com"

# Available diet types
DIET_TYPES = [
    {"value": "none", "label": "No Restriction"},
    {"value": "vegetarian", "label": "Vegetarian"},
    {"value": "vegan", "label": "Vegan"},
    {"value": "glutenFree", "label": "Gluten Free"},
    {"value": "ketogenic", "label": "Ketogenic (Keto)"},
    {"value": "paleo", "label": "Paleo"},
    {"value": "pescetarian", "label": "Pescetarian"},
]


def get_api_key() -> str:
    """Get Spoonacular API key from environment."""
    return os.environ.get("SPOONACULAR_API_KEY", "")


def is_configured() -> bool:
    """Check if Spoonacular API is configured."""
    return bool(get_api_key())


async def search_recipes(
    query: str = "",
    diet: Optional[str] = None,
    max_results: int = 6,
    include_nutrition: bool = True,
) -> list[dict]:
    """
    Search for recipes with optional diet filter.

    Args:
        query: Search query (e.g., "pasta", "chicken")
        diet: Diet type filter (vegetarian, vegan, keto, etc.)
        max_results: Maximum number of results to return
        include_nutrition: Whether to include nutrition data

    Returns:
        List of recipe dictionaries
    """
    api_key = get_api_key()
    if not api_key:
        return []

    params = {
        "apiKey": api_key,
        "query": query or "healthy",
        "number": max_results,
        "addRecipeNutrition": include_nutrition,
        "addRecipeInstructions": True,
        "fillIngredients": True,
    }

    if diet and diet != "none":
        params["diet"] = diet

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{SPOONACULAR_BASE_URL}/recipes/complexSearch", params=params
            )
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        print(f"Spoonacular API error: {e}")
        return []

    recipes = []
    for result in data.get("results", []):
        nutrition = result.get("nutrition", {})
        nutrients = {n["name"]: n for n in nutrition.get("nutrients", [])}

        recipe = {
            "id": result.get("id"),
            "title": result.get("title"),
            "image": result.get("image"),
            "ready_in_minutes": result.get("readyInMinutes"),
            "servings": result.get("servings"),
            "source_url": result.get("sourceUrl"),
            "calories": round(nutrients.get("Calories", {}).get("amount", 0)),
            "protein": round(nutrients.get("Protein", {}).get("amount", 0)),
            "carbs": round(nutrients.get("Carbohydrates", {}).get("amount", 0)),
            "fat": round(nutrients.get("Fat", {}).get("amount", 0)),
            "fiber": round(nutrients.get("Fiber", {}).get("amount", 0)),
        }
        recipes.append(recipe)

    return recipes


async def get_recipe_details(recipe_id: int) -> Optional[dict]:
    """
    Get detailed information about a specific recipe.

    Args:
        recipe_id: Spoonacular recipe ID

    Returns:
        Recipe details or None if not found
    """
    api_key = get_api_key()
    if not api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{SPOONACULAR_BASE_URL}/recipes/{recipe_id}/information",
                params={
                    "apiKey": api_key,
                    "includeNutrition": True,
                },
            )
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        print(f"Spoonacular API error: {e}")
        return None

    # Parse nutrition
    nutrition = data.get("nutrition", {})
    nutrients = {n["name"]: n for n in nutrition.get("nutrients", [])}

    # Parse ingredients
    ingredients = []
    for ing in data.get("extendedIngredients", []):
        ingredients.append(
            {
                "name": ing.get("name"),
                "amount": ing.get("amount"),
                "unit": ing.get("unit"),
                "original": ing.get("original"),
            }
        )

    # Parse instructions
    instructions = []
    for step_group in data.get("analyzedInstructions", []):
        for step in step_group.get("steps", []):
            instructions.append(
                {
                    "number": step.get("number"),
                    "step": step.get("step"),
                }
            )

    return {
        "id": data.get("id"),
        "title": data.get("title"),
        "image": data.get("image"),
        "ready_in_minutes": data.get("readyInMinutes"),
        "servings": data.get("servings"),
        "source_url": data.get("sourceUrl"),
        "summary": data.get("summary"),
        "calories": round(nutrients.get("Calories", {}).get("amount", 0)),
        "protein": round(nutrients.get("Protein", {}).get("amount", 0)),
        "carbs": round(nutrients.get("Carbohydrates", {}).get("amount", 0)),
        "fat": round(nutrients.get("Fat", {}).get("amount", 0)),
        "fiber": round(nutrients.get("Fiber", {}).get("amount", 0)),
        "sugar": round(nutrients.get("Sugar", {}).get("amount", 0)),
        "sodium": round(nutrients.get("Sodium", {}).get("amount", 0)),
        "ingredients": ingredients,
        "instructions": instructions,
        "diets": data.get("diets", []),
        "vegetarian": data.get("vegetarian", False),
        "vegan": data.get("vegan", False),
        "gluten_free": data.get("glutenFree", False),
    }


async def generate_meal_plan(
    target_calories: int = 2000, diet: Optional[str] = None, timeframe: str = "day"
) -> Optional[dict]:
    """
    Generate a meal plan.

    Args:
        target_calories: Target daily calorie intake
        diet: Diet type filter
        timeframe: "day" or "week"

    Returns:
        Meal plan data or None if error
    """
    api_key = get_api_key()
    if not api_key:
        return None

    params = {
        "apiKey": api_key,
        "targetCalories": target_calories,
        "timeFrame": timeframe,
    }

    if diet and diet != "none":
        params["diet"] = diet

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{SPOONACULAR_BASE_URL}/mealplanner/generate", params=params
            )
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        print(f"Spoonacular API error: {e}")
        return None

    if timeframe == "day":
        meals = []
        for meal in data.get("meals", []):
            meals.append(
                {
                    "id": meal.get("id"),
                    "title": meal.get("title"),
                    "ready_in_minutes": meal.get("readyInMinutes"),
                    "servings": meal.get("servings"),
                    "source_url": meal.get("sourceUrl"),
                    "image": f"https://spoonacular.com/recipeImages/{meal.get('id')}-312x231.jpg",
                }
            )

        nutrients = data.get("nutrients", {})
        return {
            "meals": meals,
            "nutrients": {
                "calories": round(nutrients.get("calories", 0)),
                "protein": round(nutrients.get("protein", 0)),
                "carbs": round(nutrients.get("carbohydrates", 0)),
                "fat": round(nutrients.get("fat", 0)),
            },
        }

    return data


def get_diet_types() -> list[dict]:
    """Get list of available diet types."""
    return DIET_TYPES
