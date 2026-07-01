const BASE = "http://localhost:8000/api";

export async function fetchMatchesToday(day) {
  const url = day ? `${BASE}/matches/today?day=${day}` : `${BASE}/matches/today`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Error cargando partidos");
  return res.json();
}

export async function fetchMatchOdds(matchId) {
  const res = await fetch(`${BASE}/matches/${matchId}/odds`);
  if (!res.ok) throw new Error("Error cargando odds");
  return res.json();
}
