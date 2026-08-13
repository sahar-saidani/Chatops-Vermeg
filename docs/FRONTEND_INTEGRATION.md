# Frontend integration

How the React frontend talks to the Spring API and the LLM orchestrator, and
what is genuinely wired versus what is still gated on infrastructure.

Everything here describes code that exists in the repository. Where something
could not be exercised in the development sandbox it is marked **NOT
VERIFIED** with the reason, rather than being described as working.

---

## 1. Request flow

```
LoginPage ──► POST /api/v1/auth/login ──► { accessToken, refreshToken, ... }
    │
    └──► GET /api/v1/users/me ──► { roles[], permissions[], memberships[] }
             │
             ▼
        AuthContext ──► apiClient (injects Bearer token)
             │
             ├──► Spring API  :8080   users, roles, tenants, agents, dashboard, conversations
             └──► Orchestrator :8100  POST /api/chat
                        │
                        ├─ IntentClassifier          which agents, which action
                        ├─ TenantMachineRegistry     which machine, which OS, local vs SSH
                        ├─ AgentRunner               subprocess or SSH
                        │        └──► agent ──► RabbitMQ ──► Spring consumer ──► canonical_events
                        ├─ CanonicalEventsRepository reads back the fresh events
                        ├─ ResponseAnalyzer          natural-language answer
                        └─ ConversationHistoryClient POST /api/v1/conversations  (X-Internal-Api-Key)
```

Two independent HTTP surfaces: the Spring API is authenticated with a JWT; the
orchestrator has no authentication of its own and is called anonymously by the
browser. That is a deliberate current-state fact, not a recommendation — see
§ 9.

## 2. Authentication

Implemented in `frontend/src/context/AuthContext.tsx` and
`frontend/src/api/apiClient.ts`.

1. `POST /api/v1/auth/login` with `{ email, password }` returns a
   `TokenResponse`. The JWT's only claim is the subject (the email).
2. Because the token carries no roles, the client immediately calls
   `GET /api/v1/users/me` for roles, permissions and tenant memberships. A
   login is only considered successful once that call succeeds; otherwise the
   whole login is unwound rather than leaving a half-authenticated session.
3. Tokens are persisted to `localStorage` when "keep me signed in" is checked
   and `sessionStorage` otherwise. On load both are read, so rehydration does
   not need to know which was used.
4. A stored token is never trusted on its own — `/users/me` must confirm it.
5. Any `401` clears auth state centrally in the API client, so one expired
   token reliably returns the user to `/login`, from anywhere.
6. `403` surfaces as a permission-denied state, never as empty data.

Account creation is invitation-only: `POST /api/v1/auth/invitations` returns a
one-time token, and the mail service links to `/activate?token=` and
`/reset-password?token=` — both routes exist in the frontend.

## 3. Roles, permissions and dashboard variants

Roles live in the `roles` table. The seeds define:

| Role code | System | Notes |
|---|---|---|
| `ADMIN` | yes | Full platform administrator |
| `TENANT_ADMIN` | yes | Manages members and settings within one client |
| `USER` | yes | Standard user |
| `OPERATOR` | yes | "Operates agents and monitors executions" (V3) |
| `AUDITOR` | no | Added outside the seeds in the live database |

Permission codes:

| Code | Seeded in | Grants |
|---|---|---|
| `TENANT_CREATE` | V3 | Create clients |
| `ROLE_MANAGE` | V3 | Full role CRUD, and the permission matrix |
| `PERMISSION_MANAGE` | V4 | Create/update permissions |
| `USER_READ` | V5 | List and view users |
| `USER_WRITE` | V5 | Update and soft-delete users |
| `ENVIRONMENT_CREATE/READ/UPDATE/DELETE` | V9 | Environments within a client |
| `AGENT_EVENT_READ` | V12 | Agent reports **for the caller's own clients** |
| `AGENT_EVENT_READ_ALL` | V12 | Agent reports **across every client** (ADMIN only) |

### There is no DevOps or Non-DevOps role

The original design called for Admin / DevOps / Non-DevOps dashboards. Those
personas do not exist in this backend, and none of the five real roles maps
onto them. Inventing the mapping in TypeScript would put in the frontend a
decision the RBAC model deliberately keeps in the database — and it would
break the moment an administrator defines a new role.

The variation is therefore keyed to the permissions that actually differ
between those personas:

| Persona in the spec | Real signal | Effect |
|---|---|---|
| Admin | `USER_READ` | Users tile shows a count; without it, an explicit no-access dash — never `0` |
| DevOps / operations | `AGENT_EVENT_READ` | Agents section renders; without it, "not available to you" — not an empty grid |
| Any user | tenant membership | Own clients, environments and conversations |

`Sidebar.tsx` filters navigation on the same principle, and `ProtectedRoute` /
`PermissionGate` enforce it per route and per control. The backend's
`@PreAuthorize` checks remain the actual enforcement; the frontend guards are
usability only.

## 4. Endpoints used

Pre-existing unless marked **added**.

### Auth — `/api/v1/auth`
| Method | Path | Notes |
|---|---|---|
| POST | `/login` | `{email,password}` → `TokenResponse` |
| POST | `/refresh` | `{refreshToken}` |
| POST | `/activate` | `{token,password}` |
| POST | `/forgot-password` | `{email}` |
| POST | `/reset-password` | `{token,password}` |
| POST | `/invitations` | authenticated → one-time token |

### Identity — `/api/v1/users`
| Method | Path | Permission |
|---|---|---|
| GET | `/` | `USER_READ` |
| GET | `/{id}` | `USER_READ` |
| **GET** | **`/me`** | **added** — authenticated; returns roles + permissions |
| PUT | `/{id}` | `USER_WRITE` |
| DELETE | `/{id}` | `USER_WRITE` (soft delete) |

### Access — `/api/v1/roles`, `/api/v1/permissions`
| Method | Path | Permission |
|---|---|---|
| GET/POST/PUT/DELETE | `/api/v1/roles` | `ROLE_MANAGE` |
| **GET** | **`/api/v1/roles/permission-matrix`** | **added** — `ROLE_MANAGE`, read-only grid |
| GET/POST/PUT | `/api/v1/permissions` | `PERMISSION_MANAGE` (no delete exists) |

### Tenancy
| Method | Path | Permission |
|---|---|---|
| GET | `/api/v1/tenants` | authenticated; returns only assigned clients |
| POST | `/api/v1/tenants` | `TENANT_CREATE` |
| GET/POST/PUT/DELETE | `/api/v1/tenants/{tenantId}/environments` | `ENVIRONMENT_*` |

### Agent events — **added**
| Method | Path | Permission |
|---|---|---|
| GET | `/api/v1/agents/events?agentKey&tenant&environment&limit` | `AGENT_EVENT_READ` |
| GET | `/api/v1/agents/status` | `AGENT_EVENT_READ` |

### Dashboard and conversations — **added**
| Method | Path | Auth |
|---|---|---|
| GET | `/api/v1/dashboard` | authenticated |
| POST | `/api/v1/conversations` | `INTERNAL_SERVICE` (orchestrator only) |
| GET | `/api/v1/conversations?limit=` | authenticated; caller's own turns only |

### Orchestrator — `:8100`
| Method | Path |
|---|---|
| GET | `/health` |
| POST | `/api/chat` — `{user_id, message}` → answer, mode, tenant, machine, `agent_statuses[]` |

## 5. Frontend routes

Public: `/login`, `/activate`, `/reset-password`, `/forgot-password`.

Protected: `/dashboard`, `/chat`, `/users`, `/roles`, `/permissions`,
`/tenants`, `/environments`, `/git`, `/jenkins`, `/installation`, `/logs`,
`/infrastructure`, `/history`, `/settings`, plus a catch-all.

`BrowserRouter` is used, so deep links survive a refresh; `ProtectedRoute`
waits for rehydration before deciding, to avoid flashing the login page.

## 6. Tenant isolation

`canonical_events` stores every client's reports in one table keyed by tenant
*name*. `AGENT_EVENT_READ` answers "may this caller read agent reports", not
"whose" — so scoping is applied in the query itself:

- The caller's clients come from their active tenant memberships, the same
  model `TenantController` uses.
- The `tenant` query parameter is a filter *within* that scope, never an
  escape hatch: asking for another client returns nothing.
- Rows with a null tenant (predating V10's machine identity) are excluded from
  tenant-scoped results — they cannot be attributed to anyone, and showing
  them would leak data on the strength of a missing column.
- `AGENT_EVENT_READ_ALL` grants cross-client visibility. It is a permission
  rather than a hardcoded `role == ADMIN` check, because roles are rows an
  operator can rename or recreate.
- `GET /api/v1/dashboard` is scoped identically, so it cannot become a side
  channel.

Covered by 8 tests in `AgentEventTenantIsolationTest`.

## 7. Agent status semantics

`AgentStatusCard` renders `ONLINE`, `STALE`, `RUNNING`, `SUCCESS`, `FAILED`,
`TIMEOUT`, `NO_DATA` and `DISABLED`.

The **events API only ever returns three** of them, because only three are
provable from stored rows:

| Status | Meaning |
|---|---|
| `NO_DATA` | The agent has never reported. Rendered distinctly — never as `ONLINE` |
| `ONLINE` | Newest report within 24 h |
| `STALE` | Has reported before, but not recently |

`RUNNING`, `FAILED` and `TIMEOUT` describe a *live orchestrator run* and
cannot be derived from the event store: a crashed agent writes nothing, which
is indistinguishable from one that was never asked to run. They reach the UI
from a chat response's `agent_statuses`, where the orchestrator reports each
planned agent as `SUCCESS`, `FAILED` (with its error) or `NO_RESULT`.

This is why an empty chat answer is worded from the real outcomes: a run where
an agent failed says so, and only a clean run with no results says the agents
returned no data. **An error is never rendered as "no data".**

## 8. Data integrity fixes worth knowing about

**`canonical_events.environment` used to record the server's Spring profile.**
Resolution consulted a payload-internal `env` key and then fell back to the
backend's active profile, ignoring the validated top-level `environment` field
the agent sends. Every event was stamped `dev` because the backend ran on the
dev profile. The top-level field now wins. Existing rows keep the old value —
the true one was never recorded, so no backfill is possible.

**`machine_reference` was overloaded.** MAIF's was `windows-local`, a value
`AgentRunner` special-cased to mean "run locally, don't SSH" — so one field
was both the machine's identity (stamped on every report, used to correlate
events) and the transport decision. `windows-local` appears in none of the
real events; every real MAIF machine is `MAIF-*`. Transport is now declared
separately as `local_execution` on the tenant route, freeing
`machine_reference` to be the real identity. The old sentinel is still
honoured so an un-migrated registry keeps working.

Current routing (`llm-orchestrator/config/tenant_machines.yml`):

| Client | Machine | OS | Repo / branch | Transport |
|---|---|---|---|---|
| MAIF | `MAIF-WINDOWS-01` | WINDOWS | `sahar-saidani/Solife-Standard` / `MAIF-Solife` | local |
| NNBE | `NNBE-CENTOS-01` | LINUX | `sahar-saidani/Solife-Standard` / `NNBE-Solife` | SSH |

## 9. Security considerations

- No secret has a committed value. `JWT_SECRET` has **no default** and the
  token provider refuses to sign or verify with a blank key.
- CORS is explicit-origin with `allowCredentials(true)`; wildcards are
  unsupported by construction.
- `POST /api/v1/conversations` is restricted to the `INTERNAL_SERVICE`
  authority, proven by a constant-time `X-Internal-Api-Key` comparison. The
  key is empty by default, so the endpoint **fails closed**. The filter runs
  after the JWT filter, so a real user token always wins over the shared key.
- Conversation history is readable only by its owner, taken from the
  authenticated principal and never from a parameter.
- The orchestrator has **no authentication of its own** and is reachable
  directly by the browser. Anyone who can reach `:8100` can run agents. It is
  expected to sit on a trusted network; exposing it publicly would need an
  auth layer first. This is a known gap, not a design endorsement.
- Frontend permission checks are usability only; `@PreAuthorize` on the server
  is the enforcement boundary.

## 10. Database

Migrations `V1`–`V12`. Added by this work:

| Migration | Purpose |
|---|---|
| `V11__create_conversation_turns_table.sql` | Conversation history |
| `V12__agent_event_permission_seed.sql` | `AGENT_EVENT_READ`, `AGENT_EVENT_READ_ALL` |

`V5`, `V7` and `V10` were rewritten for portability — they used PostgreSQL-only
syntax (`ON CONFLICT`, `PRIMARY KEY` before `DEFAULT`, `TIMESTAMPTZ`, multiple
`ADD COLUMN` in one statement) that H2 rejects, so the Flyway chain aborted
under `mvn test` and no Spring context could load.

> **Existing databases:** those three checksums no longer match. Run
> **`flyway repair`** before starting, or startup fails validation. In the
> development database observed during this work, `V1`–`V10` were applied and
> **`V11`/`V12` were not** — so conversation history and the agent-event
> permissions are absent until migration runs.

## 11. Verification status

| Area | Status |
|---|---|
| Backend build and tests | **PASS** — 13/13 |
| Frontend typecheck and build | **PASS** |
| Login, protected routes, 401/403 handling | **PASS** — exercised in a headless browser |
| Tenant isolation | **PASS** — 8 tests |
| Environment field mapping | **PASS** — 4 tests |
| Tenant routing (MAIF/NNBE identity + transport) | **PASS** — resolved and command-built directly |
| installation-agent bounded traversal | **PASS** — 52 passed, 1 skipped |
| git-agent `analyze --branch` | **PASS** locally |
| PostgreSQL | Reachable in the sandbox |
| RabbitMQ | **NOT VERIFIED** — broker not running |
| End-to-end agent → RabbitMQ → canonical_events → UI | **NOT VERIFIED** — needs the broker |
| Agents on the NNBE VM | **NOT VERIFIED** — no SSH access to 192.168.56.101 |
| Jenkins collection | **NOT VERIFIED** — no Jenkins URL or credentials |
| Log shipping (Filebeat → Logstash) | **NOT VERIFIED** — chain not running |
| infrastructure-agent Linux/Prometheus path | **NOT VERIFIED** — no Linux host |
| Chat end to end | **NOT VERIFIED** — needs orchestrator + `OPENROUTER_API_KEY` + broker |
| History end to end | **NOT VERIFIED** — `V11` not applied to the live database |

## 12. Known limitations

1. **No pagination.** `GET /api/v1/users` and `/api/v1/agents/events` return a
   list with no page metadata, so the UI does not paginate. The logs view says
   it is filtering "the most recent entries retrieved" rather than implying
   server-side paging that does not exist. Real pagination needs backend
   support first.
2. **The permission matrix is read-only.** No endpoint creates or deletes a
   `role_permissions` row — they come from the Flyway seeds. Checkboxes would
   imply an edit the API cannot perform.
3. **Installation state is not a lifecycle.** `canonical_events` stores
   completed reports, so pending/running/timeout for an installation cannot be
   shown from stored data; those states only exist during a chat run.
4. **`machine_reference` is inconsistent across agents** — the live database
   holds `MAIF-DEV-01`, `MAIF-windows-01`, `MAIF-WINDOWS-01`, `NNBE-DEV-01`,
   `NNBE-CENTOS-01`, `NNBE-DEV-JENKINS-01`. Each agent carries its own config.
   Correlation suffers until a canonical form is agreed.
5. **Legacy events are invisible to tenant-scoped users** by design (§ 6).
   Only `AGENT_EVENT_READ_ALL` holders see them.
6. **No password change for a signed-in user**, no MFA, no session registry —
   see the Settings page, which states each explicitly.
7. **Pre-existing test failures**: six `test_response_analyzer.py` tests
   (OpenRouter provider expectations) and one installation-agent CLI test that
   needs a broker. Untouched by this work.
8. **No backend controller tests beyond the slice tests added here.** The
   project had a single `contextLoads` test and no MockMvc infrastructure.
