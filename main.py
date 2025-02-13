import pygame
import sys
import os
from settings import *  
from player import Player
from enemy import Enemy, Goblin, Spider, Skeleton
from level import Level
import time
import gc  
import settings  
import how_to_play  

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)  
pygame.display.set_caption("Legend of Rey 🎮")
clock = pygame.time.Clock()

# 📌 **Kaynak Dosya Yolu Ayarlama (PyInstaller için)**
def get_resource_path(relative_path):
    """PyInstaller ile paketlenmiş EXE için kaynak yolunu düzeltir."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS  
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# 📌 **Arka Planlar**
MENU_BACKGROUND = get_resource_path("assets/menubg.png")
END_SCREEN = get_resource_path("assets/end.png")
GAME_OVER_SCREEN = get_resource_path("assets/gameover.png")

# 📌 **Arka Planları Yükleme**
def load_image(path, fallback_color):
    try:
        return pygame.image.load(path)
    except pygame.error:
        bg = pygame.Surface((WIDTH, HEIGHT))
        bg.fill(fallback_color)
        return bg

background = load_image(get_resource_path("assets/background.png"), DARK_BLUE)
menu_bg = load_image(MENU_BACKGROUND, DARK_BLUE)
game_over_bg = load_image(GAME_OVER_SCREEN, BLACK)
win_bg = load_image(END_SCREEN, PURPLE)

# 🎵 **Müzik başlat**
try:
    background_music = pygame.mixer.Sound(get_resource_path("assets/background_music.wav"))
    background_music.play(-1)
except pygame.error:
    print("⚠️ Müzik yüklenemedi!")

# 📌 **Oyun Durumları**
MENU = "menu"
GAME = "game"
GAME_OVER = "game_over"
WIN = "win"
SETTINGS = "settings"
HOW_TO_PLAY = "how_to_play"
game_state = MENU
current_level = 1  
player = None  

# 📌 **Kapıyı Yükleme**
try:
    door_image = pygame.image.load(get_resource_path("assets/door.png"))
except pygame.error:
    door_image = pygame.Surface((50, 70))
    door_image.fill(BLACK)

# 📌 **Menüler**
def start_game():
    global game_state, current_level, player
    game_state = GAME
    current_level = 1  
    load_level(current_level)

def open_settings():
    global game_state
    game_state = SETTINGS  

def open_how_to_play():
    global game_state
    game_state = HOW_TO_PLAY  

def back_to_menu():
    global game_state
    game_state = MENU

def exit_game():
    pygame.quit()
    sys.exit()

def restart_game():
    global game_state, current_level, player
    current_level = 1
    load_level(current_level)
    game_state = MENU  

def next_level():
    global current_level, game_state
    if current_level < 3:  
        current_level += 1  
        load_level(current_level)
    else:
        game_state = WIN  

# 📌 **Seviyeleri Yükleme**
def load_level(level_number):
    global level, enemies, player, door_rect
    level = Level(level_number)
    enemy_positions, enemy_type = level.get_enemy_positions()
    player = Player()

    if enemy_type == "Goblin":
        enemies = [Goblin(x, y) for x, y in enemy_positions]
    elif enemy_type == "Spider":
        enemies = [Spider(x, y) for x, y in enemy_positions]
    elif enemy_type == "Skeleton":
        enemies = [Skeleton(x, y) for x, y in enemy_positions]

    door_x, door_y = WIDTH - 80, HEIGHT // 2
    door_rect = pygame.Rect(door_x, door_y, 50, 70)

load_level(current_level)

# 📌 **Arka Plan Çizme Fonksiyonları**
def draw_scaled_background(image):
    scaled_bg = pygame.transform.scale(image, (screen.get_width(), screen.get_height()))
    screen.blit(scaled_bg, (0, 0))

# 📌 **Butonlar**
button_width = 250
button_height = 60
button_x = WIDTH // 2 - button_width // 2  

start_button = pygame.Rect(button_x, 200, button_width, button_height)
settings_button = pygame.Rect(button_x, 280, button_width, button_height)
how_to_play_button = pygame.Rect(button_x, 360, button_width, button_height)
exit_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 100, 200, 50)  
restart_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 200, 200, 50)  

def draw_button(screen, rect, text, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    color = HOVER_COLOR if rect.collidepoint(mouse) else PURPLE

    pygame.draw.rect(screen, color, rect, border_radius=10)

    font = pygame.font.SysFont("Arial", 30)
    text_surface = font.render(text, True, WHITE)
    
    text_x = rect.x + (rect.width - text_surface.get_width()) // 2
    text_y = rect.y + (rect.height - text_surface.get_height()) // 2
    screen.blit(text_surface, (text_x, text_y))

    if rect.collidepoint(mouse) and click[0] == 1 and action:
        pygame.time.delay(150)
        action()

# 🔄 **Oyun Döngüsü**
running = True
while running:
    gc.collect()  

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if game_state == GAME:
                if event.key == pygame.K_z:  
                    player.attack(enemies)  
                elif event.key == pygame.K_x:  
                    player.shoot()  # 📌 X tuşuna basınca ateş et!

    if game_state == MENU:
        draw_scaled_background(menu_bg)
        font = pygame.font.SysFont("Arial", 50, bold=True)

        draw_button(screen, start_button, "Start Game", start_game)
        draw_button(screen, settings_button, "Settings", open_settings)
        draw_button(screen, how_to_play_button, "How to Play", open_how_to_play)

    elif game_state == SETTINGS:
        settings.show_settings(screen, back_to_menu)  

    elif game_state == HOW_TO_PLAY:
        how_to_play.show_how_to_play(screen, back_to_menu)  

    elif game_state == GAME:
        draw_scaled_background(background)  
        level.draw(screen)  
        player.update(level.walls, enemies)
        player.draw(screen)

        for spike in level.spikes:
            spike.check_collision(player)

        for spike in level.spikes:
            spike.draw(screen)

        for enemy in enemies:
            enemy.update(screen, player)
            enemy.draw(screen)

        screen.blit(door_image, (door_rect.x, door_rect.y))

        if pygame.Rect(player.x, player.y, player.width, player.height).colliderect(door_rect):
            next_level()

        if player.health <= 0:  
            player.die()
            game_state = GAME_OVER  

    elif game_state == GAME_OVER:
        draw_scaled_background(game_over_bg)
        draw_button(screen, restart_button, "Restart", restart_game)
        draw_button(screen, exit_button, "Exit", exit_game)

    elif game_state == WIN:
        draw_scaled_background(win_bg)
        draw_button(screen, restart_button, "Restart", restart_game)
        draw_button(screen, exit_button, "Exit", exit_game)

    pygame.display.flip()  
    clock.tick(60)  

background_music.stop()
pygame.mixer.quit()
pygame.quit()
sys.exit()
