<?php
/**
 * Accept a SQLite backup upload from the Render app and store it as the
 * official restore file for the next Free-plan redeploy.
 *
 * Auth: header X-LA-DB-TOKEN must match token in la-config.php
 */
declare(strict_types=1);

$config = require __DIR__ . '/la-config.php';
$token = (string) ($config['db_backup_token'] ?? '');
$got = (string) ($_SERVER['HTTP_X_LA_DB_TOKEN'] ?? '');
if ($token === '' || !hash_equals($token, $got)) {
    http_response_code(401);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['ok' => false, 'error' => 'unauthorized']);
    exit;
}

$raw = file_get_contents('php://input');
if ($raw === false || strlen($raw) < 1024) {
    http_response_code(400);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['ok' => false, 'error' => 'empty_body']);
    exit;
}
// SQLite header magic
if (strncmp($raw, 'SQLite format 3', 15) !== 0) {
    http_response_code(400);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['ok' => false, 'error' => 'not_sqlite']);
    exit;
}

$name = (string) ($config['db_restore_name'] ?? '.la-db-restore-d1qyg5az73cs4unx8jl9trbw.db');
$path = __DIR__ . '/' . $name;
$tmp = $path . '.tmp';
if (file_put_contents($tmp, $raw) === false) {
    http_response_code(500);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['ok' => false, 'error' => 'write_failed']);
    exit;
}
rename($tmp, $path);
@chmod($path, 0644);

http_response_code(200);
header('Content-Type: application/json; charset=utf-8');
echo json_encode([
    'ok' => true,
    'bytes' => strlen($raw),
    'file' => $name,
], JSON_UNESCAPED_UNICODE);
