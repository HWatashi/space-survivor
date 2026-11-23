import pygame

from player import Player
from projectile import Projectile
from settings import BACKGROUND_COLOR, FIRE_COOLDOWN_MS, FPS


class Game:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.bounds = screen.get_rect()
        self.clock = pygame.time.Clock()
        self.player = Player(self.bounds.center)
        self.projectiles: list[Projectile] = []
        self.fire_cooldown_ms = 0

    def run(self) -> None:
        while True:
            elapsed_ms = self.clock.tick(FPS)
            dt = elapsed_ms / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return

            keys = pygame.key.get_pressed()
            self.player.update(keys, dt, self.bounds)

            for projectile in self.projectiles:
                projectile.update(dt)
            self.projectiles = [
                projectile
                for projectile in self.projectiles
                if projectile.rect.colliderect(self.bounds)
            ]

            self.fire_cooldown_ms = max(0, self.fire_cooldown_ms - elapsed_ms)
            if keys[pygame.K_SPACE] and self.fire_cooldown_ms == 0:
                projectile = Projectile(self.player.rect.midtop)
                if projectile.rect.colliderect(self.bounds):
                    self.projectiles.append(projectile)
                self.fire_cooldown_ms = FIRE_COOLDOWN_MS

            self.screen.fill(BACKGROUND_COLOR)
            for projectile in self.projectiles:
                projectile.draw(self.screen)
            self.player.draw(self.screen)
            pygame.display.flip()
