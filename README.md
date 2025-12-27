# CareCompass

A holistic health companion web application featuring AI-powered medical chat, healthcare facility finder, and meal planning.

## Features

- **MediChat**: AI-powered medical assistant using Google Gemini 2.5 Flash
- **Healthcare Finder**: Find nearby hospitals, pharmacies, and clinics using real-time geolocation
- **Meal Planner**: Search recipes by diet type, generate meal plans, and track calories

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML + HTMX + Alpine.js
- **Styling**: Pico CSS (responsive, mobile-friendly)
- **Package Manager**: uv
- **Deployment**: Vercel

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/CareCompass.git
cd CareCompass
```

### 2. Create environment file
Create a `.env` file with your API keys:
```env
GEMINI_API_KEY=your_gemini_api_key_here
SPOONACULAR_API_KEY=your_spoonacular_api_key_here
SESSION_SECRET=any_random_secret_string
```

Get your API keys from:
- `GEMINI_API_KEY`: [Google AI Studio](https://aistudio.google.com/app/apikey)
- `SPOONACULAR_API_KEY`: [Spoonacular](https://spoonacular.com/food-api/console#Dashboard)

### 3. Install dependencies
```bash
uv sync
```

### 4. Run locally
```bash
uv run uvicorn api.index:app --reload --port 8000
```

Open http://localhost:8000 in your browser.

## Deploy to Vercel

1. Push your code to GitHub
2. Import the project in [Vercel](https://vercel.com)
3. Add environment variables in Vercel dashboard
4. Deploy!

## Development

```bash
# Install with dev dependencies
uv sync

# Run development server
uv run uvicorn api.index:app --reload --port 8000

# Format code
uv run black api/

# Lint code
uv run ruff check api/

# Run tests
uv run pytest
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page |
| `/chat` | GET | MediChat page |
| `/nearby` | GET | Healthcare finder page |
| `/meals` | GET | Meal planner page |
| `/api/chat` | POST | Send message to AI |
| `/api/nearby` | GET | Search nearby healthcare |
| `/api/recipes` | GET | Search recipes |
| `/api/mealplan` | GET | Generate meal plan |

## Free API Limits

| API | Daily Limit |
|-----|-------------|
| Google Gemini 2.5 Flash | 1M tokens |
| Overpass (OSM) | Unlimited (rate-limited) |
| Spoonacular | 150 points |

## License

Apache License 2.0
