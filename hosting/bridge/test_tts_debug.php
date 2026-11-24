<?php
header('Content-Type: application/json');

$apiKey = "AQ.Ab8RN6JtS2uT4N631hV272r2i727qJt2L2491bS8S2v1jqvuA";
$text = "สวัสดีครับ วันนี้มารีวิวของดี";
$voice = "Kore";

$results = [];
$models = ["gemini-3.1-flash-tts-preview", "gemini-3.8-flash-tts", "gemini-2.5-flash-preview-tts"];

foreach ($models as $model) {
    $url = "https://generativelanguage.googleapis.com/v1beta/models/{$model}:generateContent?key=" . urlencode($apiKey);
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

    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $payload,
        CURLOPT_HTTPHEADER => [
            "Content-Type: application/json"
        ],
        CURLOPT_TIMEOUT => 20,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_SSL_VERIFYHOST => false
    ]);
    $resp = curl_exec($ch);
    $err = curl_error($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    $results[$model] = [
        "http_code" => $code,
        "curl_error" => $err,
        "response_preview" => substr($resp, 0, 300)
    ];
}

echo json_encode($results, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
