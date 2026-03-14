"""Conversation creation endpoints — one per auth mode."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from unifiedui_sdk.integrations.models import CreateConversationRequest, CreateConversationResponse

from app.middleware.auth import (
    verify_anonymous,
    verify_api_key_header,
    verify_basic_auth,
    verify_entra_id_appreg_token,
    verify_entra_id_token,
)
from app.session.store import session_store

router = APIRouter(prefix="/api/v1", tags=["Conversations"])


@router.post("/anonymous/conversations", response_model=CreateConversationResponse)
async def create_conversation_anonymous(
    request: CreateConversationRequest,
    _: None = Depends(verify_anonymous),
) -> CreateConversationResponse:
    """Create a new conversation session (anonymous)."""
    session_id = session_store.create_session()
    return CreateConversationResponse(conversation_id=session_id)


@router.post("/basic-auth/conversations", response_model=CreateConversationResponse)
async def create_conversation_basic_auth(
    request: CreateConversationRequest,
    _: None = Depends(verify_basic_auth),
) -> CreateConversationResponse:
    """Create a new conversation session (Basic Auth)."""
    session_id = session_store.create_session()
    return CreateConversationResponse(conversation_id=session_id)


@router.post("/api-key/conversations", response_model=CreateConversationResponse)
async def create_conversation_api_key(
    request: CreateConversationRequest,
    _: None = Depends(verify_api_key_header),
) -> CreateConversationResponse:
    """Create a new conversation session (API Key)."""
    session_id = session_store.create_session()
    return CreateConversationResponse(conversation_id=session_id)


@router.post("/entra-id/conversations", response_model=CreateConversationResponse)
async def create_conversation_entra_id(
    request: CreateConversationRequest,
    _: None = Depends(verify_entra_id_token),
) -> CreateConversationResponse:
    """Create a new conversation session (Entra ID user token)."""
    session_id = session_store.create_session()
    return CreateConversationResponse(conversation_id=session_id)


@router.post("/entra-id-appreg/conversations", response_model=CreateConversationResponse)
async def create_conversation_entra_id_appreg(
    request: CreateConversationRequest,
    _: None = Depends(verify_entra_id_appreg_token),
) -> CreateConversationResponse:
    """Create a new conversation session (Entra ID app registration)."""
    session_id = session_store.create_session()
    return CreateConversationResponse(conversation_id=session_id)
