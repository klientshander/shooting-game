"""Lightfall Background Engine for Cosmic Rift.

Faithfully recreates the React / WebGL2 Lightfall shader with squircle vault arch
projection, cascading pure white streaks (#ffffff), slate-blue (#94a3b8) ambient
illumination, mouse lens deflection, hold-to-warp hyperspace acceleration, and
smooth intro deceleration settle.
"""

from __future__ import annotations

import math
import random
import pygame


class LightfallStreak:
    __slots__ = (
        "u",
        "progress",
        "speed_factor",
        "length",
        "width",
        "twinkle_phase",
        "twinkle_speed",
        "brightness",
    )

    def __init__(
        self,
        u: float,
        progress: float,
        speed_factor: float,
        length: float,
        width: float,
    ) -> None:
        self.u = u
        self.progress = progress
        self.speed_factor = speed_factor
        self.length = length
        self.width = width
        self.twinkle_phase = random.uniform(0.0, math.tau)
        self.twinkle_speed = random.uniform(3.0, 7.0)
        self.brightness = random.uniform(0.85, 1.0)


class Lightfall:
    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        colors: list[str] | None = None,
        background_color: str = "#94a3b8",
        speed: float = 0.3,
        streak_count: int = 2,
        streak_width: float = 0.8,
        streak_length: float = 1.0,
        glow: float = 1.0,
        density: float = 0.6,
        twinkle: float = 0.3,
        zoom: float = 3.0,
        background_glow: float = 0.1,
        head_glow: float = 0.6,
        depth: float = 0.5,
        bloom: float = 0.35,
        mouse_interaction: bool = True,
        mouse_strength: float = 0.4,
        mouse_radius: float = 0.45,
        lens: float = 0.5,
        hold_to_warp: bool = True,
        intro: bool = True,
        fade: float = 0.0,
        light_mode: bool = False,
    ) -> None:
        self.width = width
        self.height = height
        self.colors = colors or ["#ffffff"]
        self.bg_hex = background_color
        self.base_speed = speed
        self.streak_count = streak_count
        self.streak_width = streak_width
        self.streak_length = streak_length
        self.glow = glow
        self.density = density
        self.twinkle = twinkle
        self.zoom = zoom
        self.background_glow = background_glow
        self.head_glow = head_glow
        self.depth = depth
        self.bloom = bloom
        self.mouse_interaction = mouse_interaction
        self.mouse_strength = mouse_strength
        self.mouse_radius = mouse_radius
        self.lens = lens
        self.hold_to_warp = hold_to_warp
        self.intro_enabled = intro
        self.fade = fade
        self.light_mode = light_mode

        # Parse slate-blue background color (#94a3b8 = 148, 163, 184)
        c_hex = self.bg_hex.lstrip("#")
        self.bg_rgb = tuple(int(c_hex[i : i + 2], 16) for i in (0, 2, 4))

        # Warp & intro animation state
        self.warp_factor: float = 1.0
        self.warp_target: float = 1.0
        self.intro_timer: float = 2.6 if self.intro_enabled else 0.0
        self.intro_duration: float = 2.6
        self.time: float = 0.0

        # Mouse tracking with smooth dampening
        self.mouse_pos: tuple[float, float] = (width * 0.5, height * 0.5)
        self.lens_pos: tuple[float, float] = (width * 0.5, height * 0.5)

        # Pre-allocated surfaces for maximum FPS
        self.overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._build_background_surface()
        self._build_glow_sprites()

        # Initialize streak particles
        self.streaks: list[LightfallStreak] = []
        self._init_streaks()

    def _build_background_surface(self) -> None:
        """Create sleek cosmic slate background with slate-blue top dome glow."""
        self.base_bg = pygame.Surface((self.width, self.height))
        # Deep cosmic slate vertical gradient
        for y in range(self.height):
            t = y / self.height
            r = int(14 + 10 * (1.0 - t))
            g = int(22 + 14 * (1.0 - t))
            b = int(36 + 22 * (1.0 - t))
            pygame.draw.line(self.base_bg, (r, g, b), (0, y), (self.width, y))

        # Top dome ambient illumination with #94a3b8 slate tint
        dome = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        cx, cy = self.width // 2, -60
        max_d = self.width * 0.75
        steps = 25
        for i in range(steps, 0, -1):
            r = int(max_d * (i / steps))
            norm = 1.0 - (i / steps)
            alpha = int(255 * self.background_glow * 1.5 * (norm ** 2.2))
            if alpha > 0:
                pygame.draw.circle(dome, (*self.bg_rgb, alpha), (cx, cy), r)
        self.base_bg.blit(dome, (0, 0))

    def _build_glow_sprites(self) -> None:
        """Build smooth Gaussian bloom sprite for streak heads."""
        self.glow_r = 7
        self.glow_surf = pygame.Surface(
            (self.glow_r * 2 + 1, self.glow_r * 2 + 1), pygame.SRCALPHA
        )
        for y in range(self.glow_r * 2 + 1):
            for x in range(self.glow_r * 2 + 1):
                d = math.hypot(x - self.glow_r, y - self.glow_r)
                if d <= self.glow_r:
                    norm = d / self.glow_r
                    alpha = int(160 * self.head_glow * ((1.0 - norm) ** 2.0))
                    self.glow_surf.set_at((x, y), (215, 235, 255, alpha))

    def _init_streaks(self) -> None:
        """Populate streaks across vault ceiling arch."""
        self.streaks.clear()
        num_columns = int(36 * self.density)
        total_streaks = num_columns * self.streak_count

        for _ in range(total_streaks):
            u = random.uniform(-0.98, 0.98)
            progress = random.uniform(0.0, 1.06)
            speed_var = random.uniform(0.85, 1.25)
            length = random.uniform(0.10, 0.26) * self.streak_length
            width = random.uniform(1.1, 1.9) * self.streak_width
            self.streaks.append(
                LightfallStreak(
                    u=u,
                    progress=progress,
                    speed_factor=speed_var,
                    length=length,
                    width=width,
                )
            )

    def trigger_warp_burst(self, duration: float = 2.0) -> None:
        """Surge streaks into hyperdrive warp (e.g. boss spawn or ultimate)."""
        self.intro_timer = duration
        self.intro_duration = duration

    def reset(self) -> None:
        """Reset streaks and re-trigger intro settle."""
        self._init_streaks()
        if self.intro_enabled:
            self.intro_timer = 2.6
            self.warp_factor = 4.5
        else:
            self.intro_timer = 0.0
            self.warp_factor = 1.0

    def update(
        self,
        dt: float,
        mouse_pos: tuple[float, float] | None = None,
        is_holding_warp: bool = False,
    ) -> None:
        """Advance simulation time, mouse lens center, and streak positions."""
        self.time += dt

        # Lens position dampening
        if mouse_pos is not None:
            self.mouse_pos = mouse_pos
            lx, ly = self.lens_pos
            mx, my = mouse_pos
            damp = min(1.0, dt * 14.0)
            self.lens_pos = (lx + (mx - lx) * damp, ly + (my - ly) * damp)

        # Intro warp-in deceleration curve (from ~5.2x down to 1.0x)
        intro_warp = 1.0
        if self.intro_timer > 0.0:
            self.intro_timer = max(0.0, self.intro_timer - dt)
            intro_frac = self.intro_timer / max(0.001, self.intro_duration)
            intro_warp = 1.0 + 4.2 * (intro_frac ** 2.4)

        # Hold-to-Warp acceleration
        if self.hold_to_warp and is_holding_warp:
            self.warp_target = 6.2
        else:
            self.warp_target = 1.0

        # Smooth lerp for warp factor
        warp_blend = min(1.0, dt * 6.5)
        self.warp_factor += (self.warp_target - self.warp_factor) * warp_blend

        current_warp = max(self.warp_factor, intro_warp)
        effective_speed = self.base_speed * current_warp

        # Move streaks
        for s in self.streaks:
            s.progress += dt * effective_speed * s.speed_factor * 0.82
            if s.progress > 1.15:
                s.progress = random.uniform(-0.16, -0.02)
                s.u = random.uniform(-0.98, 0.98)
                s.speed_factor = random.uniform(0.85, 1.25)

    def _project(
        self, u: float, t: float, lens_x: float, lens_y: float, reach_px: float
    ) -> tuple[float, float]:
        """Project arch coordinate (u, t) with vault ceiling curve and mouse lens deflection."""
        top_x = (u * 0.48 + 0.5) * self.width
        # Outward perspective widening towards viewer
        spread = 1.0 + 0.40 * (max(0.0, t) ** 1.35)
        raw_x = (top_x - self.width * 0.5) * spread + self.width * 0.5
        raw_y = -35.0 + t * (self.height + 95.0)

        # Mouse Lens deflection
        if self.mouse_interaction and self.lens > 0.0:
            dx = raw_x - lens_x
            dy = raw_y - lens_y
            dist_sq = dx * dx + dy * dy
            reach_sq = reach_px * reach_px
            if dist_sq < reach_sq:
                dist = math.sqrt(dist_sq) + 0.001
                norm_d = dist / reach_px
                deflection = (
                    math.exp(-0.5 * (norm_d * 2.2) ** 2)
                    * self.mouse_strength
                    * self.lens
                    * 40.0
                )
                raw_x += (dx / dist) * deflection
                raw_y += (dy / dist) * deflection

        return raw_x, raw_y

    def draw(
        self,
        surface: pygame.Surface,
        mouse_pos: tuple[float, float] | None = None,
        alpha_mult: float = 1.0,
    ) -> None:
        """Render the complete Lightfall scene onto the surface."""
        if alpha_mult <= 0.005:
            return

        # Clear alpha overlay
        self.overlay.fill((0, 0, 0, 0))

        lens_x, lens_y = self.lens_pos
        reach_px = self.width * self.mouse_radius
        warp_len_mult = 1.0 + (self.warp_factor - 1.0) * 1.5

        # 2. Draw falling luminous streaks
        for s in self.streaks:
            if s.progress < -0.05 or s.progress > 1.15:
                continue

            t_head = s.progress
            t_tail = max(0.0, s.progress - s.length * warp_len_mult)

            # Twinkle scintillation
            twinkle_val = 1.0
            if self.twinkle > 0.0:
                twinkle_val = 1.0 + self.twinkle * math.sin(
                    self.time * s.twinkle_speed + s.twinkle_phase
                )
            brightness = max(0.4, min(1.25, s.brightness * twinkle_val))

            steps = 6
            pts = [
                self._project(
                    s.u,
                    t_tail + (t_head - t_tail) * (i / float(steps)),
                    lens_x,
                    lens_y,
                    reach_px,
                )
                for i in range(steps + 1)
            ]

            # Draw multi-segment luminous streak
            for i in range(steps):
                frac = (i + 1) / float(steps)
                alpha_frac = frac ** 2.0

                # Outer soft slate-blue aura
                a_glow = int(160 * alpha_frac * brightness * self.glow)
                if a_glow > 2:
                    c_glow = (*self.bg_rgb, min(255, a_glow))
                    line_w_glow = max(1, int(s.width * 2.4 * alpha_frac))
                    pygame.draw.line(self.overlay, c_glow, pts[i], pts[i + 1], line_w_glow)

                # Inner brilliant white core
                a_core = int(245 * alpha_frac * brightness * self.glow)
                if a_core > 5:
                    c_core = (255, 255, 255, min(255, a_core))
                    line_w_core = max(1, int(s.width * alpha_frac))
                    pygame.draw.line(self.overlay, c_core, pts[i], pts[i + 1], line_w_core)

            # Leading head tip
            hx, hy = pts[-1]
            if -12 <= hx <= self.width + 12 and -12 <= hy <= self.height + 12:
                # Gaussian head bloom
                if self.head_glow > 0.0:
                    self.overlay.blit(
                        self.glow_surf,
                        (int(hx - self.glow_r), int(hy - self.glow_r)),
                    )
                # Pure white pinpoint spark
                pygame.draw.circle(
                    self.overlay,
                    (255, 255, 255, min(255, int(255 * brightness))),
                    (int(hx), int(hy)),
                    1,
                )

        # Composite streaks onto game canvas
        if alpha_mult >= 0.98:
            surface.blit(self.overlay, (0, 0))
        elif alpha_mult > 0.01:
            fade_overlay = self.overlay.copy()
            val = int(255 * alpha_mult)
            fade_overlay.fill((val, val, val, val), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(fade_overlay, (0, 0))

