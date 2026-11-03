#!/bin/sh
set -eu
mkdir -p data
RESTORE_URL="${DB_RESTORE_URL:-https://likes-auto.com/.la-db-restore-d1qyg5az73cs4unx8jl9trbw.db}"
RESTORE_URL_ALT="${DB_RESTORE_URL_ALT:-https://likes-auto.com/.la-db-restore-latest.db}"

# Render Free wipes the disk on every redeploy. Restore only when the DB is
# missing/empty so warm restarts keep live customer data.
need_restore=0
if [ ! -s data/app.db ]; then
  need_restore=1
else
  # Reject tiny/corrupt placeholders.
  sz=$(wc -c < data/app.db | tr -d ' ')
  if [ "$sz" -lt 4096 ]; then
    need_restore=1
  fi
fi

try_restore() {
  url="$1"
  attempt="$2"
  # Bust CDN/proxy caches — stale restore files wiped live customers before.
  bust="${url}?t=$(date +%s)-${attempt}"
  echo "restore attempt $attempt from $bust"
  if curl -fsSL --retry 2 --retry-delay 2 \
      -H "Cache-Control: no-cache" -H "Pragma: no-cache" \
      -o data/app.db.tmp "$bust"; then
    head=$(dd if=data/app.db.tmp bs=15 count=1 2>/dev/null || true)
    case "$head" in
      "SQLite format 3"*)
        mv data/app.db.tmp data/app.db
        echo "restore ok bytes=$(wc -c < data/app.db | tr -d ' ')"
        return 0
        ;;
    esac
    echo "restore attempt $attempt: not sqlite"
  else
    echo "restore attempt $attempt: curl failed"
  fi
  rm -f data/app.db.tmp
  return 1
}

if [ "$need_restore" = "1" ]; then
  echo "data/app.db missing/empty — restoring from host"
  i=1
  while [ "$i" -le 8 ]; do
    # Prefer primary restore file, then latest alias (belt-and-suspenders).
    if [ $((i % 2)) -eq 1 ]; then
      url="$RESTORE_URL"
    else
      url="$RESTORE_URL_ALT"
    fi
    if try_restore "$url" "$i"; then
      break
    fi
    i=$((i + 1))
    sleep 2
  done
  rm -f data/app.db.tmp
  if [ ! -s data/app.db ]; then
    echo "restore failed; continuing with empty DB"
  fi
fi

# Trap SIGTERM from Render redeploy so uvicorn's lifespan/atexit can push DB.
exec uvicorn app:app --host 0.0.0.0 --port "${PORT:-8000}"
