import pygame

from settings import ENEMY_COCKPIT_COLOR, ENEMY_COLOR, ENEMY_SIZE, ENEMY_SPEED


class Enemy:
    def __init__(self, left: int, bottom: int) -> None:
        self.rect = pygame.Rect((0, 0), ENEMY_SIZE)
        self.rect.bottomleft = left, bottom
        self.y = float(self.rect.y)

    def update(self, dt: float) -> None:
        self.y += ENEMY_SPEED * dt
        self.rect.y = round(self.y)

    def draw(self, screen: pygame.Surface) -> None:
        rect = self.rect
        pygame.draw.polygon(
            screen,
            ENEMY_COLOR,
            [
                rect.topleft,
                (rect.centerx, rect.top + rect.height // 4),
                (rect.right - 1, rect.top),
                (rect.right - 1, rect.centery),
                (rect.centerx, rect.bottom - 1),
                rect.midleft,
            ],
        )
        cockpit = rect.inflate(-(rect.width * 3 // 4), -(rect.height * 2 // 3))
        pygame.draw.ellipse(screen, ENEMY_COCKPIT_COLOR, cockpit)
