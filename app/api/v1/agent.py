"""Agent invoke endpoints — SSE streaming for LangChain, LangGraph, and Foundry proxy agents."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from unifiedui_sdk.integrations.models import RestApiAgentInvokeRequest
from unifiedui_sdk.streaming.models import StreamMessage, StreamMessageType
from unifiedui_sdk.streaming.writer import StreamWriter

from app.agents.langchain_agent import create_langchain_adapter
from app.agents.langgraph_agent import create_langgraph_adapter
from app.agents.echo_agent import echo_stream
from app.agents.foundry_proxy_agent import foundry_proxy_stream
from app.config import settings
from app.middleware.auth import (
    verify_anonymous,
    verify_api_key_header,
    verify_basic_auth,
    verify_entra_id_appreg_token,
    verify_entra_id_token,
)
from app.session.store import session_store

router = APIRouter(prefix="/api/v1", tags=["Agent"])


def _build_message_history(request: RestApiAgentInvokeRequest) -> list[BaseMessage]:
    """Build LangChain message history from the request."""
    messages: list[BaseMessage] = []

    if request.message_history:
        for entry in request.message_history[:-1]:
            if entry.role == "user":
                messages.append(HumanMessage(content=entry.content))
            elif entry.role == "assistant":
                messages.append(AIMessage(content=entry.content))

    return messages


def _get_user_message(request: RestApiAgentInvokeRequest) -> str:
    """Extract the latest user message from the request."""
    if request.message_history:
        for entry in reversed(request.message_history):
            if entry.role == "user":
                return entry.content

    return ""


async def _stream_agent(
    request: RestApiAgentInvokeRequest,
    agent_type: str,
) -> AsyncGenerator[dict[str, str], None]:
    """Run agent and yield SSE events."""
    message = _get_user_message(request)
    if not message:
        writer = StreamWriter()
        error_msg = writer.error("No user message found in request")
        yield {"event": error_msg.type.value, "data": error_msg.model_dump_json()}
        return

    history = _build_message_history(request)

    if request.conversation_id and session_store.session_exists(request.conversation_id):
        session_history = session_store.get_history(request.conversation_id, limit=20)
        session_messages: list[BaseMessage] = []
        for entry in session_history:
            if entry.role == "user":
                session_messages.append(HumanMessage(content=entry.content))
            elif entry.role == "assistant":
                session_messages.append(AIMessage(content=entry.content))
        history = session_messages + history

    if agent_type == "langchain":
        adapter = create_langchain_adapter()
    else:
        adapter = create_langgraph_adapter()

    full_response = ""

    async for msg in adapter.stream(message, message_history=history if history else None):
        if msg.type == StreamMessageType.TEXT_STREAM:
            full_response += msg.content
        yield {"event": msg.type.value, "data": msg.model_dump_json()}

    writer = StreamWriter()
    yield {"event": StreamMessageType.STREAM_END.value, "data": writer.stream_end().model_dump_json()}

    if request.conversation_id and session_store.session_exists(request.conversation_id):
        session_store.add_message(request.conversation_id, "user", message)
        if full_response:
            session_store.add_message(request.conversation_id, "assistant", full_response)


# --- Anonymous endpoints ---

@router.post("/anonymous/agent/langchain/invoke")
async def invoke_langchain_anonymous(
    request: RestApiAgentInvokeRequest,
    _: None = Depends(verify_anonymous),
) -> EventSourceResponse:
    """Invoke LangChain agent (anonymous auth) — returns SSE stream."""
    return EventSourceResponse(_stream_agent(request, "langchain"))


@router.post("/anonymous/agent/langgraph/invoke")
async def invoke_langgraph_anonymous(
    request: RestApiAgentInvokeRequest,
    _: None = Depends(verify_anonymous),
) -> EventSourceResponse:
    """Invoke LangGraph agent (anonymous auth) — returns SSE stream."""
    return EventSourceResponse(_stream_agent(request, "langgraph"))


# --- Basic Auth endpoints ---

@router.post("/basic-auth/agent/langchain/invoke")
async def invoke_langchain_basic_auth(
    request: RestApiAgentInvokeRequest,
    _: None = Depends(verify_basic_auth),
) -> EventSourceResponse:
    """Invoke LangChain agent (Basic Auth) — returns SSE stream."""
    return EventSourceResponse(_stream_agent(request, "langchain"))


@router.post("/basic-auth/agent/langgraph/invoke")
async def invoke_langgraph_basic_auth(
    request: RestApiAgentInvokeRequest,
    _: None = Depends(verify_basic_auth),
) -> EventSourceResponse:
    """Invoke LangGraph agent (Basic Auth) — returns SSE stream."""
    return EventSourceResponse(_stream_agent(request, "langgraph"))


# --- API Key endpoints ---

@router.post("/api-key/agent/langchain/invoke")
async def invoke_langchain_api_key(
    request: RestApiAgentInvokeRequest,
    _: None = Depends(verify_api_key_header),
) -> EventSourceResponse:
    """Invoke LangChain agent (API Key) — returns SSE stream."""
    return EventSourceResponse(_stream_agent(request, "langchain"))


@router.post("/api-key/agent/langgraph/invoke")
async def invoke_langgraph_api_key(
    request: RestApiAgentInvokeRequest,
    _: None = Depends(verify_api_key_header),
) -> EventSourceResponse:
    """Invoke LangGraph agent (API Key) — returns SSE stream."""
    return EventSourceResponse(_stream_agent(request, "langgraph"))


# --- Entra ID endpoints ---

@router.post("/entra-id/agent/langchain/invoke")
async def invoke_langchain_entra_id(
    request: RestApiAgentInvokeRequest,
    _: None = Depends(verify_entra_id_token),
) -> EventSourceResponse:
    """Invoke LangChain agent (Entra ID) — returns SSE stream."""
    return EventSourceResponse(_stream_agent(request, "langchain"))


@router.post("/entra-id/agent/langgraph/invoke")
async def invoke_langgraph_entra_id(
    request: RestApiAgentInvokeRequest,
    _: None = Depends(verify_entra_id_token),
) -> EventSourceResponse:
    """Invoke LangGraph agent (Entra ID) — returns SSE stream."""
    return EventSourceResponse(_stream_agent(request, "langgraph"))


# --- Entra ID App Registration endpoints ---

@router.post("/entra-id-appreg/agent/langchain/invoke")
async def invoke_langchain_entra_id_appreg(
    request: RestApiAgentInvokeRequest,
    _: None = Depends(verify_entra_id_appreg_token),
) -> EventSourceResponse:
    """Invoke LangChain agent (Entra ID App Registration) — returns SSE stream."""
    return EventSourceResponse(_stream_agent(request, "langchain"))


@router.post("/entra-id-appreg/agent/langgraph/invoke")
async def invoke_langgraph_entra_id_appreg(
    request: RestApiAgentInvokeRequest,
    _: None = Depends(verify_entra_id_appreg_token),
) -> EventSourceResponse:
    """Invoke LangGraph agent (Entra ID App Registration) — returns SSE stream."""
    return EventSourceResponse(_stream_agent(request, "langgraph"))


# --- Foundry Proxy endpoints ---


async def _stream_foundry_proxy(
    request: RestApiAgentInvokeRequest,
    auth_header: dict[str, str],
) -> AsyncGenerator[dict[str, str], None]:
    """Stream Foundry proxy response as SSE events."""
    async for msg in foundry_proxy_stream(request, auth_header):
        yield {"event": msg.type.value, "data": msg.model_dump_json()}


@router.post("/api-key/agent/foundry-proxy/invoke")
async def invoke_foundry_proxy_api_key(
    request: RestApiAgentInvokeRequest,
    _: None = Depends(verify_api_key_header),
) -> EventSourceResponse:
    """Invoke Foundry proxy (API Key auth) — uses configured Foundry API key internally."""
    auth_header = {"api-key": settings.foundry_project_api_key}
    return EventSourceResponse(_stream_foundry_proxy(request, auth_header))


@router.post("/entra-id/agent/foundry-proxy/invoke")
async def invoke_foundry_proxy_entra_id(
    http_request: Request,
    request: RestApiAgentInvokeRequest,
    _: None = Depends(verify_entra_id_token),
) -> EventSourceResponse:
    """Invoke Foundry proxy (Entra ID) — forwards user bearer token to Foundry."""
    authorization = http_request.headers.get("Authorization", "")
    token = authorization.removeprefix("Bearer ").strip()
    auth_header = {"Authorization": f"Bearer {token}"}
    return EventSourceResponse(_stream_foundry_proxy(request, auth_header))


# --- Echo endpoints (no LLM needed) ---

async def _stream_echo(
    request: RestApiAgentInvokeRequest,
) -> AsyncGenerator[dict[str, str], None]:
    """Run echo agent and yield SSE events."""
    message = _get_user_message(request)
    if not message:
        writer = StreamWriter()
        error_msg = writer.error("No user message found in request")
        yield {"event": error_msg.type.value, "data": error_msg.model_dump_json()}
        return

    full_response = ""
    async for msg in echo_stream(message):
        if msg.type == StreamMessageType.TEXT_STREAM:
            full_response += msg.content
        yield {"event": msg.type.value, "data": msg.model_dump_json()}

    if request.conversation_id and session_store.session_exists(request.conversation_id):
        session_store.add_message(request.conversation_id, "user", message)
        if full_response:
            session_store.add_message(request.conversation_id, "assistant", full_response)


@router.post("/anonymous/agent/echo/invoke")
async def invoke_echo_anonymous(
    request: RestApiAgentInvokeRequest,
    _: None = Depends(verify_anonymous),
) -> EventSourceResponse:
    """Invoke echo agent (anonymous) — returns SSE stream without LLM."""
    return EventSourceResponse(_stream_echo(request))


@router.post("/api-key/agent/echo/invoke")
async def invoke_echo_api_key(
    request: RestApiAgentInvokeRequest,
    _: None = Depends(verify_api_key_header),
) -> EventSourceResponse:
    """Invoke echo agent (API Key) — returns SSE stream without LLM."""
    return EventSourceResponse(_stream_echo(request))
