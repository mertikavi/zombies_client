import pygame
from config import *
from assets import assets

class HUD:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.display_health = MAX_PLAYER_HEALTH
        self.display_stamina = MAX_PLAYER_STAMINA

    def draw_glass_panel(self, surface, rect):
        s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        # Softer dark glass
        pygame.draw.rect(s, (10, 15, 25, 120), (0, 0, rect[2], rect[3]), border_radius=10)
        # Highlight border
        pygame.draw.rect(s, (255, 255, 255, 60), (0, 0, rect[2], rect[3]), 1, border_radius=10)
        surface.blit(s, (rect[0], rect[1]))

    def draw(self, surface, player, wave, zombies_alive, zombies_required):
        # Lerp values
        self.display_health += (player.health - self.display_health) * 0.1
        self.display_stamina += (player.stamina - self.display_stamina) * 0.1
        
        # Glass Panel for Bars
        self.draw_glass_panel(surface, (10, 10, 360, 100))
        
        # Health Bar
        h_txt = assets.fonts['normal'].render("CAN", True, WHITE)
        surface.blit(h_txt, (20, 25))
        
        bar_w = 220
        h_fill_w = max(0, int((self.display_health / MAX_PLAYER_HEALTH) * bar_w))
        # Draw shadow for bar
        pygame.draw.rect(surface, (0,0,0,150), (120, 30, bar_w, 20), border_radius=5)
        pygame.draw.rect(surface, (50, 0, 0), (120, 30, bar_w, 20), border_radius=5) # bg
        if h_fill_w > 0:
            pygame.draw.rect(surface, (255, 50, 50), (120, 30, h_fill_w, 20), border_radius=5)
            
        # Stamina Bar
        s_txt = assets.fonts['normal'].render("ENERJİ", True, WHITE)
        surface.blit(s_txt, (20, 65))
        
        s_fill_w = max(0, int((self.display_stamina / MAX_PLAYER_STAMINA) * bar_w))
        pygame.draw.rect(surface, (0,0,0,150), (120, 70, bar_w, 20), border_radius=5)
        pygame.draw.rect(surface, (0, 0, 50), (120, 70, bar_w, 20), border_radius=5) # bg
        if s_fill_w > 0:
            pygame.draw.rect(surface, (50, 150, 255), (120, 70, s_fill_w, 20), border_radius=5)

        # Glass Panel for Weapon Info
        self.draw_glass_panel(surface, (self.width - 270, 10, 260, 130))
        
        # Draw Weapon Info
        wp_name = player.current_weapon.upper()
        if player.current_weapon == "knife":
            ammo_str = "∞"
        else:
            ammo_str = f"{player.bullets_in_magazine} / {player.inventory[player.current_weapon]['ammo']}"
            
        wp_text = assets.fonts['normal'].render(f"Silah: {wp_name}", True, WHITE)
        ammo_text = assets.fonts['normal'].render(f"Mermi: {ammo_str}", True, WHITE)
        grenade_text = assets.fonts['normal'].render(f"Bomba: {player.grenades}/{player.max_grenades}", True, WHITE)
        
        # Drop shadow for text
        surface.blit(assets.fonts['normal'].render(f"Silah: {wp_name}", True, BLACK), (self.width - 250 + 2, 20 + 2))
        surface.blit(assets.fonts['normal'].render(f"Mermi: {ammo_str}", True, BLACK), (self.width - 250 + 2, 60 + 2))
        
        surface.blit(wp_text, (self.width - 250, 20))
        surface.blit(ammo_text, (self.width - 250, 60))
        surface.blit(grenade_text, (self.width - 250, 100))

        # Glass Panel for Wave Info
        self.draw_glass_panel(surface, (self.width - 220, 150, 210, 130))

        # Draw Wave Info
        wave_txt = assets.fonts['normal'].render(f"Wave: {wave}", True, WHITE)
        req_txt = assets.fonts['normal'].render(f"Hedef: {zombies_required}", True, WHITE)
        left_txt = assets.fonts['normal'].render(f"Kalan: {zombies_alive}", True, WHITE)
        
        surface.blit(assets.fonts['normal'].render(f"Wave: {wave}", True, BLACK), (self.width - 200 + 2, 160 + 2))
        
        surface.blit(wave_txt, (self.width - 200, 160))
        surface.blit(req_txt, (self.width - 200, 200))
        surface.blit(left_txt, (self.width - 200, 240))

        # Draw Inventory
        self.draw_inventory(surface, player)

    def draw_inventory(self, surface, player):
        inv_start_y = self.height - 250
        spacing = 80
        inv_x = self.width - 100
        
        weapons_to_draw = []
        # Slot 3: Knife
        weapons_to_draw.append(("knife", inv_start_y + spacing * 2))
        # Slot 2: Pistol
        weapons_to_draw.append(("pistol", inv_start_y + spacing))
        # Slot 1: Primary (AK47, Shotgun, or Flamethrower)
        slot1_weapon = player.inventory.get("slot1")
        if slot1_weapon and player.inventory[slot1_weapon]["owned"]:
            weapons_to_draw.append((slot1_weapon, inv_start_y))

        for weapon_name, y_pos in weapons_to_draw:
            # Slot BG
            slot_bg = pygame.Surface((60, 60), pygame.SRCALPHA)
            color = (100, 255, 100, 100) if weapon_name == player.current_weapon else (50, 50, 50, 150)
            pygame.draw.rect(slot_bg, color, (0, 0, 60, 60), border_radius=10)
            surface.blit(slot_bg, (inv_x - 5, y_pos - 5))
            
            # Weapon Image
            weapon_surf = assets.weapon_models[weapon_name].copy()
            if weapon_name == player.current_weapon:
                weapon_surf.set_alpha(255)
            else:
                weapon_surf.set_alpha(128)
            
            surface.blit(pygame.transform.scale(weapon_surf, (50, 50)), (inv_x, y_pos))
            
            # Ammo Text
            if weapon_name == "knife":
                ammo_text = "1/1"
            else:
                current_ammo = player.inventory[weapon_name]["ammo"] if weapon_name != player.current_weapon else player.bullets_in_magazine
                max_ammo = weapons_data[weapon_name]["max_ammo"]
                ammo_text = f"{current_ammo}/{max_ammo}"
                
            ammo_surf = assets.fonts['small'].render(ammo_text, True, WHITE)
            surface.blit(ammo_surf, (inv_x + 25 - ammo_surf.get_width()//2, y_pos + 50))


class Menu:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def show_main_menu(self, surface, is_paused=False):
        menu_state = "main"
        selected = 0
        clock = pygame.time.Clock()
        
        if not assets.channels['background'].get_busy():
            assets.channels['background'].play(assets.sounds['background'], -1)

        options = ["Devam Et", "Ayarlar", "Ana Menüye Dön"] if is_paused else ["Oyna", "Ayarlar", "Çıkış"]

        while True:
            # Modern Grid Background for Menu
            surface.fill((18, 18, 28))
            grid_color = (30, 30, 45)
            for x in range(0, self.width, 40):
                pygame.draw.line(surface, grid_color, (x, 0), (x, self.height))
            for y in range(0, self.height, 40):
                pygame.draw.line(surface, grid_color, (0, y), (self.width, y))
            
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            surface.blit(overlay, (0, 0))

            title_str = "Oyun Duraklatıldı" if is_paused else "ZOMBİ KAÇIŞI"
            title = assets.fonts['large'].render(title_str, True, WHITE)
            # Title Shadow
            title_shadow = assets.fonts['large'].render(title_str, True, BLACK)
            surface.blit(title_shadow, (self.width//2 - title.get_width()//2 + 4, self.height//2 - 200 + 4))
            surface.blit(title, (self.width//2 - title.get_width()//2, self.height//2 - 200))

            if menu_state == "main":
                # Glass Panel for menu options
                panel_w, panel_h = 300, len(options) * 70 + 40
                HUD(self.width, self.height).draw_glass_panel(surface, (self.width//2 - panel_w//2, self.height//2 - 80, panel_w, panel_h))
                
                for i, opt in enumerate(options):
                    color = (50, 255, 100) if i == selected else WHITE
                    txt = assets.fonts['normal'].render(opt, True, color)
                    # Add simple hover effect
                    offset = 15 if i == selected else 0
                    if i == selected:
                        pygame.draw.rect(surface, (255, 255, 255, 20), (self.width//2 - panel_w//2 + 10, self.height//2 - 60 + i * 70, panel_w - 20, 50), border_radius=5)
                    surface.blit(txt, (self.width//2 - txt.get_width()//2 + offset, self.height//2 - 50 + i * 70))
            elif menu_state == "settings":
                char_c_name = next(k for k, v in CHARACTER_COLORS.items() if v == game_settings['character_color'])
                bull_c_name = next(k for k, v in BULLET_COLORS.items() if v == game_settings['bullet_color'])
                
                settings_opts = [
                    f"Zorluk: {game_settings['difficulty']}",
                    f"Karakter Rengi: {char_c_name}",
                    f"Mermi Rengi: {bull_c_name}",
                    f"Müzik: {'Açık' if game_settings['music'] else 'Kapalı'}",
                    f"Ses Efektleri: {'Açık' if game_settings['sound'] else 'Kapalı'}",
                    f"Görüş Alanı (FOV): {'Açık' if game_settings['fov'] else 'Kapalı'}",
                    "Geri"
                ]
                panel_w, panel_h = 400, len(settings_opts) * 70 + 40
                HUD(self.width, self.height).draw_glass_panel(surface, (self.width//2 - panel_w//2, self.height//2 - 80, panel_w, panel_h))
                
                for i, opt in enumerate(settings_opts):
                    color = (50, 255, 100) if i == selected else WHITE
                    txt = assets.fonts['normal'].render(opt, True, color)
                    offset = 15 if i == selected else 0
                    if i == selected:
                        pygame.draw.rect(surface, (255, 255, 255, 20), (self.width//2 - panel_w//2 + 10, self.height//2 - 60 + i * 70, panel_w - 20, 50), border_radius=5)
                    surface.blit(txt, (self.width//2 - txt.get_width()//2 + offset, self.height//2 - 50 + i * 70))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    opts_len = len(settings_opts) if menu_state == "settings" else 3
                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % opts_len
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % opts_len
                    elif event.key == pygame.K_RETURN:
                        if menu_state == "main":
                            if selected == 0:
                                return "resume" if is_paused else "play"
                            elif selected == 1:
                                menu_state = "settings"
                                selected = 0
                            elif selected == 2:
                                if is_paused:
                                    return "main_menu"
                                else:
                                    return "quit"
                        elif menu_state == "settings":
                            if selected == 0:
                                diffs = ["Kolay", "Normal", "Zor"]
                                idx = diffs.index(game_settings["difficulty"])
                                game_settings["difficulty"] = diffs[(idx + 1) % 3]
                            elif selected == 1:
                                colors = list(CHARACTER_COLORS.items())
                                idx = next(i for i, (k, v) in enumerate(colors) if v == game_settings["character_color"])
                                game_settings["character_color"] = colors[(idx + 1) % len(colors)][1]
                                assets.recolor_weapons(game_settings["character_color"])
                            elif selected == 2:
                                colors = list(BULLET_COLORS.items())
                                idx = next(i for i, (k, v) in enumerate(colors) if v == game_settings["bullet_color"])
                                game_settings["bullet_color"] = colors[(idx + 1) % len(colors)][1]
                            elif selected == 3:
                                game_settings["music"] = not game_settings["music"]
                                assets.update_volumes()
                            elif selected == 4:
                                game_settings["sound"] = not game_settings["sound"]
                                assets.update_volumes()
                            elif selected == 5:
                                game_settings["fov"] = not game_settings["fov"]
                            elif selected == 6:
                                menu_state = "main"
                                selected = 0

            clock.tick(60)

    def show_game_over(self, surface, wave, total_kills):
        # Modern Grid Background for Game Over
        surface.fill((18, 18, 28))
        grid_color = (30, 30, 45)
        for x in range(0, self.width, 40):
            pygame.draw.line(surface, grid_color, (x, 0), (x, self.height))
        for y in range(0, self.height, 40):
            pygame.draw.line(surface, grid_color, (0, y), (self.width, y))
            
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((50, 0, 0, 100)) # Dark red tint
        surface.blit(overlay, (0, 0))

        title = assets.fonts['large'].render("GAME OVER", True, (255, 50, 50))
        title_shadow = assets.fonts['large'].render("GAME OVER", True, BLACK)
        
        # Glass panel
        panel_w, panel_h = 400, 200
        HUD(self.width, self.height).draw_glass_panel(surface, (self.width//2 - panel_w//2, self.height//2 - 80, panel_w, panel_h))
        
        wave_txt = assets.fonts['normal'].render(f"Ulaştığın Dalga: {wave}", True, WHITE)
        kills_txt = assets.fonts['normal'].render(f"Öldürdüğün Zombi: {total_kills}", True, WHITE)
        restart_txt = assets.fonts['normal'].render("Ana Menü için bir tuşa bas...", True, (100, 255, 100))
        
        surface.blit(title_shadow, (self.width//2 - title.get_width()//2 + 4, self.height//2 - 160 + 4))
        surface.blit(title, (self.width//2 - title.get_width()//2, self.height//2 - 160))
        
        surface.blit(wave_txt, (self.width//2 - wave_txt.get_width()//2, self.height//2 - 30))
        surface.blit(kills_txt, (self.width//2 - kills_txt.get_width()//2, self.height//2 + 20))
        surface.blit(restart_txt, (self.width//2 - restart_txt.get_width()//2, self.height//2 + 80))
        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    waiting = False
        return "main_menu"

    def show_wave_transition(self, surface, wave):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) # Dark transparent background
        surface.blit(overlay, (0, 0))
        
        txt = assets.fonts['large'].render(f"DALGA {wave}", True, RED)
        sub_txt = assets.fonts['normal'].render("Hazırlan...", True, WHITE)
        
        surface.blit(txt, (self.width//2 - txt.get_width()//2, self.height//2 - 50))
        surface.blit(sub_txt, (self.width//2 - sub_txt.get_width()//2, self.height//2 + 30))
        
        pygame.display.flip()
        
        # Wait a bit and clear events so player doesn't accidentally skip or shoot during transition
        pygame.time.delay(2000)
        pygame.event.clear()

