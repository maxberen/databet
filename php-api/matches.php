<?php
require_once __DIR__ . '/_config.php';
require_once __DIR__ . '/_auth.php';

cors_preflight();
require_auth();

// Calcular rango UTC equivalente a la fecha local pedida
$offset_seconds = TIMEZONE_OFFSET * 3600;

if (!empty($_GET['day'])) {
    $local_day = $_GET['day']; // YYYY-MM-DD
} else {
    $local_now  = time() + $offset_seconds;
    $local_day  = date('Y-m-d', $local_now);
}

$utc_start = date('Y-m-d H:i:s', strtotime($local_day) - $offset_seconds);
$utc_end   = date('Y-m-d H:i:s', strtotime($local_day) - $offset_seconds + 86400);

$db = db();

// Subquery: match_id más reciente por (home, away, datetime, source_id)
$latest_sql = "
    SELECT MAX(id) AS match_id
    FROM matches
    WHERE match_datetime >= :utc_start AND match_datetime < :utc_end
    GROUP BY home_team, away_team, match_datetime, source_id
";

$rows = $db->prepare("
    SELECT
        m.home_team, m.away_team, m.match_datetime, m.sport,
        MAX(m.id)          AS id,
        MAX(m.competition) AS competition,
        COUNT(DISTINCT o.bookmaker) AS sources_count,
        MIN(o.home_win)    AS min_hw,  MAX(o.home_win)    AS max_hw,
        MIN(o.draw)        AS min_draw,MAX(o.draw)        AS max_draw,
        MIN(o.away_win)    AS min_aw,  MAX(o.away_win)    AS max_aw,
        MIN(o.player1_win) AS min_p1,  MAX(o.player1_win) AS max_p1,
        MIN(o.player2_win) AS min_p2,  MAX(o.player2_win) AS max_p2
    FROM matches m
    JOIN odds o ON o.match_id = m.id
    WHERE m.id IN ($latest_sql)
    GROUP BY m.home_team, m.away_team, m.match_datetime, m.sport
    ORDER BY m.match_datetime
");
$rows->execute([':utc_start' => $utc_start, ':utc_end' => $utc_end]);

function to_local(string $dt): string {
    $ts = strtotime($dt) + TIMEZONE_OFFSET * 3600;
    return date('Y-m-d\TH:i:s', $ts);
}

function range_or_null(?string $min, ?string $max): ?array {
    if ($min === null && $max === null) return null;
    return ['min' => $min !== null ? (float)$min : null,
            'max' => $max !== null ? (float)$max : null];
}

$result = [];
foreach ($rows->fetchAll() as $r) {
    $is_tennis = $r['sport'] === 'tennis';
    $result[] = [
        'id'             => (int)$r['id'],
        'sport'          => $r['sport'],
        'competition'    => $r['competition'],
        'home_team'      => $r['home_team'],
        'away_team'      => $r['away_team'],
        'match_datetime' => to_local($r['match_datetime']),
        'sources_count'  => (int)$r['sources_count'],
        'home_win'       => range_or_null($r['min_hw'],   $r['max_hw']),
        'draw'           => $is_tennis ? null : range_or_null($r['min_draw'], $r['max_draw']),
        'away_win'       => range_or_null($r['min_aw'],   $r['max_aw']),
        'player1_win'    => $is_tennis ? range_or_null($r['min_p1'], $r['max_p1']) : null,
        'player2_win'    => $is_tennis ? range_or_null($r['min_p2'], $r['max_p2']) : null,
    ];
}

json_out(200, $result);
