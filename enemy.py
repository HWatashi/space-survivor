from collections.abc import Iterable
from enum import Enum, auto
from math import isclose

import pygame

from projectile import Projectile
from settings import (
    ENEMY_COCKPIT_COLOR,
    ENEMY_COLOR,
    ENEMY_SIZE,
    ENEMY_SPEED,
    KAMIKAZE_I_COLOR,
    KAMIKAZE_I_ENGINE_COLOR,
    KAMIKAZE_I_ENGINE_SIZE,
    KAMIKAZE_I_SPEED_MULTIPLIER,
    KAMIKAZE_II_COLOR,
    KAMIKAZE_II_DETECTION_DISTANCE,
    KAMIKAZE_II_DODGE_DISTANCE,
    KAMIKAZE_II_DODGE_SECONDS,
    KAMIKAZE_II_READY_COLOR,
    KAMIKAZE_II_READY_RADIUS,
    KAMIKAZE_II_WING_COLOR,
    KAMIKAZE_II_WING_SIZE,
)


class DodgeState(Enum):
    READY = auto()
    DODGING = auto()
    EXHAUSTED = auto()


class Enemy:
    def __init__(
        self, left: int, bottom: int, evolution_level: int = 0
    ) -> None:
        self.rect = pygame.Rect((0, 0), ENEMY_SIZE)
        self.rect.bottomleft = left, bottom
        self.y = float(self.rect.y)
        self.evolution_level = evolution_level
        self.speed = ENEMY_SPEED
        if self.evolution_level > 0:
            self.speed *= KAMIKAZE_I_SPEED_MULTIPLIER
        self.dodge_state = DodgeState.READY if evolution_level == 2 else None
        self._dodge_start = float(left)
        self._dodge_target = float(left)
        self._dodge_elapsed = 0.0

    def try_dodge(
        self, projectiles: Iterable[Projectile], bounds: pygame.Rect
    ) -> None:
        if self.dodge_state is not DodgeState.READY:
            return

        # Projectiles move straight up. Only shots below the hull can approach.
        nearby = [
            shot.rect
            for shot in projectiles
            if (
                0 <= shot.rect.top - self.rect.bottom
                <= KAMIKAZE_II_DETECTION_DISTANCE
            )
        ]
        width = self.rect.width
        left = self.rect.left
        if not any(
            shot.left < self.rect.right and shot.right > left
            for shot in nearby
        ):
            return

        min_x = max(bounds.left, left - KAMIKAZE_II_DODGE_DISTANCE)
        max_x = min(bounds.right - width, left + KAMIKAZE_II_DODGE_DISTANCE)
        candidates = [min_x, max_x]
        # A short dodge can fit between lanes that block both full dodges.
        for shot in nearby:
            candidates.extend((shot.left - width, shot.right))

        best_clearance = -1.0
        for target in candidates:
            if not min_x <= target <= max_x or target == left:
                continue
            # Negative clearance means a projectile overlaps the landing lane.
            clearance = min(
                max(target - shot.right, shot.left - (target + width))
                for shot in nearby
            )
            if clearance >= 0 and clearance > best_clearance:
                best_clearance = clearance
                self._dodge_target = target

        if best_clearance >= 0:
            self._dodge_start = float(left)
            self._dodge_elapsed = 0.0
            self.dodge_state = DodgeState.DODGING

    def update(self, dt: float) -> None:
        self.y += self.speed * dt
        self.rect.y = round(self.y)
        if self.dodge_state is DodgeState.DODGING:
            self._dodge_elapsed += dt
            duration = KAMIKAZE_II_DODGE_SECONDS
            if self._dodge_elapsed >= duration or isclose(
                self._dodge_elapsed, duration
            ):
                self.rect.x = round(self._dodge_target)
                self.dodge_state = DodgeState.EXHAUSTED
            else:
                progress = self._dodge_elapsed / duration
                distance = self._dodge_target - self._dodge_start
                self.rect.x = round(self._dodge_start + distance * progress)

    def draw(self, screen: pygame.Surface) -> None:
        rect = self.rect
        color = (ENEMY_COLOR, KAMIKAZE_I_COLOR, KAMIKAZE_II_COLOR)[
            self.evolution_level
        ]
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
        elif self.evolution_level == 2:
            wing = pygame.Rect((0, 0), KAMIKAZE_II_WING_SIZE)
            wing.midleft = rect.left, rect.top + rect.height // 3
            pygame.draw.rect(screen, KAMIKAZE_II_WING_COLOR, wing)
            wing.right = rect.right
            pygame.draw.rect(screen, KAMIKAZE_II_WING_COLOR, wing)
        cockpit = rect.inflate(-(rect.width * 3 // 4), -(rect.height * 2 // 3))
        pygame.draw.ellipse(screen, ENEMY_COCKPIT_COLOR, cockpit)
        if self.dodge_state is DodgeState.READY:
            center = rect.centerx, rect.top + rect.height // 3
            pygame.draw.circle(
                screen,
                KAMIKAZE_II_READY_COLOR,
                center,
                KAMIKAZE_II_READY_RADIUS,
            )
