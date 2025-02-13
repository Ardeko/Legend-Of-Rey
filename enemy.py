import pygame
from settings import *

# 📌 Renkler (Eğer settings.py içinde yoksa buraya ekle)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

class Enemy:
    def __init__(self, x, y, image_path):
        self.x, self.y = x, y
        self.width, self.height = 40, 40
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (40, 40))
        self.alive = True
        self.speed = 2  # Düşman hareket hızı
        self.attack_range = 50  # Saldırı menzili
        self.attack_timer = 0
        self.health = 3  # 📌 Düşmanın canı

        # 🎵 **Ses Efektleri**
        self.attack_sound = pygame.mixer.Sound("assets/enemy_attack.wav")
        self.hit_sound = pygame.mixer.Sound("assets/enemy_hit.wav")

    def update(self, screen, player):
        if not self.alive:
            return

        # 📌 Oyuncuya yaklaş
        if abs(self.x - player.x) > self.attack_range:
            if self.x < player.x:
                self.x += self.speed  
            elif self.x > player.x:
                self.x -= self.speed
        if abs(self.y - player.y) > self.attack_range:
            if self.y < player.y:
                self.y += self.speed
            elif self.y > player.y:
                self.y -= self.speed
        else:
            self.attack_timer += 1
            if self.attack_timer >= 60:  # 📌 60 frame'de bir saldır
                self.attack(player)
                self.attack_timer = 0

    def attack(self, player):
        if self.alive:
            self.attack_sound.play()
            player.take_damage()  # 📌 Oyuncunun canını azalt

    def draw(self, screen):
        if self.alive:
            screen.blit(self.image, (self.x, self.y))

    def take_damage(self):
     if self.alive:
        self.health -= 1
        self.hit_sound.play()  # 📌 Düşman vurulunca ses çalsın
        print(f"💥 {type(self).__name__} vuruldu! Kalan Can: {self.health}")
        if self.health <= 0:
            self.alive = False  # 📌 Düşman ölür
            print(f"☠️ {type(self).__name__} öldü!")

class Spider(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, "assets/spider.png")

    def attack(self, player):
        super().attack(player)
        print("🕷️ Spider ağ fırlattı!")

class Goblin(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, "assets/goblin.png")

    def attack(self, player):
        super().attack(player)
        print("👹 Goblin yakından saldırdı!")

class Skeleton(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, "assets/skeleton.png")

    def attack(self, player):
        super().attack(player)
        print("💀 Skeleton kemik fırlattı!")
