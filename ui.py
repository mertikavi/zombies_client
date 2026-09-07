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
        self.draw_glass_panel(surface, (self.width - 270, 10, 260, 165))
        
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
            options = ["Devam Et", "Ayarlar", "Ana Menüye Dön"]
        else:
            options = ["Tek Oyunculu", "Çok Oyunculu", "Ayarlar", "Çıkış"]

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
                if event.type == pygame.KEYDOWN:
                    if menu_state == "main":
                        opts_len = len(options)
                    else:
                        opts_len = len(settings_opts)

                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % opts_len
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % opts_len
                    elif event.key == pygame.K_RETURN:
                        if menu_state == "main":
                            if is_paused:
                                if selected == 0:
                                    return "resume"
                                elif selected == 1:
                                    menu_state = "settings"
                                    selected = 0
                                elif selected == 2:
                                    return "main_menu"
                            else:
                                if selected == 0:
                                    return "play"
                                elif selected == 1:
                                    return "multiplayer"
                                elif selected == 2:
                                    menu_state = "settings"
                                    selected = 0
                                elif selected == 3:
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
        info = assets.fonts['small'].render("↑↓: Seç  |  ENTER: Katıl  |  R: Yenile  |  ESC: Geri", True, (150, 150, 150))
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

                # Room name (with lock icon if password)
                name_str = room["room_name"]
                if room.get("has_password"):
                    name_str = "🔒 " + name_str
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
