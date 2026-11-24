from enum import Enum, auto
from random import randint

import pygame

from enemy import Enemy
from evolution import EvolutionManager
from player import Player
from projectile import Projectile
from settings import (
    BACKGROUND_COLOR,
    ENEMY_SIZE,
    ENEMY_SPAWN_INTERVAL_MS,
    EVOLUTION_NOTICE_COLOR,
    FIRE_COOLDOWN_MS,
    FPS,
    POINTS_PER_ENEMY,
)


class GameState(Enum):
    PLAYING = auto()
    GAME_OVER = auto()


class Game:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.bounds = screen.get_rect()
        self.clock = pygame.time.Clock()
        self.score_font = pygame.font.Font(None, 32)
        self.title_font = pygame.font.Font(None, 72)
        self.pressed_scancodes: set[int] = set()
        self.projectiles: list[Projectile] = []
        self.enemies: list[Enemy] = []
        self.evolution = EvolutionManager()
        self._reset_round()

    def _reset_round(self) -> None:
        self.state = GameState.PLAYING
        self.player = Player(self.bounds.center)
        self.projectiles.clear()
        self.enemies.clear()
        self.pressed_scancodes.clear()
        self.fire_cooldown_ms = 0
        self.enemy_spawn_elapsed_ms = 0
        self.score = 0
        self.evolution.reset()

    def run(self) -> None:
        while True:
            elapsed_ms = self.clock.tick(FPS)
            restarted = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    if self.state is GameState.GAME_OVER:
                        if event.scancode == pygame.KSCAN_R:
                            self._reset_round()
                            restarted = True
                    elif not restarted:
                        self.pressed_scancodes.add(event.scancode)
                elif event.type == pygame.KEYUP:
                    self.pressed_scancodes.discard(event.scancode)
                elif event.type == pygame.WINDOWFOCUSLOST:
                    self.pressed_scancodes.clear()

            if self.state is GameState.PLAYING and not restarted:
                self._update_playing(elapsed_ms)
            self._draw()

    def _update_playing(self, elapsed_ms: int) -> None:
        dt = elapsed_ms / 1000
        self.evolution.update(dt)
        self.player.update(self.pressed_scancodes, dt, self.bounds)

        self._update_enemies(dt, elapsed_ms)
        for projectile in self.projectiles:
            projectile.update(dt)

        self.fire_cooldown_ms = max(0, self.fire_cooldown_ms - elapsed_ms)
        if (
            pygame.KSCAN_SPACE in self.pressed_scancodes
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
        self._resolve_player_collisions()

    def _draw(self) -> None:
        self.screen.fill(BACKGROUND_COLOR)
        for projectile in self.projectiles:
            projectile.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        self.player.draw(self.screen)

        color = (230, 238, 252)
        score_image = self.score_font.render(
            f"Score: {self.score}", True, color
        )
        self.screen.blit(score_image, (16, 16))
        hp_image = self.score_font.render(f"HP: {self.player.hp}", True, color)
        hp_rect = hp_image.get_rect(topright=(self.bounds.right - 16, 16))
        self.screen.blit(hp_image, hp_rect)
        minutes, seconds = divmod(self.evolution.whole_seconds, 60)
        time_image = self.score_font.render(
            f"Time: {minutes:02d}:{seconds:02d}", True, color
        )
        time_rect = time_image.get_rect(midtop=(self.bounds.centerx, 16))
        self.screen.blit(time_image, time_rect)
        if self.evolution.notice_remaining > 0:
            level = ("I", "II")[self.evolution.max_level - 1]
            notice = self.score_font.render(
                f"KAMIKAZE {level} UNLOCKED", True, EVOLUTION_NOTICE_COLOR
            )
            notice_rect = notice.get_rect(
                midtop=(self.bounds.centerx, time_rect.bottom + 8)
            )
            self.screen.blit(notice, notice_rect)

        if self.state is GameState.GAME_OVER:
            self._draw_game_over()
        pygame.display.flip()

    def _draw_game_over(self) -> None:
        panel = pygame.Rect(0, 0, 420, 200)
        panel.center = self.bounds.center
        pygame.draw.rect(self.screen, (22, 30, 51), panel, border_radius=12)
        for text, font, offset_y in (
            ("Game Over", self.title_font, -50),
            (f"Final score: {self.score}", self.score_font, 10),
            ("Press R to restart", self.score_font, 57),
        ):
            image = font.render(text, True, (230, 238, 252))
            center = panel.centerx, panel.centery + offset_y
            self.screen.blit(image, image.get_rect(center=center))

    def _update_enemies(self, dt: float, elapsed_ms: int) -> None:
        for enemy in self.enemies:
            enemy.try_dodge(self.projectiles, self.bounds)
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
            # The remaining accumulator is the age of this scheduled spawn.
            level = self.evolution.choose_enemy_level(
                seconds_since_spawn=self.enemy_spawn_elapsed_ms / 1000
            )
            self.enemies.append(Enemy(left, self.bounds.top, level))

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

    def _resolve_player_collisions(self) -> None:
        surviving_enemies: list[Enemy] = []
        for enemy in self.enemies:
            if (
                self.player.rect.colliderect(enemy.rect)
                and self.player.take_damage()
            ):
                continue
            surviving_enemies.append(enemy)
        self.enemies = surviving_enemies
        if self.player.hp == 0:
            self.state = GameState.GAME_OVER
