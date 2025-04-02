import pygame

class PowerUp:
    def __init__(self, x, y, power_type):
        self.x = x
        self.y = y
        self.type = power_type
        self.size = 20
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        
        # Different colors for different power-ups
        self.colors = {
            'health': (255, 50, 50),    # Red
            'speed': (50, 255, 50),     # Green
            'damage': (50, 50, 255)     # Blue
        }
        
        self.image.fill(self.colors[power_type])
        self.rect = self.image.get_rect(center=(x, y))
        
    def draw(self, surface):
        surface.blit(self.image, self.rect)
        
    def apply(self, player):
        if self.type == 'health':
            player.health = min(player.health + 1, 5)
        elif self.type == 'speed':
            player.speed *= 1.5  # 50% speed boost
        elif self.type == 'damage':
            player.bullet_size *= 1.2  # 20% damage boost
