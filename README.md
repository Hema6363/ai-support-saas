# AI Support SaaS 🚀

A production-ready, privacy-focused, **Multi-Tenant AI Customer Support SaaS Platform** built with **FastAPI**, **Next.js 15**, **ChromaDB**, and **local Ollama** (Llama 3.1 & nomic-embed-text).

---

## 📑 Table of Contents
- [Key Features](#-key-features)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Getting Started](#-getting-started)
  - [1. Environment Setup](#1-environment-setup)
  - [2. Start Infrastructure (Docker)](#2-start-infrastructure-docker)
  - [3. Start Ollama (Local AI Models)](#3-start-ollama-local-ai-models)
  - [4. Backend Setup & Migrations](#4-backend-setup--migrations)
  - [5. Frontend Setup](#5-frontend-setup)
- [API Documentation](#-api-documentation)
- [Testing & Evaluation](#-testing--evaluation)
- [Environment Variables](#-environment-variables)
- [License](#-license)

---

## ✨ Key Features

- 🏢 **Strict Multi-Tenancy**: Organization-level data isolation across relational database tables and ChromaDB vector collections.
- 🧠 **Local Privacy-First RAG**: Knowledge retrieval powered by local ChromaDB and Ollama (`nomic-embed-text` embeddings + `llama3.1:8b` inference) — zero customer data sent to third-party APIs.
- 💬 **Interactive AI Support Chat**: Real-time conversation interface with document citations, similarity distance metrics, latency tracking, and confidence indicators.
- 📚 **Knowledge Base Ingestion**: Automatic parsing and chunking for `.pdf`, `.docx`, `.txt`, and `.md` documents.
- 🎫 **Smart Ticket Management**: Automated and manual human agent ticket escalation, status tracking (`open`, `in_progress`, `resolved`, `closed`), and webhook dispatch.
- 📊 **Analytics & Metrics**: Real-time resolution rates, message volumes, AI response latencies, ticket status breakdowns, and document usage charts.
- 💳 **Billing & Subscriptions**: Multi-tiered SaaS plans (Starter, Pro, Enterprise) with document/query quota limits and Stripe integration.
- 🔐 **Secure Authentication**: JWT-based access and refresh tokens with password hashing via `passlib[bcrypt]`.

---

## 🛠️ Architecture & Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Next.js 15 (App Router), TypeScript, Tailwind CSS, Lucide Icons | Responsive modern web application UI |
| **Backend API** | FastAPI (Python 3.12 / 3.13), Pydantic v2 | High-performance RESTful API |
| **ORM & Migrations** | SQLAlchemy 2.0, Alembic | Relational database schema management |
| **Database** | PostgreSQL 16 | Relational data persistence (Tenants, Users, Chats, Tickets) |
| **Vector Store** | ChromaDB | Vector search and tenant-isolated document embeddings |
| **AI / LLM Engine** | Ollama (`llama3.1:8b`, `nomic-embed-text`) | Local embeddings generation & chat completion |
| **Authentication** | OAuth2 Bearer JWT + Refresh Tokens | Stateless and secure user authentication |

---

## 📁 Project Structure

```text
ai-support-saas/
├── alembic/                  # Database migration scripts
│   └── versions/             # Migration version history
├── backend/                  # FastAPI Backend application
│   └── app/
│       ├── ai/               # Ollama client, Embeddings, ChromaDB vector store, RAG engine
│       ├── api/              # API router, dependencies, and v1 endpoints
│       │   └── api_v1/endpoints/ # auth, chat, documents, tickets, analytics, payments, health
│       ├── core/             # Configuration and security utilities
│       ├── crud/             # Database CRUD repositories
│       ├── db/               # SQLAlchemy engine & session management
│       ├── models/           # SQLAlchemy ORM models
│       ├── schemas/          # Pydantic schemas / DTOs
│       ├── services/         # Integration & payment services
│       └── main.py           # FastAPI entrypoint
├── frontend/                 # Next.js 15 Frontend
│   ├── app/                  # App router (layout, globals, main dashboard)
│   ├── components/           # UI Components (ChatView, DocumentsView, TicketsView, etc.)
│   ├── lib/                  # Frontend API client and token helpers
│   └── types/                # TypeScript type definitions
├── scripts/                  # Evaluation benchmarks (RAG evaluation)
├── tests/                    # Pytest test suite (auth, RAG, isolation, tickets)
├── docker-compose.yml        # PostgreSQL & ChromaDB container definitions
├── requirements.txt          # Python backend dependencies
└── package.json              # Root npm workspace
```

---

## 📋 Prerequisites

Before running the project, ensure you have installed:

1. **Python 3.12+**
2. **Node.js 18+** & **npm**
3. **Docker Desktop** (for PostgreSQL & ChromaDB containers)
4. **Ollama** ([Download Ollama](https://ollama.com))

---

## 🚀 Getting Started

### 1. Environment Setup

Copy `.env.example` to `.env`:

```powershell
cp .env.example .env
```

Verify your `.env` settings (defaults work out of the box for local development).

---

### 2. Start Infrastructure (Docker)

Start PostgreSQL and ChromaDB containers:

```powershell
docker compose up -d
```

*Verifications:*
- PostgreSQL is accessible at `localhost:5433` (mapped from Docker 5432 to avoid Windows local collision)
- ChromaDB is accessible at `localhost:8001`
- Ollama is accessible at `localhost:11434`

---

### 3. Start Ollama (Local AI Models)

Ensure Ollama is running and pull the required models:

```powershell
# Start Ollama server if not already running in background
ollama serve

# Pull required embedding and chat models
ollama pull nomic-embed-text
ollama pull llama3.1:8b
```

---

### 4. Backend Setup & Migrations

1. **Create and activate a virtual environment:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. **Install Python dependencies:**

```powershell
pip install -r requirements.txt
```

3. **Run database migrations:**

```powershell
alembic upgrade head
```

4. **Start the FastAPI backend server:**

```powershell
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

- **Backend API Base**: `http://127.0.0.1:8000`
- **Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **Health Check**: `http://127.0.0.1:8000/health`

---

### 5. Frontend Setup

In a new terminal window:

1. **Install frontend dependencies:**

```powershell
npm install
```

2. **Run the Next.js development server:**

```powershell
npm run dev:frontend
```

- **Web Application UI**: `http://localhost:3000`

---

## 📡 API Documentation

Interactive OpenAPI documentation is available when the backend is running:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Primary API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register a new tenant organization & admin user |
| `POST` | `/api/v1/auth/login` | Authenticate and obtain JWT access + refresh tokens |
| `GET` | `/api/v1/auth/me` | Fetch authenticated user profile & tenant ID |
| `POST` | `/api/v1/documents/upload` | Upload `.pdf`, `.docx`, or `.txt` to tenant knowledge base |
| `GET` | `/api/v1/documents` | List tenant documents and indexing status |
| `POST` | `/api/v1/chat` | Send message to AI support assistant with RAG retrieval |
| `GET` | `/api/v1/conversations` | Retrieve conversation history |
| `GET` | `/api/v1/conversations/{id}` | Retrieve conversation detail with message history |
| `GET` | `/api/v1/tickets` | List tenant support tickets |
| `POST` | `/api/v1/tickets/escalate-from-conversation` | Escalate a conversation into a human support ticket |
| `GET` | `/api/v1/analytics/dashboard`| Aggregate analytics (resolution rates, latencies, volume) |
| `GET` | `/api/v1/payments/subscription`| Current tenant subscription status and quota limits |

---

## 🧪 Testing & Evaluation

### Run Unit & Integration Tests

```powershell
.\.venv\Scripts\Activate.ps1
pytest
```

### Run RAG Benchmark Evaluation

Evaluate retrieval accuracy, hallucination resistance, and latency:

```powershell
python scripts/evaluate_rag.py
```

---

## ⚙️ Environment Variables

Key configuration variables in `.env`:

```ini
# PostgreSQL
POSTGRES_USER=ai_support
POSTGRES_PASSWORD=changeme
POSTGRES_DB=ai_support
DATABASE_URL=postgresql+psycopg2://ai_support:changeme@127.0.0.1:5432/ai_support

# ChromaDB & Ollama
CHROMADB_URL=http://127.0.0.1:8001
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_CHAT_MODEL=llama3.1:8b
OLLAMA_EMBED_MODEL=nomic-embed-text

# Security
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Uploads
MAX_FILE_SIZE_MB=25
```

---

## 📄 License

This project is licensed under the MIT License.
