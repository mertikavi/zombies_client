import pygame
import math
import random
from config import *
from utils import check_collision, draw_triangle_pointing_to_mouse, create_glow_surface, get_shadow_surface

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = PLAYER_SIZE
        self.health = MAX_PLAYER_HEALTH
        self.stamina = MAX_PLAYER_STAMINA
        self.is_sprinting = False
        
        # Weapons
        self.inventory = {
            "knife": {"ammo": "INFINITE", "owned": True},
            "pistol": {"ammo": 0, "owned": True},
            "ak47": {"ammo": 0, "owned": False},
            "shotgun": {"ammo": 0, "owned": False},
            "slot1": None
        }
        self.current_weapon = "pistol"
        self.bullets_in_magazine = 6
        self.last_shot_time = 0
        self.knife_swing = False
        self.knife_start_time = 0
        self.grenades = 0
        self.max_grenades = 5
        
    def switch_weapon(self, weapon_name):
        if weapon_name != "knife" and not self.inventory[weapon_name]["owned"]:
            return
            
        if self.current_weapon not in ["knife"]:
            self.inventory[self.current_weapon]["ammo"] = self.bullets_in_magazine
            
        self.current_weapon = weapon_name
        if weapon_name == "knife":
            self.bullets_in_magazine = "INFINITE"
        else:
            self.bullets_in_magazine = self.inventory[weapon_name]["ammo"]
            
    def pickup_weapon(self, weapon_type):
        if self.current_weapon not in ["knife"]:
            self.inventory[self.current_weapon]["ammo"] = self.bullets_in_magazine
            self.inventory[self.current_weapon]["owned"] = False
            
        self.inventory["slot1"] = weapon_type
        self.inventory[weapon_type]["owned"] = True
        self.inventory[weapon_type]["ammo"] = weapons_data[weapon_type]["max_ammo"]
        
        self.current_weapon = weapon_type
        self.bullets_in_magazine = self.inventory[weapon_type]["ammo"]
        
    def draw(self, surface, mouse_pos):
        x = self.x + self.size // 2
        y = self.y + self.size // 2
        angle = math.atan2(mouse_pos[1] - y, mouse_pos[0] - x)
        
        # Player Shadow
        shadow_size = int(PLAYER_SIZE * 0.7 * 2)
        shadow_surf = get_shadow_surface(shadow_size, shadow_size, alpha=100, is_ellipse=True)
        surface.blit(shadow_surf, (x - shadow_size//2, y - shadow_size//2))
        
        # Player Glow (Radial Gradient)
        glow_surf = create_glow_surface(int(PLAYER_SIZE * 2), (50, 100, 255), max_alpha=120)
        surface.blit(glow_surf, (x - PLAYER_SIZE*2, y - PLAYER_SIZE*2), special_flags=pygame.BLEND_RGBA_ADD)

        # Draw Player Ship Model instead of simple triangle
        p1 = (x + math.cos(angle)*PLAYER_SIZE, y + math.sin(angle)*PLAYER_SIZE)
        p2 = (x + math.cos(angle + math.pi*0.75)*PLAYER_SIZE, y + math.sin(angle + math.pi*0.75)*PLAYER_SIZE)
        p3 = (x + math.cos(angle - math.pi*0.75)*PLAYER_SIZE, y + math.sin(angle - math.pi*0.75)*PLAYER_SIZE)
        # Main Hull
        pygame.draw.polygon(surface, (30, 200, 100), [p1, p2, p3])
        # Engine trails if sprinting
        if self.is_sprinting:
            trail_p = (x + math.cos(angle + math.pi)*PLAYER_SIZE*1.2, y + math.sin(angle + math.pi)*PLAYER_SIZE*1.2)
            pygame.draw.polygon(surface, (100, 255, 255), [p2, p3, trail_p])
        # Cockpit
        cockpit_c = (x + math.cos(angle)*PLAYER_SIZE*0.2, y + math.sin(angle)*PLAYER_SIZE*0.2)
        pygame.draw.circle(surface, (200, 255, 255), (int(cockpit_c[0]), int(cockpit_c[1])), 6)
        
        # Draw knife swing if active
        if self.current_weapon == "knife" and self.knife_swing:
            self.draw_knife_swing(surface, mouse_pos)

    def draw_knife_swing(self, surface, mouse_pos):
        center_x = self.x + self.size // 2
        center_y = self.y + self.size // 2
        dx = mouse_pos[0] - center_x
        dy = mouse_pos[1] - center_y
        base_angle = math.atan2(dy, dx)
        
        angle_span = math.pi / 2
        start_angle = base_angle - angle_span / 2
        end_angle = base_angle + angle_span / 2
        
        outer_points = []
        inner_points = []
        steps = 20
        KNIFE_LENGTH = 80
        KNIFE_THICKNESS = 3
        
        for i in range(steps + 1):
            angle = start_angle + (end_angle - start_angle) * (i / steps)
            outer_x = center_x + math.cos(angle) * KNIFE_LENGTH
            outer_y = center_y + math.sin(angle) * KNIFE_LENGTH
            outer_points.append((int(outer_x), int(outer_y)))
            
            inner_x = center_x + math.cos(angle) * (KNIFE_LENGTH - KNIFE_THICKNESS * 2)
            inner_y = center_y + math.sin(angle) * (KNIFE_LENGTH - KNIFE_THICKNESS * 2)
            inner_points.append((int(inner_x), int(inner_y)))
            
        if len(outer_points) >= 2:
            points = outer_points + list(reversed(inner_points))
            color_with_alpha = (*game_settings["bullet_color"], 128)
            
            # Surface for alpha drawing
            swing_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            pygame.draw.polygon(swing_surf, color_with_alpha, points)
            surface.blit(swing_surf, (0, 0))

class Zombie:
    def __init__(self, x, y, wave):
        self.x = x
        self.y = y
        self.size = ZOMBIE_SIZE
        self.type = "normal"
        self.health = 1
        self.speed = 1.0
        self.color = RED
        self.last_damage_time = 0
        self.hit_flash_timer = 0
        self.setup_stats(wave)
        
    def setup_stats(self, wave):
        z_type = random.randint(1, 100)
        if z_type <= 50:
            self.type = "normal"
            self.health = 1
            self.speed = 1 + wave * 0.2
            self.color = RED
        elif z_type <= 80:
            self.type = "durable"
            self.health = 2
            self.speed = 1.5 + wave * 0.2
            self.color = LIGHT_BLUE
        else:
            self.type = "fast"
            self.health = 1
            self.speed = 2.5 + wave * 0.3
            self.color = PURPLE

    def draw(self, surface, player_x, player_y, current_time=0):
        center_x = self.x + self.size // 2
        center_y = self.y + self.size // 2
        
        # Calculate angle to player for directional drawing
        angle = math.atan2(player_y + PLAYER_SIZE//2 - center_y, player_x + PLAYER_SIZE//2 - center_x)
        
        # Shadow
        shadow_size = int(self.size * 1.2)
        shadow_surf = get_shadow_surface(shadow_size, shadow_size, alpha=100, is_ellipse=True)
        surface.blit(shadow_surf, (center_x - shadow_size//2 + 4, center_y - shadow_size//2 + 4))
        
        # Glow (Radial Gradient)
        glow_surf = create_glow_surface(int(self.size * 2), self.color, max_alpha=100)
        surface.blit(glow_surf, (center_x - int(self.size*2), center_y - int(self.size*2)), special_flags=pygame.BLEND_RGBA_ADD)
        
        # Hit Flash
        is_flashing = current_time > 0 and (current_time - getattr(self, 'hit_flash_timer', 0) < 100)
        draw_color = WHITE if is_flashing else self.color
        
        # Draw different shapes based on type
        if self.type == "normal":
            pygame.draw.rect(surface, draw_color, (self.x, self.y, self.size, self.size))
        elif self.type == "fast":
            # Diamond rotated
            p1 = (center_x + math.cos(angle)*self.size, center_y + math.sin(angle)*self.size)
            p2 = (center_x + math.cos(angle+math.pi/2)*self.size*0.7, center_y + math.sin(angle+math.pi/2)*self.size*0.7)
            p3 = (center_x + math.cos(angle+math.pi)*self.size*0.5, center_y + math.sin(angle+math.pi)*self.size*0.5)
            p4 = (center_x + math.cos(angle-math.pi/2)*self.size*0.7, center_y + math.sin(angle-math.pi/2)*self.size*0.7)
            pygame.draw.polygon(surface, draw_color, [p1, p2, p3, p4])
        elif self.type == "durable":
            # Hexagon rotated
            points = []
            for i in range(6):
                a = angle + (math.pi/3) * i
                points.append((center_x + math.cos(a)*self.size*0.6, center_y + math.sin(a)*self.size*0.6))
            pygame.draw.polygon(surface, draw_color, points)

class Grenade:
    def __init__(self, start_x, start_y, target_x, target_y):
        self.x = start_x
        self.y = start_y
        dist = math.hypot(target_x - start_x, target_y - start_y)
        if dist > MAX_GRENADE_DIST:
            angle = math.atan2(target_y - start_y, target_x - start_x)
            self.target_x = start_x + math.cos(angle) * MAX_GRENADE_DIST
            self.target_y = start_y + math.sin(angle) * MAX_GRENADE_DIST
        else:
            self.target_x = target_x
            self.target_y = target_y
            
        self.speed = 12
        self.active = True
        self.exploding = False
        self.explosion_timer = 0
        self.explosion_duration = 300 # ms
        
        angle = math.atan2(self.target_y - start_y, self.target_x - start_x)
        self.dx = math.cos(angle) * self.speed
        self.dy = math.sin(angle) * self.speed

    def update(self, current_time):
        if self.exploding:
            if current_time - self.explosion_timer > self.explosion_duration:
                self.active = False
            return False # hasn't just exploded
            
        dist = math.hypot(self.target_x - self.x, self.target_y - self.y)
        if dist < self.speed:
            self.x = self.target_x
            self.y = self.target_y
            self.exploding = True
            self.explosion_timer = current_time
            return True # Just exploded!
        else:
            self.x += self.dx
            self.y += self.dy
            return False

    def draw(self, surface, current_time):
        if not self.active: return
        if self.exploding:
            progress = min(1.0, max(0.0, (current_time - self.explosion_timer) / self.explosion_duration))
            current_radius = int(GRENADE_RADIUS * math.sin(progress * math.pi/2)) # easing
            alpha = int(255 * (1 - progress))
            s = pygame.Surface((GRENADE_RADIUS*2, GRENADE_RADIUS*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*EXPLOSION_COLOR, alpha), (GRENADE_RADIUS, GRENADE_RADIUS), current_radius)
            surface.blit(s, (int(self.x - GRENADE_RADIUS), int(self.y - GRENADE_RADIUS)), special_flags=pygame.BLEND_RGBA_ADD)
        else:
            # Shadow
            shadow_size = 16
            shadow_surf = get_shadow_surface(shadow_size, shadow_size, alpha=100, is_ellipse=True)
            surface.blit(shadow_surf, (self.x - shadow_size//2 + 3, self.y - shadow_size//2 + 3))
            
            pygame.draw.circle(surface, (0, 100, 0), (int(self.x), int(self.y)), 8)
            pygame.draw.circle(surface, (50, 150, 50), (int(self.x), int(self.y)), 4)

class Bullet:
    def __init__(self, x, y, dx, dy, speed, spread=0):
        self.x = x
        self.y = y
        self.size = 5
        
        # Apply spread
        if spread > 0:
            angle = math.atan2(dy, dx)
            spread_angle = math.radians(random.uniform(-spread, spread))
            angle += spread_angle
            self.dx = math.cos(angle)
            self.dy = math.sin(angle)
        else:
            self.dx = dx
            self.dy = dy
            
        # Normalize
        length = math.hypot(self.dx, self.dy)
        if length != 0:
            self.dx = (self.dx / length) * speed
            self.dy = (self.dy / length) * speed

    def move(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self, surface):
        pygame.draw.circle(surface, game_settings["bullet_color"], (int(self.x), int(self.y)), self.size)

class Item:
    def __init__(self, x, y, type):
        self.x = x
        self.y = y
        self.size = 30
        self.type = type # 'health', 'stamina', 'ak47', 'shotgun'
        self.spawn_time = pygame.time.get_ticks()
        
    def draw(self, surface, assets):
        # Floating animation
        float_offset = math.sin((pygame.time.get_ticks() - self.spawn_time) * 0.005) * 5
        draw_y = self.y + float_offset
        
        # Shadow
        shadow_surf = get_shadow_surface(self.size, 10, alpha=100, is_ellipse=True)
        surface.blit(shadow_surf, (self.x, self.y + self.size - 5))
        
        if self.type == 'health':
            glow = create_glow_surface(40, HEALTH_GREEN, 100)
            surface.blit(glow, (self.x + self.size//2 - 40, draw_y + self.size//2 - 40), special_flags=pygame.BLEND_RGBA_ADD)
            pygame.draw.circle(surface, HEALTH_GREEN, (int(self.x + self.size//2), int(draw_y + self.size//2)), 15)
            # Draw plus sign
            pygame.draw.rect(surface, WHITE, (self.x + self.size//2 - 2, draw_y + self.size//2 - 8, 4, 16))
            pygame.draw.rect(surface, WHITE, (self.x + self.size//2 - 8, draw_y + self.size//2 - 2, 16, 4))
        elif self.type == 'stamina':
            glow = create_glow_surface(40, STAMINA_BLUE, 100)
            surface.blit(glow, (self.x + self.size//2 - 40, draw_y + self.size//2 - 40), special_flags=pygame.BLEND_RGBA_ADD)
            pygame.draw.circle(surface, (0, 50, 150), (int(self.x + self.size//2), int(draw_y + self.size//2)), 15)
            # Lightning bolt
            pygame.draw.polygon(surface, STAMINA_BLUE, [
                (self.x + 15, draw_y + 8), (self.x + 10, draw_y + 16), 
                (self.x + 15, draw_y + 15), (self.x + 13, draw_y + 22), 
                (self.x + 19, draw_y + 14), (self.x + 14, draw_y + 15)
            ])
        elif self.type == 'grenade':
            glow = create_glow_surface(30, (0, 200, 0), 80)
            surface.blit(glow, (self.x + self.size//2 - 30, draw_y + self.size//2 - 30), special_flags=pygame.BLEND_RGBA_ADD)
            pygame.draw.circle(surface, (0, 100, 0), (int(self.x + self.size//2), int(draw_y + self.size//2)), 12)
            pygame.draw.rect(surface, (50, 50, 50), (self.x + self.size//2 - 4, draw_y + self.size//2 - 15, 8, 8))
        else:
            # Weapon box
            weapon_lbl = assets.fonts['small'].render(self.type.upper(), True, WHITE)
            glow = create_glow_surface(40, (200, 200, 200), 80)
            surface.blit(glow, (self.x + self.size//2 - 40, draw_y + self.size//2 - 40), special_flags=pygame.BLEND_RGBA_ADD)
            pygame.draw.rect(surface, (50, 50, 50), (self.x, draw_y, self.size, self.size), border_radius=5)
            pygame.draw.rect(surface, WHITE, (self.x, draw_y, self.size, self.size), 2, border_radius=5)
            surface.blit(weapon_lbl, (self.x + (self.size - weapon_lbl.get_width())//2, draw_y + (self.size - weapon_lbl.get_height())//2))
