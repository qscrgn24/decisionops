# DecisionOps

DecisionOps is a small full-stack web app for running **budgeted selection / portfolio-style optimization** on a CSV dataset.  
It supports uploading a dataset, previewing/validating it, creating a run with configuration, executing a baseline optimizer, and viewing results.

## Features (MVP)
- Upload a CSV dataset (`/datasets/upload`)
- Preview rows + validation warnings (`/datasets/{id}/preview`)
- Create a run with config (`/runs`)
- Execute a baseline optimizer (greedy) and persist results (`/runs/{id}/execute-greedy`)
- View run status + results (`/runs/{id}`)
- Frontend workflow: Upload → Preview → Run → Execute → Results

## Tech stack
- **Backend:** FastAPI + SQLAlchemy + Alembic
- **Database:** Postgres (Docker)
- **Frontend:** React + TypeScript (Vite)
- **Dev:** WSL2 recommended

## Status

- MVP complete

---

## CSV format

### Required columns
- `item_id` (string, unique-ish)
- `name` (string)
- `cost` (number > 0)
- `value` (number >= 0)

### Optional columns
- `category` (string)
- `risk` (number in **[0,1]** or **[0,100]**; auto-normalized to 0–1)

### Example CSV

```csv
item_id,name,cost,value,category,risk
A1,Upgrade API servers,120,300,infra,20
A2,Refactor legacy code,80,180,infra,10
A3,Add caching layer,60,150,infra,5
B1,Google Ads campaign,100,220,marketing,40
B2,SEO optimization,50,130,marketing,15
B3,Email outreach automation,30,90,marketing,8
C1,New onboarding flow,90,260,product,12
C2,Mobile UI polish,70,170,product,6
C3,A/B testing framework,40,110,product,4
D1,Customer support chatbot,110,240,ops,25
D2,Log monitoring upgrade,55,140,ops,9
