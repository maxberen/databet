<?php
require_once __DIR__ . '/_config.php';
cors_preflight();
json_out(200, ['status' => 'ok', 'time' => gmdate('c')]);
