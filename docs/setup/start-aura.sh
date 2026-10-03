#!/usr/bin/env bash
# Reference launcher for the documented install layout; does not modify src/.
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"
PYTHON="$PROJECT_DIR/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "Missing .venv. Complete the README software setup first." >&2
  exit 1
fi

ready=0
for attempt in {1..60}; do
  if curl --fail --silent --max-time 2 http://127.0.0.1:11434/api/tags > /dev/null; then
    ready=1
    break
  fi
  sleep 1
done
if [[ "$ready" != 1 ]]; then
  echo "Ollama did not become ready. Check: systemctl status ollama" >&2
  exit 1
fi

ready=0
for attempt in {1..30}; do
  if "$PYTHON" -c 'import sounddevice as sd; sd.check_input_settings(device=None, channels=2, samplerate=48000)' 2>/dev/null; then
    ready=1
    break
  fi
  sleep 1
done
if [[ "$ready" != 1 ]]; then
  echo "Default audio input is not ready for stereo capture at 48000 Hz." >&2
  exit 1
fi

export PYTHONUNBUFFERED=1
exec "$PYTHON" -m src.main
