# DecisionOps

DecisionOps is a full-stack optimization web application that allows users to upload structured datasets and compute optimal selections under budget and risk constraints.

**Live Demo:** https://decisionops.onrender.com  
**Version:** v0.1.0-beta  

---

## 🚀 Overview

DecisionOps allows users to:

- Upload CSV datasets
- Automatically resolve column aliases (flexible header handling)
- Preview and validate dataset integrity
- Run optimization under:
  - Budget constraints
  - Risk penalty (λ)
  - Optional item limits
- Compare:
  - Greedy baseline
  - Exact optimal solution
- View selection results and objective comparison

The application demonstrates full-stack development, database design, deployment, and optimization logic integration.

---

## 🛠 Tech Stack

### Backend
- FastAPI
- SQLAlchemy (2.0 style ORM)
- Alembic (migrations)
- PostgreSQL
- JWT Authentication
- Argon2 password hashing

### Frontend
- React
- TypeScript
- Axios
- TailwindCSS

### Deployment
- Render (Web Service + PostgreSQL)
- Production migrations via Alembic

---

## 🏗 Architecture

### Dataset Storage (v0.1 update)

Datasets are stored directly in PostgreSQL as binary (`BYTEA`) data rather than filesystem storage.

This design:
- Removes dependency on ephemeral container storage
- Makes deployment platform-agnostic
- Simplifies horizontal scaling

Preview and optimization both operate directly on stored binary data.

---

## 🧠 Optimization Model

Objective:

Maximize:

value − λ × risk

Subject to:

- Total cost ≤ budget
- Optional item count constraint

Two solvers implemented:

- Greedy baseline heuristic
- Exact optimal solver (combinatorial search)

Results include:
- Selected items
- Total cost
- Total value
- Risk-adjusted objective
- Baseline vs optimal comparison

---

## 🔐 Authentication

- Email/password login
- JWT-based session handling
- Password hashing with Argon2

Planned:
- Password reset
- OAuth integration

---

## 💻 Local Development

### 🔐 Environment Variables

Create a `.env` file in the backend directory using `.env.example` as a template:

```bash
cp backend/.env.example backend/.env
```

### Backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🛣 Upcoming Features

- Password Recovery Flow
- OAuth Login Providers
- Substring-based header alias
- Manual column mapping fallback UI
- Performance optimization for large datasets
- Run history
- Dashboard analytics

---

## 🤝 Contributing

This project is currently maintained by the author.

Future improvements and feature ideas are welcome.

---

## 👤 Author

Vatsal Singhania

Email: singhaniavatsal@gmail.com