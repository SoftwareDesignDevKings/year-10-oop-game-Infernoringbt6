import pygame
import app
import math
from bullet import Bullet

class Player:
    def __init__(self, x, y, assets):
        self.x = x
        self.y = y
        self.speed = app.PLAYER_SPEED
        self.animations = assets["player"]
        self.state = "idle"
        self.frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 8
        self.image = self.animations[self.state][self.frame_index]
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.facing_left = False
        self.health = 5
        self.xp = 0
        self.bullet_speed = 10
        self.bullet_size = 10
        self.bullet_count = 1
        self.shoot_cooldown = 20
        self.shoot_timer = 0
        self.bullets = []
        self.level = 1
        self.shooting_laser = False  # Track if the player is shooting a laser
        self.dash_speed = self.speed * 3
        self.dash_duration = 10  # frames
        self.dash_cooldown = 45  # frames
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.dash_direction = [0, 0]
        self.is_dashing = False

    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        # Handle dash
        if keys[pygame.K_LSHIFT] and self.dash_cooldown_timer <= 0 and not self.is_dashing:
            vel_x = 0
            vel_y = 0
            if keys[pygame.K_LEFT]: vel_x = -1
            if keys[pygame.K_RIGHT]: vel_x = 1
            if keys[pygame.K_UP]: vel_y = -1
            if keys[pygame.K_DOWN]: vel_y = 1
            
            if vel_x != 0 or vel_y != 0:
                self.start_dash(vel_x, vel_y)

        if self.is_dashing:
            self.update_dash()
        else:
            # Normal movement
            vel_x, vel_y = 0, 0
            if keys[pygame.K_LEFT]: vel_x = -self.speed
            if keys[pygame.K_RIGHT]: vel_x = self.speed
            if keys[pygame.K_UP]: vel_y = -self.speed
            if keys[pygame.K_DOWN]: vel_y = self.speed
            
            self.x += vel_x
            self.y += vel_y

        # Clamp player position to screen bounds
        self.x = max(0, min(self.x, app.WIDTH))
        self.y = max(0, min(self.y, app.HEIGHT))
        self.rect.center = (self.x, self.y)

        # Determine animation state
        if vel_x != 0 or vel_y != 0:
            self.state = "run"
        else:
            self.state = "idle"

        # Facing direction
        if vel_x < 0:
            self.facing_left = True
        elif vel_x > 0:
            self.facing_left = False

    def update(self):
        # Update dash cooldown
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= 1

        # Update shoot timer
        self.shoot_timer += 1

        # Update bullets
        for bullet in self.bullets:
            bullet.update()
            if bullet.y < 0 or bullet.y > app.HEIGHT or bullet.x < 0 or bullet.x > app.WIDTH:
                self.bullets.remove(bullet)

        # Update animation
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            frames = self.animations[self.state]
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.image = frames[self.frame_index]
            center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = center

    def draw(self, surface):
        if self.facing_left:
            flipped_img = pygame.transform.flip(self.image, True, False)
            surface.blit(flipped_img, self.rect)
        else:
            surface.blit(self.image, self.rect)

        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(surface)

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)

    def shoot_toward_position(self, tx, ty):
        if self.shoot_timer < self.shoot_cooldown:
            return

        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx**2 + dy**2)

        if dist == 0:
            return

        vx = (dx / dist) * self.bullet_speed
        vy = (dy / dist) * self.bullet_speed

        angle_spread = 10
        base_angle = math.atan2(vy, vx)
        mid = (self.bullet_count - 1) / 2

        for i in range(self.bullet_count):
            offset = i - mid
            spread_radians = math.radians(angle_spread * offset)
            angle = base_angle + spread_radians
            final_vx = math.cos(angle) * self.bullet_speed
            final_vy = math.sin(angle) * self.bullet_speed
            bullet = Bullet(self.x, self.y, final_vx, final_vy, self.bullet_size)
            self.bullets.append(bullet)

        self.shoot_timer = 0

    def shoot_toward_mouse(self, pos):
        mx, my = pos
        self.shoot_toward_position(mx, my)

    def shoot_toward_enemy(self, enemy):
        self.shoot_toward_position(enemy.x, enemy.y)

    def add_xp(self, amount):
        self.xp += amount

    def start_dash(self, dx, dy):
        self.is_dashing = True
        self.dash_timer = self.dash_duration
        self.dash_direction = [dx, dy]
        # Create a motion blur effect
        self.image.set_alpha(180)

    def update_dash(self):
        if self.dash_timer > 0:
            # Move quickly in the dash direction
            self.x += self.dash_direction[0] * self.dash_speed
            self.y += self.dash_direction[1] * self.dash_speed
            self.dash_timer -= 1
            
            # Create afterimage effect
            self.draw_afterimage()
        else:
            self.end_dash()

    def end_dash(self):
        self.is_dashing = False
        self.dash_cooldown_timer = self.dash_cooldown
        self.image.set_alpha(255)

    def draw_afterimage(self):
        # Create a fading copy of the player at their position
        afterimage = self.image.copy()
        afterimage.set_alpha(100)
        surface.blit(afterimage, (self.x - 20, self.y - 20))