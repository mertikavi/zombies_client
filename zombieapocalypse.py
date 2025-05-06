    
import pygame
import random
import sys
import math
from pypresence import Presence
import time


# Discord RPC ayarları
CLIENT_ID = '1369068337262235688'  # Discord Developer Portal'dan alınacak
try:
    RPC = Presence(CLIENT_ID)
    RPC.connect()
    discord_connected = True
except:
    discord_connected = False

def update_discord_presence(wave=0, zombies_killed=0, game_state="In Menu"):
    if discord_connected:
        try:
            RPC.update(
                state= f"Wave {wave} | Killed: {zombies_killed}" if wave != 0 else None,
                details=game_state,
                large_image="logo_short",
                large_text="Project_GG",
                start=int(time.time())
            )
        except:
            pass

# Renkler ve renk seçenekleri
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)  # Normal zombi rengi
GREEN = (0, 200, 0)
YELLOW = (255, 255, 0)
DARK_RED = (150, 0, 0)
PURPLE = (148, 0, 211)  # Hızlı zombi rengi
LIGHT_BLUE = (173, 216, 230)  # Dayanıklı zombi rengi
BROWN = (139, 69, 19)  # Engellerin rengi
GREY = (128, 128, 128)  # Shotgun rengi
ORANGE = (255, 165, 0)  # AK47 rengi
HEALTH_GREEN = (50, 205, 50)  # Can kiti rengi
STAMINA_BLUE = (0, 191, 255)  # Stamina bar rengi
STAMINA_BROWN = (165, 42, 42)  # Stamina paketi rengi
HEALTH_RED = (220, 20, 60)  # Can barı kırmızı kısmı

# Pygame'i başlat
pygame.init()
pygame.mixer.init()  # Ses sistemini başlat
pygame.mixer.set_num_channels(11)  # 11 kanal ayarla (background müziği için +1)

# Ekran boyutlarını kullanıcının monitör çözünürlüğüne göre al
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Zombi Kaçışı")

# Oyun ayarları
game_settings = {
    "difficulty": "Normal",  # Kolay, Normal, Zor
    "character_color": GREEN,
    "bullet_color": YELLOW
}

# Silah modellerini yükle
weapon_models = {
    "knife": pygame.image.load("./models/knife.png").convert_alpha(),
    "pistol": pygame.image.load("./models/pistol.png").convert_alpha(),
    "ak47": pygame.image.load("./models/ak47.png").convert_alpha(),
    "shotgun": pygame.image.load("./models/shotgun.png").convert_alpha()
}

# Silah modellerinin boyutlarını ve rengini ayarla
WEAPON_ICON_SIZE = (70, 70)  # Boyutu 50x50'den 70x70'e çıkardım
for weapon in weapon_models:
    # Modeli yeniden boyutlandır
    weapon_models[weapon] = pygame.transform.scale(weapon_models[weapon], WEAPON_ICON_SIZE)
    
    # Yüzey oluştur ve karakter rengiyle doldur
    colored_surface = pygame.Surface(WEAPON_ICON_SIZE, pygame.SRCALPHA)
    colored_surface.fill((*game_settings["character_color"], 255))  # RGBA formatında, alpha=0 (tamamen şeffaf)
    
    # Orijinal silah modelini renklendirilmiş yüzeye blit et
    weapon_models[weapon].set_alpha(255)  # Tam opaklık
    colored_surface.blit(weapon_models[weapon], (0, 0))
    
    # Renk karışımı modunu ayarla
    weapon_models[weapon] = colored_surface.copy()
    weapon_models[weapon].blit(colored_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

# Silah modellerini yeniden renklendirme fonksiyonu
def recolor_weapon_models():
    global weapon_models
    for weapon in weapon_models:
        # Orijinal modeli yükle
        weapon_models[weapon] = pygame.image.load(f"./models/{weapon}.png").convert_alpha()
        weapon_models[weapon] = pygame.transform.scale(weapon_models[weapon], WEAPON_ICON_SIZE)
        
        # Yüzey oluştur ve karakter rengiyle doldur
        colored_surface = pygame.Surface(WEAPON_ICON_SIZE, pygame.SRCALPHA)
        colored_surface.fill((*game_settings["character_color"], 255))
        
        # Orijinal silah modelini renklendirilmiş yüzeye blit et
        weapon_models[weapon].set_alpha(255)
        colored_surface.blit(weapon_models[weapon], (0, 0))
        
        # Renk karışımı modunu ayarla
        weapon_models[weapon] = colored_surface.copy()
        weapon_models[weapon].blit(colored_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

# Intro için gerekli değişkenler
intro_logo = pygame.image.load("./logos/logo_text.png").convert_alpha()
# Logonun orijinal boyutlarını al
original_width = intro_logo.get_width()
original_height = intro_logo.get_height()
aspect_ratio = original_width / original_height

# Ekranın yarısını hedef genişlik olarak al ve yüksekliği aspect ratio'ya göre hesapla
target_width = WIDTH // 2
target_height = int(target_width / aspect_ratio)

# Logoyu aspect ratio'sunu koruyarak yeniden boyutlandır
intro_logo = pygame.transform.scale(intro_logo, (target_width, target_height))

pygame.mouse.set_visible(False)

# Crosshair çizimi için fonksiyon
def draw_crosshair(surface, x, y, size=10, color=WHITE):
    # Yatay çizgi
    pygame.draw.line(surface, color, (x - size, y), (x + size, y), 2)
    # Dikey çizgi
    pygame.draw.line(surface, color, (x, y - size), (x, y + size), 2)
    # Merkez nokta
    pygame.draw.circle(surface, color, (x, y), 3)

# Ana menü gösterilmeden önce ekranı güncelle
pygame.display.flip()

# Ses kanallarını ayarla
background_channel = pygame.mixer.Channel(10)  # Yeni kanal (background müziği için)
intro_channel = pygame.mixer.Channel(9)  # Yeni kanal (intro müziği için)
walk_channel = pygame.mixer.Channel(0)
pistol_channel = pygame.mixer.Channel(1)
ak47_channel = pygame.mixer.Channel(2)
shotgun_channel = pygame.mixer.Channel(3)
reload_channel = pygame.mixer.Channel(4)
health_channel = pygame.mixer.Channel(5)
empty_channel = pygame.mixer.Channel(6)
knife_air_channel = pygame.mixer.Channel(7)  # Yeni kanal
knife_damage_channel = pygame.mixer.Channel(8)  # Yeni kanal

# Ses efektlerini yükle ve ses düzeylerini ayarla
background_music = pygame.mixer.Sound("./sound/background.mp3")  # Background müziğini yükle
intro_music = pygame.mixer.Sound("./sound/intro.mp3")  # İntro müziğini yükle
walk_sound = pygame.mixer.Sound("./sound/walk.mp3")
pistol_sound = pygame.mixer.Sound("./sound/pistol.mp3")
ak47_sound = pygame.mixer.Sound("./sound/ak47.mp3")
shotgun_sound = pygame.mixer.Sound("./sound/shotgun.mp3")
reload_sound = pygame.mixer.Sound("./sound/reload.mp3")
health_sound = pygame.mixer.Sound("./sound/health.mp3")
empty_sound = pygame.mixer.Sound("./sound/empty.mp3")
knife_air_sound = pygame.mixer.Sound("./sound/knife_air.mp3")  # Yeni ses
knife_damage_sound = pygame.mixer.Sound("./sound/knife_damage.mp3")  # Yeni ses

# Ses düzeylerini %50'ye ayarla
background_music.set_volume(0.3)  # Background müziği ses seviyesi biraz daha düşük
intro_music.set_volume(0.5)  # İntro müziği ses seviyesi
walk_sound.set_volume(0.5)
pistol_sound.set_volume(0.5)
ak47_sound.set_volume(0.5)
shotgun_sound.set_volume(0.5)
reload_sound.set_volume(0.5)
health_sound.set_volume(0.5)
empty_sound.set_volume(0.5)
knife_air_sound.set_volume(0.5)  # Yeni ses
knife_damage_sound.set_volume(0.5)  # Yeni ses

# Renkler ve renk seçenekleri
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)  # Normal zombi rengi
GREEN = (0, 200, 0)
YELLOW = (255, 255, 0)
DARK_RED = (150, 0, 0)
PURPLE = (148, 0, 211)  # Hızlı zombi rengi
LIGHT_BLUE = (173, 216, 230)  # Dayanıklı zombi rengi
BROWN = (139, 69, 19)  # Engellerin rengi
GREY = (128, 128, 128)  # Shotgun rengi
ORANGE = (255, 165, 0)  # AK47 rengi
HEALTH_GREEN = (50, 205, 50)  # Can kiti rengi
STAMINA_BLUE = (0, 191, 255)  # Stamina bar rengi
STAMINA_BROWN = (165, 42, 42)  # Stamina paketi rengi
HEALTH_RED = (220, 20, 60)  # Can barı kırmızı kısmı

# Karakter renk seçenekleri
CHARACTER_COLORS = {
    "Yeşil": GREEN,
    "Mavi": LIGHT_BLUE,
    "Sarı": YELLOW,
    "Turuncu": ORANGE
}

# Mermi renk seçenekleri
BULLET_COLORS = {
    "Sarı": YELLOW,
    "Kırmızı": RED,
    "Mavi": LIGHT_BLUE,
    "Beyaz": WHITE
}

# Zorluk seviyeleri ve etkileri
DIFFICULTY_SETTINGS = {
    "Kolay": {
        "zombie_damage_multiplier": 0.7,
        "zombie_speed_multiplier": 0.8,
        "health_kit_heal": 50,
        "stamina_pack_boost": 30,
        "stamina_drain_rate": 0.3,  # Koşarken stamina azalma hızı
        "stamina_regen_rate": 0.5  # Dinlenirken stamina yenilenme hızı
    },
    "Normal": {
        "zombie_damage_multiplier": 1.0,
        "zombie_speed_multiplier": 1.0,
        "health_kit_heal": 40,
        "stamina_pack_boost": 20,
        "stamina_drain_rate": 0.5,  # Koşarken stamina azalma hızı
        "stamina_regen_rate": 0.3  # Dinlenirken stamina yenilenme hızı
    },
    "Zor": {
        "zombie_damage_multiplier": 1.3,
        "zombie_speed_multiplier": 1.2,
        "health_kit_heal": 30,
        "stamina_pack_boost": 10,
        "stamina_drain_rate": .7,  # Koşarken stamina azalma hızı
        "stamina_regen_rate": 0.1  # Dinlenirken stamina yenilenme hızı
    }
}

# Oyuncu özellikleri
player_size = 40
player_speed = 5
player_sprint_speed = 10  # Koşma hızı (normal hızın 2 katı)
MAX_PLAYER_HEALTH = 100  # Maksimum can
MAX_PLAYER_STAMINA = 100  # Maksimum stamina
STAMINA_DRAIN_RATE = 0.5  # Koşarken stamina azalma hızı
STAMINA_REGEN_RATE = 0.3  # Dinlenirken stamina yenilenme hızı
HEALTH_KIT_HEAL = 40  # Can kitinin iyileştirme miktarı
STAMINA_BOOST = 20  # Stamina paketinin arttıracağı miktar

# Zombi hasarları
NORMAL_ZOMBIE_DAMAGE = 20  # Normal (kırmızı) zombi hasarı
DURABLE_ZOMBIE_DAMAGE = 40  # Dayanıklı (mavi) zombi hasarı
FAST_ZOMBIE_DAMAGE = 30  # Hızlı (mor) zombi hasarı
DAMAGE_COOLDOWN = 1000  # Hasar alma aralığı (ms)

# Can kiti üretme fonksiyonu
def spawn_health_kits(count, obstacles):
    health_kits = []
    for _ in range(count):
        x = random.randint(0, WIDTH - 40)
        y = random.randint(0, HEIGHT - 40)
        if not any(check_collision((x, y), obstacle, 40, 40) for obstacle in obstacles):
            health_kits.append([x, y])
    return health_kits

# Stamina paketi üretme fonksiyonu
def spawn_stamina_packs(count, obstacles):
    stamina_packs = []
    for _ in range(count):
        x = random.randint(0, WIDTH - 40)
        y = random.randint(0, HEIGHT - 40)
        if not any(check_collision((x, y), obstacle, 40, 40) for obstacle in obstacles):
            stamina_packs.append([x, y])
    return stamina_packs

# Zombi özellikleri
zombie_size = 40
zombie_count = 5

# Mermi
bullet_size = 5
bullet_speed = 10
magazine_size = 6
reload_time = 600  # reload.mp3 süresine göre ayarlandı (600ms)

# Silahlar ve mermi durumları
weapon_states = {
    "pistol": {"ammo": 0, "owned": False},  # Pistol başlangıçta yok
    "ak47": {"ammo": 0, "owned": False},
    "shotgun": {"ammo": 0, "owned": False},
    "knife": {"ammo": "INFINITE"},
    "slot1": None  # 1. slot başlangıçta boş
}

def switch_to_weapon(weapon_name):
    global current_weapon, current_weapon_data, bullets_in_magazine
    
    # Eğer silah sahiplenilmemişse geçiş yapma
    if weapon_name != "knife" and not weapon_states[weapon_name]["owned"]:
        return
        
    # Mevcut silahın mermi durumunu kaydet
    if current_weapon not in ["knife"]:
        weapon_states[current_weapon]["ammo"] = bullets_in_magazine
    
    # Yeni silaha geç
    current_weapon = weapon_name
    current_weapon_data = weapons[weapon_name]
    
    # Yeni silahın mermi durumunu al
    if weapon_name == "knife":
        bullets_in_magazine = "INFINITE"
    else:
        bullets_in_magazine = weapon_states[weapon_name]["ammo"]

# Silah özellikleri
weapons = {
    "pistol": {
        "damage": 1,
        "fire_rate": 1,
        "bullet_speed": bullet_speed,
        "fire_delay": 550,
        "reload_time": reload_time,
        "max_ammo": 6
    },
    "ak47": {
        "damage": 2,
        "fire_rate": 5,
        "bullet_speed": bullet_speed + 2,
        "fire_delay": 410,
        "reload_time": 600,
        "max_ammo": 30
    },
    "shotgun": {
        "damage": 3,
        "fire_rate": 1,
        "bullet_speed": bullet_speed,
        "fire_delay": 1060,
        "reload_time": 600,
        "spread": 5,
        "max_ammo": 10
    },
    "knife": {
        "damage": 1,
        "fire_delay": 1000,  # 1 saniye (knife_air.mp3 süresine göre)
        "swing_duration": 150
    }
}

# Bıçak ayarları
KNIFE_LENGTH = 80  # Bıçak çizgisinin uzunluğu
KNIFE_THICKNESS = 3  # Bıçak çizgisinin kalınlığı
knife_swing = False  # Bıçak sallanıyor mu?
knife_start_time = 0  # Bıçak sallama başlangıç zamanı
knife_angle = 0  # Bıçak açısı

# Başlangıçta sadece bıçak var
current_weapon = "knife"
current_weapon_data = weapons["knife"]
bullets_in_magazine = "INFINITE"

current_weapon = "pistol"  # Varsayılan silah
current_weapon_data = weapons[current_weapon]
last_shot_time = 0  # Son atış zamanını takip etmek için değişken

# Zaman ve skor
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 28)
large_font = pygame.font.SysFont("Arial", 48)

# Dünya engelleri ve arka plan
def generate_random_obstacles(count=6):
    obstacles = []
    min_size = 40
    max_size = 120
    
    for _ in range(count):
        while True:
            width = random.randint(min_size, max_size)
            height = random.randint(min_size, max_size)
            x = random.randint(0, WIDTH - width)
            y = random.randint(0, HEIGHT - height)
            
            # Oyuncunun spawn noktası etrafında güvenli bölge bırak
            safe_zone = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 100, 200, 200)
            obstacle_rect = pygame.Rect(x, y, width, height)
            
            # Diğer engellerle çakışma kontrolü
            overlapping = False
            for obs in obstacles:
                obs_rect = pygame.Rect(obs[0], obs[1], obs[2], obs[3])
                if obstacle_rect.colliderect(obs_rect):
                    overlapping = True
                    break
            
            # Eğer güvenli bölgeyle ve diğer engellerle çakışmıyorsa engeli ekle
            if not obstacle_rect.colliderect(safe_zone) and not overlapping:
                obstacles.append((x, y, width, height))
                break
                
    return obstacles

world = {
    "obstacles": generate_random_obstacles(),
    "background": pygame.transform.scale(pygame.image.load("background.png"), (WIDTH, HEIGHT))
}

# Oyuncu hareketi için çarpışma kontrolü
def check_player_collision_with_obstacles(player_pos, move_x, move_y):
    new_x = player_pos[0] + move_x
    new_y = player_pos[1] + move_y
    
    # Dünya sınırlarını kontrol et
    if new_x < 0 or new_x > WIDTH - player_size or new_y < 0 or new_y > HEIGHT - player_size:
        return player_pos[0], player_pos[1]
    
    # Engellerle çarpışmayı kontrol et
    for obstacle in world["obstacles"]:
        if check_collision((new_x, new_y), obstacle, player_size, obstacle[2]):
            return player_pos[0], player_pos[1]
    
    return new_x, new_y

# Çarpışma kontrolü
def check_collision(rect1, rect2, size1, size2):
    x1, y1 = rect1
    if len(rect2) == 2:  # Zombi ve mermi çarpışmasında engel boyutu yok
        x2, y2 = rect2
        return (x1 < x2 + size2 and
                x1 + size1 > x2 and
                y1 < y2 + size2 and
                y1 + size1 > y2)
    else:  # Engel ve zombi çarpışmasında engel boyutları var
        x2, y2, w2, h2 = rect2
        return (x1 < x2 + w2 and
                x1 + size1 > x2 and
                y1 < y2 + h2 and
                y1 + size1 > y2)

# Ana menü fonksiyonu
def show_main_menu(is_paused=False):
    menu_state = "main"  # main, settings
    selected_option = 0
    
    # Background müziğini başlat
    if not is_paused:  # Sadece oyun duraklatılmamışsa çal
        background_channel.play(background_music, -1)  # -1 sonsuz döngü için
        update_discord_presence(game_state="In Menu")  # Menüde olduğumuzu Discord'da göster
    
    if is_paused:
        options = ["Devam Et", "Ayarlar", "Ana Menüye Dön"]
        update_discord_presence(game_state="Game Paused")  # Oyunun duraklatıldığını Discord'da göster
    else:
        options = ["Oyna", "Ayarlar", "Çıkış"]
    
    while True:
        screen.fill(BLACK)
        if is_paused:
            title_text = large_font.render("Oyun Duraklatıldı", True, WHITE)
        else:
            title_text = large_font.render("Zombi Kaçışı", True, WHITE)
        screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//2 - 150))

        if menu_state == "main":
            for i, option in enumerate(options):
                color = GREEN if i == selected_option else WHITE
                option_text = font.render(option, True, color)
                screen.blit(option_text, (WIDTH//2 - option_text.get_width()//2, HEIGHT//2 - 50 + i * 50))

        elif menu_state == "settings":
            settings_options = [
                f"Zorluk: {game_settings['difficulty']}",
                f"Karakter Rengi: {next(k for k, v in CHARACTER_COLORS.items() if v == game_settings['character_color'])}",
                f"Mermi Rengi: {next(k for k, v in BULLET_COLORS.items() if v == game_settings['bullet_color'])}",
                "Geri"
            ]
            
            for i, option in enumerate(settings_options):
                color = GREEN if i == selected_option else WHITE
                option_text = font.render(option, True, color)
                screen.blit(option_text, (WIDTH//2 - option_text.get_width()//2, HEIGHT//2 - 50 + i * 50))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % (4 if menu_state == "settings" else 3)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % (4 if menu_state == "settings" else 3)
                elif event.key == pygame.K_RETURN:
                    if menu_state == "main":
                        if is_paused:
                            if selected_option == 0:  # Devam Et
                                background_channel.stop()  # Menü müziğini durdur
                                return "resume"
                            elif selected_option == 1:  # Ayarlar
                                menu_state = "settings"
                                selected_option = 0
                            elif selected_option == 2:  # Ana Menüye Dön
                                background_channel.stop()  # Menü müziğini durdur
                                return "main_menu"
                        else:
                            if selected_option == 0:  # Oyna
                                background_channel.stop()  # Menü müziğini durdur
                                return "play"
                            elif selected_option == 1:  # Ayarlar
                                menu_state = "settings"
                                selected_option = 0
                            elif selected_option == 2:  # Çıkış
                                pygame.quit()
                                sys.exit()
                    elif menu_state == "settings":
                        if selected_option == 0:  # Zorluk
                            difficulties = ["Kolay", "Normal", "Zor"]
                            current_idx = difficulties.index(game_settings["difficulty"])
                            game_settings["difficulty"] = difficulties[(current_idx + 1) % 3]
                        elif selected_option == 1:  # Karakter Rengi
                            colors = list(CHARACTER_COLORS.items())
                            current_idx = next(i for i, (k, v) in enumerate(colors) if v == game_settings["character_color"])
                            game_settings["character_color"] = colors[(current_idx + 1) % len(colors)][1]
                            recolor_weapon_models()  # Silah modellerini yeni karakter rengine göre güncelle
                        elif selected_option == 2:  # Mermi Rengi
                            colors = list(BULLET_COLORS.items())
                            current_idx = next(i for i, (k, v) in enumerate(colors) if v == game_settings["bullet_color"])
                            game_settings["bullet_color"] = colors[(current_idx + 1) % len(colors)][1]
                        elif selected_option == 3:  # Geri
                            menu_state = "main"
                            selected_option = 0

# Game Over ekranı fonksiyonu
def show_game_over(wave, total_kills):  # total_kills parametresi eklendi
    screen.fill(BLACK)
    title_text = large_font.render("GAME OVER", True, RED)
    wave_text = font.render(f"Ulaştığın Dalga: {wave}", True, WHITE)
    kills_text = font.render(f"Öldürdüğün Zombi: {total_kills}", True, WHITE)  # Yeni satır
    restart_text = font.render("Tekrar oynamak için herhangi bir tuşa bas", True, GREEN)
    
    screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//2 - 100))
    screen.blit(wave_text, (WIDTH//2 - wave_text.get_width()//2, HEIGHT//2 - 40))
    screen.blit(kills_text, (WIDTH//2 - kills_text.get_width()//2, HEIGHT//2))  # Yeni satır
    screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 50))
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                waiting = False

# Zombi üretme fonksiyonu
def spawn_zombies(count, player_pos, wave):
    z_list = []
    min_distance = 200  # Oyuncudan minimum mesafe
    
    for _ in range(count):
        # Haritanın kenarlarını seç (0: üst, 1: sağ, 2: alt, 3: sol)
        edge = random.randint(0, 3)
        
        if edge == 0:  # Üst kenar
            x = random.randint(0, WIDTH - zombie_size)
            y = -zombie_size
        elif edge == 1:  # Sağ kenar
            x = WIDTH
            y = random.randint(0, HEIGHT - zombie_size)
        elif edge == 2:  # Alt kenar
            x = random.randint(0, WIDTH - zombie_size)
            y = HEIGHT
        else:  # Sol kenar
            x = -zombie_size
            y = random.randint(0, HEIGHT - zombie_size)
        
        # Zombi tipini belirle
        zombie_type = random.randint(1, 100)  # 1-100 arası rastgele sayı
        if zombie_type <= 50:  # %50 normal zombi (kırmızı)
            health = 1
            speed = 1 + wave * 0.2
            color = "red"
        elif zombie_type <= 80:  # %30 dayanıklı zombi (mavi)
            health = 2
            speed = 1.5 + wave * 0.2
            color = "blue"
        else:  # %20 hızlı zombi (mor)
            health = 1
            speed = 2.5 + wave * 0.3
            color = "purple"
            
        z_list.append([x, y, health, speed, color])
            
    return z_list

# Silah üretme fonksiyonu
def spawn_weapons(count, obstacles):
    weapons_list = []
    for _ in range(count):
        weapon_type = random.choice(["shotgun", "ak47"])  # Sadece yerden alınabilen silahlar
        x = random.randint(0, WIDTH - 40)
        y = random.randint(0, HEIGHT - 40)
        if not any(check_collision((x, y), obstacle, 40, 40) for obstacle in obstacles):  # Silah engellere çarpmamalı
            weapons_list.append([x, y, weapon_type])
    return weapons_list

# Zombi engellerin etrafından dolaşma fonksiyonu
def move_zombie_around_obstacles(zombie_pos, obstacles):
    z_x, z_y = zombie_pos[0], zombie_pos[1]
    z_speed = zombie_pos[3]
    
    # Engellere çarpma kontrolü ve yön düzeltme
    for obstacle in obstacles:
        ox, oy, ow, oh = obstacle
        # Zombinin engelle çarpıp çarpışmadığını kontrol et
        if check_collision((z_x, z_y), obstacle, zombie_size, ow):
            # Engelin hangi tarafında olduğunu belirle
            on_left = z_x < ox - zombie_size/2
            on_right = z_x > ox + ow + zombie_size/2
            on_top = z_y < oy - zombie_size/2
            on_bottom = z_y > oy + oh + zombie_size/2
            
            # Engele göre pozisyonu düzelt ve fazladan itme uygula
            push_distance = 2  # İtme mesafesi
            if on_left:
                z_x = ox - zombie_size - push_distance
            elif on_right:
                z_x = ox + ow + push_distance
            
            if on_top:
                z_y = oy - zombie_size - push_distance
            elif on_bottom:
                z_y = oy + oh + push_distance
            
            # Köşelerden kaçınma
            if (on_left or on_right) and (on_top or on_bottom):
                diagonal_push = push_distance * 1.4  # Köşegen itme
                z_x += (-diagonal_push if on_right else diagonal_push)
                z_y += (-diagonal_push if on_bottom else diagonal_push)
    
    # Harita sınırlarını kesin olarak kontrol et
    z_x = max(zombie_size, min(WIDTH - zombie_size, z_x))
    z_y = max(zombie_size, min(HEIGHT - zombie_size, z_y))
    
    return z_x, z_y

# Bıçak çizgisi ve hasar kontrolü fonksiyonu
def handle_knife_attack(player_pos, mouse_pos, zombies):
    # Fare pozisyonuna göre açıyı hesapla
    dx = mouse_pos[0] - (player_pos[0] + player_size // 2)
    dy = mouse_pos[1] - (player_pos[1] + player_size // 2)
    base_angle = math.atan2(dy, dx)
    
    # 60 derece = pi/3 radyan
    angle_span = math.pi / 3
    start_angle = base_angle - angle_span / 2
    end_angle = base_angle + angle_span / 2
    
    # Yayı çizmek için noktalar oluştur
    center_x = player_pos[0] + player_size // 2
    center_y = player_pos[1] + player_size // 2
    
    # Kalın yay çizimi için iç ve dış noktaları oluştur
    outer_points = []
    inner_points = []
    steps = 20  # Yayın pürüzsüzlüğü için nokta sayısı
    
    for i in range(steps + 1):
        angle = start_angle + (end_angle - start_angle) * (i / steps)
        # Dış yay noktaları
        outer_x = center_x + math.cos(angle) * KNIFE_LENGTH
        outer_y = center_y + math.sin(angle) * KNIFE_LENGTH
        outer_points.append((int(outer_x), int(outer_y)))
        
        # İç yay noktaları (biraz daha kısa)
        inner_x = center_x + math.cos(angle) * (KNIFE_LENGTH - KNIFE_THICKNESS * 2)
        inner_y = center_y + math.sin(angle) * (KNIFE_LENGTH - KNIFE_THICKNESS * 2)
        inner_points.append((int(inner_x), int(inner_y)))
    
    # Yay alanını çiz
    if len(outer_points) >= 2:
        # Kalın yay çizimi için polygon oluştur
        points = outer_points + list(reversed(inner_points))
        pygame.draw.polygon(screen, (*game_settings["bullet_color"], 128), points)
    
    # Çarpışma kontrolü
    damaged_zombies = []
    for zombie in zombies:
        # Zombinin merkez noktası
        zombie_center_x = zombie[0] + zombie_size // 2
        zombie_center_y = zombie[1] + zombie_size // 2
        
        # Zombinin ana karaktere olan uzaklığını hesapla
        zombie_dx = zombie_center_x - center_x
        zombie_dy = zombie_center_y - center_y
        zombie_dist = math.hypot(zombie_dx, zombie_dy)
        zombie_angle = math.atan2(zombie_dy, zombie_dx)
        
        # Açıları normalize et
        while zombie_angle < 0:
            zombie_angle += 2 * math.pi
        while start_angle < 0:
            start_angle += 2 * math.pi
        while end_angle < 0:
            end_angle += 2 * math.pi
            
        if start_angle > end_angle:
            end_angle += 2 * math.pi
            if zombie_angle < math.pi:
                zombie_angle += 2 * math.pi

        # Zombinin merkez noktası ve köşelerini kontrol et
        corners = [
            (zombie[0], zombie[1]),  # Sol üst
            (zombie[0] + zombie_size, zombie[1]),  # Sağ üst
            (zombie[0], zombie[1] + zombie_size),  # Sol alt
            (zombie[0] + zombie_size, zombie[1] + zombie_size),  # Sağ alt
            (zombie_center_x, zombie_center_y)  # Merkez
        ]
        
        for corner_x, corner_y in corners:
            corner_dx = corner_x - center_x
            corner_dy = corner_y - center_y
            corner_dist = math.hypot(corner_dx, corner_dy)
            corner_angle = math.atan2(corner_dy, corner_dx)
            
            # Köşe açısını normalize et
            while corner_angle < 0:
                corner_angle += 2 * math.pi
            if start_angle > end_angle and corner_angle < math.pi:
                corner_angle += 2 * math.pi
                
            # Eğer herhangi bir köşe yay içindeyse ve mesafe uygunsa
            if corner_dist <= KNIFE_LENGTH * 1.1 and start_angle <= corner_angle <= end_angle:  # %10 tolerans ekle
                damaged_zombies.append(zombie)
                break
    
    return damaged_zombies

# Ana oyun döngüsü fonksiyonu
def game_loop():
    global current_weapon, current_weapon_data, bullets_in_magazine, weapon_states
    
    # Silah durumlarını sıfırla - başlangıçta sadece bıçak var
    weapon_states = {
        "pistol": {"ammo": 6, "owned": False},
        "ak47": {"ammo": 0, "owned": False},
        "shotgun": {"ammo": 0, "owned": False},
        "knife": {"ammo": "INFINITE", "owned": True},
        "slot1": None
    }
    
    # Başlangıçta bıçak seçili
    current_weapon = "knife"
    current_weapon_data = weapons["knife"]
    bullets_in_magazine = "INFINITE"

    # Zorluk ayarlarını al
    difficulty_settings = DIFFICULTY_SETTINGS[game_settings["difficulty"]]
    zombie_damage_multiplier = difficulty_settings["zombie_damage_multiplier"]
    zombie_speed_multiplier = difficulty_settings["zombie_speed_multiplier"]
    HEALTH_KIT_HEAL = difficulty_settings["health_kit_heal"]
    STAMINA_BOOST = difficulty_settings["stamina_pack_boost"]
    STAMINA_DRAIN_RATE = difficulty_settings["stamina_drain_rate"]
    STAMINA_REGEN_RATE = difficulty_settings["stamina_regen_rate"]

    
    player_pos = [WIDTH//2, HEIGHT//2]
    wave = 1
    base_zombie_count = 5
    initial_zombies = 3
    zombie_count = base_zombie_count + (wave - 1) * 2
    zombies_required = zombie_count
    zombies = spawn_zombies(initial_zombies, player_pos, wave - 1)
    bullets = []
    
    reloading = False
    reload_start = 0
    last_shot_time = 0
    game_over = False
    player_health = MAX_PLAYER_HEALTH
    player_stamina = MAX_PLAYER_STAMINA
    zombies_killed = 0
    total_zombies_killed = 0  # Toplam öldürülen zombi sayısını takip etmek için değişken
    last_damage_time = 0
    last_spawn_time = 0  # Son zombi spawn zamanını takip etmek için
    spawn_delay = 3000  # Zombi spawn aralığı (ms)
    spawn_delay_decrease = 100  # Her wave'de spawn süresinin azalma miktarı

    # Silahlar, can kitleri ve stamina paketleri ile spawn edilen nesneler
    weapons_on_ground = spawn_weapons(3, world["obstacles"])
    health_kits = spawn_health_kits(2, world["obstacles"])
    stamina_packs = spawn_stamina_packs(2, world["obstacles"])  # Stamina paketlerini ekle

    while not game_over:
        screen.fill(BLACK)
        screen.blit(world["background"], (0, 0))
        current_time = pygame.time.get_ticks()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    menu_action = show_main_menu(is_paused=True)
                    if menu_action == "main_menu":
                        return
                    elif menu_action == "resume":
                        # Silah modellerini ve zorluk ayarlarını güncelle
                        recolor_weapon_models()
                        # Zorluk ayarlarını güncelle
                        difficulty_settings = DIFFICULTY_SETTINGS[game_settings["difficulty"]]
                        zombie_damage_multiplier = difficulty_settings["zombie_damage_multiplier"]
                        zombie_speed_multiplier = difficulty_settings["zombie_speed_multiplier"]
                        HEALTH_KIT_HEAL = difficulty_settings["health_kit_heal"]
                        STAMINA_BOOST = difficulty_settings["stamina_pack_boost"]
                        STAMINA_DRAIN_RATE = difficulty_settings["stamina_drain_rate"]
                        STAMINA_REGEN_RATE = difficulty_settings["stamina_regen_rate"]
                elif event.key == pygame.K_r:  # R tuşuna basıldığında
                    # Sadece pistol için ve mermi maksimumdan az ise reload yap
                    if current_weapon == "pistol" and bullets_in_magazine < magazine_size and not reloading:
                        reloading = True
                        reload_start = current_time
                        reload_channel.play(reload_sound)
                elif event.key == pygame.K_1:  # 1 tuşu - Slot 1 silahı
                    if weapon_states["slot1"] is not None and weapon_states[weapon_states["slot1"]]["owned"]:
                        # Mevcut silahın mermi durumunu kaydet
                        if current_weapon not in ["knife"]:
                            weapon_states[current_weapon]["ammo"] = bullets_in_magazine
                        # Slot 1 silahına geç
                        current_weapon = weapon_states["slot1"]
                        current_weapon_data = weapons[current_weapon]
                        bullets_in_magazine = weapon_states[current_weapon]["ammo"]
                elif event.key == pygame.K_2:  # 2 tuşu - Pistol
                    if current_weapon != "pistol":
                        # Mevcut silahın mermi durumunu kaydet
                        if current_weapon not in ["knife"]:
                            weapon_states[current_weapon]["ammo"] = bullets_in_magazine
                        # Pistole geç
                        current_weapon = "pistol"
                        current_weapon_data = weapons[current_weapon]
                        bullets_in_magazine = weapon_states["pistol"]["ammo"]
                elif event.key == pygame.K_3:  # 3 tuşu - Bıçak
                    if current_weapon != "knife":
                        # Mevcut silahın mermi durumunu kaydet
                        if current_weapon not in ["knife"]:
                            weapon_states[current_weapon]["ammo"] = bullets_in_magazine
                        # Bıçağa geç
                        current_weapon = "knife"
                        current_weapon_data = weapons[current_weapon]
                        bullets_in_magazine = "INFINITE"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Sol tık
                current_time = pygame.time.get_ticks()
                
                if current_weapon == "knife":
                    # Bıçak saldırısı için gecikme kontrolü
                    can_attack = current_time - last_shot_time >= current_weapon_data["fire_delay"]
                    if can_attack:                        
                        # Bıçak saldırısını gerçekleştir
                        mx, my = pygame.mouse.get_pos()
                        damaged_zombies = handle_knife_attack(player_pos, (mx, my), zombies)
                        
                        # Zombiye isabet ettiyse hasar sesini çal
                        if damaged_zombies:
                            knife_damage_channel.play(knife_damage_sound)
                        else:
                            knife_air_channel.play(knife_air_sound)
                        
                        # Bıçak vuruşu hasarını uygula
                        for zombie in damaged_zombies[:]:
                            zombie[2] -= current_weapon_data["damage"]
                            if zombie[2] <= 0:
                                zombies.remove(zombie)
                                zombies_killed += 1
                                total_zombies_killed += 1
                        
                        last_shot_time = current_time
                elif not reloading:  # Diğer silahlar için kontrol
                    # Atış gecikmesi kontrolü
                    can_shoot = current_time - last_shot_time >= current_weapon_data.get("fire_delay", 0)
                    
                    # Eğer atış yapılabilirse ve mermi varsa
                    if bullets_in_magazine > 0 and can_shoot:
                        current_channel = None
                        if current_weapon == "shotgun":
                            current_channel = shotgun_channel
                        elif current_weapon == "pistol":
                            current_channel = pistol_channel
                        elif current_weapon == "ak47":
                            current_channel = ak47_channel

                        # Ses kanalı boşsa atış yap
                        if not (current_channel and current_channel.get_busy()):
                            mx, my = pygame.mouse.get_pos()
                            dx = mx - (player_pos[0] + player_size // 2)
                            dy = my - (player_pos[1] + player_size // 2)
                            dist = math.hypot(dx, dy)
                            if dist == 0:
                                dist = 1

                            # Atış işlemi
                            if current_weapon == "shotgun":
                                for i in range(5):
                                    spread_angle = math.radians(random.uniform(-15, 15))
                                    spread_dx = dx * math.cos(spread_angle) - dy * math.sin(spread_angle)
                                    spread_dy = dx * math.sin(spread_angle) + dy * math.cos(spread_angle)
                                    bullets.append([
                                        player_pos[0] + player_size // 2,
                                        player_pos[1] + player_size // 2,
                                        spread_dx / dist * current_weapon_data["bullet_speed"],
                                        spread_dy / dist * current_weapon_data["bullet_speed"]
                                    ])
                                bullets_in_magazine -= 1
                                # Silah durumunu güncelle
                                weapon_states[current_weapon]["ammo"] = bullets_in_magazine
                                shotgun_channel.play(shotgun_sound)
                            else:  # Pistol ve AK47 için ortak kod
                                bullets.append([
                                    player_pos[0] + player_size // 2,
                                    player_pos[1] + player_size // 2,
                                    dx / dist * current_weapon_data["bullet_speed"],
                                    dy / dist * current_weapon_data["bullet_speed"]
                                ])
                                bullets_in_magazine -= 1
                                # Silah durumunu güncelle
                                weapon_states[current_weapon]["ammo"] = bullets_in_magazine
                                current_channel.play(pistol_sound if current_weapon == "pistol" else ak47_sound)
                            
                            last_shot_time = current_time
                    elif bullets_in_magazine <= 0 and not empty_channel.get_busy():
                        empty_channel.play(empty_sound)

        # Reload kontrolü
        if reloading and current_weapon == "pistol":
            if current_time - reload_start >= reload_time:
                bullets_in_magazine = weapons[current_weapon]["max_ammo"]
                weapon_states[current_weapon]["ammo"] = bullets_in_magazine  # Mermi durumunu güncelle
                reloading = False

        # AK47 için otomatik ateşleme
        if pygame.mouse.get_pressed()[0] and current_weapon == "ak47":
            current_time = pygame.time.get_ticks()
            can_shoot = current_time - last_shot_time >= current_weapon_data.get("fire_delay", 0)
            
            # Sadece atış gecikmesi geçtiyse ateş et
            if bullets_in_magazine > 0 and can_shoot:
                mx, my = pygame.mouse.get_pos()
                dx = mx - (player_pos[0] + player_size // 2)
                dy = my - (player_pos[1] + player_size // 2)
                dist = math.hypot(dx, dy)
                if dist == 0:
                    dist = 1
                bullets.append([
                    player_pos[0] + player_size // 2,
                    player_pos[1] + player_size // 2,
                    dx / dist * current_weapon_data["bullet_speed"],
                    dy / dist * current_weapon_data["bullet_speed"]
                ])
                bullets_in_magazine -= 1
                ak47_channel.play(ak47_sound)
                last_shot_time = current_time
                # Silah durumunu güncelle
                weapon_states[current_weapon]["ammo"] = bullets_in_magazine

        # Mermi yokken ateşleme kontrolü (bıçak hariç)
        if pygame.mouse.get_pressed()[0] and current_weapon != "knife":
            if isinstance(bullets_in_magazine, int) and bullets_in_magazine <= 0 and not empty_channel.get_busy():
                empty_channel.play(empty_sound)

        keys = pygame.key.get_pressed()
        current_speed = player_sprint_speed if keys[pygame.K_LSHIFT] and player_stamina > 0 else player_speed
        
        # Stamina yönetimi
        if keys[pygame.K_LSHIFT] and (keys[pygame.K_a] or keys[pygame.K_d] or keys[pygame.K_w] or keys[pygame.K_s]):
            player_stamina = max(0, player_stamina - STAMINA_DRAIN_RATE)
        else:
            player_stamina = min(MAX_PLAYER_STAMINA, player_stamina + STAMINA_REGEN_RATE)

        if keys[pygame.K_a] or keys[pygame.K_d] or keys[pygame.K_w] or keys[pygame.K_s]:
            if not walk_channel.get_busy():
                walk_channel.play(walk_sound)
            if keys[pygame.K_a]:
                player_pos[0], player_pos[1] = check_player_collision_with_obstacles(player_pos, -current_speed, 0)
            if keys[pygame.K_d]:
                player_pos[0], player_pos[1] = check_player_collision_with_obstacles(player_pos, current_speed, 0)
            if keys[pygame.K_w]:
                player_pos[0], player_pos[1] = check_player_collision_with_obstacles(player_pos, 0, -current_speed)
            if keys[pygame.K_s]:
                player_pos[0], player_pos[1] = check_player_collision_with_obstacles(player_pos, 0, current_speed)

        # Mermileri güncelleme
        for bullet in bullets[:]:
            bullet[0] += bullet[2]
            bullet[1] += bullet[3]
            if not (0 <= bullet[0] <= WIDTH and 0 <= bullet[1] <= HEIGHT):
                bullets.remove(bullet)
            
            # Mermilerin engellerle çarpışmasını kontrol et
            for obstacle in world["obstacles"]:
                if check_collision((bullet[0], bullet[1]), obstacle, bullet_size, obstacle[2]):
                    bullets.remove(bullet)
                    break

        # Zombi hareketi ve hasar
        for z in zombies[:]:
            dx = player_pos[0] - z[0]
            dy = player_pos[1] - z[1]
            dist = math.hypot(dx, dy)
            if dist == 0:
                dist = 1

            # Zorluk seviyesine göre hız ayarla
            base_speed = z[3] * zombie_speed_multiplier
            move_x = dx / dist * base_speed
            move_y = dy / dist * base_speed

            # Engellere göre yeni pozisyon hesapla
            new_x, new_y = z[0], z[1]
            can_move_x = True
            can_move_y = True

            # X ve Y eksenlerinde ayrı ayrı hareket kontrolü
            test_x = new_x + move_x
            test_y = new_y + move_y

            # X ekseni hareketi için engel kontrolü
            for obstacle in world["obstacles"]:
                if check_collision((test_x, new_y), obstacle, zombie_size, obstacle[2]):
                    can_move_x = False
                    # Engelin hangi tarafında olduğunu belirle
                    if move_x > 0:  # Sağa hareket
                        new_x = obstacle[0] - zombie_size
                    else:  # Sola hareket
                        new_x = obstacle[0] + obstacle[2]
                    break

            # Y ekseni hareketi için engel kontrolü
            for obstacle in world["obstacles"]:
                if check_collision((new_x, test_y), obstacle, zombie_size, obstacle[2]):
                    can_move_y = False
                    # Engelin hangi tarafında olduğunu belirle
                    if move_y > 0:  # Aşağı hareket
                        new_y = obstacle[1] - zombie_size
                    else:  # Yukarı hareket
                        new_y = obstacle[1] + obstacle[3]
                    break

            # Engellere çarpmadan hareket edebiliyorsa hareket et
            if can_move_x:
                new_x = test_x
            if can_move_y:
                new_y = test_y

            # Harita sınırlarını kontrol et
            new_x = max(0, min(WIDTH - zombie_size, new_x))
            new_y = max(0, min(HEIGHT - zombie_size, new_y))

            # Yeni pozisyonu uygula
            z[0], z[1] = new_x, new_y

            # Oyuncuya çarpma kontrolü ve hasar verme
            if check_collision((player_pos[0], player_pos[1]), (z[0], z[1]), player_size, zombie_size):
                if current_time - last_damage_time >= DAMAGE_COOLDOWN:
                    if z[4] == "red":
                        player_health -= NORMAL_ZOMBIE_DAMAGE * zombie_damage_multiplier
                    elif z[4] == "blue":
                        player_health -= DURABLE_ZOMBIE_DAMAGE * zombie_damage_multiplier
                    elif z[4] == "purple":
                        player_health -= FAST_ZOMBIE_DAMAGE * zombie_damage_multiplier
                    last_damage_time = current_time
                    if player_health <= 0:
                        game_over = True

        # Zombi ve mermi çarpışması
        for bullet in bullets[:]:
            for z in zombies[:]:
                if check_collision((bullet[0], bullet[1]), (z[0], z[1]), bullet_size, zombie_size):
                    bullets.remove(bullet)
                    z[2] -= current_weapon_data["damage"]
                    if z[2] <= 0:
                        zombies.remove(z)
                        zombies_killed += 1
                        total_zombies_killed += 1  # Toplam öldürülen zombi sayısını artır
                        remaining_zombies_needed = zombies_required - zombies_killed - len(zombies)
                        if remaining_zombies_needed > 0:
                            new_zombie_count = min(random.randint(1, 2), remaining_zombies_needed)
                            zombies.extend(spawn_zombies(new_zombie_count, player_pos, wave - 1))
                    break

        # Silah alma kontrolü
        for weapon in weapons_on_ground[:]:
            if check_collision((player_pos[0], player_pos[1]), (weapon[0], weapon[1]), player_size, 40):
                pickup_weapon(weapon[2])
                weapons_on_ground.remove(weapon)

        # Can kiti alma kontrolü
        for health_kit in health_kits[:]:
            if check_collision((player_pos[0], player_pos[1]), (health_kit[0], health_kit[1]), player_size, 40):
                player_health = min(player_health + HEALTH_KIT_HEAL, MAX_PLAYER_HEALTH)
                health_channel.play(health_sound)  # Can kiti alındığında ses çal
                health_kits.remove(health_kit)

        # Stamina paketi alma kontrolü
        for stamina_pack in stamina_packs[:]:
            if check_collision((player_pos[0], player_pos[1]), (stamina_pack[0], stamina_pack[1]), player_size, 40):
                player_stamina = min(player_stamina + STAMINA_BOOST, MAX_PLAYER_STAMINA)
                stamina_packs.remove(stamina_pack)

        # Wave kontrolü ve silah geçişi
        if zombies_killed >= zombies_required and len(zombies) == 0:
            wave += 1
            zombies_killed = 0
            zombie_count = base_zombie_count + (wave - 1) * 2
            zombies_required = zombie_count
            
            # Oyuncunun şu anki pozisyonunu kaydet
            old_player_pos = player_pos.copy()
            
            # Yeni engelleri oluştur
            world["obstacles"] = generate_random_obstacles()
            
            # Oyuncunun pozisyonunu kontrol et ve engel içindeyse güvenli bir noktaya taşı
            for obstacle in world["obstacles"]:
                if check_collision((player_pos[0], player_pos[1]), obstacle, player_size, obstacle[2]):
                    # Oyuncuyu ekranın ortasına taşı
                    player_pos[0] = WIDTH // 2 - player_size // 2
                    player_pos[1] = HEIGHT // 2 - player_size // 2
                    break
            
            # Yeni engellere göre zombileri oluştur
            zombies = spawn_zombies(initial_zombies, player_pos, wave - 1)
            last_spawn_time = current_time  # Son spawn zamanını güncelle
            
            # Yeni wave başladığında sağlık kiti ve stamina paketi yenileme
            health_kits = spawn_health_kits(2, world["obstacles"])  # health_kits'i tamamen yenile
            stamina_packs = spawn_stamina_packs(2, world["obstacles"])  # stamina_packs'i tamamen yenile
            weapons_on_ground = spawn_weapons(3, world["obstacles"]) # weapons_on_ground'i tamamen yenile
            
            # Wave değişim ekranını göster
            screen.fill(BLACK)
            wave_text = large_font.render(f"WAVE {wave}", True, RED)
            text_rect = wave_text.get_rect(center=(WIDTH/2, HEIGHT/2))
            screen.blit(wave_text, text_rect)
            pygame.display.flip()
            pygame.time.delay(2000)  # 2 saniye bekle

        # Kademeli zombi spawn sistemi
        if current_time - last_spawn_time >= spawn_delay and len(zombies) < zombies_required:
            remaining_zombies_needed = zombies_required - zombies_killed - len(zombies)
            new_zombie_count = min(random.randint(1, 2), remaining_zombies_needed)
            zombies.extend(spawn_zombies(new_zombie_count, player_pos, wave - 1))
            last_spawn_time = current_time  # Son spawn zamanını güncelle

        # Mermi kontrolü ve otomatik pistole geçiş
        if current_weapon not in ["knife", "pistol"]:  # Sadece AK47 ve Shotgun için kontrol et
            if isinstance(bullets_in_magazine, (int, float)) and bullets_in_magazine <= 0:
                # Silahı envanterden kaldır
                weapon_states[current_weapon]["owned"] = False
                # Pistole geç
                current_weapon = "pistol"
                current_weapon_data = weapons[current_weapon]
                bullets_in_magazine = weapon_states["pistol"]["ammo"]
                last_shot_time = 0

        # Mermileri çizme
        for bullet in bullets:
            pygame.draw.circle(screen, game_settings["bullet_color"], (int(bullet[0]), int(bullet[1])), bullet_size)
        
        # Zombileri çizme
        for z in zombies:
            # İç renk (fill color)
            color = RED if z[4] == "red" else LIGHT_BLUE if z[4] == "blue" else PURPLE
            # Dış çizgi rengi (outline color)
            outline_color = DARK_RED if z[4] == "red" else (0, 0, 150) if z[4] == "blue" else (50, 0, 50)
            
            pygame.draw.rect(screen, color, (int(z[0]), int(z[1]), zombie_size, zombie_size))
            pygame.draw.rect(screen, outline_color, (int(z[0]), int(z[1]), zombie_size, zombie_size), 2)

        # Oyuncu karakterini çiz
        pygame.draw.rect(screen, game_settings["character_color"], (*player_pos, player_size, player_size))

        # Engelleri çizme
        for obstacle in world["obstacles"]:
            pygame.draw.rect(screen, BROWN, (obstacle[0], obstacle[1], obstacle[2], obstacle[3]))

        # Silahları yere yerleştirme
        for weapon in weapons_on_ground:
            # Tüm silahlar sarı renkte
            pygame.draw.rect(screen, YELLOW, (weapon[0], weapon[1], 40, 40))
            # Silah adını gri renkte üzerine yaz
            weapon_name = weapon[2].upper()
            weapon_label = font.render(weapon_name, True, GREY)
            # Yazıyı silahın üzerine ortalayarak yerleştir
            label_x = weapon[0] + (40 - weapon_label.get_width()) // 2
            label_y = weapon[1] + (40 - weapon_label.get_height()) // 2
            screen.blit(weapon_label, (label_x, label_y))

        # Can kitlerini yere yerleştirme
        for health_kit in health_kits:
            pygame.draw.rect(screen, HEALTH_GREEN, (health_kit[0], health_kit[1], 40, 40))

        # Stamina paketlerini çizme
        for stamina_pack in stamina_packs:
            pygame.draw.rect(screen, STAMINA_BROWN, (stamina_pack[0], stamina_pack[1], 40, 40))

        # Can barı
        health_bar_width = 200
        health_bar_height = 20
        health_bar_x = 10
        health_bar_y = HEIGHT - 60  # Stamina barının üstüne yerleştir

        # Can barı arka planı (kırmızı)
        pygame.draw.rect(screen, HEALTH_RED, (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
        
        # Can barı doluluk oranı (yeşil)
        health_width = int((player_health / MAX_PLAYER_HEALTH) * health_bar_width)
        pygame.draw.rect(screen, HEALTH_GREEN, (health_bar_x, health_bar_y, health_width, health_bar_height))
        
        # Can değeri yazısı
        health_percentage = int((player_health / MAX_PLAYER_HEALTH) * 100)
        health_text = font.render(f"{health_percentage}%", True, WHITE)
        # Yazıyı barın içine ortalayarak yerleştir
        health_text_x = health_bar_x + (health_bar_width - health_text.get_width()) // 2
        health_text_y = health_bar_y + (health_bar_height - health_text.get_height()) // 2
        screen.blit(health_text, (health_text_x, health_text_y))

        # Stamina bar
        stamina_bar_width = 200
        stamina_bar_height = 20
        stamina_bar_x = 10
        stamina_bar_y = HEIGHT - 30
        
        # Stamina bar arka planı (gri)
        pygame.draw.rect(screen, (64, 64, 64), (stamina_bar_x, stamina_bar_y, stamina_bar_width, stamina_bar_height))
        
        # Stamina bar doluluk oranı (mavi)
        stamina_width = int((player_stamina / MAX_PLAYER_STAMINA) * stamina_bar_width)
        pygame.draw.rect(screen, STAMINA_BLUE, (stamina_bar_x, stamina_bar_y, stamina_width, stamina_bar_height))
        
        # Stamina değeri yazısı
        stamina_percentage = int((player_stamina / MAX_PLAYER_STAMINA) * 100)
        stamina_text = font.render(f"{stamina_percentage}%", True, WHITE)
        # Yazıyı barın içine ortalayarak yerleştir
        stamina_text_x = stamina_bar_x + (stamina_bar_width - stamina_text.get_width()) // 2
        stamina_text_y = stamina_bar_y + (stamina_bar_height - stamina_text.get_height()) // 2
        screen.blit(stamina_text, (stamina_text_x, stamina_text_y))

        # Wave ve zombi bilgisini yazdırma
        wave_text = font.render(f"Wave: {wave}", True, WHITE)
        zombies_required_text = font.render(f"Required: {zombies_required - zombies_killed}", True, WHITE)
        zombies_left_text = font.render(f"Alive: {len(zombies)}", True, WHITE)
        
        # Sağ üst köşeye yerleştirme, ekran dışına taşmayacak şekilde
        margin_right = 20  # Sağ kenardan boşluk
        screen.blit(wave_text, (WIDTH - wave_text.get_width() - margin_right, 10))
        screen.blit(zombies_required_text, (WIDTH - zombies_required_text.get_width() - margin_right, 40))
        screen.blit(zombies_left_text, (WIDTH - zombies_left_text.get_width() - margin_right, 70))

        # Envanter çizimi
        inventory_start_y = HEIGHT - 210
        weapon_spacing = 70
        inventory_x = WIDTH - 70
        
        # Envanter slotlarının arkaplan rengi (siyah yarı saydam)
        for i in range(3):
            slot_y = inventory_start_y + (weapon_spacing * i)
            slot_surface = pygame.Surface((50, 50))
            slot_surface.fill((0,0,0))
            slot_surface.set_alpha(128)
            screen.blit(slot_surface, (inventory_x, slot_y))
        
        # Silahları çiz
        weapons_to_draw = []
        
        # Alt slot - Bıçak (her zaman var)
        weapons_to_draw.append(("knife", inventory_start_y + weapon_spacing * 2))
        
        # Orta slot - Pistol (her zaman var)
        weapons_to_draw.append(("pistol", inventory_start_y + weapon_spacing))
        
        # Üst slot - AK47 veya Shotgun (eğer sahipse ve mermisi varsa)
        if weapon_states["ak47"]["owned"] and (weapon_states["ak47"]["ammo"] > 0 or current_weapon == "ak47"):
            weapons_to_draw.append(("ak47", inventory_start_y))
        elif weapon_states["shotgun"]["owned"] and (weapon_states["shotgun"]["ammo"] > 0 or current_weapon == "shotgun"):
            weapons_to_draw.append(("shotgun", inventory_start_y))
        
        # Silahları ve mermi bilgilerini çiz
        small_font = pygame.font.SysFont("Arial", 16)
        for weapon_name, y_pos in weapons_to_draw:
            weapon_surface = weapon_models[weapon_name].copy()
            # Mevcut silahın opaklığını 1, diğerlerinin 0.5 yap
            if weapon_name == current_weapon:
                weapon_surface.set_alpha(255)  # Tam opaklık
            else:
                weapon_surface.set_alpha(128)  # Yarı saydam
            screen.blit(weapon_surface, (inventory_x, y_pos))
            
            # Mermi bilgisini ekle
            if weapon_name == "knife":
                ammo_text = "1/1"
            else:
                current_ammo = weapon_states[weapon_name]["ammo"]
                max_ammo = weapons[weapon_name]["max_ammo"]
                ammo_text = f"{current_ammo}/{max_ammo}"
            
            ammo_surface = small_font.render(ammo_text, True, WHITE)
            screen.blit(ammo_surface, (inventory_x, y_pos + 50))  # Silah modelinin 50 piksel altına

        # Discord Rich Presence güncelle
        update_discord_presence(wave=wave, zombies_killed=total_zombies_killed, game_state="Playing")

        # Game Over ekranına toplam öldürülen zombi sayısını gönder
        if game_over:
            show_game_over(wave, total_zombies_killed)
            return

        # Crosshair'i çiz - mermi rengiyle aynı renkte
        mx, my = pygame.mouse.get_pos()
        draw_crosshair(screen, mx, my, size=15, color=game_settings["bullet_color"])

        # Ekran güncellemesi ve diğer işlemler
        pygame.display.update()
        clock.tick(60)

    # Game Over durumunda Discord Rich Presence güncelle
    update_discord_presence(wave=wave, zombies_killed=total_zombies_killed, game_state="Game Over")
    show_game_over(wave, total_zombies_killed)
    return

# Silah alma kontrolü
def pickup_weapon(weapon_type):
    global current_weapon, current_weapon_data, bullets_in_magazine, weapon_states
    
    # Mevcut silahın mermi durumunu kaydet
    if current_weapon not in ["knife"]:
        weapon_states[current_weapon]["ammo"] = bullets_in_magazine
        weapon_states[current_weapon]["owned"] = False  # Mevcut silahın owned durumunu false yap

    
    # Yeni silahı slot1'e yerleştir ve owned durumunu güncelle
    old_weapon = weapon_states["slot1"]  # Eski slot1 silahını kaydet
  
    weapon_states["slot1"] = weapon_type  # Yeni silahı slot1'e koy
    
    # Yeni silahı al ve mermisini ayarla
    weapon_states[weapon_type] = {
        "ammo": weapons[weapon_type]["max_ammo"],  # Silahı max mermi ile başlat
        "owned": True
    }
    
    # Yeni silaha geç
    current_weapon = weapon_type
    current_weapon_data = weapons[weapon_type]
    bullets_in_magazine = weapon_states[weapon_type]["ammo"]

# Ana oyun döngüsü
def main():
    # Intro ekranı
    fade_in_duration = 2000  # 2 saniye fade in
    fade_out_duration = 2000  # 2 saniye fade out
    background_fade_out_duration = 2000  # 2 saniye arkaplan fade out
    display_duration = 2000  # 5 saniye gösterim
    
    
    # Logo için alpha değeri (başlangıçta tamamen şeffaf)
    alpha = 0
    start_time = pygame.time.get_ticks()
    
    # Intro müziğini başlat
    intro_channel.play(intro_music)
    
    # İntro arkaplan rengi
    INTRO_BG = (239, 206, 146)  # #EFCE92
    screen.fill(INTRO_BG)
    
    # Intro ekranını göster (Enter ile atlanabilir)
    show_intro = True
    while show_intro:
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - start_time
        
        # Yeni arkaplan rengi
        if (elapsed_time < fade_in_duration + display_duration + fade_out_duration):
            screen.fill(INTRO_BG)
        
        # Logo için yeni surface oluştur
        logo_surface = intro_logo.copy()
        
        # Fade in
        if (elapsed_time < fade_in_duration):
            alpha = int((elapsed_time / fade_in_duration) * 255)
        # Logo gösterimi
        elif (elapsed_time < fade_in_duration + display_duration):
            alpha = 255
        # Fade out
        elif (elapsed_time < fade_in_duration + display_duration + fade_out_duration):
            alpha = int(255 - ((elapsed_time - (fade_in_duration + display_duration)) / fade_out_duration) * 255)
        # Arkaplan fade out
        elif (elapsed_time < fade_in_duration + display_duration + fade_out_duration + background_fade_out_duration):
            alpha = 0
            # Arkaplanı yavaşça backgorund_fade_out süresi boyunca #EFCE92 renginden siyaha çevir
            fade_out_alpha = int(255 - ((elapsed_time - (fade_in_duration + display_duration + fade_out_duration)) / background_fade_out_duration) * 255)
            screen.fill((INTRO_BG[0] * fade_out_alpha // 255, INTRO_BG[1] * fade_out_alpha // 255, INTRO_BG[2] * fade_out_alpha // 255))            
        elif (not intro_channel.get_busy()):
            show_intro = False  # İntro bitti
            
        # Alpha değerini ayarla
        logo_surface.set_alpha(alpha)
        
        # Logoyu ekranın ortasına yerleştir
        logo_rect = logo_surface.get_rect(center=(WIDTH/2, HEIGHT/2))
        screen.blit(logo_surface, logo_rect)
        
        pygame.display.flip()
        
        # Event kontrolü
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:  # ENTER tuşu
                    show_intro = False  # İntroyu atla
                elif event.key == pygame.K_ESCAPE:  # ESC tuşu
                    pygame.quit()
                    sys.exit()
        
        clock.tick(60)
    
    # İntro müziğini durdur
    intro_channel.stop()
    
    # Ana oyun döngüsüne gir
    while True:
        menu_result = show_main_menu()  # Ana menüyü göster
        if menu_result == "play":
            game_loop()  # Oyunu başlat

if __name__ == "__main__":
    main()