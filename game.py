import pygame
import random
import os

import app
from player import Player
from enemy import Enemy
from coin import Coin

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((app.WIDTH, app.HEIGHT))
        pygame.display.set_caption("Shooter")
        self.clock = pygame.time.Clock()

        self.assets = app.load_assets()

        font_path = os.path.join("assets", "PressStart2P.ttf")
        self.font_small = pygame.font.Font(font_path, 10)
        self.font_large = pygame.font.Font(font_path, 32)

        self.background = self.create_random_background(
            app.WIDTH, app.HEIGHT, self.assets["floor_tiles"]
        )

        self.running = True
        self.game_over = False

        self.enemies = []
        self.enemy_spawn_timer = 0
        self.enemy_spawn_interval = 60
        self.enemies_per_spawn = 1

        self.coins = []

        self.reset_game()
        self.in_level_up_menu = False
        self.upgrade_options = []

        self.time_freeze_active = False
        self.time_freeze_timer = 0
        self.time_freeze_cooldown = 0  # Cooldown timer for time freeze
        self.time_freeze_color = (0, 255, 255, 50)  # Light cyan with transparency

        self.shield_active = False
        self.shield_timer = 0
        self.shield_cooldown = 0  # Cooldown timer for the shield

        self.boss_spawn_level = 5  # Spawn boss every 5 levels
        self.combo_count = 0
        self.combo_timer = 0
        self.max_combo_timer = app.FPS * 3  # 3 seconds to maintain combo
        self.power_ups = []
        self.power_up_spawn_timer = 0
        self.power_up_spawn_interval = app.FPS * 15  # Spawn power-up every 15 seconds

    def reset_game(self):
        self.player = Player(app.WIDTH // 2, app.HEIGHT // 2, self.assets)
        self.enemies = []
        self.enemy_spawn_timer = 0
        self.enemies_per_spawn = 1

        self.coins = []
        self.game_over = False

    def create_random_background(self, width, height, floor_files):
        bg = pygame.Surface((width, height))
        tile_w = floor_files[0].get_width()
        tile_h = floor_files[0].get_height()

        for y in range(0, height, tile_h):
            for x in range(0, width, tile_w):
                tile = random.choice(floor_files)
                bg.blit(tile, (x, y))

        return bg

    def run(self):
        while self.running:
            self.clock.tick(app.FPS)
            self.handle_events()

            if not self.game_over:
                if not self.in_level_up_menu:
                    self.update()
                self.draw()

        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.game_over:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                elif self.in_level_up_menu:
                    # Handle upgrade selection
                    if event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                        index = event.key - pygame.K_1  # 0, 1, 2
                        if 0 <= index < len(self.upgrade_options):
                            upgrade = self.upgrade_options[index]
                            self.apply_upgrade(self.player, upgrade)
                            self.in_level_up_menu = False
                else:
                    # Normal gameplay
                    if event.key == pygame.K_SPACE:
                        nearest_enemy = self.find_nearest_enemy()
                        if nearest_enemy:
                            self.player.shoot_toward_enemy(nearest_enemy)
                    if event.key == pygame.K_t:  # Activate time freeze
                        self.activate_time_freeze()
                    if event.key == pygame.K_s:  # Activate shield
                        self.activate_shield()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    self.player.shoot_toward_mouse(event.pos)

    def activate_time_freeze(self):
        if not self.time_freeze_active and self.time_freeze_cooldown <= 0:
            self.time_freeze_active = True
            self.time_freeze_timer = app.FPS * 5  # Freeze for 5 seconds
            self.time_freeze_cooldown = app.FPS * 30  # Cooldown for 30 seconds

    def activate_shield(self):
        if not self.shield_active and self.shield_cooldown <= 0:
            self.shield_active = True
            self.shield_timer = app.FPS * 5  # Shield lasts for 5 seconds
            self.shield_cooldown = app.FPS * 20  # Cooldown for 20 seconds

    def update(self):
        try:
            # Handle shield logic
            if self.shield_active:
                self.shield_timer -= 1
                if self.shield_timer <= 0:
                    self.shield_active = False
                    self.shield_timer = 0

            # Handle time freeze logic
            if self.time_freeze_active:
                self.time_freeze_timer -= 1
                if self.time_freeze_timer <= 0:
                    self.time_freeze_active = False

            # Handle cooldowns
            if self.time_freeze_cooldown > 0:
                self.time_freeze_cooldown -= 1
            if self.shield_cooldown > 0:
                self.shield_cooldown -= 1

            # Update enemy positions only if not frozen
            if not self.time_freeze_active:
                for enemy in list(self.enemies):  # Create a copy of the list for iteration
                    try:
                        enemy.update(self.player)
                    except Exception as e:
                        print(f"Enemy update error: {e}")
                        if enemy in self.enemies:
                            self.enemies.remove(enemy)

            # Update player and game state
            self.player.handle_input()
            self.player.update()

            self.check_player_enemy_collisions()
            self.check_bullet_enemy_collisions()
            self.check_player_coin_collisions()

            if self.player.health <= 0:
                self.game_over = True
                return

            self.spawn_enemies()
            self.check_for_level_up()

        except Exception as e:
            print(f"Update error: {e}")

    def draw(self):
        self.screen.blit(self.background, (0, 0))

        # Draw time freeze effect
        if self.time_freeze_active:
            freeze_overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
            freeze_overlay.fill(self.time_freeze_color)
            self.screen.blit(freeze_overlay, (0, 0))

        for coin in self.coins:
            coin.draw(self.screen)

        if not self.game_over and not self.in_level_up_menu:
            if self.shield_active:
                self.draw_shield()  # Draw the shield around the player
            self.player.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        hp = max(0, min(self.player.health, 5))
        health_img = self.assets["health"][hp]
        self.screen.blit(health_img, (10, 10))

        vp_text_surf = self.font_small.render(f"VP: {self.player.xp}", True, (255, 255, 255))
        self.screen.blit(vp_text_surf, (10, 70))

        next_level_xp = self.player.level * self.player.level * 5
        xp_to_next = max(0, next_level_xp - self.player.xp)
        xp_next_surf = self.font_small.render(f"Next Lvl XP: {xp_to_next}", True, (255, 255, 255))
        self.screen.blit(xp_next_surf, (10, 100))

        if self.in_level_up_menu:
            self.draw_upgrade_menu()

        if self.game_over:
            self.draw_game_over_screen()

        if self.time_freeze_active:
            freeze_text = self.font_small.render("Time Freeze Active!", True, (0, 255, 255))
            self.screen.blit(freeze_text, (app.WIDTH // 2 - 80, 10))
        elif self.time_freeze_cooldown > 0:
            cooldown_seconds = self.time_freeze_cooldown // app.FPS
            cooldown_text = self.font_small.render(f"Time Freeze Cooldown: {cooldown_seconds}s", True, (255, 0, 0))
            self.screen.blit(cooldown_text, (app.WIDTH // 2 - 100, 10))
        else:
            ready_text = self.font_small.render("Time Freeze Ready!", True, (0, 255, 0))
            self.screen.blit(ready_text, (app.WIDTH // 2 - 80, 10))

        if self.shield_active:
            shield_text = self.font_small.render("Shield Active!", True, (0, 255, 255))
            self.screen.blit(shield_text, (app.WIDTH // 2 - 80, 30))
        elif self.shield_cooldown > 0:
            cooldown_seconds = self.shield_cooldown // app.FPS
            cooldown_text = self.font_small.render(f"Shield Cooldown: {cooldown_seconds}s", True, (255, 0, 0))
            self.screen.blit(cooldown_text, (app.WIDTH // 2 - 100, 30))
        else:
            ready_text = self.font_small.render("Shield Ready!", True, (0, 255, 0))
            self.screen.blit(ready_text, (app.WIDTH // 2 - 80, 30))

        # Draw dash cooldown
        if self.player.dash_cooldown_timer > 0:
            cooldown_text = self.font_small.render(f"Dash Cooldown: {self.player.dash_cooldown_timer//3}s", True, (255, 0, 0))
            self.screen.blit(cooldown_text, (app.WIDTH // 2 - 80, 70))
        else:
            ready_text = self.font_small.render("Dash Ready!", True, (0, 255, 0))
            self.screen.blit(ready_text, (app.WIDTH // 2 - 80, 70))

        pygame.display.flip()

    def draw_shield(self):
        """Draw a blue shield around the player."""
        shield_surface = pygame.Surface((self.player.rect.width * 2, self.player.rect.height * 2), pygame.SRCALPHA)
        pygame.draw.circle(shield_surface, (0, 0, 255, 100), (self.player.rect.width, self.player.rect.height), self.player.rect.width)
        self.screen.blit(shield_surface, (self.player.rect.centerx - self.player.rect.width, self.player.rect.centery - self.player.rect.height))

    def spawn_enemies(self):
        self.enemy_spawn_timer += 1
        if self.enemy_spawn_timer >= self.enemy_spawn_interval:
            self.enemy_spawn_timer = 0

            for _ in range(self.enemies_per_spawn):
                side = random.choice(['top', 'bottom', 'left', 'right'])
                if side == "top":
                    x = random.randint(0, app.WIDTH)
                    y = -app.SPAWN_MARGIN
                elif side == "bottom":
                    x = random.randint(0, app.WIDTH)
                    y = app.HEIGHT + app.SPAWN_MARGIN
                elif side == "left":
                    x = -app.SPAWN_MARGIN
                    y = random.randint(0, app.HEIGHT)
                else:
                    x = app.WIDTH + app.SPAWN_MARGIN
                    y = random.randint(0, app.HEIGHT)

                enemy_type = random.choice(list(self.assets["enemies"].keys()))
                enemy = Enemy(x, y, enemy_type, self.assets["enemies"])
                self.enemies.append(enemy)

    def check_player_enemy_collisions(self):
        if self.shield_active:
            return  # Block all damage while the shield is active

        collided = False
        for enemy in self.enemies:
            if enemy.rect.colliderect(self.player.rect):
                collided = True
                break

        if collided:
            self.player.take_damage(1)
            px, py = self.player.x, self.player.y
            for enemy in self.enemies:
                enemy.set_knockback(px, py, app.PUSHBACK_DISTANCE)

    def draw_game_over_screen(self):
        # Overlay
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))

        # Game Over Text
        game_over_surf = self.font_large.render("GAME OVER!", True, (255, 0, 0))
        game_over_rect = game_over_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 50))
        self.screen.blit(game_over_surf, game_over_rect)

        # Prompt to restart or quit
        prompt_surf = self.font_small.render("Press R to Play Again or ESC to Quit", True, (255, 255, 255))
        prompt_rect = prompt_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 + 20))
        self.screen.blit(prompt_surf, prompt_rect)

    def find_nearest_enemy(self):
        if not self.enemies:
            return None

        nearest = None
        min_dist = float('inf')
        px, py = self.player.x, self.player.y

        for enemy in self.enemies:
            dist = ((enemy.x - px) ** 2 + (enemy.y - py) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                nearest = enemy

        return nearest

    def check_bullet_enemy_collisions(self):
        try:
            bullets_to_remove = []
            coins_to_add = []

            # First, gather all collisions
            for bullet in self.player.bullets:
                if not hasattr(bullet, 'rect'):
                    bullets_to_remove.append(bullet)
                    continue

                for enemy in self.enemies:
                    if not hasattr(enemy, 'rect'):
                        continue

                    if bullet.rect.colliderect(enemy.rect):
                        bullets_to_remove.append(bullet)
                        # Deal damage instead of instant kill
                        if enemy.take_damage(1):  # Returns True if enemy dies
                            self.enemies.remove(enemy)
                            coins_to_add.append((enemy.x, enemy.y))
                            self.combo_count += 1
                            self.combo_timer = self.max_combo_timer
                            bonus_xp = min(self.combo_count - 1, 3)  # Reduced max bonus XP
                        break

            # Remove used bullets
            for bullet in bullets_to_remove:
                if bullet in self.player.bullets:
                    self.player.bullets.remove(bullet)

            # Add coins for defeated enemies
            for x, y in coins_to_add:
                self.coins.append(Coin(x, y))

        except Exception as e:
            print(f"Collision error: {e}")

    def check_player_coin_collisions(self):
        coins_collected = []
        for coin in self.coins:
            if coin.rect.colliderect(self.player.rect):
                coins_collected.append(coin)
                self.player.add_xp(1)

        for c in coins_collected:
            if c in self.coins:
                self.coins.remove(c)

    def pick_random_upgrades(self, num):
        possible_upgrades = [
            {"name": "Bigger Bullet",  "desc": "Bullet size +5"},
            {"name": "Faster Bullet",  "desc": "Bullet speed +2"},
            {"name": "Extra Bullet",   "desc": "Fire additional bullet"},
            {"name": "Shorter Cooldown", "desc": "Shoot more frequently"},
        ]
        return random.sample(possible_upgrades, k=num)

    def apply_upgrade(self, player, upgrade):
        try:
            name = upgrade["name"]
            if name == "Bigger Bullet":
                player.bullet_size = min(player.bullet_size + 5, 50)  # Cap bullet size
            elif name == "Faster Bullet":
                player.bullet_speed = min(player.bullet_speed + 2, 20)  # Cap bullet speed
            elif name == "Extra Bullet":
                player.bullet_count = min(player.bullet_count + 1, 5)  # Cap bullet count
            elif name == "Shorter Cooldown":
                player.shoot_cooldown = max(5, int(player.shoot_cooldown * 0.8))  # Minimum cooldown
        except Exception as e:
            print(f"Upgrade error: {e}")

    def draw_upgrade_menu(self):
        # Dark overlay behind the menu
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Title
        title_surf = self.font_large.render("Choose an Upgrade!", True, (255, 255, 0))
        title_rect = title_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 3 - 50))
        self.screen.blit(title_surf, title_rect)

        # Options
        for i, upgrade in enumerate(self.upgrade_options):
            text_str = f"{i+1}. {upgrade['name']} - {upgrade['desc']}"
            option_surf = self.font_small.render(text_str, True, (255, 255, 255))
            line_y = app.HEIGHT // 3 + i * 40
            option_rect = option_surf.get_rect(center=(app.WIDTH // 2, line_y))
            self.screen.blit(option_surf, option_rect)

    def check_for_level_up(self):
        # Make leveling much slower
        xp_needed = self.player.level * self.player.level * 15  # Increased from 5 to 15
        if self.player.xp >= xp_needed:
            self.player.level += 1
            self.in_level_up_menu = True
            self.upgrade_options = self.pick_random_upgrades(3)
            
            if self.player.level % self.boss_spawn_level == 0:
                self.spawn_boss()
            
            # Slower enemy spawn increase
            if self.player.level % 2 == 0:  # Only increase every 2 levels
                self.enemies_per_spawn += 1

    def spawn_boss(self):
        x = app.WIDTH // 2
        y = -50
        boss = Boss(x, y, "demon", self.assets["enemies"], health=10)
        self.enemies.append(boss)

    def update_combo_timer(self):
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer <= 0:
                self.combo_count = 0

    def update_power_ups(self):
        self.power_up_spawn_timer += 1
        if self.power_up_spawn_timer >= self.power_up_spawn_interval:
            self.power_up_spawn_timer = 0
            self.spawn_power_up()

    def spawn_power_up(self):
        power_up_type = random.choice(['health', 'speed', 'damage'])
        x = random.randint(50, app.WIDTH - 50)
        y = random.randint(50, app.HEIGHT - 50)
        self.power_ups.append(PowerUp(x, y, power_up_type))