#!/bin/sh
set -eu
mkdir -p data
RESTORE_URL="${DB_RESTORE_URL:-https://likes-auto.com/.la-db-restore-d1qyg5az73cs4unx8jl9trbw.db}"
# Free plan wipes the disk on redeploy. Restore only when the DB file is missing,
# so normal restarts keep live customer data.
if [ ! -s data/app.db ]; then
  echo "data/app.db missing — restoring from $RESTORE_URL"
  curl -fsSL -o data/app.db "$RESTORE_URL" || echo "restore curl failed; continuing with empty DB"
fi
exec uvicorn app:app --host 0.0.0.0 --port "${PORT:-8000}"
