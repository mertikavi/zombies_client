import pygame
import math
import time
from pypresence import Presence
from config import *

# --- DISCORD RPC ---
CLIENT_ID = '1369068337262235688'
discord_connected = False
RPC = None

import threading

def _connect_rpc():
    global RPC, discord_connected
    try:
        RPC = Presence(CLIENT_ID)
        RPC.connect()
        discord_connected = True
        print("Discord RPC connected.")
    except Exception as e:
        discord_connected = False
        print("Discord RPC failed to connect:", e)

def init_discord_rpc():
    t = threading.Thread(target=_connect_rpc, daemon=True)
    t.start()

def update_discord_presence(wave=0, zombies_killed=0, game_state="In Menu"):
    if discord_connected and RPC:
        try:
            RPC.update(
                state=f"Wave {wave} | Killed: {zombies_killed}" if wave != 0 else None,
                details=game_state,
                large_image="logo_short",
                large_text="Project_GG",
                start=int(time.time())
            )
        except Exception:
            pass

_glow_cache = {}

def create_glow_surface(radius, color, max_alpha=100):
    key = (radius, color, max_alpha)
    if key in _glow_cache:
        return _glow_cache[key]
        
    surf = pygame.Surface((radius * 2, radius * 2)) # Black surface for additive blending
    for r in range(radius, 0, -1):
        progress = 1.0 - (r / radius)
        alpha = max_alpha * (progress ** 2) # Quadratic falloff
        
        # Pre-multiply color by alpha for additive blending
        factor = alpha / 255.0
        r_c = min(255, int(color[0] * factor))
        g_c = min(255, int(color[1] * factor))
        b_c = min(255, int(color[2] * factor))
        
        pygame.draw.circle(surf, (r_c, g_c, b_c), (radius, radius), r)
        
    _glow_cache[key] = surf
    return surf

_shadow_cache = {}

def get_shadow_surface(w, h, alpha=100, is_ellipse=False):
    key = (w, h, alpha, is_ellipse)
    if key in _shadow_cache:
        return _shadow_cache[key]
        
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    if is_ellipse:
        pygame.draw.ellipse(surf, (0, 0, 0, alpha), (0, 0, w, h))
    else:
        pygame.draw.rect(surf, (0, 0, 0, alpha), (0, 0, w, h), border_radius=5)
        
    _shadow_cache[key] = surf
    return surf

# --- COLLISION LOGIC ---
def check_collision(rect1, rect2, size1, size2=None):
    """
    Checks collision between two AABB rects.
    rect1: (x, y)
    rect2: (x, y) or (x, y, w, h)
    size1: width/height of rect1 (assumed square)
    size2: width/height of rect2 (assumed square) if rect2 is (x, y)
    """
    x1, y1 = rect1
    if len(rect2) == 2:  # Target is a square entity
        x2, y2 = rect2
        return (x1 < x2 + size2 and
                x1 + size1 > x2 and
                y1 < y2 + size2 and
                y1 + size1 > y2)
    else:  # Target is an obstacle with w, h
        x2, y2, w2, h2 = rect2
        return (x1 < x2 + w2 and
                x1 + size1 > x2 and
                y1 < y2 + h2 and
                y1 + size1 > y2)

def check_player_collision_with_obstacles(player_pos, move_x, move_y, player_size, obstacles, width, height):
    new_x = player_pos[0] + move_x
    new_y = player_pos[1] + move_y
    
    # World bounds
    if new_x < 0 or new_x > width - player_size or new_y < 0 or new_y > height - player_size:
        return player_pos[0], player_pos[1]
    
    # Obstacles
    for obstacle in obstacles:
        if check_collision((new_x, new_y), obstacle, player_size, obstacle[2]):
            return player_pos[0], player_pos[1]
            
    return new_x, new_y

# --- DRAWING UTILS ---
def draw_triangle_pointing_to_mouse(surface, center_pos, mouse_pos, color, size):
    """
    Draws a triangle (player) pointing towards the mouse.
    """
    x, y = center_pos
    mx, my = mouse_pos
    
    # Calculate angle to mouse
    angle = math.atan2(my - y, mx - x)
    
    # Triangle points relative to center
    # Tip of the triangle
    p1 = (x + math.cos(angle) * size, y + math.sin(angle) * size)
    # Bottom corners
    p2 = (x + math.cos(angle + math.pi * 0.75) * size * 0.8, y + math.sin(angle + math.pi * 0.75) * size * 0.8)
    p3 = (x + math.cos(angle - math.pi * 0.75) * size * 0.8, y + math.sin(angle - math.pi * 0.75) * size * 0.8)
    
    pygame.draw.polygon(surface, color, [p1, p2, p3])

def draw_crosshair(surface, x, y, size=10, color=WHITE):
    pygame.draw.line(surface, color, (x - size, y), (x + size, y), 2)
    pygame.draw.line(surface, color, (x, y - size), (x, y + size), 2)
    pygame.draw.circle(surface, color, (x, y), 3)

def safe_remove(target_list, item):
    """Safely remove an item from a list if present, suppressing ValueError."""
    try:
        target_list.remove(item)
        return True
    except (ValueError, KeyError, AttributeError):
        return False

