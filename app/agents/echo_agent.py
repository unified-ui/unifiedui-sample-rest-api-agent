"""Echo agent — streams back the user message without needing an LLM."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from unifiedui_sdk.streaming.models import StreamMessage, StreamMessageType
from unifiedui_sdk.streaming.writer import StreamWriter


async def echo_stream(
    message: str,
    config: dict[str, object] | None = None,
) -> AsyncGenerator[StreamMessage]:
    """Echo the user message back as a streaming response.

    Args:
        message: The user message to echo back.
        config: Optional config (unused, for interface compatibility).

    Yields:
        StreamMessage objects mimicking a real agent response.
    """
    writer = StreamWriter()

    yield writer.stream_start(config)

    response = f"Echo: {message}"
    for word in response.split(" "):
        yield writer.text_stream(word + " ")

    yield writer.message_complete({"content": response})
    yield writer.stream_end()
