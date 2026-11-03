#!/bin/sh
set -eu
mkdir -p data
RESTORE_URL="${DB_RESTORE_URL:-https://likes-auto.com/.la-db-restore-d1qyg5az73cs4unx8jl9trbw.db}"
RESTORE_URL_ALT="${DB_RESTORE_URL_ALT:-https://likes-auto.com/.la-db-restore-latest.db}"

# Render Free wipes the disk on every redeploy. Restore only when the DB is
# missing/empty/too thin so warm restarts keep live customer data.
client_count() {
  if [ ! -s data/app.db ]; then
    echo 0
    return
  fi
  python - <<'PY' 2>/dev/null || echo 0
import sqlite3
try:
    con = sqlite3.connect("data/app.db")
    n = int(con.execute("SELECT COUNT(*) FROM clients").fetchone()[0] or 0)
    con.close()
    print(n)
except Exception:
    print(0)
PY
}

need_restore=0
if [ ! -s data/app.db ]; then
  need_restore=1
else
  sz=$(wc -c < data/app.db | tr -d ' ')
  if [ "$sz" -lt 4096 ]; then
    need_restore=1
  else
    n=$(client_count | tr -d ' \r\n')
    if [ "${n:-0}" -lt 1 ]; then
      echo "local DB has 0 clients — will restore from Visperhost"
      need_restore=1
    fi
  fi
fi

try_restore() {
  url="$1"
  attempt="$2"
  bust="${url}?t=$(date +%s)-${attempt}"
  echo "restore attempt $attempt from $bust"
  if curl -fsSL --retry 3 --retry-delay 2 \
      -H "Cache-Control: no-cache" -H "Pragma: no-cache" \
      -o data/app.db.tmp "$bust"; then
    head=$(dd if=data/app.db.tmp bs=15 count=1 2>/dev/null || true)
    case "$head" in
      "SQLite format 3"*)
        mv data/app.db.tmp data/app.db
        n=$(client_count | tr -d ' \r\n')
        echo "restore ok bytes=$(wc -c < data/app.db | tr -d ' ') clients=$n"
        if [ "${n:-0}" -ge 1 ]; then
          return 0
        fi
        echo "restore attempt $attempt: sqlite but 0 clients — retry"
        ;;
      *)
        echo "restore attempt $attempt: not sqlite"
        ;;
    esac
  else
    echo "restore attempt $attempt: curl failed"
  fi
  rm -f data/app.db.tmp
  return 1
}

if [ "$need_restore" = "1" ]; then
  echo "data/app.db missing/empty/thin — restoring from host (never start empty if backup exists)"
  ok=0
  i=1
  while [ "$i" -le 12 ]; do
    if [ $((i % 2)) -eq 1 ]; then
      url="$RESTORE_URL"
    else
      url="$RESTORE_URL_ALT"
    fi
    if try_restore "$url" "$i"; then
      ok=1
      break
    fi
    i=$((i + 1))
    sleep 2
  done
  rm -f data/app.db.tmp
  if [ "$ok" != "1" ]; then
    echo "WARNING: restore failed; refusing to delete any existing local DB"
    if [ ! -s data/app.db ]; then
      echo "WARNING: continuing with empty DB only because no local file exists"
    fi
  fi
fi

# Trap SIGTERM from Render redeploy so uvicorn's lifespan/atexit can push DB.
exec uvicorn app:app --host 0.0.0.0 --port "${PORT:-8000}"
