from random import random

from settings import (
    EVOLUTION_NOTICE_SECONDS,
    KAMIKAZE_I_SPAWN_CHANCE,
    KAMIKAZE_I_UNLOCK_SECONDS,
    KAMIKAZE_II_SPAWN_CHANCE,
    KAMIKAZE_II_UNLOCK_SECONDS,
)


# Adding frame deltas can leave a small floating-point error at a boundary.
TIME_TOLERANCE = 1e-9
UNLOCK_TIMES = (KAMIKAZE_I_UNLOCK_SECONDS, KAMIKAZE_II_UNLOCK_SECONDS)


class EvolutionManager:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.survival_seconds = 0.0
        self.max_level = 0

    def update(self, dt: float) -> bool:
        """Advance the round clock and report a newly unlocked evolution."""
        self.survival_seconds += dt
        previous_level = self.max_level
        self.max_level = self._level_at(self.survival_seconds)
        return self.max_level > previous_level

    @property
    def notice_remaining(self) -> float:
        if self.max_level == 0:
            return 0.0
        unlocked_at = UNLOCK_TIMES[self.max_level - 1]
        elapsed = max(0.0, self.survival_seconds - unlocked_at)
        remaining = EVOLUTION_NOTICE_SECONDS - elapsed
        return remaining if remaining > TIME_TOLERANCE else 0.0

    @property
    def whole_seconds(self) -> int:
        return int(self.survival_seconds + TIME_TOLERANCE)

    def choose_enemy_level(self, seconds_since_spawn: float = 0.0) -> int:
        spawn_time = self.survival_seconds - seconds_since_spawn
        available_level = self._level_at(spawn_time)
        if available_level == 0:
            return 0
        roll = random()
        if roll < KAMIKAZE_I_SPAWN_CHANCE:
            return 1
        if (
            available_level == 2
            and roll < KAMIKAZE_I_SPAWN_CHANCE + KAMIKAZE_II_SPAWN_CHANCE
        ):
            return 2
        return 0

    @staticmethod
    def _level_at(seconds: float) -> int:
        return sum(seconds >= time - TIME_TOLERANCE for time in UNLOCK_TIMES)
