import pygame
from settings import *
from projectile import Projectile

class Player:
    def __init__(self):
        self.x, self.y = 100, 100
        self.width, self.height = 40, 40
        self.speed = 4
        self.health = 3  
        self.max_health = 3  
        self.image = pygame.image.load("assets/rey.png")
        self.image = pygame.transform.scale(self.image, (40, 40))
        self.heart_image = pygame.image.load("assets/heart.png")  
        self.heart_image = pygame.transform.scale(self.heart_image, (30, 30))
        
        self.is_attacking = False
        self.attack_timer = 0
        self.attack_image = pygame.image.load("assets/rey_attack.png")
        self.attack_image = pygame.transform.scale(self.attack_image, (50, 50))
        self.attack_range = 50  

        self.direction = "right"

        # 📌 **Ses Efektleri**
        self.attack_sound = pygame.mixer.Sound("assets/attack.wav")
        self.hit_sound = pygame.mixer.Sound("assets/hit.wav")
        self.shoot_sound = pygame.mixer.Sound("assets/shoot.wav")  # 📌 Uzaktan saldırı sesi

        # 📌 **Mermi Listesi**
        self.projectiles = []

    def update(self, walls, enemies):
        """Oyuncunun hareketini ve saldırılarını günceller."""
        keys = pygame.key.get_pressed()
        new_x, new_y = self.x, self.y

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_x -= self.speed
            self.direction = "left"
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_x += self.speed
            self.direction = "right"
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            new_y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_y += self.speed

        if not self.collides(new_x, new_y, walls):
            self.x, self.y = new_x, new_y

        # 📌 Saldırı süresi bittiğinde animasyonu kaldır
        if self.is_attacking:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.is_attacking = False

        # 📌 Mermileri güncelle ve çarpışmaları kontrol et
        for projectile in self.projectiles[:]:
            projectile.update()
            
            if projectile.check_collision(enemies) or projectile.x < 0 or projectile.x > WIDTH:
                self.projectiles.remove(projectile)  # 📌 Mermi çarpınca siliniyor!

    def collides(self, x, y, walls):
        """Oyuncunun duvarlara çarpmasını önler."""
        player_rect = pygame.Rect(x, y, self.width, self.height)
        for wall in walls:
            if player_rect.colliderect(wall):
                return True
        return False

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

        # 📌 Can Barı Çizme
        for i in range(self.health):
            screen.blit(self.heart_image, (10 + i * 35, 10))

        # 📌 Eğer saldırı yapılıyorsa, saldırı animasyonunu ekleyelim
        if self.is_attacking:
            if self.direction == "right":
                screen.blit(self.attack_image, (self.x + self.width, self.y))
            else:
                screen.blit(self.attack_image, (self.x - 50, self.y))

        # 📌 Mermileri ekrana çiz
        for projectile in self.projectiles:
            projectile.draw(screen)

    def attack(self, enemies):
        """Oyuncunun yakın saldırısını gerçekleştirir."""
        self.is_attacking = True
        self.attack_timer = 15  
        self.attack_sound.play()  

        # 📌 Saldırı menzili içindeki düşmanlara vur
        attack_rect = pygame.Rect(
            self.x + (self.width if self.direction == "right" else -self.attack_range),
            self.y,
            self.attack_range,
            self.height
        )

        for enemy in enemies:
            enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
            if attack_rect.colliderect(enemy_rect):
                enemy.take_damage()  

    def shoot(self):
        """Oyuncunun uzaktan ateş etmesini sağlar (X tuşu ile)."""
        self.shoot_sound.play()
        projectile = Projectile(self.x, self.y, self.direction)
        self.projectiles.append(projectile)
        print("🔫 Rey ateş etti!")  # Konsolda test mesajı

    def take_damage(self, amount=1):
        """Oyuncunun canını azaltır. Eğer canı 0'a düşerse ölür."""
        if self.health > 0:
            self.health -= amount
            self.hit_sound.play()  
            print(f"⚠️ Rey darbe aldı! Kalan Can: {self.health}")

        if self.health <= 0:
            self.die()

    def heal(self, amount=1):
        """Oyuncunun canını artırır ancak maksimum can sınırını aşmaz."""
        self.health += amount
        if self.health > self.max_health:
            self.health = self.max_health
        print(f"❤️ Rey iyileşti! Yeni Can: {self.health}")

    def die(self):
        """Oyuncunun ölmesini ve oyun durumunun değişmesini sağlar."""
        global game_state
        print("💀 Game Over! Rey öldü!")
        game_state = "game_over"  
