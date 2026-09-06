import pygame
import random
import math
import sys
from config import *
from assets import assets
from utils import check_collision, check_player_collision_with_obstacles, draw_crosshair, update_discord_presence, get_shadow_surface
from entities import Player, Zombie, Bullet, Item, Grenade
from ui import HUD, Menu
from particles import ParticleSystem

class GameManager:
    def __init__(self, surface, width, height):
        self.surface = surface
        self.width = width
        self.height = height
        self.hud = HUD(width, height)
        self.menu = Menu(width, height)
        
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
        self.obstacles = self.generate_obstacles(6)
        
        self.game_over = False
        self.is_paused = False
        self.menu.show_wave_transition(self.surface, self.wave)
        self.spawn_wave()
        self.spawn_wave_items()

    def generate_obstacles(self, count=6):
        obstacles = []
        min_size, max_size = 40, 120
        safe_zone = pygame.Rect(self.width//2 - 100, self.height//2 - 100, 200, 200)
        
        for _ in range(count):
            while True:
                w = random.randint(min_size, max_size)
                h = random.randint(min_size, max_size)
                x = random.randint(0, self.width - w)
                y = random.randint(0, self.height - h)
                
                obs_rect = pygame.Rect(x, y, w, h)
                overlapping = any(obs_rect.colliderect(pygame.Rect(*obs)) for obs in obstacles)
                
                if not obs_rect.colliderect(safe_zone) and not overlapping:
                    obstacles.append((x, y, w, h))
                    break
        return obstacles

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
            self._spawn_single_item(random.choice(['ak47', 'shotgun']))
        for _ in range(grenade_count):
            self._spawn_single_item('grenade')
            
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
            
    def handle_input(self, dt):
        keys = pygame.key.get_pressed()
        move_x = move_y = 0
        
        # Sprinting
        if keys[pygame.K_LSHIFT] and self.player.stamina > 0:
            speed = PLAYER_SPRINT_SPEED
            self.player.is_sprinting = True
            diff = DIFFICULTY_SETTINGS[game_settings["difficulty"]]
            self.player.stamina -= diff["stamina_drain_rate"]
        else:
            speed = PLAYER_BASE_SPEED
            self.player.is_sprinting = False
            if self.player.stamina < MAX_PLAYER_STAMINA:
                diff = DIFFICULTY_SETTINGS[game_settings["difficulty"]]
                self.player.stamina = min(MAX_PLAYER_STAMINA, self.player.stamina + diff["stamina_regen_rate"])

        if keys[pygame.K_w]: move_y = -speed
        if keys[pygame.K_s]: move_y = speed
        if keys[pygame.K_a]: move_x = -speed
        if keys[pygame.K_d]: move_x = speed
        
        if move_x != 0 and move_y != 0:
            move_x *= 0.7071
            move_y *= 0.7071

        self.player.x, self.player.y = check_player_collision_with_obstacles(
            (self.player.x, self.player.y), move_x, move_y, PLAYER_SIZE, self.obstacles, self.width, self.height)

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

        # Right click - Grenade
        if mouse_pressed[2]:
            if current_time - getattr(self.player, "last_grenade_time", 0) >= 1000:
                if self.player.grenades > 0:
                    self.player.grenades -= 1
                    self.player.last_grenade_time = current_time
                    center_x = self.player.x + PLAYER_SIZE//2
                    center_y = self.player.y + PLAYER_SIZE//2
                    self.grenades.append(Grenade(center_x, center_y, mouse_pos[0], mouse_pos[1]))

    def fire_bullet(self, mouse_pos, wp):
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
        else:
            self.bullets.append(Bullet(center_x, center_y, dx, dy, wp["bullet_speed"], spread=wp.get("spread", 0)))

    def handle_knife_attack(self, mouse_pos):
        center_x = self.player.x + PLAYER_SIZE//2
        center_y = self.player.y + PLAYER_SIZE//2
        base_angle = math.atan2(mouse_pos[1] - center_y, mouse_pos[0] - center_x)
        KNIFE_LENGTH = 80
        hit = False
        
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
                    z.health -= weapons_data["knife"]["damage"]
                    z.hit_flash_timer = pygame.time.get_ticks()
                    self.particles.add_blood(zx, zy, 15)
                    if z.health <= 0:
                        self.zombies.remove(z)
                        self.handle_zombie_death(z)
                        
        if hit:
            assets.channels['knife_damage'].play(assets.sounds['knife_damage'])
        return hit

    def handle_zombie_death(self, zombie):
        self.total_kills += 1
        self.zombies_killed_in_wave += 1
        
        # Item drops
        rand = random.randint(1, 100)
        if rand <= 10:
            self.items.append(Item(zombie.x, zombie.y, 'health'))
        elif rand <= 20:
            self.items.append(Item(zombie.x, zombie.y, 'stamina'))
        elif rand <= 25:
            self.items.append(Item(zombie.x, zombie.y, random.choice(['ak47', 'shotgun'])))

    def update_zombies(self):
        diff = DIFFICULTY_SETTINGS[game_settings["difficulty"]]
        px = self.player.x + PLAYER_SIZE//2
        py = self.player.y + PLAYER_SIZE//2
        current_time = pygame.time.get_ticks()
        
        for z in self.zombies:
            zx = z.x + z.size//2
            zy = z.y + z.size//2
            angle = math.atan2(py - zy, px - zx)
            
            speed = z.speed * diff["zombie_speed_multiplier"]
            move_x = math.cos(angle) * speed
            move_y = math.sin(angle) * speed
            
            # Move X and slide
            z.x += move_x
            for obs in self.obstacles:
                if check_collision((z.x, z.y), obs, z.size, obs[2]):
                    if move_x > 0: # Moving right
                        z.x = obs[0] - z.size
                    elif move_x < 0: # Moving left
                        z.x = obs[0] + obs[2]
            
            # Move Y and slide
            z.y += move_y
            for obs in self.obstacles:
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
            b.move()
            if b.x < 0 or b.x > self.width or b.y < 0 or b.y > self.height:
                self.bullets.remove(b)
                continue
                
            hit = False
            for obs in self.obstacles:
                if check_collision((b.x, b.y), obs, b.size, obs[2]):
                    self.bullets.remove(b)
                    hit = True
                    break
            
            if not hit:
                for z in list(self.zombies):
                    if check_collision((b.x, b.y), (z.x, z.y), b.size, z.size):
                        self.bullets.remove(b)
                        z.health -= weapons_data[self.player.current_weapon]["damage"]
                        z.hit_flash_timer = pygame.time.get_ticks()
                        self.particles.add_blood(z.x + z.size//2, z.y + z.size//2, 5)
                        if z.health <= 0:
                            self.zombies.remove(z)
                            self.handle_zombie_death(z)
                        break

    def update_items(self):
        for item in list(self.items):
            if check_collision((self.player.x, self.player.y), (item.x, item.y), PLAYER_SIZE, item.size):
                diff = DIFFICULTY_SETTINGS[game_settings["difficulty"]]
                if item.type == 'health':
                    self.player.health = min(MAX_PLAYER_HEALTH, self.player.health + diff["health_kit_heal"])
                    assets.channels['health'].play(assets.sounds['health'])
                    self.items.remove(item)
                elif item.type == 'stamina':
                    self.player.stamina = min(MAX_PLAYER_STAMINA, self.player.stamina + diff["stamina_pack_boost"])
                    assets.channels['health'].play(assets.sounds['health'])
                    self.items.remove(item)
                elif item.type == 'grenade':
                    if self.player.grenades < self.player.max_grenades:
                        self.player.grenades += 1
                        assets.channels['reload'].play(assets.sounds['reload'])
                        self.items.remove(item)
                else: # Weapon
                    self.player.pickup_weapon(item.type)
                    assets.channels['reload'].play(assets.sounds['reload'])
                    self.items.remove(item)

    def update_grenades(self, current_time):
        for g in list(self.grenades):
            just_exploded = g.update(current_time)
            if just_exploded:
                # Kill all zombies within radius
                for z in list(self.zombies):
                    zx = z.x + z.size//2
                    zy = z.y + z.size//2
                    dist = math.hypot(zx - g.x, zy - g.y)
                    if dist <= GRENADE_RADIUS:
                        z.health -= 100 # lethal
                        z.hit_flash_timer = current_time
                        self.particles.add_blood(zx, zy, 25)
                        if z.health <= 0:
                            self.zombies.remove(z)
                            self.handle_zombie_death(z)
            if not g.active:
                self.grenades.remove(g)

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
            
        shake_surface = pygame.Surface((self.width, self.height))
        shake_surface.fill((18, 18, 28)) # #12121c dark theme
        self.draw_grid(shake_surface)
        
        # Draw obstacles
        for obs in self.obstacles:
            # Draw drop shadow for obstacle
            shadow_surf = get_shadow_surface(obs[2], obs[3], alpha=100)
            shake_surface.blit(shadow_surf, (obs[0]+5, obs[1]+5))
            pygame.draw.rect(shake_surface, BROWN, obs)
            pygame.draw.rect(shake_surface, (80, 40, 10), obs, 3) # border
            
        # Draw items
        for item in self.items:
            item.draw(shake_surface, assets)
            
        # Draw zombies
        for z in self.zombies:
            z.draw(shake_surface, self.player.x, self.player.y, pygame.time.get_ticks())
            
        # Draw bullets
        for b in self.bullets:
            b.draw(shake_surface)
            
        # Draw particles
        self.particles.draw(shake_surface)
            
        # Draw grenades
        for g in self.grenades:
            g.draw(shake_surface, pygame.time.get_ticks())
            
        # Draw player
        self.player.draw(shake_surface, pygame.mouse.get_pos())
        
        # Vignette effect (Dark edges)
        shake_surface.fill((0, 0, 20, 30), special_flags=pygame.BLEND_RGBA_SUB)
        
        # Blit the shaken surface
        self.surface.blit(shake_surface, (offset_x, offset_y))
        
        # Draw HUD (UI is not shaken)
        self.hud.draw(self.surface, self.player, self.wave, len(self.zombies), self.zombies_required)
        
        # Crosshair
        draw_crosshair(self.surface, *pygame.mouse.get_pos(), 15, game_settings["bullet_color"])

    def run(self):
        clock = pygame.time.Clock()
        pygame.mouse.set_visible(False)
        
        update_discord_presence(game_state="Playing")
        
        while True:
            dt = clock.tick(60)
            self.particles.update(dt)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.is_paused = not self.is_paused
                    if event.key == pygame.K_r and self.player.current_weapon == "pistol":
                        # Reload only pistol
                        wp = weapons_data[self.player.current_weapon]
                        if self.player.bullets_in_magazine < wp["max_ammo"]:
                            assets.channels['reload'].play(assets.sounds['reload'])
                            self.player.bullets_in_magazine = wp["max_ammo"]

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

            self.handle_input(dt)
            self.handle_shooting(pygame.mouse.get_pos())
            self.update_zombies()
            self.update_bullets()
            self.update_grenades(pygame.time.get_ticks())
            self.update_items()
            
            update_discord_presence(wave=self.wave, zombies_killed=self.total_kills, game_state="Playing")

            self.draw()
            pygame.display.flip()
