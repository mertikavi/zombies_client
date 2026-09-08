"""
Zombi Kaçışı — Multiplayer Sinyal Sunucusu
WebSocket tabanlı oda yönetimi ve mesaj relay sunucusu.
"""

import asyncio
import json
import uuid
import time
from typing import Dict, Set, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dataclasses import dataclass, field

app = FastAPI(title="Zombi Kaçışı Multiplayer Server")


@dataclass
class PlayerConnection:
    """Represents a connected player."""
    player_id: str
    player_name: str
    websocket: WebSocket
    room_id: Optional[str] = None
    is_host: bool = False


@dataclass
class Room:
    """Represents a game room."""
    room_id: str
    room_name: str
    password: Optional[str]
    host_id: str
    players: Dict[str, PlayerConnection] = field(default_factory=dict)
    game_started: bool = False
    created_at: float = field(default_factory=time.time)
    max_players: int = 4
    map_seed: Optional[int] = None


# Global state
rooms: Dict[str, Room] = {}
connections: Dict[str, PlayerConnection] = {}


async def send_json(ws: WebSocket, data: dict):
    """Send JSON data to a WebSocket connection."""
    try:
        await ws.send_text(json.dumps(data))
    except Exception:
        pass


async def broadcast_to_room(room_id: str, data: dict, exclude_player_id: str = None):
    """Broadcast a message to all players in a room except the sender."""
    room = rooms.get(room_id)
    if not room:
        return
    for pid, player in list(room.players.items()):
        if pid != exclude_player_id:
            await send_json(player.websocket, data)


async def broadcast_room_update(room_id: str):
    """Send updated player list to all players in the room."""
    room = rooms.get(room_id)
    if not room:
        return
    player_list = [
        {
            "player_id": p.player_id,
            "player_name": p.player_name,
            "is_host": p.is_host
        }
        for p in room.players.values()
    ]
    await broadcast_to_room(room_id, {
        "type": "room_update",
        "players": player_list,
        "room_name": room.room_name,
        "game_started": room.game_started
    })


def get_room_list():
    """Get serializable list of rooms."""
    return [
        {
            "room_id": r.room_id,
            "room_name": r.room_name,
            "player_count": len(r.players),
            "max_players": r.max_players,
            "has_password": r.password is not None and r.password != "",
            "game_started": r.game_started,
            "host_name": next(
                (p.player_name for p in r.players.values() if p.is_host),
                "Unknown"
            )
        }
        for r in rooms.values()
    ]


async def handle_create_room(player: PlayerConnection, data: dict):
    """Handle room creation."""
    room_name = data.get("room_name", "Oda")
    password = data.get("password", None)
    player_name = data.get("player_name", "Oyuncu")

    # Leave current room if in one
    if player.room_id:
        await handle_leave_room(player)

    room_id = str(uuid.uuid4())[:8]
    player.player_name = player_name
    player.room_id = room_id
    player.is_host = True

    room = Room(
        room_id=room_id,
        room_name=room_name,
        password=password if password else None,
        host_id=player.player_id,
        players={player.player_id: player}
    )
    rooms[room_id] = room

    await send_json(player.websocket, {
        "type": "room_created",
        "room_id": room_id,
        "room_name": room_name,
        "is_host": True,
        "player_id": player.player_id
    })
    await broadcast_room_update(room_id)
    print(f"[SERVER] Room created: {room_name} ({room_id}) by {player_name}")


async def handle_join_room(player: PlayerConnection, data: dict):
    """Handle joining a room."""
    room_id = data.get("room_id")
    password = data.get("password", None)
    player_name = data.get("player_name", "Oyuncu")

    room = rooms.get(room_id)
    if not room:
        await send_json(player.websocket, {
            "type": "error",
            "message": "Oda bulunamadı."
        })
        return

    if room.game_started:
        await send_json(player.websocket, {
            "type": "error",
            "message": "Oyun zaten başlamış."
        })
        return

    if len(room.players) >= room.max_players:
        await send_json(player.websocket, {
            "type": "error",
            "message": "Oda dolu."
        })
        return

    if room.password and room.password != password:
        await send_json(player.websocket, {
            "type": "error",
            "message": "Yanlış şifre."
        })
        return

    # Leave current room if in one
    if player.room_id:
        await handle_leave_room(player)

    player.player_name = player_name
    player.room_id = room_id
    player.is_host = False
    room.players[player.player_id] = player

    await send_json(player.websocket, {
        "type": "room_joined",
        "room_id": room_id,
        "room_name": room.room_name,
        "is_host": False,
        "player_id": player.player_id
    })

    # Notify others
    await broadcast_to_room(room_id, {
        "type": "player_joined",
        "player_id": player.player_id,
        "player_name": player_name
    }, exclude_player_id=player.player_id)

    await broadcast_room_update(room_id)
    print(f"[SERVER] {player_name} joined room {room.room_name} ({room_id})")


async def handle_leave_room(player: PlayerConnection):
    """Handle leaving a room."""
    room_id = player.room_id
    if not room_id or room_id not in rooms:
        player.room_id = None
        return

    room = rooms[room_id]
    room.players.pop(player.player_id, None)

    # Notify others
    await broadcast_to_room(room_id, {
        "type": "player_left",
        "player_id": player.player_id,
        "player_name": player.player_name
    })

    player.room_id = None
    player.is_host = False

    # If room is empty, delete it
    if len(room.players) == 0:
        del rooms[room_id]
        print(f"[SERVER] Room {room_id} deleted (empty)")
    elif player.player_id == room.host_id:
        # Transfer host to next player
        new_host = next(iter(room.players.values()))
        new_host.is_host = True
        room.host_id = new_host.player_id
        await broadcast_to_room(room_id, {
            "type": "host_changed",
            "new_host_id": new_host.player_id,
            "new_host_name": new_host.player_name
        })
        await broadcast_room_update(room_id)
        print(f"[SERVER] Host transferred to {new_host.player_name} in room {room_id}")
    else:
        await broadcast_room_update(room_id)

    print(f"[SERVER] {player.player_name} left room {room_id}")


async def handle_list_rooms(player: PlayerConnection):
    """Send room list to a player."""
    await send_json(player.websocket, {
        "type": "room_list",
        "rooms": get_room_list()
    })


async def handle_start_game(player: PlayerConnection, data: dict):
    """Handle game start (host only)."""
    room_id = player.room_id
    if not room_id or room_id not in rooms:
        return

    room = rooms[room_id]
    if player.player_id != room.host_id:
        await send_json(player.websocket, {
            "type": "error",
            "message": "Sadece oda sahibi oyunu başlatabilir."
        })
        return

    import random
    room.map_seed = data.get("map_seed", random.randint(0, 999999))
    room.game_started = True

    # Build player info list for all clients
    player_info = [
        {
            "player_id": p.player_id,
            "player_name": p.player_name,
            "is_host": p.is_host
        }
        for p in room.players.values()
    ]

    await broadcast_to_room(room_id, {
        "type": "game_started",
        "map_seed": room.map_seed,
        "players": player_info
    })

    print(f"[SERVER] Game started in room {room.room_name} ({room_id}) with seed {room.map_seed}")


async def handle_game_message(player: PlayerConnection, data: dict):
    """Relay game messages to other players in the room."""
    room_id = player.room_id
    if not room_id or room_id not in rooms:
        return

    # Add sender info
    data["sender_id"] = player.player_id
    data["sender_name"] = player.player_name

    # Relay to all other players in the room
    await broadcast_to_room(room_id, data, exclude_player_id=player.player_id)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    player_id = str(uuid.uuid4())[:12]
    player = PlayerConnection(
        player_id=player_id,
        player_name="Unknown",
        websocket=websocket
    )
    connections[player_id] = player

    await send_json(websocket, {
        "type": "connected",
        "player_id": player_id
    })

    print(f"[SERVER] Player connected: {player_id}")

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")

            if msg_type == "create_room":
                await handle_create_room(player, data)
            elif msg_type == "join_room":
                await handle_join_room(player, data)
            elif msg_type == "leave_room":
                await handle_leave_room(player)
            elif msg_type == "list_rooms":
                await handle_list_rooms(player)
            elif msg_type == "start_game":
                await handle_start_game(player, data)
            elif msg_type in (
                "player_update", "bullet_fire", "entity_spawn",
                "entity_kill", "player_action", "grenade_throw",
                "sentry_place", "game_state", "wave_change",
                "item_pickup", "chat", "zombie_sync", "entity_damage"
            ):
                await handle_game_message(player, data)
            else:
                await send_json(websocket, {
                    "type": "error",
                    "message": f"Bilinmeyen mesaj türü: {msg_type}"
                })

    except WebSocketDisconnect:
        print(f"[SERVER] Player disconnected: {player.player_name} ({player_id})")
    except Exception as e:
        print(f"[SERVER] Error for {player_id}: {e}")
    finally:
        # Clean up
        if player.room_id:
            await handle_leave_room(player)
        connections.pop(player_id, None)


@app.get("/")
async def root():
    return {"status": "running", "rooms": len(rooms), "connections": len(connections)}


@app.get("/rooms")
async def list_rooms_api():
    return {"rooms": get_room_list()}
