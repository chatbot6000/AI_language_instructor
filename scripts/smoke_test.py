#!/usr/bin/env python3
"""
M0/M1 smoke test against a running server (default http://127.0.0.1:8000).

Checks: health → register → config → chat turn → session resume.
Works without a live LLM (expects stub reply when unreachable).
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from uuid import uuid4

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"


def req(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"} if body is not None else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        f"{BASE}{path}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        raise SystemExit(f"{method} {path} → {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Cannot reach {BASE}: {exc}") from exc


def main() -> None:
    health = req("GET", "/health")
    assert health.get("status") == "ok", health
    print("OK  /health")

    username = f"smoke_{uuid4().hex[:8]}"
    password = "testpass"
    token = req("POST", "/api/auth/register", {"username": username, "password": password})[
        "access_token"
    ]
    print(f"OK  register ({username})")

    me = req("GET", "/api/auth/me", token=token)
    assert me["username"] == username
    print("OK  /api/auth/me")

    cfg = req(
        "PUT",
        "/api/config/ai",
        {
            "base_url": "http://127.0.0.1:11434/v1",
            "model": "llama3.2",
            "api_key": None,
            "temperature": 0.7,
        },
        token=token,
    )
    assert cfg["model"] == "llama3.2"
    print("OK  AI config")

    chat = req(
        "POST",
        "/api/chat/message",
        {"message": "Hola"},
        token=token,
    )
    assert chat["user_message"]["text"] == "Hola"
    assert chat["assistant_message"]["text"]
    print(
        f"OK  chat turn (mocked={chat.get('mocked')}) → "
        f"{chat['assistant_message']['text'][:80]!r}"
    )

    session = req("GET", "/api/chat/session", token=token)
    assert len(session["messages"]) >= 2
    print(f"OK  session resume ({len(session['messages'])} messages)")
    print("Smoke test passed.")


if __name__ == "__main__":
    main()
