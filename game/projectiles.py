"""Player energy projectiles with glowing plasma trails and blade tips."""

import math

import pygame


class Projectile:
    def __init__(self, x, y, vx, vy, color, damage=1, radius=7, enemy=False, life=3.5, piercing=False):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = float(vx), float(vy)
        self.color = color
        self.damage = damage
        self.radius = radius
        self.enemy = enemy
        self.life = life
        self.alive = True
        self.piercing = piercing
        self.hit_enemies = set()
        self.trail = []
        self.angle = math.atan2(self.vy, self.vx)

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            self.alive = False
            return
        self.trail.append((self.x, self.y))
        max_trail = 10 if self.piercing else 6
        if len(self.trail) > max_trail:
            self.trail.pop(0)
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.x < -50 or self.x > 1330 or self.y < -50 or self.y > 770:
            self.alive = False

    def draw(self, surface, offset=(0, 0)):
        ox, oy = offset
        for i, (tx, ty) in enumerate(self.trail):
            t_radius = max(1, self.radius * (i + 1) // (len(self.trail) + 2))
            pygame.draw.circle(surface, self.color, (int(tx + ox), int(ty + oy)), t_radius)

        cx, cy = int(self.x + offset[0]), int(self.y + offset[1])
        cos_a, sin_a = math.cos(self.angle), math.sin(self.angle)
        perp_x, perp_y = -sin_a, cos_a

        # Outer glow
        glow_r = self.radius + (9 if self.piercing else 6)
        glow = pygame.Surface((glow_r * 2 + 2, glow_r * 2 + 2), pygame.SRCALPHA)
        glow_alpha = 110 if self.piercing else 75
        pygame.draw.circle(glow, (*self.color, glow_alpha), (glow_r + 1, glow_r + 1), glow_r)
        surface.blit(glow, (cx - glow_r - 1, cy - glow_r - 1))

        # Sleek arrowhead energy bolt
        tip = (cx + int(cos_a * (self.radius + (11 if self.piercing else 7))), cy + int(sin_a * (self.radius + (11 if self.piercing else 7))))
        left = (
            cx - int(cos_a * self.radius) + int(perp_x * (self.radius - 1)),
            cy - int(sin_a * self.radius) + int(perp_y * (self.radius - 1)),
        )
        tail = (cx - int(cos_a * (self.radius - 2)), cy - int(sin_a * (self.radius - 2)))
        right = (
            cx - int(cos_a * self.radius) - int(perp_x * (self.radius - 1)),
            cy - int(sin_a * self.radius) - int(perp_y * (self.radius - 1)),
        )
        pygame.draw.polygon(surface, self.color, [tip, left, tail, right])
        pygame.draw.circle(surface, (255, 255, 240), (cx, cy), max(2, self.radius // 2))

        # High-energy piercing halo rings
        if self.piercing:
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), self.radius + 3, 1)
            pygame.draw.line(surface, (255, 255, 255), (cx - 10, cy), (cx + 14, cy), 1)

