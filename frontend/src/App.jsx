import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import dayjs from "dayjs";
import { fetchMatchesToday, fetchMatchOdds } from "./api";
import "./App.css";

const SPORT_ICON = { football: "⚽", tennis: "🎾" };

function OddsRange({ range, color }) {
  if (!range || (range.min == null && range.max == null)) return <span className="muted">—</span>;
  const same = range.min === range.max;
  return (
    <span className="odds-range" style={{ color }}>
      {same ? range.min?.toFixed(2) : `${range.min?.toFixed(2)} – ${range.max?.toFixed(2)}`}
    </span>
  );
}

function Modal({ matchId, onClose }) {
  const { data, isLoading } = useQuery({
    queryKey: ["odds", matchId],
    queryFn: () => fetchMatchOdds(matchId),
  });

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>✕</button>
        {isLoading && <p className="muted">Cargando...</p>}
        {data && (
          <>
            <div className="modal-header">
              <span className="sport-icon-lg">{SPORT_ICON[data.sport]}</span>
              <div>
                <div className="modal-title">{data.home_team} vs {data.away_team}</div>
                <div className="muted">{data.competition} · {dayjs(data.match_datetime).format("DD/MM/YYYY HH:mm")}</div>
              </div>
            </div>

            <table className="detail-table">
              <thead>
                <tr>
                  <th>Fuente</th>
                  <th>Bookmaker</th>
                  {data.sport === "football" ? (
                    <>
                      <th>Local</th>
                      <th>Empate</th>
                      <th>Visitante</th>
                    </>
                  ) : (
                    <>
                      <th>{data.home_team}</th>
                      <th>{data.away_team}</th>
                    </>
                  )}
                  <th>Overhead</th>
                  <th>Hora</th>
                </tr>
              </thead>
              <tbody>
                {data.odds.map((o, i) => {
                  const fav = data.sport === "football"
                    ? (() => {
                        const m = Math.min(o.home_win ?? Infinity, o.away_win ?? Infinity, o.draw ?? Infinity);
                        return m === o.home_win ? "home" : m === o.away_win ? "away" : "draw";
                      })()
                    : (o.player1_win ?? Infinity) <= (o.player2_win ?? Infinity) ? "p1" : "p2";

                  const prob = (v) => v != null ? 1 / v : null;
                  const pct = (v) => v != null ? (v * 100).toFixed(1) + "%" : null;

                  const probs = data.sport === "football"
                    ? [prob(o.home_win), prob(o.draw), prob(o.away_win)].filter(p => p != null)
                    : [prob(o.player1_win), prob(o.player2_win)].filter(p => p != null);
                  const overhead = probs.length ? ((probs.reduce((a, b) => a + b, 0) - 1) * 100).toFixed(2) + "%" : "—";

                  const OddCell = ({ val, favClass }) => (
                    <td className={`odds-cell ${favClass ? "green" : ""}`}>
                      <div>{val?.toFixed(2) ?? "—"}</div>
                      {prob(val) != null && <div className="prob-label">{pct(prob(val))}</div>}
                    </td>
                  );

                  return (
                    <tr key={i}>
                      <td><span className="source-badge">{o.source}</span></td>
                      <td>{o.bookmaker}</td>
                      {data.sport === "football" ? (
                        <>
                          <OddCell val={o.home_win} favClass={fav === "home"} />
                          <OddCell val={o.draw} favClass={fav === "draw"} />
                          <OddCell val={o.away_win} favClass={fav === "away"} />
                        </>
                      ) : (
                        <>
                          <OddCell val={o.player1_win} favClass={fav === "p1"} />
                          <OddCell val={o.player2_win} favClass={fav === "p2"} />
                        </>
                      )}
                      <td className="overhead-cell">{overhead}</td>
                      <td className="muted">{dayjs(o.scraped_at).format("HH:mm")}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </>
        )}
      </div>
    </div>
  );
}

function MatchRow({ match, onClick }) {
  const isTennis = match.sport === "tennis";

  // El favorito es la columna con cuota mínima más baja
  const favorite = isTennis
    ? (match.player1_win?.min ?? Infinity) <= (match.player2_win?.min ?? Infinity) ? "p1" : "p2"
    : (() => {
        const hw = match.home_win?.min ?? Infinity;
        const aw = match.away_win?.min ?? Infinity;
        const dw = match.draw?.min ?? Infinity;
        const m = Math.min(hw, aw, dw);
        return m === hw ? "home" : m === aw ? "away" : "draw";
      })();

  return (
    <tr className="match-row" onClick={() => onClick(match.id)}>
      <td>
        <span className="sport-icon">{SPORT_ICON[match.sport]}</span>
      </td>
      <td>
        <div className="competition">{match.competition}</div>
        <div className="time muted">{dayjs(match.match_datetime).format("HH:mm")}</div>
      </td>
      <td className="teams">
        <div className="team">{match.home_team}</div>
        <div className="vs muted">vs</div>
        <div className="team">{match.away_team}</div>
      </td>
      <td className="center">
        <span className="sources-badge">{match.sources_count}</span>
      </td>
      {isTennis ? (
        <>
          <td className="odds-cell"><OddsRange range={match.player1_win} color={favorite === "p1" ? "var(--green)" : undefined} /></td>
          <td className="odds-cell"><OddsRange range={match.player2_win} color={favorite === "p2" ? "var(--green)" : undefined} /></td>
          <td className="odds-cell muted">—</td>
        </>
      ) : (
        <>
          <td className="odds-cell"><OddsRange range={match.home_win} color={favorite === "home" ? "var(--green)" : undefined} /></td>
          <td className="odds-cell"><OddsRange range={match.away_win} color={favorite === "away" ? "var(--green)" : undefined} /></td>
          <td className="odds-cell"><OddsRange range={match.draw} color={favorite === "draw" ? "var(--green)" : undefined} /></td>
        </>
      )}
    </tr>
  );
}

export default function App() {
  const [day, setDay] = useState(dayjs().format("YYYY-MM-DD"));
  const [selectedId, setSelectedId] = useState(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["matches", day],
    queryFn: () => fetchMatchesToday(day),
  });

  const football = data?.filter((m) => m.sport === "football") ?? [];
  const tennis = data?.filter((m) => m.sport === "tennis") ?? [];

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo">⚡ databet</div>
          <input
            type="date"
            className="date-picker"
            value={day}
            onChange={(e) => setDay(e.target.value)}
          />
        </div>
      </header>

      <main className="main">
        {isLoading && <p className="muted center-msg">Cargando partidos...</p>}
        {error && <p className="error center-msg">Error: {error.message}</p>}
        {data && data.length === 0 && (
          <p className="muted center-msg">No hay partidos para esta fecha.</p>
        )}

        {football.length > 0 && (
          <section className="section">
            <h2 className="section-title">⚽ Fútbol <span className="count">{football.length}</span></h2>
            <div className="table-wrap">
              <table className="matches-table">
                <thead>
                  <tr>
                    <th></th>
                    <th>Competencia</th>
                    <th>Partido</th>
                    <th className="center">Fuentes</th>
                    <th>Local</th>
                    <th>Visitante</th>
                    <th>Empate</th>
                  </tr>
                </thead>
                <tbody>
                  {football.map((m) => (
                    <MatchRow key={m.id} match={m} onClick={setSelectedId} />
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {tennis.length > 0 && (
          <section className="section">
            <h2 className="section-title">🎾 Tenis <span className="count">{tennis.length}</span></h2>
            <div className="table-wrap">
              <table className="matches-table">
                <thead>
                  <tr>
                    <th></th>
                    <th>Torneo</th>
                    <th>Partido</th>
                    <th className="center">Fuentes</th>
                    <th>Jugador 1</th>
                    <th>Jugador 2</th>
                    <th>Empate</th>
                  </tr>
                </thead>
                <tbody>
                  {tennis.map((m) => (
                    <MatchRow key={m.id} match={m} onClick={setSelectedId} />
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </main>

      {selectedId && <Modal matchId={selectedId} onClose={() => setSelectedId(null)} />}
    </div>
  );
}
