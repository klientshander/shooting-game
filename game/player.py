"""Upgraded Player starfighter with dynamic banking, single-bullet default, and charge-based Ultimate."""

import math
import sys
from pathlib import Path

import pygame

# Ensure project root is in sys.path when running player.py directly in VS Code
_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    from game.projectiles import Projectile
except ModuleNotFoundError:
    from projectiles import Projectile


_satellite_sprite = None


def get_satellite_sprite():
    global _satellite_sprite
    if _satellite_sprite is None:
        try:
            raw = pygame.image.load("assets/player_satellite_tight.png").convert_alpha()
            _satellite_sprite = pygame.transform.smoothscale(raw, (76, 88))
        except Exception:
            _satellite_sprite = None
    return _satellite_sprite


class Player:
    def __init__(self, color=(88, 231, 255), health=4):
        self.x, self.y = 180.0, 360.0
        self.color = color
        self.max_health = health
        self.health = health
        self.radius = 22
        self.speed = 520.0
        self.speed_multiplier = 1.0
        self.damage = 1
        self.fire_cooldown = 0.0
        self.base_fire_interval = 0.18
        self.shot_requested = False
        self.invulnerable = 0.0
        self.dash_cooldown = 0.0
        self.dash_time = 0.0
        self.aim_angle = 0.0
        self.pitch = 0.0  # Dynamic banking tilt

        # Ultimate is acquired ONLY from random in-game pickups! (Starts at 0)
        self.ultimate_charges = 0
        self.max_ultimate_charges = 3

        # Temporary skill pickup timers (all start at 0.0)
        self.skill_timers = {
            "attack_speed": 0.0,
            "split_bullets": 0.0,
            "shield": 0.0,
            "meteor_explosion": 0.0,
        }

    @property
    def fire_interval(self) -> float:
        if self.skill_timers["attack_speed"] > 0:
            return 0.09
        return self.base_fire_interval

    @property
    def has_shield(self) -> bool:
        return self.skill_timers["shield"] > 0

    @property
    def has_split_bullets(self) -> bool:
        return self.skill_timers["split_bullets"] > 0

    @property
    def has_meteor_explosion(self) -> bool:
        return self.skill_timers["meteor_explosion"] > 0

    @property
    def is_dashing(self) -> bool:
        return self.dash_time > 0.0

    def activate_skill(self, skill_id: str) -> str:
        """Activate the collected floating skill orb."""
        if skill_id == "attack_speed":
            self.skill_timers["attack_speed"] = 16.0
            return "SKILL: ATTACK SPEED (16s)"
        elif skill_id == "split_bullets":
            self.skill_timers["split_bullets"] = 16.0
            return "SKILL: SPLIT BULLETS (16s)"
        elif skill_id == "shield":
            self.skill_timers["shield"] = 16.0
            return "SKILL: STAR-SHIELD ACTIVE (16s)"
        elif skill_id == "meteor_explosion":
            self.skill_timers["meteor_explosion"] = 16.0
            return "SKILL: METEOR EXPLOSION (16s)"
        elif skill_id == "ultimate":
            self.ultimate_charges = min(self.max_ultimate_charges, self.ultimate_charges + 1)
            return f"ULTIMATE CHARGED! (x{self.ultimate_charges}) PRESS [Q] TO UNLEASH"
        return ""

    def update(self, dt, keys, mouse_pos=None, auto_fire=True):
        dx = float(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - float(keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = float(keys[pygame.K_s] or keys[pygame.K_DOWN]) - float(keys[pygame.K_w] or keys[pygame.K_UP])
        length = math.hypot(dx, dy)
        if length > 0:
            dx, dy = dx / length, dy / length
        movement = self.speed * self.speed_multiplier * (2.4 if self.dash_time > 0 else 1.0) * dt
        self.x += dx * movement
        self.y += dy * movement
        self.x = max(32.0, min(1248.0, self.x))
        self.y = max(82.0, min(676.0, self.y))

        # Dynamic banking tilt when moving vertically
        target_pitch = dy * 0.35
        self.pitch += (target_pitch - self.pitch) * min(1.0, dt * 14.0)

        # Bullets fire straight ahead (+X), independent of cursor position
        self.aim_angle = 0.0
        self.fire_cooldown = max(0.0, self.fire_cooldown - dt)
        self.invulnerable = max(0.0, self.invulnerable - dt)
        self.dash_cooldown = max(0.0, self.dash_cooldown - dt)
        self.dash_time = max(0.0, self.dash_time - dt)

        # Decay active skill pickup timers
        for k in self.skill_timers:
            if self.skill_timers[k] > 0:
                self.skill_timers[k] = max(0.0, self.skill_timers[k] - dt)

        # Automatic continuous shooting straight forward
        if auto_fire and self.fire_cooldown <= 0.0:
            self.fire_cooldown = self.fire_interval
            self.shot_requested = True
        else:
            self.shot_requested = False

    def request_shot(self):
        if self.fire_cooldown <= 0.0:
            self.shot_requested = True

    def fire(self):
        speed = 880.0
        shots = []

        # Split Bullets: fires 3-way spread straight ahead only when the pickup is active!
        if self.has_split_bullets:
            spreads = (-0.14, 0.0, 0.14)
            color = (255, 235, 95)
            for spread in spreads:
                is_center = abs(spread) < 0.01
                bolt_color = (120, 240, 255) if is_center else color
                bolt_radius = 8 if is_center else 6
                vx = math.cos(spread) * speed
                vy = math.sin(spread) * speed
                offset_y = 0.0 if is_center else math.sin(spread) * 16.0
                shots.append(
                    Projectile(
                        self.x + 38.0,
                        self.y + offset_y,
                        vx,
                        vy,
                        bolt_color,
                        self.damage,
                        bolt_radius,
                    )
                )
        else:
            # ONE SINGLE BULLET default stream fired strictly straight forward (+X) from satellite nose
            color = (255, 140, 255) if self.skill_timers["attack_speed"] > 0 else (88, 231, 255)
            shots.append(
                Projectile(
                    self.x + 38.0,
                    self.y,
                    speed,
                    0.0,
                    color,
                    self.damage,
                    7,
                )
            )

        self.shot_requested = False
        return shots

    def dash(self):
        if self.dash_cooldown <= 0:
            self.dash_time = 0.20
            self.dash_cooldown = 1.45
            self.invulnerable = max(self.invulnerable, 0.32)
            return True
        return False

    def use_special(self) -> bool:
        """Activate Ultimate Rift Pulse using a collected charge."""
        if self.ultimate_charges > 0:
            self.ultimate_charges -= 1
            return True
        return False

    def take_damage(self, amount=1):
        if self.invulnerable > 0:
            return False
        if self.has_shield:
            self.skill_timers["shield"] = 0.0
            self.invulnerable = 0.75
            return True
        self.health = max(0, self.health - amount)
        self.invulnerable = 0.90
        return True

    def draw(self, surface, offset=(0, 0)):
        ox, oy = offset
        x, y = int(self.x + ox), int(self.y + oy)
        ticks = pygame.time.get_ticks()

        if self.invulnerable > 0 and int(self.invulnerable * 16) % 2 == 0:
            return

        # Atmospheric ion aura glow
        aura = pygame.Surface((114, 114), pygame.SRCALPHA)
        pygame.draw.circle(aura, (*self.color, 42), (57, 57), 46)
        surface.blit(aura, (x - 57, y - 57))

        # Dynamic banking tilt angle
        bank_deg = -self.pitch * 9.0

        # Rear plasma rocket thruster exhaust
        flame = 22 + int(math.sin(ticks / 38) * 7)
        rear_x = x - 34
        pygame.draw.polygon(
            surface,
            (255, 95, 30),
            [(rear_x, y - 6), (rear_x - flame, y), (rear_x, y + 6)],
        )
        pygame.draw.polygon(
            surface,
            (255, 230, 95),
            [(rear_x, y - 3), (rear_x - flame // 2, y), (rear_x, y + 3)],
        )

        # Draw Satellite Spacecraft Sprite
        sprite = get_satellite_sprite()
        if sprite:
            if abs(bank_deg) > 0.5:
                rotated = pygame.transform.rotate(sprite, bank_deg)
                surface.blit(rotated, rotated.get_rect(center=(x, y)))
            else:
                surface.blit(sprite, sprite.get_rect(center=(x, y)))

        # Star-Shield active visual: rotating neon energy bubble with 4 orbiters
        if self.has_shield:
            pulse = int(math.sin(ticks / 110) * 3)
            sh_r = 44 + pulse
            sh_surf = pygame.Surface((sh_r * 2 + 14, sh_r * 2 + 14), pygame.SRCALPHA)
            sc = sh_r + 7
            pygame.draw.circle(sh_surf, (195, 70, 255, 52), (sc, sc), sh_r)
            pygame.draw.circle(sh_surf, (110, 225, 255, 220), (sc, sc), sh_r, 2)
            pygame.draw.circle(sh_surf, (235, 95, 255, 190), (sc, sc), sh_r - 3, 2)
            rot = ticks / 360.0
            for i in range(4):
                ang = rot + i * (math.pi / 2)
                nx = sc + int(math.cos(ang) * sh_r)
                ny = sc + int(math.sin(ang) * sh_r)
                pygame.draw.circle(sh_surf, (255, 240, 255), (nx, ny), 3)
            surface.blit(sh_surf, (x - sc, y - sc))


if __name__ == "__main__":
    from main import CosmicRift

    CosmicRift().run()
