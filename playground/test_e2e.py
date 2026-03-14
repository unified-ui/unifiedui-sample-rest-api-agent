"""Quick E2E test for anonymous and API key auth flows."""

import httpx
import sys
import json


BASE = "http://localhost:8087"


def test_anonymous():
    print("=" * 60)
    print("TEST: Anonymous Auth Flow")
    print("=" * 60)

    # 1. Create conversation
    resp = httpx.post(f"{BASE}/api/v1/anonymous/conversations", json={"config": {}})
    assert resp.status_code == 200, f"Create conversation failed: {resp.status_code} {resp.text}"
    conv_id = resp.json()["conversation_id"]
    print(f"  [OK] Created conversation: {conv_id}")

    # 2. Invoke echo agent (no LLM needed)
    print("  [..] Invoking echo agent...")
    with httpx.stream(
        "POST",
        f"{BASE}/api/v1/anonymous/agent/echo/invoke",
        json={
            "conversation_id": conv_id,
            "unified_ui_conversation_id": "test-anon-1",
            "message_history": [{"role": "user", "content": "Hello from anonymous!"}],
        },
        timeout=30,
    ) as resp:
        assert resp.status_code == 200, f"Echo invoke failed: {resp.status_code}"
        events = []
        for line in resp.iter_lines():
            if line.startswith("event:"):
                events.append(line.split(":", 1)[1].strip())
        print(f"  [OK] Echo SSE events: {events}")

    # 3. Invoke langchain agent (real LLM)
    print("  [..] Invoking langchain agent (Azure OpenAI)...")
    with httpx.stream(
        "POST",
        f"{BASE}/api/v1/anonymous/agent/langchain/invoke",
        json={
            "conversation_id": conv_id,
            "unified_ui_conversation_id": "test-anon-2",
            "message_history": [{"role": "user", "content": "What is the weather in Berlin?"}],
        },
        timeout=60,
    ) as resp:
        assert resp.status_code == 200, f"Langchain invoke failed: {resp.status_code}"
        events = []
        full_text = ""
        for line in resp.iter_lines():
            if line.startswith("event:"):
                events.append(line.split(":", 1)[1].strip())
            elif line.startswith("data:"):
                try:
                    data = json.loads(line.split(":", 1)[1].strip())
                    if data.get("type") == "TEXT_STREAM":
                        full_text += data.get("content", "")
                except json.JSONDecodeError:
                    pass
        print(f"  [OK] LangChain SSE events: {events}")
        print(f"  [OK] Response text: {full_text[:200]}...")

    print("  [PASS] Anonymous auth flow complete!\n")


def test_api_key():
    print("=" * 60)
    print("TEST: API Key Auth Flow")
    print("=" * 60)

    headers = {"Authorization": "Bearer test-key-123"}

    # 1. Create conversation
    resp = httpx.post(f"{BASE}/api/v1/api-key/conversations", json={"config": {}}, headers=headers)
    assert resp.status_code == 200, f"Create conversation failed: {resp.status_code} {resp.text}"
    conv_id = resp.json()["conversation_id"]
    print(f"  [OK] Created conversation: {conv_id}")

    # 2. Test wrong API key (should fail)
    bad_resp = httpx.post(
        f"{BASE}/api/v1/api-key/conversations",
        json={"config": {}},
        headers={"Authorization": "Bearer wrong-key"},
    )
    assert bad_resp.status_code == 401, f"Expected 401, got {bad_resp.status_code}"
    print("  [OK] Wrong API key correctly rejected (401)")

    # 3. Invoke echo agent
    print("  [..] Invoking echo agent with API key...")
    with httpx.stream(
        "POST",
        f"{BASE}/api/v1/api-key/agent/echo/invoke",
        json={
            "conversation_id": conv_id,
            "unified_ui_conversation_id": "test-apikey-1",
            "message_history": [{"role": "user", "content": "Hello from API key!"}],
        },
        headers=headers,
        timeout=30,
    ) as resp:
        assert resp.status_code == 200, f"Echo invoke failed: {resp.status_code}"
        events = []
        for line in resp.iter_lines():
            if line.startswith("event:"):
                events.append(line.split(":", 1)[1].strip())
        print(f"  [OK] Echo SSE events: {events}")

    # 4. Invoke langchain agent (real LLM)
    print("  [..] Invoking langchain agent with API key (Azure OpenAI)...")
    with httpx.stream(
        "POST",
        f"{BASE}/api/v1/api-key/agent/langchain/invoke",
        json={
            "conversation_id": conv_id,
            "unified_ui_conversation_id": "test-apikey-2",
            "message_history": [{"role": "user", "content": "What is 2 + 3?"}],
        },
        headers=headers,
        timeout=60,
    ) as resp:
        assert resp.status_code == 200, f"Langchain invoke failed: {resp.status_code}"
        events = []
        full_text = ""
        for line in resp.iter_lines():
            if line.startswith("event:"):
                events.append(line.split(":", 1)[1].strip())
            elif line.startswith("data:"):
                try:
                    data = json.loads(line.split(":", 1)[1].strip())
                    if data.get("type") == "TEXT_STREAM":
                        full_text += data.get("content", "")
                except json.JSONDecodeError:
                    pass
        print(f"  [OK] LangChain SSE events: {events}")
        print(f"  [OK] Response text: {full_text[:200]}...")

    print("  [PASS] API key auth flow complete!\n")


if __name__ == "__main__":
    try:
        test_anonymous()
        test_api_key()
        print("=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
    except Exception as e:
        print(f"\n  [FAIL] {e}", file=sys.stderr)
        sys.exit(1)
