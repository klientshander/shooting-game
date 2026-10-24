"""Cosmic Boss with upgraded visual design, holographic target reticle, and damage lag tracking."""

import math
import sys
from pathlib import Path

import pygame

_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from settings import HEIGHT, WIDTH, asset_path


_BOSS_SPRITE = None


def _get_boss_sprite():
    global _BOSS_SPRITE
    if _BOSS_SPRITE is None:
        try:
            raw = pygame.image.load(asset_path("enemy_alien_tight.png")).convert_alpha()
            base = pygame.transform.smoothscale(raw, (160, 122))
            tinted = base.copy()
            tinted.fill((75, 15, 70, 0), special_flags=pygame.BLEND_RGB_ADD)
            _BOSS_SPRITE = tinted
        except Exception:
            _BOSS_SPRITE = None
    return _BOSS_SPRITE


class Boss:
    def __init__(self, milestone=1):
        self.x = float(WIDTH + 90)
        self.y = 360.0
        self.radius = 72
        self.milestone = milestone
        self.max_health = min(1100, int(260 + (milestone - 1) * 110))
        self.health = self.max_health
        self.damage_lag_health = float(self.max_health)
        self.damage = 2 if milestone == 1 else 3
        self.speed = 135.0 + min(60.0, milestone * 12.0)
        self.age = 0.0
        self.hit_flash = 0.0
        self.phase = 1

    def update(self, dt, player_x=0.0, player_y=0.0):
        self.age += dt
        self.hit_flash = max(0.0, self.hit_flash - dt)
        self.phase = 1 if self.health > self.max_health * 0.5 else 2

        # Straight-line horizontal charge across the arena (no shooting)
        move_speed = self.speed * (1.30 if self.phase == 2 else 1.0)
        self.x -= move_speed * dt

        # Smooth damage lag bar decay towards current health
        if self.damage_lag_health > self.health:
            self.damage_lag_health = max(float(self.health), self.damage_lag_health - (self.max_health * 0.85 * dt))
        else:
            self.damage_lag_health = float(self.health)

        # Re-enter from the right side along alternating combat lanes
        if self.x < -self.radius - 50:
            self.x = float(WIDTH + self.radius + 50)
            lanes = (180.0, 270.0, 360.0, 450.0, 540.0)
            self.y = lanes[int(self.age * 12) % len(lanes)]

        return None

    def draw_incoming_indicator(self, surface, screen_width=1280):
        """Draw an intense flashing BOSS WARNING marker on the right edge when incoming."""
        if screen_width <= self.x <= screen_width + 180:
            edge_x = screen_width - 24
            edge_y = int(self.y)
            pulse = int(math.sin(self.age * 16.0) * 4)

            # Flashing danger beacon
            banner = pygame.Surface((140, 34), pygame.SRCALPHA)
            pygame.draw.rect(banner, (185, 25, 45, 215), (0, 0, 140, 34), border_radius=6)
            pygame.draw.rect(banner, (255, 215, 80), (0, 0, 140, 34), 2, border_radius=6)
            font = pygame.font.SysFont("segoeui", 13, bold=True)
            txt = font.render("⚠ BOSS INCOMING", True, (255, 255, 255))
            banner.blit(txt, txt.get_rect(center=(70, 17)))
            surface.blit(banner, (screen_width - 150 - pulse, edge_y - 17))

    def draw(self, surface, offset=(0, 0)):
        x, y = int(self.x + offset[0]), int(self.y + offset[1])
        r = self.radius
        flash = self.hit_flash > 0

        # Radiant boss aura
        glow = pygame.Surface((r * 3, r * 3), pygame.SRCALPHA)
        pygame.draw.circle(glow, (235, 65, 220, 68), (int(r * 1.5), int(r * 1.5)), int(r * 1.4))
        surface.blit(glow, (x - int(r * 1.5), y - int(r * 1.5)))

        # Holographic tactical targeting reticle around boss
        rot = self.age * 1.4
        for i in range(4):
            ang = rot + i * (math.pi / 2)
            c_dist = r + 16
            cx = x + int(math.cos(ang) * c_dist)
            cy = y + int(math.sin(ang) * c_dist)
            pygame.draw.circle(surface, (255, 215, 80) if self.phase == 2 else (235, 80, 245), (cx, cy), 4)

        # Rear plasma tail
        tail = int(48 + math.sin(self.age * 14) * 12)
        pygame.draw.polygon(
            surface,
            (255, 110, 50),
            [(x + r - 10, y - 36), (x + r + tail + 28, y), (x + r - 10, y + 36)],
        )
        pygame.draw.polygon(
            surface,
            (255, 225, 95),
            [(x + r - 10, y - 18), (x + r + tail, y), (x + r - 10, y + 18)],
        )

        # Outer alien energy containment rings
        pygame.draw.circle(surface, (52, 18, 86), (x, y), r + 14)
        pygame.draw.circle(surface, (255, 85, 215), (x, y), r + 9, 3)
        pygame.draw.circle(surface, (85, 230, 255), (x, y), r + 2, 2)

        # Draw Giant Alien Mothership Sprite
        sprite = _get_boss_sprite()
        if sprite:
            if flash:
                flash_surf = sprite.copy()
                flash_surf.fill((210, 210, 210, 0), special_flags=pygame.BLEND_RGB_ADD)
                surface.blit(flash_surf, flash_surf.get_rect(center=(x, y)))
            else:
                surface.blit(sprite, sprite.get_rect(center=(x, y)))

        # Glowing pulsating alien reactor core
        core_pulse = int(math.sin(self.age * 10) * 3)
        pygame.draw.circle(surface, (255, 130, 60), (x - 6, y), 24 + core_pulse)
        pygame.draw.circle(surface, (255, 235, 130), (x - 6, y), 13)
        pygame.draw.circle(surface, (255, 255, 255), (x - 6, y), 6)
