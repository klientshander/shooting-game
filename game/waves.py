"""Dynamic progressive difficulty: starts accessible and gets steadily harder the longer you survive."""

import random
import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    from game.boss import Boss
    from game.enemies import Enemy
    from settings import HEIGHT, WIDTH
except ModuleNotFoundError:
    from boss import Boss
    from enemies import Enemy
    from settings import HEIGHT, WIDTH


class Waves:
    def __init__(self):
        self.reset()

    def reset(self):
        self.survival_time = 0.0
        self.spawn_timer = 0.0
        self.boss_milestone = 0
        self.next_boss_time = 120.0  # First boss arrives at 2:00
        self.boss_active = False

    @property
    def formatted_time(self) -> str:
        total_seconds = int(self.survival_time)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def get_tier(self) -> int:
        t = self.survival_time
        if t < 30.0:
            return 1
        elif t < 60.0:
            return 2
        elif t < 120.0:
            return 3
        elif t < 180.0:
            return 4
        else:
            return 5 + int((t - 180.0) // 60.0)

    def get_health_multiplier(self) -> float:
        # Starts at 1.0 (calm start), scales smoothly up to 3.4x the longer you survive
        return min(3.4, 1.0 + (self.survival_time / 65.0) * 0.42)

    def get_speed_multiplier(self) -> float:
        # Starts at 1.0, increases smoothly up to 1.45x
        return min(1.45, 1.0 + (self.survival_time / 110.0) * 0.22)

    def get_damage(self) -> int:
        if self.survival_time < 90.0:
            return 1
        elif self.survival_time < 210.0:
            return 2
        return 3

    def get_spawn_interval(self) -> float:
        # Starts at a relaxed 1.65s (easy to dodge and collect orbs), drops smoothly to 0.38s at high survival!
        return max(0.38, 1.65 - (self.survival_time / 150.0) * 1.0)

    def choose_enemy_type(self) -> str:
        t = self.survival_time
        if t < 25.0:
            # First 25s: Scouts and slow Tanks only
            pool = ["scout"] * 4 + ["tank"] * 2
        elif t < 55.0:
            # 25-55s: Hunters start appearing
            pool = ["scout"] * 3 + ["tank"] * 2 + ["hunter"] * 2
        elif t < 110.0:
            # 55-110s: Bombers enter
            pool = ["scout"] * 3 + ["tank"] * 2 + ["hunter"] * 2 + ["bomber"] * 2
        else:
            # 110s+: Full mix with Elites
            pool = ["scout"] * 2 + ["tank"] * 2 + ["hunter"] * 3 + ["bomber"] * 2 + ["elite"] * 2
        return random.choice(pool)

    def update(self, dt: float, enemies_count: int, boss_present: bool):
        self.survival_time += dt
        self.boss_active = boss_present
        self.spawn_timer += dt

    def should_spawn_enemy(self, current_enemy_count: int) -> bool:
        interval = self.get_spawn_interval() * (1.3 if self.boss_active else 1.0)
        # Max concurrent enemies scales with survival time
        max_enemies = 14 if self.boss_active else min(32, 8 + self.get_tier() * 4)

        if self.spawn_timer >= interval and current_enemy_count < max_enemies:
            self.spawn_timer = 0.0
            return True
        return False

    def create_enemies(self, player_x: float, player_y: float) -> list[Enemy]:
        tier = self.get_tier()
        # Single spawns early on; multi-spawns only at Tier 3+ (after 60s)
        count = 1
        if tier >= 3 and random.random() < 0.35:
            count = 2
        elif tier >= 5 and random.random() < 0.55:
            count = 2

        spawned = []
        base_x = WIDTH + random.randrange(25, 90)
        lanes = random.sample(range(105, HEIGHT - 70, 48), count)
        for y in lanes:
            kind = self.choose_enemy_type()
            spawned.append(
                Enemy(
                    kind=kind,
                    spawn_x=base_x + random.randrange(0, 40),
                    spawn_y=y,
                    target_x=player_x,
                    target_y=player_y,
                    health_mult=self.get_health_multiplier(),
                    speed_mult=self.get_speed_multiplier(),
                    damage=self.get_damage(),
                )
            )
        return spawned

    def should_spawn_boss(self, boss_present: bool) -> bool:
        if not boss_present and self.survival_time >= self.next_boss_time:
            return True
        return False

    def create_boss(self) -> Boss:
        self.boss_milestone += 1
        self.boss_active = True
        return Boss(milestone=self.boss_milestone)

    def boss_defeated(self):
        self.boss_active = False
        self.next_boss_time = self.survival_time + 120.0
