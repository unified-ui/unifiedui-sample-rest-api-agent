"""LangChain agent — creates a LangchainStreamAdapter for streaming."""

from __future__ import annotations

from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent

from app.config import settings
from app.tools.sample_tools import all_tools

from unifiedui_sdk.integrations.langchain import LangchainStreamAdapter

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to weather, calculator, and time tools. "
    "Use them when needed to answer the user's questions accurately."
)


def create_langchain_adapter() -> LangchainStreamAdapter:
    """Create a LangchainStreamAdapter with sample tools."""
    llm = AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        azure_deployment=settings.azure_openai_deployment,
        api_version=settings.azure_openai_api_version,
        streaming=True,
    )
    agent = create_react_agent(llm, all_tools, prompt=SYSTEM_PROMPT)
    return LangchainStreamAdapter(agent=agent)
