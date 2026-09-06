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
    width, height = info.current_w, info.current_h
    game_settings["width"] = width
    game_settings["height"] = height
    
    screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
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
        res = menu.show_main_menu(screen)
        if res == "play":
            game = GameManager(screen, width, height)
            game.run()
        elif res == "quit":
            pygame.quit()
            sys.exit()

if __name__ == "__main__":
    main()
