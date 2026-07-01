<?php
require_once __DIR__ . '/_config.php';
require_once __DIR__ . '/_jwt.php';
require_once __DIR__ . '/_auth.php';

cors_preflight();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') json_out(405, ['detail' => 'Método no permitido.']);

$body = json_decode(file_get_contents('php://input'), true);
$email    = trim($body['email']    ?? '');
$password = trim($body['password'] ?? '');
$ip       = $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';

rate_limit_check($ip);

$hash = hash('sha256', AUTH_SALT . $password);
if ($email !== AUTH_USER || $hash !== AUTH_HASH) {
    rate_limit_fail($ip);
}

rate_limit_ok($ip);

$expire = time() + TOKEN_EXPIRE_H * 3600;
$token  = jwt_encode(['sub' => $email, 'exp' => $expire], JWT_SECRET);

json_out(200, ['access_token' => $token, 'token_type' => 'bearer']);
