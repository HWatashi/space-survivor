import pygame

from settings import (
    ENEMY_COCKPIT_COLOR,
    ENEMY_COLOR,
    ENEMY_SIZE,
    ENEMY_SPEED,
    KAMIKAZE_I_COLOR,
    KAMIKAZE_I_ENGINE_COLOR,
    KAMIKAZE_I_ENGINE_SIZE,
    KAMIKAZE_I_SPEED_MULTIPLIER,
)


class Enemy:
    def __init__(
        self, left: int, bottom: int, evolution_level: int = 0
    ) -> None:
        self.rect = pygame.Rect((0, 0), ENEMY_SIZE)
        self.rect.bottomleft = left, bottom
        self.y = float(self.rect.y)
        self.evolution_level = evolution_level
        self.speed = ENEMY_SPEED
        if self.evolution_level == 1:
            self.speed *= KAMIKAZE_I_SPEED_MULTIPLIER

    def update(self, dt: float) -> None:
        self.y += self.speed * dt
        self.rect.y = round(self.y)

    def draw(self, screen: pygame.Surface) -> None:
        rect = self.rect
        color = KAMIKAZE_I_COLOR if self.evolution_level == 1 else ENEMY_COLOR
        pygame.draw.polygon(
            screen,
            color,
            [
                rect.topleft,
                (rect.centerx, rect.top + rect.height // 4),
                (rect.right - 1, rect.top),
                (rect.right - 1, rect.centery),
                (rect.centerx, rect.bottom - 1),
                rect.midleft,
            ],
        )
        if self.evolution_level == 1:
            engine = pygame.Rect((0, 0), KAMIKAZE_I_ENGINE_SIZE)
            engine.midtop = rect.midtop
            pygame.draw.rect(screen, KAMIKAZE_I_ENGINE_COLOR, engine)
        cockpit = rect.inflate(-(rect.width * 3 // 4), -(rect.height * 2 // 3))
        pygame.draw.ellipse(screen, ENEMY_COCKPIT_COLOR, cockpit)
