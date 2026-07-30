# LLM Orchestrator — ChatOps VERMEG

Implements the "LLM Orchestrator" box in the architecture diagram. It does
**not** collect technical data itself: it detects intent, launches the
existing Python collection agents as subprocesses (Mode 1), reads
`canonical_events` from PostgreSQL (Mode 1 + Mode 2), calls an LLM through
OpenRouter (OpenAI-compatible API, model `openai/gpt-oss-20b:free` by
default) to turn events into a natural-language answer, and persists the
conversation via the Spring Boot REST API.

## Layout

```
llm-orchestrator/
├── config/settings.py          # env-based Settings, same convention as other agents
├── agents/registry.py          # maps agent_key -> real CLI contract (git-agent, jenkins-agent, ...)
├── agents/runner.py            # subprocess.run(...) launcher, no HTTP
├── intent/classifier.py        # rule-based intent detection + optional LLM fallback
├── data/canonical_events_repository.py  # read-only SELECT access to canonical_events
├── data/conversation_history_client.py  # POSTs conversation turns to Spring Boot
├── llm/provider.py              # LLMProvider abstract interface (generate_response)
├── llm/openrouter_provider.py   # OpenRouterProvider(LLMProvider), via the OpenAI SDK
├── llm/analyzer.py             # builds the final answer through an injected LLMProvider
├── orchestrator.py             # ties everything together (Mode 1 / Mode 2)
├── api.py                      # FastAPI app: POST /api/chat
└── main.py                     # uvicorn entrypoint (mirrors installation-agent/main.py)
```

## Setup

```bash
cd llm-orchestrator
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in POSTGRES_*, OPENROUTER_API_KEY, SPRING_API_BASE_URL
python main.py          # serves http://127.0.0.1:8100, docs at /docs
```

## How agent execution works (Mode 1)

`agents/registry.py` is the single source of truth for how to invoke each
**existing, unmodified** agent. It was built by reading each agent's actual
`main.py`/`cli.py`, not by guessing:

| agent_key        | working dir                  | invocation                                  |
|-------------------|------------------------------|----------------------------------------------|
| `git`             | `git-agent/`                 | `python main.py analyze [--repo|--path ...]` |
| `jenkins`         | `jenkins-agent/`              | `python main.py analyze [--repo-path ...]`   |
| `jira`            | `jira-agent/`                 | `python main.py collect` then `python main.py report` |
| `installation`    | `installation-agent/`         | `python cli.py analyze [--path ...]`         |
| `infrastructure`  | `infrastructure-Agent/app/`   | `python main.py --collect`                   |
| `log`             | `log-agent/logs-agent/`       | `python main.py --mode prometheus`           |

`AgentRunner` runs each step with `subprocess.run(...)`, exactly as the
architecture requires ("NOT HTTP, NOT FastAPI" for agent invocation — the
one existing exception is installation-agent's optional FastAPI server in
`app/main.py`, which this orchestrator deliberately does not call; it uses
`cli.py analyze` instead).

After a successful run, `CanonicalEventsRepository.wait_for_fresh_data(...)`
polls `canonical_events` (written by the Java Data Processing Agent after
consuming the agent's RabbitMQ message) until a row newer than the launch
timestamp appears, or a timeout is reached.

## LLM provider

The orchestrator only depends on the `LLMProvider` interface
(`llm/provider.py`, one method: `generate_response(system_prompt,
user_prompt, ...)`). The default implementation, `OpenRouterProvider`
(`llm/openrouter_provider.py`), calls OpenRouter's OpenAI-compatible
`/v1/chat/completions` endpoint through the official `openai` Python SDK,
pointed at OpenRouter via `base_url`. Model and credentials come from
`OPENROUTER_API_KEY` / `OPENROUTER_BASE_URL` / `OPENROUTER_MODEL` - the
model name is never hardcoded.

Both `ResponseAnalyzer` (final NL answer) and `LLMIntentFallback` (intent
detection when no keyword matches) are built on top of this same
`OpenRouterProvider`. Swapping to a different vendor later only requires a
new `LLMProvider` implementation plus a one-line change in
`api.py::build_orchestrator` - `orchestrator.py`, `intent/classifier.py`'s
rule-based logic, agent execution, and the PostgreSQL/RabbitMQ paths are
untouched.

## Known gaps (out of scope for this change, flagged for follow-up)

1. **`oracle`, `configuration`, `security`, `business-documents` agents do
   not exist in the repository yet.** The registry only wires up the six
   agents that are actually implemented (`git`, `jenkins`, `jira`,
   `installation`, `infrastructure`, `log`), which also matches
   `chatops.rabbitmq.queues` in `application.yml`. The intent classifier
   will report `confidence=0.0` / no agent match for requests about those
   domains until the corresponding agent is built.
2. **No `conversation_history` table or Spring Boot endpoint exists yet.**
   Migrations only go up to `V6__create_canonical_events_table.sql`, and
   there is no `conversation` package under `com.vermeg.chatops`.
   `ConversationHistoryClient` is written against the contract the
   architecture specifies (`POST /api/v1/conversations`) so the
   orchestrator is ready the moment that endpoint exists; until then it
   logs a warning and still returns the answer to the user instead of
   failing the request.

## Testing

```bash
pytest -q   # classifier + registry tests, no DB/RabbitMQ/API key required
```
