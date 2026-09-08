import pygame

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
game_settings = {
    "difficulty": "Normal",
    "character_color": YELLOW,
    "bullet_color": YELLOW,
    "music": True,
    "sound": True,
    "fov": True,
    "display_mode": "Tam Ekran",
    "width": 1920, # Default, will be updated by pygame.display.Info
    "height": 1080
}

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
