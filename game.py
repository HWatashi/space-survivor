from random import randint

import pygame

from enemy import Enemy
from player import Player
from projectile import Projectile
from settings import (
    BACKGROUND_COLOR,
    ENEMY_SIZE,
    ENEMY_SPAWN_INTERVAL_MS,
    FIRE_COOLDOWN_MS,
    FPS,
    POINTS_PER_ENEMY,
)


class Game:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.bounds = screen.get_rect()
        self.clock = pygame.time.Clock()
        self.player = Player(self.bounds.center)
        self.projectiles: list[Projectile] = []
        self.fire_cooldown_ms = 0
        self.enemies: list[Enemy] = []
        self.enemy_spawn_elapsed_ms = 0
        self.score = 0
        self.score_font = pygame.font.Font(None, 32)

    def run(self) -> None:
        pressed_scancodes: set[int] = set()
        while True:
            elapsed_ms = self.clock.tick(FPS)
            dt = elapsed_ms / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    pressed_scancodes.add(event.scancode)
                elif event.type == pygame.KEYUP:
                    pressed_scancodes.discard(event.scancode)
                elif event.type == pygame.WINDOWFOCUSLOST:
                    pressed_scancodes.clear()

            self.player.update(pressed_scancodes, dt, self.bounds)

            for projectile in self.projectiles:
                projectile.update(dt)

            self._update_enemies(dt, elapsed_ms)
            self.fire_cooldown_ms = max(0, self.fire_cooldown_ms - elapsed_ms)
            if (
                pygame.KSCAN_SPACE in pressed_scancodes
                and self.fire_cooldown_ms == 0
            ):
                projectile = Projectile(self.player.rect.midtop)
                if projectile.rect.colliderect(self.bounds):
                    self.projectiles.append(projectile)
                self.fire_cooldown_ms = FIRE_COOLDOWN_MS

            self._resolve_hits()
            self.projectiles = [
                projectile
                for projectile in self.projectiles
                if projectile.rect.colliderect(self.bounds)
            ]

            self.screen.fill(BACKGROUND_COLOR)
            for projectile in self.projectiles:
                projectile.draw(self.screen)
            for enemy in self.enemies:
                enemy.draw(self.screen)
            self.player.draw(self.screen)
            score_image = self.score_font.render(
                f"Score: {self.score}", True, (230, 238, 252)
            )
            self.screen.blit(score_image, (16, 16))
            pygame.display.flip()

    def _update_enemies(self, dt: float, elapsed_ms: int) -> None:
        for enemy in self.enemies:
            enemy.update(dt)
        # Enemies start above the window and are removed only below it.
        self.enemies = [
            enemy for enemy in self.enemies
            if enemy.rect.top < self.bounds.bottom
        ]

        self.enemy_spawn_elapsed_ms += elapsed_ms
        while self.enemy_spawn_elapsed_ms >= ENEMY_SPAWN_INTERVAL_MS:
            self.enemy_spawn_elapsed_ms -= ENEMY_SPAWN_INTERVAL_MS
            left = randint(self.bounds.left, self.bounds.right - ENEMY_SIZE[0])
            self.enemies.append(Enemy(left, self.bounds.top))

    def _resolve_hits(self) -> None:
        surviving_projectiles: list[Projectile] = []
        for projectile in self.projectiles:
            for index, enemy in enumerate(self.enemies):
                if projectile.rect.colliderect(enemy.rect):
                    self.enemies.pop(index)
                    self.score += POINTS_PER_ENEMY
                    break
            else:
                surviving_projectiles.append(projectile)
        self.projectiles = surviving_projectiles
