import pygame
import random
import math
import sys
from config import *
from assets import assets
from utils import check_collision, check_player_collision_with_obstacles, draw_crosshair, update_discord_presence, get_shadow_surface, safe_remove
from entities import Player, Zombie, Bullet, Item, Grenade, BreakableProp, Pet, SentryGun
from ui import HUD, Menu
from particles import ParticleSystem

class GameManager:
    def __init__(self, surface, width, height):
        self.surface = surface
        self.width = width
        self.height = height
        self.hud = HUD(width, height)
        self.menu = Menu(width, height)
        self.shake_surface = pygame.Surface((self.width, self.height))
        self.fov_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.bg_surface = pygame.Surface((self.width, self.height))
        self.bg_surface.fill((18, 18, 28))
        grid_color = (30, 30, 45)
        for x in range(0, self.width, 40):
            pygame.draw.line(self.bg_surface, grid_color, (x, 0), (x, self.height))
        for y in range(0, self.height, 40):
            pygame.draw.line(self.bg_surface, grid_color, (0, y), (self.width, y))
        
        self.reset_game()

    def reset_game(self):
        self.player = Player(self.width//2, self.height//2)
        self.wave = 1
        self.zombies = []
        self.bullets = []
        self.items = []
        self.grenades = []
        self.particles = ParticleSystem()
        self.screen_shake = 0
        self.total_kills = 0
        self.zombies_killed_in_wave = 0
        self.zombies_required = 10
        self.obstacles = []
        self.breakables = []
        self.generate_obstacles_and_breakables(8)
        self.pet = Pet(self.width//2, self.height//2)
        self.is_aiming_grenade = False
        self.sentries_deployed = []
        
        self.game_over = False
        self.is_paused = False
        self.menu.show_wave_transition(self.surface, self.wave)
        self.spawn_wave()
        self.spawn_wave_items()

    def generate_obstacles_and_breakables(self, count=8):
        self.obstacles = []
        self.breakables = []
        min_size, max_size = 40, 100
        safe_zone = pygame.Rect(self.width//2 - 100, self.height//2 - 100, 200, 200)
        
        for i in range(count):
            while True:
                w = random.randint(min_size, max_size)
                h = random.randint(min_size, max_size)
                x = random.randint(0, self.width - w)
                y = random.randint(0, self.height - h)
                
                obs_rect = pygame.Rect(x, y, w, h)
                overlapping_obs = any(obs_rect.colliderect(pygame.Rect(*obs)) for obs in self.obstacles)
                overlapping_brk = any(obs_rect.colliderect(pygame.Rect(b.x, b.y, b.width, b.height)) for b in self.breakables)
                
                if not obs_rect.colliderect(safe_zone) and not overlapping_obs and not overlapping_brk:
                    # 50% chance to be breakable
                    if random.random() > 0.5:
                        self.breakables.append(BreakableProp(x, y, w, h, health=10))
                    else:
                        self.obstacles.append((x, y, w, h))
                    break

    def spawn_wave(self):
        count = self.zombies_required - self.zombies_killed_in_wave
        # Limit max zombies at once for performance/gameplay
        count = min(count, 15 + self.wave * 2) 
        
        for _ in range(count - len(self.zombies)):
            edge = random.randint(0, 3)
            if edge == 0:
                x, y = random.randint(0, self.width - ZOMBIE_SIZE), -ZOMBIE_SIZE
            elif edge == 1:
                x, y = self.width, random.randint(0, self.height - ZOMBIE_SIZE)
            elif edge == 2:
                x, y = random.randint(0, self.width - ZOMBIE_SIZE), self.height
            else:
                x, y = -ZOMBIE_SIZE, random.randint(0, self.height - ZOMBIE_SIZE)
                
            self.zombies.append(Zombie(x, y, self.wave))

    def spawn_wave_items(self):
        # Clear some old items to avoid clutter
        if len(self.items) > 10:
            self.items = self.items[-10:]
            
        health_count = self.wave * 2
        stamina_count = self.wave
        weapon_count = 1
        grenade_count = 2
        
        for _ in range(health_count):
            self._spawn_single_item('health')
        for _ in range(stamina_count):
            self._spawn_single_item('stamina')
        for _ in range(weapon_count):
            self._spawn_single_item(random.choice(['ak47', 'shotgun', 'flamethrower']))
        for _ in range(grenade_count):
            self._spawn_single_item('grenade')
        self._spawn_single_item('flamethrower')
        if self.wave >= 2:
            self._spawn_single_item('sentry')
            
    def _spawn_single_item(self, type):
        for _ in range(10): # try 10 times to find a good spot
            x = random.randint(0, self.width - 40)
            y = random.randint(0, self.height - 40)
            safe = True
            for obs in self.obstacles:
                if check_collision((x, y), obs, 40, obs[2]):
                    safe = False
                    break
            if safe:
                self.items.append(Item(x, y, type))
                break
            
    def handle_input(self, dt, dt_factor=1.0):
        keys = pygame.key.get_pressed()
        move_x = move_y = 0
        diff = DIFFICULTY_SETTINGS[game_settings["difficulty"]]
        is_moving = keys[pygame.K_w] or keys[pygame.K_s] or keys[pygame.K_a] or keys[pygame.K_d]

        # Exhaustion recovery: must reach at least 25 stamina to sprint again once exhausted
        if getattr(self.player, "stamina_exhausted", False):
            if self.player.stamina >= 25:
                self.player.stamina_exhausted = False

        shift_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        # Sprinting:
        # Prevent micro-sprinting when stamina runs out:
        # - Must not be exhausted
        # - Must be pressing shift and moving
        # - If already sprinting, stamina must be > 0. If starting a new sprint, stamina must be >= 10.
        can_sprint = (
            shift_pressed and
            is_moving and
            not getattr(self.player, "stamina_exhausted", False) and
            (self.player.stamina > 0 if self.player.is_sprinting else self.player.stamina >= 10)
        )

        if can_sprint:
            speed = PLAYER_SPRINT_SPEED * dt_factor
            self.player.is_sprinting = True
            self.player.stamina -= diff["stamina_drain_rate"] * dt_factor
            if self.player.stamina <= 0:
                self.player.stamina = 0
                self.player.stamina_exhausted = True
                self.player.is_sprinting = False
        else:
            speed = PLAYER_BASE_SPEED * dt_factor
            self.player.is_sprinting = False
            if self.player.stamina < MAX_PLAYER_STAMINA:
                self.player.stamina = min(MAX_PLAYER_STAMINA, self.player.stamina + diff["stamina_regen_rate"] * dt_factor)

        if keys[pygame.K_w]: move_y = -speed
        if keys[pygame.K_s]: move_y = speed
        if keys[pygame.K_a]: move_x = -speed
        if keys[pygame.K_d]: move_x = speed
        
        if move_x != 0 and move_y != 0:
            move_x *= 0.7071
            move_y *= 0.7071
            
        current_time = pygame.time.get_ticks()
        # Update Pet
        attacked_zombie = self.pet.update(self.player.x, self.player.y, self.zombies, pygame.time.get_ticks())
        if attacked_zombie:
            self.particles.add_floating_text(attacked_zombie.x, attacked_zombie.y - 10, str(self.pet.damage), (200, 200, 255))
            self.particles.add_blood(attacked_zombie.x + attacked_zombie.size//2, attacked_zombie.y + attacked_zombie.size//2, 5)
            if attacked_zombie.health <= 0:
                safe_remove(self.zombies, attacked_zombie)
                self.handle_zombie_death(attacked_zombie)
        
        # Dash Logic
        if keys[pygame.K_SPACE] and not self.player.is_dashing and current_time - self.player.dash_cooldown_timer > 1000 and self.player.stamina >= 20:
            self.player.is_dashing = True
            self.player.dash_timer = current_time
            self.player.stamina -= 20
            if self.player.stamina <= 0:
                self.player.stamina = 0
                self.player.stamina_exhausted = True
            if move_x == 0 and move_y == 0:
                mouse_pos = pygame.mouse.get_pos()
                angle = math.atan2(mouse_pos[1] - self.player.y, mouse_pos[0] - self.player.x)
                self.player.dash_dir_x = math.cos(angle)
                self.player.dash_dir_y = math.sin(angle)
            else:
                l = math.hypot(move_x, move_y)
                self.player.dash_dir_x = move_x / l
                self.player.dash_dir_y = move_y / l
                
        if self.player.is_dashing:
            if current_time - self.player.dash_timer < 200: # 200ms dash duration
                move_x = self.player.dash_dir_x * PLAYER_BASE_SPEED * 4 * dt_factor
                move_y = self.player.dash_dir_y * PLAYER_BASE_SPEED * 4 * dt_factor
                # Spawn dash trail particles
                self.particles.add_blood(self.player.x + PLAYER_SIZE//2, self.player.y + PLAYER_SIZE//2, 1, color=(100, 255, 255))
            else:
                self.player.is_dashing = False
                self.player.dash_cooldown_timer = current_time

        # Check breakable collision for player
        # We'll treat breakables as obstacles for movement
        all_blocks = self.obstacles + [(b.x, b.y, b.width, b.height) for b in self.breakables]
        self.player.x, self.player.y = check_player_collision_with_obstacles(
            (self.player.x, self.player.y), move_x, move_y, PLAYER_SIZE, all_blocks, self.width, self.height)

        # Weapon switching
        if keys[pygame.K_1]: 
            if self.player.inventory["slot1"]:
                self.player.switch_weapon(self.player.inventory["slot1"])
        if keys[pygame.K_2]: self.player.switch_weapon("pistol")
        if keys[pygame.K_3]: self.player.switch_weapon("knife")

    def handle_shooting(self, mouse_pos):
        mouse_pressed = pygame.mouse.get_pressed()
        current_time = pygame.time.get_ticks()
        wp = weapons_data[self.player.current_weapon]
        
        # Left click - shoot / knife
        if mouse_pressed[0]: 
            if current_time - self.player.last_shot_time >= wp["fire_delay"]:
                if self.player.current_weapon == "knife":
                    self.player.knife_swing = True
                    self.player.knife_start_time = current_time
                    self.player.last_shot_time = current_time
                    hit = self.handle_knife_attack(mouse_pos)
                    if not hit:
                        assets.channels['knife_air'].play(assets.sounds['knife_air'])
                else:
                    if self.player.bullets_in_magazine > 0:
                        self.player.bullets_in_magazine -= 1
                        self.player.last_shot_time = current_time
                        self.fire_bullet(mouse_pos, wp)
                    else:
                        if not assets.channels['empty'].get_busy():
                            assets.channels['empty'].play(assets.sounds['empty'])
        else:
            # Stop flamethrower sound when not firing
            if assets.channels['flamethrower'].get_busy():
                assets.channels['flamethrower'].stop()

        # Right click - Grenade aiming and throwing
        if mouse_pressed[2]:
            if current_time - getattr(self.player, "last_grenade_time", 0) >= 1000:
                if self.player.grenades > 0:
                    self.is_aiming_grenade = True
        else:
            if getattr(self, "is_aiming_grenade", False):
                self.is_aiming_grenade = False
                if self.player.grenades > 0:
                    self.player.grenades -= 1
                    self.player.last_grenade_time = current_time
                    center_x = self.player.x + PLAYER_SIZE//2
                    center_y = self.player.y + PLAYER_SIZE//2
                    self.grenades.append(Grenade(center_x, center_y, mouse_pos[0], mouse_pos[1]))

    def fire_bullet(self, mouse_pos, wp):
        if self.player.current_weapon == "flamethrower":
            if not assets.channels['flamethrower'].get_busy():
                assets.channels['flamethrower'].play(assets.sounds['flamethrower'])
        else:
            assets.channels[self.player.current_weapon].play(assets.sounds[self.player.current_weapon])
        center_x = self.player.x + PLAYER_SIZE//2
        center_y = self.player.y + PLAYER_SIZE//2
        
        # Muzzle flash & casings
        angle = math.atan2(mouse_pos[1] - center_y, mouse_pos[0] - center_x)
        self.particles.add_muzzle_flash(center_x + math.cos(angle)*PLAYER_SIZE, center_y + math.sin(angle)*PLAYER_SIZE, angle)
        self.particles.add_casing(center_x, center_y, angle)
        
        # Screen shake for shotgun
        if self.player.current_weapon == 'shotgun':
            self.screen_shake = 10
            
        dx = mouse_pos[0] - center_x
        dy = mouse_pos[1] - center_y
        
        if self.player.current_weapon == "shotgun":
            for _ in range(5):
                self.bullets.append(Bullet(center_x, center_y, dx, dy, wp["bullet_speed"], spread=15))
        elif self.player.current_weapon == "flamethrower":
            self.bullets.append(Bullet(center_x, center_y, dx, dy, wp["bullet_speed"], spread=wp["spread"], weapon_type="flamethrower"))
        else:
            self.bullets.append(Bullet(center_x, center_y, dx, dy, wp["bullet_speed"], spread=wp.get("spread", 0)))

    def handle_knife_attack(self, mouse_pos):
        center_x = self.player.x + PLAYER_SIZE//2
        center_y = self.player.y + PLAYER_SIZE//2
        base_angle = math.atan2(mouse_pos[1] - center_y, mouse_pos[0] - center_x)
        KNIFE_LENGTH = 80
        hit = False
        current_time = pygame.time.get_ticks()
        
        for z in list(self.zombies):
            zx = z.x + z.size//2
            zy = z.y + z.size//2
            dist = math.hypot(zx - center_x, zy - center_y)
            if dist - z.size//2 <= KNIFE_LENGTH:
                z_angle = math.atan2(zy - center_y, zx - center_x)
                # Angle difference check
                diff = (z_angle - base_angle + math.pi) % (2*math.pi) - math.pi
                if abs(diff) < math.pi/4:
                    hit = True
                    damage = weapons_data["knife"]["damage"]
                    z.health -= damage
                    z.hit_flash_timer = current_time
                    self.particles.add_blood(zx, zy, 15)
                    self.particles.add_floating_text(zx, zy - 10, str(damage), (255, 255, 255))
                    if z.health <= 0:
                        safe_remove(self.zombies, z)
                        self.handle_zombie_death(z)      
        if hit:
            assets.channels['knife_damage'].play(assets.sounds['knife_damage'])
        return hit

    def handle_zombie_death(self, z):
        self.total_kills += 1
        self.zombies_killed_in_wave += 1
        
        # Boomer explosion
        if z.type == "boomer":
            assets.channels['grenade'].play(assets.sounds['grenade'])
            self.screen_shake = 10
            # Damage nearby
            zx = z.x + z.size//2
            zy = z.y + z.size//2
            
            # Player damage
            if math.hypot((self.player.x + PLAYER_SIZE//2) - zx, (self.player.y + PLAYER_SIZE//2) - zy) < 100:
                self.player.health -= 30
                self.particles.add_floating_text(self.player.x, self.player.y, "30", (255, 0, 0))
                if self.player.health <= 0:
                    self.game_over = True
            
            # Zombie damage
            for other_z in list(self.zombies):
                if other_z not in self.zombies:
                    continue
                if math.hypot((other_z.x + other_z.size//2) - zx, (other_z.y + other_z.size//2) - zy) < 100:
                    other_z.health -= 50
                    other_z.hit_flash_timer = pygame.time.get_ticks()
                    self.particles.add_blood(other_z.x, other_z.y, 10)
                    if other_z.health <= 0:
                        safe_remove(self.zombies, other_z)
                        self.handle_zombie_death(other_z)
        
        # Drops
        drop_chance = 0.2
        if z.type == "boss":
            drop_chance = 1.0 # Boss always drops
        elif z.type == "durable":
            drop_chance = 0.4
            
        if random.random() < drop_chance:
            drop_type = random.choices(['health', 'stamina', 'ak47', 'shotgun', 'grenade', 'flamethrower', 'sentry'], weights=[20, 20, 12, 12, 10, 10, 10])[0]
            self.items.append(Item(z.x, z.y, drop_type))
            
        if self.zombies_killed_in_wave >= self.zombies_required:
            self.wave += 1
            self.zombies_required = int(self.zombies_required * 1.5)
            self.zombies_killed_in_wave = 0
            self.menu.show_wave_transition(self.surface, self.wave)
            self.spawn_wave()
            self.spawn_wave_items()
            update_discord_presence(self.wave, self.total_kills, self.player.health)

    def update_zombies(self, dt_factor=1.0):
        diff = DIFFICULTY_SETTINGS[game_settings["difficulty"]]
        px = self.player.x + PLAYER_SIZE//2
        py = self.player.y + PLAYER_SIZE//2
        current_time = pygame.time.get_ticks()
        
        for z in self.zombies:
            zx = z.x + z.size//2
            zy = z.y + z.size//2
            angle = math.atan2(py - zy, px - zx)
            
            speed = z.speed * diff["zombie_speed_multiplier"] * dt_factor
            move_x = math.cos(angle) * speed
            move_y = math.sin(angle) * speed
            
            # Zombie collision with obstacles and breakables
            all_blocks = self.obstacles + [(b.x, b.y, b.width, b.height) for b in self.breakables]
            
            # Move X and slide
            z.x += move_x
            for obs in all_blocks:
                if check_collision((z.x, z.y), obs, z.size, obs[2]):
                    if move_x > 0: # Moving right
                        z.x = obs[0] - z.size
                    elif move_x < 0: # Moving left
                        z.x = obs[0] + obs[2]
            
            # Move Y and slide
            z.y += move_y
            for obs in all_blocks:
                if check_collision((z.x, z.y), obs, z.size, obs[2]):
                    if move_y > 0: # Moving down
                        z.y = obs[1] - z.size
                    elif move_y < 0: # Moving up
                        z.y = obs[1] + obs[3]
            
            # Clamp to screen
            z.x = max(0, min(self.width - z.size, z.x))
            z.y = max(0, min(self.height - z.size, z.y))
            
            # Player collision (Damage)
            if check_collision((self.player.x, self.player.y), (z.x, z.y), PLAYER_SIZE, z.size):
                if current_time - z.last_damage_time > DAMAGE_COOLDOWN:
                    z.last_damage_time = current_time
                    dmg = 20 if z.type == "normal" else (40 if z.type == "durable" else 30)
                    self.player.health -= dmg * diff["zombie_damage_multiplier"]
                    if self.player.health <= 0:
                        self.game_over = True

    def update_bullets(self):
        for b in list(self.bullets):
            if getattr(b, "weapon_type", "normal") == "flamethrower" and b.lifetime > weapons_data["flamethrower"]["lifetime"]:
                safe_remove(self.bullets, b)
                continue
                
            b.move()
            if b.x < 0 or b.x > self.width or b.y < 0 or b.y > self.height:
                safe_remove(self.bullets, b)
                continue
                
            hit = False
            for obs in self.obstacles:
                if check_collision((b.x, b.y), obs, b.size, obs[2]):
                    safe_remove(self.bullets, b)
                    hit = True
                    break
                    
            if not hit:
                for brk in list(self.breakables):
                    if check_collision((b.x, b.y), (brk.x, brk.y, brk.width, brk.height), b.size, brk.width):
                        safe_remove(self.bullets, b)
                        damage = weapons_data[self.player.current_weapon]["damage"]
                        brk.health -= damage
                        brk.hit_flash_timer = pygame.time.get_ticks()
                        self.particles.add_floating_text(brk.x + brk.width//2, brk.y, str(damage), (255, 255, 255))
                        if brk.health <= 0:
                            # Drop something when broken
                            if random.random() < 0.3:
                                drop_types = ['health', 'stamina', 'ak47', 'shotgun']
                                self.items.append(Item(brk.x + brk.width//2, brk.y + brk.height//2, random.choice(drop_types)))
                            safe_remove(self.breakables, brk)
                        hit = True
                        break
            
            if not hit:
                for z in list(self.zombies):
                    if check_collision((b.x, b.y), (z.x, z.y), b.size, z.size):
                        if getattr(b, "weapon_type", "normal") == "flamethrower":
                            if z in getattr(b, "pierced_zombies", set()):
                                continue
                            b.pierced_zombies.add(z)
                        else:
                            safe_remove(self.bullets, b)
                            
                        damage = weapons_data[self.player.current_weapon]["damage"]
                        z.health -= damage
                        z.hit_flash_timer = pygame.time.get_ticks()
                        self.particles.add_blood(z.x + z.size//2, z.y + z.size//2, 5)
                        self.particles.add_floating_text(z.x + z.size//2, z.y, str(damage), (255, 255, 255))
                        if z.health <= 0:
                            safe_remove(self.zombies, z)
                            self.handle_zombie_death(z)
                        if getattr(b, "weapon_type", "normal") != "flamethrower":
                            break

    def update_items(self):
        for item in list(self.items):
            if check_collision((self.player.x, self.player.y), (item.x, item.y), PLAYER_SIZE, item.size):
                diff = DIFFICULTY_SETTINGS[game_settings["difficulty"]]
                if item.type == 'health':
                    self.player.health = min(MAX_PLAYER_HEALTH, self.player.health + diff["health_kit_heal"])
                    assets.channels['health'].play(assets.sounds['health'])
                    safe_remove(self.items, item)
                elif item.type == 'stamina':
                    self.player.stamina = min(MAX_PLAYER_STAMINA, self.player.stamina + diff["stamina_pack_boost"])
                    assets.channels['health'].play(assets.sounds['health'])
                    safe_remove(self.items, item)
                elif item.type == 'grenade':
                    if self.player.grenades < self.player.max_grenades:
                        self.player.grenades += 1
                        assets.channels['reload'].play(assets.sounds['reload'])
                        safe_remove(self.items, item)
                elif item.type == 'sentry':
                    if self.player.sentries < self.player.max_sentries:
                        self.player.sentries += 1
                        assets.channels['reload'].play(assets.sounds['reload'])
                        safe_remove(self.items, item)
                else: # Weapon
                    self.player.pickup_weapon(item.type)
                    assets.channels['reload'].play(assets.sounds['reload'])
                    safe_remove(self.items, item)

    def update_grenades(self, current_time):
        for g in list(self.grenades):
            just_exploded = g.update(current_time)
            if just_exploded:
                self.screen_shake = 20
                assets.channels['grenade'].play(assets.sounds['grenade'])
                
                # Check player self-damage
                p_dist = math.hypot((self.player.x + PLAYER_SIZE//2) - g.x, (self.player.y + PLAYER_SIZE//2) - g.y)
                if p_dist <= GRENADE_RADIUS:
                    self.player.health -= 100
                    self.particles.add_floating_text(self.player.x, self.player.y, "100", (255, 0, 0))
                    if self.player.health <= 0:
                        self.game_over = True
                        
                # Break breakables
                for brk in list(self.breakables):
                    brk_cx = brk.x + brk.width//2
                    brk_cy = brk.y + brk.height//2
                    if math.hypot(brk_cx - g.x, brk_cy - g.y) <= GRENADE_RADIUS + brk.width//2:
                        brk.health = 0
                        # Drop loot
                        if random.random() < 0.3:
                            drop_types = ['health', 'stamina', 'ak47', 'shotgun']
                            self.items.append(Item(brk.x + brk.width//2, brk.y + brk.height//2, random.choice(drop_types)))
                        self.particles.add_blood(brk_cx, brk_cy, 15, color=(139, 69, 19))
                        safe_remove(self.breakables, brk)
                        assets.channels['knife_damage'].play(assets.sounds['knife_damage'])
                
                # Kill all zombies within radius
                for z in list(self.zombies):
                    if z not in self.zombies:
                        continue
                    zx = z.x + z.size//2
                    zy = z.y + z.size//2
                    dist = math.hypot(zx - g.x, zy - g.y)
                    if dist <= GRENADE_RADIUS:
                        damage = 100
                        z.health -= damage # lethal
                        z.hit_flash_timer = current_time
                        self.particles.add_blood(zx, zy, 25)
                        self.particles.add_floating_text(zx, zy - 10, str(damage), (255, 100, 100))
                        if z.health <= 0:
                            safe_remove(self.zombies, z)
                            self.handle_zombie_death(z)
            if not g.active:
                safe_remove(self.grenades, g)

    def update_sentries(self, current_time):
        for s in list(self.sentries_deployed):
            target = s.update(self.zombies, current_time)
            if target:
                assets.channels['pistol'].play(assets.sounds['pistol'])
                # Fire visual bullet
                dx = math.cos(s.angle)
                dy = math.sin(s.angle)
                self.bullets.append(Bullet(s.x, s.y, dx, dy, 15, spread=3))
                # Casing and flash
                self.particles.add_casing(s.x, s.y, s.angle)
                self.particles.add_muzzle_flash(s.x + dx*s.size, s.y + dy*s.size, s.angle)
            if s.ammo <= 0:
                safe_remove(self.sentries_deployed, s)
                self.particles.add_blood(s.x, s.y, 20, color=(100, 100, 100)) # Explosion dust

    def draw_grid(self, surface):
        grid_color = (30, 30, 45)
        grid_size = 40
        for x in range(0, self.width, grid_size):
            pygame.draw.line(surface, grid_color, (x, 0), (x, self.height))
        for y in range(0, self.height, grid_size):
            pygame.draw.line(surface, grid_color, (0, y), (self.width, y))

    def draw(self):
        # Handle Screen Shake
        offset_x = 0
        offset_y = 0
        if self.screen_shake > 0:
            offset_x = random.randint(-self.screen_shake, self.screen_shake)
            offset_y = random.randint(-self.screen_shake, self.screen_shake)
            self.screen_shake -= 1
            
        shake_surface = self.shake_surface
        shake_surface.blit(self.bg_surface, (0, 0))
        
        g_qual = game_settings.get("graphics_quality", "Orta")
        # Draw obstacles
        for obs in self.obstacles:
            if g_qual != "Düşük":
                shadow_surf = get_shadow_surface(obs[2], 10, alpha=150)
                shake_surface.blit(shadow_surf, (obs[0], obs[1] + obs[3] - 5))
            pygame.draw.rect(shake_surface, (50, 50, 70), (obs[0], obs[1], obs[2], obs[3]))
            pygame.draw.rect(shake_surface, (70, 70, 90), (obs[0], obs[1], obs[2], obs[3]), 2)
            
        # Draw breakables
        for brk in self.breakables:
            brk.draw(shake_surface)           
        # Draw items
        for item in self.items:
            item.draw(shake_surface, assets)
            
        # Draw Sentries
        for sentry in self.sentries_deployed:
            sentry.draw(shake_surface)
            
        # Draw grenade aim
        if getattr(self, "is_aiming_grenade", False):
            px = self.player.x + PLAYER_SIZE//2
            py = self.player.y + PLAYER_SIZE//2
            mx, my = pygame.mouse.get_pos()
            
            # Apply screen shake offset to mouse pos to keep it accurate on screen
            mx -= offset_x
            my -= offset_y
            
            dist = math.hypot(mx - px, my - py)
            if dist > MAX_GRENADE_DIST:
                angle = math.atan2(my - py, mx - px)
                target_x = px + math.cos(angle) * MAX_GRENADE_DIST
                target_y = py + math.sin(angle) * MAX_GRENADE_DIST
            else:
                target_x = mx
                target_y = my
                
            # Draw dashed line
            line_color = (200, 50, 50, 150)
            dash_length = 10
            dash_count = int(math.hypot(target_x - px, target_y - py) / dash_length)
            for i in range(dash_count):
                if i % 2 == 0:
                    start_pos = (px + (target_x - px) * (i / dash_count), py + (target_y - py) * (i / dash_count))
                    end_pos = (px + (target_x - px) * ((i + 1) / dash_count), py + (target_y - py) * ((i + 1) / dash_count))
                    pygame.draw.line(shake_surface, line_color, start_pos, end_pos, 2)
                    
            # Draw blast radius circle
            preview_surface = pygame.Surface((GRENADE_RADIUS*2, GRENADE_RADIUS*2), pygame.SRCALPHA)
            pygame.draw.circle(preview_surface, (255, 50, 50, 80), (GRENADE_RADIUS, GRENADE_RADIUS), GRENADE_RADIUS)
            pygame.draw.circle(preview_surface, (255, 50, 50, 200), (GRENADE_RADIUS, GRENADE_RADIUS), GRENADE_RADIUS, 1)
            shake_surface.blit(preview_surface, (target_x - GRENADE_RADIUS, target_y - GRENADE_RADIUS))

        # Draw zombies
        for z in self.zombies:
            z.draw(shake_surface, self.player.x, self.player.y, pygame.time.get_ticks())
            
        # Draw bullets
        for b in self.bullets:
            b.draw(shake_surface)
            
        # Draw particles
        self.particles.draw(shake_surface, font=assets.fonts['small'])
        
        self.pet.draw(shake_surface)
            
        # Draw grenades
        for g in self.grenades:
            g.draw(shake_surface, pygame.time.get_ticks())
            
        # Draw player
        self.player.draw(shake_surface, pygame.mouse.get_pos())
        
        # CS2D-style FOV cone
        if game_settings.get("fov", False):
            px = self.player.x + PLAYER_SIZE//2
            py = self.player.y + PLAYER_SIZE//2
            mx, my = pygame.mouse.get_pos()
            angle = math.atan2(my - py, mx - px)
            
            fov_surface = self.fov_surface
            fov_surface.fill((0, 0, 0, 255))
            
            # Cut out the visible cone
            fov_angle = math.radians(90)  # 90 degree cone
            fov_dist = max(self.width, self.height) * 1.5
            num_points = 30
            cone_points = [(px, py)]
            for i in range(num_points + 1):
                a = angle - fov_angle/2 + (fov_angle * i / num_points)
                cone_points.append((px + math.cos(a) * fov_dist, py + math.sin(a) * fov_dist))
            
            # Draw the cone as transparent (cut out from dark overlay)
            pygame.draw.polygon(fov_surface, (0, 0, 0, 0), cone_points)
            
            # Also keep a small circle around player visible
            pygame.draw.circle(fov_surface, (0, 0, 0, 0), (int(px), int(py)), 80)
            
            shake_surface.blit(fov_surface, (0, 0))
        
        # Blit the shaken surface
        self.surface.blit(shake_surface, (offset_x, offset_y))
        
        # Draw HUD (UI is not shaken)
        self.hud.draw(self.surface, self.player, self.wave, len(self.zombies), self.zombies_required)

        # FPS Indicator
        if game_settings.get("show_fps", True):
            self.draw_fps(self.surface)
        
        # Crosshair
        draw_crosshair(self.surface, *pygame.mouse.get_pos(), 15, game_settings["bullet_color"])

    def draw_fps(self, surface):
        """Draw FPS badge on HUD."""
        fps_val = getattr(self, "current_fps", 60)
        fps_surf = assets.fonts['small'].render(f"FPS: {fps_val}", True, (200, 240, 200))
        bw = fps_surf.get_width() + 16
        bh = 24
        s = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(s, (15, 20, 30, 190), (0, 0, bw, bh), border_radius=4)
        pygame.draw.rect(s, (70, 90, 120, 150), (0, 0, bw, bh), 1, border_radius=4)
        surface.blit(s, (15, 118))
        surface.blit(fps_surf, (23, 121))

    def run(self):
        clock = pygame.time.Clock()
        self.clock = clock
        self.current_fps = 60
        pygame.mouse.set_visible(False)
        
        update_discord_presence(game_state="Playing")
        
        while True:
            dt = clock.tick(60)
            dt_factor = min(max(dt / (1000.0 / 60.0), 0.5), 3.0)
            self.current_fps = int(clock.get_fps())
            current_time = pygame.time.get_ticks()
            self.particles.update(dt)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_p):
                        self.is_paused = not self.is_paused
                    if event.key == pygame.K_r and self.player.current_weapon == "pistol":
                        # Reload only pistol
                        wp = weapons_data[self.player.current_weapon]
                        if self.player.bullets_in_magazine < wp["max_ammo"]:
                            assets.channels['reload'].play(assets.sounds['reload'])
                            self.player.bullets_in_magazine = wp["max_ammo"]
                    if event.key == pygame.K_t:
                        if self.player.sentries > 0:
                            self.player.sentries -= 1
                            center_x = self.player.x + PLAYER_SIZE//2
                            center_y = self.player.y + PLAYER_SIZE//2
                            self.sentries_deployed.append(SentryGun(center_x, center_y))

            if self.is_paused:
                pygame.mouse.set_visible(True)
                res = self.menu.show_main_menu(self.surface, is_paused=True)
                if res == "resume":
                    self.is_paused = False
                    pygame.mouse.set_visible(False)
                elif res == "main_menu":
                    return "main_menu"
                elif res == "quit":
                    pygame.quit()
                    sys.exit()
                continue
                
            if self.game_over:
                pygame.mouse.set_visible(True)
                update_discord_presence(wave=self.wave, zombies_killed=self.total_kills, game_state="Game Over")
                res = self.menu.show_game_over(self.surface, self.wave, self.total_kills)
                if res == "main_menu":
                    return "main_menu"
                elif res == "quit":
                    pygame.quit()
                    sys.exit()

            # Handle Knife Swing state
            if self.player.knife_swing:
                if pygame.time.get_ticks() - self.player.knife_start_time > weapons_data["knife"]["swing_duration"]:
                    self.player.knife_swing = False

            # Update Wave logic
            if len(self.zombies) == 0 and self.zombies_killed_in_wave >= self.zombies_required:
                self.wave += 1
                self.zombies_killed_in_wave = 0
                self.zombies_required = int(self.zombies_required * 1.5)
                self.menu.show_wave_transition(self.surface, self.wave)
                self.spawn_wave()
                self.spawn_wave_items()
            elif len(self.zombies) < 5:
                self.spawn_wave()

            self.update_sentries(current_time)
            self.handle_input(dt, dt_factor)
            self.handle_shooting(pygame.mouse.get_pos())
            self.update_zombies(dt_factor)
            self.update_bullets()
            self.update_grenades(current_time)
            self.update_items()
            
            update_discord_presence(wave=self.wave, zombies_killed=self.total_kills, game_state="Playing")

            self.draw()
            pygame.display.flip()
