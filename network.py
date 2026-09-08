"""
Zombi Kaçışı — Network Client Module
WebSocket client for multiplayer communication.
Runs WebSocket listener in a background thread with a thread-safe message queue.
"""

import json
import queue
import threading
import asyncio
import time
from config import MULTIPLAYER_SERVER_URL


class NetworkClient:
    """WebSocket-based network client for multiplayer communication."""

    def __init__(self, server_url=None):
        self.server_url = server_url or MULTIPLAYER_SERVER_URL
        self.player_id = None
        self.room_id = None
        self.is_host = False
        self.connected = False
        self.player_name = ""
        self.ping = 0

        # Thread-safe message queue for incoming messages
        self._incoming = queue.Queue()
        # Thread-safe queue for outgoing messages
        self._outgoing = queue.Queue()

        self._ws = None
        self._loop = None
        self._thread = None
        self._running = False

    def connect(self):
        """Start the WebSocket connection in a background thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        # Wait for connection (up to 3 seconds)
        start = time.time()
        while not self.connected and time.time() - start < 3:
            time.sleep(0.05)

        return self.connected

    def _run_loop(self):
        """Run the asyncio event loop in a background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._ws_handler())
        except Exception as e:
            print(f"[NETWORK] Loop error: {e}")
        finally:
            self._running = False
            self.connected = False

    async def _ws_handler(self):
        """Main WebSocket handler - connect, send, and receive."""
        try:
            import websockets
            async with websockets.connect(self.server_url) as ws:
                self._ws = ws
                self.connected = True
                print(f"[NETWORK] Connected to {self.server_url}")

                # Run send, receive, and ping loops concurrently
                send_task = asyncio.ensure_future(self._send_loop(ws))
                recv_task = asyncio.ensure_future(self._recv_loop(ws))
                ping_task = asyncio.ensure_future(self._ping_loop(ws))

                done, pending = await asyncio.wait(
                    [send_task, recv_task, ping_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                for task in pending:
                    task.cancel()

        except Exception as e:
            print(f"[NETWORK] Connection error: {e}")
            self.connected = False

    async def _send_loop(self, ws):
        """Send outgoing messages from the queue."""
        while self._running:
            try:
                sent_any = False
                while not self._outgoing.empty():
                    try:
                        msg = self._outgoing.get_nowait()
                        await ws.send(json.dumps(msg))
                        sent_any = True
                    except queue.Empty:
                        break
                if not sent_any:
                    await asyncio.sleep(0.005)
            except Exception as e:
                print(f"[NETWORK] Send error: {e}")
                break

    async def _ping_loop(self, ws):
        """Periodically ping server to measure round-trip latency."""
        while self._running:
            try:
                if self.connected:
                    self._send({
                        "type": "ping",
                        "client_time": time.time()
                    })
                await asyncio.sleep(1.0)
            except Exception:
                break

    async def _recv_loop(self, ws):
        """Receive incoming messages and put them in the queue."""
        try:
            async for raw in ws:
                try:
                    data = json.loads(raw)
                    # Handle ping pong
                    if data.get("type") == "pong":
                        c_time = data.get("client_time", 0)
                        if c_time > 0:
                            self.ping = max(1, int((time.time() - c_time) * 1000))
                        continue

                    # Handle connection response
                    if data.get("type") == "connected":
                        self.player_id = data.get("player_id")
                        print(f"[NETWORK] Assigned player_id: {self.player_id}")
                    elif data.get("type") == "room_created":
                        self.room_id = data.get("room_id")
                        self.is_host = True
                    elif data.get("type") == "room_joined":
                        self.room_id = data.get("room_id")
                        self.is_host = False

                    self._incoming.put(data)
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            print(f"[NETWORK] Receive error: {e}")

    def _send(self, data: dict):
        """Queue a message for sending."""
        if self.connected:
            self._outgoing.put(data)

    # --- High-level API ---

    def create_room(self, room_name: str, player_name: str, password: str = None):
        """Create a new room."""
        self.player_name = player_name
        self._send({
            "type": "create_room",
            "room_name": room_name,
            "player_name": player_name,
            "password": password
        })

    def join_room(self, room_id: str, player_name: str, password: str = None):
        """Join an existing room."""
        self.player_name = player_name
        self._send({
            "type": "join_room",
            "room_id": room_id,
            "player_name": player_name,
            "password": password
        })

    def leave_room(self):
        """Leave the current room."""
        self._send({"type": "leave_room"})
        self.room_id = None
        self.is_host = False

    def list_rooms(self):
        """Request room list from server."""
        self._send({"type": "list_rooms"})

    def start_game(self, map_seed: int = None):
        """Start the game (host only)."""
        data = {"type": "start_game"}
        if map_seed is not None:
            data["map_seed"] = map_seed
        self._send(data)

    def send_player_update(self, x, y, health, stamina, weapon, angle,
                           is_sprinting, is_dashing, knife_swing, is_alive=True,
                           pet_x=0, pet_y=0):
        """Send player state update."""
        self._send({
            "type": "player_update",
            "x": round(x, 1),
            "y": round(y, 1),
            "health": round(health, 1),
            "stamina": round(stamina, 1),
            "weapon": weapon,
            "angle": round(angle, 3),
            "is_sprinting": is_sprinting,
            "is_dashing": is_dashing,
            "knife_swing": knife_swing,
            "is_alive": is_alive,
            "pet_x": round(pet_x, 1),
            "pet_y": round(pet_y, 1)
        })

    def send_bullet_fire(self, x, y, dx, dy, speed, spread=0, weapon_type="normal"):
        """Send bullet fire event."""
        self._send({
            "type": "bullet_fire",
            "x": round(x, 1),
            "y": round(y, 1),
            "dx": round(dx, 3),
            "dy": round(dy, 3),
            "speed": speed,
            "spread": spread,
            "weapon_type": weapon_type
        })

    def send_entity_spawn(self, entity_type, entity_id, x, y, wave=1, extra=None):
        """Send entity spawn event (host only)."""
        data = {
            "type": "entity_spawn",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "x": round(x, 1),
            "y": round(y, 1),
            "wave": wave
        }
        if extra:
            data.update(extra)
        self._send(data)

    def send_entity_kill(self, entity_type, entity_id):
        """Send entity kill event."""
        self._send({
            "type": "entity_kill",
            "entity_type": entity_type,
            "entity_id": entity_id
        })

    def send_entity_damage(self, entity_type, entity_id, damage, new_health):
        """Send entity damage event."""
        self._send({
            "type": "entity_damage",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "damage": damage,
            "new_health": new_health
        })

    def send_grenade_throw(self, start_x, start_y, target_x, target_y):
        """Send grenade throw event."""
        self._send({
            "type": "grenade_throw",
            "start_x": round(start_x, 1),
            "start_y": round(start_y, 1),
            "target_x": round(target_x, 1),
            "target_y": round(target_y, 1)
        })

    def send_sentry_place(self, x, y):
        """Send sentry placement event."""
        self._send({
            "type": "sentry_place",
            "x": round(x, 1),
            "y": round(y, 1)
        })

    def send_item_pickup(self, item_id, x=None, y=None):
        """Send item pickup event with item_id and optional coordinates."""
        data = {
            "type": "item_pickup",
            "item_id": item_id
        }
        if x is not None and y is not None:
            data["x"] = round(x, 1)
            data["y"] = round(y, 1)
        self._send(data)

    def send_item_sync(self, items: list):
        """Send authoritative item list from host to clients."""
        self._send({
            "type": "item_sync",
            "items": items
        })

    def send_game_over(self, wave, total_kills):
        """Send game over event to all players in room."""
        self._send({
            "type": "game_over",
            "wave": wave,
            "total_kills": total_kills
        })

    def send_wave_change(self, wave, zombies_required, map_seed=None):
        """Send wave change event (host only)."""
        self._send({
            "type": "wave_change",
            "wave": wave,
            "zombies_required": zombies_required,
            "map_seed": map_seed
        })

    def send_zombie_sync(self, zombies: list, wave: int = 1):
        """Send authoritative zombie positions from host to clients."""
        self._send({
            "type": "zombie_sync",
            "zombies": zombies,
            "wave": wave
        })

    def send_chat(self, message: str):
        """Send chat message to room."""
        self._send({
            "type": "chat",
            "message": message
        })

    def get_ping(self) -> int:
        """Return the current latency in milliseconds."""
        return self.ping

    def get_messages(self) -> list:
        """Get all pending incoming messages (non-blocking)."""
        messages = []
        while True:
            try:
                msg = self._incoming.get_nowait()
                messages.append(msg)
            except queue.Empty:
                break
        return messages

    def disconnect(self):
        """Disconnect from the server."""
        self._running = False
        if self._ws and self._loop:
            try:
                asyncio.run_coroutine_threadsafe(
                    self._ws.close(), self._loop
                )
            except Exception:
                pass
        self.connected = False
        self.room_id = None
        self.is_host = False
        self.player_id = None
