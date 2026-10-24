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
        self.next_boss_time = 60.0  # First boss arrives at 1:00 (each minute!)
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
        else:
            # 2 MINUTES+ (HARD): Tier 4 and beyond
            return 4 + int((t - 120.0) // 45.0)

    def get_health_multiplier(self) -> float:
        t = self.survival_time
        if t < 120.0:
            return 1.0 + (t / 120.0) * 0.85
        else:
            # 2 MINUTES+ (HARD): Heavy health boost (2.5x up to 5.0x)
            return min(5.0, 2.5 + ((t - 120.0) / 60.0) * 0.90)

    def get_speed_multiplier(self) -> float:
        t = self.survival_time
        if t < 120.0:
            return 1.0 + (t / 120.0) * 0.22
        else:
            # 2 MINUTES+ (HARD): Fast aggressive enemies
            return min(1.65, 1.30 + ((t - 120.0) / 75.0) * 0.25)

    def get_damage(self) -> int:
        if self.survival_time < 60.0:
            return 1
        elif self.survival_time < 120.0:
            return 2
        else:
            # 2 MINUTES+ (HARD): High-threat attacks
            return 2 if self.survival_time < 180.0 else 3

    def get_spawn_interval(self) -> float:
        t = self.survival_time
        if t < 120.0:
            return max(0.65, 1.65 - (t / 120.0) * 1.0)
        else:
            # 2 MINUTES+ (HARD): Rapid wave spawns
            return max(0.32, 0.52 - ((t - 120.0) / 100.0) * 0.20)

    def choose_enemy_type(self) -> str:
        t = self.survival_time
        if t < 25.0:
            # First 25s: Scouts, slow Tanks, and early Chargers
            pool = ["scout"] * 4 + ["tank"] * 2 + ["charger"] * 2
        elif t < 60.0:
            # 25-60s: Hunters start appearing
            pool = ["scout"] * 3 + ["tank"] * 2 + ["hunter"] * 2 + ["charger"] * 2
        elif t < 120.0:
            # 60-120s: Bombers enter
            pool = ["scout"] * 2 + ["tank"] * 2 + ["hunter"] * 2 + ["bomber"] * 2 + ["charger"] * 2
        else:
            # 2 MINUTES+ (HARD): Overwhelmingly Elite UFOs, deadly Chargers, Bombers, and Hunters!
            pool = ["elite"] * 5 + ["charger"] * 4 + ["bomber"] * 3 + ["hunter"] * 3 + ["tank"] * 2
        return random.choice(pool)

    def update(self, dt: float, enemies_count: int, boss_present: bool):
        self.survival_time += dt
        self.boss_active = boss_present
        self.spawn_timer += dt

    def should_spawn_enemy(self, current_enemy_count: int) -> bool:
        interval = self.get_spawn_interval() * (1.3 if self.boss_active else 1.0)
        # Max concurrent enemies scales with survival time (up to 36 on screen)
        max_enemies = 18 if self.boss_active else min(36, 10 + self.get_tier() * 4)

        if self.spawn_timer >= interval and current_enemy_count < max_enemies:
            self.spawn_timer = 0.0
            return True
        return False

    def create_enemies(self, player_x: float, player_y: float) -> list[Enemy]:
        tier = self.get_tier()
        if self.survival_time < 60.0:
            count = 1
        elif self.survival_time < 120.0:
            count = 2 if random.random() < 0.45 else 1
        else:
            # 2 MINUTES+ (HARD): Multi-lane swarms of 2 to 3 enemies simultaneously!
            count = random.choice([2, 3])

        spawned = []
        base_x = WIDTH + random.randrange(25, 90)
        lanes = random.sample(range(105, HEIGHT - 70, 48), count)
        for y in lanes:
            kind = self.choose_enemy_type()
            # If charger, spawn exactly on the right-edge warning line (WIDTH - 55)
            spawn_x = (WIDTH - 55.0) if kind == "charger" else (base_x + random.randrange(0, 40))
            spawned.append(
                Enemy(
                    kind=kind,
                    spawn_x=spawn_x,
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
        # Each minute there must be a boss: 1:00, 2:00, 3:00, 4:00...
        self.next_boss_time = max(self.survival_time + 30.0, (self.boss_milestone + 1) * 60.0)
