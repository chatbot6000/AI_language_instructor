/**
 * Main tutor shell — four panels + Spanish text chat (M1).
 */

import { api, clearToken, getToken } from "./api.js";

const state = {
  user: null,
  sessionId: null,
};

function requireToken() {
  if (!getToken()) {
    window.location.href = "/login";
    return false;
  }
  return true;
}

function appendBubble(logEl, role, text, extra = "") {
  const div = document.createElement("div");
  div.className = `bubble ${role}`;
  const meta = document.createElement("span");
  meta.className = "meta";
  meta.textContent = role === "user" ? "You" : "EVANGELINE";
  div.appendChild(meta);
  div.appendChild(document.createTextNode(text));
  if (extra) {
    const badge = document.createElement("div");
    badge.style.marginTop = "0.35rem";
    badge.innerHTML = `<span class="badge">${extra}</span>`;
    div.appendChild(badge);
  }
  logEl.appendChild(div);
  logEl.scrollTop = logEl.scrollHeight;
}

async function loadSession(logEl) {
  const session = await api("/api/chat/session");
  state.sessionId = session.id;
  logEl.innerHTML = "";
  if (!session.messages.length) {
    appendBubble(
      logEl,
      "assistant",
      "¡Hola! I'm EVANGELINE. Let's practice Spanish with short, friendly turns. Type anything to begin — try “Hola”.",
    );
  } else {
    for (const m of session.messages) {
      if (m.role === "user" || m.role === "assistant") {
        appendBubble(logEl, m.role, m.display_text || m.text);
      }
    }
  }
  document.getElementById("session-id").textContent = `Session #${session.id}`;
}

async function boot() {
  if (!requireToken()) return;

  const logEl = document.getElementById("chat-log");
  const form = document.getElementById("composer-form");
  const input = document.getElementById("message-input");
  const sendBtn = document.getElementById("send-btn");
  const llmBadge = document.getElementById("llm-badge");

  try {
    state.user = await api("/api/auth/me");
    document.getElementById("user-label").textContent = state.user.username;
  } catch {
    clearToken();
    window.location.href = "/login";
    return;
  }

  try {
    const cfg = await api("/api/config/ai");
    llmBadge.textContent = cfg.model ? `AI: ${cfg.model}` : "AI: not configured";
    llmBadge.className = cfg.model ? "badge ok" : "badge";
  } catch {
    llmBadge.textContent = "AI: unknown";
  }

  try {
    await loadSession(logEl);
  } catch (err) {
    appendBubble(logEl, "assistant", `Could not load session: ${err.message}`);
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    sendBtn.disabled = true;
    input.value = "";
    appendBubble(logEl, "user", text);
    try {
      const res = await api("/api/chat/message", {
        method: "POST",
        body: JSON.stringify({ message: text, session_id: state.sessionId }),
      });
      state.sessionId = res.session_id;
      document.getElementById("session-id").textContent = `Session #${res.session_id}`;
      appendBubble(
        logEl,
        "assistant",
        res.assistant_message.display_text || res.assistant_message.text,
        res.mocked ? "demo stub (no live LLM)" : "",
      );
      if (res.mocked) {
        llmBadge.textContent = "AI: stub / unreachable";
        llmBadge.className = "badge";
      } else {
        llmBadge.className = "badge ok";
      }
    } catch (err) {
      appendBubble(logEl, "assistant", `Error: ${err.message}`);
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  });

  document.getElementById("new-session-btn").addEventListener("click", async () => {
    try {
      const session = await api("/api/chat/session/new", { method: "POST" });
      state.sessionId = session.id;
      await loadSession(logEl);
    } catch (err) {
      appendBubble(logEl, "assistant", `Could not start new session: ${err.message}`);
    }
  });

  document.getElementById("settings-btn").addEventListener("click", () => {
    window.location.href = "/settings";
  });

  document.getElementById("logout-btn").addEventListener("click", () => {
    clearToken();
    window.location.href = "/login";
  });
}

boot();
