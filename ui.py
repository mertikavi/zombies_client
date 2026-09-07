import pygame
import math
from config import *
from assets import assets
from utils import get_shadow_surface, create_glow_surface

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
        self.draw_glass_panel(surface, (self.width - 270, 10, 260, 165))
        
        # Draw Weapon Info
        wp_name = player.current_weapon.upper()
        if player.current_weapon == "knife":
            ammo_str = "SONSUZ"
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
        
        sentry_text = assets.fonts['normal'].render(f"Taret: {player.sentries}/{player.max_sentries}", True, WHITE)
        surface.blit(sentry_text, (self.width - 250, 135))

        # Glass Panel for Wave Info
        self.draw_glass_panel(surface, (self.width - 220, 190, 210, 130))

        # Draw Wave Info
        wave_txt = assets.fonts['normal'].render(f"Wave: {wave}", True, WHITE)
        req_txt = assets.fonts['normal'].render(f"Hedef: {zombies_required}", True, WHITE)
        left_txt = assets.fonts['normal'].render(f"Kalan: {zombies_alive}", True, WHITE)
        
        surface.blit(assets.fonts['normal'].render(f"Wave: {wave}", True, BLACK), (self.width - 200 + 2, 200 + 2))
        
        surface.blit(wave_txt, (self.width - 200, 200))
        surface.blit(req_txt, (self.width - 200, 240))
        surface.blit(left_txt, (self.width - 200, 280))

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

    def _draw_background(self, surface):
        """Draw the common grid background for menus."""
        surface.fill((18, 18, 28))
        grid_color = (30, 30, 45)
        for x in range(0, self.width, 40):
            pygame.draw.line(surface, grid_color, (x, 0), (x, self.height))
        for y in range(0, self.height, 40):
            pygame.draw.line(surface, grid_color, (0, y), (self.width, y))
        
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        surface.blit(overlay, (0, 0))

    def _draw_title(self, surface, title_str, y_offset=-200):
        """Draw a title with shadow."""
        title = assets.fonts['large'].render(title_str, True, WHITE)
        title_shadow = assets.fonts['large'].render(title_str, True, BLACK)
        surface.blit(title_shadow, (self.width//2 - title.get_width()//2 + 4, self.height//2 + y_offset + 4))
        surface.blit(title, (self.width//2 - title.get_width()//2, self.height//2 + y_offset))

    def _draw_menu_options(self, surface, options, selected, panel_w=300, y_start=-80):
        """Draw a list of menu options with glass panel."""
        panel_h = len(options) * 70 + 40
        HUD(self.width, self.height).draw_glass_panel(
            surface, (self.width//2 - panel_w//2, self.height//2 + y_start, panel_w, panel_h)
        )
        
        for i, opt in enumerate(options):
            color = (50, 255, 100) if i == selected else WHITE
            txt = assets.fonts['normal'].render(opt, True, color)
            offset = 15 if i == selected else 0
            if i == selected:
                pygame.draw.rect(surface, (255, 255, 255, 20),
                    (self.width//2 - panel_w//2 + 10, self.height//2 + y_start + 20 + i * 70, panel_w - 20, 50),
                    border_radius=5)
            surface.blit(txt, (self.width//2 - txt.get_width()//2 + offset, self.height//2 + y_start + 30 + i * 70))

    def show_main_menu(self, surface, is_paused=False):
        menu_state = "main"
        selected = 0
        clock = pygame.time.Clock()
        
        if not assets.channels['background'].get_busy():
            assets.channels['background'].play(assets.sounds['background'], -1)

        if is_paused:
            options = ["Devam Et", "Nasıl Oynanır", "Ayarlar", "Ana Menüye Dön"]
        else:
            options = ["Tek Oyunculu", "Çok Oyunculu", "Nasıl Oynanır", "Ayarlar", "Çıkış"]

        while True:
            self._draw_background(surface)

            title_str = "Oyun Duraklatıldı" if is_paused else "ZOMBİ KAÇIŞI"
            self._draw_title(surface, title_str)

            if menu_state == "main":
                self._draw_menu_options(surface, options, selected)
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
                self._draw_menu_options(surface, settings_opts, selected, panel_w=400)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                
                trigger_action = False
                if event.type == pygame.MOUSEMOTION:
                    m_x, m_y = event.pos
                    curr_opts = options if menu_state == "main" else settings_opts
                    cur_pw = 400 if menu_state == "settings" else 300
                    y_start = -80
                    for i in range(len(curr_opts)):
                        btn_rect = pygame.Rect(self.width//2 - cur_pw//2 + 10, self.height//2 + y_start + 20 + i * 70, cur_pw - 20, 50)
                        if btn_rect.collidepoint(m_x, m_y):
                            selected = i
                            break
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    m_x, m_y = event.pos
                    curr_opts = options if menu_state == "main" else settings_opts
                    cur_pw = 400 if menu_state == "settings" else 300
                    y_start = -80
                    for i in range(len(curr_opts)):
                        btn_rect = pygame.Rect(self.width//2 - cur_pw//2 + 10, self.height//2 + y_start + 20 + i * 70, cur_pw - 20, 50)
                        if btn_rect.collidepoint(m_x, m_y):
                            selected = i
                            trigger_action = True
                            break
                elif event.type == pygame.KEYDOWN:
                    if menu_state == "main":
                        opts_len = len(options)
                    else:
                        opts_len = len(settings_opts)

                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % opts_len
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % opts_len
                    elif event.key == pygame.K_ESCAPE:
                        if menu_state == "settings":
                            menu_state = "main"
                            selected = 0
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        trigger_action = True

                if trigger_action:
                    if menu_state == "main":
                        if is_paused:
                            if selected == 0:
                                return "resume"
                            elif selected == 1:
                                self.show_tutorial(surface)
                            elif selected == 2:
                                menu_state = "settings"
                                selected = 0
                            elif selected == 3:
                                return "main_menu"
                        else:
                            if selected == 0:
                                return "play"
                            elif selected == 1:
                                return "multiplayer"
                            elif selected == 2:
                                self.show_tutorial(surface)
                            elif selected == 3:
                                menu_state = "settings"
                                selected = 0
                            elif selected == 4:
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
        self._draw_background(surface)
        
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

    # ================================================================
    # TUTORIAL & OYUN REHBERİ
    # ================================================================

    def show_tutorial(self, surface):
        """Show interactive game tutorial and guide."""
        clock = pygame.time.Clock()
        current_tab = 0  # 0: Kontroller & Oynanış, 1: Zombi Rehberi, 2: Silahlar & Destek
        tabs = [
            "Kontroller & Oynanış",
            "Zombi Rehberi",
            "Silahlar & Destek"
        ]

        # Make sure mouse is visible in tutorial
        pygame.mouse.set_visible(True)

        while True:
            current_time = pygame.time.get_ticks()
            mouse_pos = pygame.mouse.get_pos()

            # Responsive dimensions
            panel_w = min(1100, self.width - 60)
            panel_h = min(680, self.height - 60)
            panel_x = (self.width - panel_w) // 2
            panel_y = (self.height - panel_h) // 2

            # Background & backdrop
            self._draw_background(surface)
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            surface.blit(overlay, (0, 0))

            # Main Glass Panel
            HUD(self.width, self.height).draw_glass_panel(surface, (panel_x, panel_y, panel_w, panel_h))

            # Header / Title
            title_surf = assets.fonts['large'].render("NASIL OYNANIR & OYUN REHBERİ", True, (255, 215, 0))
            surface.blit(title_surf, (panel_x + 35, panel_y + 18))
            
            sub_surf = assets.fonts['small'].render("Hayatta kalmak için kontrolleri, tehlikeli zombi türlerini ve cephaneliğinizi iyi öğrenin.", True, (190, 200, 220))
            surface.blit(sub_surf, (panel_x + 38, panel_y + 70))

            # Close / Back Button (Top Right)
            close_btn_rect = pygame.Rect(panel_x + panel_w - 150, panel_y + 24, 120, 36)
            close_hover = close_btn_rect.collidepoint(mouse_pos)
            self._draw_tutorial_btn(surface, close_btn_rect, "[X] Geri (ESC)", close_hover, bg_color=(180, 40, 40) if close_hover else (70, 25, 25))

            # Tab Buttons Bar
            tab_y = panel_y + 102
            tab_btn_w = (panel_w - 70) // len(tabs)
            tab_rects = []
            for i, tab_title in enumerate(tabs):
                tab_rect = pygame.Rect(panel_x + 35 + i * tab_btn_w, tab_y, tab_btn_w - 12, 40)
                tab_rects.append(tab_rect)
                is_active = (current_tab == i)
                is_hover = tab_rect.collidepoint(mouse_pos)
                self._draw_tutorial_tab_btn(surface, tab_rect, tab_title, is_active, is_hover)

            # Content Area inside the panel
            content_rect = pygame.Rect(panel_x + 35, tab_y + 52, panel_w - 70, panel_h - 170)
            
            if current_tab == 0:
                self._draw_tutorial_controls(surface, content_rect, mouse_pos)
            elif current_tab == 1:
                self._draw_tutorial_zombies(surface, content_rect, current_time)
            elif current_tab == 2:
                self._draw_tutorial_weapons(surface, content_rect, current_time)

            # Bottom Navigation Bar
            prev_btn_rect = pygame.Rect(panel_x + 35, panel_y + panel_h - 52, 140, 36)
            next_btn_rect = pygame.Rect(panel_x + panel_w - 175, panel_y + panel_h - 52, 140, 36)
            
            prev_hover = prev_btn_rect.collidepoint(mouse_pos)
            next_hover = next_btn_rect.collidepoint(mouse_pos)
            
            self._draw_tutorial_btn(surface, prev_btn_rect, "< Önceki (A)", prev_hover, active=(current_tab > 0))
            self._draw_tutorial_btn(surface, next_btn_rect, "Sonraki (D) >", next_hover, active=(current_tab < len(tabs) - 1))

            # Page Indicator in the center bottom
            page_str = f"Sayfa {current_tab + 1} / {len(tabs)}  (Klavye: 1, 2, 3 veya A / D)"
            page_surf = assets.fonts['small'].render(page_str, True, (150, 165, 185))
            surface.blit(page_surf, (panel_x + panel_w//2 - page_surf.get_width()//2, panel_y + panel_h - 43))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        current_tab = (current_tab - 1) % len(tabs)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        current_tab = (current_tab + 1) % len(tabs)
                    elif event.key == pygame.K_1:
                        current_tab = 0
                    elif event.key == pygame.K_2:
                        current_tab = 1
                    elif event.key == pygame.K_3:
                        current_tab = 2
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if close_btn_rect.collidepoint(event.pos):
                        return
                    if prev_btn_rect.collidepoint(event.pos) and current_tab > 0:
                        current_tab -= 1
                    elif next_btn_rect.collidepoint(event.pos) and current_tab < len(tabs) - 1:
                        current_tab += 1
                    for i, t_rect in enumerate(tab_rects):
                        if t_rect.collidepoint(event.pos):
                            current_tab = i
            clock.tick(60)

    def _draw_tutorial_btn(self, surface, rect, text, is_hover=False, active=True, bg_color=None):
        """Draw a sleek button for the tutorial."""
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        if not active:
            pygame.draw.rect(s, (25, 30, 40, 100), (0, 0, rect.width, rect.height), border_radius=8)
            pygame.draw.rect(s, (70, 80, 100, 80), (0, 0, rect.width, rect.height), 1, border_radius=8)
            txt_surf = assets.fonts['small'].render(text, True, (100, 110, 130))
        elif is_hover:
            fill_col = bg_color if bg_color else (45, 90, 160, 220)
            pygame.draw.rect(s, fill_col, (0, 0, rect.width, rect.height), border_radius=8)
            pygame.draw.rect(s, (120, 180, 255, 230), (0, 0, rect.width, rect.height), 2, border_radius=8)
            txt_surf = assets.fonts['small'].render(text, True, WHITE)
        else:
            fill_col = bg_color if bg_color else (25, 40, 70, 180)
            pygame.draw.rect(s, fill_col, (0, 0, rect.width, rect.height), border_radius=8)
            pygame.draw.rect(s, (80, 120, 180, 160), (0, 0, rect.width, rect.height), 1, border_radius=8)
            txt_surf = assets.fonts['small'].render(text, True, (220, 230, 245))
            
        surface.blit(s, (rect.x, rect.y))
        surface.blit(txt_surf, (rect.x + (rect.width - txt_surf.get_width()) // 2, rect.y + (rect.height - txt_surf.get_height()) // 2))

    def _draw_tutorial_tab_btn(self, surface, rect, text, is_active=False, is_hover=False):
        """Draw top tab selection button with glow and bottom indicator."""
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        if is_active:
            pygame.draw.rect(s, (30, 70, 130, 220), (0, 0, rect.width, rect.height), border_radius=8)
            pygame.draw.rect(s, (80, 160, 255, 240), (0, 0, rect.width, rect.height), 2, border_radius=8)
            pygame.draw.rect(s, (255, 215, 0), (8, rect.height - 4, rect.width - 16, 4), border_radius=2)
            txt_surf = assets.fonts['normal'].render(text, True, (255, 255, 255))
        elif is_hover:
            pygame.draw.rect(s, (25, 45, 80, 180), (0, 0, rect.width, rect.height), border_radius=8)
            pygame.draw.rect(s, (100, 150, 220, 180), (0, 0, rect.width, rect.height), 1, border_radius=8)
            txt_surf = assets.fonts['normal'].render(text, True, (220, 240, 255))
        else:
            pygame.draw.rect(s, (15, 22, 35, 140), (0, 0, rect.width, rect.height), border_radius=8)
            pygame.draw.rect(s, (60, 80, 110, 120), (0, 0, rect.width, rect.height), 1, border_radius=8)
            txt_surf = assets.fonts['normal'].render(text, True, (160, 175, 200))
            
        surface.blit(s, (rect.x, rect.y))
        surface.blit(txt_surf, (rect.x + (rect.width - txt_surf.get_width()) // 2, rect.y + (rect.height - txt_surf.get_height()) // 2))

    def _draw_key_badge(self, surface, x, y, key_text, badge_w=None, color=(35, 50, 75)):
        """Draw an arcade-style keycap badge."""
        txt = assets.fonts['small'].render(key_text, True, (240, 245, 255))
        w = max(badge_w or 0, txt.get_width() + 16)
        h = 24
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, color, (0, 0, w, h), border_radius=5)
        pygame.draw.rect(s, (130, 160, 210, 180), (0, 0, w, h), 1, border_radius=5)
        pygame.draw.line(s, (15, 20, 30, 180), (2, h - 2), (w - 2, h - 2), 2)
        surface.blit(s, (x, y))
        surface.blit(txt, (x + (w - txt.get_width()) // 2, y + (h - txt.get_height()) // 2))
        return w

    def _draw_wrapped_text(self, surface, text, font, color, x, y, max_w, line_spacing=18):
        """Helper to draw multi-line wrapped text."""
        words = text.split(' ')
        lines = []
        curr_line = []
        for word in words:
            test_line = ' '.join(curr_line + [word])
            if font.size(test_line)[0] <= max_w:
                curr_line.append(word)
            else:
                if curr_line:
                    lines.append(' '.join(curr_line))
                curr_line = [word]
        if curr_line:
            lines.append(' '.join(curr_line))
            
        curr_y = y
        for line in lines:
            surf = font.render(line, True, color)
            surface.blit(surf, (x, curr_y))
            curr_y += line_spacing
        return curr_y

    def _draw_tutorial_controls(self, surface, rect, mouse_pos):
        """Draw the Controls & Gameplay mechanics tutorial page."""
        col_w = (rect.width - 20) // 2
        
        # Left column: Movement & Survival
        card1_h = 235
        card1_rect = pygame.Rect(rect.x, rect.y, col_w, card1_h)
        HUD(self.width, self.height).draw_glass_panel(surface, (card1_rect.x, card1_rect.y, card1_rect.width, card1_rect.height))
        
        pygame.draw.circle(surface, (100, 220, 255), (card1_rect.x + 22, card1_rect.y + 24), 5)
        title1 = assets.fonts['normal'].render("HAREKET & TEMEL KONTROLLER", True, (100, 220, 255))
        surface.blit(title1, (card1_rect.x + 36, card1_rect.y + 12))
        
        controls = [
            ("W, A, S, D", "Karakteri hareket ettirir (Yukarı / Sol / Aşağı / Sağ)"),
            ("SOL SHIFT", "Hızlı Koşu / Depar (Enerji - Stamina harcar)"),
            ("BOŞLUK", "Ani Kaçış (Dash - 1 sn bekleme, engellerden sıyrılma)"),
            ("ESC", "Oyunu Duraklat / Ayarlar & Çıkış Menüsü")
        ]
        cur_y = card1_rect.y + 52
        for key_label, desc in controls:
            bw = self._draw_key_badge(surface, card1_rect.x + 16, cur_y, key_label, badge_w=95)
            self._draw_wrapped_text(surface, desc, assets.fonts['small'], (220, 230, 240), card1_rect.x + 16 + bw + 12, cur_y + 3, col_w - bw - 40, 18)
            cur_y += 44

        # Card 2: Hayatta Kalma Taktikleri
        card2_y = card1_rect.bottom + 12
        card2_h = rect.bottom - card2_y
        card2_rect = pygame.Rect(rect.x, card2_y, col_w, card2_h)
        HUD(self.width, self.height).draw_glass_panel(surface, (card2_rect.x, card2_rect.y, card2_rect.width, card2_rect.height))
        
        pygame.draw.circle(surface, (255, 215, 0), (card2_rect.x + 22, card2_rect.y + 22), 5)
        title2 = assets.fonts['normal'].render("HAYATTA KALMA TAKTİKLERİ", True, (255, 215, 0))
        surface.blit(title2, (card2_rect.x + 36, card2_rect.y + 10))
        
        tips = [
            ("Sandıklar & Variller", "Haritadaki kutuları ve varilleri vurup kırarak can, stamina, el bombası ve güçlü silahlar bulun."),
            ("Enerji Yönetimi", "Deparı gereksiz yere harcamayın! Zombiler hızlandığında veya köşeye sıkıştığınızda koşu hayat kurtarır."),
            ("Görüş Alanı (FOV)", "Zombiler fenerinizin aydınlattığı açının dışındayken gizlenebilir. Arkanızı sürekli kollayın!")
        ]
        cur_y = card2_rect.y + 44
        for tip_title, tip_desc in tips:
            pygame.draw.circle(surface, (255, 200, 100), (card2_rect.x + 22, cur_y + 8), 3)
            t_surf = assets.fonts['small'].render(tip_title, True, (255, 230, 150))
            surface.blit(t_surf, (card2_rect.x + 32, cur_y))
            cur_y = self._draw_wrapped_text(surface, tip_desc, assets.fonts['small'], (200, 210, 225), card2_rect.x + 32, cur_y + 20, col_w - 48, 17) + 8

        # Right column: Combat & Arsenal
        right_x = rect.x + col_w + 20
        card3_rect = pygame.Rect(right_x, rect.y, col_w, rect.height)
        HUD(self.width, self.height).draw_glass_panel(surface, (card3_rect.x, card3_rect.y, card3_rect.width, card3_rect.height))
        
        pygame.draw.circle(surface, (255, 120, 120), (card3_rect.x + 22, card3_rect.y + 24), 5)
        title3 = assets.fonts['normal'].render("SAVAŞ & CEPHANELİK", True, (255, 120, 120))
        surface.blit(title3, (card3_rect.x + 36, card3_rect.y + 12))
        
        combat_keys = [
            ("SOL TIK", "Ateş Et veya Bıçakla Saldır (Menzilli / Yakın Dövüş)"),
            ("SAĞ TIK", "El Bombası Nişan Al & Fırlat (Büyük Alan Hasarı)"),
            ("1 - 2 - 3", "Silah Değiştir (1: Birincil Tüfek, 2: Tabanca, 3: Bıçak)"),
            ("R TUŞU", "Tabancayı Yeniden Doldur (6 Mermilik Şarjör)"),
            ("T TUŞU", "Otomatik Taret Kur (Zombileri otomatik hedef alır)"),
            ("SADIK KURT", "Haritada bulunan evcil hayvan sizi takip eder ve zombilere saldırır!")
        ]
        cur_y = card3_rect.y + 52
        for key_label, desc in combat_keys:
            bw = self._draw_key_badge(surface, card3_rect.x + 16, cur_y, key_label, badge_w=95, color=(60, 30, 45) if "TIK" in key_label else (35, 50, 75))
            cur_y = self._draw_wrapped_text(surface, desc, assets.fonts['small'], (225, 230, 240), card3_rect.x + 16 + bw + 12, cur_y + 3, col_w - bw - 40, 18) + 16

    def _draw_zombie_icon(self, surface, z_type, cx, cy, current_time=0):
        """Draw authentic animated in-game zombie icons."""
        size = 28
        if z_type == "normal":
            pygame.draw.rect(surface, (255, 60, 60), (cx - size//2, cy - size//2, size, size), border_radius=4)
            pygame.draw.rect(surface, (255, 180, 180), (cx - size//2, cy - size//2, size, size), 2, border_radius=4)
            pygame.draw.circle(surface, (255, 255, 255), (cx - 5, cy - 3), 3)
            pygame.draw.circle(surface, (255, 255, 255), (cx + 5, cy - 3), 3)
            pygame.draw.circle(surface, (20, 0, 0), (cx - 4, cy - 3), 1)
            pygame.draw.circle(surface, (20, 0, 0), (cx + 6, cy - 3), 1)
        elif z_type == "fast":
            p1 = (cx, cy - size * 0.7)
            p2 = (cx + size * 0.7, cy)
            p3 = (cx, cy + size * 0.7)
            p4 = (cx - size * 0.7, cy)
            pygame.draw.polygon(surface, PURPLE, [p1, p2, p3, p4])
            pygame.draw.polygon(surface, (230, 160, 255), [p1, p2, p3, p4], 2)
            glow = create_glow_surface(int(size * 1.6), PURPLE, 60)
            surface.blit(glow, (cx - int(size * 0.8), cy - int(size * 0.8)), special_flags=pygame.BLEND_RGBA_ADD)
        elif z_type == "durable":
            points = []
            for i in range(6):
                a = (math.pi / 3) * i
                points.append((cx + math.cos(a) * size * 0.7, cy + math.sin(a) * size * 0.7))
            pygame.draw.polygon(surface, LIGHT_BLUE, points)
            pygame.draw.polygon(surface, (220, 245, 255), points, 2)
            pygame.draw.line(surface, (40, 80, 140), (cx - 8, cy), (cx + 8, cy), 2)
        elif z_type == "boomer":
            pulse = math.sin(current_time * 0.008) * 3
            points = []
            for i in range(6):
                a = (math.pi / 3) * i
                rad = size * 0.65 + pulse
                points.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad))
            pygame.draw.polygon(surface, (140, 255, 40), points)
            pygame.draw.polygon(surface, (220, 255, 140), points, 2)
            pygame.draw.circle(surface, (30, 60, 10), (cx, cy), 5)
        elif z_type == "stealth":
            s = pygame.Surface((size, size), pygame.SRCALPHA)
            alpha = int(120 + 80 * math.sin(current_time * 0.005))
            pygame.draw.rect(s, (70, 75, 90, alpha), (0, 0, size, size), border_radius=4)
            pygame.draw.rect(s, (140, 150, 180, alpha), (0, 0, size, size), 1, border_radius=4)
            surface.blit(s, (cx - size//2, cy - size//2))
            pygame.draw.circle(surface, (255, 70, 70), (cx - 5, cy - 3), 2)
            pygame.draw.circle(surface, (255, 70, 70), (cx + 5, cy - 3), 2)
        elif z_type == "boss":
            points = []
            for i in range(6):
                a = (math.pi / 3) * i
                points.append((cx + math.cos(a) * size * 0.9, cy + math.sin(a) * size * 0.9))
            pygame.draw.polygon(surface, (220, 30, 60), points)
            pygame.draw.polygon(surface, (255, 215, 0), points, 3)
            pygame.draw.circle(surface, (255, 215, 0), (cx, cy), 7, 2)

    def _draw_tutorial_zombies(self, surface, rect, current_time):
        """Draw the Zombie Bestiary tutorial page."""
        cols = 2
        rows = 3
        spacing_x = 18
        spacing_y = 12
        card_w = (rect.width - spacing_x) // cols
        card_h = (rect.height - spacing_y * 2) // rows

        zombies_info = [
            {
                "type": "normal",
                "name": "Normal Zombi",
                "badge_color": (255, 70, 70),
                "stats": "Can: 1  |  Hız: Dengeli  |  Tehdit: Düşük / Orta",
                "desc": "Standart yürüyen ölü. İlerleyen dalgalarda hızları artar. Tek başlarına zayıftırlar ancak sürü haline geldiklerinde ölümcül olurlar."
            },
            {
                "type": "fast",
                "name": "Hızlı Zombi (Runner)",
                "badge_color": PURPLE,
                "stats": "Can: 1  |  Hız: Çok Yüksek  |  Tehdit: Yüksek",
                "desc": "Karakterden daha hızlı koşar! Oyuncuyu köşeye sıkıştırma kabiliyeti yüksektir. Görüldüğü anda öncelikli olarak vurulmalıdır."
            },
            {
                "type": "durable",
                "name": "Dayanıklı Zombi (Tank)",
                "badge_color": LIGHT_BLUE,
                "stats": "Can: 2  |  Hız: Ağır  |  Tehdit: Yüksek",
                "desc": "Çift cana sahiptir. Kurşunları emerek arkasından gelen zombilere koruma sağlar. Pompalı tüfek veya el bombasıyla hızlıca imha edin."
            },
            {
                "type": "boomer",
                "name": "Patlayan Zombi (Boomer)",
                "badge_color": (150, 255, 50),
                "stats": "Can: 2  |  Hız: Orta  |  Tehdit: Çok Yüksek",
                "desc": "Zehirli ve titreşen bir gövdesi vardır. Öldüğünde veya temas ettiğinde büyük bir patlamaya yol açar. Asla yanınızda patlatmayın!"
            },
            {
                "type": "stealth",
                "name": "Görünmez Zombi (Stealth)",
                "badge_color": (160, 175, 200),
                "stats": "Can: 1  |  Hız: Yüksek  |  Tehdit: Sinsi",
                "desc": "Karanlıkta gizlenir; yalnızca hasar aldığında veya 120px mesafeye kadar yaklaştığında görünür olur. Arkanızdan sessizce yaklaşabilir."
            },
            {
                "type": "boss",
                "name": "Bölüm Canavarı (Boss)",
                "badge_color": (255, 215, 0),
                "stats": "Can: 15+  |  Hız: Güçlü  |  Tehdit: ÖLÜMCÜL",
                "desc": "Her 5 dalgada bir ortaya çıkar. Devasa can havuzu ve yıkıcı vuruş gücü vardır. Otomatik taretler, el bombaları ve takım koordinasyonu gerektirir."
            }
        ]

        for idx, z_data in enumerate(zombies_info):
            col = idx % cols
            row = idx // cols
            cx = rect.x + col * (card_w + spacing_x)
            cy = rect.y + row * (card_h + spacing_y)

            HUD(self.width, self.height).draw_glass_panel(surface, (cx, cy, card_w, card_h))

            # Icon box
            icon_box_w = 64
            icon_cx = cx + icon_box_w // 2 + 10
            icon_cy = cy + card_h // 2
            
            # Subtle glow bg for icon
            icon_bg = pygame.Surface((icon_box_w, card_h - 16), pygame.SRCALPHA)
            pygame.draw.rect(icon_bg, (15, 20, 32, 160), (0, 0, icon_box_w, card_h - 16), border_radius=6)
            pygame.draw.rect(icon_bg, (50, 65, 90, 120), (0, 0, icon_box_w, card_h - 16), 1, border_radius=6)
            surface.blit(icon_bg, (cx + 10, cy + 8))

            self._draw_zombie_icon(surface, z_data["type"], icon_cx, icon_cy, current_time)

            # Text area
            text_x = cx + icon_box_w + 24
            max_t_w = card_w - (icon_box_w + 34)

            # Title
            title_surf = assets.fonts['normal'].render(z_data["name"], True, z_data["badge_color"])
            surface.blit(title_surf, (text_x, cy + 10))

            # Stats
            stats_surf = assets.fonts['small'].render(z_data["stats"], True, (255, 235, 150))
            surface.blit(stats_surf, (text_x, cy + 38))

            # Desc
            self._draw_wrapped_text(surface, z_data["desc"], assets.fonts['small'], (210, 220, 235), text_x, cy + 62, max_t_w, 16)

    def _draw_tutorial_weapons(self, surface, rect, current_time):
        """Draw the Weapons & Equipment tutorial page."""
        cols = 2
        rows = 3
        spacing_x = 18
        spacing_y = 12
        card_w = (rect.width - spacing_x) // cols
        card_h = (rect.height - spacing_y * 2) // rows

        items_info = [
            {
                "icon_type": "weapon",
                "model_key": "pistol",
                "name": "Tabanca (Pistol) [Tuş: 2]",
                "accent": (255, 215, 0),
                "stats": "Hasar: 1  |  Şarjör: 6  |  Yedek: Sınırsız",
                "desc": "Temel başlangıç silahınız. Cephanesi asla bitmez; boşaldığında [R] tuşu ile anında şarjör doldurabilirsiniz."
            },
            {
                "icon_type": "weapon",
                "model_key": "ak47",
                "name": "AK-47 Saldırı Tüfeği [Tuş: 1]",
                "accent": (100, 220, 255),
                "stats": "Hasar: 2  |  Şarjör: 30  |  Seri Atış",
                "desc": "Yüksek atış hızı ve mermi gücüne sahip tam otomatik tüfek. Kırılan kutulardan ve varillerden elde edilir."
            },
            {
                "icon_type": "weapon",
                "model_key": "shotgun",
                "name": "Pompalı Tüfek (Shotgun) [Tuş: 1]",
                "accent": (255, 140, 50),
                "stats": "Hasar: 3x5  |  Şarjör: 10  |  Yayılım",
                "desc": "Tek atışta 5 ölümcül saçma fırlatır. Yakın mesafeden zombi sürülerini ve tankları tek vuruşta parçalamak için birebirdir."
            },
            {
                "icon_type": "weapon",
                "model_key": "flamethrower",
                "name": "Alev Silahı (Flamethrower)",
                "accent": (255, 80, 40),
                "stats": "Hasar: 1 (Sürekli)  |  Yakıt: 100  |  Delici Alev",
                "desc": "Tüm hedefleri delip geçen kesintisiz bir alev sütunu püskürtür. Kalabalık zombi ordularını saniyeler içinde kül eder."
            },
            {
                "icon_type": "special",
                "spec_type": "grenade_knife",
                "name": "Av Bıçağı [3] & El Bombası [Sağ Tık]",
                "accent": (180, 255, 120),
                "stats": "Bıçak: Sonsuz  |  Bomba: 150px Alan Hasarı",
                "desc": "Bıçak cephane harcamadan yakın düşmanları savurur. El bombası ise fırlatıldığı noktadaki tüm zombileri havaya uçurur."
            },
            {
                "icon_type": "special",
                "spec_type": "sentry_pet",
                "name": "Otomatik Taret [T] & Sadık Kurt (Pet)",
                "accent": (220, 160, 255),
                "stats": "Taret: 360 Derece Tarama  |  Kurt: Saldırı & Yoldaş",
                "desc": "[T] ile yere kurulan taret yaklaşan zombileri otomatik vurur. Sadık kurt ise düşmanların dikkatini dağıtıp sizi korur."
            }
        ]

        for idx, item_data in enumerate(items_info):
            col = idx % cols
            row = idx // cols
            cx = rect.x + col * (card_w + spacing_x)
            cy = rect.y + row * (card_h + spacing_y)

            HUD(self.width, self.height).draw_glass_panel(surface, (cx, cy, card_w, card_h))

            icon_box_w = 64
            icon_cx = cx + icon_box_w // 2 + 10
            icon_cy = cy + card_h // 2

            icon_bg = pygame.Surface((icon_box_w, card_h - 16), pygame.SRCALPHA)
            pygame.draw.rect(icon_bg, (15, 20, 32, 160), (0, 0, icon_box_w, card_h - 16), border_radius=6)
            pygame.draw.rect(icon_bg, (50, 65, 90, 120), (0, 0, icon_box_w, card_h - 16), 1, border_radius=6)
            surface.blit(icon_bg, (cx + 10, cy + 8))

            if item_data["icon_type"] == "weapon":
                wp_key = item_data["model_key"]
                if wp_key in assets.weapon_models:
                    wp_surf = assets.weapon_models[wp_key]
                    scaled = pygame.transform.scale(wp_surf, (50, 50))
                    surface.blit(scaled, (icon_cx - 25, icon_cy - 25))
            elif item_data["icon_type"] == "special":
                if item_data["spec_type"] == "grenade_knife":
                    pygame.draw.circle(surface, (30, 140, 40), (icon_cx - 10, icon_cy), 10)
                    pygame.draw.rect(surface, (60, 60, 60), (icon_cx - 13, icon_cy - 14, 6, 6))
                    pygame.draw.line(surface, (240, 240, 255), (icon_cx + 4, icon_cy - 12), (icon_cx + 18, icon_cy + 10), 3)
                elif item_data["spec_type"] == "sentry_pet":
                    pygame.draw.circle(surface, (80, 140, 220), (icon_cx - 8, icon_cy), 10)
                    pygame.draw.line(surface, (180, 220, 255), (icon_cx - 8, icon_cy), (icon_cx - 8, icon_cy - 14), 3)
                    pygame.draw.circle(surface, (255, 180, 50), (icon_cx + 12, icon_cy + 2), 7)
                    pygame.draw.circle(surface, (255, 200, 80), (icon_cx + 9, icon_cy - 6), 3)
                    pygame.draw.circle(surface, (255, 200, 80), (icon_cx + 15, icon_cy - 6), 3)

            text_x = cx + icon_box_w + 24
            max_t_w = card_w - (icon_box_w + 34)

            title_surf = assets.fonts['normal'].render(item_data["name"], True, item_data["accent"])
            surface.blit(title_surf, (text_x, cy + 10))

            stats_surf = assets.fonts['small'].render(item_data["stats"], True, (255, 235, 150))
            surface.blit(stats_surf, (text_x, cy + 38))

            self._draw_wrapped_text(surface, item_data["desc"], assets.fonts['small'], (210, 220, 235), text_x, cy + 62, max_t_w, 16)

    # ================================================================
    # MULTIPLAYER UI
    # ================================================================

    def show_multiplayer_menu(self, surface, network):
        """Show the multiplayer menu: room browser, create room, join room."""
        clock = pygame.time.Clock()
        state = "browser"  # browser, create, join, lobby
        selected = 0
        rooms_list = []
        selected_room = None  # Track which room user is joining
        error_msg = ""
        error_timer = 0

        # Text input fields
        input_fields = {
            "player_name": "",
            "room_name": "",
            "password": ""
        }
        active_field = "player_name"

        # Lobby state
        lobby_players = []
        game_started = False
        game_start_data = None

        # Connect to server
        if not network.connected:
            connected = network.connect()
            if not connected:
                error_msg = "Sunucuya bağlanılamadı!"
                error_timer = pygame.time.get_ticks()

        # Request room list
        if network.connected:
            network.list_rooms()

        while True:
            current_time = pygame.time.get_ticks()

            # Process network messages
            for msg in network.get_messages():
                msg_type = msg.get("type")
                if msg_type == "room_list":
                    rooms_list = msg.get("rooms", [])
                elif msg_type == "room_created":
                    state = "lobby"
                    lobby_players = []
                    selected = 0
                elif msg_type == "room_joined":
                    state = "lobby"
                    lobby_players = []
                    selected = 0
                elif msg_type == "room_update":
                    lobby_players = msg.get("players", [])
                elif msg_type == "player_joined":
                    pass  # room_update handles this
                elif msg_type == "player_left":
                    pass  # room_update handles this
                elif msg_type == "host_changed":
                    network.is_host = (msg.get("new_host_id") == network.player_id)
                elif msg_type == "game_started":
                    game_started = True
                    game_start_data = msg
                    return ("start_game", game_start_data)
                elif msg_type == "error":
                    error_msg = msg.get("message", "Hata!")
                    error_timer = current_time

            if game_started and game_start_data:
                return ("start_game", game_start_data)

            # Draw
            self._draw_background(surface)

            if state == "browser":
                self._draw_room_browser(surface, rooms_list, selected, error_msg if current_time - error_timer < 3000 else "")
            elif state == "create":
                self._draw_create_room(surface, input_fields, active_field, error_msg if current_time - error_timer < 3000 else "")
            elif state == "join":
                room_name = selected_room.get("room_name", "?") if selected_room else "?"
                self._draw_join_room_dialog(surface, input_fields, active_field, room_name, error_msg if current_time - error_timer < 3000 else "")
            elif state == "lobby":
                self._draw_lobby(surface, lobby_players, network.is_host, network.room_id)

            pygame.display.flip()

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    network.disconnect()
                    return ("quit", None)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if state == "create" or state == "join":
                            state = "browser"
                            selected = 0
                            selected_room = None
                        elif state == "lobby":
                            network.leave_room()
                            state = "browser"
                            selected = 0
                            network.list_rooms()
                        else:
                            network.disconnect()
                            return ("back", None)

                    if state == "browser":
                        if event.key == pygame.K_UP:
                            selected = max(0, selected - 1)
                        elif event.key == pygame.K_DOWN:
                            selected = min(len(rooms_list), selected + 1)  # +1 for "Create Room"
                        elif event.key == pygame.K_r:
                            network.list_rooms()
                        elif event.key == pygame.K_RETURN:
                            if selected == 0:
                                # Create room
                                state = "create"
                                active_field = "player_name"
                                input_fields["player_name"] = ""
                                input_fields["room_name"] = ""
                                input_fields["password"] = ""
                                selected = 0
                            elif selected > 0 and selected <= len(rooms_list):
                                # Join room - show join dialog
                                room = rooms_list[selected - 1]
                                if room.get("game_started"):
                                    error_msg = "Oyun zaten başlamış!"
                                    error_timer = current_time
                                elif room.get("player_count", 0) >= room.get("max_players", 4):
                                    error_msg = "Oda dolu!"
                                    error_timer = current_time
                                else:
                                    selected_room = room
                                    state = "join"
                                    input_fields["player_name"] = ""
                                    input_fields["password"] = ""
                                    active_field = "player_name"

                    elif state == "create":
                        if event.key == pygame.K_TAB:
                            fields = ["player_name", "room_name", "password"]
                            idx = fields.index(active_field)
                            active_field = fields[(idx + 1) % len(fields)]
                        elif event.key == pygame.K_RETURN:
                            pname = input_fields["player_name"].strip()
                            rname = input_fields["room_name"].strip()
                            pw = input_fields["password"].strip() or None

                            if not pname:
                                error_msg = "Oyuncu adı boş olamaz!"
                                error_timer = current_time
                            elif not rname:
                                error_msg = "Oda adı boş olamaz!"
                                error_timer = current_time
                            else:
                                network.create_room(rname, pname, pw)
                        elif event.key == pygame.K_BACKSPACE:
                            input_fields[active_field] = input_fields[active_field][:-1]
                        else:
                            if event.unicode and event.unicode.isprintable() and len(input_fields[active_field]) < 20:
                                input_fields[active_field] += event.unicode

                    elif state == "join":
                        if event.key == pygame.K_TAB:
                            fields = ["player_name", "password"]
                            idx = fields.index(active_field)
                            active_field = fields[(idx + 1) % len(fields)]
                        elif event.key == pygame.K_RETURN:
                            pname = input_fields["player_name"].strip()
                            pw = input_fields["password"].strip() or None

                            if not pname:
                                error_msg = "Oyuncu adı boş olamaz!"
                                error_timer = current_time
                            elif selected_room:
                                network.join_room(selected_room["room_id"], pname, pw)
                        elif event.key == pygame.K_BACKSPACE:
                            input_fields[active_field] = input_fields[active_field][:-1]
                        else:
                            if event.unicode and event.unicode.isprintable() and len(input_fields[active_field]) < 20:
                                input_fields[active_field] += event.unicode

                    elif state == "lobby":
                        if event.key == pygame.K_RETURN:
                            if network.is_host:
                                import random
                                seed = random.randint(0, 999999)
                                network.start_game(seed)
                                game_start_data = {
                                    "map_seed": seed,
                                    "players": lobby_players
                                }
                                return ("start_game", game_start_data)

            clock.tick(60)

    def _draw_room_browser(self, surface, rooms_list, selected, error_msg=""):
        """Draw the room browser screen."""
        self._draw_title(surface, "ÇOK OYUNCULU", y_offset=-280)

        # Instructions
        info = assets.fonts['small'].render("YÖN TUŞLARI: Seç  |  ENTER: Katıl  |  R: Yenile  |  ESC: Geri", True, (150, 150, 150))
        surface.blit(info, (self.width//2 - info.get_width()//2, self.height//2 - 220))

        # Panel
        panel_w = 600
        panel_h = 500
        panel_x = self.width//2 - panel_w//2
        panel_y = self.height//2 - 180
        HUD(self.width, self.height).draw_glass_panel(surface, (panel_x, panel_y, panel_w, panel_h))

        # "Create Room" option at top
        y = panel_y + 20
        create_color = (50, 255, 100) if selected == 0 else WHITE
        if selected == 0:
            pygame.draw.rect(surface, (255, 255, 255, 20), (panel_x + 10, y - 5, panel_w - 20, 40), border_radius=5)
        create_txt = assets.fonts['normal'].render("+ Yeni Oda Oluştur", True, create_color)
        surface.blit(create_txt, (panel_x + 20, y))

        # Separator
        y += 50
        pygame.draw.line(surface, (100, 100, 100), (panel_x + 20, y), (panel_x + panel_w - 20, y))
        y += 10

        # Column headers
        header_font = assets.fonts['small']
        surface.blit(header_font.render("Oda Adı", True, (150, 150, 150)), (panel_x + 20, y))
        surface.blit(header_font.render("Host", True, (150, 150, 150)), (panel_x + 250, y))
        surface.blit(header_font.render("Oyuncu", True, (150, 150, 150)), (panel_x + 400, y))
        surface.blit(header_font.render("Durum", True, (150, 150, 150)), (panel_x + 490, y))
        y += 30

        if not rooms_list:
            no_rooms = assets.fonts['normal'].render("Henüz oda yok.", True, (100, 100, 100))
            surface.blit(no_rooms, (self.width//2 - no_rooms.get_width()//2, y + 20))
        else:
            for i, room in enumerate(rooms_list):
                idx = i + 1  # 0 is "Create Room"
                row_y = y + i * 50
                if row_y > panel_y + panel_h - 40:
                    break

                row_color = (50, 255, 100) if idx == selected else WHITE
                if idx == selected:
                    pygame.draw.rect(surface, (255, 255, 255, 20),
                        (panel_x + 10, row_y - 5, panel_w - 20, 40), border_radius=5)

                # Room name (with lock tag if password)
                name_str = room["room_name"]
                if room.get("has_password"):
                    name_str = "[ŞİFRELİ] " + name_str
                surface.blit(assets.fonts['normal'].render(name_str, True, row_color), (panel_x + 20, row_y))

                # Host name
                surface.blit(assets.fonts['small'].render(room.get("host_name", "?"), True, row_color), (panel_x + 250, row_y + 4))

                # Player count
                count_str = f"{room['player_count']}/{room['max_players']}"
                surface.blit(assets.fonts['normal'].render(count_str, True, row_color), (panel_x + 400, row_y))

                # Status
                if room.get("game_started"):
                    status_str = "Oyunda"
                    status_color = (255, 100, 100)
                else:
                    status_str = "Bekliyor"
                    status_color = (100, 255, 100)
                surface.blit(assets.fonts['small'].render(status_str, True, status_color), (panel_x + 490, row_y + 4))

        # Error message
        if error_msg:
            err_surf = assets.fonts['normal'].render(error_msg, True, (255, 80, 80))
            surface.blit(err_surf, (self.width//2 - err_surf.get_width()//2, panel_y + panel_h + 10))

    def _draw_create_room(self, surface, fields, active_field, error_msg=""):
        """Draw the create room dialog."""
        self._draw_title(surface, "ODA OLUŞTUR", y_offset=-280)

        panel_w = 450
        panel_h = 350
        panel_x = self.width//2 - panel_w//2
        panel_y = self.height//2 - 150
        HUD(self.width, self.height).draw_glass_panel(surface, (panel_x, panel_y, panel_w, panel_h))

        field_configs = [
            ("Oyuncu Adı:", "player_name"),
            ("Oda Adı:", "room_name"),
            ("Şifre (opsiyonel):", "password"),
        ]

        y = panel_y + 30
        for label, field_key in field_configs:
            # Label
            lbl = assets.fonts['normal'].render(label, True, WHITE)
            surface.blit(lbl, (panel_x + 30, y))
            y += 35

            # Input box
            is_active = active_field == field_key
            box_color = (50, 255, 100) if is_active else (100, 100, 100)
            pygame.draw.rect(surface, (20, 20, 35), (panel_x + 30, y, panel_w - 60, 35), border_radius=5)
            pygame.draw.rect(surface, box_color, (panel_x + 30, y, panel_w - 60, 35), 2, border_radius=5)

            # Text content
            display_text = fields[field_key]
            if field_key == "password" and display_text:
                display_text = "*" * len(display_text)
            if is_active:
                # Blinking cursor
                cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
                display_text += cursor

            txt_surf = assets.fonts['normal'].render(display_text, True, WHITE)
            surface.blit(txt_surf, (panel_x + 40, y + 5))
            y += 55

        # Hint
        hint = assets.fonts['small'].render("TAB: Sonraki Alan  |  ENTER: Oluştur  |  ESC: Geri", True, (150, 150, 150))
        surface.blit(hint, (self.width//2 - hint.get_width()//2, y + 10))

        # Error
        if error_msg:
            err_surf = assets.fonts['normal'].render(error_msg, True, (255, 80, 80))
            surface.blit(err_surf, (self.width//2 - err_surf.get_width()//2, y + 40))

    def _draw_join_room_dialog(self, surface, fields, active_field, room_name, error_msg=""):
        """Draw the join room dialog."""
        self._draw_title(surface, f"ODAYA KATIL: {room_name}", y_offset=-250)

        panel_w = 450
        panel_h = 250
        panel_x = self.width//2 - panel_w//2
        panel_y = self.height//2 - 100
        HUD(self.width, self.height).draw_glass_panel(surface, (panel_x, panel_y, panel_w, panel_h))

        field_configs = [
            ("Oyuncu Adı:", "player_name"),
            ("Şifre:", "password"),
        ]

        y = panel_y + 30
        for label, field_key in field_configs:
            lbl = assets.fonts['normal'].render(label, True, WHITE)
            surface.blit(lbl, (panel_x + 30, y))
            y += 35

            is_active = active_field == field_key
            box_color = (50, 255, 100) if is_active else (100, 100, 100)
            pygame.draw.rect(surface, (20, 20, 35), (panel_x + 30, y, panel_w - 60, 35), border_radius=5)
            pygame.draw.rect(surface, box_color, (panel_x + 30, y, panel_w - 60, 35), 2, border_radius=5)

            display_text = fields[field_key]
            if field_key == "password" and display_text:
                display_text = "*" * len(display_text)
            if is_active:
                cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
                display_text += cursor

            txt_surf = assets.fonts['normal'].render(display_text, True, WHITE)
            surface.blit(txt_surf, (panel_x + 40, y + 5))
            y += 55

        hint = assets.fonts['small'].render("ENTER: Katıl  |  ESC: Geri", True, (150, 150, 150))
        surface.blit(hint, (self.width//2 - hint.get_width()//2, y + 10))

        if error_msg:
            err_surf = assets.fonts['normal'].render(error_msg, True, (255, 80, 80))
            surface.blit(err_surf, (self.width//2 - err_surf.get_width()//2, y + 40))

    def _draw_lobby(self, surface, players, is_host, room_id):
        """Draw the lobby waiting screen."""
        self._draw_title(surface, "LOBİ", y_offset=-280)

        # Room info
        if room_id:
            room_info = assets.fonts['small'].render(f"Oda ID: {room_id}", True, (150, 150, 150))
            surface.blit(room_info, (self.width//2 - room_info.get_width()//2, self.height//2 - 220))

        panel_w = 450
        panel_h = 350
        panel_x = self.width//2 - panel_w//2
        panel_y = self.height//2 - 180
        HUD(self.width, self.height).draw_glass_panel(surface, (panel_x, panel_y, panel_w, panel_h))

        # "Oyuncular" header
        header = assets.fonts['normal'].render("Oyuncular", True, (150, 150, 150))
        surface.blit(header, (panel_x + 20, panel_y + 15))
        pygame.draw.line(surface, (100, 100, 100), (panel_x + 20, panel_y + 45), (panel_x + panel_w - 20, panel_y + 45))

        # Player list
        y = panel_y + 60
        player_colors = [(0, 200, 255), (255, 100, 200), (100, 255, 100), (255, 200, 50)]
        for i, p in enumerate(players):
            color = player_colors[i % len(player_colors)]
            name = p.get("player_name", "?")
            role = " (Host)" if p.get("is_host") else ""

            # Color indicator
            pygame.draw.circle(surface, color, (panel_x + 35, y + 12), 8)

            # Name
            name_surf = assets.fonts['normal'].render(f"{name}{role}", True, WHITE)
            surface.blit(name_surf, (panel_x + 55, y))
            y += 45

        # Waiting dots animation
        dots = "." * ((pygame.time.get_ticks() // 500) % 4)
        wait_txt = assets.fonts['normal'].render(f"Bekleniyor{dots}", True, (100, 100, 100))
        surface.blit(wait_txt, (self.width//2 - wait_txt.get_width()//2, panel_y + panel_h - 50))

        # Bottom instructions
        if is_host:
            hint = assets.fonts['normal'].render("ENTER: Oyunu Başlat  |  ESC: Ayrıl", True, (50, 255, 100))
        else:
            hint = assets.fonts['normal'].render("Host oyunu başlatmasını bekleyin...  |  ESC: Ayrıl", True, (150, 150, 150))
        surface.blit(hint, (self.width//2 - hint.get_width()//2, panel_y + panel_h + 20))
