#!/usr/bin/env bash
set -euo pipefail
ready=0
for attempt in {1..120}; do
  if curl --fail --silent --max-time 2 http://127.0.0.1:8000/ > /dev/null; then
    ready=1
    break
  fi
  sleep 1
done
if [[ "$ready" != 1 ]]; then
  echo "AURA dashboard did not become ready on port 8000." >&2
  exit 1
fi
if command -v chromium > /dev/null; then
  BROWSER_BIN="$(command -v chromium)"
elif command -v chromium-browser > /dev/null; then
  BROWSER_BIN="$(command -v chromium-browser)"
else
  echo "Chromium is not installed." >&2
  exit 1
fi
exec "$BROWSER_BIN" --kiosk --noerrdialogs --disable-infobars --no-first-run http://127.0.0.1:8000/
