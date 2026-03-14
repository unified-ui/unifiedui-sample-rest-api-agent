"""Test script for the sample REST API agent endpoints."""

from __future__ import annotations

import json

import httpx

BASE_URL = "http://localhost:8087"


def test_anonymous_flow() -> None:
    """Test anonymous auth: create conversation + invoke agent."""
    print("\n=== Anonymous Flow ===")

    response = httpx.post(f"{BASE_URL}/api/v1/anonymous/conversations", json={"config": {}})
    print(f"Create conversation: {response.status_code}")
    data = response.json()
    conversation_id = data["conversation_id"]
    print(f"  conversation_id: {conversation_id}")

    print("\nInvoking LangChain agent...")
    invoke_request = {
        "conversation_id": conversation_id,
        "unified_ui_conversation_id": "test-unified-ui-conv-1",
        "message_history": [
            {"role": "user", "content": "What is the weather in Berlin?"},
        ],
        "config": {},
    }

    with httpx.stream("POST", f"{BASE_URL}/api/v1/anonymous/agent/langchain/invoke", json=invoke_request) as resp:
        print(f"  Status: {resp.status_code}")
        for line in resp.iter_lines():
            if line.startswith("data:"):
                event_data = json.loads(line[5:].strip())
                print(f"  [{event_data['type']}] {event_data.get('content', '')[:100]}")

    print("\nSending follow-up message...")
    invoke_request["message_history"] = [
        {"role": "user", "content": "And what about Tokyo?"},
    ]

    with httpx.stream("POST", f"{BASE_URL}/api/v1/anonymous/agent/langchain/invoke", json=invoke_request) as resp:
        for line in resp.iter_lines():
            if line.startswith("data:"):
                event_data = json.loads(line[5:].strip())
                print(f"  [{event_data['type']}] {event_data.get('content', '')[:100]}")


def test_api_key_flow() -> None:
    """Test API key auth: create conversation + invoke LangGraph agent."""
    print("\n=== API Key Flow ===")

    headers = {"Authorization": "Bearer your-api-key-here"}

    response = httpx.post(
        f"{BASE_URL}/api/v1/api-key/conversations",
        json={"config": {}},
        headers=headers,
    )
    print(f"Create conversation: {response.status_code}")

    if response.status_code != 200:
        print(f"  Error: {response.text}")
        return

    conversation_id = response.json()["conversation_id"]
    print(f"  conversation_id: {conversation_id}")

    print("\nInvoking LangGraph agent...")
    invoke_request = {
        "conversation_id": conversation_id,
        "unified_ui_conversation_id": "test-unified-ui-conv-2",
        "message_history": [
            {"role": "user", "content": "Calculate sqrt(144) + 10"},
        ],
        "config": {},
    }

    with httpx.stream(
        "POST",
        f"{BASE_URL}/api/v1/api-key/agent/langgraph/invoke",
        json=invoke_request,
        headers=headers,
    ) as resp:
        print(f"  Status: {resp.status_code}")
        for line in resp.iter_lines():
            if line.startswith("data:"):
                event_data = json.loads(line[5:].strip())
                print(f"  [{event_data['type']}] {event_data.get('content', '')[:100]}")


if __name__ == "__main__":
    print("Testing Sample REST API Agent Service")
    print("Make sure the server is running on port 8087")
    test_anonymous_flow()
    test_api_key_flow()
    print("\nDone!")
