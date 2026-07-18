# AI Support SaaS

Production-ready AI customer support SaaS scaffold with a Next.js frontend and FastAPI backend.

## Project structure

- `frontend/` - Next.js 15 + TypeScript + Tailwind CSS frontend
- `backend/` - FastAPI backend with SQLAlchemy and PostgreSQL support
- `docker-compose.yml` - Local development stack with PostgreSQL and ChromaDB
- `.env.example` - Environment variable template
- `requirements.txt` - Python backend dependencies
- `package.json` - Root npm workspace configuration

## Milestone 1

This milestone establishes the complete project structure, configuration files, and Docker scaffold. It does not include business logic.

## Commands

### Install dependencies

1. Install Python dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Install frontend dependencies:

```powershell
npm install
```

### Run services locally

- Frontend development server:

```powershell
npm run dev:frontend
```

- Backend development server:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

- Docker Compose stack:

```powershell
docker compose up --build
```
