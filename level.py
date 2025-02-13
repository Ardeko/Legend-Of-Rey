import pygame
from settings import *
from spikes import Spike


class Level:
    def __init__(self, level_number=1):
        self.level_number = level_number
        self.walls = self.generate_walls()
        self.spikes = [Spike(200, 300), Spike(500, 450)]  # 📌 Dikenler eklendi

        # 📌 **Platformları yükle**
        self.wall_texture = pygame.image.load("assets/platform.png")
        self.wall_texture = pygame.transform.scale(self.wall_texture, (20, 20))

    def generate_walls(self):
        """Haritaya göre duvarları oluşturur"""
        if self.level_number == 1:
            return [
                pygame.Rect(50, 50, 700, 20),  # Üst duvar
                pygame.Rect(50, 530, 700, 20),  # Alt duvar
                pygame.Rect(50, 50, 20, 500),  # Sol duvar
                pygame.Rect(730, 50, 20, 500),  # Sağ duvar
                pygame.Rect(300, 200, 200, 20),  # İç engel 1
            ]
        elif self.level_number == 2:
            return [
                pygame.Rect(50, 50, 700, 20),
                pygame.Rect(50, 530, 700, 20),
                pygame.Rect(50, 50, 20, 500),
                pygame.Rect(730, 50, 20, 500),
                pygame.Rect(250, 150, 300, 20),  # Labirent Engelleri
                pygame.Rect(100, 350, 500, 20),
            ]
        elif self.level_number == 3:
            return [
                pygame.Rect(50, 50, 700, 20),
                pygame.Rect(50, 530, 700, 20),
                pygame.Rect(50, 50, 20, 500),
                pygame.Rect(730, 50, 20, 500),
                pygame.Rect(200, 250, 400, 20),
                pygame.Rect(400, 400, 300, 20),
            ]
        return []

    def draw(self, screen):
        """Duvarları ve dikenleri çizer"""
        for wall in self.walls:
            for x in range(wall.x, wall.x + wall.width, 20):
                for y in range(wall.y, wall.y + wall.height, 20):
                    screen.blit(self.wall_texture, (x, y))

        # 📌 **Dikenleri çiz**
        for spike in self.spikes:
            spike.draw(screen)

    def update(self, player):
        """Oyuncunun dikenlere çarpmasını ve çarpışmaları kontrol eder."""
        for spike in self.spikes:
            spike.check_collision(player)

    def get_enemy_positions(self):
        """Seviye numarasına göre düşmanları döndürür"""
        if self.level_number == 1:
            return [(100, 200), (400, 300)], "Goblin"
        elif self.level_number == 2:
            return [(200, 150), (500, 400)], "Spider"
        elif self.level_number == 3:
            return [(300, 250), (600, 350)], "Skeleton"
        return [], ""
