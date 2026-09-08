import pygame
import sys
from config import *
from assets import assets
from utils import init_discord_rpc
from game import GameManager
from ui import Menu

def main():
    # Initialize Pygame and Mixer
    pygame.init()
    init_discord_rpc()
    
    # Setup Display
    info = pygame.display.Info()
    full_w, full_h = info.current_w, info.current_h
    disp_mode = game_settings.get("display_mode", "Tam Ekran")

    if disp_mode == "Pencere":
        width, height = int(full_w * 0.8), int(full_h * 0.8)
        screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    elif disp_mode == "Kenarlıksız":
        width, height = full_w, full_h
        screen = pygame.display.set_mode((width, height), pygame.NOFRAME)
    else:
        width, height = full_w, full_h
        screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)

    game_settings["width"] = width
    game_settings["height"] = height
    pygame.display.set_caption("Zombi Kaçışı")
    pygame.mouse.set_visible(False)
    
    # Load all assets
    assets.load_all(width, height)
    
    clock = pygame.time.Clock()
    
    # --- INTRO SEQUENCE ---
    assets.channels['intro'].play(assets.sounds['intro'])
    fade_in_d, fade_out_d, bg_fade_d, disp_d = 2000, 2000, 2000, 2000
    start_time = pygame.time.get_ticks()
    
    show_intro = True
    while show_intro:
        elapsed = pygame.time.get_ticks() - start_time
        
        if elapsed < fade_in_d + disp_d + fade_out_d:
            screen.fill(INTRO_BG)
            
        logo_surf = assets.images['logo'].copy()
        
        if elapsed < fade_in_d:
            alpha = int((elapsed / fade_in_d) * 255)
        elif elapsed < fade_in_d + disp_d:
            alpha = 255
        elif elapsed < fade_in_d + disp_d + fade_out_d:
            alpha = int(255 - ((elapsed - (fade_in_d + disp_d)) / fade_out_d) * 255)
        elif elapsed < fade_in_d + disp_d + fade_out_d + bg_fade_d:
            alpha = 0
            bg_alpha = int(255 - ((elapsed - (fade_in_d + disp_d + fade_out_d)) / bg_fade_d) * 255)
            screen.fill((INTRO_BG[0] * bg_alpha // 255, INTRO_BG[1] * bg_alpha // 255, INTRO_BG[2] * bg_alpha // 255))
        elif not assets.channels['intro'].get_busy():
            show_intro = False
            alpha = 0
            
        logo_surf.set_alpha(alpha)
        logo_rect = logo_surf.get_rect(center=(width/2, height/2))
        screen.blit(logo_surf, logo_rect)
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    show_intro = False
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                    
        clock.tick(60)

    assets.channels['intro'].stop()
    pygame.mouse.set_visible(True)
    
    # --- MAIN MENU / GAME LOOP ---
    menu = Menu(width, height)

    while True:
        screen = pygame.display.get_surface()
        width, height = screen.get_width(), screen.get_height()
        menu.width, menu.height = width, height
        res = menu.show_main_menu(screen)
        screen = pygame.display.get_surface()
        width, height = screen.get_width(), screen.get_height()
        menu.width, menu.height = width, height
        if res == "play":
            game = GameManager(screen, width, height)
            game.run()
        elif res == "multiplayer":
            _handle_multiplayer(screen, width, height, menu)
        elif res == "quit":
            pygame.quit()
            sys.exit()


def _handle_multiplayer(screen, width, height, menu):
    """Handle the full multiplayer flow: connect, browse/create rooms, lobby, game."""
    from network import NetworkClient
    from multiplayer_game import MultiplayerGameManager

    network = NetworkClient()

    while True:
        screen = pygame.display.get_surface()
        width, height = screen.get_width(), screen.get_height()
        menu.width, menu.height = width, height
        result = menu.show_multiplayer_menu(screen, network)
        action = result[0]
        data = result[1]

        if action == "back":
            network.disconnect()
            return
        elif action == "quit":
            network.disconnect()
            pygame.quit()
            sys.exit()
        elif action == "start_game":
            # Extract game start data
            map_seed = data.get("map_seed", 0)
            player_list = data.get("players", [])
            is_host = network.is_host
            player_name = network.player_name

            # Start the multiplayer game
            game = MultiplayerGameManager(
                surface=screen,
                width=width,
                height=height,
                network=network,
                is_host=is_host,
                player_name=player_name,
                map_seed=map_seed,
                player_list=player_list
            )
            result = game.run()

            # After game ends, go back to multiplayer menu or main menu
            if result == "main_menu":
                network.disconnect()
                return
            # Otherwise loop back to multiplayer menu


if __name__ == "__main__":
    main()
