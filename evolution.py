from random import random

from settings import (
    EVOLUTION_NOTICE_SECONDS,
    KAMIKAZE_I_SPAWN_CHANCE,
    KAMIKAZE_I_UNLOCK_SECONDS,
)


# Adding frame deltas can leave a small floating-point error at a boundary.
TIME_TOLERANCE = 1e-9


class EvolutionManager:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.survival_seconds = 0.0
        self.max_level = 0

    def update(self, dt: float) -> bool:
        """Advance the round clock and report a newly unlocked evolution."""
        self.survival_seconds += dt
        if self.max_level == 0 and self._is_unlocked_at(self.survival_seconds):
            self.max_level = 1
            return True
        return False

    @property
    def notice_remaining(self) -> float:
        if self.max_level == 0:
            return 0.0
        elapsed = max(0.0, self.survival_seconds - KAMIKAZE_I_UNLOCK_SECONDS)
        remaining = EVOLUTION_NOTICE_SECONDS - elapsed
        return remaining if remaining > TIME_TOLERANCE else 0.0

    @property
    def whole_seconds(self) -> int:
        return int(self.survival_seconds + TIME_TOLERANCE)

    def choose_enemy_level(self, seconds_since_spawn: float = 0.0) -> int:
        spawn_time = self.survival_seconds - seconds_since_spawn
        if self.max_level == 0 or not self._is_unlocked_at(spawn_time):
            return 0
        return int(random() < KAMIKAZE_I_SPAWN_CHANCE)

    @staticmethod
    def _is_unlocked_at(seconds: float) -> bool:
        return seconds >= KAMIKAZE_I_UNLOCK_SECONDS - TIME_TOLERANCE
