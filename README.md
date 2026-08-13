# ChatOps Vermeg

A conversational operations platform: ask a question in natural language, and
the system runs the right collection agent against the right machine for your
client, then answers from what the agent actually reported.

Detailed integration notes live in [`docs/FRONTEND_INTEGRATION.md`](docs/FRONTEND_INTEGRATION.md).

---

## Architecture

```
                       ┌──────────────────────────────┐
   browser ───────────►│  Frontend (React 19 + Vite)  │
                       │  :8443                       │
                       └───────┬──────────────┬───────┘
                               │ REST + JWT   │ REST (no auth)
                               ▼              ▼
        ┌──────────────────────────────┐   ┌────────────────────────────┐
        │  Spring Boot API  :8080      │   │  LLM Orchestrator  :8100   │
        │  auth, RBAC, tenants,        │◄──┤  FastAPI                   │
        │  conversations, agent events │   │  intent → routing → plan   │
        └───────┬──────────────────────┘   └─────────────┬──────────────┘
                │  JPA                       X-Internal-  │ subprocess / SSH
                ▼                            Api-Key      ▼
        ┌──────────────────────┐              ┌──────────────────────────┐
        │  PostgreSQL          │              │  Agents                  │
        │  canonical_events,   │              │  git, jenkins,           │
        │  users/roles/tenants,│              │  installation, log,      │
        │  conversation_turns  │              │  infrastructure          │
        └──────────▲───────────┘              └───────────┬──────────────┘
                   │                                      │ publish
                   │        ┌──────────────┐              │
                   └────────┤  RabbitMQ    │◄─────────────┘
                   consume  └──────────────┘
```

The orchestrator never writes agent data itself. Agents publish to RabbitMQ;
the Spring consumer normalizes each message into `canonical_events`; both the
orchestrator (to answer questions) and the frontend (to render agent pages)
read from there.

## Components

| Component | Stack | Port | Source |
|---|---|---|---|
| Frontend | React 19, Vite 8, TypeScript 5.7, Tailwind v4 | 8443 | `frontend/` |
| API | Spring Boot 3.5.6, Java 17, Flyway | 8080 | `src/main/java/com/vermeg/chatops/` |
| Orchestrator | Python, FastAPI, uvicorn | 8100 | `llm-orchestrator/` |
| Agents | Python | — | `git-agent/`, `jenkins-agent/`, `installation-agent/`, `log-agent/`, `infrastructure-Agent/` |

`jira-agent/` exists and still publishes, but is deliberately not surfaced in
the UI or the agent events API.

## Prerequisites

PostgreSQL (database `chatops`), RabbitMQ, JDK 17, Node 22 with `corepack`,
and Python 3.11+ with a `.venv` in each agent directory.

## Setup

```bash
cp .env.example .env                 # then fill in — see "Environment variables"
export JWT_SECRET=$(openssl rand -base64 32)
export POSTGRES_PASSWORD=...
export INTERNAL_API_KEY=...
```

> **Upgrading an existing dev database?** Migrations V5, V7 and V10 were
> rewritten for PostgreSQL/H2 portability, so their checksums no longer match
> what was applied. **Run `flyway repair` before starting**, or the application
> will refuse to boot. See `docs/FRONTEND_INTEGRATION.md` § Database.

### Backend

```bash
./mvnw spring-boot:run     # :8080, dev profile is the default
./mvnw test                # 13 tests
```

### Orchestrator

```bash
cd llm-orchestrator
.venv/Scripts/python.exe main.py       # Windows;  .venv/bin/python on Linux
.venv/Scripts/python.exe -m pytest tests/
```

Serves `http://127.0.0.1:8100`, interactive docs at `/docs`.

### Frontend

```bash
cd frontend
cp .env.example .env
corepack pnpm install                  # pnpm per pnpm-lock.yaml
corepack pnpm dev                      # :8443  (PORT overrides)
corepack pnpm exec tsc --noEmit
corepack pnpm run build
```

`corepack pnpm` is used because `pnpm` is not assumed to be on `PATH`.

## Environment variables

No secret has a usable default. `JWT_SECRET` is intentionally empty — the
application fails loudly rather than signing tokens with a committed key.

| Variable | Used by | Notes |
|---|---|---|
| `JWT_SECRET` | API | **Required.** `openssl rand -base64 32` |
| `JWT_EXPIRATION` | API | Access token lifetime in ms (default 3600000) |
| `POSTGRES_HOST` / `_PORT` / `_DB` / `_USER` / `_PASSWORD` | API, orchestrator | |
| `RABBITMQ_HOST` / `_PORT` / `_USER` / `_PASSWORD` | API, agents | |
| `INTERNAL_API_KEY` | API + orchestrator | Shared secret for conversation writes. Must match on both sides; empty means the endpoint rejects everyone |
| `CORS_ALLOWED_ORIGINS` | API | Comma-separated. Default `http://localhost:5173,http://localhost:8443`. Wildcards unsupported — credentials are allowed |
| `AUTH_FRONTEND_BASE_URL` | API | Base for activation and reset links in email |
| `MAIL_HOST` / `_PORT` / `_USERNAME` / `_PASSWORD` | API | |
| `VITE_API_URL` | Frontend | Default `http://localhost:8080` |
| `VITE_ORCHESTRATOR_URL` | Frontend | Default `http://localhost:8100` |
| `OPENROUTER_API_KEY` | Orchestrator | Without it, intent detection is rule-based only |
| `AGENT_MAX_SCAN_*`, `AGENT_FOLLOW_SYMLINKS` | installation-agent | Scan bounds; see `installation-agent/app/config/settings.py` |

Root `.env.example` and `frontend/.env.example` document every key. Both are
gitignored so real values never land in the repository.

## Roles and permissions

Roles are database rows, not an enum. The seeds define **ADMIN**,
**TENANT_ADMIN**, **USER**, **OPERATOR** and **AUDITOR** — there is **no
DevOps or Non-DevOps role**. The frontend therefore keys navigation and
dashboard variants off permissions, never off a role name. See
`docs/FRONTEND_INTEGRATION.md` § Roles for the full matrix and rationale.

## Known limitations

- Agent execution against remote machines, the RabbitMQ pipeline, Jenkins
  collection and log shipping are **not verified** in the development sandbox —
  they need the target VM, a broker and real credentials.
- `machine_reference` is spelled inconsistently by different agents
  (`MAIF-DEV-01`, `MAIF-windows-01`, `MAIF-WINDOWS-01`, …), which weakens
  correlation. Unresolved; needs a decision on the canonical form.
- Six `test_response_analyzer.py` tests fail on OpenRouter provider
  expectations, and one installation-agent CLI test needs a live broker. All
  pre-date this integration work.

Full list in `docs/FRONTEND_INTEGRATION.md` § Known limitations.
