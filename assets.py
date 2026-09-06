import pygame
import os
from config import *

class AssetManager:
    def __init__(self):
        self.fonts = {}
        self.images = {}
        self.weapon_models = {}
        self.sounds = {}
        self.channels = {}
        
    def load_all(self, width, height):
        # Initialize mixer
        pygame.mixer.init()
        pygame.mixer.set_num_channels(11)
        
        # Load Fonts
        pygame.font.init()
        self.fonts['normal'] = pygame.font.SysFont("segoeui", 24, bold=True)
        self.fonts['large'] = pygame.font.SysFont("segoeui", 48, bold=True)
        self.fonts['small'] = pygame.font.SysFont("segoeui", 16)
        
        # Intro Logo (keep aspect ratio)
        intro_logo = pygame.image.load("./logos/logo_text.png").convert_alpha()
        original_width = intro_logo.get_width()
        original_height = intro_logo.get_height()
        aspect_ratio = original_width / original_height
        target_width = width // 2
        target_height = int(target_width / aspect_ratio)
        self.images['logo'] = pygame.transform.scale(intro_logo, (target_width, target_height))
        
        # Load Weapons
        self.WEAPON_ICON_SIZE = (70, 70)
        self._load_and_color_weapons(game_settings["character_color"])

        # Load Sounds
        self.sounds['background'] = pygame.mixer.Sound("./sound/background.mp3")
        self.sounds['intro'] = pygame.mixer.Sound("./sound/intro.mp3")
        self.sounds['walk'] = pygame.mixer.Sound("./sound/walk.mp3")
        self.sounds['pistol'] = pygame.mixer.Sound("./sound/pistol.mp3")
        self.sounds['ak47'] = pygame.mixer.Sound("./sound/ak47.mp3")
        self.sounds['shotgun'] = pygame.mixer.Sound("./sound/shotgun.mp3")
        self.sounds['reload'] = pygame.mixer.Sound("./sound/reload.mp3")
        self.sounds['health'] = pygame.mixer.Sound("./sound/health.mp3")
        self.sounds['empty'] = pygame.mixer.Sound("./sound/empty.mp3")
        self.sounds['knife_air'] = pygame.mixer.Sound("./sound/knife_air.mp3")
        self.sounds['knife_damage'] = pygame.mixer.Sound("./sound/knife_damage.mp3")
        self.sounds['grenade'] = pygame.mixer.Sound("./sound/grenade.mp3")
        
        self.sounds['flamethrower'] = pygame.mixer.Sound("./sound/flamethrower.mp3")

        # Setup Channels
        pygame.mixer.set_num_channels(16)
        self.channels['walk'] = pygame.mixer.Channel(0)
        self.channels['pistol'] = pygame.mixer.Channel(1)
        self.channels['ak47'] = pygame.mixer.Channel(2)
        self.channels['shotgun'] = pygame.mixer.Channel(3)
        self.channels['reload'] = pygame.mixer.Channel(4)
        self.channels['health'] = pygame.mixer.Channel(5)
        self.channels['empty'] = pygame.mixer.Channel(6)
        self.channels['knife_air'] = pygame.mixer.Channel(7)
        self.channels['knife_damage'] = pygame.mixer.Channel(8)
        self.channels['intro'] = pygame.mixer.Channel(9)
        self.channels['background'] = pygame.mixer.Channel(10)
        self.channels['grenade'] = pygame.mixer.Channel(11)
        self.channels['flamethrower'] = pygame.mixer.Channel(12)
        self.update_volumes()

    def update_volumes(self):
        bg_vol = 0.3 if game_settings.get("music", True) else 0
        sfx_vol = 0.5 if game_settings.get("sound", True) else 0
        
        self.sounds['background'].set_volume(bg_vol)
        for name, sound in self.sounds.items():
            if name != 'background':
                sound.set_volume(sfx_vol)

    def recolor_weapons(self, color):
        self._load_and_color_weapons(color)

    def _load_and_color_weapons(self, color):
        weapons_list = ["knife", "pistol", "ak47", "shotgun", "flamethrower"]
        for weapon in weapons_list:
            try:
                original = pygame.image.load(f"./models/{weapon}.png").convert_alpha()
                scaled = pygame.transform.scale(original, self.WEAPON_ICON_SIZE)
                
                # Create a colored surface
                colored_surface = pygame.Surface(self.WEAPON_ICON_SIZE, pygame.SRCALPHA)
                colored_surface.fill((*color, 255))
                
                scaled.set_alpha(255)
                colored_surface.blit(scaled, (0, 0))
                
                final_weapon = colored_surface.copy()
                final_weapon.blit(colored_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                
                self.weapon_models[weapon] = final_weapon
            except FileNotFoundError:
                # Fallback icon if missing
                fallback = pygame.Surface(self.WEAPON_ICON_SIZE, pygame.SRCALPHA)
                pygame.draw.rect(fallback, (*color, 255), (10, 20, 50, 30), border_radius=5)
                text = self.fonts['small'].render(weapon[:3].upper(), True, (0,0,0))
                fallback.blit(text, (self.WEAPON_ICON_SIZE[0]//2 - text.get_width()//2, self.WEAPON_ICON_SIZE[1]//2 - text.get_height()//2))
                self.weapon_models[weapon] = fallback

# Singleton instance to be shared across modules
assets = AssetManager()
