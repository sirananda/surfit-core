# SurfitAI V2 — Live Engine + Dashboard

## Quick Start (two terminals)

### Terminal 1 — Wave Engine API
```bash
cd surfit-v2
pip install -r requirements.txt
python server.py
```
Runs on http://localhost:8000

### Terminal 2 — Dashboard UI
```bash
cd surfit-v2/dashboard
npm install
npm run dev
```
Opens http://localhost:3000

## What's New in V2

- **Live engine integration** — Dashboard calls the real Wave Engine API
- **Simulate Action panel** — 8 preset actions you can fire at the engine with one click
- **"Why This Wave" modal** — Click any simulated action's reason to see full factor breakdown
- **Engine status indicator** — Shows whether the API is reachable
- **Real wave assignments** — No more hardcoded mock waves; every action is evaluated live

## How to Demo

1. Start both terminals
2. Open dashboard at localhost:3000
3. On the Dashboard page, find "Simulate Action" section
4. Click any preset (e.g., "Slack Announcement", "GitHub Merge to Main")
5. Watch the action appear in the activity table with a real wave assignment
6. For pending actions (Wave 4-5), use Approve/Reject/Override buttons
7. Click the blue underlined "Why" text to see the full wave breakdown

## File Structure

```
surfit-v2/
├── server.py              # FastAPI server with CORS
├── requirements.txt       # fastapi + uvicorn
├── surfit_wave/           # Wave engine (unchanged from v1.1)
│   ├── engine.py
│   ├── models.py
│   ├── policy.py
│   ├── classifier.py
│   └── api.py
└── dashboard/             # React frontend (V2)
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        └── App.jsx        # Full dashboard with live API integration
```

## API Contract

### POST /api/v1/governance/evaluate

```json
{
  "system": "slack",
  "action": "post_announcement",
  "resource": { "channel_name": "company-announcements" },
  "context": { "env": "prod", "visibility": "company_wide" }
}
```

Response includes wave_score, wave_label, handling, reasons[], contributing_factors[].

### GET /api/v1/health

Returns `{ "status": "ok", "engine": "surfit-wave-engine-v2" }`
