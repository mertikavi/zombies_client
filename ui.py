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
        is_exhausted = getattr(player, "stamina_exhausted", False)
        s_txt = assets.fonts['normal'].render("ENERJİ", True, (255, 120, 50) if is_exhausted else WHITE)
        surface.blit(s_txt, (20, 65))
        
        s_fill_w = max(0, int((self.display_stamina / MAX_PLAYER_STAMINA) * bar_w))
        pygame.draw.rect(surface, (0,0,0,150), (120, 70, bar_w, 20), border_radius=5)
        pygame.draw.rect(surface, (0, 0, 50), (120, 70, bar_w, 20), border_radius=5) # bg
        if s_fill_w > 0:
            bar_color = (255, 120, 50) if is_exhausted else (50, 150, 255)
            pygame.draw.rect(surface, bar_color, (120, 70, s_fill_w, 20), border_radius=5)

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
        """Draw the common grid background for menus (cached)."""
        if not hasattr(self, "_cached_bg") or self._cached_bg.get_size() != (self.width, self.height):
            self._cached_bg = pygame.Surface((self.width, self.height))
            self._cached_bg.fill((18, 18, 28))
            grid_color = (30, 30, 45)
            for x in range(0, self.width, 40):
                pygame.draw.line(self._cached_bg, grid_color, (x, 0), (x, self.height))
            for y in range(0, self.height, 40):
                pygame.draw.line(self._cached_bg, grid_color, (0, y), (self.width, y))
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            self._cached_bg.blit(overlay, (0, 0))
        
        surface.blit(self._cached_bg, (0, 0))

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

    def prompt_player_name(self, surface, title="OYUNCU ADI BELİRLE"):
        """Modal text input dialog for player name."""
        cur_name = game_settings.get("player_name", "")
        input_text = cur_name
        clock = pygame.time.Clock()

        panel_w = 420
        panel_h = 190
        panel_x = self.width // 2 - panel_w // 2
        panel_y = self.height // 2 - panel_h // 2

        while True:
            self._draw_background(surface)
            self._draw_title(surface, title, y_offset=-160)

            HUD(self.width, self.height).draw_glass_panel(surface, (panel_x, panel_y, panel_w, panel_h))

            # Prompt label
            lbl = assets.fonts['normal'].render("İsminizi girin:", True, (210, 220, 240))
            surface.blit(lbl, (panel_x + 30, panel_y + 22))

            # Input Box
            input_rect = pygame.Rect(panel_x + 30, panel_y + 60, panel_w - 60, 42)
            pygame.draw.rect(surface, (20, 25, 40), input_rect, border_radius=6)
            pygame.draw.rect(surface, (80, 210, 255), input_rect, 2, border_radius=6)

            # Cursor blink
            cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
            disp_txt = input_text + cursor
            txt_surf = assets.fonts['normal'].render(disp_txt, True, WHITE)
            surface.blit(txt_surf, (input_rect.x + 12, input_rect.centery - txt_surf.get_height() // 2))

            # Buttons: Kaydet (ENTER), İptal (ESC)
            btn_save = pygame.Rect(panel_x + 30, panel_y + 122, 170, 42)
            btn_cancel = pygame.Rect(panel_x + panel_w - 200, panel_y + 122, 170, 42)

            pygame.draw.rect(surface, (30, 110, 60), btn_save, border_radius=6)
            pygame.draw.rect(surface, (60, 210, 100), btn_save, 1, border_radius=6)
            s_txt = assets.fonts['small'].render("Kaydet (ENTER)", True, WHITE)
            surface.blit(s_txt, (btn_save.centerx - s_txt.get_width() // 2, btn_save.centery - s_txt.get_height() // 2))

            pygame.draw.rect(surface, (70, 35, 40), btn_cancel, border_radius=6)
            pygame.draw.rect(surface, (180, 60, 70), btn_cancel, 1, border_radius=6)
            c_txt = assets.fonts['small'].render("İptal (ESC)", True, WHITE)
            surface.blit(c_txt, (btn_cancel.centerx - c_txt.get_width() // 2, btn_cancel.centery - c_txt.get_height() // 2))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    m_x, m_y = event.pos
                    if btn_save.collidepoint(m_x, m_y):
                        val = input_text.strip()
                        if val:
                            game_settings["player_name"] = val
                            save_settings()
                            return val
                    elif btn_cancel.collidepoint(m_x, m_y):
                        return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        val = input_text.strip()
                        if val:
                            game_settings["player_name"] = val
                            save_settings()
                            return val
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        if event.unicode and event.unicode.isprintable() and len(input_text) < 18:
                            input_text += event.unicode

            clock.tick(60)

    def _get_settings_layout(self):
        panel_w = 680
        panel_h = 365
        panel_x = self.width // 2 - panel_w // 2
        panel_y = self.height // 2 - 180

        col1_x = panel_x + 25
        col2_x = panel_x + 355
        btn_w = 300
        btn_h = 42
        step_y = 48

        rects = [
            # Col 1: Oyun & Görüntü
            pygame.Rect(col1_x, panel_y + 50 + 0 * step_y, btn_w, btn_h),   # 0: Zorluk
            pygame.Rect(col1_x, panel_y + 50 + 1 * step_y, btn_w, btn_h),   # 1: Karakter Rengi
            pygame.Rect(col1_x, panel_y + 50 + 2 * step_y, btn_w, btn_h),   # 2: Mermi Rengi
            pygame.Rect(col1_x, panel_y + 50 + 3 * step_y, btn_w, btn_h),   # 3: FOV
            pygame.Rect(col1_x, panel_y + 50 + 4 * step_y, btn_w, btn_h),   # 4: Grafik Kalitesi
            # Col 2: Sistem & Profil
            pygame.Rect(col2_x, panel_y + 50 + 0 * step_y, btn_w, btn_h),   # 5: Oyuncu Adı
            pygame.Rect(col2_x, panel_y + 50 + 1 * step_y, btn_w, btn_h),   # 6: Müzik
            pygame.Rect(col2_x, panel_y + 50 + 2 * step_y, btn_w, btn_h),   # 7: Ses Efektleri
            pygame.Rect(col2_x, panel_y + 50 + 3 * step_y, btn_w, btn_h),   # 8: FPS Göstergesi
            pygame.Rect(col2_x, panel_y + 50 + 4 * step_y, btn_w, btn_h),   # 9: Ekran Modu
            # Bottom: Geri
            pygame.Rect(panel_x + panel_w // 2 - 120, panel_y + 302, 240, 44) # 10: Geri
        ]
        return panel_x, panel_y, panel_w, panel_h, rects

    def _draw_settings_menu(self, surface, selected):
        panel_x, panel_y, panel_w, panel_h, rects = self._get_settings_layout()
        HUD(self.width, self.height).draw_glass_panel(surface, (panel_x, panel_y, panel_w, panel_h))

        char_c_name = next((k for k, v in CHARACTER_COLORS.items() if v == game_settings['character_color']), "Sarı")
        bull_c_name = next((k for k, v in BULLET_COLORS.items() if v == game_settings['bullet_color']), "Sarı")

        # Headers
        h1 = assets.fonts['small'].render("OYUN AYARLARI", True, (160, 200, 255))
        surface.blit(h1, (panel_x + 25, panel_y + 18))
        pygame.draw.line(surface, (70, 90, 120), (panel_x + 25, panel_y + 40), (panel_x + 325, panel_y + 40))

        h2 = assets.fonts['small'].render("SİSTEM & PROFİL", True, (160, 200, 255))
        surface.blit(h2, (panel_x + 355, panel_y + 18))
        pygame.draw.line(surface, (70, 90, 120), (panel_x + 355, panel_y + 40), (panel_x + 655, panel_y + 40))

        diff_col = (100, 255, 100) if game_settings["difficulty"] == "Kolay" else (255, 215, 0) if game_settings["difficulty"] == "Normal" else (255, 80, 80)
        g_qual = game_settings.get("graphics_quality", "Orta")
        g_qual_col = (80, 240, 120) if g_qual == "Yüksek" else (255, 215, 0) if g_qual == "Orta" else (100, 210, 255)

        p_name = game_settings.get("player_name", "").strip() or "Belirtilmedi"
        p_name_col = (100, 220, 255) if game_settings.get("player_name", "").strip() else (140, 140, 150)

        items = [
            ("Zorluk", game_settings["difficulty"], diff_col, None),
            ("Karakter Rengi", char_c_name, WHITE, game_settings["character_color"]),
            ("Mermi Rengi", bull_c_name, WHITE, game_settings["bullet_color"]),
            ("Görüş Alanı (FOV)", "Açık" if game_settings["fov"] else "Kapalı", (80, 240, 120) if game_settings["fov"] else (160, 80, 80), None),
            ("Grafik Kalitesi", g_qual, g_qual_col, None),
            ("Oyuncu Adı", p_name, p_name_col, None),
            ("Müzik", "Açık" if game_settings["music"] else "Kapalı", (80, 240, 120) if game_settings["music"] else (160, 80, 80), None),
            ("Ses Efektleri", "Açık" if game_settings["sound"] else "Kapalı", (80, 240, 120) if game_settings["sound"] else (160, 80, 80), None),
            ("FPS Göstergesi", "Açık" if game_settings.get("show_fps", True) else "Kapalı", (80, 240, 120) if game_settings.get("show_fps", True) else (160, 80, 80), None),
            ("Ekran Modu", game_settings.get("display_mode", "Tam Ekran"), (100, 210, 255), None),
        ]

        for i in range(10):
            r = rects[i]
            is_sel = (selected == i)
            lbl, val_str, val_col, dot_col = items[i]

            bg_col = (35, 65, 105) if is_sel else (18, 24, 38)
            border_col = (80, 210, 255) if is_sel else (50, 65, 90)
            pygame.draw.rect(surface, bg_col, r, border_radius=6)
            pygame.draw.rect(surface, border_col, r, 2 if is_sel else 1, border_radius=6)

            lbl_surf = assets.fonts['small'].render(lbl, True, (210, 220, 235))
            surface.blit(lbl_surf, (r.x + 12, r.centery - lbl_surf.get_height() // 2))

            val_surf = assets.fonts['small'].render(val_str, True, val_col)
            val_x = r.right - val_surf.get_width() - 14
            if dot_col:
                val_x -= 18
                pygame.draw.circle(surface, dot_col, (r.right - 18, r.centery), 6)
                pygame.draw.circle(surface, WHITE, (r.right - 18, r.centery), 7, 1)

            surface.blit(val_surf, (val_x, r.centery - val_surf.get_height() // 2))

        # Back button (index 10)
        r_back = rects[10]
        is_sel_back = (selected == 10)
        bg_b = (70, 35, 40) if is_sel_back else (35, 20, 25)
        border_b = (240, 80, 80) if is_sel_back else (120, 50, 60)
        pygame.draw.rect(surface, bg_b, r_back, border_radius=6)
        pygame.draw.rect(surface, border_b, r_back, 2 if is_sel_back else 1, border_radius=6)
        back_txt = assets.fonts['normal'].render("Geri (ESC)", True, WHITE)
        surface.blit(back_txt, (r_back.centerx - back_txt.get_width() // 2, r_back.centery - back_txt.get_height() // 2))

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

            title_str = "AYARLAR" if menu_state == "settings" else ("Oyun Duraklatıldı" if is_paused else "ZOMBİ KAÇIŞI")
            y_off = -240 if menu_state == "settings" else -200
            self._draw_title(surface, title_str, y_offset=y_off)

            if menu_state == "main":
                self._draw_menu_options(surface, options, selected)
            elif menu_state == "settings":
                self._draw_settings_menu(surface, selected)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                
                trigger_action = False
                if event.type == pygame.MOUSEMOTION:
                    m_x, m_y = event.pos
                    if menu_state == "main":
                        cur_pw = 300
                        y_start = -80
                        for i in range(len(options)):
                            btn_rect = pygame.Rect(self.width//2 - cur_pw//2 + 10, self.height//2 + y_start + 20 + i * 70, cur_pw - 20, 50)
                            if btn_rect.collidepoint(m_x, m_y):
                                selected = i
                                break
                    else:
                        _, _, _, _, s_rects = self._get_settings_layout()
                        for i, r in enumerate(s_rects):
                            if r.collidepoint(m_x, m_y):
                                selected = i
                                break
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    m_x, m_y = event.pos
                    if menu_state == "main":
                        cur_pw = 300
                        y_start = -80
                        for i in range(len(options)):
                            btn_rect = pygame.Rect(self.width//2 - cur_pw//2 + 10, self.height//2 + y_start + 20 + i * 70, cur_pw - 20, 50)
                            if btn_rect.collidepoint(m_x, m_y):
                                selected = i
                                trigger_action = True
                                break
                    else:
                        _, _, _, _, s_rects = self._get_settings_layout()
                        for i, r in enumerate(s_rects):
                            if r.collidepoint(m_x, m_y):
                                selected = i
                                trigger_action = True
                                break
                elif event.type == pygame.KEYDOWN:
                    if menu_state == "main":
                        opts_len = len(options)
                        if event.key == pygame.K_UP:
                            selected = (selected - 1) % opts_len
                        elif event.key == pygame.K_DOWN:
                            selected = (selected + 1) % opts_len
                    else:
                        if event.key == pygame.K_UP:
                            if selected == 10:
                                selected = 4
                            elif selected in (0, 1, 2, 3, 4):
                                selected = (selected - 1) % 5
                            elif selected in (5, 6, 7, 8, 9):
                                selected = 5 + (selected - 5 - 1) % 5
                        elif event.key == pygame.K_DOWN:
                            if selected in (0, 1, 2, 3):
                                selected += 1
                            elif selected == 4:
                                selected = 10
                            elif selected in (5, 6, 7, 8):
                                selected += 1
                            elif selected == 9:
                                selected = 10
                            elif selected == 10:
                                selected = 0
                        elif event.key == pygame.K_LEFT:
                            if selected in (5, 6, 7, 8, 9):
                                selected -= 5
                        elif event.key == pygame.K_RIGHT:
                            if selected in (0, 1, 2, 3, 4):
                                selected += 5

                    if event.key == pygame.K_ESCAPE:
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
                            save_settings()
                        elif selected == 1:
                            colors = list(CHARACTER_COLORS.items())
                            idx = next(i for i, (k, v) in enumerate(colors) if v == game_settings["character_color"])
                            game_settings["character_color"] = colors[(idx + 1) % len(colors)][1]
                            assets.recolor_weapons(game_settings["character_color"])
                            save_settings()
                        elif selected == 2:
                            colors = list(BULLET_COLORS.items())
                            idx = next(i for i, (k, v) in enumerate(colors) if v == game_settings["bullet_color"])
                            game_settings["bullet_color"] = colors[(idx + 1) % len(colors)][1]
                            save_settings()
                        elif selected == 3:
                            game_settings["fov"] = not game_settings["fov"]
                            save_settings()
                        elif selected == 4:
                            qualities = ["Düşük", "Orta", "Yüksek"]
                            cur_q = game_settings.get("graphics_quality", "Orta")
                            idx = qualities.index(cur_q) if cur_q in qualities else 1
                            game_settings["graphics_quality"] = qualities[(idx + 1) % len(qualities)]
                            save_settings()
                        elif selected == 5:
                            # Set Player Name
                            self.prompt_player_name(surface)
                        elif selected == 6:
                            game_settings["music"] = not game_settings["music"]
                            assets.update_volumes()
                            save_settings()
                        elif selected == 7:
                            game_settings["sound"] = not game_settings["sound"]
                            assets.update_volumes()
                            save_settings()
                        elif selected == 8:
                            game_settings["show_fps"] = not game_settings.get("show_fps", True)
                            save_settings()
                        elif selected == 9:
                            # Cycle display mode
                            modes = ["Tam Ekran", "Kenarlıksız"]
                            current_mode = game_settings.get("display_mode", "Tam Ekran")
                            idx = modes.index(current_mode) if current_mode in modes else 0
                            new_mode = modes[(idx + 1) % len(modes)]
                            game_settings["display_mode"] = new_mode
                            save_settings()
                            # Apply display mode change
                            info = pygame.display.Info()
                            w, h = info.current_w, info.current_h
                            if new_mode == "Tam Ekran":
                                surface = pygame.display.set_mode((w, h), pygame.FULLSCREEN)
                                self.width = w
                                self.height = h
                                game_settings["width"] = w
                                game_settings["height"] = h
                            elif new_mode == "Kenarlıksız":
                                surface = pygame.display.set_mode((w, h), pygame.NOFRAME)
                                self.width = w
                                self.height = h
                                game_settings["width"] = w
                                game_settings["height"] = h
                        elif selected == 10:
                            menu_state = "main"
                            selected = 0

            clock.tick(60)

    def show_game_over(self, surface, wave, total_kills, is_multiplayer=False):
        # Modern Grid Background for Game Over
        self._draw_background(surface)
        
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((50, 0, 0, 100)) # Dark red tint
        surface.blit(overlay, (0, 0))

        title = assets.fonts['large'].render("GAME OVER", True, (255, 50, 50))
        title_shadow = assets.fonts['large'].render("GAME OVER", True, BLACK)
        
        # Glass panel
        panel_w, panel_h = 450, 200
        HUD(self.width, self.height).draw_glass_panel(surface, (self.width//2 - panel_w//2, self.height//2 - 80, panel_w, panel_h))
        
        wave_txt = assets.fonts['normal'].render(f"Ulaştığın Dalga: {wave}", True, WHITE)
        kills_txt = assets.fonts['normal'].render(f"Öldürdüğün Zombi: {total_kills}", True, WHITE)
        prompt_str = "Odaya Dönmek için ENTER tuşuna bas..." if is_multiplayer else "Ana Menü için ENTER tuşuna bas..."
        restart_txt = assets.fonts['normal'].render(prompt_str, True, (100, 255, 100))
        
        surface.blit(title_shadow, (self.width//2 - title.get_width()//2 + 4, self.height//2 - 160 + 4))
        surface.blit(title, (self.width//2 - title.get_width()//2, self.height//2 - 160))
        
        surface.blit(wave_txt, (self.width//2 - wave_txt.get_width()//2, self.height//2 - 30))
        surface.blit(kills_txt, (self.width//2 - kills_txt.get_width()//2, self.height//2 + 20))
        surface.blit(restart_txt, (self.width//2 - restart_txt.get_width()//2, self.height//2 + 80))
        pygame.display.flip()

        clock = pygame.time.Clock()
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        waiting = False
            clock.tick(60)
        return "lobby" if is_multiplayer else "main_menu"

    def show_wave_transition(self, surface, wave):
        """Blocking wave transition — used in single-player only."""
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

    def start_wave_transition(self, wave):
        """Non-blocking wave transition — starts an overlay timer for multiplayer."""
        self._wave_overlay_wave = wave
        self._wave_overlay_start = pygame.time.get_ticks()
        self._wave_overlay_duration = 2000  # ms

    def draw_wave_overlay(self, surface):
        """Draw the wave transition overlay if active. Call every frame. Non-blocking."""
        if not hasattr(self, '_wave_overlay_start') or self._wave_overlay_start is None:
            return
        elapsed = pygame.time.get_ticks() - self._wave_overlay_start
        if elapsed >= self._wave_overlay_duration:
            self._wave_overlay_start = None
            return
        
        # Fade: full opacity for first 1.5s, then fade out in last 0.5s
        if elapsed < 1500:
            alpha = 180
        else:
            alpha = int(180 * (1.0 - (elapsed - 1500) / 500.0))
        
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, max(0, alpha)))
        surface.blit(overlay, (0, 0))
        
        wave = self._wave_overlay_wave
        txt = assets.fonts['large'].render(f"DALGA {wave}", True, RED)
        sub_txt = assets.fonts['normal'].render("Hazırlan...", True, WHITE)
        
        surface.blit(txt, (self.width//2 - txt.get_width()//2, self.height//2 - 50))
        surface.blit(sub_txt, (self.width//2 - sub_txt.get_width()//2, self.height//2 + 30))

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
            ("BOŞLUK", "Ani Kaçış (Dash - engellerden hızla sıyrılma)"),
            ("P / ESC", "Oyunu Duraklat (P) / Menü & Ayarlar (ESC)"),
            ("Y TUŞU", "Çok Oyunculuda Sohbet Penceresini Açar")
        ]
        cur_y = card1_rect.y + 44
        for key_label, desc in controls:
            bw = self._draw_key_badge(surface, card1_rect.x + 16, cur_y, key_label, badge_w=95)
            self._draw_wrapped_text(surface, desc, assets.fonts['small'], (220, 230, 240), card1_rect.x + 16 + bw + 12, cur_y + 3, col_w - bw - 40, 18)
            cur_y += 38

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

        # Check if player_name is configured. If not, prompt user once and save it!
        saved_name = game_settings.get("player_name", "").strip()
        if not saved_name:
            prompted_name = self.prompt_player_name(surface, title="ÇOK OYUNCULU - İSİM BELİRLE")
            if not prompted_name:
                return ("back", None)
            saved_name = prompted_name
            game_settings["player_name"] = saved_name
            save_settings()

        state = "browser"  # browser, create, join, lobby
        selected = 0
        rooms_list = []
        selected_room = None  # Track which room user is joining
        error_msg = ""
        error_timer = 0

        # Text input fields
        input_fields = {
            "player_name": saved_name,
            "room_name": "",
            "password": ""
        }
        active_field = "room_name"

        # Lobby state
        lobby_players = []
        lobby_chat_messages = []
        lobby_chat_input = ""
        lobby_chat_active = False
        game_started = False
        game_start_data = None

        # If returning from a game with active room, switch to lobby and inform server
        if network.connected and network.room_id:
            state = "lobby"
            network.send_return_to_lobby()

        # Connect to server
        if not network.connected:
            connected = network.connect()
            if not connected:
                error_msg = "Sunucuya bağlanılamadı!"
                error_timer = pygame.time.get_ticks()

        # Request room list
        last_room_refresh_time = pygame.time.get_ticks()
        if network.connected and state != "lobby":
            network.list_rooms()

        while True:
            current_time = pygame.time.get_ticks()

            # Auto-refresh room browser list every 2 seconds when browsing
            if state == "browser" and network.connected:
                if current_time - last_room_refresh_time > 2000:
                    network.list_rooms()
                    last_room_refresh_time = current_time

            # Process network messages
            messages = network.get_messages()
            for i, msg in enumerate(messages):
                msg_type = msg.get("type")
                if msg_type == "room_list":
                    rooms_list = msg.get("rooms", [])
                elif msg_type == "room_created":
                    state = "lobby"
                    lobby_players = []
                    lobby_chat_messages = []
                    lobby_chat_input = ""
                    lobby_chat_active = False
                    selected = 0
                elif msg_type == "room_joined":
                    state = "lobby"
                    lobby_players = []
                    lobby_chat_messages = []
                    lobby_chat_input = ""
                    lobby_chat_active = False
                    selected = 0
                elif msg_type == "room_update":
                    lobby_players = msg.get("players", [])
                elif msg_type == "chat":
                    lobby_chat_messages.append({
                        "sender": msg.get("sender_name", "Oyuncu"),
                        "text": msg.get("message", "")
                    })
                    if len(lobby_chat_messages) > 30:
                        lobby_chat_messages = lobby_chat_messages[-30:]
                elif msg_type == "player_joined":
                    pass  # room_update handles this
                elif msg_type == "player_left":
                    pass  # room_update handles this
                elif msg_type == "host_changed":
                    network.is_host = (msg.get("new_host_id") == network.player_id)
                elif msg_type == "kicked":
                    state = "browser"
                    network.room_id = None
                    network.is_host = False
                    error_msg = msg.get("message", "Odadan atıldınız!")
                    error_timer = current_time
                    network.list_rooms()
                elif msg_type == "game_started":
                    game_started = True
                    game_start_data = msg
                    # Re-queue any remaining messages (e.g. initial entity_spawn, zombie_sync)
                    # so that MultiplayerGameManager can process them!
                    for rem_msg in messages[i + 1:]:
                        network._incoming.put(rem_msg)
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
                self._draw_lobby(
                    surface, lobby_players, network.is_host, network.room_id,
                    lobby_chat_messages, lobby_chat_input, lobby_chat_active,
                    input_fields["player_name"],
                    ping=network.get_ping(),
                    error_msg=error_msg if current_time - error_timer < 3000 else ""
                )

            pygame.display.flip()

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    network.disconnect()
                    return ("quit", None)

                # Mouse click support for multiplayer menus
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    m_x, m_y = event.pos
                    if state == "browser":
                        panel_w = 600
                        panel_h = 400
                        panel_x = self.width//2 - panel_w//2
                        panel_y = self.height//2 - 180
                        # "Create Room" button
                        create_rect = pygame.Rect(panel_x + 10, panel_y + 15, panel_w - 20, 40)
                        # "Back" button
                        back_rect = pygame.Rect(panel_x + 10, panel_y + panel_h + 15, 170, 40)

                        if create_rect.collidepoint(m_x, m_y):
                            state = "create"
                            active_field = "room_name"
                            input_fields["player_name"] = game_settings.get("player_name", saved_name)
                            input_fields["room_name"] = ""
                            input_fields["password"] = ""
                            selected = 0
                        elif back_rect.collidepoint(m_x, m_y):
                            network.disconnect()
                            return ("back", None)
                        else:
                            # Room rows
                            row_y_start = panel_y + 100
                            for i, room in enumerate(rooms_list):
                                row_rect = pygame.Rect(panel_x + 10, row_y_start + i * 50 - 5, panel_w - 20, 40)
                                if row_rect.collidepoint(m_x, m_y):
                                    if room.get("game_started"):
                                        error_msg = "Oyun zaten başlamış!"
                                        error_timer = current_time
                                    elif room.get("player_count", 0) >= room.get("max_players", 4):
                                        error_msg = "Oda dolu!"
                                        error_timer = current_time
                                    else:
                                        pname = game_settings.get("player_name", saved_name).strip() or "Oyuncu"
                                        if room.get("has_password"):
                                            selected_room = room
                                            state = "join"
                                            input_fields["player_name"] = pname
                                            input_fields["password"] = ""
                                            active_field = "password"
                                        else:
                                            network.join_room(room["room_id"], pname, None)
                                    break
                    elif state == "create":
                        panel_w = 450
                        panel_x = self.width//2 - panel_w//2
                        panel_y = self.height//2 - 130
                        # Click on input fields to focus them
                        field_configs = [
                            ("room_name", panel_y + 80),
                            ("password", panel_y + 148),
                        ]
                        clicked_field = False
                        for field_key, fy in field_configs:
                            field_rect = pygame.Rect(panel_x + 30, fy, panel_w - 60, 35)
                            if field_rect.collidepoint(m_x, m_y):
                                active_field = field_key
                                clicked_field = True
                                break

                        if not clicked_field:
                            # Check Create / Back buttons
                            btn_create = pygame.Rect(panel_x + 30, panel_y + 225, 185, 42)
                            btn_back = pygame.Rect(panel_x + panel_w - 215, panel_y + 225, 185, 42)
                            if btn_create.collidepoint(m_x, m_y):
                                pname = game_settings.get("player_name", saved_name).strip() or "Oyuncu"
                                rname = input_fields["room_name"].strip()
                                pw = input_fields["password"].strip() or None
                                if not rname:
                                    error_msg = "Oda adı boş olamaz!"
                                    error_timer = current_time
                                else:
                                    network.create_room(rname, pname, pw)
                            elif btn_back.collidepoint(m_x, m_y):
                                state = "browser"
                                selected = 0
                                network.list_rooms()

                    elif state == "join":
                        panel_w = 450
                        panel_x = self.width//2 - panel_w//2
                        panel_y = self.height//2 - 90
                        field_rect = pygame.Rect(panel_x + 30, panel_y + 80, panel_w - 60, 35)
                        if field_rect.collidepoint(m_x, m_y):
                            active_field = "password"
                        else:
                            btn_join = pygame.Rect(panel_x + 30, panel_y + 145, 185, 42)
                            btn_back = pygame.Rect(panel_x + panel_w - 215, panel_y + 145, 185, 42)
                            if btn_join.collidepoint(m_x, m_y):
                                pname = game_settings.get("player_name", saved_name).strip() or "Oyuncu"
                                pw = input_fields["password"].strip() or None
                                if selected_room:
                                    network.join_room(selected_room["room_id"], pname, pw)
                            elif btn_back.collidepoint(m_x, m_y):
                                state = "browser"
                                selected = 0
                                network.list_rooms()

                    elif state == "lobby":
                        panel_h = 360
                        left_w = 350
                        right_w = 370
                        spacing = 20
                        total_w = left_w + spacing + right_w
                        left_x = self.width // 2 - total_w // 2
                        right_x = left_x + left_w + spacing
                        panel_y = self.height // 2 - 190
                        chat_input_rect = pygame.Rect(right_x + 15, panel_y + panel_h - 48, right_w - 30, 36)

                        # Check if host clicked any kick button
                        kick_clicked = False
                        if network.is_host and hasattr(self, "_lobby_kick_buttons"):
                            for k_rect, pid, pname in self._lobby_kick_buttons:
                                if k_rect.collidepoint(m_x, m_y):
                                    network.kick_player(pid)
                                    error_msg = f"{pname} odadan atıldı."
                                    error_timer = current_time
                                    kick_clicked = True
                                    break

                        if not kick_clicked:
                            if chat_input_rect.collidepoint(m_x, m_y):
                                lobby_chat_active = True
                            else:
                                lobby_chat_active = False

                            if network.is_host:
                                btn_start = pygame.Rect(self.width // 2 - 215, panel_y + panel_h + 18, 205, 45)
                                btn_leave = pygame.Rect(self.width // 2 + 10, panel_y + panel_h + 18, 205, 45)
                                if btn_start.collidepoint(m_x, m_y):
                                    # Verify all ready
                                    not_ready = [p for p in lobby_players if p.get("ready_state") == "Oyunda"]
                                    if not_ready:
                                        error_msg = "Tüm oyuncuların odaya dönmesi bekleniyor!"
                                        error_timer = current_time
                                    else:
                                        import random
                                        seed = random.randint(0, 999999)
                                        network.start_game(seed)
                                        game_start_data = {
                                            "map_seed": seed,
                                            "players": lobby_players
                                        }
                                        return ("start_game", game_start_data)
                                elif btn_leave.collidepoint(m_x, m_y):
                                    network.leave_room()
                                    state = "browser"
                                    selected = 0
                                    network.list_rooms()
                            else:
                                btn_leave = pygame.Rect(self.width // 2 - 100, panel_y + panel_h + 18, 200, 45)
                                if btn_leave.collidepoint(m_x, m_y):
                                    network.leave_room()
                                    state = "browser"
                                    selected = 0
                                    network.list_rooms()

                elif event.type == pygame.MOUSEMOTION:
                    m_x, m_y = event.pos
                    if state == "browser":
                        panel_w = 600
                        panel_x = self.width//2 - panel_w//2
                        panel_y = self.height//2 - 180
                        # Create button hover
                        create_rect = pygame.Rect(panel_x + 10, panel_y + 15, panel_w - 20, 40)
                        if create_rect.collidepoint(m_x, m_y):
                            selected = 0
                        else:
                            row_y_start = panel_y + 100
                            for i in range(len(rooms_list)):
                                row_rect = pygame.Rect(panel_x + 10, row_y_start + i * 50 - 5, panel_w - 20, 40)
                                if row_rect.collidepoint(m_x, m_y):
                                    selected = i + 1
                                    break

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if state == "create" or state == "join":
                            state = "browser"
                            selected = 0
                            selected_room = None
                            network.list_rooms()
                        elif state == "lobby":
                            if lobby_chat_active:
                                lobby_chat_active = False
                            else:
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
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            if selected == 0:
                                # Create room
                                state = "create"
                                active_field = "room_name"
                                input_fields["player_name"] = game_settings.get("player_name", saved_name)
                                input_fields["room_name"] = ""
                                input_fields["password"] = ""
                                selected = 0
                            elif selected > 0 and selected <= len(rooms_list):
                                room = rooms_list[selected - 1]
                                if room.get("game_started"):
                                    error_msg = "Oyun zaten başlamış!"
                                    error_timer = current_time
                                elif room.get("player_count", 0) >= room.get("max_players", 4):
                                    error_msg = "Oda dolu!"
                                    error_timer = current_time
                                else:
                                    pname = game_settings.get("player_name", saved_name).strip() or "Oyuncu"
                                    if room.get("has_password"):
                                        selected_room = room
                                        state = "join"
                                        input_fields["password"] = ""
                                        active_field = "password"
                                    else:
                                        network.join_room(room["room_id"], pname, None)

                    elif state == "create":
                        if event.key == pygame.K_TAB:
                            fields = ["room_name", "password"]
                            idx = fields.index(active_field) if active_field in fields else 0
                            active_field = fields[(idx + 1) % len(fields)]
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            pname = game_settings.get("player_name", saved_name).strip() or "Oyuncu"
                            rname = input_fields["room_name"].strip()
                            pw = input_fields["password"].strip() or None

                            if not rname:
                                error_msg = "Oda adı boş olamaz!"
                                error_timer = current_time
                            else:
                                network.create_room(rname, pname, pw)
                        elif event.key == pygame.K_ESCAPE:
                            state = "browser"
                            selected = 0
                            network.list_rooms()
                        elif event.key == pygame.K_BACKSPACE:
                            input_fields[active_field] = input_fields[active_field][:-1]
                        else:
                            if event.unicode and event.unicode.isprintable() and len(input_fields[active_field]) < 20:
                                input_fields[active_field] += event.unicode

                    elif state == "join":
                        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            pname = game_settings.get("player_name", saved_name).strip() or "Oyuncu"
                            pw = input_fields["password"].strip() or None
                            if selected_room:
                                network.join_room(selected_room["room_id"], pname, pw)
                        elif event.key == pygame.K_ESCAPE:
                            state = "browser"
                            selected = 0
                            network.list_rooms()
                        elif event.key == pygame.K_BACKSPACE:
                            input_fields["password"] = input_fields["password"][:-1]
                        else:
                            if event.unicode and event.unicode.isprintable() and len(input_fields["password"]) < 20:
                                input_fields["password"] += event.unicode

                    elif state == "lobby":
                        if lobby_chat_active:
                            if event.key == pygame.K_ESCAPE:
                                lobby_chat_active = False
                            elif event.key == pygame.K_RETURN:
                                text = lobby_chat_input.strip()
                                if text:
                                    network.send_chat(text)
                                    my_name = input_fields["player_name"].strip() or "Ben"
                                    lobby_chat_messages.append({"sender": my_name, "text": text})
                                    if len(lobby_chat_messages) > 30:
                                        lobby_chat_messages = lobby_chat_messages[-30:]
                                    lobby_chat_input = ""
                                lobby_chat_active = False
                            elif event.key == pygame.K_BACKSPACE:
                                lobby_chat_input = lobby_chat_input[:-1]
                            else:
                                if event.unicode and event.unicode.isprintable() and len(lobby_chat_input) < 50:
                                    lobby_chat_input += event.unicode
                        else:
                            if event.key == pygame.K_y:
                                lobby_chat_active = True
                            elif event.key == pygame.K_RETURN:
                                if network.is_host:
                                    not_ready = [p for p in lobby_players if p.get("ready_state") == "Oyunda"]
                                    if not_ready:
                                        error_msg = "Tüm oyuncuların odaya dönmesi bekleniyor!"
                                        error_timer = current_time
                                    else:
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

        # Active player name badge
        pname_badge = game_settings.get("player_name", "").strip() or "Oyuncu"
        p_surf = assets.fonts['small'].render(f"Oyuncu: {pname_badge}", True, (100, 210, 255))
        surface.blit(p_surf, (panel_x + panel_w - p_surf.get_width() - 20, y + 5))

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

        # Navigation back button
        back_rect = pygame.Rect(panel_x + 10, panel_y + panel_h + 15, 170, 40)
        pygame.draw.rect(surface, (40, 40, 60), back_rect, border_radius=6)
        pygame.draw.rect(surface, (80, 80, 120), back_rect, 1, border_radius=6)
        back_txt = assets.fonts['normal'].render("<- Geri (ESC)", True, WHITE)
        surface.blit(back_txt, (back_rect.centerx - back_txt.get_width()//2, back_rect.centery - back_txt.get_height()//2))

        # Error message
        if error_msg:
            err_surf = assets.fonts['normal'].render(error_msg, True, (255, 80, 80))
            surface.blit(err_surf, (self.width//2 - err_surf.get_width()//2, panel_y + panel_h + 65))

    def _draw_create_room(self, surface, fields, active_field, error_msg=""):
        """Draw the create room dialog."""
        self._draw_title(surface, "ODA OLUŞTUR", y_offset=-250)

        panel_w = 450
        panel_h = 290
        panel_x = self.width//2 - panel_w//2
        panel_y = self.height//2 - 130
        HUD(self.width, self.height).draw_glass_panel(surface, (panel_x, panel_y, panel_w, panel_h))

        # Current player badge
        pname = game_settings.get("player_name", fields.get("player_name", "")).strip() or "Oyuncu"
        p_badge = assets.fonts['small'].render(f"Oyuncu: {pname}", True, (100, 210, 255))
        surface.blit(p_badge, (panel_x + 30, panel_y + 18))

        field_configs = [
            ("Oda Adı:", "room_name"),
            ("Şifre (opsiyonel):", "password"),
        ]

        y = panel_y + 48
        for label, field_key in field_configs:
            # Label
            lbl = assets.fonts['normal'].render(label, True, WHITE)
            surface.blit(lbl, (panel_x + 30, y))
            y += 32

            # Input box
            is_active = active_field == field_key
            box_color = (50, 255, 100) if is_active else (100, 100, 100)
            pygame.draw.rect(surface, (20, 20, 35), (panel_x + 30, y, panel_w - 60, 35), border_radius=5)
            pygame.draw.rect(surface, box_color, (panel_x + 30, y, panel_w - 60, 35), 2, border_radius=5)

            # Text content
            display_text = fields.get(field_key, "")
            if field_key == "password" and display_text:
                display_text = "*" * len(display_text)
            if is_active:
                cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
                display_text += cursor

            txt_surf = assets.fonts['normal'].render(display_text, True, WHITE)
            surface.blit(txt_surf, (panel_x + 40, y + 5))
            y += 48

        # Buttons
        btn_create = pygame.Rect(panel_x + 30, panel_y + 225, 185, 42)
        btn_back = pygame.Rect(panel_x + panel_w - 215, panel_y + 225, 185, 42)
        pygame.draw.rect(surface, (30, 120, 60), btn_create, border_radius=6)
        pygame.draw.rect(surface, (60, 220, 100), btn_create, 1, border_radius=6)
        c_txt = assets.fonts['normal'].render("Oluştur (ENTER)", True, WHITE)
        surface.blit(c_txt, (btn_create.centerx - c_txt.get_width()//2, btn_create.centery - c_txt.get_height()//2))

        pygame.draw.rect(surface, (70, 35, 35), btn_back, border_radius=6)
        pygame.draw.rect(surface, (150, 60, 60), btn_back, 1, border_radius=6)
        b_txt = assets.fonts['normal'].render("Geri (ESC)", True, WHITE)
        surface.blit(b_txt, (btn_back.centerx - b_txt.get_width()//2, btn_back.centery - b_txt.get_height()//2))

        # Error
        if error_msg:
            err_surf = assets.fonts['normal'].render(error_msg, True, (255, 80, 80))
            surface.blit(err_surf, (self.width//2 - err_surf.get_width()//2, panel_y + panel_h + 15))

    def _draw_join_room_dialog(self, surface, fields, active_field, room_name, error_msg=""):
        """Draw the join room dialog."""
        self._draw_title(surface, f"ODAYA KATIL: {room_name}", y_offset=-220)

        panel_w = 450
        panel_h = 210
        panel_x = self.width//2 - panel_w//2
        panel_y = self.height//2 - 90
        HUD(self.width, self.height).draw_glass_panel(surface, (panel_x, panel_y, panel_w, panel_h))

        # Current player badge
        pname = game_settings.get("player_name", fields.get("player_name", "")).strip() or "Oyuncu"
        p_badge = assets.fonts['small'].render(f"Oyuncu: {pname}", True, (100, 210, 255))
        surface.blit(p_badge, (panel_x + 30, panel_y + 18))

        lbl = assets.fonts['normal'].render("Oda Şifresi:", True, WHITE)
        surface.blit(lbl, (panel_x + 30, panel_y + 48))

        box_color = (50, 255, 100) if active_field == "password" else (100, 100, 100)
        pygame.draw.rect(surface, (20, 20, 35), (panel_x + 30, panel_y + 80, panel_w - 60, 35), border_radius=5)
        pygame.draw.rect(surface, box_color, (panel_x + 30, panel_y + 80, panel_w - 60, 35), 2, border_radius=5)

        display_text = "*" * len(fields.get("password", ""))
        cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
        display_text += cursor
        txt_surf = assets.fonts['normal'].render(display_text, True, WHITE)
        surface.blit(txt_surf, (panel_x + 40, panel_y + 85))

        # Buttons
        btn_join = pygame.Rect(panel_x + 30, panel_y + 145, 185, 42)
        btn_back = pygame.Rect(panel_x + panel_w - 215, panel_y + 145, 185, 42)
        pygame.draw.rect(surface, (30, 120, 60), btn_join, border_radius=6)
        pygame.draw.rect(surface, (60, 220, 100), btn_join, 1, border_radius=6)
        j_txt = assets.fonts['normal'].render("Katıl (ENTER)", True, WHITE)
        surface.blit(j_txt, (btn_join.centerx - j_txt.get_width()//2, btn_join.centery - j_txt.get_height()//2))

        pygame.draw.rect(surface, (70, 35, 35), btn_back, border_radius=6)
        pygame.draw.rect(surface, (150, 60, 60), btn_back, 1, border_radius=6)
        b_txt = assets.fonts['normal'].render("Geri (ESC)", True, WHITE)
        surface.blit(b_txt, (btn_back.centerx - b_txt.get_width()//2, btn_back.centery - b_txt.get_height()//2))

        if error_msg:
            err_surf = assets.fonts['normal'].render(error_msg, True, (255, 80, 80))
            surface.blit(err_surf, (self.width//2 - err_surf.get_width()//2, panel_y + panel_h + 15))

    def _draw_lobby(self, surface, players, is_host, room_id, chat_messages=None, chat_input="", chat_active=False, local_name="Ben", ping=0, error_msg=""):
        """Draw the lobby waiting screen with players, ready states, kick buttons, and room chat."""
        self._draw_title(surface, "LOBİ", y_offset=-280)

        # Room info & ping
        if room_id:
            ping_txt = f"  |  Ping: {ping} ms" if ping > 0 else ""
            room_info = assets.fonts['small'].render(f"Oda ID: {room_id}{ping_txt}", True, (150, 150, 150))
            surface.blit(room_info, (self.width//2 - room_info.get_width()//2, self.height//2 - 225))

        if chat_messages is None:
            chat_messages = []

        self._lobby_kick_buttons = []
        all_ready = all(p.get("ready_state") != "Oyunda" for p in players)

        # Dual panel dimensions
        panel_h = 360
        left_w = 350
        right_w = 370
        spacing = 20
        total_w = left_w + spacing + right_w
        left_x = self.width // 2 - total_w // 2
        right_x = left_x + left_w + spacing
        panel_y = self.height // 2 - 190

        # === LEFT PANEL: PLAYERS ===
        HUD(self.width, self.height).draw_glass_panel(surface, (left_x, panel_y, left_w, panel_h))

        header = assets.fonts['normal'].render(f"Oyuncular ({len(players)}/4)", True, (160, 200, 255))
        surface.blit(header, (left_x + 20, panel_y + 15))
        pygame.draw.line(surface, (70, 90, 120), (left_x + 20, panel_y + 45), (left_x + left_w - 20, panel_y + 45))

        y = panel_y + 55
        player_colors = [(0, 200, 255), (255, 100, 200), (100, 255, 100), (255, 200, 50)]
        for i, p in enumerate(players):
            color = player_colors[i % len(player_colors)]
            p_index = p.get("join_index", i + 1)
            name = p.get("player_name", "?")
            p_is_host = p.get("is_host", False)
            r_state = p.get("ready_state", "Hazır")

            # Sleek dark card background for each player
            row_x = left_x + 15
            row_w = left_w - 30
            row_h = 38
            card_rect = pygame.Rect(row_x, y, row_w, row_h)
            pygame.draw.rect(surface, (24, 30, 44), card_rect, border_radius=6)
            pygame.draw.rect(surface, (48, 62, 88), card_rect, 1, border_radius=6)

            # Player index & color dot
            idx_txt = assets.fonts['small'].render(f"#{p_index}", True, (130, 150, 180))
            surface.blit(idx_txt, (row_x + 10, y + 10))
            pygame.draw.circle(surface, color, (row_x + 38, y + 19), 6)
            pygame.draw.circle(surface, (20, 20, 30), (row_x + 38, y + 19), 6, 1)

            # Player name
            d_name = name
            if len(d_name) > 11:
                d_name = d_name[:10] + ".."
            name_surf = assets.fonts['normal'].render(d_name, True, WHITE)
            surface.blit(name_surf, (row_x + 52, y + 7))

            # Host badge tag
            if p_is_host:
                host_tag = assets.fonts['small'].render("HOST", True, (255, 215, 0))
                surface.blit(host_tag, (row_x + 56 + name_surf.get_width(), y + 10))

            # Status Badge & Kick Button (neatly aligned inside the card)
            can_kick = (is_host and not p_is_host)
            badge_w = 64 if r_state == "Oyunda" else 56

            if can_kick:
                kick_w = 38
                kick_x = row_x + row_w - kick_w - 8
                kick_rect = pygame.Rect(kick_x, y + 7, kick_w, 24)
                badge_x = kick_x - badge_w - 6
                target_pid = p.get("player_id", p.get("id"))
                self._lobby_kick_buttons.append((kick_rect, target_pid, name))
                pygame.draw.rect(surface, (130, 30, 30), kick_rect, border_radius=4)
                pygame.draw.rect(surface, (220, 70, 70), kick_rect, 1, border_radius=4)
                at_txt = assets.fonts['small'].render("At", True, (255, 220, 220))
                surface.blit(at_txt, (kick_rect.centerx - at_txt.get_width()//2, kick_rect.centery - at_txt.get_height()//2))
            else:
                badge_x = row_x + row_w - badge_w - 8

            badge_rect = pygame.Rect(badge_x, y + 7, badge_w, 24)
            if r_state == "Oyunda":
                pygame.draw.rect(surface, (48, 34, 14), badge_rect, border_radius=4)
                pygame.draw.rect(surface, (230, 160, 40), badge_rect, 1, border_radius=4)
                badge_txt = assets.fonts['small'].render("Oyunda", True, (255, 190, 60))
            else:
                pygame.draw.rect(surface, (16, 44, 26), badge_rect, border_radius=4)
                pygame.draw.rect(surface, (60, 200, 100), badge_rect, 1, border_radius=4)
                badge_txt = assets.fonts['small'].render("Hazır", True, (90, 240, 130))
            surface.blit(badge_txt, (badge_rect.centerx - badge_txt.get_width()//2, badge_rect.centery - badge_txt.get_height()//2))

            y += 46

        dots = "." * ((pygame.time.get_ticks() // 500) % 4)
        wait_label = "Tüm oyuncular hazır" if all_ready else "Oyuncular bekleniyor"
        wait_txt = assets.fonts['small'].render(f"{wait_label}{dots}", True, (120, 140, 160))
        surface.blit(wait_txt, (left_x + left_w//2 - wait_txt.get_width()//2, panel_y + panel_h - 38))

        # === RIGHT PANEL: LOBBY CHAT ===
        HUD(self.width, self.height).draw_glass_panel(surface, (right_x, panel_y, right_w, panel_h))

        chat_header = assets.fonts['normal'].render("Oda Sohbeti", True, (160, 200, 255))
        surface.blit(chat_header, (right_x + 20, panel_y + 15))
        pygame.draw.line(surface, (70, 90, 120), (right_x + 20, panel_y + 45), (right_x + right_w - 20, panel_y + 45))

        # Chat message history (show last 7 messages)
        msg_area_y = panel_y + 55
        visible_msgs = chat_messages[-7:]
        if not visible_msgs:
            empty_txt = assets.fonts['small'].render("Henüz mesaj yok. [Y] ile sohbet et!", True, (110, 120, 140))
            surface.blit(empty_txt, (right_x + 20, msg_area_y + 20))
        else:
            cur_y = msg_area_y
            for m in visible_msgs:
                s_name = m.get("sender", "?")
                s_text = m.get("text", "")
                is_me = (s_name == local_name or s_name == "Ben")
                tag_col = (255, 215, 0) if is_me else (80, 210, 255)

                sender_surf = assets.fonts['small'].render(f"{s_name}: ", True, tag_col)
                surface.blit(sender_surf, (right_x + 18, cur_y))

                text_surf = assets.fonts['small'].render(s_text, True, (230, 230, 230))
                surface.blit(text_surf, (right_x + 18 + sender_surf.get_width(), cur_y))
                cur_y += 30

        # Chat input box at bottom of right panel
        input_rect = pygame.Rect(right_x + 15, panel_y + panel_h - 48, right_w - 30, 36)
        box_border_col = (60, 220, 120) if chat_active else (70, 85, 110)
        pygame.draw.rect(surface, (15, 20, 30), input_rect, border_radius=6)
        pygame.draw.rect(surface, box_border_col, input_rect, 2 if chat_active else 1, border_radius=6)

        if chat_active:
            cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
            in_txt = assets.fonts['small'].render(f"{chat_input}{cursor}", True, WHITE)
            surface.blit(in_txt, (input_rect.x + 10, input_rect.y + 8))
        else:
            placeholder = chat_input if chat_input else "[Y] Mesaj yaz... (ENTER)"
            in_txt = assets.fonts['small'].render(placeholder, True, (130, 140, 160))
            surface.blit(in_txt, (input_rect.x + 10, input_rect.y + 8))

        # === BOTTOM BUTTONS ===
        if is_host:
            btn_start = pygame.Rect(self.width//2 - 215, panel_y + panel_h + 18, 205, 45)
            btn_leave = pygame.Rect(self.width//2 + 10, panel_y + panel_h + 18, 205, 45)

            if all_ready:
                pygame.draw.rect(surface, (30, 140, 60), btn_start, border_radius=6)
                pygame.draw.rect(surface, (60, 230, 100), btn_start, 2, border_radius=6)
                s_txt = assets.fonts['normal'].render("Oyunu Başlat", True, WHITE)
            else:
                pygame.draw.rect(surface, (45, 50, 60), btn_start, border_radius=6)
                pygame.draw.rect(surface, (75, 80, 90), btn_start, 1, border_radius=6)
                s_txt = assets.fonts['small'].render("Oyunda Olanlar Var", True, (150, 150, 150))
            surface.blit(s_txt, (btn_start.centerx - s_txt.get_width()//2, btn_start.centery - s_txt.get_height()//2))

            pygame.draw.rect(surface, (70, 35, 35), btn_leave, border_radius=6)
            pygame.draw.rect(surface, (160, 60, 60), btn_leave, 1, border_radius=6)
            l_txt = assets.fonts['normal'].render("Ayrıl (ESC)", True, WHITE)
            surface.blit(l_txt, (btn_leave.centerx - l_txt.get_width()//2, btn_leave.centery - l_txt.get_height()//2))
        else:
            btn_leave = pygame.Rect(self.width//2 - 100, panel_y + panel_h + 18, 200, 45)
            pygame.draw.rect(surface, (70, 35, 35), btn_leave, border_radius=6)
            pygame.draw.rect(surface, (160, 60, 60), btn_leave, 1, border_radius=6)
            l_txt = assets.fonts['normal'].render("Ayrıl (ESC)", True, WHITE)
            surface.blit(l_txt, (btn_leave.centerx - l_txt.get_width()//2, btn_leave.centery - l_txt.get_height()//2))

        # Error message under buttons if any
        if error_msg:
            err_surf = assets.fonts['normal'].render(error_msg, True, (255, 80, 80))
            surface.blit(err_surf, (self.width//2 - err_surf.get_width()//2, panel_y + panel_h + 72))
