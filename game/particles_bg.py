"""Particles Background Engine for Cosmic Rift.

Pygame port of the React Bits <Particles /> component: a 3D cloud of
particles with perspective projection, harmonic bobbing, slow field rotation,
parallax hover, soft glow, twinkle and click/shockwave bursts.

Tuned to read as deep space: tinted star colours, small depth-attenuated
points, a gentle leftward drift (the ship flies to the right) and additive
premultiplied glow sprites (no alpha artifacts).
"""

from __future__ import annotations

import math
import random

import pygame

from settings import WIDTH, HEIGHT


class ParticleBurst:
    __slots__ = ("x", "y", "age", "max_age", "speed", "width")

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.age = 0.0
        self.max_age = 1.5
        self.speed = 520.0
        self.width = 46.0


class ParticlePoint:
    __slots__ = ("x", "y", "z", "r0", "r1", "r2", "r3", "size", "color_idx")

    def __init__(self, x, y, z, r0, r1, r2, r3, size, color_idx) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.r0 = r0
        self.r1 = r1
        self.r2 = r2
        self.r3 = r3
        self.size = size
        self.color_idx = color_idx


def _hex(value: str) -> tuple[int, int, int]:
    h = value.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


class ParticlesBackground:
    BRIGHT_LEVELS = 6
    RADII = (1, 2, 3, 4, 6)

    def __init__(
        self,
        width: int = WIDTH,
        height: int = HEIGHT,
        particle_count: int = 200,
        particle_spread: float = 10.0,
        speed: float = 0.1,
        particle_colors: list[str] | None = None,
        particle_base_size: float = 100.0,
        glow: float = 0.5,
        twinkle: float = 0.3,
        camera_distance: float = 20.0,
        move_particles_on_hover: bool = True,
        drift_speed: float = 0.6,
        intro: bool = True,
        seed: int = 1337,
    ) -> None:
        self.width = width
        self.height = height
        self.count = particle_count
        self.spread = particle_spread
        self.speed = speed
        self.base_size = particle_base_size
        self.glow = glow
        self.twinkle_amount = twinkle
        self.camera_distance = camera_distance
        self.move_on_hover = move_particles_on_hover
        self.drift_speed = drift_speed
        self.intro_enabled = intro
        self._rng = random.Random(seed)  # local RNG: never reseeds the game's global RNG

        # Space palette: mostly white, with pale blue / warm gold / soft violet stars
        colors = particle_colors or ["#ffffff", "#ffffff", "#cfe0ff", "#ffe9c4", "#d9c8ff"]
        self.rgb_colors = [_hex(c) for c in colors]

        self.time = 0.0
        self.spin = 0.0
        self.travel = 0.0
        self.intro_timer = 1.8 if intro else 0.0
        self.intro_duration = 1.8

        self.offset_x = 0.0
        self.offset_y = 0.0
        self.target_offset_x = 0.0
        self.target_offset_y = 0.0

        self.bursts: list[ParticleBurst] = []
        self.particles: list[ParticlePoint] = []
        self._init_particles()
        self._build_sprites()

    # ------------------------------------------------------------------ setup
    def _init_particles(self) -> None:
        rng = self._rng
        self.particles.clear()
        for _ in range(self.count):
            while True:
                x, y, z = rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)
                l2 = x * x + y * y + z * z
                if 0.001 < l2 <= 1.0:
                    break
            r = math.cbrt(rng.random())
            self.particles.append(
                ParticlePoint(
                    x=x * r * self.spread * 1.9,  # wider than tall to fill a 16:9 screen
                    y=y * r * self.spread * 1.1,
                    z=z * r * self.spread * 1.2,
                    r0=rng.random(),
                    r1=rng.random(),
                    r2=rng.random(),
                    r3=rng.random(),
                    size=(self.base_size * 0.022) * (0.6 + 0.9 * rng.random() ** 2),
                    color_idx=rng.randrange(len(self.rgb_colors)),
                )
            )

    def _build_sprites(self) -> None:
        """Pre-render additive (black-backed, premultiplied) star sprites.

        Keyed by (radius, colour index, brightness level) so drawing a star is
        a single BLEND_ADD blit with no per-frame surface copies.
        """
        self._sprites: dict[tuple[int, int, int], pygame.Surface] = {}
        for radius in self.RADII:
            halo = radius * 3 + 2
            size = halo * 2 + 1
            for ci, col in enumerate(self.rgb_colors):
                base = pygame.Surface((size, size))
                for py in range(size):
                    for px in range(size):
                        d = math.hypot(px - halo, py - halo)
                        core = max(0.0, min(1.0, radius + 0.5 - d))  # anti-aliased disc
                        glow = math.exp(-d / max(1.0, radius * 1.1)) * self.glow * 0.55
                        k = min(1.0, core + glow * (1.0 - core))
                        if k > 0.004:
                            base.set_at((px, py), (int(col[0] * k), int(col[1] * k), int(col[2] * k)))
                for level in range(1, self.BRIGHT_LEVELS + 1):
                    s = base.copy()
                    v = int(255 * level / self.BRIGHT_LEVELS)
                    s.fill((v, v, v), special_flags=pygame.BLEND_RGB_MULT)
                    self._sprites[(radius, ci, level)] = s

    # ----------------------------------------------------------------- update
    def trigger_burst(self, x: float, y: float) -> None:
        if len(self.bursts) >= 4:
            self.bursts.pop(0)
        self.bursts.append(ParticleBurst(x, y))

    def reset(self) -> None:
        self.time = 0.0
        self.spin = 0.0
        self.intro_timer = 1.8 if self.intro_enabled else 0.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.bursts.clear()

    def update(self, dt: float, mouse_pos: tuple[float, float] | None = None) -> None:
        pace = dt * self.speed * 2.8
        self.time += pace
        self.spin += pace * 0.25
        self.travel += dt * self.drift_speed

        if self.intro_timer > 0.0:
            self.intro_timer = max(0.0, self.intro_timer - dt)

        if self.move_on_hover and mouse_pos is not None:
            nx = (mouse_pos[0] / float(self.width)) * 2.0 - 1.0
            ny = (mouse_pos[1] / float(self.height)) * 2.0 - 1.0
            self.target_offset_x = -nx * 24.0
            self.target_offset_y = -ny * 16.0

        follow = min(1.0, dt * 3.0)
        self.offset_x += (self.target_offset_x - self.offset_x) * follow
        self.offset_y += (self.target_offset_y - self.offset_y) * follow

        for b in self.bursts:
            b.age += dt
        self.bursts = [b for b in self.bursts if b.age < b.max_age]

    # ------------------------------------------------------------------- draw
    def draw(self, surface: pygame.Surface, alpha_mult: float = 1.0) -> None:
        if alpha_mult <= 0.005:
            return

        intro = 1.0
        if self.intro_timer > 0.0:
            t = 1.0 - self.intro_timer / self.intro_duration
            intro = t * t * (3.0 - 2.0 * t)
        fade = alpha_mult * intro

        rx = math.sin(self.time * 0.22) * 0.10
        ry = math.cos(self.time * 0.35) * 0.12
        rz = math.sin(self.spin) * 0.25  # gentle rocking instead of a full spin
        sx_, cx_ = math.sin(rx), math.cos(rx)
        sy_, cy_ = math.sin(ry), math.cos(ry)
        sz_, cz_ = math.sin(rz), math.cos(rz)
        r00 = cy_ * cz_ + sy_ * sx_ * sz_
        r01 = cx_ * sz_
        r02 = -sy_ * cz_ + cy_ * sx_ * sz_
        r10 = -cy_ * sz_ + sy_ * sx_ * cz_
        r11 = cx_ * cz_
        r12 = sy_ * sz_ + cy_ * sx_ * cz_
        r20 = sy_ * cx_
        r21 = -sx_
        r22 = cy_ * cx_

        w, h = self.width, self.height
        cx = w * 0.5 + self.offset_x
        cy = h * 0.5 + self.offset_y
        focal = h * 1.6
        span_x = self.spread * 1.9 * 2.0
        t = self.time
        sprites = self._sprites
        levels = self.BRIGHT_LEVELS

        for p in self.particles:
            bob_x = math.sin(t * p.r2 * 2.5 + 6.28 * p.r3) * (0.1 + 0.8 * p.r0)
            bob_y = math.sin(t * p.r1 * 2.5 + 6.28 * p.r0) * (0.1 + 0.8 * p.r3)
            bob_z = math.sin(t * p.r3 * 2.5 + 6.28 * p.r1) * (0.1 + 0.8 * p.r2)

            # Leftward drift with wrap-around (nearer particles appear to move faster)
            px = (p.x - self.travel * (0.6 + p.r1)) % span_x - span_x * 0.5

            wx = r00 * px + r01 * p.y + r02 * p.z + bob_x
            wy = r10 * px + r11 * p.y + r12 * p.z + bob_y
            wz = r20 * px + r21 * p.y + r22 * p.z + bob_z

            ahead = self.camera_distance - wz
            if ahead < 3.0:
                continue
            scale = focal / ahead
            sx = cx + wx * scale
            sy = cy + wy * scale
            if sx < -20 or sx > w + 20 or sy < -20 or sy > h + 20:
                continue

            flash = 0.0
            for b in self.bursts:
                prog = b.age / b.max_age
                dx = sx - b.x
                dy = sy - b.y
                dist = math.hypot(dx, dy)
                if dist > 0.5:
                    diff = dist - prog * b.speed
                    wave = math.exp(-(diff * diff) / (b.width * b.width)) * (1.0 - prog) ** 2
                    sx += dx / dist * wave * 40.0
                    sy += dy / dist * wave * 40.0
                    flash += wave

            depth = max(0.15, min(1.25, 20.0 / ahead))
            twinkle = 1.0 - self.twinkle_amount * 0.6 * (0.5 + 0.5 * math.sin(t * (6.0 + p.r1 * 12.0) + p.r3 * 40.0))
            bright = min(1.0, depth * depth * twinkle * (1.0 + flash * 1.5) * fade)
            level = int(bright * levels + 0.5)
            if level <= 0:
                continue

            rad = p.size * depth * (1.0 + min(flash, 1.0) * 0.5)
            r = 1
            for cand in self.RADII:
                if rad >= cand - 0.5:
                    r = cand
            spr = sprites[(r, p.color_idx, level)]
            half = spr.get_width() // 2
            surface.blit(spr, (int(sx) - half, int(sy) - half), special_flags=pygame.BLEND_ADD)
