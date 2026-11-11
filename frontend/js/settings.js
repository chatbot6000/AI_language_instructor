/**
 * AI Configuration screen — secrets stay on the server.
 */

import { api, clearToken, getToken } from "./api.js";

async function requireAuth() {
  if (!getToken()) {
    window.location.href = "/login";
    return null;
  }
  try {
    return await api("/api/auth/me");
  } catch {
    clearToken();
    window.location.href = "/login";
    return null;
  }
}

async function boot() {
  const user = await requireAuth();
  if (!user) return;

  document.getElementById("whoami").textContent = user.username;
  const form = document.getElementById("config-form");
  const statusEl = document.getElementById("status");
  const keyHint = document.getElementById("key-hint");

  try {
    const cfg = await api("/api/config/ai");
    document.getElementById("base_url").value = cfg.base_url || "";
    document.getElementById("model").value = cfg.model || "";
    document.getElementById("temperature").value = cfg.temperature ?? 0.7;
    keyHint.textContent = cfg.has_api_key
      ? "A key is stored on the server. Leave blank to keep it, or enter a new one."
      : "No key stored (fine for local Ollama).";
  } catch (err) {
    statusEl.textContent = err.message;
    statusEl.className = "error";
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    statusEl.textContent = "Saving…";
    statusEl.className = "ok";
    const payload = {
      base_url: document.getElementById("base_url").value.trim(),
      model: document.getElementById("model").value.trim(),
      temperature: Number(document.getElementById("temperature").value),
    };
    const keyVal = document.getElementById("api_key").value;
    // Only send api_key when the field was touched / filled — empty means clear if user typed nothing after having cleared intentionally.
    // UX: blank field leaves key unchanged (send null by omitting). Use checkbox to clear.
    if (document.getElementById("clear_key").checked) {
      payload.api_key = "";
    } else if (keyVal.trim() !== "") {
      payload.api_key = keyVal.trim();
    } else {
      payload.api_key = null;
    }

    try {
      const cfg = await api("/api/config/ai", {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      document.getElementById("api_key").value = "";
      document.getElementById("clear_key").checked = false;
      keyHint.textContent = cfg.has_api_key
        ? "A key is stored on the server. Leave blank to keep it, or enter a new one."
        : "No key stored (fine for local Ollama).";
      statusEl.textContent = "Saved.";
      statusEl.className = "ok";
    } catch (err) {
      statusEl.textContent = err.message;
      statusEl.className = "error";
    }
  });

  document.getElementById("back-btn").addEventListener("click", () => {
    window.location.href = "/app";
  });

  document.getElementById("logout-btn").addEventListener("click", () => {
    clearToken();
    window.location.href = "/login";
  });
}

boot();
