<?php
/**
 * Apache bridge: forward non-static requests to the Python FastAPI backend.
 */
declare(strict_types=1);

$config = require __DIR__ . '/la-config.php';
$base = rtrim((string) ($config['backend_base'] ?? ''), '/');
$host = (string) ($config['backend_host'] ?? 'likes-auto.com');

$uri = $_SERVER['REQUEST_URI'] ?? '/';
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

if ($base === '') {
    if ($method === 'GET' || $method === 'HEAD') {
        $path = parse_url($uri, PHP_URL_PATH) ?: '/';
        if ($path !== '/' && substr($path, -1) === '/') {
            $path = rtrim($path, '/');
        }
        $candidates = [];
        if ($path === '/' || $path === '') {
            $candidates[] = __DIR__ . '/index.html';
        } else {
            $candidates[] = __DIR__ . $path . '/index.html';
            $candidates[] = __DIR__ . $path;
        }
        foreach ($candidates as $file) {
            if (is_file($file)) {
                if (str_ends_with($file, '.html')) {
                    header('Content-Type: text/html; charset=utf-8');
                }
                if ($method === 'HEAD') {
                    exit;
                }
                readfile($file);
                exit;
            }
        }
        http_response_code(404);
        header('Content-Type: text/html; charset=utf-8');
        echo '<!DOCTYPE html><html lang="th"><head><meta charset="utf-8"><title>ไม่พบหน้า</title></head>';
        echo '<body style="font-family:sans-serif;background:#070512;color:#eee;padding:2rem;max-width:42rem">';
        echo '<h1>ไม่พบหน้านี้</h1>';
        echo '<p><a href="/" style="color:#7dd3fc">กลับหน้าแรก</a></p></body></html>';
        exit;
    }
    http_response_code(503);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode([
        'ok' => false,
        'error' => 'backend_not_configured',
        'message' => 'ตั้งค่า backend ใน la-config.php หรือเปิด Python app บนโฮสต์',
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

$path = parse_url($uri, PHP_URL_PATH) ?: '/';
$query = parse_url($uri, PHP_URL_QUERY);
if ($path !== '/' && substr($path, -1) === '/') {
    $path = rtrim($path, '/');
}
$forwardUri = $path . ($query !== null && $query !== '' ? ('?' . $query) : '');
$url = $base . $forwardUri;
$headers = [];
$skip = ['host', 'connection', 'content-length', 'accept-encoding', 'content-type'];
foreach ($_SERVER as $key => $value) {
    if (strpos($key, 'HTTP_') !== 0) {
        continue;
    }
    $name = str_replace('_', '-', strtolower(substr($key, 5)));
    if (in_array($name, $skip, true)) {
        continue;
    }
    $headers[] = $name . ': ' . $value;
}
$upstreamHost = (string) (parse_url($base, PHP_URL_HOST) ?: $host);
$headers[] = 'Host: ' . $upstreamHost;
$headers[] = 'X-Forwarded-Proto: ' . ((!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http');
$headers[] = 'X-Forwarded-Host: ' . ($host ?: ($_SERVER['HTTP_HOST'] ?? 'likes-auto.com'));
// Prefer real visitor IP (CF / proxy). Never rate-limit the whole site on the edge IP.
$clientIp = '';
if (!empty($_SERVER['HTTP_CF_CONNECTING_IP'])) {
    $clientIp = trim((string) $_SERVER['HTTP_CF_CONNECTING_IP']);
} elseif (!empty($_SERVER['HTTP_TRUE_CLIENT_IP'])) {
    $clientIp = trim((string) $_SERVER['HTTP_TRUE_CLIENT_IP']);
} elseif (!empty($_SERVER['HTTP_X_FORWARDED_FOR'])) {
    $clientIp = trim(explode(',', (string) $_SERVER['HTTP_X_FORWARDED_FOR'])[0]);
}
if ($clientIp === '') {
    $clientIp = (string) ($_SERVER['REMOTE_ADDR'] ?? '127.0.0.1');
}
$headers[] = 'X-Forwarded-For: ' . $clientIp;
$headers[] = 'X-Real-IP: ' . $clientIp;
if (str_contains($base, 'loca.lt') || str_contains($base, 'trycloudflare.com')) {
    $headers[] = 'Bypass-Tunnel-Reminder: true';
}

$contentType = (string) ($_SERVER['CONTENT_TYPE'] ?? $_SERVER['HTTP_CONTENT_TYPE'] ?? '');
$isMultipart = $method !== 'GET' && $method !== 'HEAD' && (
    !empty($_FILES) || stripos($contentType, 'multipart/form-data') !== false
);

$ch = curl_init($url);
$opts = [
    CURLOPT_CUSTOMREQUEST => $method,
    CURLOPT_HTTPHEADER => $headers,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HEADER => true,
    CURLOPT_FOLLOWLOCATION => false,
    CURLOPT_TIMEOUT => 120,
];

if ($isMultipart) {
    // php://input is empty for multipart; rebuild from $_POST/$_FILES so slip uploads reach Render.
    $fields = [];
    foreach ($_POST as $key => $value) {
        $fields[$key] = $value;
    }
    foreach ($_FILES as $key => $file) {
        if (!is_array($file) || !isset($file['name'])) {
            continue;
        }
        if (is_array($file['name'])) {
            $count = count($file['name']);
            for ($i = 0; $i < $count; $i++) {
                $err = $file['error'][$i] ?? UPLOAD_ERR_NO_FILE;
                $tmp = $file['tmp_name'][$i] ?? '';
                $name = $file['name'][$i] ?? 'file.bin';
                $type = $file['type'][$i] ?? 'application/octet-stream';
                if ((int) $err === UPLOAD_ERR_OK && $tmp !== '' && is_uploaded_file($tmp)) {
                    $fields[$key . '[' . $i . ']'] = new CURLFile($tmp, $type ?: 'application/octet-stream', $name);
                }
            }
            continue;
        }
        $err = $file['error'] ?? UPLOAD_ERR_NO_FILE;
        $tmp = $file['tmp_name'] ?? '';
        $name = $file['name'] ?? 'file.bin';
        $type = $file['type'] ?? 'application/octet-stream';
        if ((int) $err === UPLOAD_ERR_OK && $tmp !== '' && is_uploaded_file($tmp)) {
            $fields[$key] = new CURLFile($tmp, $type ?: 'application/octet-stream', $name);
        }
    }
    $opts[CURLOPT_POSTFIELDS] = $fields;
} else {
    $body = file_get_contents('php://input');
    $opts[CURLOPT_POSTFIELDS] = $body !== false ? $body : null;
    if ($method !== 'GET' && $method !== 'HEAD' && $contentType !== '') {
        $opts[CURLOPT_HTTPHEADER] = array_merge($headers, ['Content-Type: ' . $contentType]);
    }
}

curl_setopt_array($ch, $opts);

$raw = curl_exec($ch);
if ($raw === false) {
    http_response_code(502);
    header('Content-Type: text/plain; charset=utf-8');
    echo 'Backend unreachable: ' . curl_error($ch);
    curl_close($ch);
    exit;
}
$code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
$headerSize = (int) curl_getinfo($ch, CURLINFO_HEADER_SIZE);
curl_close($ch);

$rawHeaders = substr($raw, 0, $headerSize);
$respBody = substr($raw, $headerSize);

// Patch dynamic templates if live backend is running older container build
if ($code === 200 && strpos($path, '/admin/services') === 0 && stripos($respBody, '<section class="adm-card svc-rate-card">') !== false && stripos($respBody, 'svc-unified-rate-card') === false) {
    $patchFile = __DIR__ . '/svc_rate_card.html';
    if (is_file($patchFile)) {
        $patchHtml = file_get_contents($patchFile);
        if ($patchHtml !== false && $patchHtml !== '') {
            if (preg_match('/1 USD = ([\d\.]+) บาท/', $respBody, $mRate)) {
                $patchHtml = str_replace('1 USD = 35.0 บาท', '1 USD = ' . $mRate[1] . ' บาท', $patchHtml);
            }
            $rStart = strpos($respBody, '<section class="adm-card svc-rate-card">');
            $rEnd = strpos($respBody, '</section>', $rStart);
            if ($rStart !== false && $rEnd !== false) {
                $respBody = substr($respBody, 0, $rStart) . $patchHtml . substr($respBody, $rEnd + strlen('</section>'));
            }
        }
    }
}

if ($code === 200 && strpos($path, '/admin/providers') === 0 && stripos($respBody, 'prov-kpi-grid') === false) {
    $patchFile = __DIR__ . '/prov_card.php';
    if (is_file($patchFile)) {
        $providers = [];
        if (preg_match_all('#<tr>\s*<td>(\d+)</td>\s*<td>(.*?)</td>\s*<td class="wrap">(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>#s', $respBody, $matches, PREG_SET_ORDER)) {
            foreach ($matches as $m) {
                $balParts = preg_split('/\s+/', trim(strip_tags($m[4])));
                $providers[] = [
                    'id' => trim($m[1]),
                    'name' => trim(strip_tags($m[2])),
                    'api_url' => trim(strip_tags($m[3])),
                    'balance' => $balParts[0] ?? '0.00',
                    'currency' => $balParts[1] ?? 'USD',
                    'created_at' => trim(strip_tags($m[5])),
                ];
            }
        }
        $editing = null;
        if (preg_match('#<input type="hidden" name="pid" value="(\d+)">#s', $respBody, $mPid) && $mPid[1] !== '') {
            $eName = '';
            $eUrl = '';
            if (preg_match('#name="name"\s+value="([^"]*)"#', $respBody, $mName)) { $eName = $mName[1]; }
            if (preg_match('#name="api_url"\s+value="([^"]*)"#', $respBody, $mUrl)) { $eUrl = $mUrl[1]; }
            $editing = ['id' => $mPid[1], 'name' => $eName, 'api_url' => $eUrl];
        }
        $saved = stripos($respBody, 'บันทึกแล้ว') !== false;
        $imported = '';
        if (preg_match('#ดึงบริการแล้ว\s+(\d+)\s+รายการ#u', $respBody, $mImp)) {
            $imported = $mImp[1];
        }
        $error = '';
        if (preg_match('#<div class="adm-error">(.*?)</div>#s', $respBody, $mErr)) {
            $error = trim(strip_tags($mErr[1]));
        }

        ob_start();
        include $patchFile;
        $newContent = ob_get_clean();

        if ($newContent !== false && $newContent !== '') {
            $mStart = strpos($respBody, '<main class="dash-content">');
            $mEnd = strpos($respBody, '</main>', $mStart);
            if ($mStart !== false && $mEnd !== false) {
                $respBody = substr($respBody, 0, $mStart) . '<main class="dash-content">' . $newContent . substr($respBody, $mEnd);
            }
        }
    }
}

http_response_code($code);
foreach (preg_split("/\r\n|\n|\r/", $rawHeaders) as $line) {
    if ($line === '' || stripos($line, 'HTTP/') === 0) {
        continue;
    }
    if (stripos($line, 'transfer-encoding:') === 0 || stripos($line, 'content-length:') === 0) {
        continue;
    }
    header($line, false);
}
header('Content-Length: ' . strlen($respBody));
echo $respBody;
