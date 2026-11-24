import unittest
from unittest.mock import patch

from enemy import Enemy
from evolution import EvolutionManager
from settings import ENEMY_SPEED


class EvolutionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.evolution = EvolutionManager()

    def test_initial_state(self) -> None:
        self.assertEqual(self.evolution.survival_seconds, 0)
        self.assertEqual(self.evolution.max_level, 0)
        self.assertEqual(self.evolution.notice_remaining, 0)

    def test_unlock_at_30_seconds(self) -> None:
        with patch("evolution.random") as draw:
            self.assertFalse(self.evolution.update(29.999))
            self.assertEqual(self.evolution.max_level, 0)
            self.assertEqual(self.evolution.choose_enemy_level(), 0)
            draw.assert_not_called()
        self.assertTrue(self.evolution.update(0.001))
        self.assertEqual(self.evolution.whole_seconds, 30)
        self.assertEqual(self.evolution.max_level, 1)
        self.assertAlmostEqual(self.evolution.notice_remaining, 3)

    def test_crossing_threshold_unlocks_only_once(self) -> None:
        self.evolution.update(29.5)
        self.assertTrue(self.evolution.update(1.0))
        self.assertEqual(self.evolution.max_level, 1)
        self.assertAlmostEqual(self.evolution.notice_remaining, 2.5)
        self.assertFalse(self.evolution.update(0.5))
        self.assertAlmostEqual(self.evolution.notice_remaining, 2)
        self.assertFalse(self.evolution.update(2.0))
        self.assertEqual(self.evolution.notice_remaining, 0)

    def test_samples_each_spawn_independently_after_unlock(self) -> None:
        self.evolution.update(30)
        with patch("evolution.random", side_effect=[0.39, 0.4, 0.0]) as draw:
            levels = [self.evolution.choose_enemy_level() for _ in range(3)]
        self.assertEqual(levels, [1, 0, 1])
        self.assertEqual(draw.call_count, 3)

    def test_evolved_enemy_moves_30_percent_faster(self) -> None:
        base = Enemy(0, 0)
        evolved = Enemy(0, 0, evolution_level=1)
        start = base.y
        for _ in range(3):
            base.update(0.25)
            evolved.update(0.25)
        self.assertEqual(base.speed, ENEMY_SPEED)
        self.assertAlmostEqual(evolved.speed, ENEMY_SPEED * 1.3)
        self.assertAlmostEqual(evolved.y - start, (base.y - start) * 1.3)
        self.assertEqual(evolved.rect.size, base.rect.size)
