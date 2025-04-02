import pygame
import app
import math

class Enemy:
    def __init__(self, x, y, enemy_type, enemy_assets, speed=app.DEFAULT_ENEMY_SPEED):
        # Initialize enemy properties
        self.x = x
        self.y = y
        self.speed = speed
        self.frames = enemy_assets[enemy_type]  # Load animation frames
        self.frame_index = 0  # Current frame index
        self.animation_timer = 0  # Timer for animation
        self.animation_speed = 8  # Speed of animation
        self.image = self.frames[self.frame_index]  # Current image
        self.rect = self.image.get_rect(center=(self.x, self.y))  # Enemy's rectangle
        self.enemy_type = enemy_type  # Type of enemy
        self.facing_left = False  # Direction the enemy is facing

        # Knockback properties
        self.knockback_dx = 0  # Knockback direction (x)
        self.knockback_dy = 0  # Knockback direction (y)
        self.knockback_dist_remaining = 0  # Remaining knockback distance

        # Evolution properties
        self.evolution_level = 0
        self.time_alive = 0
        self.evolve_threshold = app.FPS * 10  # Evolve every 10 seconds
        self.size_multiplier = 1.0
        self.original_speed = speed

        # Health properties
        self.max_health = 3  # Base health for all enemies
        self.health = self.max_health

    def update(self, player):
        try:
            self.time_alive += 1
            if self.time_alive >= self.evolve_threshold:
                self.evolve()

            self.apply_knockback()

            if self.knockback_dist_remaining <= 0:
                self.move_toward_player(player)

            self.animate()
        except Exception as e:
            print(f"Enemy update error: {e}")
            return False

    def move_toward_player(self, player):
        try:
            dx = player.x - self.x
            dy = player.y - self.y
            dist = max((dx**2 + dy**2) ** 0.5, 0.1)  # Prevent division by zero

            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
            self.facing_left = dx < 0
            self.rect.center = (self.x, self.y)
        except Exception as e:
            print(f"Move error: {e}")

    def apply_knockback(self):
        # Apply knockback effect to enemy position
        if self.knockback_dist_remaining > 0:
            step = min(app.ENEMY_KNOCKBACK_SPEED, self.knockback_dist_remaining)
            self.x += self.knockback_dx * step
            self.y += self.knockback_dy * step
            self.knockback_dist_remaining -= step

            # Update enemy position
            self.rect.center = (self.x, self.y)

    def animate(self):
        # Animate the enemy
        self.animation_timer += 1

        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)  # Loop frames
            center = self.rect.center  # Save current center
            self.image = self.frames[self.frame_index]  # Update image
            self.rect = self.image.get_rect()  # Update rectangle
            self.rect.center = center  # Restore center

    def evolve(self):
        try:
            self.evolution_level += 1
            self.time_alive = 0
            
            # Increase health with evolution
            self.max_health += 2
            self.health = self.max_health
            
            # Limit size increase to prevent massive enemies
            max_size_multiplier = 2.5
            self.size_multiplier = min(self.size_multiplier + 0.2, max_size_multiplier)
            
            # Save center position
            center = self.rect.center
            
            # Create scaled image with error handling
            try:
                new_width = int(self.frames[0].get_width() * self.size_multiplier)
                new_height = int(self.frames[0].get_height() * self.size_multiplier)
                
                # Ensure minimum size
                new_width = max(10, new_width)
                new_height = max(10, new_height)
                
                self.image = pygame.transform.scale(
                    self.frames[self.frame_index],
                    (new_width, new_height)
                )
            except Exception:
                # Fallback to original image if scaling fails
                self.image = self.frames[self.frame_index]
            
            self.rect = self.image.get_rect(center=center)
            
            # Cap speed increase
            max_speed = self.original_speed * 3
            self.speed = min(self.original_speed * (1 + self.evolution_level * 0.15), max_speed)
            
            # Add color tint
            if self.image.get_size()[0] > 0 and self.image.get_size()[1] > 0:
                tint_surface = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
                if self.evolution_level == 1:
                    tint_surface.fill((255, 0, 0, 100))
                elif self.evolution_level == 2:
                    tint_surface.fill((128, 0, 128, 100))
                else:
                    tint_surface.fill((255, 215, 0, 100))
                
                self.image.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        except Exception as e:
            print(f"Evolution error: {e}")
            # Reset to safe state
            self.speed = self.original_speed
            self.image = self.frames[0]
            self.rect = self.image.get_rect(center=center)

    def draw(self, surface):
        # Draw the enemy on the screen
        if self.facing_left:
            flipped_image = pygame.transform.flip(self.image, True, False)  # Flip image
            surface.blit(flipped_image, self.rect)
        else:
            surface.blit(self.image, self.rect)

        # Add evolution level indicator
        if self.evolution_level > 0:
            star_color = (255, 255, 0)  # Yellow
            for i in range(self.evolution_level):
                x = self.rect.right - 5 - (i * 8)
                y = self.rect.top - 5
                pygame.draw.circle(surface, star_color, (x, y), 3)

        # Draw health bar
        health_ratio = self.health / self.max_health
        bar_width = self.rect.width
        bar_height = 4
        bar_pos = (self.rect.x, self.rect.y - 8)
        
        # Background (red)
        pygame.draw.rect(surface, (255, 0, 0), (*bar_pos, bar_width, bar_height))
        # Foreground (green)
        pygame.draw.rect(surface, (0, 255, 0), 
                        (*bar_pos, bar_width * health_ratio, bar_height))

    def set_knockback(self, px, py, dist):
        # Set knockback direction and distance
        dx = self.x - px
        dy = self.y - py
        length = math.sqrt(dx * dx + dy * dy)  # Calculate length of vector

        if length > 0:
            self.knockback_dx = dx / length  # Normalize x direction
            self.knockback_dy = dy / length  # Normalize y direction
            self.knockback_dist_remaining = dist  # Set knockback distance

    def take_damage(self, damage):
        self.health -= damage
        return self.health <= 0