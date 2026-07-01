<?php
// Cargá estas variables en tu cPanel → PHP → Environment Variables
// o en un .env.php local que no se commitea

define('DB_HOST',         getenv('DB_HOST')         ?: '127.0.0.1');
define('DB_NAME',         getenv('DB_NAME')         ?: 'bets');
define('DB_USER',         getenv('DB_USER')         ?: 'root');
define('DB_PASS',         getenv('DB_PASS')         ?: '');
define('TIMEZONE_OFFSET', (int)(getenv('TIMEZONE_OFFSET') ?: -4));
define('AUTH_USER',       getenv('AUTH_USER')       ?: '');
define('AUTH_SALT',       getenv('AUTH_SALT')       ?: '');
define('AUTH_HASH',       getenv('AUTH_HASH')       ?: '');
define('JWT_SECRET',      getenv('JWT_SECRET')      ?: '');

define('MAX_ATTEMPTS',    5);
define('LOCKOUT_MINUTES', 60);
define('TOKEN_EXPIRE_H',  12);

function db(): PDO {
    static $pdo;
    if (!$pdo) {
        $dsn = 'mysql:host=' . DB_HOST . ';dbname=' . DB_NAME . ';charset=utf8mb4';
        $pdo = new PDO($dsn, DB_USER, DB_PASS, [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);
    }
    return $pdo;
}

function json_out(int $status, mixed $data): never {
    http_response_code($status);
    header('Content-Type: application/json');
    header('Access-Control-Allow-Origin: *');
    header('Access-Control-Allow-Headers: Authorization, Content-Type');
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

function cors_preflight(): void {
    if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
        header('Access-Control-Allow-Origin: *');
        header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
        header('Access-Control-Allow-Headers: Authorization, Content-Type');
        http_response_code(204);
        exit;
    }
}
