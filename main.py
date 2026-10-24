"""Entry point for COSMIC RIFT: Starfall - The Longer The Harder with In-Game Pickups."""

from __future__ import annotations

import json
import math
import os
import random
import sys

import pygame

from game.audio import Audio
from game.boss import Boss
from game.enemies import Enemy
from game.lightfall import Lightfall
from game.lightpillar import LightPillar
from game.particles import DamageNumber, ExplosionRing, Particle
from game.particles_bg import ParticlesBackground
from game.pickups import SkillPickup
from game.player import Player
from game.projectiles import Projectile
from game.solarsystem import SolarSystemBackground
from game.ui import UI
from game.waves import Waves
from game.webthreads import WebThreads
from settings import (
    BACKGROUND,
    CHARACTERS,
    CYAN,
    FPS,
    GOLD,
    HEIGHT,
    MAGENTA,
    SAVE_PATH,
    SKILLS,
    TITLE,
    WIDTH,
)
from game.collision import collision_pairs, engine_name


class CosmicRift:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.fullscreen = False
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.ui = UI()
        self.audio = Audio()
        self.state = "menu"
        self.menu_items = ["Play", "Character", "Settings", "Quit"]
        self.menu_index = 0
        self.overlay_index = 0
        self.setting_index = 0
        self.character_index = 0
        self.running = True
        self.settings_return_state = "menu"

        save_data = self._load_save()
        self.high_score = save_data["high_score"]
        self.best_time = save_data["best_time"]
        self.fullscreen = save_data["fullscreen"]
        self.character_index = save_data["character"]
        self.bg_setting = save_data.get("bg_setting", "random")

        # Multi-background engines (Solar System, LightPillar, Deep Stars, Lightfall, Particles, WebThreads)
        self.solarsystem = SolarSystemBackground(width=WIDTH, height=HEIGHT)
        self.lightpillar = LightPillar(width=WIDTH, height=HEIGHT)
        self.lightfall = Lightfall(width=WIDTH, height=HEIGHT)
        self.particles_bg = ParticlesBackground(width=WIDTH, height=HEIGHT)
        self.webthreads = WebThreads(
            width=WIDTH,
            height=HEIGHT,
            colors=["#5227FF", "#FF9FFC"],
            core_color="#FFFFFF",
            thread_count=6,
            spread=0.18,
        )
        self.current_bg = self._pick_random_bg(exclude_current=False) if self.bg_setting == "random" else self.bg_setting
        self.prev_bg: str | None = None
        self.bg_transition = 1.0
        self.bg_transition_duration = 2.0
        self.bg_random_timer = random.uniform(45.0, 65.0)
        self.bg_toast_message = ""
        self.bg_toast_timer = 0.0

        # Cinematic camera & letterbox framing
        self.cinema_letterbox = 0.0
        self.boss_alert_timer = 0.0

        # Pre-render cinematic anamorphic vignette
        self.vignette_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        diag = math.hypot(WIDTH * 0.5, HEIGHT * 0.5)
        for vy in range(0, HEIGHT, 8):
            for vx in range(0, WIDTH, 8):
                vd = math.hypot(vx - WIDTH * 0.5, vy - HEIGHT * 0.5) / diag
                if vd > 0.60:
                    vk = ((vd - 0.60) / 0.40) ** 1.8
                    self.vignette_surf.fill((3, 5, 15, int(145 * vk)), (vx, vy, 8, 8))

        if self.fullscreen:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        self.canvas_mouse = (WIDTH / 2.0, HEIGHT / 2.0)
        self._init_stars()
        self.reset_game()

    def _pick_random_bg(self, exclude_current: bool = True) -> str:
        options = ["solarsystem", "lightpillar", "stars", "lightfall", "particles", "webthreads"]
        if exclude_current and hasattr(self, "current_bg") and self.current_bg in options:
            candidates = [b for b in options if b != self.current_bg]
        else:
            candidates = options
        return random.choice(candidates)

    def switch_background(self, new_bg: str, announce: bool = True) -> None:
        if new_bg == self.current_bg and self.bg_transition >= 1.0:
            return
        self.prev_bg = self.current_bg
        self.current_bg = new_bg
        self.bg_transition = 0.0
        if announce:
            names = {
                "solarsystem": "SOLAR SYSTEM",
                "lightpillar": "LIGHT PILLAR",
                "stars": "DEEP STARS",
                "lightfall": "LIGHTFALL",
                "particles": "PARTICLES",
                "webthreads": "WEB THREADS",
            }
            self.bg_toast_message = f"BACKGROUND: {names.get(new_bg, new_bg.upper())}"
            self.bg_toast_timer = 2.5

    def _cycle_background(self, direction: int = 1) -> None:
        modes = ["solarsystem", "webthreads", "lightpillar", "stars", "lightfall", "particles", "random"]
        cur_idx = modes.index(self.bg_setting) if self.bg_setting in modes else 0
        new_idx = (cur_idx + direction) % len(modes)
        self.bg_setting = modes[new_idx]
        self._save_high_score()
        if self.bg_setting == "random":
            self.switch_background(self._pick_random_bg(exclude_current=True), announce=True)
        else:
            self.switch_background(self.bg_setting, announce=True)

    def _init_stars(self) -> None:
        """Create pure black multi-layer deep cosmic starfield with subtle stellar nebulae and shooting stars."""
        random.seed(42)
        # Layer 1: 180 distant faint stars [x, y, speed, brightness]
        self.stars_layer1 = [
            [random.randrange(WIDTH), random.randrange(HEIGHT), random.uniform(0.4, 0.7), random.randint(120, 180)]
            for _ in range(180)
        ]
        # Layer 2: 95 midground twinkling stars [x, y, speed, brightness, phase]
        self.stars_layer2 = [
            [random.randrange(WIDTH), random.randrange(HEIGHT), random.uniform(0.9, 1.4), random.randint(190, 245), random.uniform(0.0, 6.28)]
            for _ in range(95)
        ]
        # Layer 3: 38 bright diamond cross-glint stars [x, y, speed, spike_len, phase]
        self.stars_layer3 = [
            [random.randrange(WIDTH), random.randrange(HEIGHT), random.uniform(1.6, 2.3), random.randint(4, 7), random.uniform(0.0, 6.28)]
            for _ in range(38)
        ]
        # Cosmic shooting stars: [x, y, vx, vy, age, max_age, length]
        self.shooting_stars: list[list[float]] = []
        self.shooting_star_timer = random.uniform(4.0, 8.0)

        # Distant cosmic nebula dust clouds [x, y, radius, color, drift_speed]
        self.nebula_clouds = [
            [WIDTH * 0.22, HEIGHT * 0.35, 260, (20, 10, 48), 5.0],
            [WIDTH * 0.72, HEIGHT * 0.62, 320, (10, 22, 52), 7.5],
            [WIDTH * 0.48, HEIGHT * 0.18, 220, (28, 14, 38), 4.5],
            [WIDTH * 0.88, HEIGHT * 0.38, 280, (12, 28, 44), 6.5],
        ]
        # Pre-render soft circular nebula stamps with additive falloff
        self.nebula_surfs: list[pygame.Surface] = []
        for _, _, rad, col, _ in self.nebula_clouds:
            sz = int(rad * 2)
            surf = pygame.Surface((sz, sz))
            for y_pix in range(0, sz, 4):
                for x_pix in range(0, sz, 4):
                    d = math.hypot(x_pix - rad, y_pix - rad) / rad
                    if d < 1.0:
                        k = (1.0 - d) ** 2.2
                        c = (int(col[0] * k), int(col[1] * k), int(col[2] * k))
                        surf.fill(c, (x_pix, y_pix, 4, 4))
            self.nebula_surfs.append(surf)

    def _load_save(self) -> dict:
        try:
            with open(SAVE_PATH, "r", encoding="utf-8") as save_file:
                data = json.load(save_file)
            return {
                "high_score": max(0, int(data.get("high_score", 0))),
                "best_time": max(0.0, float(data.get("best_time", 0.0))),
                "fullscreen": bool(data.get("fullscreen", False)),
                "character": max(0, min(len(CHARACTERS) - 1, int(data.get("character", 0)))),
                "bg_setting": str(data.get("bg_setting", "solarsystem")),
            }
        except (FileNotFoundError, OSError, ValueError, TypeError, json.JSONDecodeError):
            return {"high_score": 0, "best_time": 0.0, "fullscreen": False, "character": 0, "bg_setting": "solarsystem"}

    def _save_high_score(self) -> None:
        os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
        with open(SAVE_PATH, "w", encoding="utf-8") as save_file:
            json.dump(
                {
                    "high_score": self.high_score,
                    "best_time": self.best_time,
                    "fullscreen": self.fullscreen,
                    "character": self.character_index,
                    "bg_setting": self.bg_setting,
                },
                save_file,
                indent=2,
            )

    def reset_game(self) -> None:
        """Reset all game objects and difficulty progression for a fresh run."""
        chosen = CHARACTERS[self.character_index]
        self.player = Player(chosen["color"], chosen.get("health", 4))
        self.player.speed_multiplier = chosen.get("speed", 1.0)
        self.player.damage = chosen.get("damage", 1)

        self.projectiles: list[Projectile] = []
        self.enemies: list[Enemy] = []
        self.pickups: list[SkillPickup] = []
        self.particles: list[Particle] = []
        self.rings: list[ExplosionRing] = []
        self.damage_numbers: list[DamageNumber] = []
        self.boss: Boss | None = None
        self.waves = Waves()
        self.score = 0
        self.combo = 0
        self.combo_timer = 0.0
        self.shake = 0.0
        self.upgrade_message = ""
        self.upgrade_timer = 0.0
        self.last_score_saved = False
        self.ambient_pickup_timer = 15.0

        # Background selection for fresh run
        if self.bg_setting == "random":
            self.current_bg = self._pick_random_bg(exclude_current=False)
            self.prev_bg = None
            self.bg_transition = 1.0
            self.bg_random_timer = random.uniform(45.0, 65.0)
        else:
            self.current_bg = self.bg_setting
            self.prev_bg = None
            self.bg_transition = 1.0
        self.solarsystem.reset()
        self.lightpillar.reset()
        self.lightfall.reset()
        self.particles_bg.reset()
        self.webthreads.reset()
        self.shooting_stars.clear()
        self.cinema_letterbox = 0.0
        self.boss_alert_timer = 0.0

    def _toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        flags = pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        self._save_high_score()

    def _begin_game(self) -> None:
        self.audio.play("select")
        self._save_high_score()
        self.reset_game()
        self.state = "playing"

    def _spawn_skill_pickup(self, x: float, y: float, skill_id: str | None = None) -> None:
        if skill_id is None:
            skill_id = random.choice([s["id"] for s in SKILLS])
        self.pickups.append(SkillPickup(x, y, skill_id))

    def _handle_key(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.audio.play("click")
            if self.state == "playing":
                self.state = "paused"
                self.overlay_index = 0
            elif self.state == "paused":
                self.state = "playing"
            elif self.state == "settings":
                self.state = self.settings_return_state
            elif self.state in ("character", "game_over"):
                self.state = "menu"
            return

        if key == pygame.K_b:
            self.audio.play("click")
            self._cycle_background(1)
            return

        if self.state == "menu":
            if key in (pygame.K_UP, pygame.K_w):
                self.menu_index = (self.menu_index - 1) % len(self.menu_items)
                self.audio.play("hover")
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.menu_index = (self.menu_index + 1) % len(self.menu_items)
                self.audio.play("hover")
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self.audio.play("click")
                self._menu_select()

        elif self.state == "character":
            if key in (pygame.K_LEFT, pygame.K_a):
                self.character_index = (self.character_index - 1) % len(CHARACTERS)
                self.audio.play("hover")
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.character_index = (self.character_index + 1) % len(CHARACTERS)
                self.audio.play("hover")
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self.audio.play("select")
                self._begin_game()

        elif self.state == "settings":
            if key in (pygame.K_UP, pygame.K_w):
                self.setting_index = (self.setting_index - 1) % 3
                self.audio.play("hover")
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.setting_index = (self.setting_index + 1) % 3
                self.audio.play("hover")
            elif key in (pygame.K_LEFT, pygame.K_a):
                self.audio.play("click")
                if self.setting_index == 0:
                    self._toggle_fullscreen()
                elif self.setting_index == 1:
                    self._cycle_background(-1)
            elif key in (pygame.K_RIGHT, pygame.K_d, pygame.K_RETURN, pygame.K_SPACE):
                self.audio.play("click")
                if self.setting_index == 0:
                    self._toggle_fullscreen()
                elif self.setting_index == 1:
                    self._cycle_background(1)
                else:
                    self.state = self.settings_return_state

        elif self.state == "paused":
            if key in (pygame.K_UP, pygame.K_w):
                self.overlay_index = (self.overlay_index - 1) % 3
                self.audio.play("hover")
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.overlay_index = (self.overlay_index + 1) % 3
                self.audio.play("hover")
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self.audio.play("click")
                if self.overlay_index == 0:
                    self.state = "playing"
                elif self.overlay_index == 1:
                    self._begin_game()
                else:
                    self.state = "menu"

        elif self.state == "game_over":
            if key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s):
                self.overlay_index = 1 - self.overlay_index
                self.audio.play("hover")
            elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                self.audio.play("select")
                if key == pygame.K_r or self.overlay_index == 0:
                    self._begin_game()
                else:
                    self.state = "menu"

        elif self.state == "playing":
            if key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                if self.player.dash():
                    self.audio.play("dash")
                    self.particles_bg.trigger_burst(self.player.x, self.player.y)
            elif key == pygame.K_q:
                self._special()

    def _menu_select(self) -> None:
        selected = self.menu_items[self.menu_index]
        if selected == "Play":
            self._begin_game()
        elif selected == "Character":
            self.state = "character"
        elif selected == "Settings":
            self.settings_return_state = "menu"
            self.state = "settings"
        else:
            self.running = False

    def _special(self) -> None:
        """Unleash Ultimate Rift Pulse using a collected Ultimate Orb charge."""
        if self.player.use_special():
            self.audio.play("special")
            self.shake = max(self.shake, 15.0)
            self.lightpillar.trigger_pulse(-0.8)
            self.lightfall.trigger_warp_burst(3.0)
            self.particles_bg.trigger_burst(self.player.x, self.player.y)
            self.webthreads.trigger_pulse()
            self.solarsystem.trigger_flare(2.0)
            pulse_radius = 540.0
            self.rings.append(ExplosionRing(self.player.x, self.player.y, pulse_radius, GOLD, 0.48))
            self.rings.append(ExplosionRing(self.player.x, self.player.y, pulse_radius * 0.75, (235, 75, 245), 0.38))

            defeated = [
                enemy
                for enemy in self.enemies
                if math.hypot(enemy.x - self.player.x, enemy.y - self.player.y) <= pulse_radius
            ]
            for enemy in defeated:
                self._burst(enemy.x, enemy.y, (255, 215, 80), 16)
                self._kill_enemy(enemy, trigger_chain=False)
            self.enemies = [enemy for enemy in self.enemies if enemy not in defeated]

            if self.boss:
                self.boss.health -= 50
                self.boss.hit_flash = 0.25
                self._burst(self.boss.x, self.boss.y, GOLD, 35)

            self.upgrade_message = "COSMIC RIFT ULTIMATE ACTIVATED!"
            self.upgrade_timer = 2.5
        else:
            self.upgrade_message = "NO ULTIMATE CHARGE! COLLECT A GOLDEN ORB IN SPACE"
            self.upgrade_timer = 2.0

    def _burst(self, x: float, y: float, color: tuple[int, int, int], amount: int = 12) -> None:
        for _ in range(amount):
            self.particles.append(Particle(x, y, color))

    def _kill_enemy(self, enemy: Enemy, trigger_chain: bool = True) -> None:
        self.combo += 1
        self.combo_timer = 2.5
        points = enemy.reward * min(5, 1 + (self.combo - 1) // 4)
        self.score += points
        self._burst(enemy.x, enemy.y, enemy.color, 18 if enemy.kind == "elite" else 13)
        self.audio.play("explosion")

        # Skill 4: "Destroy meteor with small explosion" AoE blast damage
        if self.player.has_meteor_explosion:
            blast_radius = 110.0
            blast_damage = 2
            self.rings.append(ExplosionRing(enemy.x, enemy.y, blast_radius, (220, 85, 255), 0.32))
            if trigger_chain:
                for other in self.enemies:
                    if other is not enemy and other.health > 0:
                        if math.hypot(other.x - enemy.x, other.y - enemy.y) <= blast_radius + other.radius:
                            other.health -= blast_damage
                            other.hit_flash = 0.14
                            self.damage_numbers.append(
                                DamageNumber(other.x, other.y - other.radius, blast_damage, False)
                            )

        # ~18% chance to drop one of the random skill orbs (including Ultimate Charge!)
        if random.random() < 0.18:
            self._spawn_skill_pickup(enemy.x, enemy.y)

        self.shake = max(self.shake, 4.0)

    def _player_hit(self, damage: int = 1) -> None:
        if self.player.take_damage(damage):
            self.audio.play("damage")
            self.shake = max(self.shake, 10.0)
            self._burst(self.player.x, self.player.y, (255, 93, 145), 18)
            if self.player.health <= 0:
                self.state = "game_over"
                self.overlay_index = 0
                self._save_final_score()

    def _save_final_score(self) -> None:
        if not self.last_score_saved:
            self.high_score = max(self.high_score, self.score)
            self.best_time = max(self.best_time, self.waves.survival_time)
            self._save_high_score()
            self.last_score_saved = True

    def _update_game(self, dt: float) -> None:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        screen_width, screen_height = self.screen.get_size()
        aim_pos = (mouse_x * WIDTH / screen_width, mouse_y * HEIGHT / screen_height)

        # Single-bullet default continuous shooting (split bullets only with pickup)
        self.player.update(dt, pygame.key.get_pressed(), aim_pos, auto_fire=True)

        if self.player.shot_requested:
            self.projectiles.extend(self.player.fire())
            self.audio.play("shoot")

        # The longer the harder: progressive scaling driven by survival time
        self.waves.update(dt, len(self.enemies), self.boss is not None)

        # Spawning straight-line enemies/meteors
        if self.waves.should_spawn_enemy(len(self.enemies)):
            self.enemies.extend(self.waves.create_enemies(self.player.x, self.player.y))

        # Check for milestone boss spawns
        if self.waves.should_spawn_boss(self.boss is not None):
            self.boss = self.waves.create_boss()
            self.audio.play("boss")
            self.boss_alert_timer = 4.0
            self.solarsystem.trigger_flare(1.6)
            self.upgrade_message = f"WARNING: COSMIC BOSS APPROACHING (MILESTONE {self.boss.milestone})"
            self.upgrade_timer = 4.0

        # Ambient random floating orb drifting across space every ~22 seconds
        self.ambient_pickup_timer -= dt
        if self.ambient_pickup_timer <= 0.0:
            self.ambient_pickup_timer = random.uniform(20.0, 28.0)
            self._spawn_skill_pickup(WIDTH + 30, random.uniform(110, HEIGHT - 110))

        # Update straight-line enemies (strictly straight horizontal movement, no shooting)
        for enemy in self.enemies:
            enemy.update(dt, self.player.x, self.player.y)

        # Trigger secondary kills from meteor explosion chain
        chain_defeated = [enemy for enemy in self.enemies if enemy.health <= 0]
        for enemy in chain_defeated:
            self._kill_enemy(enemy, trigger_chain=False)

        # Clean up off-screen enemies
        self.enemies = [
            enemy
            for enemy in self.enemies
            if enemy.health > 0 and not enemy.is_offscreen(WIDTH, HEIGHT)
        ]

        # Update floating skill & ultimate pickups & check collision with player
        remaining_pickups = []
        for pickup in self.pickups:
            if pickup.update(dt):
                if math.hypot(self.player.x - pickup.x, self.player.y - pickup.y) < self.player.radius + pickup.radius:
                    msg = self.player.activate_skill(pickup.skill_id)
                    self.audio.play("pickup")
                    burst_col = GOLD if pickup.theme == "gold" else (110, 230, 255) if pickup.theme == "blue" else (240, 90, 255)
                    self._burst(pickup.x, pickup.y, burst_col, 22)
                    self.rings.append(ExplosionRing(pickup.x, pickup.y, 70, burst_col, 0.28))
                    self.upgrade_message = msg
                    self.upgrade_timer = 2.6
                else:
                    remaining_pickups.append(pickup)
        self.pickups = remaining_pickups

        # Update boss (straight-line pass, no shooting)
        if self.boss:
            self.boss.update(dt, self.player.x, self.player.y)
            if self.boss.health <= 0:
                bonus = 2500 + self.boss.milestone * 1000
                self.score += bonus
                self._burst(self.boss.x, self.boss.y, (255, 126, 83), 52)
                self.rings.append(ExplosionRing(self.boss.x, self.boss.y, 280, GOLD, 0.60))
                self.rings.append(ExplosionRing(self.boss.x, self.boss.y, 150, (255, 225, 130), 0.42))
                self.audio.play("explosion")
                self.solarsystem.trigger_flare(2.2)
                # Defeating the boss drops a guaranteed Ultimate Orb + Skill Orb!
                self._spawn_skill_pickup(self.boss.x, self.boss.y - 25, "ultimate")
                self._spawn_skill_pickup(self.boss.x, self.boss.y + 25, "split_bullets")
                self.waves.boss_defeated()
                self.boss = None
                self.upgrade_message = "BOSS DEFEATED! ULTIMATE CHARGE & SKILL ORB DROPPED!"
                self.upgrade_timer = 3.5

        # Cinematic Starfighter Ion Thruster Trail
        rx = self.player.x - 30.0
        ry = self.player.y + random.uniform(-3.5, 3.5)
        if self.player.dash_time > 0:
            p_col = (255, random.randint(180, 240), 90)
            self.particles.append(Particle(rx, ry, p_col, speed_range=(90, 220), size_range=(2, 4)))
        elif random.random() < 0.60:
            p_col = (90, random.randint(200, 245), 255)
            self.particles.append(Particle(rx, ry, p_col, speed_range=(40, 110), size_range=(1, 3)))

        # Update player projectiles and visual effects
        for shot in self.projectiles:
            shot.update(dt)
        self.projectiles = [shot for shot in self.projectiles if shot.alive]
        self.particles = [p for p in self.particles if p.update(dt)]
        self.rings = [r for r in self.rings if r.update(dt)]
        self.damage_numbers = [number for number in self.damage_numbers if number.update(dt)]

        # Collision detection: Player shots vs Enemies
        shot_pairs = collision_pairs(
            [(shot.x, shot.y, shot.radius) for shot in self.projectiles],
            [(enemy.x, enemy.y, enemy.radius) for enemy in self.enemies],
        )
        defeated = set()
        for shot_index, enemy_index in shot_pairs:
            if shot_index < len(self.projectiles) and enemy_index < len(self.enemies):
                shot, enemy = self.projectiles[shot_index], self.enemies[enemy_index]
                if shot.alive and enemy.health > 0:
                    shot.alive = False
                    critical = random.random() < 0.14
                    damage = shot.damage * (2 if critical else 1)
                    enemy.health -= damage
                    self.damage_numbers.append(
                        DamageNumber(enemy.x, enemy.y - enemy.radius, damage, critical)
                    )
                    enemy.hit_flash = 0.12
                    self.audio.play("hit")
                    if enemy.health <= 0:
                        defeated.add(enemy)
        for enemy in defeated:
            self._kill_enemy(enemy)

        # Collision detection: Player shots vs Boss
        if self.boss:
            for shot in self.projectiles:
                if (
                    shot.alive
                    and math.hypot(shot.x - self.boss.x, shot.y - self.boss.y)
                    < self.boss.radius + shot.radius
                ):
                    shot.alive = False
                    critical = random.random() < 0.14
                    damage = shot.damage * (2 if critical else 1)
                    self.boss.health -= damage
                    self.damage_numbers.append(
                        DamageNumber(self.boss.x, self.boss.y - self.boss.radius, damage, critical)
                    )
                    self.boss.hit_flash = 0.10
                    self.audio.play("hit")

            # Boss hull vs Player collision
            if math.hypot(self.boss.x - self.player.x, self.boss.y - self.player.y) < self.boss.radius + self.player.radius:
                if not self.player.invulnerable:
                    self._player_hit(self.boss.damage)

        # Collision detection: Enemy hull vs Player
        for enemy in self.enemies:
            if math.hypot(enemy.x - self.player.x, enemy.y - self.player.y) < enemy.radius + self.player.radius:
                enemy_damage = enemy.damage
                enemy.health = 0
                self._kill_enemy(enemy, trigger_chain=True)
                if not self.player.invulnerable:
                    self._player_hit(enemy_damage)
        self.enemies = [enemy for enemy in self.enemies if enemy.health > 0]

        # Combo and screen shake decay
        if self.combo_timer > 0:
            self.combo_timer = max(0.0, self.combo_timer - dt)
            if self.combo_timer == 0:
                self.combo = 0
        if self.upgrade_timer > 0:
            self.upgrade_timer = max(0.0, self.upgrade_timer - dt)
        self.shake = max(0.0, self.shake - 22.0 * dt)

        # Background transition & random cycle
        if self.bg_transition < 1.0:
            self.bg_transition = min(1.0, self.bg_transition + dt / self.bg_transition_duration)

        if self.bg_toast_timer > 0.0:
            self.bg_toast_timer = max(0.0, self.bg_toast_timer - dt)

        if self.bg_setting == "random":
            self.bg_random_timer -= dt
            if self.bg_random_timer <= 0.0:
                self.bg_random_timer = random.uniform(45.0, 65.0)
                self.switch_background(self._pick_random_bg(exclude_current=True), announce=True)

        # Update cinematic letterbox & boss warning
        target_letterbox = 1.0 if self.boss else 0.0
        self.cinema_letterbox += (target_letterbox - self.cinema_letterbox) * min(1.0, dt * 3.5)
        if self.boss_alert_timer > 0.0:
            self.boss_alert_timer = max(0.0, self.boss_alert_timer - dt)

        # Update active background engines
        is_dashing = self.player.dash_time > 0.0
        is_holding_warp = is_dashing or pygame.mouse.get_pressed()[0]
        self.solarsystem.update(dt, mouse_pos=self.canvas_mouse)
        self.lightpillar.update(dt, mouse_pos=self.canvas_mouse)
        self.lightfall.update(dt, mouse_pos=self.canvas_mouse, is_holding_warp=is_holding_warp)
        self.particles_bg.update(dt, mouse_pos=self.canvas_mouse)
        self.webthreads.update(dt, mouse_pos=self.canvas_mouse)

    def _draw_background(self, dt: float) -> None:
        # Pure deep space void
        self.canvas.fill((0, 0, 0))
        ticks = pygame.time.get_ticks()

        # Distant cosmic nebula clouds drifting slowly
        for i, cloud in enumerate(self.nebula_clouds):
            cloud[0] -= cloud[4] * dt
            if cloud[0] + cloud[2] < 0:
                cloud[0] = WIDTH + cloud[2]
                cloud[1] = random.uniform(60, HEIGHT - 60)
            if i < len(self.nebula_surfs):
                self.canvas.blit(
                    self.nebula_surfs[i],
                    (int(cloud[0] - cloud[2]), int(cloud[1] - cloud[2])),
                    special_flags=pygame.BLEND_ADD,
                )

        # Layer 1: Distant faint stars drifting slowly
        for s in self.stars_layer1:
            s[0] -= s[2] * 28.0 * dt
            if s[0] < 0:
                s[0] = WIDTH - 1
                s[1] = random.randrange(HEIGHT)
            sx, sy = int(s[0]), int(s[1])
            if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
                c = s[3]
                self.canvas.set_at((sx, sy), (max(0, c - 20), max(0, c - 10), c))

        # Layer 2: Midground twinkling stars drifting at medium speed
        for s in self.stars_layer2:
            s[0] -= s[2] * 58.0 * dt
            if s[0] < 0:
                s[0] = WIDTH - 1
                s[1] = random.randrange(HEIGHT)
            twinkle = int(math.sin(ticks / 320.0 + s[4]) * 35)
            c = max(130, min(255, s[3] + twinkle))
            sx, sy = int(s[0]), int(s[1])
            if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
                pygame.draw.circle(self.canvas, (max(0, c - 15), max(0, c - 5), c), (sx, sy), 1)

        # Layer 3: Foreground luminous diamond cross-glint stars drifting fast
        for s in self.stars_layer3:
            s[0] -= s[2] * 92.0 * dt
            if s[0] < 0:
                s[0] = WIDTH - 1
                s[1] = random.randrange(HEIGHT)
            sx, sy, spike = int(s[0]), int(s[1]), s[3]
            if -10 <= sx <= WIDTH + 10 and -10 <= sy <= HEIGHT + 10:
                glint_mult = 1.0 + 0.3 * math.sin(ticks / 260.0 + s[4])
                cur_spike = max(2, int(spike * glint_mult))
                pygame.draw.circle(self.canvas, (255, 255, 255), (sx, sy), 2)
                pygame.draw.line(self.canvas, (185, 225, 255), (sx - cur_spike, sy), (sx + cur_spike, sy), 1)
                pygame.draw.line(self.canvas, (185, 225, 255), (sx, sy - cur_spike), (sx, sy + cur_spike), 1)

        # Occasional shooting star across deep space
        self.shooting_star_timer -= dt
        if self.shooting_star_timer <= 0:
            self.shooting_star_timer = random.uniform(5.0, 10.0)
            sx = random.uniform(WIDTH * 0.35, WIDTH + 60)
            sy = random.uniform(-30, HEIGHT * 0.45)
            spd = random.uniform(550.0, 850.0)
            ang = random.uniform(2.45, 2.75)  # shooting left-downward
            self.shooting_stars.append([
                sx, sy,
                math.cos(ang) * spd,
                math.sin(ang) * spd,
                0.0,  # age
                random.uniform(0.40, 0.70),  # max_age
                random.uniform(40.0, 75.0),  # tail length
            ])

        alive_stars = []
        for ss in self.shooting_stars:
            ss[4] += dt
            if ss[4] < ss[5]:
                ss[0] += ss[2] * dt
                ss[1] += ss[3] * dt
                progress = ss[4] / ss[5]
                alpha = math.sin(progress * math.pi)
                tail_len = ss[6]
                spd_len = math.hypot(ss[2], ss[3]) or 1.0
                nx, ny = ss[2] / spd_len, ss[3] / spd_len
                tail_x = ss[0] - nx * tail_len
                tail_y = ss[1] - ny * tail_len
                bright = int(255 * alpha)
                if bright > 15:
                    head_col = (bright, bright, bright)
                    tail_col = (int(160 * alpha), int(210 * alpha), int(255 * alpha))
                    pygame.draw.line(self.canvas, tail_col, (int(tail_x), int(tail_y)), (int(ss[0]), int(ss[1])), 1)
                    pygame.draw.circle(self.canvas, head_col, (int(ss[0]), int(ss[1])), 2)
                alive_stars.append(ss)
        self.shooting_stars = alive_stars

        # Composite active background layer(s) with smooth crossfade
        if self.bg_transition < 1.0 and self.prev_bg:
            fade_in = self.bg_transition
            fade_out = 1.0 - self.bg_transition
            self._render_bg_layer(self.prev_bg, fade_out)
            self._render_bg_layer(self.current_bg, fade_in)
        else:
            self._render_bg_layer(self.current_bg, 1.0)

    def _render_bg_layer(self, bg_name: str, alpha: float) -> None:
        if alpha <= 0.005:
            return
        if bg_name == "solarsystem":
            self.solarsystem.draw(self.canvas, alpha_mult=alpha)
        elif bg_name == "lightpillar":
            self.lightpillar.draw(self.canvas, alpha_mult=alpha)
        elif bg_name == "lightfall":
            self.lightfall.draw(self.canvas, mouse_pos=self.canvas_mouse, alpha_mult=alpha)
        elif bg_name == "particles":
            self.particles_bg.draw(self.canvas, alpha_mult=alpha)
        elif bg_name == "webthreads":
            self.webthreads.draw(self.canvas, alpha_mult=alpha)
        elif bg_name == "stars":
            pass  # Base cosmic starfield is already drawn

    def _draw(self, dt: float) -> None:
        self._draw_background(dt)
        offset = (
            (
                random.randint(-int(self.shake), int(self.shake)),
                random.randint(-int(self.shake), int(self.shake)),
            )
            if self.shake >= 1
            else (0, 0)
        )

        if self.state in ("playing", "paused", "game_over"):
            for r in self.rings:
                r.draw(self.canvas, offset)
            for p in self.particles:
                p.draw(self.canvas, offset)
            for pickup in self.pickups:
                pickup.draw(self.canvas, self.ui, offset)
            for number in self.damage_numbers:
                number.draw(self.canvas, offset)
            for shot in self.projectiles:
                shot.draw(self.canvas, offset)
            for enemy in self.enemies:
                enemy.draw(self.canvas, offset)
                enemy.draw_incoming_indicator(self.canvas, WIDTH)
            if self.boss:
                self.boss.draw(self.canvas, offset)
                self.boss.draw_incoming_indicator(self.canvas, WIDTH)
            self.player.draw(self.canvas, offset)

            if self.state == "playing":
                self.ui.draw_hud(
                    self.canvas,
                    self.player,
                    self.score,
                    self.high_score,
                    self.waves.formatted_time,
                    self.waves.get_tier(),
                    len(self.enemies),
                    self.boss,
                    self.combo,
                    engine_name(),
                    self.upgrade_message if self.upgrade_timer > 0 else "",
                )

        if self.state == "menu":
            best_time_str = f"{int(self.best_time) // 60:02d}:{int(self.best_time) % 60:02d}"
            self.ui.draw_menu(
                self.canvas,
                self.menu_items,
                self.menu_index,
                self.high_score,
                best_time_str,
            )
        elif self.state == "character":
            self.ui.draw_character(self.canvas, CHARACTERS, self.character_index)
        elif self.state == "settings":
            display_bg = self.bg_setting
            if display_bg == "solarsystem":
                bg_name = "SOLAR SYSTEM"
            elif display_bg == "lightpillar":
                bg_name = "LIGHT PILLAR"
            elif display_bg == "stars":
                bg_name = "DEEP STARS"
            elif display_bg == "lightfall":
                bg_name = "LIGHTFALL"
            elif display_bg == "particles":
                bg_name = "PARTICLES"
            elif display_bg == "webthreads":
                bg_name = "WEB THREADS"
            else:
                bg_name = "RANDOM"
            self.ui.draw_settings(self.canvas, self.fullscreen, self.setting_index, bg_mode=bg_name)
        elif self.state == "paused":
            self.ui.draw_overlay(
                self.canvas,
                "PAUSED",
                ["RESUME", "RESTART", "MAIN MENU"],
                self.overlay_index,
                f"SURVIVAL: {self.waves.formatted_time}   •   TIER {self.waves.get_tier()}",
                "ENTER / CLICK TO SELECT   •   ESC TO RESUME",
            )
        elif self.state == "game_over":
            self.ui.draw_overlay(
                self.canvas,
                "RIFT COLLAPSED",
                ["RESTART", "MAIN MENU"],
                self.overlay_index,
                f"SURVIVED: {self.waves.formatted_time}   •   SCORE: {self.score:,}   •   BEST: {self.high_score:,}",
                "PRESS ENTER OR 'R' TO RESTART IMMEDIATELY",
            )

        # In-game background switch toast notification
        if self.bg_toast_timer > 0.0 and self.bg_toast_message:
            toast_alpha = min(1.0, self.bg_toast_timer / 0.5)
            font = pygame.font.SysFont("segoeui", 12, bold=True)
            txt = font.render(f"• {self.bg_toast_message} •", True, (255, 225, 110))
            tw, th = txt.get_size()
            badge_surf = pygame.Surface((tw + 32, th + 12), pygame.SRCALPHA)
            a_bg = int(210 * toast_alpha)
            pygame.draw.rect(badge_surf, (15, 20, 55, a_bg), (0, 0, tw + 32, th + 12), border_radius=6)
            pygame.draw.rect(badge_surf, (80, 210, 255, int(220 * toast_alpha)), (0, 0, tw + 32, th + 12), 1, border_radius=6)
            txt.set_alpha(int(255 * toast_alpha))
            badge_surf.blit(txt, (16, 6))
            self.canvas.blit(badge_surf, (WIDTH // 2 - (tw + 32) // 2, 60))

        # Cinematic widescreen letterbox bars (smooth slide on Boss / Milestones)
        if self.cinema_letterbox > 0.01:
            bar_h = int(28 * self.cinema_letterbox)
            pygame.draw.rect(self.canvas, (0, 0, 0), (0, 0, WIDTH, bar_h))
            pygame.draw.rect(self.canvas, (0, 0, 0), (0, HEIGHT - bar_h, WIDTH, bar_h))
            pygame.draw.line(self.canvas, (215, 65, 50), (0, bar_h), (WIDTH, bar_h), 1)
            pygame.draw.line(self.canvas, (215, 65, 50), (0, HEIGHT - bar_h), (WIDTH, HEIGHT - bar_h), 1)

        # Cinematic Boss Approach Alert Banner
        if self.boss_alert_timer > 0.0 and self.state == "playing":
            alert_alpha = min(1.0, self.boss_alert_timer / 0.6)
            ticks = pygame.time.get_ticks()
            flash = 0.72 + 0.28 * math.sin(ticks / 90.0)
            font = pygame.font.SysFont("segoeui", 14, bold=True)
            txt = font.render("⚠  CLASS-IV COSMIC DREADNOUGHT APPROACHING  ⚠", True, (255, int(215 * flash), int(65 * flash)))
            tw, th = txt.get_size()
            box_w = tw + 46
            box_h = th + 12
            banner_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            a_bg = int(220 * alert_alpha)
            pygame.draw.rect(banner_surf, (26, 8, 16, a_bg), (0, 0, box_w, box_h), border_radius=6)
            pygame.draw.rect(banner_surf, (255, 65, 55, int(230 * alert_alpha * flash)), (0, 0, box_w, box_h), 1, border_radius=6)
            txt.set_alpha(int(255 * alert_alpha))
            banner_surf.blit(txt, (23, 6))
            self.canvas.blit(banner_surf, (WIDTH // 2 - box_w // 2, 40))

        # Cinematic anamorphic film vignette (draws focus and enriches cosmic contrast)
        self.canvas.blit(self.vignette_surf, (0, 0))

        display_size = self.screen.get_size()
        scaled = pygame.transform.smoothscale(self.canvas, display_size)
        self.screen.blit(scaled, (0, 0))
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)

            # Mouse mapping in canvas space and hold-to-warp detection
            mouse_x, mouse_y = pygame.mouse.get_pos()
            screen_width, screen_height = self.screen.get_size()
            self.canvas_mouse = (
                mouse_x * WIDTH / max(1, screen_width),
                mouse_y * HEIGHT / max(1, screen_height),
            )

            # Mouse hover detection for menus & overlays
            if self.state == "menu":
                for i in range(len(self.menu_items)):
                    if 365 + i * 52 <= self.canvas_mouse[1] <= 410 + i * 52:
                        if self.menu_index != i:
                            self.menu_index = i
                            self.audio.play("hover")
                        break
            elif self.state == "character":
                if 280 <= self.canvas_mouse[1] <= 520:
                    for i in range(len(CHARACTERS)):
                        card_x = 330 + i * 310
                        if card_x - 116 <= self.canvas_mouse[0] <= card_x + 116:
                            if self.character_index != i:
                                self.character_index = i
                                self.audio.play("hover")
                            break
            elif self.state == "settings":
                if 280 <= self.canvas_mouse[1] <= 335:
                    s_idx = 0
                elif 345 <= self.canvas_mouse[1] <= 400:
                    s_idx = 1
                elif 410 <= self.canvas_mouse[1] <= 465:
                    s_idx = 2
                else:
                    s_idx = None
                if s_idx is not None and self.setting_index != s_idx:
                    self.setting_index = s_idx
                    self.audio.play("hover")
            elif self.state in ("paused", "game_over"):
                num_opts = 3 if self.state == "paused" else 2
                for i in range(num_opts):
                    if 370 + i * 54 <= self.canvas_mouse[1] <= 420 + i * 54:
                        if self.overlay_index != i:
                            self.overlay_index = i
                            self.audio.play("hover")
                        break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_key(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    screen_width, screen_height = self.screen.get_size()
                    canvas_x = mouse_x * WIDTH / screen_width
                    canvas_y = mouse_y * HEIGHT / screen_height

                    # Click on top background badge or menu bottom hint to cycle backgrounds
                    if (45 <= canvas_y <= 95 and abs(canvas_x - WIDTH // 2) <= 160) or (self.state == "menu" and canvas_y >= 645 and canvas_x >= WIDTH // 2 + 60):
                        self.audio.play("click")
                        self._cycle_background(1)
                        continue

                    if self.state == "playing":
                        if WIDTH - 126 <= canvas_x <= WIDTH - 18 and HEIGHT - 57 <= canvas_y <= HEIGHT - 27:
                            self.audio.play("click")
                            self.state = "paused"
                            self.overlay_index = 0

                    elif self.state == "menu":
                        clicked_btn = False
                        for i in range(len(self.menu_items)):
                            if 365 + i * 52 <= canvas_y <= 410 + i * 52:
                                self.menu_index = i
                                self.audio.play("click")
                                self._menu_select()
                                clicked_btn = True
                                break
                        if not clicked_btn:
                            self.audio.play("click")

                    elif self.state == "character":
                        clicked_card = False
                        if 280 <= canvas_y <= 520:
                            for i in range(len(CHARACTERS)):
                                card_x = 330 + i * 310
                                if card_x - 116 <= canvas_x <= card_x + 116:
                                    self.character_index = i
                                    self.audio.play("select")
                                    self._begin_game()
                                    clicked_card = True
                                    break
                        if not clicked_card:
                            self.audio.play("click")

                    elif self.state == "paused":
                        options = ["RESUME", "RESTART", "MAIN MENU"]
                        clicked_opt = False
                        for i in range(len(options)):
                            if 370 + i * 54 <= canvas_y <= 420 + i * 54:
                                self.overlay_index = i
                                self.audio.play("click" if i == 2 else "select")
                                if i == 0:
                                    self.state = "playing"
                                elif i == 1:
                                    self._begin_game()
                                else:
                                    self.state = "menu"
                                clicked_opt = True
                                break
                        if not clicked_opt:
                            self.audio.play("click")

                    elif self.state == "game_over":
                        options = ["RESTART", "MAIN MENU"]
                        clicked_opt = False
                        for i in range(len(options)):
                            if 370 + i * 54 <= canvas_y <= 420 + i * 54:
                                self.overlay_index = i
                                self.audio.play("select" if i == 0 else "click")
                                if i == 0:
                                    self._begin_game()
                                else:
                                    self.state = "menu"
                                clicked_opt = True
                                break
                        if not clicked_opt:
                            self.audio.play("click")

                    elif self.state == "settings":
                        clicked_setting = False
                        if 280 <= canvas_y <= 335:
                            self.setting_index = 0
                            self.audio.play("click")
                            self._toggle_fullscreen()
                            clicked_setting = True
                        elif 345 <= canvas_y <= 400:
                            self.setting_index = 1
                            self.audio.play("click")
                            self._cycle_background(1)
                            clicked_setting = True
                        elif 410 <= canvas_y <= 465:
                            self.setting_index = 2
                            self.audio.play("click")
                            self.state = self.settings_return_state
                            clicked_setting = True
                        if not clicked_setting:
                            self.audio.play("click")

            if self.state == "playing":
                self._update_game(dt)
            else:
                if self.bg_transition < 1.0:
                    self.bg_transition = min(1.0, self.bg_transition + dt / self.bg_transition_duration)
                self.solarsystem.update(dt, mouse_pos=self.canvas_mouse)
                self.lightpillar.update(dt, mouse_pos=self.canvas_mouse)
                self.lightfall.update(dt, mouse_pos=self.canvas_mouse, is_holding_warp=False)
                self.particles_bg.update(dt, mouse_pos=self.canvas_mouse)
                self.webthreads.update(dt, mouse_pos=self.canvas_mouse)
            self._draw(dt)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    CosmicRift().run()
