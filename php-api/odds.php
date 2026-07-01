<?php
require_once __DIR__ . '/_config.php';
require_once __DIR__ . '/_auth.php';

cors_preflight();
require_auth();

$match_id = (int)($_GET['id'] ?? 0);
if (!$match_id) json_out(400, ['detail' => 'Falta id.']);

$db = db();

$match = $db->prepare("SELECT * FROM matches WHERE id = :id");
$match->execute([':id' => $match_id]);
$match = $match->fetch();
if (!$match) json_out(404, ['detail' => 'Partido no encontrado.']);

// Todos los match_ids del mismo partido real
$same = $db->prepare("
    SELECT id FROM matches
    WHERE home_team = :home AND away_team = :away AND match_datetime = :dt
");
$same->execute([':home' => $match['home_team'], ':away' => $match['away_team'], ':dt' => $match['match_datetime']]);
$same_ids = array_column($same->fetchAll(), 'id');

if (!$same_ids) json_out(200, []);

$placeholders = implode(',', array_fill(0, count($same_ids), '?'));

// Último match_id por source
$latest = $db->prepare("
    SELECT MAX(id) AS match_id FROM matches
    WHERE id IN ($placeholders)
    GROUP BY source_id
");
$latest->execute($same_ids);
$latest_ids = array_column($latest->fetchAll(), 'match_id');

if (!$latest_ids) json_out(200, []);

$ph2 = implode(',', array_fill(0, count($latest_ids), '?'));

$odds = $db->prepare("
    SELECT o.*, s.name AS source_name
    FROM odds o
    JOIN sources s ON s.id = o.source_id
    WHERE o.match_id IN ($ph2)
    ORDER BY s.name, o.bookmaker
");
$odds->execute($latest_ids);

function to_local(string $dt): string {
    $ts = strtotime($dt) + TIMEZONE_OFFSET * 3600;
    return date('Y-m-d\TH:i:s', $ts);
}

$odds_list = [];
foreach ($odds->fetchAll() as $o) {
    $odds_list[] = [
        'source'       => $o['source_name'],
        'bookmaker'    => $o['bookmaker'],
        'home_win'     => $o['home_win']     !== null ? (float)$o['home_win']     : null,
        'draw'         => $o['draw']         !== null ? (float)$o['draw']         : null,
        'away_win'     => $o['away_win']     !== null ? (float)$o['away_win']     : null,
        'player1_win'  => $o['player1_win']  !== null ? (float)$o['player1_win']  : null,
        'player2_win'  => $o['player2_win']  !== null ? (float)$o['player2_win']  : null,
        'scraped_at'   => to_local($o['scraped_at']),
    ];
}

json_out(200, [
    'id'             => (int)$match['id'],
    'sport'          => $match['sport'],
    'competition'    => $match['competition'],
    'home_team'      => $match['home_team'],
    'away_team'      => $match['away_team'],
    'match_datetime' => to_local($match['match_datetime']),
    'odds'           => $odds_list,
]);
