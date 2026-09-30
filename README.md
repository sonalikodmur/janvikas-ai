# JanVikas AI — citizen-powered development planning (prototype)

Citizens submit requests by text or voice (English / Hindi / Marathi) → Gemini analyses them (keyword fallback if no key) → saved in SQLite → grouped into demand hotspots → explainable priority scores → policymaker dashboard.

> **All demo data is SYNTHETIC** (500 generated requests, districts, infrastructure and investment figures). Scores are **AI-assisted planning priorities, not official government decisions.**

## Structure
```
backend/app/  main.py (REST API) · models.py (SQLAlchemy) · ai.py (Gemini + fallback)
              planning.py (hotspots + scoring, edit WEIGHTS here) · seed.py (synthetic data)
backend/tests/test_api.py
frontend/src/ App.jsx · Citizen.jsx · Dashboard.jsx · MapView.jsx · i18n.js · api.js
render.yaml · .env.example · .gitignore
```

## Run locally (Windows, PowerShell) — Python 3.11+ and Node 18+
Backend:
```
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy ..\.env.example .env
uvicorn app.main:app --reload
```
Edit `backend/.env` and paste your `GEMINI_API_KEY` (optional; without it the keyword fallback is used). API docs: http://localhost:8000/docs

Frontend (new terminal):
```
cd frontend
copy ..\.env.example .env
npm install
npm run dev
```
Open http://localhost:5173

## Test
```
cd backend
pytest -q
```
Manual: submit a request in the portal → note the ID → open Dashboard → total increases; hotspot click shows district, category, count, score.

## APIs
`GET /api/health` · `GET /api/meta` · `POST /api/requests` · `GET /api/requests` · `GET /api/requests/{id}` · `POST /api/requests/{id}/analyze` · `GET /api/dashboard/summary` · `GET /api/hotspots` · `GET /api/recommendations`

## Method (transparent)
- **Hotspot:** requests grouped by district + category; ≥ `HOTSPOT_MIN` (10) requests = one hotspot = one candidate project (not one project per request).
- **Score (0–100):** demand 30% + infrastructure gap 25% + population 20% + vulnerability 15% + investment gap 10%. Each factor is 0–100; the dashboard shows every contribution. Change `WEIGHTS` in `backend/app/planning.py`.
- **Affected population** = district population × gap/100 × 10% (assumption, may overlap).

## Push to GitHub
```
git init
git add .
git commit -m "JanVikas AI prototype"
git branch -M main
git remote add origin https://github.com/<your-user>/janvikas-ai.git
git push -u origin main
```
(Create the empty repo on github.com first. `.env` is git-ignored — never commit keys.)

## Deploy on Render (free tier)
1. Render dashboard → **New → Blueprint** → select your repo (uses `render.yaml`), or create the two services manually:
2. **Backend** (Web Service, root `backend`): build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Env vars: `GEMINI_API_KEY`, `FRONTEND_ORIGIN` (the static site URL, no trailing slash).
3. **Frontend** (Static Site, root `frontend`): build `npm install && npm run build`, publish dir `dist`. Env var: `VITE_API_URL` = backend URL.
4. Deploy the backend first, copy its URL into `VITE_API_URL`, then deploy the frontend, then set `FRONTEND_ORIGIN` on the backend and redeploy.
5. Verify: open `<backend-url>/api/health`, then the frontend URL.

**Free-tier limits:** the backend sleeps after inactivity (first load can take ~30–60 s) and its disk is ephemeral, so SQLite data (including submitted requests) resets on redeploy/restart; demo data is re-seeded automatically. Use a managed database for anything real.
