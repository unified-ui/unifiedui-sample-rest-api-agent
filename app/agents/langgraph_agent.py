"""LangGraph agent — creates a LanggraphStreamAdapter for streaming."""

from __future__ import annotations

from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent

from app.config import settings
from app.tools.sample_tools import all_tools

from unifiedui_sdk.integrations.langgraph import LanggraphStreamAdapter

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to weather, calculator, and time tools. "
    "Use them when needed to answer the user's questions accurately."
)


def create_langgraph_adapter() -> LanggraphStreamAdapter:
    """Create a LanggraphStreamAdapter with a prebuilt ReACT graph."""
    llm = AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        azure_deployment=settings.azure_openai_deployment,
        api_version=settings.azure_openai_api_version,
        streaming=True,
    )
    graph = create_react_agent(llm, all_tools)
    return LanggraphStreamAdapter(graph=graph)
