"""Procedural sparks, glowing explosion rings, and outlined damage popups."""

import math
import random

import pygame


class Particle:
    def __init__(self, x, y, color, speed_range=(45, 280), size_range=(2, 6)):
        angle = random.random() * math.tau
        speed = random.uniform(*speed_range)
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed
        self.color = color
        self.life = random.uniform(0.28, 0.78)
        self.max_life = self.life
        self.radius = random.randint(*size_range)

    def update(self, dt):
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 0.96
        self.vy *= 0.96
        return self.life > 0

    def draw(self, surface, offset=(0, 0)):
        ratio = max(0.0, self.life / self.max_life)
        radius = max(1, int(self.radius * ratio))
        pos = (int(self.x + offset[0]), int(self.y + offset[1]))
        glow_r = radius + 3
        glow_surf = pygame.Surface((glow_r * 2 + 2, glow_r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color, int(95 * ratio)), (glow_r + 1, glow_r + 1), glow_r)
        surface.blit(glow_surf, (pos[0] - glow_r - 1, pos[1] - glow_r - 1))
        pygame.draw.circle(surface, self.color, pos, radius)
        if radius >= 3:
            pygame.draw.circle(surface, (255, 255, 255), pos, max(1, radius // 2))


class ExplosionRing:
    """Expanding shockwave ring for 'Destroy meteor with small explosion' and Ultimate."""

    def __init__(self, x, y, max_radius=85, color=(215, 95, 255), duration=0.32):
        self.x = float(x)
        self.y = float(y)
        self.max_radius = float(max_radius)
        self.color = color
        self.duration = duration
        self.life = duration

    def update(self, dt):
        self.life -= dt
        return self.life > 0

    def draw(self, surface, offset=(0, 0)):
        progress = 1.0 - max(0.0, self.life / self.duration)
        radius = max(4, int(self.max_radius * progress))
        alpha = max(0, int(220 * (1.0 - progress)))
        size = radius * 2 + 12
        ring_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        pygame.draw.circle(ring_surf, (*self.color, alpha // 3), center, radius)
        pygame.draw.circle(ring_surf, (*self.color, alpha), center, radius, max(2, int(6 * (1.0 - progress))))
        pygame.draw.circle(ring_surf, (255, 240, 255, alpha), center, max(2, int(radius * 0.7)), 2)
        surface.blit(ring_surf, (int(self.x + offset[0]) - size // 2, int(self.y + offset[1]) - size // 2))


class DamageNumber:
    _font = None

    def __init__(self, x, y, damage, critical=False):
        self.x, self.y = float(x), float(y)
        self.label = f"CRIT -{damage}" if critical else f"-{damage}"
        self.color = (255, 225, 85) if critical else (245, 250, 255)
        self.life = 0.75

    def update(self, dt):
        self.life -= dt
        self.y -= 44 * dt
        return self.life > 0

    def draw(self, surface, offset=(0, 0)):
        if DamageNumber._font is None:
            DamageNumber._font = pygame.font.SysFont("segoeui", 17, bold=True)
        cx, cy = int(self.x + offset[0]), int(self.y + offset[1])
        shadow = DamageNumber._font.render(self.label, True, (10, 12, 32))
        text = DamageNumber._font.render(self.label, True, self.color)
        rect = text.get_rect(center=(cx, cy))
        for ox, oy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            surface.blit(shadow, rect.move(ox, oy))
        surface.blit(text, rect)
