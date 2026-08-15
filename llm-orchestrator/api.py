from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.runner import AgentRunner
from config import get_settings
from data.canonical_events_repository import CanonicalEventsRepository
from data.conversation_history_client import ConversationHistoryClient
from intent.classifier import IntentClassifier, LLMIntentFallback
from llm.analyzer import ResponseAnalyzer
from orchestrator import Orchestrator
from routing.tenant_machine_registry import TenantMachineRegistry

settings = get_settings()
logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChatOps VERMEG - LLM Orchestrator",
    description="Intent detection, agent launching and NL response generation",
    version="0.1.0",
)

# The frontend calls this API directly from the browser (not through Spring),
# so without CORS headers the browser silently blocks every response and the
# chat UI reports a generic "could not reach the server" even though the
# orchestrator answered. Anonymous by design (see chatApi.ts), so there is no
# credentialed cookie/session to protect - explicit origins still preferred
# over "*" to match the Spring-side policy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


def build_orchestrator() -> Orchestrator:
    tenant_registry = TenantMachineRegistry.from_file(settings.tenant_machine_registry_path)
    llm_fallback = (
        LLMIntentFallback(
            settings.openrouter_api_key,
            settings.openrouter_base_url,
            settings.openrouter_model,
            fallback_model=settings.openrouter_fallback_model,
        )
        if settings.openrouter_api_key
        else None
    )
    return Orchestrator(
        settings=settings,
        classifier=IntentClassifier(llm_client=llm_fallback, tenant_registry=tenant_registry),
        runner=AgentRunner(settings),
        events_repository=CanonicalEventsRepository(settings),
        analyzer=ResponseAnalyzer(settings),
        conversation_client=ConversationHistoryClient(settings),
        tenant_registry=tenant_registry,
    )


_orchestrator: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = build_orchestrator()
    return _orchestrator


class ChatRequest(BaseModel):
    user_id: str
    message: str


class AgentStatus(BaseModel):
    agent: str
    # SUCCESS, FAILED, or NO_RESULT (planned but never reported back).
    status: str
    error: str | None = None


class ChatResponse(BaseModel):
    answer: str
    mode: str
    tenant: str | None
    machine_reference: str | None
    agent_keys: list[str]
    environment: str | None
    task_id: str | None
    conversation_saved: bool
    # Per-agent outcome. Without this a client receives an answer and cannot
    # tell an agent that crashed from one that ran and found nothing, so it
    # would have to render both as "no data". Empty when no agent was launched.
    agent_statuses: list[AgentStatus] = []


@app.get("/health")
def health() -> dict:
    return {"status": "UP"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = get_orchestrator().handle_request(request.user_id, request.message)
    except RuntimeError as exc:
        # e.g. AGENTROUTER_API_KEY missing -> misconfiguration, not a client error
        logger.exception("Orchestrator misconfiguration")
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ChatResponse(
        answer=result.answer,
        mode=result.mode.value,
        tenant=result.tenant,
        machine_reference=result.machine_reference,
        agent_keys=result.agent_keys,
        environment=result.environment,
        task_id=result.task_id,
        conversation_saved=result.conversation_saved,
        agent_statuses=[AgentStatus(**status) for status in result.agent_statuses],
    )
