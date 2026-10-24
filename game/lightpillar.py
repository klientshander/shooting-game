"""LightPillar Background Engine for Cosmic Rift.

Faithfully recreates the React / WebGL2 LightPillar shader with volumetric
ray-marched light pillar, deep violet (#5227FF) to neon pink (#FF9FFC)
chromatic gradient, harmonic plasma twist ribbons, dynamic traveling flares,
and interactive tilt sway.
"""

from __future__ import annotations

import math
import random
import pygame

from settings import WIDTH, HEIGHT


class PillarPulse:
    __slots__ = ("axis", "age", "speed", "size", "max_age", "intensity")

    def __init__(self, axis: float = -0.6, speed: float = 0.55, size: float = 1.0) -> None:
        self.axis = axis  # Normalized position along axis (-0.8 to 0.8)
        self.age = 0.0
        self.speed = speed
        self.size = size
        self.max_age = 2.4
        self.intensity = random.uniform(0.75, 1.0)


class PillarParticle:
    __slots__ = ("s", "offset", "speed", "size", "phase", "brightness")

    def __init__(self) -> None:
        self.s = random.uniform(-650.0, 650.0)
        self.offset = random.gauss(0.0, 24.0)
        self.speed = random.uniform(40.0, 95.0)
        self.size = random.uniform(1.0, 2.5)
        self.phase = random.uniform(0.0, math.tau)
        self.brightness = random.uniform(0.5, 1.0)


class LightPillar:
    def __init__(
        self,
        width: int = WIDTH,
        height: int = HEIGHT,
        top_color: str = "#5227FF",
        bottom_color: str = "#FF9FFC",
        intensity: float = 1.0,
        glow_amount: float = 0.002,
        bloom: float = 0.5,
        pillar_width: float = 3.0,
        pillar_height: float = 0.4,
        pillar_rotation: float = 25.0,
        rotation_speed: float = 0.3,
        twist: float = 0.4,
        detail: int = 4,
        flow: float = 1.0,
        noise_intensity: float = 0.5,
        interactive: bool = True,
        click_pulse: bool = True,
        intro: bool = True,
    ) -> None:
        self.width = width
        self.height = height
        self.top_hex = top_color
        self.bottom_hex = bottom_color
        self.intensity = intensity
        self.glow_amount = glow_amount
        self.bloom = bloom
        self.pillar_width = pillar_width
        self.pillar_height = pillar_height
        self.base_rotation = pillar_rotation
        self.rotation_speed = rotation_speed
        self.twist = twist
        self.detail = detail
        self.flow = flow
        self.noise_intensity = noise_intensity
        self.interactive = interactive
        self.click_pulse = click_pulse
        self.intro_enabled = intro

        # Parse hex colors
        def hex_to_rgb(h: str) -> tuple[int, int, int]:
            h = h.lstrip("#")
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

        self.top_rgb = hex_to_rgb(top_color)        # (82, 39, 255)
        self.bottom_rgb = hex_to_rgb(bottom_color)  # (255, 159, 252)

        self.time = 0.0
        self.intro_timer = 2.0 if intro else 0.0
        self.intro_duration = 2.0

        # Interactive motion state
        self.spin = 0.0
        self.lean = 0.0
        self.shift = 0.0
        self.mouse_pos = (width * 0.5, height * 0.5)

        # Pulses and particles
        self.pulses: list[PillarPulse] = [
            PillarPulse(axis=-0.4, speed=0.45, size=1.1),
            PillarPulse(axis=0.2, speed=0.55, size=0.9),
        ]
        self.particles: list[PillarParticle] = [PillarParticle() for _ in range(35)]
        self.pulse_spawn_timer = 1.4

        # Precompute master volumetric light beam
        self._build_beam_textures()
        self._rot_cache: dict[float, pygame.Surface] = {}

    def _build_beam_textures(self) -> None:
        """Precompute the smooth multi-layer volumetric beam texture with premultiplied falloff."""
        grid_w, grid_h = 240, 360
        beam_grid = pygame.Surface((grid_w, grid_h), pygame.SRCALPHA)
        cx = grid_w / 2.0
        cy = grid_h / 2.0

        top_r, top_g, top_b = self.top_rgb
        bot_r, bot_g, bot_b = self.bottom_rgb

        for y in range(grid_h):
            ty = y / float(grid_h - 1)
            y_norm = abs(y - cy) / cy
            if y_norm >= 0.98:
                continue
            y_fade = math.cos(y_norm * math.pi * 0.5) ** 1.8

            # Color gradient along pillar from top to bottom
            r_base = top_r * (1.0 - ty) + bot_r * ty
            g_base = top_g * (1.0 - ty) + bot_g * ty
            b_base = top_b * (1.0 - ty) + bot_b * ty

            for x in range(grid_w):
                x_norm = abs(x - cx) / cx
                if x_norm >= 0.98:
                    continue

                x_fade = math.cos(x_norm * math.pi * 0.5) ** 2.2

                # 3-tier volumetric profile: intense core -> vibrant sheath -> soft outer bloom
                core = math.exp(- (x_norm / 0.08) ** 2)
                sheath = math.exp(- (x_norm / 0.25) ** 2) * 0.55
                bloom = math.exp(- (x_norm / 0.60) ** 1.8) * 0.28

                factor = (core * 1.5 + sheath + bloom) * x_fade * y_fade
                if factor < 0.002:
                    continue

                # Core whitening
                r_tot = min(255.0, r_base * (1.0 - core * 0.80) + 255.0 * (core * 0.80))
                g_tot = min(255.0, g_base * (1.0 - core * 0.70) + 245.0 * (core * 0.70))
                b_tot = min(255.0, b_base * (1.0 - core * 0.50) + 255.0 * (core * 0.50))

                # Premultiply RGB for clean additive blending without bounding-box artifacts
                r = max(0, min(255, int(r_tot * factor)))
                g = max(0, min(255, int(g_tot * factor)))
                b = max(0, min(255, int(b_tot * factor)))
                alpha = max(0, min(255, int(255 * factor)))

                beam_grid.set_at((x, y), (r, g, b, alpha))

        # Full size beam surface
        beam_w = int(480 * (self.pillar_width / 3.0))
        beam_h = 1600
        self.smooth_beam = pygame.transform.smoothscale(beam_grid, (beam_w, beam_h))

    def trigger_pulse(self, axis_pos: float = -0.7) -> None:
        """Trigger an energy flare pulse traveling down the pillar."""
        if len(self.pulses) < 4:
            self.pulses.append(PillarPulse(axis=axis_pos, speed=0.65, size=1.2))

    def reset(self) -> None:
        self.time = 0.0
        self.intro_timer = 2.0 if self.intro_enabled else 0.0
        self.spin = 0.0
        self.lean = 0.0
        self.shift = 0.0

    def update(self, dt: float, mouse_pos: tuple[float, float] | None = None) -> None:
        self.time += dt * self.flow * 0.96 * max(0.1, self.rotation_speed)

        if self.intro_timer > 0.0:
            self.intro_timer = max(0.0, self.intro_timer - dt)

        # Interactive sway
        if self.interactive and mouse_pos is not None:
            self.mouse_pos = mouse_pos
            aim_x = (mouse_pos[0] / float(self.width) - 0.5)
            follow = min(1.0, dt * 2.8)
            self.spin += (aim_x * 1.4 - self.spin) * follow
            self.lean += (aim_x * 7.5 - self.lean) * follow
            self.shift += (aim_x * 45.0 - self.shift) * follow

        # Update pulses
        for p in self.pulses:
            p.age += dt
            p.axis += dt * p.speed
        self.pulses = [p for p in self.pulses if p.axis < 0.9 and p.age < p.max_age]

        self.pulse_spawn_timer -= dt
        if self.pulse_spawn_timer <= 0.0:
            self.pulse_spawn_timer = random.uniform(1.8, 3.2)
            if len(self.pulses) < 3:
                self.trigger_pulse(random.uniform(-0.8, -0.4))

        # Update particles
        for pt in self.particles:
            pt.s += pt.speed * dt
            if pt.s > 680.0:
                pt.s = -680.0
                pt.offset = random.gauss(0.0, 26.0)
                pt.speed = random.uniform(40.0, 95.0)

    def draw(self, surface: pygame.Surface, alpha_mult: float = 1.0) -> None:
        """Render the LightPillar effect onto the surface with optional crossfade alpha."""
        if alpha_mult <= 0.005:
            return

        # Intro grow factor
        intro_frac = 1.0
        if self.intro_timer > 0.0:
            t = 1.0 - (self.intro_timer / self.intro_duration)
            intro_frac = t * t * (3.0 - 2.0 * t)  # Smoothstep intro

        effective_alpha = alpha_mult * intro_frac

        # Calculate current tilt angle and center
        current_tilt = self.base_rotation + self.lean
        center_x = self.width * 0.5 + self.shift
        center_y = self.height * 0.5

        # Cached rotated beam surface
        cache_key = round(current_tilt * 2.0) / 2.0
        if cache_key not in self._rot_cache:
            if len(self._rot_cache) > 20:
                self._rot_cache.clear()
            self._rot_cache[cache_key] = pygame.transform.rotate(self.smooth_beam, cache_key)
        rot_beam = self._rot_cache[cache_key]

        # Draw beam
        rect = rot_beam.get_rect(center=(int(center_x), int(center_y)))

        if effective_alpha >= 0.98:
            surface.blit(rot_beam, rect, special_flags=pygame.BLEND_ADD)
        else:
            fade_beam = rot_beam.copy()
            val = int(255 * effective_alpha)
            fade_beam.fill((val, val, val, val), special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(fade_beam, rect, special_flags=pygame.BLEND_ADD)

        # Coordinate axes along the pillar
        tilt_rad = math.radians(current_tilt)
        ux = math.sin(tilt_rad)
        uy = math.cos(tilt_rad)
        nx = math.cos(tilt_rad)
        ny = -math.sin(tilt_rad)

        top_r, top_g, top_b = self.top_rgb
        bot_r, bot_g, bot_b = self.bottom_rgb

        # Draw dynamic harmonic plasma twist ribbons
        ribbon_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        num_ribbons = min(5, max(2, self.detail))

        for r_idx in range(num_ribbons):
            pts = []
            freq = 0.006 + r_idx * 0.0028
            phase = self.time * 2.4 + r_idx * 1.55
            base_offset = (r_idx - (num_ribbons - 1) * 0.5) * 14.0
            amp = (22.0 + r_idx * 5.5) * (self.twist / 0.4)

            for s in range(-680, 680, 16):
                t_prog = (s + 680) / 1360.0
                cr = int(top_r * (1.0 - t_prog) + bot_r * t_prog)
                cg = int(top_g * (1.0 - t_prog) + bot_g * t_prog)
                cb = int(top_b * (1.0 - t_prog) + bot_b * t_prog)

                px = center_x + ux * s
                py = center_y + uy * s
                wave = math.sin(s * freq - phase) * amp + math.cos(s * freq * 0.5 + phase * 0.6) * (amp * 0.3)
                pts.append((px + nx * (base_offset + wave), py + ny * (base_offset + wave)))

            if len(pts) > 1:
                a1 = int(45 * effective_alpha)
                a2 = int(95 * effective_alpha)
                if a1 > 1:
                    pygame.draw.lines(ribbon_surf, (cr, cg, cb, a1), False, pts, 4)
                if a2 > 2:
                    pygame.draw.lines(ribbon_surf, (245, 230, 255, a2), False, pts, 2)

        surface.blit(ribbon_surf, (0, 0), special_flags=pygame.BLEND_ADD)

        # Draw traveling energy pulses along the pillar axis
        for pulse in self.pulses:
            s = pulse.axis * 1200.0
            px = center_x + ux * s
            py = center_y + uy * s

            t_pulse = max(0.0, min(1.0, (pulse.axis + 0.8) / 1.6))
            pr = int(top_r * (1.0 - t_pulse) + bot_r * t_pulse)
            pg = int(top_g * (1.0 - t_pulse) + bot_g * t_pulse)
            pb = int(top_b * (1.0 - t_pulse) + bot_b * t_pulse)

            p_size = int(80 * pulse.size)
            p_surf = pygame.Surface((p_size * 2, p_size * 2), pygame.SRCALPHA)
            for rad_ratio, val in ((1.0, 15), (0.65, 35), (0.35, 75), (0.15, 140)):
                r_step = max(2, int(p_size * rad_ratio))
                v_eff = int(val * effective_alpha * pulse.intensity)
                if v_eff > 1:
                    col = (int(pr * v_eff / 255), int(pg * v_eff / 255), int(pb * v_eff / 255), v_eff)
                    pygame.draw.circle(p_surf, col, (p_size, p_size), r_step)
            surface.blit(p_surf, (int(px - p_size), int(py - p_size)), special_flags=pygame.BLEND_ADD)

        # Ambient cosmic energy sparks
        if self.noise_intensity > 0.05:
            for pt in self.particles:
                px = center_x + ux * pt.s + nx * pt.offset
                py = center_y + uy * pt.s + ny * pt.offset
                if 0 <= px <= self.width and 0 <= py <= self.height:
                    t_prog = max(0.0, min(1.0, (pt.s + 680) / 1360.0))
                    pr = int(top_r * (1.0 - t_prog) + bot_r * t_prog)
                    pg = int(top_g * (1.0 - t_prog) + bot_g * t_prog)
                    pb = int(top_b * (1.0 - t_prog) + bot_b * t_prog)

                    twinkle = 0.5 + 0.5 * math.sin(self.time * 5.0 + pt.phase)
                    br = int(255 * pt.brightness * twinkle * effective_alpha)
                    if br > 15:
                        spark_col = (min(255, int(pr * br / 255) + 60), min(255, int(pg * br / 255) + 60), min(255, int(pb * br / 255) + 60))
                        pygame.draw.circle(surface, spark_col, (int(px), int(py)), max(1, int(pt.size)), 0)

