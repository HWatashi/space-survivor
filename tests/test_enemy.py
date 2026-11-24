import unittest

import pygame

from enemy import DodgeState, Enemy
from projectile import Projectile
from settings import (
    ENEMY_SIZE,
    KAMIKAZE_II_READY_COLOR,
    PROJECTILE_SIZE,
    WINDOW_SIZE,
)


class DodgeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.bounds = pygame.Rect((0, 0), WINDOW_SIZE)
        self.enemy = Enemy(200, 200, evolution_level=2)

    def shot(self, x: int, gap: int) -> Projectile:
        bottom = self.enemy.rect.bottom + gap + PROJECTILE_SIZE[1]
        return Projectile((x, bottom))

    def test_detects_approaching_shot_at_range_limit(self) -> None:
        enemy = self.enemy
        shot = self.shot(enemy.rect.left + 3, 100)
        enemy.try_dodge([shot], self.bounds)
        self.assertIs(enemy.dodge_state, DodgeState.DODGING)
        start = enemy.rect.topleft
        enemy.update(0.075)
        self.assertEqual(enemy.rect.x, start[0] + 40)
        self.assertGreater(enemy.rect.y, start[1])

    def test_safe_shots_do_not_trigger_dodge(self) -> None:
        rect = self.enemy.rect
        for shot in (
            self.shot(rect.centerx, 101),
            self.shot(rect.centerx, -rect.height - 15),
            self.shot(rect.right + PROJECTILE_SIZE[0] // 2, 20),
        ):
            self.enemy.try_dodge([shot], self.bounds)
            self.assertIs(self.enemy.dodge_state, DodgeState.READY)

    def test_dodge_finishes_at_same_position_for_varied_steps(self) -> None:
        for steps in ((0.05, 0.05, 0.05), (0.07, 0.08), (0.9,)):
            with self.subTest(steps=steps):
                enemy = Enemy(200, 200, evolution_level=2)
                enemy.try_dodge([self.shot(203, 60)], self.bounds)
                for dt in steps:
                    enemy.update(dt)
                self.assertIs(enemy.dodge_state, DodgeState.EXHAUSTED)
                self.assertEqual(enemy.rect.x, 280)

    def test_stays_inside_both_edges_and_cannot_dodge_twice(self) -> None:
        right_edge = self.bounds.right - ENEMY_SIZE[0]
        for left, direction in ((0, 1), (right_edge, -1)):
            with self.subTest(left=left):
                self.enemy = enemy = Enemy(left, 200, evolution_level=2)
                threat = self.shot(enemy.rect.centerx, 65)
                enemy.try_dodge([threat], self.bounds)
                enemy.update(0.15)
                self.assertEqual(enemy.rect.x, left + 80 * direction)
                self.assertTrue(self.bounds.contains(enemy.rect))
                threat = self.shot(enemy.rect.centerx, 65)
                enemy.try_dodge([threat], self.bounds)
                enemy.update(0.05)
                self.assertEqual(enemy.rect.x, left + 80 * direction)
                self.assertIs(enemy.dodge_state, DodgeState.EXHAUSTED)

    def test_uses_short_dodge_when_full_landings_are_blocked(self) -> None:
        shots = [self.shot(x, 50) for x in (122, 203, 290)]
        self.enemy.try_dodge(shots, self.bounds)
        self.enemy.update(0.15)
        self.assertIs(self.enemy.dodge_state, DodgeState.EXHAUSTED)
        self.assertLess(abs(self.enemy.rect.left - 200), 80)
        self.assertTrue(all(
            shot.rect.right <= self.enemy.rect.left
            or shot.rect.left >= self.enemy.rect.right
            for shot in shots
        ))

    def test_keeps_ability_when_all_landings_are_blocked(self) -> None:
        shots = [self.shot(x, 50) for x in range(130, 340, 30)]
        self.enemy.try_dodge(shots, self.bounds)
        self.enemy.update(0.15)
        self.assertEqual(self.enemy.rect.x, 200)
        self.assertIs(self.enemy.dodge_state, DodgeState.READY)

    def test_lower_levels_have_no_dodge(self) -> None:
        shot = self.shot(self.enemy.rect.centerx, 50)
        for level in (0, 1):
            enemy = Enemy(200, 200, evolution_level=level)
            enemy.try_dodge([shot], self.bounds)
            enemy.update(0.15)
            self.assertIsNone(enemy.dodge_state)
            self.assertEqual(enemy.rect.x, 200)

    def test_ready_indicator_disappears_when_dodge_starts(self) -> None:
        screen = pygame.Surface(WINDOW_SIZE)
        enemy = self.enemy
        indicator = enemy.rect.centerx, enemy.rect.top + enemy.rect.height // 3
        enemy.draw(screen)
        self.assertEqual(screen.get_at(indicator)[:3], KAMIKAZE_II_READY_COLOR)
        enemy.try_dodge([self.shot(enemy.rect.centerx, 50)], self.bounds)
        enemy.draw(screen)
        self.assertNotEqual(
            screen.get_at(indicator)[:3], KAMIKAZE_II_READY_COLOR
        )
