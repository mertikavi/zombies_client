import os
import json

# --- COLORS ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)         # Normal zombie
GREEN = (0, 200, 0)       # Player (default)
YELLOW = (255, 255, 0)    # Bullet (default)
DARK_RED = (150, 0, 0)
PURPLE = (148, 0, 211)    # Fast zombie
LIGHT_BLUE = (173, 216, 230)# Durable zombie
BROWN = (139, 69, 19)     # Obstacles
GREY = (128, 128, 128)    # Shotgun
ORANGE = (255, 165, 0)    # AK47
HEALTH_GREEN = (50, 205, 50)
STAMINA_BLUE = (0, 191, 255)
STAMINA_BROWN = (165, 42, 42)
HEALTH_RED = (220, 20, 60)
INTRO_BG = (239, 206, 146)

# UI COLORS
UI_BG = (30, 30, 30, 200)

CHARACTER_COLORS = {
    "Yeşil": GREEN,
    "Mavi": LIGHT_BLUE,
    "Sarı": YELLOW,
    "Turuncu": ORANGE
}

BULLET_COLORS = {
    "Sarı": YELLOW,
    "Kırmızı": RED,
    "Mavi": LIGHT_BLUE,
    "Beyaz": WHITE
}

# --- GLOBAL GAME SETTINGS ---
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

game_settings = {
    "player_name": "",
    "difficulty": "Normal",
    "character_color": YELLOW,
    "bullet_color": YELLOW,
    "music": True,
    "sound": True,
    "fov": True,
    "display_mode": "Tam Ekran",
    "show_fps": True,
    "graphics_quality": "Orta",  # Düşük, Orta, Yüksek
    "width": 1920, # Default, will be updated by pygame.display.Info
    "height": 1080
}

def save_settings():
    """Save current game settings to settings.json."""
    try:
        char_c_name = next((k for k, v in CHARACTER_COLORS.items() if v == game_settings.get('character_color')), "Sarı")
        bull_c_name = next((k for k, v in BULLET_COLORS.items() if v == game_settings.get('bullet_color')), "Sarı")
        data = {
            "player_name": game_settings.get("player_name", "").strip(),
            "difficulty": game_settings.get("difficulty", "Normal"),
            "character_color": char_c_name,
            "bullet_color": bull_c_name,
            "music": bool(game_settings.get("music", True)),
            "sound": bool(game_settings.get("sound", True)),
            "fov": bool(game_settings.get("fov", True)),
            "display_mode": game_settings.get("display_mode", "Tam Ekran"),
            "show_fps": bool(game_settings.get("show_fps", True)),
            "graphics_quality": game_settings.get("graphics_quality", "Orta")
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[SETTINGS] Save failed: {e}")

def load_settings():
    """Load settings from settings.json or create defaults if not found."""
    if not os.path.exists(SETTINGS_FILE):
        save_settings()
        return

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "player_name" in data:
            game_settings["player_name"] = str(data["player_name"]).strip()
        if "difficulty" in data and data["difficulty"] in ("Kolay", "Normal", "Zor"):
            game_settings["difficulty"] = data["difficulty"]
        if "character_color" in data:
            val = data["character_color"]
            if val in CHARACTER_COLORS:
                game_settings["character_color"] = CHARACTER_COLORS[val]
            elif isinstance(val, (list, tuple)) and len(val) >= 3:
                game_settings["character_color"] = tuple(val[:3])
        if "bullet_color" in data:
            val = data["bullet_color"]
            if val in BULLET_COLORS:
                game_settings["bullet_color"] = BULLET_COLORS[val]
            elif isinstance(val, (list, tuple)) and len(val) >= 3:
                game_settings["bullet_color"] = tuple(val[:3])
        if "music" in data:
            game_settings["music"] = bool(data["music"])
        if "sound" in data:
            game_settings["sound"] = bool(data["sound"])
        if "fov" in data:
            game_settings["fov"] = bool(data["fov"])
        if "display_mode" in data and data["display_mode"] in ("Tam Ekran", "Kenarlıksız"):
            game_settings["display_mode"] = data["display_mode"]
        if "show_fps" in data:
            game_settings["show_fps"] = bool(data["show_fps"])
        if "graphics_quality" in data and data["graphics_quality"] in ("Düşük", "Orta", "Yüksek"):
            game_settings["graphics_quality"] = data["graphics_quality"]
    except Exception as e:
        print(f"[SETTINGS] Load failed: {e}")
        save_settings()

load_settings()

# --- ENTITY CONSTANTS ---
PLAYER_SIZE = 40
PLAYER_BASE_SPEED = 5
PLAYER_SPRINT_SPEED = 10
MAX_PLAYER_HEALTH = 100
MAX_PLAYER_STAMINA = 100
STAMINA_DRAIN_RATE = 0.5
STAMINA_REGEN_RATE = 0.3
HEALTH_KIT_HEAL = 40
STAMINA_BOOST = 20

ZOMBIE_SIZE = 40
DAMAGE_COOLDOWN = 1000  # ms
MAX_GRENADE_DIST = 400
GRENADE_RADIUS = 150
EXPLOSION_COLOR = (255, 100, 0)

# --- DIFFICULTY TUNING ---
DIFFICULTY_SETTINGS = {
    "Kolay": {
        "zombie_damage_multiplier": 0.7,
        "zombie_speed_multiplier": 0.8,
        "health_kit_heal": 50,
        "stamina_pack_boost": 30,
        "stamina_drain_rate": 0.3,
        "stamina_regen_rate": 0.5
    },
    "Normal": {
        "zombie_damage_multiplier": 1.0,
        "zombie_speed_multiplier": 1.0,
        "health_kit_heal": 40,
        "stamina_pack_boost": 20,
        "stamina_drain_rate": 0.5,
        "stamina_regen_rate": 0.3
    },
    "Zor": {
        "zombie_damage_multiplier": 1.3,
        "zombie_speed_multiplier": 1.2,
        "health_kit_heal": 30,
        "stamina_pack_boost": 10,
        "stamina_drain_rate": 0.7,
        "stamina_regen_rate": 0.1
    }
}

# --- WEAPONS ---
bullet_speed = 10
reload_time = 600

weapons_data = {
    "pistol": {
        "damage": 1,
        "fire_rate": 1,
        "bullet_speed": bullet_speed,
        "fire_delay": 550,
        "reload_time": reload_time,
        "max_ammo": 6,
        "spread": 0
    },
    "ak47": {
        "damage": 2,
        "fire_rate": 5,
        "bullet_speed": bullet_speed + 2,
        "fire_delay": 120,
        "reload_time": 600,
        "max_ammo": 30,
        "spread": 1
    },
    "shotgun": {
        "damage": 3,
        "fire_rate": 1,
        "bullet_speed": bullet_speed,
        "fire_delay": 1060,
        "reload_time": 600,
        "spread": 5,
        "max_ammo": 10
    },
    "knife": {
        "damage": 1,
        "fire_delay": 1000,
        "swing_duration": 150
    },
    "flamethrower": {
        "damage": 1,
        "fire_rate": 1,
        "bullet_speed": bullet_speed - 2,
        "fire_delay": 50,
        "reload_time": 400,
        "spread": 15,
        "max_ammo": 100,
        "pierce": True,
        "lifetime": 20
    }
}

# --- MULTIPLAYER ---
MULTIPLAYER_SERVER_URL = "ws://localhost:8765/ws"
MULTIPLAYER_TICK_RATE = 30  # Send updates per second (33ms interval)
MULTIPLAYER_INTERPOLATION_SPEED = 0.45  # Lerp factor for remote player positions
MULTIPLAYER_MAX_PLAYERS = 4
REMOTE_PLAYER_COLORS = [
    (0, 200, 255),    # Cyan
    (255, 100, 200),  # Pink
    (100, 255, 100),  # Lime
    (255, 200, 50),   # Gold
]
