<?php
// JWT HS256 mínimo — sin dependencias externas

function jwt_encode(array $payload, string $secret): string {
    $header  = base64url(json_encode(['alg' => 'HS256', 'typ' => 'JWT']));
    $payload = base64url(json_encode($payload));
    $sig     = base64url(hash_hmac('sha256', "$header.$payload", $secret, true));
    return "$header.$payload.$sig";
}

function jwt_decode(string $token, string $secret): array {
    $parts = explode('.', $token);
    if (count($parts) !== 3) throw new RuntimeException('Token malformado');

    [$header, $payload, $sig] = $parts;
    $expected = base64url(hash_hmac('sha256', "$header.$payload", $secret, true));

    if (!hash_equals($expected, $sig)) throw new RuntimeException('Firma inválida');

    $data = json_decode(base64_decode(strtr($payload, '-_', '+/')), true);
    if (isset($data['exp']) && $data['exp'] < time()) throw new RuntimeException('Token expirado');

    return $data;
}

function base64url(string $data): string {
    return rtrim(strtr(base64_encode($data), '+/', '-_'), '=');
}
