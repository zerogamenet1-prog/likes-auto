<?php
/**
 * LikesAuto Studio High-Performance API Bridge
 * Handles AI Script Generation & Neural Thai Voice Synthesis (TTS)
 */

header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

$action = $_GET['action'] ?? ($_POST['action'] ?? '');
$apiKey = "AQ.Ab8RN6JtS2uT4N631hV272r2i727qJt2L2491bS8S2v1jqvuA";

// Try reading local .env if available
$envPaths = [__DIR__ . '/.env', dirname(__DIR__) . '/.env', dirname(dirname(__DIR__)) . '/.env'];
foreach ($envPaths as $p) {
    if (file_exists($p)) {
        $lines = file($p, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        foreach ($lines as $line) {
            if (strpos(trim($line), 'GEMINI_API_KEY=') === 0) {
                $val = trim(substr(trim($line), 15), " \"'");
                if (strlen($val) > 10) {
                    $apiKey = $val;
                    break 2;
                }
            }
        }
    }
}

// -------------------------------------------------------------
// ACTION: SCRIPT (Generate Tailored Thai Sales Script from Video & Product)
// -------------------------------------------------------------
if ($action === 'script') {
    header('Content-Type: application/json; charset=utf-8');
    $product = trim($_GET['product'] ?? ($_POST['product'] ?? ''));
    $frameData = $_POST['frame'] ?? '';
    $style = trim($_GET['style'] ?? ($_POST['style'] ?? 'creator_viral'));

    $cleanProd = mb_substr($product, 0, 80);
    $lines = preg_split('/[\n,]+/', $product);
    $mainName = trim($lines[0]);
    if (mb_strlen($mainName) > 40) {
        $mainName = mb_substr($mainName, 0, 40);
    }
    if (empty($mainName)) {
        $mainName = 'สินค้าคุณภาพพรีเมียม';
    }

    $parts = [];
    if (!empty($frameData)) {
        $cleanB64 = preg_replace('#^data:image/\w+;base64,#i', '', $frameData);
        $parts[] = [
            "inlineData" => [
                "mimeType" => "image/jpeg",
                "data" => $cleanB64
            ]
        ];
        $prompt = "You are an elite Thai viral video marketer on TikTok and Facebook Reels.\n" .
            "Look at this exact video frame carefully. Identify the exact product, brand, model, color and features shown in the video.\n" .
            "Write a natural, high-converting Thai sales script matching this exact video 100% (duration ~22-26 seconds, around 55-70 words).\n" .
            ($product ? "Seller note: {$product}\n\n" : "\n") .
            "Return STRICTLY a JSON object with this exact schema (no markdown formatting, no backticks):\n" .
            "{\n" .
            "  \"detected_product\": \"ชื่อสินค้าและแบรนด์ที่เห็นในภาพจริง\",\n" .
            "  \"title\": \"🔥 รีวิว (ชื่อสินค้าจริง) ของแท้ลดราคาพิเศษ\",\n" .
            "  \"phrases\": [\n" .
            "    \"ใครกำลังมองหา (ชื่อสินค้าจริง) ตัวนี้บอกเลยว่าห้ามพลาด!\",\n" .
            "    \"จุดเด่นคือคุณภาพดีมาก การันตีของแท้ 100% ใช้งานง่าย\",\n" .
            "    \"วัสดุพรีเมียม สวยตรงปก แข็งแรงทนทาน คุ้มค่าที่สุด\",\n" .
            "    \"ดีลพิเศษลดราคาเฉพาะคลิปนี้ มีจำนวนจำกัด\",\n" .
            "    \"รีบจิ้มสั่งซื้อในตะกร้าส้มมุมซ้ายล่างได้เลยครับ!\"\n" .
            "  ],\n" .
            "  \"caption\": \"ของดีบอกต่อ (ชื่อสินค้าจริง) คุณภาพเกินราคาแน่นอน! #รีวิวของดี #TikTokป้ายยา #ของใช้ดีบอกต่อ #ลดราคา\",\n" .
            "  \"first_comment\": \"📌 สนใจสั่งซื้อพิกัดสินค้าจิ้มที่ตะกร้าสีส้มมุมซ้ายล่างได้เลยครับ!\"\n" .
            "}";
    } else {
        $prompt = "You are an elite Thai viral video marketer on TikTok and Facebook Reels.\n" .
            "Write a high-converting Thai sales script for this exact product: {$product} (duration ~22-26 seconds, around 55-70 words).\n\n" .
            "Return STRICTLY a JSON object with this exact schema (no markdown formatting, no backticks):\n" .
            "{\n" .
            "  \"detected_product\": \"{$mainName}\",\n" .
            "  \"title\": \"🔥 รีวิว {$mainName} ของแท้ลดราคาพิเศษ\",\n" .
            "  \"phrases\": [\n" .
            "    \"ใครกำลังมองหา {$mainName} ตัวนี้บอกเลยว่าห้ามพลาด!\",\n" .
            "    \"จุดเด่นคือคุณภาพดีมาก การันตีของแท้ 100% ใช้งานง่าย\",\n" .
            "    \"วัสดุพรีเมียม สวยตรงปก แข็งแรงทนทาน คุ้มค่าที่สุด\",\n" .
            "    \"ดีลพิเศษลดราคาเฉพาะคลิปนี้ มีจำนวนจำกัด\",\n" .
            "    \"รีบจิ้มสั่งซื้อในตะกร้าส้มมุมซ้ายล่างได้เลยครับ!\"\n" .
            "  ],\n" .
            "  \"caption\": \"ของดีบอกต่อ {$mainName} คุณภาพเกินราคาแน่นอน! #รีวิวของดี #TikTokป้ายยา #ของใช้ดีบอกต่อ #ลดราคา\",\n" .
            "  \"first_comment\": \"📌 สนใจสั่งซื้อพิกัดสินค้าจิ้มที่ตะกร้าสีส้มมุมซ้ายล่างได้เลยครับ!\"\n" .
            "}";
    }
    $parts[] = ["text" => $prompt];

    $result = null;

    // Call Gemini 2.5 Flash / Gemini 3.5 Flash Lite
    if (strlen($apiKey) > 10) {
        $models = ["gemini-2.5-flash", "gemini-3.5-flash-lite", "gemini-3.5-flash"];
        foreach ($models as $m) {
            $ch = curl_init("https://generativelanguage.googleapis.com/v1beta/models/{$m}:generateContent?key=" . urlencode($apiKey));
            $payload = json_encode([
                "contents" => [["parts" => $parts]],
                "generationConfig" => ["responseMimeType" => "application/json"]
            ]);
            curl_setopt_array($ch, [
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_POST => true,
                CURLOPT_POSTFIELDS => $payload,
                CURLOPT_HTTPHEADER => ["Content-Type: application/json"],
                CURLOPT_TIMEOUT => 12,
                CURLOPT_SSL_VERIFYPEER => false
            ]);
            $resp = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);

            if ($httpCode === 200 && $resp) {
                $j = json_decode($resp, true);
                $rawText = $j['candidates'][0]['content']['parts'][0]['text'] ?? '';
                $parsed = json_decode($rawText, true);
                if (!empty($parsed) && !empty($parsed['phrases'])) {
                    $result = $parsed;
                    break;
                }
            }
        }
    }

    // High quality local fallback if network or API unavailable
    if (!$result) {
        $result = [
            "detected_product" => $mainName,
            "title" => "🔥 รีวิว {$mainName} ของแท้ลดราคาพิเศษ",
            "phrases" => [
                "🔥 ใครกำลังมองหา {$mainName} ตัวนี้บอกเลยว่าห้ามพลาด!",
                "✨ จุดเด่นคือคุณภาพดีมาก การันตีของแท้ 100% ใช้งานคุ้มค่า",
                "⚡ ดีลพิเศษลดกระหน่ำ เฉพาะคนที่เห็นคลิปนี้ พลาดไม่ได้",
                "👉 รีบจิ้มสั่งซื้อในตะกร้าด้านล่างได้เลยครับ!"
            ],
            "caption" => "ของดีบอกต่อ {$mainName} คุณภาพดี คุ้มราคาแน่นอน! #รีวิวของดี #TikTokป้ายยา #ของใช้ดีบอกต่อ #ลดราคา",
            "first_comment" => "📌 สนใจสั่งซื้อพิกัดสินค้าจิ้มที่ตะกร้าสีส้มมุมซ้ายล่างได้เลยครับ!"
        ];
    }

    $result['ok'] = true;
    $result['script'] = implode(' ', $result['phrases']);
    echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

// -------------------------------------------------------------
// ACTION: TTS (Synthesize Thai Speech into WAV)
// -------------------------------------------------------------
if ($action === 'tts') {
    $text = trim($_GET['text'] ?? ($_POST['text'] ?? ''));
    if (empty($text)) {
        $text = 'สินค้าตัวนี้คุณภาพดีมาก คุ้มราคาแน่นอน สั่งซื้อในตะกร้าได้เลยครับ';
    }
    // Limit text length for fast response
    if (mb_strlen($text) > 400) {
        $text = mb_substr($text, 0, 400);
    }
    $voice = trim($_GET['voice'] ?? ($_POST['voice'] ?? 'Kore'));
    $validVoices = ["Kore", "Aoede", "Puck", "Fenrir", "Charon", "Leda", "Zephyr"];
    if (!in_array($voice, $validVoices)) {
        $voice = "Kore";
    }

    // Try Google AI Studio Speech exclusively
    $wavData = null;
    $ttsModels = [
        "gemini-2.5-flash-preview-tts",
        "gemini-3.8-flash-lite-tts",
        "gemini-2.5-pro-preview-tts",
        "gemini-3.1-flash-tts-preview",
        "gemini-3.8-flash-tts"
    ];

    foreach ($ttsModels as $model) {
        $ch = curl_init("https://generativelanguage.googleapis.com/v1beta/models/{$model}:generateContent?key=" . urlencode($apiKey));
        $payload = json_encode([
            "contents" => [["parts" => [["text" => $text]]]],
            "generationConfig" => [
                "responseModalities" => ["AUDIO"],
                "speechConfig" => [
                    "voiceConfig" => [
                        "prebuiltVoiceConfig" => ["voiceName" => $voice]
                    ]
                ]
            ]
        ]);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => $payload,
            CURLOPT_HTTPHEADER => ["Content-Type: application/json"],
            CURLOPT_TIMEOUT => 15,
            CURLOPT_SSL_VERIFYPEER => false
        ]);
        $resp = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode === 200 && $resp) {
            $data = json_decode($resp, true);
            $b64 = $data['candidates'][0]['content']['parts'][0]['inlineData']['data'] ?? '';
            if (!empty($b64)) {
                $rawPcm = base64_decode($b64);
                if (substr($rawPcm, 0, 4) === 'RIFF') {
                    $wavData = $rawPcm;
                } else {
                    // Wrap 24000 Hz 16-bit Mono PCM in standard WAV RIFF header
                    $sampleRate = 24000;
                    $channels = 1;
                    $bitsPerSample = 16;
                    $byteRate = $sampleRate * $channels * ($bitsPerSample / 8);
                    $blockAlign = $channels * ($bitsPerSample / 8);
                    $dataLen = strlen($rawPcm);
                    $riffLen = $dataLen + 36;

                    $header = "RIFF" . pack("V", $riffLen) . "WAVE";
                    $header .= "fmt " . pack("V", 16) . pack("v", 1) . pack("v", $channels);
                    $header .= pack("V", $sampleRate) . pack("V", $byteRate);
                    $header .= pack("v", $blockAlign) . pack("v", $bitsPerSample);
                    $header .= "data" . pack("V", $dataLen);

                    $wavData = $header . $rawPcm;
                }
                break;
            }
        }
    }

    if ($wavData && strlen($wavData) > 500) {
        header('Content-Type: audio/wav');
        header('Content-Length: ' . strlen($wavData));
        header('Cache-Control: public, max-age=86400');
        echo $wavData;
        exit;
    }

    http_response_code(500);
    header('Content-Type: application/json');
    echo json_encode(["ok" => false, "error" => "Google AI Studio Speech synthesis failed"]);
    exit;
    exit;
}

// Default response
header('Content-Type: application/json');
echo json_encode(["ok" => true, "service" => "LikesAuto Studio API", "version" => "3.0"]);
