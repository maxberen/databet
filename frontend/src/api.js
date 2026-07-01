const BASE = "http://localhost:8000/api";

function getToken() {
  return localStorage.getItem("token");
}

async function apiFetch(url, options = {}) {
  const res = await fetch(url, {
    ...options,
    headers: { ...(options.headers || {}), Authorization: `Bearer ${getToken()}` },
  });
  if (res.status === 401) {
    localStorage.removeItem("token");
    window.location.reload();
  }
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiLogin(email, password) {
  const res = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Error al iniciar sesión");
  localStorage.setItem("token", data.access_token);
}

export function apiLogout() {
  localStorage.removeItem("token");
}

export function isAuthenticated() {
  return !!getToken();
}

export async function fetchMatchesToday(day) {
  const url = day ? `${BASE}/matches/today?day=${day}` : `${BASE}/matches/today`;
  return apiFetch(url);
}

export async function fetchMatchOdds(matchId) {
  return apiFetch(`${BASE}/matches/${matchId}/odds`);
}
