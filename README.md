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

---

## Setup Instructions (First Time Only)

### 1. Prerequisites
- Python 3.11
- Java 17
- Maven 3.9+
- MySQL 8.0 (service name: `MySQL80`)

### 2. Configure the Database
Copy the example config and fill in your MySQL password:
```
spring-backend/src/main/resources/application.properties.example
→ copy to →
spring-backend/src/main/resources/application.properties
```
Edit `application.properties` and replace `your_mysql_password` with your real password.  
*(This file is gitignored — your credentials stay local.)*

### 3. Configure API Keys
Create a `.env` file inside `python-engine/`:
```env
NEWS_API_KEY=your_newsapi_key
YOUTUBE_API_KEY=your_youtube_api_key
GROQ_API_KEY=your_groq_api_key
```

### 4. Install Python Dependencies
```powershell
cd python-engine
pip install -r requirements.txt
```

---

## Running the Project (Every Time)

Open **3 separate PowerShell terminals** and run in this exact order:

### Step 1 — Start MySQL
```powershell
Start-Service MySQL80
```
Verify it's running:
```powershell
Get-Service MySQL80
# Expected: Status = Running
```

### Step 2 — Start Python Engine (Terminal 1)
```powershell
cd "d:\PROJECTS\Web Scrapping\brand-intelligence-analyzer\python-engine"
powershell -ExecutionPolicy Bypass -File start.ps1
```
Wait until you see:
```
Application startup complete.
Uvicorn running on http://127.0.0.1:8000
```

### Step 3 — Start Spring Boot Backend (Terminal 2)
```powershell
cd "d:\PROJECTS\Web Scrapping\brand-intelligence-analyzer\spring-backend"
powershell -ExecutionPolicy Bypass -File start.ps1
```
Wait until you see:
```
Started SpringBackendApplication in X seconds
Tomcat started on port 8080
```

### Step 4 — Open the Frontend (Browser)
Open this file directly in your browser:
```
d:\PROJECTS\Web Scrapping\brand-intelligence-analyzer\frontend\home.html
```

---

## Using the App
1. Click **Sign Up** and create an account
2. Go to **Dashboard**
3. Type a brand name (e.g. `Nike`, `Puma`, `Adidas`)
4. Click **Run Analysis** and wait ~3 minutes
5. View sentiment, topics, and AI strategy recommendations
6. Click **Download PDF** for the full report

---

## Port Reference
| Service        | Port |
|---------------|------|
| Python Engine | 8000 |
| Spring Boot   | 8080 |
| MySQL         | 3306 |

---

## Notes
- `start.ps1` in both `python-engine/` and `spring-backend/` automatically kills any orphan process on the port before starting fresh.
- The `application.properties` file is gitignored — never committed to GitHub.
- Reddit data collection may return 0 results due to API blocking (graceful fallback, does not crash).
- First run downloads ~2GB of NLP models (DistilBERT + zero-shot classifier). Subsequent runs are fast.
