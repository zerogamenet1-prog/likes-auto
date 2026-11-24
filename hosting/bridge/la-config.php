<?php
/**
 * FastAPI backend (Gunicorn/Uvicorn).
 * Production URL: 'https://likes-auto.onrender.com'
 * DO NOT change backend_base to temporary/ephemeral tunnels (trycloudflare, etc.) in production!
 */
return [
    'backend_base' => 'https://likes-auto.onrender.com',
    'backend_host' => 'likes-auto.com',
    'production_fallback' => 'https://likes-auto.onrender.com',
    'allow_tunnel' => false,
    'db_backup_token' => 'la-db-bak-RMkcYN4hq7OE19m6vhGe9c-zwDoWGI0Yx9IfvF-IGA',
    'db_restore_name' => '.la-db-restore-d1qyg5az73cs4unx8jl9trbw.db',
];
