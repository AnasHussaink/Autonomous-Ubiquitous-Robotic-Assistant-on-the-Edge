#!/bin/bash
# Wait for Ollama service
until curl -s http://127.0.0.1:11434/api/tags > /dev/null; do
    sleep 1
done

# Wait for sound card 2 to register in kernel
until [ -e /proc/asound/card2 ] || grep -q "voicehat" /proc/asound/cards 2>/dev/null; do
    sleep 1
done

# Let ALSA state settle
sleep 3

cd /home/pi/Desktop/Pi-Edge-Smart-Display
source .venv/bin/activate
export PYTHONPATH=.
exec python3 src/main.py
