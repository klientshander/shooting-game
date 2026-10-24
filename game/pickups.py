"""Floating random skill and ultimate orb pickups with glowing beacon rings and name labels."""

import math
import sys
from pathlib import Path

import pygame

_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from settings import SKILLS


class SkillPickup:
    def __init__(self, x: float, y: float, skill_id: str):
        self.x = float(x)
        self.y = float(y)
        self.base_y = self.y
        self.skill_id = skill_id
        self.radius = 24
        self.age = 0.0
        self.life = 18.0
        self.vx = -65.0  # Drifts gently across the screen

        skill_info = next((s for s in SKILLS if s["id"] == skill_id), None)
        self.theme = skill_info["theme"] if skill_info else "blue"
        self.short_name = skill_info["short_name"] if skill_info else skill_id.upper()

    def update(self, dt: float) -> bool:
        self.age += dt
        self.life -= dt
        if self.life <= 0.0:
            return False
        self.x += self.vx * dt
        self.y = self.base_y + math.sin(self.age * 3.2) * 16.0
        return self.x > -50.0

    def draw(self, surface, ui, offset=(0, 0)):
        if self.life < 3.0 and int(self.life * 8) % 2 == 0:
            return

        ox, oy = offset
        cx, cy = int(self.x + ox), int(self.y + oy)

        # Pulsating outer beacon ring
        pulse = int(math.sin(self.age * 5.0) * 4)
        glow_r = self.radius + 8 + pulse
        beacon = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
        if self.theme == "gold":
            ring_col = (255, 215, 75, 120)
        elif self.theme == "blue":
            ring_col = (70, 210, 255, 95)
        else:
            ring_col = (235, 80, 255, 95)
        pygame.draw.circle(beacon, ring_col, (glow_r + 2, glow_r + 2), glow_r, 2)
        surface.blit(beacon, (cx - glow_r - 2, cy - glow_r - 2))

        # Render the 3D glossy orb
        ui.draw_skill_orb(surface, self.skill_id, self.theme, (cx, cy), radius=self.radius, selected=True)

        # Crisp floating name tag directly above the orb so it's instantly identifiable
        tag_color = (255, 235, 110) if self.theme == "gold" else (180, 235, 255) if self.theme == "blue" else (255, 190, 255)
        ui.text(surface, self.short_name, (cx, cy - self.radius - 16), tag_color, ui.small, center=True, outline=True)
