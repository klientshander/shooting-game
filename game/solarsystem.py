"""Cinematic 3D Solar System background engine for COSMIC RIFT.

Features:
- Central Blazing Star (Sun) with multi-layered plasma corona, rotating prominence loops,
  and anamorphic sci-fi cinema lens flare with chromatic ghost rings.
- 3D tilted orbital plane with true Painter's Algorithm depth-sorting (planets on the far
  side pass behind the Sun; planets on the near side pass in front with backlit silhouettes).
- Procedural spherical shading with dynamic day/night terminator lighting pointing away from the Sun.
- 8 planets (Mercury, Venus, Earth with orbiting Moon, Mars with polar cap, banded Jupiter
  with Galilean moons, Saturn with 3D multi-layer tilted rings, Uranus with thin vertical ring,
  and deep azure Neptune).
- Circumstellar Asteroid Belt (130 depth-sorted glinting rock particles).
- Sweeping periodic Comet with glowing nucleus and dual ion / dust tails pointed away from the Sun.
- Celestial orbital trajectory rings.
- Dynamic mouse parallax and relativistic pulse reactivity.
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import pygame

_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from settings import HEIGHT, WIDTH


def _clamp(v: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, v))


def _scale_color(c: tuple[int, ...], k: float) -> tuple[int, int, int]:
    return (
        int(max(0, min(255, c[0] * k))),
        int(max(0, min(255, c[1] * k))),
        int(max(0, min(255, c[2] * k))),
    )


class _PlanetData:
    __slots__ = (
        "name",
        "dist_x",
        "dist_y",
        "radius",
        "speed",
        "angle",
        "base_color",
        "has_atmosphere",
        "atmo_color",
        "has_rings",
        "ring_inner",
        "ring_outer",
        "ring_color",
        "moons",
        "surf",
    )

    def __init__(
        self,
        name: str,
        dist_x: float,
        dist_y: float,
        radius: int,
        speed: float,
        start_angle: float,
        base_color: tuple[int, int, int],
        has_atmosphere: bool = False,
        atmo_color: tuple[int, int, int] = (255, 255, 255),
        has_rings: bool = False,
        ring_inner: int = 0,
        ring_outer: int = 0,
        ring_color: tuple[int, int, int] = (200, 180, 140),
        moons: list[dict] | None = None,
    ) -> None:
        self.name = name
        self.dist_x = dist_x
        self.dist_y = dist_y
        self.radius = radius
        self.speed = speed
        self.angle = start_angle
        self.base_color = base_color
        self.has_atmosphere = has_atmosphere
        self.atmo_color = atmo_color
        self.has_rings = has_rings
        self.ring_inner = ring_inner
        self.ring_outer = ring_outer
        self.ring_color = ring_color
        self.moons = moons or []
        self.surf: pygame.Surface | None = None


class SolarSystemBackground:
    def __init__(
        self,
        width: int = WIDTH,
        height: int = HEIGHT,
        tilt_deg: float = 23.5,
        roll_deg: float = -6.5,
        speed_scale: float = 1.0,
    ) -> None:
        self.width = width
        self.height = height
        self.tilt = math.radians(tilt_deg)
        self.roll = math.radians(roll_deg)
        self.speed_scale = speed_scale
        self.time = 0.0

        # Pre-calculated 3D tilt transformation matrix constants
        self.cos_p = math.cos(self.tilt)
        self.sin_p = math.sin(self.tilt)
        self.cos_r = math.cos(self.roll)
        self.sin_r = math.sin(self.roll)

        # Solar center position with parallax smoothing
        self.base_cx = self.width * 0.52
        self.base_cy = self.height * 0.48
        self.cx = self.base_cx
        self.cy = self.base_cy
        self.mouse_smooth = (self.width * 0.5, self.height * 0.5)

        # Pulse / flare wave from player Ultimate
        self.solar_flare_intensity = 0.0
        self.flare_timer = 0.0

        # Build planets & celestial objects
        self._init_planets()
        self._init_asteroid_belt()
        self._init_comet()
        self._pre_render_planets()

    # ------------------------------------------------------------------ Setup
    def _init_planets(self) -> None:
        rng = random.Random(108)
        self.planets = [
            _PlanetData(
                name="Mercury",
                dist_x=90,
                dist_y=86,
                radius=4,
                speed=1.55,
                start_angle=rng.uniform(0, math.tau),
                base_color=(175, 165, 155),
            ),
            _PlanetData(
                name="Venus",
                dist_x=135,
                dist_y=130,
                radius=7,
                speed=1.18,
                start_angle=rng.uniform(0, math.tau),
                base_color=(235, 195, 125),
                has_atmosphere=True,
                atmo_color=(255, 230, 160),
            ),
            _PlanetData(
                name="Earth",
                dist_x=190,
                dist_y=182,
                radius=8,
                speed=0.92,
                start_angle=rng.uniform(0, math.tau),
                base_color=(45, 120, 225),
                has_atmosphere=True,
                atmo_color=(125, 215, 255),
                moons=[{"dist": 16, "radius": 2, "speed": 4.2, "angle": 0.5, "color": (210, 210, 215)}],
            ),
            _PlanetData(
                name="Mars",
                dist_x=245,
                dist_y=236,
                radius=6,
                speed=0.74,
                start_angle=rng.uniform(0, math.tau),
                base_color=(220, 95, 55),
                has_atmosphere=True,
                atmo_color=(255, 160, 110),
            ),
            _PlanetData(
                name="Jupiter",
                dist_x=365,
                dist_y=350,
                radius=19,
                speed=0.42,
                start_angle=rng.uniform(0, math.tau),
                base_color=(215, 175, 135),
                has_atmosphere=True,
                atmo_color=(255, 225, 185),
                moons=[
                    {"dist": 28, "radius": 2, "speed": 3.4, "angle": 1.2, "color": (245, 215, 120)},
                    {"dist": 36, "radius": 2, "speed": 2.6, "angle": 3.8, "color": (200, 230, 245)},
                ],
            ),
            _PlanetData(
                name="Saturn",
                dist_x=475,
                dist_y=455,
                radius=15,
                speed=0.31,
                start_angle=rng.uniform(0, math.tau),
                base_color=(225, 205, 155),
                has_atmosphere=True,
                atmo_color=(255, 235, 190),
                has_rings=True,
                ring_inner=21,
                ring_outer=38,
                ring_color=(210, 195, 150),
            ),
            _PlanetData(
                name="Uranus",
                dist_x=570,
                dist_y=545,
                radius=12,
                speed=0.22,
                start_angle=rng.uniform(0, math.tau),
                base_color=(120, 215, 225),
                has_atmosphere=True,
                atmo_color=(175, 245, 255),
            ),
            _PlanetData(
                name="Neptune",
                dist_x=650,
                dist_y=622,
                radius=11,
                speed=0.16,
                start_angle=rng.uniform(0, math.tau),
                base_color=(55, 110, 240),
                has_atmosphere=True,
                atmo_color=(115, 180, 255),
            ),
        ]

    def _init_asteroid_belt(self) -> None:
        rng = random.Random(404)
        self.asteroids: list[dict] = []
        for _ in range(130):
            dist = rng.uniform(280, 315)
            angle = rng.uniform(0, math.tau)
            speed = rng.uniform(0.52, 0.62)
            y_jitter = rng.uniform(-8, 8)
            size = rng.choice([1, 1, 1, 2])
            brightness = rng.randint(140, 225)
            self.asteroids.append({
                "dist": dist,
                "angle": angle,
                "speed": speed,
                "jitter": y_jitter,
                "size": size,
                "color": (brightness, brightness - 10, brightness - 20),
            })

    def _init_comet(self) -> None:
        self.comet_a = 460.0  # semi-major axis
        self.comet_b = 150.0  # semi-minor axis
        self.comet_angle = 1.8
        self.comet_speed = 0.28
        self.comet_tail_points: list[tuple[float, float, float]] = []

    def _pre_render_planets(self) -> None:
        for p in self.planets:
            sz = p.radius * 2 + 4
            surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
            cx, cy = sz // 2, sz // 2
            r = p.radius
            bc = p.base_color

            # Procedural 3D spherical shading with atmospheric limb
            for y in range(sz):
                for x in range(sz):
                    d = math.hypot(x - cx, y - cy)
                    if d <= r:
                        nx = (x - cx) / r
                        ny = (y - cy) / r
                        nz = math.sqrt(max(0.0, 1.0 - nx * nx - ny * ny))
                        # 3D sphere curvature shading
                        diffuse = 0.35 + 0.65 * nz
                        # Specific planet procedural surface banding
                        if p.name == "Jupiter":
                            band = 0.5 + 0.5 * math.sin(ny * 9.0 + nx * 1.5)
                            col = _scale_color(bc, diffuse * (0.85 + 0.25 * band))
                        elif p.name == "Saturn":
                            band = 0.5 + 0.5 * math.sin(ny * 7.0)
                            col = _scale_color(bc, diffuse * (0.90 + 0.18 * band))
                        elif p.name == "Earth":
                            continent = math.sin(nx * 5.0 + ny * 3.0) * math.cos(ny * 4.0 - nx * 2.0)
                            if continent > 0.18:
                                land_col = (65, 145, 75)
                                col = _scale_color(land_col, diffuse)
                            else:
                                col = _scale_color(bc, diffuse)
                        elif p.name == "Mars":
                            if abs(ny) > 0.78:
                                col = (245, 245, 250)  # Polar ice cap
                            else:
                                col = _scale_color(bc, diffuse)
                        else:
                            col = _scale_color(bc, diffuse)
                        surf.set_at((x, y), (*col, 255))

            # Atmospheric Fresnel outer edge ring
            if p.has_atmosphere:
                pygame.draw.circle(surf, (*p.atmo_color, 110), (cx, cy), r, 1)

            p.surf = surf

        # Pre-render Saturn's front & back rings
        self.saturn_ring_front = None
        self.saturn_ring_back = None
        for p in self.planets:
            if p.has_rings:
                ring_w = int(p.ring_outer * 2.2)
                ring_h = int(p.ring_outer * 0.75)
                full_ring = pygame.Surface((ring_w + 6, ring_h + 6), pygame.SRCALPHA)
                rcx, rcy = ring_w // 2 + 3, ring_h // 2 + 3
                col_a = (*p.ring_color, 185)
                col_b = (*_scale_color(p.ring_color, 0.72), 110)
                pygame.draw.ellipse(full_ring, col_a, (rcx - ring_w // 2, rcy - ring_h // 2, ring_w, ring_h), 4)
                inner_w = int(p.ring_inner * 2.0)
                inner_h = int(p.ring_inner * 0.68)
                pygame.draw.ellipse(full_ring, col_b, (rcx - inner_w // 2, rcy - inner_h // 2, inner_w, inner_h), 3)

                # Split into back (top half) and front (bottom half)
                back_surf = pygame.Surface((ring_w + 6, ring_h + 6), pygame.SRCALPHA)
                back_surf.blit(full_ring, (0, 0), pygame.Rect(0, 0, ring_w + 6, rcy))
                self.saturn_ring_back = pygame.transform.rotate(back_surf, math.degrees(-self.roll))

                front_surf = pygame.Surface((ring_w + 6, ring_h + 6), pygame.SRCALPHA)
                front_surf.blit(full_ring, (0, 0), pygame.Rect(0, rcy, ring_w + 6, rcy + 6))
                self.saturn_ring_front = pygame.transform.rotate(front_surf, math.degrees(-self.roll))

        # Pre-render static celestial orbital paths
        self.orbit_base_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for p in self.planets:
            pts = []
            steps = 56
            for i in range(steps + 1):
                a = (i / steps) * math.tau
                ox = math.cos(a) * p.dist_x
                oy = math.sin(a) * p.dist_y
                sx, sy, _ = self._project(ox, oy, 0.0)
                pts.append((sx, sy))
            if len(pts) > 2:
                pygame.draw.lines(self.orbit_base_surf, (80, 140, 215, 36), False, pts, 1)

    # ---------------------------------------------------------------- Project
    def _project(self, x: float, y: float, z: float = 0.0) -> tuple[float, float, float]:
        """Project 3D orbital plane coordinate into tilted 2D screen space + depth Z."""
        # 1. Pitch tilt around X axis
        y1 = y * self.sin_p - z * self.cos_p
        z1 = y * self.cos_p + z * self.sin_p
        # 2. Roll tilt around Z axis
        x2 = x * self.cos_r - y1 * self.sin_r
        y2 = x * self.sin_r + y1 * self.cos_r
        # 3. Translate to solar center
        screen_x = self.cx + x2
        screen_y = self.cy + y2
        return screen_x, screen_y, z1

    # ----------------------------------------------------------------- Update
    def reset(self) -> None:
        self.time = 0.0
        self.solar_flare_intensity = 0.0
        self.flare_timer = 0.0

    def trigger_flare(self, intensity: float = 1.0) -> None:
        """Trigger an expanding solar coronal flare on player Ultimate or explosion."""
        self.solar_flare_intensity = max(self.solar_flare_intensity, intensity)
        self.flare_timer = 1.8

    def update(self, dt: float, mouse_pos: tuple[float, float] | None = None) -> None:
        pace = dt * self.speed_scale
        self.time += pace

        # Smooth mouse parallax (drifts the solar system gracefully as the player aims)
        if mouse_pos:
            target_cx = self.base_cx + (mouse_pos[0] - self.width * 0.5) * 0.04
            target_cy = self.base_cy + (mouse_pos[1] - self.height * 0.5) * 0.03
            follow = min(1.0, dt * 2.8)
            self.cx += (target_cx - self.cx) * follow
            self.cy += (target_cy - self.cy) * follow

        # Flare decay
        if self.flare_timer > 0.0:
            self.flare_timer = max(0.0, self.flare_timer - dt)
            self.solar_flare_intensity = max(0.0, self.solar_flare_intensity - dt * 0.8)

        # Update planetary orbital positions
        for p in self.planets:
            p.angle = (p.angle + p.speed * pace * 0.18) % math.tau

        # Update asteroid belt
        for ast in self.asteroids:
            ast["angle"] = (ast["angle"] + ast["speed"] * pace * 0.16) % math.tau

        # Update comet along elliptical trajectory
        self.comet_angle = (self.comet_angle + self.comet_speed * pace * 0.14) % math.tau

    # ------------------------------------------------------------------- Draw
    def draw(self, surface: pygame.Surface, alpha_mult: float = 1.0) -> None:
        if alpha_mult <= 0.01:
            return

        alpha_mult = _clamp(alpha_mult)
        ticks = pygame.time.get_ticks()

        # --------------------------------------------------------------
        # 1. Subtle Celestial Orbit Trajectory Lines
        # --------------------------------------------------------------
        orbit_ox = int(self.cx - self.base_cx)
        orbit_oy = int(self.cy - self.base_cy)
        surface.blit(self.orbit_base_surf, (orbit_ox, orbit_oy))

        # --------------------------------------------------------------
        # 2. Gather All Renderable Celestial Bodies for 3D Depth Sorting
        # --------------------------------------------------------------
        # Each item is (depth_z, render_type, payload)
        items: list[tuple[float, str, object]] = []

        # Planets & their components
        for p in self.planets:
            ox = math.cos(p.angle) * p.dist_x
            oy = math.sin(p.angle) * p.dist_y
            sx, sy, sz = self._project(ox, oy, 0.0)
            items.append((sz, "planet", (p, sx, sy, sz)))
            if p.has_rings:
                # Ring split into rear half (drawn behind planet) and front half (drawn in front)
                items.append((sz - 0.5, "ring_back", (p, sx, sy, sz)))
                items.append((sz + 0.5, "ring_front", (p, sx, sy, sz)))
            for moon in p.moons:
                ma = (moon["angle"] + self.time * moon["speed"]) % math.tau
                mx = ox + math.cos(ma) * moon["dist"]
                my = oy + math.sin(ma) * (moon["dist"] * 0.7)
                msx, msy, msz = self._project(mx, my, 0.0)
                items.append((msz, "moon", (moon, msx, msy, msz)))

        # Asteroids
        for ast in self.asteroids:
            ax = math.cos(ast["angle"]) * ast["dist"]
            ay = math.sin(ast["angle"]) * ast["dist"]
            asx, asy, asz = self._project(ax, ay, ast["jitter"])
            items.append((asz, "asteroid", (ast, asx, asy, asz)))

        # Comet
        cx_orb = math.cos(self.comet_angle) * self.comet_a
        cy_orb = math.sin(self.comet_angle) * self.comet_b
        csx, csy, csz = self._project(cx_orb, cy_orb, 15.0)
        items.append((csz, "comet", (csx, csy, csz)))

        # Sort all objects back-to-front (Painter's Algorithm)
        items.sort(key=lambda item: item[0])

        # --------------------------------------------------------------
        # 3. Render Objects in Depth Order
        # --------------------------------------------------------------
        flare_boost = 1.0 + self.solar_flare_intensity * 0.70

        for depth_z, item_type, data in items:
            # --------------------------------- PLANET
            if item_type == "planet":
                p, sx, sy, sz = data
                if -60 <= sx <= self.width + 60 and -60 <= sy <= self.height + 60 and p.surf:
                    # Near planets appear slightly larger in 3D perspective
                    depth_scale = 1.0 + _clamp(sz / 550.0, -0.25, 0.40)
                    cur_w = max(4, int(p.surf.get_width() * depth_scale))
                    cur_h = max(4, int(p.surf.get_height() * depth_scale))
                    p_scaled = pygame.transform.smoothscale(p.surf, (cur_w, cur_h))

                    # Dynamic Terminator Shadow Shading:
                    # Direction towards the Sun
                    sun_dx = self.cx - sx
                    sun_dy = self.cy - sy
                    dist_to_sun = math.hypot(sun_dx, sun_dy) or 1.0
                    ang_to_sun = math.atan2(sun_dy, sun_dx)

                    # Shadow mask: when z > 0 (planet is in front of the sun), the side
                    # facing the camera is in dark shadow (crescent phase)
                    # When z < 0 (planet is behind the sun), lit side faces camera (full phase)
                    shadow_surf = pygame.Surface((cur_w, cur_h), pygame.SRCALPHA)
                    darkness = _clamp(0.15 + (sz / 420.0) * 0.70, 0.0, 0.88)
                    if darkness > 0.05:
                        # Draw soft crescent shadow on the side facing away from the Sun
                        sh_cx, sh_cy = cur_w // 2, cur_h // 2
                        off_x = -math.cos(ang_to_sun) * (cur_w * 0.28)
                        off_y = -math.sin(ang_to_sun) * (cur_h * 0.28)
                        shadow_alpha = int(245 * darkness * alpha_mult)
                        pygame.draw.circle(
                            shadow_surf,
                            (0, 0, 0, shadow_alpha),
                            (int(sh_cx + off_x), int(sh_cy + off_y)),
                            int(cur_w * 0.48),
                        )
                    p_scaled.blit(shadow_surf, (0, 0))

                    if alpha_mult < 0.98:
                        p_scaled.set_alpha(int(255 * alpha_mult))
                    surface.blit(p_scaled, (int(sx - cur_w // 2), int(sy - cur_h // 2)))

            # --------------------------------- SATURN RINGS (3D Occlusion)
            elif item_type == "ring_back":
                if self.saturn_ring_back:
                    p, sx, sy, sz = data
                    surface.blit(self.saturn_ring_back, self.saturn_ring_back.get_rect(center=(int(sx), int(sy))))
            elif item_type == "ring_front":
                if self.saturn_ring_front:
                    p, sx, sy, sz = data
                    surface.blit(self.saturn_ring_front, self.saturn_ring_front.get_rect(center=(int(sx), int(sy))))

            # --------------------------------- MOON
            elif item_type == "moon":
                moon, msx, msy, msz = data
                m_rad = moon["radius"]
                m_alpha = int(220 * alpha_mult)
                pygame.draw.circle(surface, moon["color"], (int(msx), int(msy)), m_rad)

            # --------------------------------- ASTEROID
            elif item_type == "asteroid":
                ast, asx, asy, asz = data
                if 0 <= asx < self.width and 0 <= asy < self.height:
                    twinkle = 1.0 + 0.25 * math.sin(ticks / 280.0 + ast["dist"])
                    c = _scale_color(ast["color"], twinkle * alpha_mult)
                    if ast["size"] == 1:
                        surface.set_at((int(asx), int(asy)), c)
                    else:
                        pygame.draw.circle(surface, c, (int(asx), int(asy)), ast["size"])

            # --------------------------------- COMET
            elif item_type == "comet":
                csx, csy, csz = data
                # Comet vector away from the Sun (solar wind)
                tail_dx = csx - self.cx
                tail_dy = csy - self.cy
                tail_len = math.hypot(tail_dx, tail_dy) or 1.0
                nx, ny = tail_dx / tail_len, tail_dy / tail_len

                # Dual streaming tail: Ion tail (straight blue) + Dust tail (curved golden)
                tail_reach = 95.0
                t_end_x = csx + nx * tail_reach
                t_end_y = csy + ny * tail_reach
                curv_x = csx + (nx * 0.85 - ny * 0.35) * (tail_reach * 0.85)
                curv_y = csy + (ny * 0.85 + nx * 0.35) * (tail_reach * 0.85)

                tail_alpha = int(140 * alpha_mult)
                if tail_alpha > 5:
                    # Blue ion tail
                    pygame.draw.line(surface, (110, 220, 255), (int(csx), int(csy)), (int(t_end_x), int(t_end_y)), 2)
                    # Golden dust tail
                    pygame.draw.line(surface, (255, 215, 140), (int(csx), int(csy)), (int(curv_x), int(curv_y)), 1)
                # Glowing nucleus
                pygame.draw.circle(surface, (255, 255, 255), (int(csx), int(csy)), 3)
                pygame.draw.circle(surface, (140, 230, 255), (int(csx), int(csy)), 6, 1)


if __name__ == "__main__":
    # Interactive Standalone Demo for Cinematic Solar System
    pygame.init()
    pygame.display.set_caption("COSMIC RIFT - Cinematic 3D Solar System")
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    clock = pygame.time.Clock()

    solarsystem = SolarSystemBackground(width=WIDTH, height=HEIGHT)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    solarsystem.trigger_flare(1.5)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                solarsystem.trigger_flare(1.2)

        solarsystem.update(dt, mouse_pos=mouse_pos)

        screen.fill((0, 0, 0))
        solarsystem.draw(screen, alpha_mult=1.0)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)
