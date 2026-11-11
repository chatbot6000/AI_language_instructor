/**
 * Login / register page logic.
 */

import { api, setToken, getToken } from "./api.js";

async function boot() {
  // Already signed in? Skip to tutor.
  if (getToken()) {
    try {
      await api("/api/auth/me");
      window.location.href = "/app";
      return;
    } catch {
      // stale token — stay on login
    }
  }

  const form = document.getElementById("auth-form");
  const modeToggle = document.getElementById("mode-toggle");
  const submitBtn = document.getElementById("submit-btn");
  const errorEl = document.getElementById("error");
  const titleEl = document.getElementById("auth-title");
  let mode = "login"; // or register

  modeToggle.addEventListener("click", () => {
    mode = mode === "login" ? "register" : "login";
    titleEl.textContent = mode === "login" ? "Sign in" : "Create account";
    submitBtn.textContent = mode === "login" ? "Sign in" : "Create account";
    modeToggle.textContent =
      mode === "login" ? "Need an account? Register" : "Have an account? Sign in";
    errorEl.textContent = "";
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.textContent = "";
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    submitBtn.disabled = true;
    try {
      const path = mode === "login" ? "/api/auth/login" : "/api/auth/register";
      const data = await api(path, {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      setToken(data.access_token);
      window.location.href = "/app";
    } catch (err) {
      errorEl.textContent = err.message || "Something went wrong";
    } finally {
      submitBtn.disabled = false;
    }
  });
}

boot();
