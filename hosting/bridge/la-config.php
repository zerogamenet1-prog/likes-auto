<?php
/**
 * FastAPI backend (Gunicorn/Uvicorn). Leave empty for static-only hosting.
 * Example: 'https://your-app.onrender.com' or a Cloudflare Tunnel URL.
 */
return [
    'backend_base' => 'https://likes-auto.onrender.com',
    'backend_host' => 'likes-auto.com',
    'db_backup_token' => 'la-db-bak-RMkcYN4hq7OE19m6vhGe9c-zwDoWGI0Yx9IfvF-IGA',
    'db_restore_name' => '.la-db-restore-d1qyg5az73cs4unx8jl9trbw.db',
];
