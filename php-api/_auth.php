<?php
require_once __DIR__ . '/_jwt.php';
require_once __DIR__ . '/_config.php';

// Rate limiting en tabla MySQL
// CREATE TABLE IF NO EXISTS rate_limits (ip VARCHAR(45) PRIMARY KEY, attempts INT DEFAULT 0, locked_until DATETIME NULL);

function rate_limit_check(string $ip): void {
    $db = db();
    $db->exec("CREATE TABLE IF NOT EXISTS rate_limits (
        ip VARCHAR(45) PRIMARY KEY,
        attempts INT DEFAULT 0,
        locked_until DATETIME NULL
    )");

    $row = $db->query("SELECT * FROM rate_limits WHERE ip = " . $db->quote($ip))->fetch();

    if ($row && $row['locked_until'] !== null) {
        $locked = strtotime($row['locked_until']);
        if (time() < $locked) {
            $remaining = (int)(($locked - time()) / 60) + 1;
            json_out(429, ['detail' => "Cuenta suspendida. Intentá en $remaining minutos."]);
        }
        // Bloqueo expiró — resetear
        $db->exec("UPDATE rate_limits SET attempts=0, locked_until=NULL WHERE ip=" . $db->quote($ip));
    }
}

function rate_limit_fail(string $ip): void {
    $db = db();
    $db->exec("INSERT INTO rate_limits (ip, attempts) VALUES (" . $db->quote($ip) . ", 1)
               ON DUPLICATE KEY UPDATE attempts = attempts + 1");

    $row = $db->query("SELECT attempts FROM rate_limits WHERE ip=" . $db->quote($ip))->fetch();
    $attempts = (int)$row['attempts'];

    if ($attempts >= MAX_ATTEMPTS) {
        $until = date('Y-m-d H:i:s', time() + LOCKOUT_MINUTES * 60);
        $db->exec("UPDATE rate_limits SET locked_until=" . $db->quote($until) . " WHERE ip=" . $db->quote($ip));
        json_out(429, ['detail' => "Demasiados intentos. Cuenta suspendida por " . LOCKOUT_MINUTES . " minutos."]);
    }

    $remaining = MAX_ATTEMPTS - $attempts;
    json_out(401, ['detail' => "Credenciales incorrectas. Intentos restantes: $remaining."]);
}

function rate_limit_ok(string $ip): void {
    db()->exec("UPDATE rate_limits SET attempts=0, locked_until=NULL WHERE ip=" . db()->quote($ip));
}

function require_auth(): string {
    $header = $_SERVER['HTTP_AUTHORIZATION'] ?? $_SERVER['REDIRECT_HTTP_AUTHORIZATION'] ?? '';
    if (!str_starts_with($header, 'Bearer ')) {
        json_out(401, ['detail' => 'Token requerido.']);
    }
    $token = substr($header, 7);
    try {
        $payload = jwt_decode($token, JWT_SECRET);
        return $payload['sub'] ?? '';
    } catch (RuntimeException) {
        json_out(401, ['detail' => 'Token inválido o expirado.']);
    }
}
