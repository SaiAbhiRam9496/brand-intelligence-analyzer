# Brand Intelligence Analyzer

A multi-source brand intelligence platform that scrapes public data, runs NLP analysis, and generates AI-powered marketing strategy reports.

## Architecture

```
brand-intelligence-analyzer/
├── python-engine/     → FastAPI backend (scraping, NLP, Groq, PDF)
├── spring-backend/    → Spring Boot (JWT auth, DB caching, routing)
└── frontend/          → Plain HTML/CSS/JS dashboard
```

## Data Sources
- **NewsAPI** — recent news headlines
- **YouTube** — public video comments + official brand channel (tone)
- **Google Play Store** — app reviews
- **Reddit** — public search mentions (graceful fallback if blocked)
- **Wikipedia** — background context for Groq strategy generation

## Running the Python Engine
```bash
cd python-engine
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service liveness check |
| POST | `/analyze` | Run full brand analysis |
| POST | `/generate-pdf` | Generate PDF from cached data |

## Environment Variables
Create a `.env` file inside `python-engine/`:
```
NEWS_API_KEY=your_key
YOUTUBE_API_KEY=your_key
GROQ_API_KEY=your_key
```
