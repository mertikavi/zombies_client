import pygame
import math
import random
from config import game_settings

_particle_cache = {}

class Particle:
    def __init__(self, x, y, color, size, speed, angle, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.initial_size = size
        self.speed = speed
        self.angle = angle
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.friction = 0.92

    def update(self, dt):
        self.x += self.dx
        self.y += self.dy
        self.dx *= self.friction
        self.dy *= self.friction
        self.lifetime -= dt
        
        # Shrink over time
        progress = self.lifetime / self.max_lifetime
        self.size = max(0.1, self.initial_size * progress)
        return self.lifetime > 0

    def draw(self, surface):
        if self.lifetime <= 0:
            return
        
        sz = int(self.size)
        if sz <= 3:
            # Direct draw for small particles (blood, casings, sparks) - zero surface allocations!
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), max(1, sz))
        else:
            # Cached alpha surface for larger particles (muzzle flashes, explosions)
            alpha = max(0, min(255, int(255 * (self.lifetime / self.max_lifetime))))
            alpha_bucket = (alpha // 30) * 30
            cache_key = (sz, self.color, alpha_bucket)
            if cache_key not in _particle_cache:
                s = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.color, alpha_bucket), (sz, sz), sz)
                _particle_cache[cache_key] = s
            surface.blit(_particle_cache[cache_key], (int(self.x - sz), int(self.y - sz)))


class FloatingText:
    def __init__(self, x, y, text, color, lifetime=1000):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.dy = -1.5 # Float upwards
        self.surf = None

    def update(self, dt):
        self.y += self.dy
        self.lifetime -= dt
        return self.lifetime > 0

    def draw(self, surface, font):
        if self.lifetime > 0:
            if self.surf is None and font is not None:
                self.surf = font.render(self.text, True, self.color)
            if self.surf:
                alpha = max(0, min(255, int(255 * (self.lifetime / self.max_lifetime))))
                self.surf.set_alpha(alpha)
                surface.blit(self.surf, (int(self.x), int(self.y)))


class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.floating_texts = []
        
    def add_floating_text(self, x, y, text, color=(255, 255, 255)):
        # Randomize x slightly so texts don't perfectly overlap
        self.floating_texts.append(FloatingText(x + random.uniform(-10, 10), y, text, color))
        
    def add_blood(self, x, y, count=10, color=(200, 0, 0)):
        g_qual = game_settings.get("graphics_quality", "Orta")
        if g_qual == "Düşük":
            count = max(3, count // 3)
        elif g_qual == "Orta":
            count = max(5, int(count * 0.7))
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 6)
            size = random.uniform(2, 5)
            lifetime = random.uniform(200, 600)
            color = (random.randint(150, 255), 0, 0)
            self.particles.append(Particle(x, y, color, size, speed, angle, lifetime))
            
    def add_casing(self, x, y, weapon_angle):
        # Eject to the right side of the weapon
        angle = weapon_angle + math.pi/2 + random.uniform(-0.3, 0.3)
        speed = random.uniform(3, 7)
        size = 2
        lifetime = random.uniform(300, 500)
        color = (255, 215, 0) # Gold
        self.particles.append(Particle(x, y, color, size, speed, angle, lifetime))
        
    def add_muzzle_flash(self, x, y, angle):
        # Flash is just a big bright short-lived particle
        self.particles.append(Particle(x, y, (255, 255, 200), size=15, speed=0, angle=0, lifetime=50))
        self.particles.append(Particle(x, y, (255, 150, 50), size=25, speed=0, angle=0, lifetime=30))

    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]
        self.floating_texts = [ft for ft in self.floating_texts if ft.update(dt)]
        # Cap particle counts dynamically based on graphics quality
        g_qual = game_settings.get("graphics_quality", "Orta")
        max_p = 200 if g_qual == "Yüksek" else (100 if g_qual == "Orta" else 50)
        max_ft = 30 if g_qual == "Yüksek" else (20 if g_qual == "Orta" else 12)
        if len(self.particles) > max_p:
            self.particles = self.particles[-max_p:]
        if len(self.floating_texts) > max_ft:
            self.floating_texts = self.floating_texts[-max_ft:]

    def draw(self, surface, font=None):
        for p in self.particles:
            p.draw(surface)
        if font:
            for ft in self.floating_texts:
                ft.draw(surface, font)
