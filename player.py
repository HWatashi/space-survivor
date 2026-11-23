from math import isclose

import pygame

from settings import (
    PLAYER_BLINK_INTERVAL_SECONDS,
    PLAYER_INVULNERABILITY_SECONDS,
    PLAYER_MAX_HP,
    PLAYER_SIZE,
    PLAYER_SPEED,
)


class Player:
    def __init__(self, center: tuple[int, int]) -> None:
        self.image = pygame.Surface(PLAYER_SIZE, pygame.SRCALPHA)
        pygame.draw.polygon(
            self.image,
            (174, 205, 230),
            [(24, 1), (33, 28), (46, 47), (24, 40), (1, 47), (15, 28)],
        )
        pygame.draw.polygon(
            self.image, (44, 108, 157), [(24, 7), (32, 33), (24, 39), (16, 33)]
        )
        pygame.draw.ellipse(self.image, (104, 233, 248), (20, 18, 8, 12))
        pygame.draw.polygon(
            self.image, (255, 153, 72), [(19, 42), (29, 42), (24, 51)]
        )
        self.rect = self.image.get_rect(center=center)
        self.position = pygame.Vector2(self.rect.topleft)
        self.hp = PLAYER_MAX_HP
        self.invulnerability_remaining = 0.0

    def update(
        self, pressed_scancodes: set[int], dt: float, bounds: pygame.Rect
    ) -> None:
        remaining = self.invulnerability_remaining - dt
        # Treat floating-point residue at the expiry time as zero.
        if isclose(remaining, 0.0, abs_tol=1e-9):
            remaining = 0.0
        self.invulnerability_remaining = max(0.0, remaining)

        left = (
            pygame.KSCAN_A in pressed_scancodes
            or pygame.KSCAN_LEFT in pressed_scancodes
        )
        right = (
            pygame.KSCAN_D in pressed_scancodes
            or pygame.KSCAN_RIGHT in pressed_scancodes
        )
        up = (
            pygame.KSCAN_W in pressed_scancodes
            or pygame.KSCAN_UP in pressed_scancodes
        )
        down = (
            pygame.KSCAN_S in pressed_scancodes
            or pygame.KSCAN_DOWN in pressed_scancodes
        )
        direction = pygame.Vector2(right - left, down - up)

        if direction:
            # Normalizing keeps diagonal and horizontal speeds equal.
            self.position += direction.normalize() * PLAYER_SPEED * dt

        # Clamp the float position to preserve subpixel movement.
        self.position.x = max(
            bounds.left, min(self.position.x, bounds.right - self.rect.width)
        )
        self.position.y = max(
            bounds.top, min(self.position.y, bounds.bottom - self.rect.height)
        )
        self.rect.topleft = round(self.position.x), round(self.position.y)

    def take_damage(self) -> bool:
        if self.hp == 0 or self.invulnerability_remaining > 0:
            return False
        self.hp -= 1
        if self.hp > 0:
            self.invulnerability_remaining = PLAYER_INVULNERABILITY_SECONDS
        return True

    def draw(self, screen: pygame.Surface) -> None:
        if self.invulnerability_remaining > 0:
            elapsed = (
                PLAYER_INVULNERABILITY_SECONDS - self.invulnerability_remaining
            )
            if int(elapsed / PLAYER_BLINK_INTERVAL_SECONDS) % 2 == 0:
                return
        screen.blit(self.image, self.rect)
