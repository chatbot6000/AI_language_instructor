# EVANGELINE

**E**volving **V**irtual **A**ssistant for **N**urturing **G**raduated **E**ngagement in **L**anguage **I**mmersion **N**eural **E**xperience

Conversational language tutor with spaced review — **not** Pimsleur branding or fidelity.

This repository currently ships the **M0 + M1** vertical slice:

| Milestone | What’s included |
|---|---|
| **M0** | Project layout (`backend/`, `frontend/`, `content/`), FastAPI app, SQLite, config, splash + four-panel shell |
| **M1** | Username/password auth (JWT), AI Config UI (OpenAI-compatible base URL / model / key), Spanish **text-only** tutor with persisted sessions & messages |

**Deferred (M2+):** SRS warm-up, audio STT/TTS, Japanese/romaji track, curated illustrations, persona instructions UI, ComfyUI, avatar wardrobe, etc.

---

## Requirements

- Python 3.11+ (3.12 fine)
- Optional: [Ollama](https://ollama.com/) or any OpenAI-compatible HTTP endpoint

## Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000/** in Brave (or any modern desktop browser).

- Splash → **Get started** → register → tutor shell  
- **AI config** (top bar) to point at your LLM  
- Chat works even **without** an LLM: replies fall back to a clear demo stub

Health check: `GET /health` → `{"status":"ok",...}`

### Environment (optional)

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` / `secret_key` | `dev-only-change-me-evangeline` | JWT signing (change for anything shared) |
| `DATABASE_URL` / `database_url` | `sqlite:///…/backend/data/evangeline.db` | SQLite path |

Copy patterns into a `backend/.env` if you like; `pydantic-settings` loads it.

---

## Pointing at an LLM

Configure in the UI (**AI config**) or rely on the per-user defaults created at registration.

### Local Ollama

1. Install Ollama and pull a model, e.g. `ollama pull llama3.2`
2. Ensure the OpenAI-compatible server is up (default `http://127.0.0.1:11434`)
3. In AI config:
   - **Base URL:** `http://127.0.0.1:11434/v1`
   - **Model:** `llama3.2` (or whatever you pulled)
   - **API key:** leave empty

### Cloud OpenAI-compatible endpoint

Examples: OpenRouter, OpenAI, Grok-compatible gateways.

- **Base URL:** e.g. `https://openrouter.ai/api/v1`
- **Model:** provider’s model id
- **API key:** stored **only on the server** (never in `localStorage`)

If the endpoint is unreachable or misconfigured, chat still responds with a **demo stub** so you can exercise auth + persistence offline.

---

## Layout

```
backend/
  app/
    main.py           # FastAPI entry + static frontend
    config.py         # env settings
    database.py       # SQLite engine
    models.py         # User, AiConfig, Session, Message
    schemas.py        # Pydantic I/O
    auth.py           # bcrypt + JWT
    llm_client.py     # OpenAI-compatible client + stub
    routers/          # health, auth, config, chat
  requirements.txt
  data/               # created at runtime (sqlite db)
frontend/
  index.html          # splash
  login.html
  app.html            # four-panel tutor
  settings.html       # AI config
  css/  js/
content/              # seed packs later (M2+)
```

---

## Smoke test (no browser)

With the server running:

```bash
# from repo root, with backend venv active and deps installed
python scripts/smoke_test.py
```

Or manually:

```bash
curl -s http://127.0.0.1:8000/health
```

---

## Product locks (v0)

1. Conversational tutor + spaced review — no Pimsleur fidelity claims  
2. I/O surface later: text, images, audio, persona personality instructions  
3. Japanese starts as **romaji**; **all chat text always visible**
