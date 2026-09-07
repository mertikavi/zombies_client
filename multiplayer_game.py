"""
Zombi Kaçışı — Multiplayer Game Manager
Extends the single-player GameManager with networked multiplayer support.
Host-authoritative model: the room creator manages zombie spawns, items, and waves.
"""

import pygame
import random
import math
import sys
from config import *
from assets import assets
from utils import check_collision, check_player_collision_with_obstacles, draw_crosshair, update_discord_presence, get_shadow_surface
from entities import Player, Zombie, Bullet, Item, Grenade, BreakableProp, Pet, SentryGun, RemotePlayer
from ui import HUD, Menu
from particles import ParticleSystem


class MultiplayerGameManager:
    """Multiplayer game manager with P2P networking via WebSocket relay."""

    def __init__(self, surface, width, height, network, is_host, player_name,
                 map_seed, player_list):
        self.surface = surface
        self.width = width
        self.height = height
        self.hud = HUD(width, height)
        self.menu = Menu(width, height)
        self.network = network
        self.is_host = is_host
        self.player_name = player_name
        self.map_seed = map_seed
        self.player_list = player_list  # List of {player_id, player_name, is_host}

        # Remote players
        self.remote_players = {}  # player_id -> RemotePlayer
        self._init_remote_players()

        # Network timing
        self.last_network_send = 0
        self.network_send_interval = 1000 // MULTIPLAYER_TICK_RATE  # ms

        self.reset_game()

    def _init_remote_players(self):
        """Initialize RemotePlayer objects for all other players."""
        color_idx = 0
        for p in self.player_list:
            if p["player_id"] != self.network.player_id:
                color = REMOTE_PLAYER_COLORS[color_idx % len(REMOTE_PLAYER_COLORS)]
                remote = RemotePlayer(p["player_id"], p["player_name"], color)
                self.remote_players[p["player_id"]] = remote
                color_idx += 1

    def reset_game(self):
        self.player = Player(self.width // 2, self.height // 2, self.player_name)
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
        self.is_aiming_grenade = False
        self.sentries_deployed = []
        self.pet = Pet(self.width // 2, self.height // 2)

        self.game_over = False
        self.is_paused = False

        # Use map_seed for deterministic obstacle generation
        random.seed(self.map_seed)
        self.generate_obstacles_and_breakables(8)
        random.seed()  # Reset to random seed

        if self.is_host:
            self.menu.show_wave_transition(self.surface, self.wave)
            self.spawn_wave()
            self.spawn_wave_items()

    def generate_obstacles_and_breakables(self, count=8):
        self.obstacles = []
        self.breakables = []
        min_size, max_size = 40, 100
        safe_zone = pygame.Rect(self.width // 2 - 100, self.height // 2 - 100, 200, 200)

        for i in range(count):
            for _ in range(100):  # Max attempts
                w = random.randint(min_size, max_size)
                h = random.randint(min_size, max_size)
                x = random.randint(0, self.width - w)
                y = random.randint(0, self.height - h)

                obs_rect = pygame.Rect(x, y, w, h)
                overlapping_obs = any(obs_rect.colliderect(pygame.Rect(*obs)) for obs in self.obstacles)
                overlapping_brk = any(
                    obs_rect.colliderect(pygame.Rect(b.x, b.y, b.width, b.height)) for b in self.breakables)

                if not obs_rect.colliderect(safe_zone) and not overlapping_obs and not overlapping_brk:
                    if random.random() > 0.5:
                        self.breakables.append(BreakableProp(x, y, w, h, health=10))
                    else:
                        self.obstacles.append((x, y, w, h))
                    break

    def spawn_wave(self):
        """Spawn zombies (host only) and broadcast spawn events."""
        if not self.is_host:
            return

        count = self.zombies_required - self.zombies_killed_in_wave
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

            zombie = Zombie(x, y, self.wave)
            self.zombies.append(zombie)

            # Broadcast spawn
            self.network.send_entity_spawn(
                entity_type="zombie",
                entity_id=zombie.entity_id,
                x=x, y=y,
                wave=self.wave,
                extra={
                    "zombie_type": zombie.type,
                    "zombie_health": zombie.health,
                    "zombie_speed": zombie.speed,
                    "zombie_size": zombie.size,
                    "zombie_color": list(zombie.color)
                }
            )

    def spawn_wave_items(self):
        """Spawn items (host only) and broadcast."""
        if not self.is_host:
            return

        if len(self.items) > 10:
            self.items = self.items[-10:]

        health_count = self.wave * 2
        stamina_count = self.wave
        weapon_count = 1
        grenade_count = 2

        item_id = 0
        for _ in range(health_count):
            self._spawn_single_item('health', item_id)
            item_id += 1
        for _ in range(stamina_count):
            self._spawn_single_item('stamina', item_id)
            item_id += 1
        for _ in range(weapon_count):
            self._spawn_single_item(random.choice(['ak47', 'shotgun', 'flamethrower']), item_id)
            item_id += 1
        for _ in range(grenade_count):
            self._spawn_single_item('grenade', item_id)
            item_id += 1
        self._spawn_single_item('flamethrower', item_id)
        item_id += 1
        if self.wave >= 2:
            self._spawn_single_item('sentry', item_id)

    def _spawn_single_item(self, type, item_id=0):
        for _ in range(10):
            x = random.randint(0, self.width - 40)
            y = random.randint(0, self.height - 40)
            safe = True
            for obs in self.obstacles:
                if check_collision((x, y), obs, 40, obs[2]):
                    safe = False
                    break
            if safe:
                item = Item(x, y, type)
                self.items.append(item)

                # Broadcast item spawn
                self.network.send_entity_spawn(
                    entity_type="item",
                    entity_id=item_id,
                    x=x, y=y,
                    extra={"item_type": type}
                )
                break

    # ================================================================
    # NETWORK MESSAGE HANDLING
    # ================================================================

    def process_network_messages(self):
        """Process all pending network messages."""
        for msg in self.network.get_messages():
            msg_type = msg.get("type")
            sender_id = msg.get("sender_id")

            if msg_type == "player_update":
                self._handle_remote_player_update(sender_id, msg)
            elif msg_type == "bullet_fire":
                self._handle_remote_bullet(msg)
            elif msg_type == "entity_spawn":
                self._handle_entity_spawn(msg)
            elif msg_type == "entity_kill":
                self._handle_entity_kill(msg)
            elif msg_type == "entity_damage":
                self._handle_entity_damage(msg)
            elif msg_type == "grenade_throw":
                self._handle_remote_grenade(msg)
            elif msg_type == "sentry_place":
                self._handle_remote_sentry(msg)
            elif msg_type == "wave_change":
                self._handle_wave_change(msg)
            elif msg_type == "item_pickup":
                self._handle_item_pickup(msg)
            elif msg_type == "player_left":
                self._handle_player_left(msg)

    def _handle_remote_player_update(self, sender_id, data):
        """Update remote player state."""
        if sender_id and sender_id in self.remote_players:
            self.remote_players[sender_id].update_from_network(data)

    def _handle_remote_bullet(self, data):
        """Create a bullet from a remote player."""
        b = Bullet(
            data["x"], data["y"],
            data["dx"], data["dy"],
            data["speed"],
            spread=data.get("spread", 0),
            weapon_type=data.get("weapon_type", "normal")
        )
        self.bullets.append(b)

    def _handle_entity_spawn(self, data):
        """Handle entity spawn from host."""
        entity_type = data.get("entity_type")
        if entity_type == "zombie":
            z = Zombie(data["x"], data["y"], data.get("wave", 1), entity_id=data["entity_id"])
            # Override stats from host
            z.type = data.get("zombie_type", z.type)
            z.health = data.get("zombie_health", z.health)
            z.speed = data.get("zombie_speed", z.speed)
            z.size = data.get("zombie_size", z.size)
            color_data = data.get("zombie_color")
            if color_data:
                z.color = tuple(color_data)
            self.zombies.append(z)
        elif entity_type == "item":
            item_type = data.get("item_type", "health")
            item = Item(data["x"], data["y"], item_type)
            self.items.append(item)

    def _handle_entity_kill(self, data):
        """Handle entity kill from another player."""
        entity_type = data.get("entity_type")
        entity_id = data.get("entity_id")

        if entity_type == "zombie":
            for z in list(self.zombies):
                if z.entity_id == entity_id:
                    self.particles.add_blood(z.x + z.size // 2, z.y + z.size // 2, 15)
                    self.zombies.remove(z)
                    self.total_kills += 1
                    self.zombies_killed_in_wave += 1
                    break

    def _handle_entity_damage(self, data):
        """Handle entity damage from another player."""
        entity_type = data.get("entity_type")
        entity_id = data.get("entity_id")

        if entity_type == "zombie":
            for z in self.zombies:
                if z.entity_id == entity_id:
                    z.health = data.get("new_health", z.health)
                    z.hit_flash_timer = pygame.time.get_ticks()
                    self.particles.add_blood(z.x + z.size // 2, z.y + z.size // 2, 5)
                    break

    def _handle_remote_grenade(self, data):
        """Create a grenade from a remote player."""
        g = Grenade(data["start_x"], data["start_y"], data["target_x"], data["target_y"])
        self.grenades.append(g)

    def _handle_remote_sentry(self, data):
        """Place a sentry from a remote player."""
        self.sentries_deployed.append(SentryGun(data["x"], data["y"]))

    def _handle_wave_change(self, data):
        """Handle wave change from host."""
        self.wave = data.get("wave", self.wave)
        self.zombies_required = data.get("zombies_required", self.zombies_required)
        self.zombies_killed_in_wave = 0
        self.menu.show_wave_transition(self.surface, self.wave)

    def _handle_item_pickup(self, data):
        """Handle item pickup by another player."""
        item_index = data.get("item_index")
        if item_index is not None and 0 <= item_index < len(self.items):
            self.items.pop(item_index)

    def _handle_player_left(self, data):
        """Handle a player leaving the game."""
        player_id = data.get("player_id")
        if player_id in self.remote_players:
            del self.remote_players[player_id]

    # ================================================================
    # SEND LOCAL STATE
    # ================================================================

    def send_local_state(self):
        """Send local player state to other players."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_network_send < self.network_send_interval:
            return
        self.last_network_send = current_time

        mouse_pos = pygame.mouse.get_pos()
        px = self.player.x + PLAYER_SIZE // 2
        py = self.player.y + PLAYER_SIZE // 2
        angle = math.atan2(mouse_pos[1] - py, mouse_pos[0] - px)

        self.network.send_player_update(
            x=self.player.x,
            y=self.player.y,
            health=self.player.health,
            stamina=self.player.stamina,
            weapon=self.player.current_weapon,
            angle=angle,
            is_sprinting=self.player.is_sprinting,
            is_dashing=self.player.is_dashing,
            knife_swing=self.player.knife_swing,
            is_alive=not self.game_over
        )

    # ================================================================
    # GAME LOGIC (mostly from GameManager, adapted for multiplayer)
    # ================================================================

    def handle_input(self, dt):
        keys = pygame.key.get_pressed()
        move_x = move_y = 0

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

        current_time = pygame.time.get_ticks()
        # Update Pet
        attacked_zombie = self.pet.update(self.player.x, self.player.y, self.zombies, current_time)
        if attacked_zombie:
            self.particles.add_floating_text(attacked_zombie.x, attacked_zombie.y - 10, str(self.pet.damage),
                                             (200, 200, 255))
            self.particles.add_blood(attacked_zombie.x + attacked_zombie.size // 2,
                                     attacked_zombie.y + attacked_zombie.size // 2, 5)
            if attacked_zombie.health <= 0 and attacked_zombie in self.zombies:
                self.zombies.remove(attacked_zombie)
                self.handle_zombie_death(attacked_zombie)

        # Dash Logic
        if keys[pygame.K_SPACE] and not self.player.is_dashing and current_time - self.player.dash_cooldown_timer > 1000 and self.player.stamina >= 20:
            self.player.is_dashing = True
            self.player.dash_timer = current_time
            self.player.stamina -= 20
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
            if current_time - self.player.dash_timer < 200:
                move_x = self.player.dash_dir_x * PLAYER_BASE_SPEED * 4
                move_y = self.player.dash_dir_y * PLAYER_BASE_SPEED * 4
                self.particles.add_blood(self.player.x + PLAYER_SIZE // 2, self.player.y + PLAYER_SIZE // 2, 1,
                                         color=(100, 255, 255))
            else:
                self.player.is_dashing = False
                self.player.dash_cooldown_timer = current_time

        all_blocks = self.obstacles + [(b.x, b.y, b.width, b.height) for b in self.breakables]
        self.player.x, self.player.y = check_player_collision_with_obstacles(
            (self.player.x, self.player.y), move_x, move_y, PLAYER_SIZE, all_blocks, self.width, self.height)

        if keys[pygame.K_1]:
            if self.player.inventory["slot1"]:
                self.player.switch_weapon(self.player.inventory["slot1"])
        if keys[pygame.K_2]: self.player.switch_weapon("pistol")
        if keys[pygame.K_3]: self.player.switch_weapon("knife")

    def handle_shooting(self, mouse_pos):
        mouse_pressed = pygame.mouse.get_pressed()
        current_time = pygame.time.get_ticks()
        wp = weapons_data[self.player.current_weapon]

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
                    center_x = self.player.x + PLAYER_SIZE // 2
                    center_y = self.player.y + PLAYER_SIZE // 2
                    self.grenades.append(Grenade(center_x, center_y, mouse_pos[0], mouse_pos[1]))
                    # Broadcast grenade
                    self.network.send_grenade_throw(center_x, center_y, mouse_pos[0], mouse_pos[1])

    def fire_bullet(self, mouse_pos, wp):
        if self.player.current_weapon == "flamethrower":
            if not assets.channels['flamethrower'].get_busy():
                assets.channels['flamethrower'].play(assets.sounds['flamethrower'])
        else:
            assets.channels[self.player.current_weapon].play(assets.sounds[self.player.current_weapon])

        center_x = self.player.x + PLAYER_SIZE // 2
        center_y = self.player.y + PLAYER_SIZE // 2

        angle = math.atan2(mouse_pos[1] - center_y, mouse_pos[0] - center_x)
        self.particles.add_muzzle_flash(center_x + math.cos(angle) * PLAYER_SIZE,
                                         center_y + math.sin(angle) * PLAYER_SIZE, angle)
        self.particles.add_casing(center_x, center_y, angle)

        if self.player.current_weapon == 'shotgun':
            self.screen_shake = 10

        dx = mouse_pos[0] - center_x
        dy = mouse_pos[1] - center_y

        if self.player.current_weapon == "shotgun":
            for _ in range(5):
                b = Bullet(center_x, center_y, dx, dy, wp["bullet_speed"], spread=15)
                self.bullets.append(b)
                self.network.send_bullet_fire(center_x, center_y, dx, dy, wp["bullet_speed"], 15)
        elif self.player.current_weapon == "flamethrower":
            b = Bullet(center_x, center_y, dx, dy, wp["bullet_speed"], spread=wp["spread"],
                       weapon_type="flamethrower")
            self.bullets.append(b)
            self.network.send_bullet_fire(center_x, center_y, dx, dy, wp["bullet_speed"],
                                           wp["spread"], "flamethrower")
        else:
            b = Bullet(center_x, center_y, dx, dy, wp["bullet_speed"], spread=wp.get("spread", 0))
            self.bullets.append(b)
            self.network.send_bullet_fire(center_x, center_y, dx, dy, wp["bullet_speed"],
                                           wp.get("spread", 0))

    def handle_knife_attack(self, mouse_pos):
        center_x = self.player.x + PLAYER_SIZE // 2
        center_y = self.player.y + PLAYER_SIZE // 2
        base_angle = math.atan2(mouse_pos[1] - center_y, mouse_pos[0] - center_x)
        KNIFE_LENGTH = 80
        hit = False
        current_time = pygame.time.get_ticks()

        for z in list(self.zombies):
            zx = z.x + z.size // 2
            zy = z.y + z.size // 2
            dist = math.hypot(zx - center_x, zy - center_y)
            if dist - z.size // 2 <= KNIFE_LENGTH:
                z_angle = math.atan2(zy - center_y, zx - center_x)
                diff = (z_angle - base_angle + math.pi) % (2 * math.pi) - math.pi
                if abs(diff) < math.pi / 4:
                    hit = True
                    damage = weapons_data["knife"]["damage"]
                    z.health -= damage
                    z.hit_flash_timer = current_time
                    self.particles.add_blood(zx, zy, 15)
                    self.particles.add_floating_text(zx, zy - 10, str(damage), (255, 255, 255))

                    # Broadcast damage
                    self.network.send_entity_damage("zombie", z.entity_id, damage, z.health)

                    if z.health <= 0:
                        self.zombies.remove(z)
                        self.handle_zombie_death(z)
        if hit:
            assets.channels['knife_damage'].play(assets.sounds['knife_damage'])
        return hit

    def handle_zombie_death(self, z):
        self.total_kills += 1
        self.zombies_killed_in_wave += 1

        # Broadcast kill
        self.network.send_entity_kill("zombie", z.entity_id)

        # Boomer explosion
        if z.type == "boomer":
            assets.channels['grenade'].play(assets.sounds['grenade'])
            self.screen_shake = 10
            zx = z.x + z.size // 2
            zy = z.y + z.size // 2

            # Player damage (only local player)
            if math.hypot((self.player.x + PLAYER_SIZE // 2) - zx,
                          (self.player.y + PLAYER_SIZE // 2) - zy) < 100:
                self.player.health -= 30
                self.particles.add_floating_text(self.player.x, self.player.y, "30", (255, 0, 0))
                if self.player.health <= 0:
                    self.game_over = True

            for other_z in list(self.zombies):
                if math.hypot((other_z.x + other_z.size // 2) - zx,
                              (other_z.y + other_z.size // 2) - zy) < 100:
                    other_z.health -= 50
                    other_z.hit_flash_timer = pygame.time.get_ticks()
                    self.particles.add_blood(other_z.x, other_z.y, 10)
                    if other_z.health <= 0:
                        self.zombies.remove(other_z)
                        self.handle_zombie_death(other_z)

        # Drops (host only)
        if self.is_host:
            drop_chance = 0.2
            if z.type == "boss":
                drop_chance = 1.0
            elif z.type == "durable":
                drop_chance = 0.4

            if random.random() < drop_chance:
                drop_type = random.choices(
                    ['health', 'stamina', 'ak47', 'shotgun', 'grenade', 'flamethrower', 'sentry'],
                    weights=[20, 20, 12, 12, 10, 10, 10]
                )[0]
                item = Item(z.x, z.y, drop_type)
                self.items.append(item)
                self.network.send_entity_spawn("item", id(item), z.x, z.y, extra={"item_type": drop_type})

        # Wave management (host only)
        if self.is_host and self.zombies_killed_in_wave >= self.zombies_required:
            self.wave += 1
            self.zombies_required = int(self.zombies_required * 1.5)
            self.zombies_killed_in_wave = 0
            self.menu.show_wave_transition(self.surface, self.wave)
            self.spawn_wave()
            self.spawn_wave_items()
            self.network.send_wave_change(self.wave, self.zombies_required)
            update_discord_presence(self.wave, self.total_kills, self.player.health)

    def update_zombies(self):
        """All clients update zombie movement locally (deterministic)."""
        diff = DIFFICULTY_SETTINGS[game_settings["difficulty"]]
        px = self.player.x + PLAYER_SIZE // 2
        py = self.player.y + PLAYER_SIZE // 2
        current_time = pygame.time.get_ticks()

        # Find nearest player target for each zombie (local + remotes)
        all_player_positions = [(px, py)]
        for rp in self.remote_players.values():
            if rp.is_alive:
                all_player_positions.append((rp.x + rp.size // 2, rp.y + rp.size // 2))

        for z in self.zombies:
            zx = z.x + z.size // 2
            zy = z.y + z.size // 2

            # Find nearest player
            nearest_dist = float('inf')
            target_x, target_y = px, py
            for tpx, tpy in all_player_positions:
                d = math.hypot(tpx - zx, tpy - zy)
                if d < nearest_dist:
                    nearest_dist = d
                    target_x, target_y = tpx, tpy

            angle = math.atan2(target_y - zy, target_x - zx)
            speed = z.speed * diff["zombie_speed_multiplier"]
            move_x = math.cos(angle) * speed
            move_y = math.sin(angle) * speed

            all_blocks = self.obstacles + [(b.x, b.y, b.width, b.height) for b in self.breakables]

            z.x += move_x
            for obs in all_blocks:
                if check_collision((z.x, z.y), obs, z.size, obs[2]):
                    if move_x > 0:
                        z.x = obs[0] - z.size
                    elif move_x < 0:
                        z.x = obs[0] + obs[2]

            z.y += move_y
            for obs in all_blocks:
                if check_collision((z.x, z.y), obs, z.size, obs[2]):
                    if move_y > 0:
                        z.y = obs[1] - z.size
                    elif move_y < 0:
                        z.y = obs[1] + obs[3]

            z.x = max(0, min(self.width - z.size, z.x))
            z.y = max(0, min(self.height - z.size, z.y))

            # Damage to LOCAL player only (no friendly fire)
            if check_collision((self.player.x, self.player.y), (z.x, z.y), PLAYER_SIZE, z.size):
                if current_time - z.last_damage_time > DAMAGE_COOLDOWN:
                    z.last_damage_time = current_time
                    dmg = 20 if z.type == "normal" else (40 if z.type == "durable" else 30)
                    self.player.health -= dmg * diff["zombie_damage_multiplier"]
                    if self.player.health <= 0:
                        self.game_over = True

    def update_bullets(self):
        for b in list(self.bullets):
            if getattr(b, "weapon_type", "normal") == "flamethrower" and b.lifetime > \
                    weapons_data["flamethrower"]["lifetime"]:
                if b in self.bullets: self.bullets.remove(b)
                continue

            b.move()
            if b.x < 0 or b.x > self.width or b.y < 0 or b.y > self.height:
                if b in self.bullets: self.bullets.remove(b)
                continue

            hit = False
            for obs in self.obstacles:
                if check_collision((b.x, b.y), obs, b.size, obs[2]):
                    self.bullets.remove(b)
                    hit = True
                    break

            if not hit:
                for brk in list(self.breakables):
                    if check_collision((b.x, b.y), (brk.x, brk.y, brk.width, brk.height), b.size, brk.width):
                        self.bullets.remove(b)
                        damage = weapons_data[self.player.current_weapon]["damage"]
                        brk.health -= damage
                        brk.hit_flash_timer = pygame.time.get_ticks()
                        self.particles.add_floating_text(brk.x + brk.width // 2, brk.y, str(damage),
                                                         (255, 255, 255))
                        if brk.health <= 0:
                            if random.random() < 0.3:
                                drop_types = ['health', 'stamina', 'ak47', 'shotgun']
                                self.items.append(
                                    Item(brk.x + brk.width // 2, brk.y + brk.height // 2, random.choice(drop_types)))
                            self.breakables.remove(brk)
                        hit = True
                        break

            # Bullets do NOT hit remote players (no friendly fire)
            if not hit:
                for z in list(self.zombies):
                    if check_collision((b.x, b.y), (z.x, z.y), b.size, z.size):
                        if getattr(b, "weapon_type", "normal") == "flamethrower":
                            if z in getattr(b, "pierced_zombies", set()):
                                continue
                            b.pierced_zombies.add(z)
                        else:
                            if b in self.bullets: self.bullets.remove(b)

                        damage = weapons_data[self.player.current_weapon]["damage"]
                        z.health -= damage
                        z.hit_flash_timer = pygame.time.get_ticks()
                        self.particles.add_blood(z.x + z.size // 2, z.y + z.size // 2, 5)
                        self.particles.add_floating_text(z.x + z.size // 2, z.y, str(damage), (255, 255, 255))

                        # Broadcast damage
                        self.network.send_entity_damage("zombie", z.entity_id, damage, z.health)

                        if z.health <= 0:
                            self.zombies.remove(z)
                            self.handle_zombie_death(z)
                        if getattr(b, "weapon_type", "normal") != "flamethrower":
                            break

    def update_items(self):
        for i, item in enumerate(list(self.items)):
            if check_collision((self.player.x, self.player.y), (item.x, item.y), PLAYER_SIZE, item.size):
                diff = DIFFICULTY_SETTINGS[game_settings["difficulty"]]
                picked_up = False

                if item.type == 'health':
                    self.player.health = min(MAX_PLAYER_HEALTH, self.player.health + diff["health_kit_heal"])
                    assets.channels['health'].play(assets.sounds['health'])
                    picked_up = True
                elif item.type == 'stamina':
                    self.player.stamina = min(MAX_PLAYER_STAMINA, self.player.stamina + diff["stamina_pack_boost"])
                    assets.channels['health'].play(assets.sounds['health'])
                    picked_up = True
                elif item.type == 'grenade':
                    if self.player.grenades < self.player.max_grenades:
                        self.player.grenades += 1
                        assets.channels['reload'].play(assets.sounds['reload'])
                        picked_up = True
                elif item.type == 'sentry':
                    if self.player.sentries < self.player.max_sentries:
                        self.player.sentries += 1
                        assets.channels['reload'].play(assets.sounds['reload'])
                        picked_up = True
                else:  # Weapon
                    self.player.pickup_weapon(item.type)
                    assets.channels['reload'].play(assets.sounds['reload'])
                    picked_up = True

                if picked_up:
                    idx = self.items.index(item)
                    self.items.remove(item)
                    self.network.send_item_pickup(idx)

    def update_grenades(self, current_time):
        for g in list(self.grenades):
            just_exploded = g.update(current_time)
            if just_exploded:
                self.screen_shake = 20
                assets.channels['grenade'].play(assets.sounds['grenade'])

                # Self-damage
                p_dist = math.hypot((self.player.x + PLAYER_SIZE // 2) - g.x,
                                    (self.player.y + PLAYER_SIZE // 2) - g.y)
                if p_dist <= GRENADE_RADIUS:
                    self.player.health -= 100
                    self.particles.add_floating_text(self.player.x, self.player.y, "100", (255, 0, 0))
                    if self.player.health <= 0:
                        self.game_over = True

                # Break breakables
                for brk in list(self.breakables):
                    brk_cx = brk.x + brk.width // 2
                    brk_cy = brk.y + brk.height // 2
                    if math.hypot(brk_cx - g.x, brk_cy - g.y) <= GRENADE_RADIUS + brk.width // 2:
                        brk.health = 0
                        if random.random() < 0.3:
                            drop_types = ['health', 'stamina', 'ak47', 'shotgun']
                            self.items.append(Item(brk.x + brk.width // 2, brk.y + brk.height // 2,
                                                   random.choice(drop_types)))
                        self.particles.add_blood(brk_cx, brk_cy, 15, color=(139, 69, 19))
                        self.breakables.remove(brk)
                        assets.channels['knife_damage'].play(assets.sounds['knife_damage'])

                # Kill zombies within radius
                for z in list(self.zombies):
                    zx = z.x + z.size // 2
                    zy = z.y + z.size // 2
                    dist = math.hypot(zx - g.x, zy - g.y)
                    if dist <= GRENADE_RADIUS:
                        damage = 100
                        z.health -= damage
                        z.hit_flash_timer = current_time
                        self.particles.add_blood(zx, zy, 25)
                        self.particles.add_floating_text(zx, zy - 10, str(damage), (255, 100, 100))
                        self.network.send_entity_damage("zombie", z.entity_id, damage, z.health)
                        if z.health <= 0:
                            self.zombies.remove(z)
                            self.handle_zombie_death(z)
            if not g.active:
                self.grenades.remove(g)

    def update_sentries(self, current_time):
        for s in list(self.sentries_deployed):
            target = s.update(self.zombies, current_time)
            if target:
                assets.channels['pistol'].play(assets.sounds['pistol'])
                dx = math.cos(s.angle)
                dy = math.sin(s.angle)
                self.bullets.append(Bullet(s.x, s.y, dx, dy, 15, spread=3))
                self.particles.add_casing(s.x, s.y, s.angle)
                self.particles.add_muzzle_flash(s.x + dx * s.size, s.y + dy * s.size, s.angle)
            if s.ammo <= 0:
                self.sentries_deployed.remove(s)
                self.particles.add_blood(s.x, s.y, 20, color=(100, 100, 100))

    # ================================================================
    # DRAWING
    # ================================================================

    def draw_grid(self, surface):
        grid_color = (30, 30, 45)
        grid_size = 40
        for x in range(0, self.width, grid_size):
            pygame.draw.line(surface, grid_color, (x, 0), (x, self.height))
        for y in range(0, self.height, grid_size):
            pygame.draw.line(surface, grid_color, (0, y), (self.width, y))

    def draw(self):
        offset_x = 0
        offset_y = 0
        if self.screen_shake > 0:
            offset_x = random.randint(-self.screen_shake, self.screen_shake)
            offset_y = random.randint(-self.screen_shake, self.screen_shake)
            self.screen_shake -= 1

        shake_surface = pygame.Surface((self.width, self.height))
        shake_surface.fill((18, 18, 28))
        self.draw_grid(shake_surface)

        # Draw obstacles
        for obs in self.obstacles:
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
            px = self.player.x + PLAYER_SIZE // 2
            py = self.player.y + PLAYER_SIZE // 2
            mx, my = pygame.mouse.get_pos()
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

            line_color = (200, 50, 50, 150)
            dash_length = 10
            dash_count = int(math.hypot(target_x - px, target_y - py) / dash_length)
            for i in range(dash_count):
                if i % 2 == 0:
                    start_pos = (
                        px + (target_x - px) * (i / dash_count), py + (target_y - py) * (i / dash_count))
                    end_pos = (px + (target_x - px) * ((i + 1) / dash_count),
                               py + (target_y - py) * ((i + 1) / dash_count))
                    pygame.draw.line(shake_surface, line_color, start_pos, end_pos, 2)

            preview_surface = pygame.Surface((GRENADE_RADIUS * 2, GRENADE_RADIUS * 2), pygame.SRCALPHA)
            pygame.draw.circle(preview_surface, (255, 50, 50, 80), (GRENADE_RADIUS, GRENADE_RADIUS), GRENADE_RADIUS)
            pygame.draw.circle(preview_surface, (255, 50, 50, 200), (GRENADE_RADIUS, GRENADE_RADIUS), GRENADE_RADIUS,
                               1)
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

        # Draw remote players
        for rp in self.remote_players.values():
            rp.draw(shake_surface)

        # Draw local player
        self.player.draw(shake_surface, pygame.mouse.get_pos(), draw_name=True)

        # Vignette
        shake_surface.fill((0, 0, 20, 30), special_flags=pygame.BLEND_RGBA_SUB)

        # FOV cone
        if game_settings.get("fov", False):
            px = self.player.x + PLAYER_SIZE // 2
            py = self.player.y + PLAYER_SIZE // 2
            mx, my = pygame.mouse.get_pos()
            angle = math.atan2(my - py, mx - px)

            fov_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            fov_surface.fill((0, 0, 0, 255))

            fov_angle = math.radians(90)
            fov_dist = max(self.width, self.height) * 1.5
            num_points = 30
            cone_points = [(px, py)]
            for i in range(num_points + 1):
                a = angle - fov_angle / 2 + (fov_angle * i / num_points)
                cone_points.append((px + math.cos(a) * fov_dist, py + math.sin(a) * fov_dist))

            pygame.draw.polygon(fov_surface, (0, 0, 0, 0), cone_points)
            pygame.draw.circle(fov_surface, (0, 0, 0, 0), (int(px), int(py)), 80)

            shake_surface.blit(fov_surface, (0, 0))

        self.surface.blit(shake_surface, (offset_x, offset_y))

        # HUD
        self.hud.draw(self.surface, self.player, self.wave, len(self.zombies), self.zombies_required)

        # Draw multiplayer player count indicator
        alive_count = 1 + sum(1 for rp in self.remote_players.values() if rp.is_alive)
        total_count = 1 + len(self.remote_players)
        mp_txt = assets.fonts['small'].render(f"Oyuncular: {alive_count}/{total_count}", True, (150, 255, 150))
        self.surface.blit(mp_txt, (10, 120))

        # Crosshair
        draw_crosshair(self.surface, *pygame.mouse.get_pos(), 15, game_settings["bullet_color"])

    # ================================================================
    # MAIN GAME LOOP
    # ================================================================

    def run(self):
        clock = pygame.time.Clock()
        pygame.mouse.set_visible(False)

        update_discord_presence(game_state="Multiplayer")

        while True:
            dt = clock.tick(60)
            current_time = pygame.time.get_ticks()
            self.particles.update(dt)

            # Process network messages
            self.process_network_messages()

            # Interpolate remote players
            for rp in self.remote_players.values():
                rp.interpolate(MULTIPLAYER_INTERPOLATION_SPEED)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.network.leave_room()
                    self.network.disconnect()
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.network.leave_room()
                        pygame.mouse.set_visible(True)
                        return "main_menu"
                    if event.key == pygame.K_r and self.player.current_weapon == "pistol":
                        wp = weapons_data[self.player.current_weapon]
                        if self.player.bullets_in_magazine < wp["max_ammo"]:
                            assets.channels['reload'].play(assets.sounds['reload'])
                            self.player.bullets_in_magazine = wp["max_ammo"]
                    if event.key == pygame.K_t:
                        if self.player.sentries > 0:
                            self.player.sentries -= 1
                            center_x = self.player.x + PLAYER_SIZE // 2
                            center_y = self.player.y + PLAYER_SIZE // 2
                            self.sentries_deployed.append(SentryGun(center_x, center_y))
                            self.network.send_sentry_place(center_x, center_y)

            if self.game_over:
                pygame.mouse.set_visible(True)
                update_discord_presence(wave=self.wave, zombies_killed=self.total_kills, game_state="MP Game Over")
                res = self.menu.show_game_over(self.surface, self.wave, self.total_kills)
                if res == "main_menu":
                    self.network.leave_room()
                    return "main_menu"
                elif res == "quit":
                    self.network.leave_room()
                    self.network.disconnect()
                    pygame.quit()
                    sys.exit()

            # Handle Knife Swing state
            if self.player.knife_swing:
                if pygame.time.get_ticks() - self.player.knife_start_time > weapons_data["knife"]["swing_duration"]:
                    self.player.knife_swing = False

            # Wave management (host only)
            if self.is_host:
                if len(self.zombies) == 0 and self.zombies_killed_in_wave >= self.zombies_required:
                    self.wave += 1
                    self.zombies_killed_in_wave = 0
                    self.zombies_required = int(self.zombies_required * 1.5)
                    self.menu.show_wave_transition(self.surface, self.wave)
                    self.spawn_wave()
                    self.spawn_wave_items()
                    self.network.send_wave_change(self.wave, self.zombies_required)
                elif len(self.zombies) < 5:
                    self.spawn_wave()

            self.update_sentries(current_time)
            self.handle_input(dt)
            self.handle_shooting(pygame.mouse.get_pos())
            self.update_zombies()
            self.update_bullets()
            self.update_grenades(current_time)
            self.update_items()

            # Send local state
            self.send_local_state()

            update_discord_presence(wave=self.wave, zombies_killed=self.total_kills, game_state="Multiplayer")

            self.draw()
            pygame.display.flip()
