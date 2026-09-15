import asyncio
import json
import os
import psutil
from typing import Set, Callable, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
INDEX_FILE = os.path.join(TEMPLATES_DIR, "index.html")

app = FastAPI(title="AURA-OS Smart Display Backend")

# Mount static files for style.css, app.js, and assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

connected_clients: Set[WebSocket] = set()
on_user_query_callback: Optional[Callable[[str], None]] = None
on_touch_trigger_callback: Optional[Callable[[], None]] = None

# Referenced directly by src/main.py
server_loop: Optional[asyncio.AbstractEventLoop] = None


def get_cpu_temp() -> str:
    """Read Pi thermal zone 0 sysfs temperature in Celsius."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_val = round(int(f.read().strip()) / 1000.0, 1)
            return f"{temp_val}°C"
    except Exception:
        return "--°C"


@app.get("/")
async def get_index():
    return FileResponse(INDEX_FILE)


@app.get("/api/vitals")
async def get_vitals():
    temp_str = get_cpu_temp().replace("°C", "").strip()
    try:
        cpu_temp = float(temp_str)
    except ValueError:
        cpu_temp = 0.0

    return {
        "cpu_temp": cpu_temp,
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_percent": psutil.virtual_memory().percent
    }


@app.post("/api/touch-trigger")
async def api_touch_trigger():
    if on_touch_trigger_callback:
        on_touch_trigger_callback()
    return {"status": "triggered"}


@app.post("/api/mute")
async def api_mute():
    return {"status": "muted"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)

    # Send initial state upon connection
    temp_str = get_cpu_temp().replace("°C", "").strip()
    try:
        temp_val = float(temp_str)
    except ValueError:
        temp_val = 0.0

    init_payload = {
        "type": "init",
        "state": "STANDBY",
        "cpu_temp": temp_val,
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_percent": psutil.virtual_memory().percent
    }
    await websocket.send_text(json.dumps(init_payload))

    try:
        while True:
            raw_msg = await websocket.receive_text()
            try:
                data = json.loads(raw_msg)
                action = data.get("action")
                if action == "query" and on_user_query_callback:
                    query_text = data.get("text", "").strip()
                    if query_text:
                        on_user_query_callback(query_text)
                elif action == "wake" and on_touch_trigger_callback:
                    on_touch_trigger_callback()
            except Exception:
                pass
    except WebSocketDisconnect:
        connected_clients.remove(websocket)


async def _broadcast(payload: dict):
    if not connected_clients:
        return
    message = json.dumps(payload)
    for client in list(connected_clients):
        try:
            await client.send_text(message)
        except Exception:
            connected_clients.remove(client)


def broadcast_state(state: str, user_text: str = None, assistant_text: str = None):
    """Thread-safe state updater called directly from src/main.py."""
    global server_loop

    temp_str = get_cpu_temp().replace("°C", "").strip()
    try:
        temp_val = float(temp_str)
    except ValueError:
        temp_val = 0.0

    payload = {
        "type": "state_update",
        "state": state.upper(),
        "user_text": user_text,
        "assistant_text": assistant_text,
        "cpu_temp": temp_val,
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_percent": psutil.virtual_memory().percent
    }

    if server_loop and server_loop.is_running():
        asyncio.run_coroutine_threadsafe(_broadcast(payload), server_loop)


async def telemetry_loop():
    """Background task spawned by src/main.py to stream telemetry periodically."""
    while True:
        if connected_clients:
            temp_str = get_cpu_temp().replace("°C", "").strip()
            try:
                temp_val = float(temp_str)
            except ValueError:
                temp_val = 0.0

            vitals = {
                "type": "vitals",
                "cpu_temp": temp_val,
                "cpu_percent": psutil.cpu_percent(interval=None),
                "ram_percent": psutil.virtual_memory().percent
            }
            await _broadcast(vitals)
        await asyncio.sleep(2.0)