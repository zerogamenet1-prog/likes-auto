<?php
/**
 * Health + optional backend warm (use as cron every 10–14 min on free Render).
 * Example cron: curl -fsS https://likes-auto.com/ping.php >/dev/null
 */
header('Content-Type: application/json; charset=utf-8');

$cfg = @include __DIR__ . '/la-config.php';
$backend = is_array($cfg) ? (string)($cfg['backend_base'] ?? '') : '';
$warm = ['ok' => null, 'ms' => null, 'error' => null];

if ($backend !== '') {
    $url = rtrim($backend, '/') . '/health';
    $t0 = microtime(true);
    $ctx = stream_context_create([
        'http' => [
            'method' => 'GET',
            'timeout' => 25,
            'header' => "User-Agent: likes-auto-keepalive\r\n",
            'ignore_errors' => true,
        ],
    ]);
    $body = @file_get_contents($url, false, $ctx);
    $warm['ms'] = (int)round((microtime(true) - $t0) * 1000);
    if ($body === false) {
        $warm['ok'] = false;
        $warm['error'] = 'fetch_failed';
    } else {
        $j = json_decode($body, true);
        $warm['ok'] = is_array($j) ? (bool)($j['ok'] ?? false) : false;
    }
}

echo json_encode([
    'ok' => true,
    'php' => PHP_VERSION,
    'backend' => $backend,
    'warm' => $warm,
], JSON_UNESCAPED_UNICODE);
