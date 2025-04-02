from enemy import Enemy
import math
import random

class Boss(Enemy):
    def __init__(self, x, y, enemy_type, enemy_assets, health=10):
        super().__init__(x, y, enemy_type, enemy_assets)
        self.health = health
        self.size_multiplier = 2.0  # Bosses are bigger
        self.speed *= 0.75  # Slower but tougher
        
        # Scale the boss sprite
        self.image = pygame.transform.scale(
            self.image,
            (int(self.image.get_width() * self.size_multiplier),
             int(self.image.get_height() * self.size_multiplier))
        )
        self.rect = self.image.get_rect(center=(x, y))
        
    def take_damage(self, amount):
        self.health -= amount
        return self.health <= 0
        
    def update(self, player):
        super().update(player)
        # Special attack pattern
        if random.random() < 0.02:  # 2% chance per frame to charge
            self.charge_at_player(player)
            
    def charge_at_player(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist != 0:
            self.x += (dx / dist) * self.speed * 3
            self.y += (dy / dist) * self.speed * 3
            self.rect.center = (self.x, self.y)
