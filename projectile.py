import pygame

from settings import PROJECTILE_COLOR, PROJECTILE_SIZE, PROJECTILE_SPEED


class Projectile:
    def __init__(self, origin: tuple[int, int]) -> None:
        self.rect = pygame.Rect((0, 0), PROJECTILE_SIZE)
        self.rect.midbottom = origin
        self.y = float(self.rect.y)

    def update(self, dt: float) -> None:
        self.y -= PROJECTILE_SPEED * dt
        self.rect.y = round(self.y)

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, PROJECTILE_COLOR, self.rect, border_radius=2)
