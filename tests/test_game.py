import unittest
from unittest.mock import Mock, patch

import pygame

from enemy import Enemy
from game import Game, GameState
from projectile import Projectile
from settings import PLAYER_MAX_HP, WINDOW_SIZE


class GameTest(unittest.TestCase):
    def setUp(self) -> None:
        pygame.font.init()
        self.addCleanup(pygame.font.quit)
        self.game = Game(pygame.Surface(WINDOW_SIZE))

    def add_contact(self) -> None:
        rect = self.game.player.rect
        self.game.enemies.append(Enemy(rect.left, rect.bottom))

    def run_frames(self, *frames: list[pygame.event.Event]) -> None:
        self.game.clock = Mock()
        self.game.clock.tick.return_value = 16
        with (
            patch.object(pygame.event, "get", side_effect=frames),
            patch.object(pygame.display, "flip"),
        ):
            self.game.run()

    def test_vulnerable_contact_damages_player_and_removes_enemy(self) -> None:
        self.add_contact()
        self.game._update_playing(0)
        self.assertEqual(self.game.player.hp, PLAYER_MAX_HP - 1)
        self.assertEqual(self.game.player.invulnerability_remaining, 1.5)
        self.assertFalse(self.game.enemies)
        self.assertEqual(self.game.score, 0)

    def test_protected_contact_keeps_enemy_moving(self) -> None:
        self.add_contact()
        self.game._update_playing(0)
        self.add_contact()
        enemy = self.game.enemies[0]
        start_y = enemy.y

        self.game._update_playing(100)

        self.assertEqual(self.game.player.hp, PLAYER_MAX_HP - 1)
        self.assertAlmostEqual(self.game.player.invulnerability_remaining, 1.4)
        self.assertEqual(self.game.enemies, [enemy])
        self.assertGreater(enemy.y, start_y)
        self.assertTrue(self.game.player.rect.colliderect(enemy.rect))
        self.assertEqual(self.game.score, 0)

    def test_simultaneous_contacts_remove_only_one_enemy(self) -> None:
        self.add_contact()
        self.add_contact()
        remaining_enemy = self.game.enemies[1]

        self.game._update_playing(0)

        self.assertEqual(self.game.player.hp, PLAYER_MAX_HP - 1)
        self.assertEqual(self.game.enemies, [remaining_enemy])

    def test_damage_returns_after_invulnerability_expires(self) -> None:
        self.add_contact()
        self.game._update_playing(0)
        for _ in range(14):
            self.game._update_playing(100)
        self.add_contact()
        enemy = self.game.enemies[0]
        self.game._update_playing(99)
        self.assertEqual(self.game.player.hp, PLAYER_MAX_HP - 1)
        self.assertEqual(self.game.enemies, [enemy])
        self.game._update_playing(1)
        self.assertEqual(self.game.player.hp, PLAYER_MAX_HP - 2)
        self.assertNotIn(enemy, self.game.enemies)
        self.assertEqual(self.game.player.invulnerability_remaining, 1.5)

    def test_ship_blinks_during_invulnerability(self) -> None:
        player = self.game.player
        background = (1, 2, 3)
        self.game.screen.fill(background)
        player.take_damage()
        player.draw(self.game.screen)
        color = self.game.screen.get_at(player.rect.center)[:3]
        self.assertEqual(color, background)

        player.update(set(), 0.16, self.game.bounds)
        player.draw(self.game.screen)
        self.assertNotEqual(
            self.game.screen.get_at(player.rect.center)[:3], background
        )

    def test_game_over_stops_simulation(self) -> None:
        self.game.player.hp = 1
        self.add_contact()
        enemy = Enemy(24, 120)
        projectile = Projectile((100, 200))
        self.game.enemies.append(enemy)
        self.game.projectiles.append(projectile)
        self.game._update_playing(0)
        self.assertIs(self.game.state, GameState.GAME_OVER)
        self.assertEqual(self.game.player.hp, 0)

        start = self.game.player.position.copy(), enemy.y, projectile.y
        self.game.enemy_spawn_elapsed_ms = 1499
        self.game.fire_cooldown_ms = 100
        self.run_frames(
            [pygame.event.Event(
                pygame.KEYDOWN, key=pygame.K_d, scancode=pygame.KSCAN_D
            )],
            [pygame.event.Event(
                pygame.KEYDOWN, key=pygame.K_SPACE, scancode=pygame.KSCAN_SPACE
            )],
            [pygame.event.Event(pygame.QUIT)],
        )
        end = self.game.player.position, enemy.y, projectile.y
        self.assertEqual(start, end)
        self.assertEqual(self.game.enemies, [enemy])
        self.assertEqual(self.game.projectiles, [projectile])
        self.assertEqual(self.game.enemy_spawn_elapsed_ms, 1499)
        self.assertEqual(self.game.fire_cooldown_ms, 100)

    def test_restart_resets_round_and_held_keys(self) -> None:
        self.game.player.hp = 1
        self.add_contact()
        self.game._update_playing(0)
        self.game.player.rect.x = 30
        self.game.player.position.x = 30
        self.game.score = 20
        self.game.enemies.append(Enemy(24, 120))
        self.game.projectiles.append(Projectile((100, 200)))
        self.game.enemy_spawn_elapsed_ms = 900
        self.game.fire_cooldown_ms = 140
        self.game.pressed_scancodes.update(
            (pygame.KSCAN_W, pygame.KSCAN_SPACE)
        )

        self.run_frames(
            [pygame.event.Event(
                pygame.KEYDOWN, key=ord("к"), scancode=pygame.KSCAN_R
            )],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)],
        )
        self.assertIs(self.game.state, GameState.PLAYING)
        self.assertEqual(self.game.player.hp, PLAYER_MAX_HP)
        player = self.game.player
        self.assertEqual(player.rect.center, self.game.bounds.center)
        self.assertEqual(player.position, player.rect.topleft)
        self.assertEqual(self.game.player.invulnerability_remaining, 0)
        self.assertEqual(self.game.score, 0)
        self.assertEqual(self.game.enemy_spawn_elapsed_ms, 0)
        self.assertEqual(self.game.fire_cooldown_ms, 0)
        self.assertFalse(self.game.enemies)
        self.assertFalse(self.game.projectiles)
        self.assertFalse(self.game.pressed_scancodes)

    def test_window_close_and_escape_work_in_both_states(self) -> None:
        for state in GameState:
            for event in (
                pygame.event.Event(pygame.QUIT),
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE),
            ):
                with self.subTest(state=state, event_type=event.type):
                    self.game.state = state
                    self.run_frames([event])

    def test_playing_accepts_scancodes_and_awards_points(self) -> None:
        start = self.game.player.position.copy()
        left = self.game.player.rect.centerx
        self.game.enemies.append(Enemy(left, self.game.player.rect.top))
        move = pygame.event.Event(
            pygame.KEYDOWN, key=ord("в"), scancode=pygame.KSCAN_D
        )
        fire = pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_SPACE, scancode=pygame.KSCAN_SPACE
        )
        self.run_frames([move, fire], [pygame.event.Event(pygame.QUIT)])
        self.assertGreater(self.game.player.position.x, start.x)
        self.assertEqual(self.game.score, 10)
        self.assertEqual(self.game.player.hp, PLAYER_MAX_HP)
        self.assertFalse(self.game.enemies)
        self.assertFalse(self.game.projectiles)
