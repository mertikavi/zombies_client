import pygame
import math
import random

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
        if self.lifetime > 0:
            alpha = int(255 * (self.lifetime / self.max_lifetime))
            s = pygame.Surface((int(self.size*2), int(self.size*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (int(self.size), int(self.size)), int(self.size))
            surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))


class FloatingText:
    def __init__(self, x, y, text, color, lifetime=1000):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.dy = -1.5 # Float upwards

    def update(self, dt):
        self.y += self.dy
        self.lifetime -= dt
        return self.lifetime > 0

    def draw(self, surface, font):
        if self.lifetime > 0:
            alpha = int(255 * (self.lifetime / self.max_lifetime))
            txt_surf = font.render(self.text, True, self.color)
            txt_surf.set_alpha(alpha)
            surface.blit(txt_surf, (int(self.x), int(self.y)))


class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.floating_texts = []
        
    def add_floating_text(self, x, y, text, color=(255, 255, 255)):
        # Randomize x slightly so texts don't perfectly overlap
        self.floating_texts.append(FloatingText(x + random.uniform(-10, 10), y, text, color))
        
    def add_blood(self, x, y, count=10, color=(200, 0, 0)):
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

    def draw(self, surface, font=None):
        for p in self.particles:
            p.draw(surface)
        if font:
            for ft in self.floating_texts:
                ft.draw(surface, font)
