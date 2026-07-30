from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agents.runner import AgentRunner
from config import get_settings
from data.canonical_events_repository import CanonicalEventsRepository
from data.conversation_history_client import ConversationHistoryClient
from intent.classifier import IntentClassifier, LLMIntentFallback
from llm.analyzer import ResponseAnalyzer
from orchestrator import Orchestrator

settings = get_settings()
logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChatOps VERMEG - LLM Orchestrator",
    description="Intent detection, agent launching and NL response generation",
    version="0.1.0",
)


def build_orchestrator() -> Orchestrator:
    llm_fallback = (
        LLMIntentFallback(settings.openrouter_api_key, settings.openrouter_base_url, settings.openrouter_model)
        if settings.openrouter_api_key
        else None
    )
    return Orchestrator(
        settings=settings,
        classifier=IntentClassifier(llm_client=llm_fallback),
        runner=AgentRunner(settings),
        events_repository=CanonicalEventsRepository(settings),
        analyzer=ResponseAnalyzer(settings),
        conversation_client=ConversationHistoryClient(settings),
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


class ChatResponse(BaseModel):
    answer: str
    mode: str
    agent_keys: list[str]
    environment: str | None
    conversation_saved: bool


@app.get("/health")
def health() -> dict:
    return {"status": "UP"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = get_orchestrator().handle_request(request.user_id, request.message)
    except RuntimeError as exc:
        # e.g. OPENROUTER_API_KEY missing -> misconfiguration, not a client error
        logger.exception("Orchestrator misconfiguration")
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ChatResponse(
        answer=result.answer,
        mode=result.mode.value,
        agent_keys=result.agent_keys,
        environment=result.environment,
        conversation_saved=result.conversation_saved,
    )
