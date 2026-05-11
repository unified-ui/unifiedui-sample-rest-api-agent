"""Foundry proxy agent — streams Foundry responses as unified-ui SSE events."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from unifiedui_sdk.integrations.models import RestApiAgentInvokeRequest
from unifiedui_sdk.streaming.models import StreamMessage
from unifiedui_sdk.streaming.writer import StreamWriter

from app.config import settings


def _build_foundry_input(request: RestApiAgentInvokeRequest) -> str:
    """Extract the latest user message from the invoke request."""
    if request.message_history:
        for entry in reversed(request.message_history):
            if entry.role == "user":
                return entry.content
    return ""


def _build_foundry_payload(
    message: str,
    conversation_id: str | None,
) -> dict[str, Any]:
    """Build the Foundry /openai/responses request payload."""
    payload: dict[str, Any] = {
        "agent": {
            "type": "agent_reference",
            "name": settings.foundry_agent,
        },
        "input": message,
        "stream": True,
    }
    if conversation_id:
        payload["conversation"] = conversation_id
    return payload


def _convert_foundry_event(event_data: dict[str, Any], writer: StreamWriter) -> list[StreamMessage]:
    """Convert a Foundry SSE event into unified-ui StreamMessages."""
    event_type = event_data.get("type", "")
    messages: list[StreamMessage] = []

    if event_type == "response.output_text.delta":
        delta = event_data.get("delta", "")
        if delta:
            messages.append(writer.text_stream(delta))

    elif event_type == "response.output_item.added":
        item = event_data.get("item", {})
        item_type = item.get("type", "")
        if item_type == "message":
            messages.append(writer.stream_new_message())
        elif item_type.endswith("_call"):
            messages.append(writer.tool_call_start(
                tool_call_id=item.get("call_id", ""),
                tool_name=item.get("name", ""),
                tool_arguments={"call_type": item_type},
            ))

    elif event_type == "response.output_item.done":
        item = event_data.get("item", {})
        item_type = item.get("type", "")
        if item_type.endswith("_call"):
            messages.append(writer.tool_call_stream(
                tool_call_id=item.get("call_id", ""),
                content=item.get("arguments", ""),
            ))
        elif item_type.endswith("_call_output"):
            messages.append(writer.tool_call_end(
                tool_call_id=item.get("call_id", ""),
                tool_name=item.get("name", ""),
                tool_status="success",
                tool_result=item.get("output", ""),
            ))

    elif event_type == "response.completed":
        response = event_data.get("response", {})
        output_text = response.get("output_text", "")
        if output_text:
            messages.append(writer.message_complete({"content": output_text}))

    return messages


async def foundry_proxy_stream(
    request: RestApiAgentInvokeRequest,
    auth_header: dict[str, str],
) -> AsyncGenerator[StreamMessage, None]:
    """Stream a Foundry agent response, converting events to unified-ui SSE format.

    Args:
        request: The unified-ui invoke request.
        auth_header: Auth headers for the Foundry API (e.g. api-key or Authorization).

    Yields:
        StreamMessage objects in the unified-ui SSE protocol.
    """
    writer = StreamWriter()
    yield writer.stream_start()

    message = _build_foundry_input(request)
    if not message:
        yield writer.error("No user message found in request")
        yield writer.stream_end()
        return

    url = (
        f"{settings.foundry_project_endpoint.strip()}"
        f"/openai/responses?api-version={settings.foundry_api_version}"
    )
    payload = _build_foundry_payload(message, request.conversation_id)

    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        **auth_header,
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(600.0)) as client:
        try:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    yield writer.error(
                        f"Foundry API error: status={resp.status_code}, body={body.decode()}"
                    )
                    yield writer.stream_end()
                    return

                async for line in resp.aiter_lines():
                    if not line:
                        continue

                    json_data = ""
                    if line.startswith("data: "):
                        json_data = line.removeprefix("data: ")
                    elif line.startswith("{"):
                        json_data = line
                    else:
                        continue

                    if json_data == "[DONE]":
                        break

                    try:
                        event_data = json.loads(json_data)
                    except json.JSONDecodeError:
                        continue

                    for msg in _convert_foundry_event(event_data, writer):
                        yield msg

        except httpx.HTTPError as exc:
            yield writer.error(f"Foundry connection error: {exc}")
        except Exception as exc:
            yield writer.error(f"Foundry proxy error: {exc}")

    yield writer.stream_end()
