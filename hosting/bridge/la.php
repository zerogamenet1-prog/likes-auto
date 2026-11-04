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

// ── Google Search Console Verification File Handler ──
if (preg_match('#^/google([a-zA-Z0-9_-]+)\.html$#', $path, $mG)) {
    header('Content-Type: text/html; charset=utf-8');
    echo 'google-site-verification: google' . $mG[1] . '.html';
    exit;
}

// ── IndexNow Key File Handler ──
if ($path === '/la7f3c9e2b1d8a4f6.txt') {
    header('Content-Type: text/plain; charset=utf-8');
    echo 'la7f3c9e2b1d8a4f6';
    exit;
}

// ── One-Click IndexNow Push for Search Engines ──
if ($path === '/admin/settings/seo/indexnow' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $urls = ['https://likes-auto.com/', 'https://likes-auto.com/services', 'https://likes-auto.com/blog', 'https://likes-auto.com/faq', 'https://likes-auto.com/terms', 'https://likes-auto.com/api'];
    $sitemaps = ['sitemap-blog.xml', 'sitemap-pages.xml', 'sitemap-platforms.xml'];
    foreach ($sitemaps as $sm) {
        $p = __DIR__ . '/' . $sm;
        if (file_exists($p)) {
            $xml = file_get_contents($p);
            if (preg_match_all('#<loc>([^<]+)</loc>#i', $xml, $matches)) {
                $urls = array_merge($urls, $matches[1]);
            }
        }
    }
    $urls = array_values(array_unique($urls));
    $cnt = count($urls);
    
    $payload = json_encode([
        'host' => 'likes-auto.com',
        'key' => 'la7f3c9e2b1d8a4f6',
        'keyLocation' => 'https://likes-auto.com/la7f3c9e2b1d8a4f6.txt',
        'urlList' => $urls
    ], JSON_UNESCAPED_SLASHES);
    
    $ch = curl_init('https://api.indexnow.org/indexnow');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json; charset=utf-8']);
    curl_setopt($ch, CURLOPT_TIMEOUT, 12);
    $res = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    $ok = ($code >= 200 && $code < 300);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode([
        'ok' => $ok,
        'http_code' => $code,
        'count' => $cnt,
        'message' => $ok ? "ส่ง {$cnt} URLs ไปยัง IndexNow (Bing/Yandex/Naver) เรียบร้อยแล้ว!" : "IndexNow ตอบกลับสถานะ {$code}",
        'submitted_at' => date('Y-m-d H:i:s')
    ], JSON_UNESCAPED_UNICODE);
    exit;
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


if ($code === 200 && strpos($path, '/admin/appearance/pages') === 0 && stripos($respBody, 'page-kpi-grid') === false) {
    $patchFile = __DIR__ . '/pages_card.php';
    if (is_file($patchFile)) {
        $defaultSnippets = [
            'faq' => 'รวมคำถามที่พบบ่อยเกี่ยวกับการสั่งซื้อ การเติมเงิน อัตราค่าบริการ และการใช้งานระบบ',
            'terms' => 'ข้อกำหนดและเงื่อนไขการใช้บริการของ LIKES AUTO เพื่อความเข้าใจที่ถูกต้องระหว่างผู้ให้บริการและผู้ใช้บริการ',
            'privacy' => 'นโยบายการคุ้มครองข้อมูลส่วนบุคคลและการรักษาความลับของลูกค้า LIKES AUTO',
            'about' => 'ผู้ให้บริการระบบการตลาดโซเชียลมีเดียอันดับ 1 ในไทย ด้วยระบบอัตโนมัติ 24 ชั่วโมง',
            'contact' => 'ช่องทางการติดต่อทีมงาน LIKES AUTO เพื่อช่วยเหลือและตอบคำถามตลอด 24 ชม.',
            'guide' => 'คู่มือขั้นตอนการเติมเงินและสั่งซื้อบริการต่างๆ บนระบบอย่างละเอียด',
        ];
        $pages = [];
        if (preg_match_all('#<tr>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td><a href="/p/([^"]*)"[^>]*>.*?</a></td>\s*<td class="adm-actions">\s*<a[^>]*edit=(\d+)#s', $respBody, $matches, PREG_SET_ORDER)) {
            foreach ($matches as $m) {
                $pSlug = trim(strip_tags($m[1]));
                $pTitle = trim(strip_tags($m[2]));
                $pId = trim($m[4]);
                $pages[] = [
                    'id' => $pId,
                    'slug' => $pSlug,
                    'title' => $pTitle,
                    'body' => $defaultSnippets[$pSlug] ?? 'หน้าเว็บคงที่สำหรับข้อมูลบริการและนโยบายของเว็บไซต์',
                ];
            }
        }
        $editing = null;
        if (preg_match('#<input type="hidden" name="pid" value="(\d+)">#s', $respBody, $mPid) && $mPid[1] !== '') {
            $eSlug = '';
            $eTitle = '';
            $eBody = '';
            if (preg_match('#name="slug"[^>]*value="([^"]*)"#', $respBody, $mS)) { $eSlug = $mS[1]; }
            if (preg_match('#name="title"[^>]*value="([^"]*)"#', $respBody, $mT)) { $eTitle = $mT[1]; }
            if (preg_match('#<textarea[^>]*name="body"[^>]*>(.*?)</textarea>#s', $respBody, $mB)) { $eBody = $mB[1]; }
            $editing = ['id' => $mPid[1], 'slug' => $eSlug, 'title' => $eTitle, 'body' => $eBody];
        }

        ob_start();
        include $patchFile;
        $newContent = ob_get_clean();

        if ($newContent !== false && $newContent !== '') {
            $navEnd = strpos($respBody, '</nav>');
            $mainEnd = strpos($respBody, '</main>', $navEnd);
            if ($navEnd !== false && $mainEnd !== false) {
                $respBody = substr($respBody, 0, $navEnd + 6) . "\n" . $newContent . "\n" . substr($respBody, $mainEnd);
            }
        }
    }
}


if ($code === 200 && strpos($path, '/admin/appearance/blog') === 0 && stripos($respBody, 'blog-kpi-grid') === false) {
    $patchFile = __DIR__ . '/blog_card.php';
    if (is_file($patchFile)) {
        $q = $_GET['q'] ?? '';
        $st = $_GET['st'] ?? '';

        $all_n = 0; $pub_n = 0; $draft_n = 0;
        if (preg_match('#(\d+)\s*·[^\d]+(\d+)\s*·[^\d]+(\d+)#u', $respBody, $mCounts)) {
            $all_n = (int)$mCounts[1];
            $pub_n = (int)$mCounts[2];
            $draft_n = (int)$mCounts[3];
        }

        $posts = [];
        $rowPattern = '#<tr>\s*<td class="wrap" data-label="[^"]*">(.*?)</td>\s*<td class="wrap" data-label="[^"]*">(.*?)</td>\s*<td data-label="[^"]*">(.*?)</td>\s*<td data-label="[^"]*">(.*?)</td>\s*<td class="adm-actions"[^>]*>(.*?)</td>\s*</tr>#s';
        if (preg_match_all($rowPattern, $respBody, $matches, PREG_SET_ORDER)) {
            foreach ($matches as $m) {
                $col1 = $m[1];
                $colTags = trim(strip_tags($m[2]));
                if ($colTags === '-') { $colTags = ''; }
                $colSt = $m[3];
                $colTime = trim(strip_tags($m[4]));
                $colAct = $m[5];

                $pCover = '';
                if (preg_match('#<img [^>]*src="([^"]*)"#', $col1, $mCov)) {
                    $pCover = $mCov[1];
                }
                $pTitle = '';
                if (preg_match('#<b>(.*?)</b>#s', $col1, $mTit)) {
                    $pTitle = trim(strip_tags($mTit[1]));
                }
                $pSlug = '';
                if (preg_match('#href="/blog/([^"]*)"#', $colAct, $mSlg)) {
                    $pSlug = trim($mSlg[1]);
                } elseif (preg_match('#<div class="la-muted">/blog/([^<]+)</div>#', $col1, $mSlg2)) {
                    $pSlug = trim($mSlg2[1]);
                }
                $pId = '';
                if (preg_match('#edit=(\d+)#', $colAct, $mId)) {
                    $pId = $mId[1];
                }
                $isPub = (stripos($colSt, 'completed') !== false || stripos($colSt, 'เผยแพร่') !== false) ? 1 : 0;

                $posts[] = [
                    'id' => $pId,
                    'title' => $pTitle,
                    'slug' => $pSlug,
                    'cover' => $pCover,
                    'tags' => $colTags,
                    'published' => $isPub,
                    'created_at' => $colTime,
                    'excerpt' => '',
                ];
            }
        }

        $editing = null;
        if (preg_match('#<input type="hidden" name="pid" [^>]*value="(\d+)"#s', $respBody, $mPid) && $mPid[1] !== '') {
            $eTitle = ''; $eSlug = ''; $eTags = ''; $eExcerpt = ''; $eCreated = ''; $eBody = ''; $ePub = 1;
            if (preg_match('#name="title"[^>]*value="([^"]*)"#', $respBody, $mT)) $eTitle = $mT[1];
            if (preg_match('#name="slug"[^>]*value="([^"]*)"#', $respBody, $mS)) $eSlug = $mS[1];
            if (preg_match('#name="tags"[^>]*value="([^"]*)"#', $respBody, $mTag)) $eTags = $mTag[1];
            if (preg_match('#name="excerpt"[^>]*value="([^"]*)"#', $respBody, $mExc)) $eExcerpt = $mExc[1];
            if (preg_match('#name="created_at"[^>]*value="([^"]*)"#', $respBody, $mCre)) $eCreated = $mCre[1];
            if (preg_match('#<textarea[^>]*name="body"[^>]*>(.*?)</textarea>#s', $respBody, $mB)) $eBody = $mB[1];
            if (preg_match('#name="published"[^>]*checked#', $respBody)) $ePub = 1;
            $editing = [
                'id' => $mPid[1],
                'title' => $eTitle,
                'slug' => $eSlug,
                'tags' => $eTags,
                'excerpt' => $eExcerpt,
                'created_at' => $eCreated,
                'body' => $eBody,
                'published' => $ePub
            ];
        }
        $show_form = (!empty($editing) || (isset($_GET['new']) && $_GET['new'] === '1'));
        $saved = (stripos($respBody, 'บันทึกบทความแล้ว') !== false || (isset($_GET['saved']) && $_GET['saved'] === '1'));

        $media = [];
        if (preg_match_all('#blogImg\(\'([^\']*)\'\)#', $respBody, $mMedia)) {
            $media = array_values(array_unique($mMedia[1]));
        }
        if (empty($media)) {
            $media = [
                '/static/assets/blog/blog-facebook.jpg',
                '/static/assets/blog/blog-tiktok.jpg',
                '/static/assets/blog/blog-instagram.jpg',
                '/static/assets/blog/blog-youtube.jpg',
                '/static/assets/blog/blog-ads.jpg',
                '/static/assets/blog/blog-brand.jpg',
                '/static/assets/blog/blog-likes.jpg',
                '/static/assets/blog/blog-live.jpg',
                '/static/assets/blog/blog-chart.jpg',
                '/static/assets/blog/blog-shop.jpg',
                '/static/assets/blog/blog-cafe.jpg',
                '/static/assets/blog/blog-beauty.jpg',
                '/static/assets/blog/blog-api.jpg',
                '/static/assets/blog/blog-plan.jpg',
                '/static/assets/blog/blog-student.jpg',
                '/static/assets/blog/blog-check.jpg',
                '/static/assets/blog/blog-comments.jpg',
                '/static/assets/blog/blog-restaurant.jpg',
                '/static/assets/blog/blog-budget.jpg',
                '/static/assets/blog/blog-order.jpg',
                '/static/assets/blog/blog-team.jpg',
                '/static/assets/blog/blog-funnel.jpg',
                '/static/assets/blog/blog-secure.jpg',
                '/static/assets/blog/blog-pay.jpg',
            ];
        }

        ob_start();
        include $patchFile;
        $newContent = ob_get_clean();

        if ($newContent !== false && $newContent !== '') {
            $navEnd = strpos($respBody, '</nav>');
            $mainEnd = strpos($respBody, '</main>', $navEnd);
            if ($navEnd !== false && $mainEnd !== false) {
                $respBody = substr($respBody, 0, $navEnd + 6) . "\n" . $newContent . "\n" . substr($respBody, $mainEnd);
            }
        }
    }
}


if ($code === 200 && (strpos($path, '/admin/settings/integrations') === 0 || (strpos($path, '/admin/settings') === 0 && isset($_GET['tab']) && $_GET['tab'] === 'integrations')) && stripos($respBody, 'la-seo-hub-card') === false) {
    $patchFile = __DIR__ . '/seo_card.php';
    if (is_file($patchFile)) {
        ob_start();
        include $patchFile;
        $seoHtml = ob_get_clean();
        
        if ($seoHtml !== false && $seoHtml !== '') {
            $target = '<form method="post" class="adm-form" style="margin-top:16px">';
            $pos = strpos($respBody, $target);
            if ($pos !== false) {
                $respBody = substr($respBody, 0, $pos) . $seoHtml . "\n" . substr($respBody, $pos);
            } else {
                $mainEnd = strrpos($respBody, '</main>');
                if ($mainEnd !== false) {
                    $respBody = substr($respBody, 0, $mainEnd) . "\n" . $seoHtml . "\n" . substr($respBody, $mainEnd);
                }
            }
        }
    }
}


if ($code === 200 && stripos($respBody, '<header class="la-header') !== false) {
    $drawerFile = __DIR__ . '/drawer_nav.php';
    if (is_file($drawerFile)) {
        $isUser = (stripos($respBody, 'la-dash-av') !== false || stripos($respBody, '/logout') !== false);
        $username = '';
        if (preg_match('#<span class="la-dash-av">([^<]+)</span>#', $respBody, $mU)) {
            $username = $mU[1];
        } elseif (preg_match('#href="/account">([^<]+)</a>#', $respBody, $mU2)) {
            $username = $mU2[1];
        }
        $balance = '0.00';
        if (preg_match('#(?:฿|&#3647;)\\s*([\\d,]+\\.?\\d*)#', $respBody, $mB)) {
            $balance = str_replace(',', '', $mB[1]);
        }
        $currentPage = trim($path, '/');
        
        ob_start();
        include $drawerFile;
        $newDrawer = ob_get_clean();
        
        if ($newDrawer !== false && $newDrawer !== '') {
            $pattern = '#(<div class="la-header-left">.*?</div>\\s*)(.*?)(\\s*<div class="la-tools">)#s';
            if (preg_match($pattern, $respBody, $mNav, PREG_OFFSET_CAPTURE)) {
                $pre = substr($respBody, 0, $mNav[2][1]);
                $post = substr($respBody, $mNav[2][1] + strlen($mNav[2][0]));
                
                // Enhance brand logo with Peakerr styling & skew in $pre
                $pre = preg_replace(
                    '#<a class="la-brand"[^>]*>.*?</a>#s',
                    '<a class="la-brand pk-brand" href="/"><span class="la-brand-mark pk-brand-mark" aria-hidden="true"><i class="ri-flashlight-fill"></i></span><span class="la-brand-text pk-brand-text">Likes<span>Auto</span></span></a>',
                    $pre
                );
                
                // Enhance Sign Up button with Peakerr rocket icon in $post
                $post = preg_replace(
                    '#<a class="la-btn la-btn-mini"[^>]*href="/signup"[^>]*>(?:<i[^>]*></i>\s*)?([^<]+)</a>#s',
                    '<a class="la-btn la-btn-mini pk-signup-btn" href="/signup"><i class="ri-rocket-fill"></i> $1</a>',
                    $post
                );
                
                // Enhance Theme Switcher to Sleek Executive Swatch Strip (แทบสีแบบเดิม สวยโมเดิร์น)
                $themeStripHtml = '<div class="la-pack-switch pk-theme-strip" role="group" aria-label="เลือกธีม">
  <span class="pk-theme-icon" title="เลือกธีมการแสดงผล"><i class="ri-palette-line"></i></span>
  <button type="button" class="pk-swatch-btn pk-swatch-peak" data-pack="peak" onclick="laSetPack(\'peak\')" title="Peakerr Lime" aria-label="Peakerr Lime" style="--sw:#051408;--sw2:#8ee31f;background:linear-gradient(135deg,#051408 0%,#369c0d 55%,#8ee31f 100%) !important;"></button>
  <button type="button" class="pk-swatch-btn pk-swatch-violet" data-pack="violet" onclick="laSetPack(\'violet\')" title="Night Violet" aria-label="Night Violet" style="--sw:#100622;--sw2:#a855f7;background:linear-gradient(135deg,#100622 0%,#6d1ec7 55%,#b45cf8 100%) !important;"></button>
  <button type="button" class="pk-swatch-btn pk-swatch-navy" data-pack="navy" onclick="laSetPack(\'navy\')" title="Midnight Navy" aria-label="Midnight Navy" style="--sw:#061228;--sw2:#3b82f6;background:linear-gradient(135deg,#061228 0%,#1a56bc 55%,#3b82f6 100%) !important;"></button>
  <button type="button" class="pk-swatch-btn pk-swatch-light" data-pack="light" onclick="laSetPack(\'light\')" title="Peakerr Soft (Light)" aria-label="Peakerr Soft (Light)" style="--sw:#e2f8dc;--sw2:#5eb516;background:linear-gradient(135deg,#ffffff 0%,#7ee634 50%,#2f9414 100%) !important;"></button>
</div>';

                if (stripos($post, 'pk-theme-strip') === false) {
                    if (stripos($post, 'la-theme-dropdown') !== false) {
                        $post = preg_replace(
                            '#<div class="la-theme-dropdown\\b[^"]*"[^>]*>.*?</div>\\s*</div>\\s*</div>#s',
                            $themeStripHtml,
                            $post,
                            1
                        );
                    } else {
                        $post = preg_replace(
                            '#<div class="la-pack-switch\\b[^"]*"[^>]*>.*?</div>#s',
                            $themeStripHtml,
                            $post,
                            1
                        );
                    }
                }
                
                $respBody = $pre . "\n" . $newDrawer . "\n" . $post;
                
                // Inject helper script for theme strip if not present
                if (stripos($respBody, 'window.laSyncPack') === false && stripos($respBody, '</body>') !== false) {
                    $themeJs = '<script>
(function(){
  window.laSyncPack = function(pack){
    pack = pack || document.documentElement.getAttribute("data-la-pack") || "peak";
    document.querySelectorAll(".la-pack-switch [data-pack]").forEach(function(b){
      var on = b.getAttribute("data-pack") === pack;
      b.classList.toggle("is-on", on);
      b.classList.toggle("active", on);
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });
    document.querySelectorAll(".pk-theme-card").forEach(function(c){
      var on = c.getAttribute("onclick") && c.getAttribute("onclick").indexOf(pack) !== -1;
      c.classList.toggle("active", on);
    });
  };
  var origSetPack = window.laSetPack;
  window.laSetPack = function(pack){
    if (typeof origSetPack === "function") {
      origSetPack(pack);
    } else {
      var allowed = {peak:1, violet:1, navy:1, light:1};
      if (!allowed[pack]) pack = "peak";
      var root = document.documentElement;
      root.setAttribute("data-la-pack", pack);
      root.classList.toggle("la-light", pack === "light");
      try {
        localStorage.setItem("la-pack", pack);
        localStorage.setItem("la-theme", pack === "light" ? "light" : "dark");
        document.cookie = "la_pack=" + pack + ";path=/;max-age=31536000";
      } catch (e) {}
    }
    laSyncPack(pack);
  };
  window.laSelectTheme = function(pack, e){
    if (e) e.stopPropagation();
    laSetPack(pack);
  };
  setTimeout(function(){ laSyncPack(); }, 30);
  document.addEventListener("DOMContentLoaded", function(){ laSyncPack(); });
})();
</script>';
                    $respBody = str_ireplace('</body>', $themeJs . "\n</body>", $respBody);
                }
            }
        }
    }
}

// ── STYLE 6: GOOGLE-FIRST LOGIN CARD ENHANCEMENT ──
if ($code === 200 && stripos($respBody, 'la-login-style-6') === false && stripos($respBody, 'la-login-card') !== false) {
    // 1) Home page Hero Login aside
    if (preg_match('#<aside class="la-hero-login la-login-card(?: la-login-fz)?"[^>]*>(.*?)</aside>#s', $respBody, $mHome)) {
        $oldHomeCard = $mHome[0];
        $inner = $mHome[1];
        
        $guardFields = '';
        if (preg_match('#<input type="hidden" name="_csrf" value="([^"]+)">#', $inner, $mCsrf)) {
            $guardFields .= $mCsrf[0] . "\n";
        }
        if (preg_match('#<p class="la-hp".*?</p>#s', $inner, $mHp)) {
            $guardFields .= $mHp[0] . "\n";
        }
        
        $hasGoogle = (stripos($inner, 'href="/google-login"') !== false);
        $googleBlock = '';
        if ($hasGoogle) {
            $googleBlock = '
        <!-- Style 6: Google-First Spotlight Button -->
        <a class="la-google-btn la-google-spotlight" href="/google-login">
          <svg viewBox="0 0 48 48" width="22" height="22" aria-hidden="true">
            <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.1 8 3l5.7-5.7C34.2 6.1 29.4 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.3-.4-3.5z"/>
            <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16 19 12 24 12c3.1 0 5.8 1.1 8 3l5.7-5.7C34.2 6.1 29.4 4 24 4 16.3 4 9.6 8.3 6.3 14.7z"/>
            <path fill="#4CAF50" d="M24 44c5.2 0 10-2 13.6-5.2l-6.3-5.2C29.2 35.1 26.7 36 24 36c-5.3 0-9.7-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z"/>
            <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-1.1 3.2-3.5 5.8-6.7 7.3l6.3 5.2C37.5 38.4 44 33 44 24c0-1.3-.1-2.3-.4-3.5z"/>
          </svg>
          <span>เข้าสู่ระบบด้วย Google ทันที</span>
        </a>

        <div class="la-or la-google-first-divider"><span>หรือใช้ชื่อผู้ใช้และรหัสผ่าน</span></div>';
        }
        
        $newHomeCard = '<aside class="la-hero-login la-login-card la-login-style-6">
        <div class="la-login-hi">
          <h3>ยินดีต้อนรับกลับ</h3>
          <p>เข้าสู่ระบบเพื่อใช้งานแดชบอร์ดใน 1 คลิก</p>
        </div>' . $googleBlock . '

        <form method="post" action="/signin/" id="laHomeLogin" class="la-login-fz-form">
          ' . $guardFields . '
          <label class="la-field" for="laHomeUser">ชื่อผู้ใช้</label>
          <div class="la-input-ico la-input-ico-start">
            <i class="ri-user-3-line la-field-ico"></i>
            <input class="la-input" id="laHomeUser" type="text" name="username" required autocomplete="username" placeholder="ชื่อผู้ใช้" autocapitalize="off" spellcheck="false">
          </div>

          <label class="la-field" for="laHomePass">รหัสผ่าน</label>
          <div class="la-input-ico la-input-ico-start la-input-ico-end">
            <i class="ri-lock-line la-field-ico"></i>
            <input class="la-input" type="password" name="password" required autocomplete="current-password" placeholder="รหัสผ่าน" id="laHomePass">
            <button class="la-pass-eye" type="button" id="laHomeEye" aria-label="แสดงรหัสผ่าน"><i class="ri-eye-line"></i></button>
          </div>

          <div class="la-login-row">
            <label><input type="checkbox" name="remember" value="1"> จดจำฉัน</label>
            <a href="/forgot">ลืมรหัสผ่าน?</a>
          </div>

          <button class="la-btn la-login-submit pk-submit-btn" type="submit">
            <i class="ri-login-circle-fill"></i> เข้าสู่ระบบด้วยรหัสผ่าน
          </button>
        </form>

        <p class="la-login-foot">ยังไม่มีบัญชี? <a href="/signup">สมัครสมาชิกฟรี</a></p>
      </aside>';

        $respBody = str_replace($oldHomeCard, $newHomeCard, $respBody);
    }
    
    // 2) Dedicated Signin page card
    if (preg_match('#<div class="la-auth-card la-login-card(?: la-login-fz)?"[^>]*>(.*?)</div>\s*</div>\s*</div>\s*</main>#s', $respBody, $mSignin)) {
        $oldSigninCard = $mSignin[0];
        $inner = $mSignin[1];
        
        $errorHtml = '';
        if (preg_match('#<div class="adm-error">(.*?)</div>#s', $inner, $mErr)) {
            $errorHtml = $mErr[0];
        }
        
        $guardFields = '';
        if (preg_match('#<input type="hidden" name="_csrf" value="([^"]+)">#', $inner, $mCsrf)) {
            $guardFields .= $mCsrf[0] . "\n";
        }
        if (preg_match('#<p class="la-hp".*?</p>#s', $inner, $mHp)) {
            $guardFields .= $mHp[0] . "\n";
        }
        
        $hasGoogle = (stripos($inner, 'href="/google-login"') !== false);
        $googleBlock = '';
        if ($hasGoogle) {
            $googleBlock = '
        <!-- Style 6: Google-First Spotlight Button -->
        <a class="la-google-btn la-google-spotlight" href="/google-login">
          <svg viewBox="0 0 48 48" width="22" height="22" aria-hidden="true">
            <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.1 8 3l5.7-5.7C34.2 6.1 29.4 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.3-.4-3.5z"/>
            <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16 19 12 24 12c3.1 0 5.8 1.1 8 3l5.7-5.7C34.2 6.1 29.4 4 24 4 16.3 4 9.6 8.3 6.3 14.7z"/>
            <path fill="#4CAF50" d="M24 44c5.2 0 10-2 13.6-5.2l-6.3-5.2C29.2 35.1 26.7 36 24 36c-5.3 0-9.7-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z"/>
            <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-1.1 3.2-3.5 5.8-6.7 7.3l6.3 5.2C37.5 38.4 44 33 44 24c0-1.3-.1-2.3-.4-3.5z"/>
          </svg>
          <span>เข้าสู่ระบบด้วย Google ทันที</span>
        </a>

        <div class="la-or la-google-first-divider"><span>หรือใช้ชื่อผู้ใช้และรหัสผ่าน</span></div>';
        }
        
        $newSigninCard = '<div class="la-auth-card la-login-card la-login-style-6">
        <div class="la-login-hi">
          <h1 class="la-auth-card-title">ยินดีต้อนรับกลับ</h1>
          <p class="la-auth-card-lead">เข้าสู่ระบบเพื่อใช้งานแดชบอร์ดใน 1 คลิก</p>
        </div>
        ' . $errorHtml . '
        ' . $googleBlock . '

        <form method="post" action="/signin/" id="laSigninForm" class="la-login-fz-form la-auth-form">
          ' . $guardFields . '
          <label class="la-field" for="siUser">ชื่อผู้ใช้</label>
          <div class="la-input-ico la-input-ico-start">
            <i class="ri-user-3-line la-field-ico"></i>
            <input class="la-input" id="siUser" type="text" name="username" required autocomplete="username" placeholder="ชื่อผู้ใช้" autocapitalize="off" spellcheck="false" enterkeyhint="next">
          </div>

          <label class="la-field" for="siPass">รหัสผ่าน</label>
          <div class="la-input-ico la-input-ico-start la-input-ico-end">
            <i class="ri-lock-line la-field-ico"></i>
            <input class="la-input" id="siPass" type="password" name="password" required autocomplete="current-password" placeholder="รหัสผ่าน" enterkeyhint="done">
            <button class="la-pass-eye" type="button" id="siEye" aria-label="แสดงรหัสผ่าน"><i class="ri-eye-line"></i></button>
          </div>

          <div class="la-login-row">
            <label><input type="checkbox" name="remember" value="1"> จดจำฉัน</label>
            <a href="/forgot">ลืมรหัสผ่าน?</a>
          </div>

          <button class="la-btn la-login-submit pk-submit-btn" type="submit">
            <i class="ri-login-circle-fill"></i> เข้าสู่ระบบด้วยรหัสผ่าน
          </button>
        </form>

        <p class="la-login-foot">ยังไม่มีบัญชี? <a href="/signup">สมัครสมาชิกฟรี</a></p>
      </div>
    </div>
  </div>
</main>';

        $respBody = str_replace($oldSigninCard, $newSigninCard, $respBody);
    }
}

// Bump pages.css to v=pro116 so browser/CDN bypasses cached CSS
if ($code === 200 && stripos($respBody, 'pages.css?v=') !== false) {
    $respBody = preg_replace('#pages\.css\?v=[a-zA-Z0-9_-]+#', 'pages.css?v=pro117', $respBody);
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
