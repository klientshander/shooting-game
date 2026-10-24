"""WebThreads animated background - a native Pygame port of React Bits <WebThreads />.

Self-contained (depends only on ``pygame``, ``math`` and ``random``) so it can be
used inside Cosmic Rift or in any other Pygame project.

How it works
------------
* Each thread is a curve sampled across the screen. Its vertical offset is a
  combination of:
    - a *lane* (where the thread sits inside the bundle),
    - a *pinch envelope* that periodically squeezes all lanes together, which
      creates the drifting "web knots" where threads meet,
    - two per-thread sine waves (the organic wobble),
    - a shared sway so the whole bundle flows like a fibre-optic cable.
* Rendering is purely additive on black RGB layers (no per-pixel alpha), so the
  glow is cheap and never produces bounding-box artifacts:
    1. A low-resolution glow layer (wide dim strokes + narrow bright strokes,
       plus an out-of-focus back layer for depth) is smooth-scaled up, which
       blurs it into a soft bloom.
    2. Crisp anti-aliased cores with a purple -> pink gradient, faint web
       "rungs" linking neighbouring threads, white glowing knots and light
       pulses travelling along the threads are drawn at full resolution.
    3. The finished layer is added onto the target surface with BLEND_ADD.
"""

from __future__ import annotations

import math
import random

import pygame

TAU = math.tau


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    h = value.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[float, float, float]:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def _scale(c, k: float) -> tuple[int, int, int]:
    return (
        max(0, min(255, int(c[0] * k))),
        max(0, min(255, int(c[1] * k))),
        max(0, min(255, int(c[2] * k))),
    )


class _Thread:
    __slots__ = ("lane", "phase", "freq", "speed", "amp", "tint", "width")

    def __init__(self, lane, phase, freq, speed, amp, tint, width):
        self.lane = lane
        self.phase = phase
        self.freq = freq
        self.speed = speed
        self.amp = amp
        self.tint = tint  # 0 = first colour, 1 = last colour
        self.width = width


class _Pulse:
    __slots__ = ("thread", "u", "speed", "size")

    def __init__(self, thread, u, speed, size):
        self.thread = thread
        self.u = u
        self.speed = speed
        self.size = size


class WebThreads:
    def __init__(
        self,
        width: int,
        height: int,
        colors=("#5227FF", "#FF9FFC"),
        core_color: str = "#FFFFFF",
        thread_count: int = 6,
        spread: float = 0.18,
        speed: float = 1.0,
        glow_intensity: float = 1.0,
        intensity: float = 1.0,
        node_frequency: float = 1.35,
        back_layer: bool = True,
        mouse_interaction: bool = True,
        mouse_strength: float = 0.22,
        samples: int = 96,
        glow_scale: int = 4,
        seed: int = 7,
    ) -> None:
        self.colors = [hex_to_rgb(c) for c in colors] or [(255, 255, 255)]
        self.core_rgb = hex_to_rgb(core_color)
        self.thread_count = max(1, int(thread_count))
        self.spread = spread
        self.speed = speed
        self.glow_intensity = glow_intensity
        self.intensity = intensity
        self.node_frequency = node_frequency
        self.back_layer = back_layer
        self.mouse_interaction = mouse_interaction
        self.mouse_strength = mouse_strength
        self.samples = max(16, int(samples))
        self.glow_scale = max(2, int(glow_scale))
        self._rng = random.Random(seed)

        self.time = 0.0
        self.mouse_target: tuple[float, float] | None = None
        self.mouse_smooth = (width * 0.5, height * 0.5)
        self.mouse_presence = 0.0

        self._build_threads()
        self._build_sprites()
        self.resize(width, height)

    # ------------------------------------------------------------------ setup
    def _build_threads(self) -> None:
        rng = self._rng
        n = self.thread_count
        self.threads: list[_Thread] = []
        self.back_threads: list[_Thread] = []
        for i in range(n):
            lane = 0.0 if n == 1 else (i / (n - 1)) * 2.0 - 1.0
            tint = 0.0 if n == 1 else i / (n - 1)
            self.threads.append(
                _Thread(
                    lane=lane,
                    phase=rng.uniform(0.0, TAU),
                    freq=rng.uniform(1.1, 2.1),
                    speed=rng.uniform(0.55, 1.05) * (1 if i % 2 == 0 else -1),
                    amp=rng.uniform(0.35, 0.6),
                    tint=tint,
                    width=2 if i in (n // 2 - 1, n // 2) else 1,
                )
            )
            # Out-of-focus depth layer: wider, slower, dimmer
            self.back_threads.append(
                _Thread(
                    lane=lane * 1.7,
                    phase=rng.uniform(0.0, TAU),
                    freq=rng.uniform(0.7, 1.3),
                    speed=rng.uniform(0.25, 0.5) * (-1 if i % 2 == 0 else 1),
                    amp=rng.uniform(0.5, 0.9),
                    tint=1.0 - tint,
                    width=1,
                )
            )
        self.pulses: list[_Pulse] = []
        for i in range(n):
            self.pulses.append(_Pulse(i, rng.random(), rng.uniform(0.08, 0.16), rng.uniform(0.8, 1.2)))

    def _build_sprites(self) -> None:
        """Pre-render additive (black-backed) radial glow sprites at several brightness levels."""
        self._sprite_levels = 8
        self._sprites: dict[tuple[int, int], pygame.Surface] = {}
        for radius in (6, 10, 16, 24):
            base = pygame.Surface((radius * 2 + 1, radius * 2 + 1))
            for y in range(radius * 2 + 1):
                for x in range(radius * 2 + 1):
                    d = math.hypot(x - radius, y - radius) / radius
                    if d < 1.0:
                        k = (1.0 - d) ** 2.2
                        base.set_at((x, y), _scale(self.core_rgb, k))
            for level in range(1, self._sprite_levels + 1):
                s = base.copy()
                v = int(255 * level / self._sprite_levels)
                s.fill((v, v, v), special_flags=pygame.BLEND_RGB_MULT)
                self._sprites[(radius, level)] = s

    def resize(self, width: int, height: int) -> None:
        self.width = max(1, int(width))
        self.height = max(1, int(height))
        gs = self.glow_scale
        self._glow = pygame.Surface((max(1, self.width // gs), max(1, self.height // gs)))
        self._layer = pygame.Surface((self.width, self.height))

    # ----------------------------------------------------------------- update
    def reset(self) -> None:
        self.time = 0.0

    def trigger_pulse(self) -> None:
        """Fire a burst of light pulses from the left edge along every thread."""
        for i in range(self.thread_count):
            self.pulses.append(_Pulse(i, 0.0, self._rng.uniform(0.35, 0.5), 1.4))
        if len(self.pulses) > self.thread_count * 3:
            self.pulses = self.pulses[-self.thread_count * 3:]

    def update(self, dt: float, mouse_pos: tuple[float, float] | None = None) -> None:
        self.time += dt * self.speed

        if self.mouse_interaction and mouse_pos is not None:
            mx, my = self.mouse_smooth
            follow = min(1.0, dt * 5.0)
            self.mouse_smooth = (mx + (mouse_pos[0] - mx) * follow, my + (mouse_pos[1] - my) * follow)
            self.mouse_presence += (1.0 - self.mouse_presence) * min(1.0, dt * 2.0)
        else:
            self.mouse_presence *= max(0.0, 1.0 - dt * 2.0)

        alive = []
        for p in self.pulses:
            p.u += p.speed * dt * self.speed
            if p.u <= 1.05:
                alive.append(p)
            elif p.size < 1.3:  # ambient pulses loop forever
                p.u = -0.05
                alive.append(p)
        self.pulses = alive

    # ------------------------------------------------------------------ curve
    def _curve(self, th: _Thread, t: float, spread_px: float, mouse) -> list[tuple[float, float]]:
        w, h = self.width, self.height
        cy = h * 0.5
        n = self.samples
        nf = self.node_frequency
        pts = []
        for k in range(n + 1):
            u = k / n
            x = -0.03 * w + u * 1.06 * w
            pinch = 0.5 + 0.5 * math.sin(TAU * u * nf - t * 0.35)
            env = 0.14 + 0.86 * pinch ** 1.6
            wave = math.sin(TAU * u * th.freq + t * th.speed + th.phase)
            wave2 = math.sin(TAU * u * th.freq * 0.53 - t * th.speed * 0.7 + th.phase * 1.7)
            sway = math.sin(TAU * u * 0.6 + t * 0.25) * 0.55 + math.sin(TAU * u * 1.3 - t * 0.18) * 0.25
            off = th.lane * env + (0.55 * wave + 0.3 * wave2) * (0.3 + 0.7 * env) * th.amp
            y = cy + spread_px * (off + sway)
            if mouse is not None:
                mx, my, strength, radius = mouse
                dx = (x - mx) / radius
                if -2.5 < dx < 2.5:
                    y += (my - y) * strength * math.exp(-dx * dx)
            pts.append((x, y))
        return pts

    def _sprite(self, radius: int, brightness: float):
        level = max(1, min(self._sprite_levels, int(round(brightness * self._sprite_levels))))
        return self._sprites[(radius, level)]

    # ------------------------------------------------------------------- draw
    def draw(self, surface: pygame.Surface, alpha_mult: float = 1.0) -> None:
        if surface.get_size() != (self.width, self.height):
            self.resize(*surface.get_size())

        k = max(0.0, min(1.0, alpha_mult)) * self.intensity
        if k <= 0.01:
            return

        t = self.time
        spread_px = self.height * self.spread
        gs = self.glow_scale
        glow_k = k * self.glow_intensity
        mouse = None
        if self.mouse_interaction and self.mouse_presence > 0.01:
            mouse = (
                self.mouse_smooth[0],
                self.mouse_smooth[1],
                self.mouse_strength * self.mouse_presence,
                self.width * 0.12,
            )

        c0 = self.colors[0]
        c1 = self.colors[-1]
        curves = [self._curve(th, t, spread_px, mouse) for th in self.threads]

        # ---- 1. low-res glow layer (blurred by smooth upscale)
        glow = self._glow
        glow.fill((0, 0, 0))
        if self.back_layer:
            for th in self.back_threads:
                pts = self._curve(th, t * 0.8, spread_px, None)
                col = _mix(c0, c1, th.tint)
                small = [(x / gs, y / gs) for x, y in pts]
                pygame.draw.lines(glow, _scale(col, 0.35 * glow_k), False, small, 3)
        for th, pts in zip(self.threads, curves):
            col = _mix(c0, c1, th.tint)
            small = [(x / gs, y / gs) for x, y in pts]
            pygame.draw.lines(glow, _scale(col, 0.45 * glow_k), False, small, 6)
            pygame.draw.lines(glow, _scale(col, 1.0 * glow_k), False, small, 2)

        # Soften the low-res strokes so the upscaled bloom has no stair-stepping.
        # Two cheap box-blur passes approximate a gaussian at a fraction of the cost.
        box_blur = getattr(pygame.transform, "box_blur", None)
        if box_blur is not None:
            glow = box_blur(box_blur(glow, 2), 1)

        layer = self._layer
        pygame.transform.smoothscale(glow, (self.width, self.height), layer)
        surface.blit(layer, (0, 0), special_flags=pygame.BLEND_ADD)

        # Crisp details go on their own black layer so they ADD to the glow
        # instead of overwriting it (which would leave dark fringes).
        layer.fill((0, 0, 0))

        # ---- 2. web rungs linking neighbouring threads
        n = self.samples
        step = max(4, n // 16)
        rung_reach = spread_px * 1.1
        for i in range(len(curves) - 1):
            a_pts, b_pts = curves[i], curves[i + 1]
            col = _mix(c0, c1, (i + 0.5) / max(1, len(curves) - 1))
            offset = (i * 3) % step
            for kk in range(offset, n - 2, step):
                for pa, pb in ((a_pts[kk], b_pts[kk + 2]), (b_pts[kk], a_pts[kk + 2])):
                    d = math.hypot(pa[0] - pb[0], pa[1] - pb[1])
                    if d < rung_reach:
                        b = (1.0 - d / rung_reach) ** 1.5 * 0.55 * k
                        if b > 0.03:
                            pygame.draw.aaline(layer, _scale(col, b), pa, pb)

        # ---- 3. crisp gradient cores
        chunks = 8
        per = max(2, n // chunks)
        for th, pts in zip(self.threads, curves):
            for c in range(0, n, per):
                seg = pts[c:c + per + 1]
                if len(seg) < 2:
                    continue
                u = (c + per * 0.5) / n
                drift = 0.5 + 0.5 * math.sin(TAU * u + t * 0.3 + th.phase)
                col = _mix(c0, c1, min(1.0, th.tint * 0.65 + drift * 0.35))
                bright = _mix(col, self.core_rgb, 0.35)
                if th.width > 1:
                    pygame.draw.lines(layer, _scale(col, 0.9 * k), False, seg, 2)
                pygame.draw.aalines(layer, _scale(bright, 0.95 * k), False, seg)

        # ---- 4. white glowing knots where the bundle pinches together
        nf = self.node_frequency
        base = t * 0.35 / TAU
        m = math.floor(-base + 0.25) - 1
        while True:
            u = (m - 0.25 + base) / nf
            m += 1
            if u > 1.02:
                break
            if u < -0.02:
                continue
            idx = max(0, min(n, int(round(u * n))))
            ys = [pts[idx][1] for pts in curves]
            x = curves[0][idx][0]
            y = sum(ys) / len(ys)
            spr = self._sprite(24, 0.55 * k)
            layer.blit(spr, (int(x - 24), int(y - 24)), special_flags=pygame.BLEND_ADD)
            spr = self._sprite(10, 0.9 * k)
            layer.blit(spr, (int(x - 10), int(y - 10)), special_flags=pygame.BLEND_ADD)

        # ---- 5. light pulses travelling along the threads
        for p in self.pulses:
            if not (0.0 <= p.u <= 1.0) or p.thread >= len(curves):
                continue
            pts = curves[p.thread]
            fi = p.u * n
            i0 = int(fi)
            i1 = min(n, i0 + 1)
            f = fi - i0
            x = pts[i0][0] + (pts[i1][0] - pts[i0][0]) * f
            y = pts[i0][1] + (pts[i1][1] - pts[i0][1]) * f
            fade = math.sin(math.pi * p.u)
            r = 16 if p.size > 1.3 else 10
            spr = self._sprite(r, min(1.0, 0.9 * fade * k))
            layer.blit(spr, (int(x - r), int(y - r)), special_flags=pygame.BLEND_ADD)
            spr = self._sprite(6, min(1.0, fade * k))
            layer.blit(spr, (int(x - 6), int(y - 6)), special_flags=pygame.BLEND_ADD)

        # ---- 6. composite additively onto the target
        surface.blit(layer, (0, 0), special_flags=pygame.BLEND_ADD)


if __name__ == "__main__":
    # Standalone demo running React Bits <WebThreads /> in Pygame
    import sys

    COLORS = ["#5227FF", "#FF9FFC"]
    CORE_COLOR = "#FFFFFF"
    THREAD_COUNT = 6
    SPREAD = 0.18
    WIDTH = 1000
    HEIGHT = 600

    pygame.init()
    pygame.display.set_caption("React Bits <WebThreads /> - Python Pygame Port")
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    clock = pygame.time.Clock()

    threads = WebThreads(
        width=WIDTH,
        height=HEIGHT,
        colors=COLORS,
        core_color=CORE_COLOR,
        thread_count=THREAD_COUNT,
        spread=SPREAD,
        speed=1.0,
    )

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        cur_w, cur_h = screen.get_size()
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    threads.trigger_pulse()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                threads.trigger_pulse()

        threads.update(dt, mouse_pos=mouse_pos)

        screen.fill((0, 0, 0))
        threads.draw(screen, alpha_mult=1.0)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)
