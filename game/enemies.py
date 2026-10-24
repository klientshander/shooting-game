"""Enemy and Meteor archetypes with upgraded visual designs, holographic health bars, and tactical indicators."""

import math
import random

import pygame


ENEMY_TYPES = ("scout", "tank", "hunter", "bomber", "elite", "charger")
COLORS = {
    "scout": (255, 145, 55),
    "tank": (175, 195, 225),
    "hunter": (235, 75, 225),
    "bomber": (195, 85, 255),
    "elite": (255, 210, 75),
    "charger": (255, 55, 80),
}

_TAG_FONT = None
_UFO_SPRITES = {}
_ASTEROID_SPRITES = {}


def _get_tag_font():
    global _TAG_FONT
    if _TAG_FONT is None:
        _TAG_FONT = pygame.font.SysFont("segoeui", 11, bold=True)
    return _TAG_FONT


def _get_asteroid_sprite(radius):
    global _ASTEROID_SPRITES
    if radius in _ASTEROID_SPRITES:
        return _ASTEROID_SPRITES[radius]

    pad = 14
    size = radius * 2 + pad * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2

    rng = random.Random(radius * 313)

    num_pts = 14
    radii = [radius * rng.uniform(0.85, 1.15) for _ in range(num_pts)]
    outer_pts = []
    for i in range(num_pts):
        ang = i * (math.tau / num_pts)
        outer_pts.append((cx + math.cos(ang) * radii[i], cy + math.sin(ang) * radii[i]))

    int_outer = [(int(x), int(y)) for x, y in outer_pts]
    pygame.draw.polygon(surf, (55, 60, 72), int_outer)

    inner_nodes = [
        (cx - radius * 0.28, cy - radius * 0.25),
        (cx + radius * 0.25, cy - radius * 0.20),
        (cx + radius * 0.20, cy + radius * 0.28),
        (cx - radius * 0.22, cy + radius * 0.22),
    ]

    lx, ly = -0.6, -0.8

    facets = [
        ([inner_nodes[0], inner_nodes[1], (cx, cy)], (0.0, -1.0)),
        ([inner_nodes[1], inner_nodes[2], (cx, cy)], (1.0, 0.2)),
        ([inner_nodes[2], inner_nodes[3], (cx, cy)], (0.2, 1.0)),
        ([inner_nodes[3], inner_nodes[0], (cx, cy)], (-1.0, 0.0)),
        ([outer_pts[10], outer_pts[11], outer_pts[12], inner_nodes[0]], (-0.7, -0.7)),
        ([outer_pts[12], outer_pts[13], outer_pts[0], inner_nodes[0]], (-0.5, -0.9)),
        ([outer_pts[0], outer_pts[1], outer_pts[2], inner_nodes[1]], (0.4, -0.8)),
        ([outer_pts[2], outer_pts[3], outer_pts[4], inner_nodes[1]], (0.9, -0.3)),
        ([outer_pts[4], outer_pts[5], outer_pts[6], inner_nodes[2]], (0.8, 0.6)),
        ([outer_pts[6], outer_pts[7], outer_pts[8], inner_nodes[2]], (0.2, 0.9)),
        ([outer_pts[8], outer_pts[9], outer_pts[10], inner_nodes[3]], (-0.5, 0.7)),
    ]

    base_r, base_g, base_b = 75, 82, 98
    for poly, normal in facets:
        nx, ny = normal
        length = math.hypot(nx, ny) or 1.0
        nx, ny = nx / length, ny / length
        dot = -(nx * lx + ny * ly)
        intensity = 0.95 + dot * 0.50
        r_col = max(28, min(225, int(base_r * intensity)))
        g_col = max(32, min(235, int(base_g * intensity)))
        b_col = max(40, min(250, int(base_b * intensity)))
        int_poly = [(int(x), int(y)) for x, y in poly]
        pygame.draw.polygon(surf, (r_col, g_col, b_col), int_poly)

    for poly, _ in facets:
        int_poly = [(int(x), int(y)) for x, y in poly]
        pygame.draw.polygon(surf, (36, 40, 50), int_poly, 1)

    craters = [
        (-radius * 0.35, -radius * 0.15, radius * 0.22),
        (radius * 0.18, -radius * 0.28, radius * 0.18),
        (-radius * 0.08, radius * 0.26, radius * 0.20),
        (radius * 0.32, radius * 0.18, radius * 0.15),
    ]
    for ox, oy, cr in craters:
        c_x, c_y = cx + int(ox), cy + int(oy)
        cr_i = max(2, int(cr))
        pygame.draw.circle(surf, (24, 27, 34), (c_x, c_y), cr_i)
        pygame.draw.circle(surf, (15, 17, 22), (c_x + 1, c_y + 1), max(1, cr_i - 2))
        pygame.draw.arc(surf, (175, 190, 220), (c_x - cr_i, c_y - cr_i, cr_i * 2, cr_i * 2), 0.8, 2.8, 2)
        pygame.draw.arc(surf, (20, 22, 28), (c_x - cr_i, c_y - cr_i, cr_i * 2, cr_i * 2), 3.8, 6.0, 2)

    pygame.draw.polygon(surf, (20, 24, 32), int_outer, 2)
    for i in (10, 11, 12, 13, 0):
        p1 = (int(outer_pts[i][0]), int(outer_pts[i][1]))
        p2 = (int(outer_pts[(i + 1) % num_pts][0]), int(outer_pts[(i + 1) % num_pts][1]))
        pygame.draw.line(surf, (190, 210, 240), p1, p2, 2)

    _ASTEROID_SPRITES[radius] = surf
    return surf


def _get_ufo_sprite(kind, radius):
    global _UFO_SPRITES
    key = (kind, radius)
    if key in _UFO_SPRITES:
        return _UFO_SPRITES[key]

    try:
        raw = pygame.image.load("assets/enemy_alien_tight.png").convert_alpha()
        w = int(radius * 2.5)
        h = int(radius * 1.9)
        base = pygame.transform.smoothscale(raw, (w, h))

        if kind == "elite":
            tinted = base.copy()
            tinted.fill((80, 60, 15, 0), special_flags=pygame.BLEND_RGB_ADD)
            _UFO_SPRITES[key] = tinted
        elif kind == "hunter":
            tinted = base.copy()
            tinted.fill((65, 15, 75, 0), special_flags=pygame.BLEND_RGB_ADD)
            _UFO_SPRITES[key] = tinted
        elif kind == "bomber":
            tinted = base.copy()
            tinted.fill((45, 15, 75, 0), special_flags=pygame.BLEND_RGB_ADD)
            _UFO_SPRITES[key] = tinted
        elif kind == "charger":
            tinted = base.copy()
            tinted.fill((125, 20, 35, 0), special_flags=pygame.BLEND_RGB_ADD)
            _UFO_SPRITES[key] = tinted
        else:
            _UFO_SPRITES[key] = base
    except Exception:
        _UFO_SPRITES[key] = None

    return _UFO_SPRITES[key]


class Enemy:
    def __init__(
        self,
        kind,
        spawn_x,
        spawn_y,
        target_x=None,
        target_y=None,
        health_mult=1.0,
        speed_mult=1.0,
        damage=1,
        fire_rate_mult=1.0,
    ):
        self.kind = kind if kind in ENEMY_TYPES else "scout"
        self.x = float(spawn_x)
        self.y = float(spawn_y)
        self.color = COLORS[self.kind]
        self.hit_flash = 0.0
        self.age = random.random() * 6.28

        # Fair starting base health (scales up smoothly over survival time)
        base_health = {"scout": 2, "tank": 7, "hunter": 4, "bomber": 5, "elite": 13, "charger": 3}[self.kind]
        self.max_health = max(1, int(base_health * health_mult))
        self.health = self.max_health
        self.damage_lag_health = float(self.max_health)

        # Accessible base speeds at start (scales up smoothly over survival time)
        base_speed = {"scout": 235, "tank": 115, "hunter": 215, "bomber": 170, "elite": 145, "charger": 195}[self.kind]
        self.speed = base_speed * speed_mult

        self.damage = max(damage, 2 if self.kind in ("tank", "elite") else 1)
        self.radius = {"scout": 19, "tank": 28, "hunter": 21, "bomber": 23, "elite": 30, "charger": 20}[self.kind]
        self.reward = {"scout": 100, "tank": 240, "hunter": 180, "bomber": 220, "elite": 450, "charger": 210}[self.kind]

        # Strictly straight horizontal movement across the screen (no vertical drift, no shooting)
        self.vx = -self.speed
        self.vy = 0.0

        # Special state machine for Charger (warning signal light + straight red line at spawn, then hyper-sprint)
        self.state = "normal"
        if self.kind == "charger":
            self.state = "warning"
            self.warning_timer = 1.10
            self.warning_total = 1.10
            self.warning_sound_played = False
            self.sprint_speed = 920.0 * speed_mult
            self.vx = 0.0
            self.vy = 0.0

    def update(self, dt, player_x=0.0, player_y=0.0):
        event = None
        if self.kind == "charger":
            if self.state == "warning":
                self.vx = 0.0
                self.vy = 0.0
                if not self.warning_sound_played:
                    self.warning_sound_played = True
                    event = "warning"
                self.warning_timer -= dt
                if self.warning_timer <= 0.0:
                    self.state = "sprint"
                    self.vx = -self.sprint_speed
                    self.damage = max(self.damage, 2)
                    event = "sprint"
            elif self.state == "sprint":
                self.vx = -self.sprint_speed

        self.age += dt
        self.hit_flash = max(0.0, self.hit_flash - dt)
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Smooth damage lag bar decay towards current health
        if self.damage_lag_health > self.health:
            self.damage_lag_health = max(float(self.health), self.damage_lag_health - (self.max_health * 1.6 * dt))
        else:
            self.damage_lag_health = float(self.health)

        return event

    def is_offscreen(self, width=1280, height=720):
        margin = 130
        return (
            self.x < -margin
            or self.x > width + margin + 160
            or self.y < -margin
            or self.y > height + margin
        )

    def draw_incoming_indicator(self, surface, screen_width=1280):
        """Draw a sleek off-screen threat warning chevron when approaching from the right edge."""
        if screen_width <= self.x <= screen_width + 150:
            edge_x = screen_width - 16
            edge_y = int(self.y)
            pulse = int(math.sin(self.age * 12.0) * 3)

            # Warning chevron in enemy's theme color
            col = self.color
            pts = [
                (edge_x - 12 - pulse, edge_y - 8),
                (edge_x - pulse, edge_y),
                (edge_x - 12 - pulse, edge_y + 8),
                (edge_x - 8 - pulse, edge_y),
            ]
            pygame.draw.polygon(surface, col, pts)
            pygame.draw.circle(surface, (255, 255, 255), (edge_x - 4 - pulse, edge_y), 2)

    def draw(self, surface, offset=(0, 0)):
        # Apply high-frequency vibration offset when Charger is charging up
        shk_y = int(math.sin(self.age * 55.0) * 2.0) if getattr(self, "state", None) == "warning" else 0
        x, y = int(self.x + offset[0]), int(self.y + offset[1] + shk_y)
        r = self.radius
        flash = self.hit_flash > 0
        primary = (255, 255, 250) if flash else self.color

        # If Charger is in warning state, render high-tech laser targeting line straight across screen
        if self.kind == "charger" and getattr(self, "state", None) == "warning" and x > 0:
            warn_pct = max(0.0, min(1.0, 1.0 - (self.warning_timer / max(0.001, self.warning_total))))
            pulse = math.sin(self.age * 28.0)
            line_alpha = int(140 + warn_pct * 95 + pulse * 20)

            # Outer danger glow beam spanning to far left edge
            beam_w = max(1, x)
            beam_h = 6 if warn_pct > 0.4 else 4
            beam_surf = pygame.Surface((beam_w, beam_h), pygame.SRCALPHA)
            beam_surf.fill((255, 30, 60, min(255, line_alpha // 2)))
            surface.blit(beam_surf, (0, y - beam_h // 2))

            # Inner sharp laser line
            core_surf = pygame.Surface((beam_w, 2), pygame.SRCALPHA)
            core_surf.fill((255, 235, 245, min(255, line_alpha)))
            surface.blit(core_surf, (0, y - 1))

            # Dynamic animated warning chevrons traveling left along the line
            chev_step = 130
            chev_off = int((self.age * 460.0) % chev_step)
            for cx_lane in range(x - chev_off, 0, -chev_step):
                if cx_lane > 10:
                    pts = [(cx_lane, y - 5), (cx_lane - 7, y), (cx_lane, y + 5)]
                    pygame.draw.lines(surface, (255, 240, 245, min(255, line_alpha)), False, pts, 2)

            # Signal warning light beacon at right spawn edge
            sig_pulse = math.sin(self.age * 22.0)
            sig_r = int(24 + sig_pulse * 6)
            sig_surf = pygame.Surface((sig_r * 2 + 4, sig_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(sig_surf, (255, 25, 55, int(160 + sig_pulse * 75)), (sig_r + 2, sig_r + 2), sig_r)
            surface.blit(sig_surf, (x - sig_r - 2, y - sig_r - 2))

            # Expanding warning shockwave ring
            ring_phase = (self.age * 3.2) % 1.0
            ring_r = int(ring_phase * 38)
            ring_alpha = int(220 * (1.0 - ring_phase))
            if ring_r > 3 and ring_alpha > 10:
                ring_surf = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(ring_surf, (255, 80, 100, ring_alpha), (ring_r + 2, ring_r + 2), ring_r, 2)
                surface.blit(ring_surf, (x - ring_r - 2, y - ring_r - 2))

            # Hot white core
            pygame.draw.circle(surface, (255, 250, 255), (x, y), 6)
            pygame.draw.circle(surface, (255, 215, 80), (x, y), 10, 2)

            # Tactical warning badge hovering above the spawn signal light
            tag_font = _get_tag_font()
            badge_txt = tag_font.render("! CHARGER !", True, (255, 245, 250))
            bw, bh = badge_txt.get_size()
            bx_pos = x - bw // 2
            by_pos = y - r - bh - 6
            pygame.draw.rect(surface, (160, 18, 32), (bx_pos - 3, by_pos - 1, bw + 6, bh + 2), border_radius=3)
            pygame.draw.rect(surface, (255, 65, 85), (bx_pos - 3, by_pos - 1, bw + 6, bh + 2), 1, border_radius=3)
            surface.blit(badge_txt, (bx_pos, by_pos))

        # Ambient glow beneath enemy/meteor
        glow_r = r + 15
        glow = pygame.Surface((glow_r * 2 + 2, glow_r * 2 + 2), pygame.SRCALPHA)
        glow_alpha = 40 if self.kind == "tank" else (85 if self.kind == "charger" else 65)
        pygame.draw.circle(glow, (*self.color, glow_alpha), (glow_r + 1, glow_r + 1), glow_r)
        surface.blit(glow, (x - glow_r - 1, y - glow_r - 1))

        # Holographic tactical targeting brackets for Elites, Tanks, and Chargers
        if self.kind in ("elite", "tank", "charger"):
            bracket_r = r + 9
            bracket_col = (
                (255, 220, 85, 140) if self.kind == "elite"
                else (170, 195, 230, 130) if self.kind == "tank"
                else (255, 65, 85, 150)
            )
            bs = 7
            bracket_surf = pygame.Surface((bracket_r * 2 + 4, bracket_r * 2 + 4), pygame.SRCALPHA)
            bc = bracket_r + 2
            # 4 corner brackets [ ]
            # Top-left
            pygame.draw.lines(bracket_surf, bracket_col, False, [(bc - bracket_r, bc - bracket_r + bs), (bc - bracket_r, bc - bracket_r), (bc - bracket_r + bs, bc - bracket_r)], 2)
            # Top-right
            pygame.draw.lines(bracket_surf, bracket_col, False, [(bc + bracket_r - bs, bc - bracket_r), (bc + bracket_r, bc - bracket_r), (bc + bracket_r, bc - bracket_r + bs)], 2)
            # Bottom-left
            pygame.draw.lines(bracket_surf, bracket_col, False, [(bc - bracket_r, bc + bracket_r - bs), (bc - bracket_r, bc + bracket_r), (bc - bracket_r + bs, bc + bracket_r)], 2)
            # Bottom-right
            pygame.draw.lines(bracket_surf, bracket_col, False, [(bc + bracket_r - bs, bc + bracket_r), (bc + bracket_r, bc + bracket_r), (bc + bracket_r, bc + bracket_r - bs)], 2)
            surface.blit(bracket_surf, (x - bc, y - bc))

        # If Charger is in full sprint, draw supersonic jet exhaust flames behind it
        if self.kind == "charger" and getattr(self, "state", None) == "sprint":
            flame_len = random.randint(48, 72)
            flame_pts = [(x + r - 2, y - 8), (x + r + flame_len, y), (x + r - 2, y + 8)]
            pygame.draw.polygon(surface, (255, 65, 45), flame_pts)
            core_pts = [(x + r - 1, y - 4), (x + r + int(flame_len * 0.65), y), (x + r - 1, y + 4)]
            pygame.draw.polygon(surface, (255, 245, 150), core_pts)
            for roff in (flame_len * 0.35, flame_len * 0.70):
                rx = int(x + r + roff)
                pygame.draw.ellipse(surface, (255, 140, 70), (rx - 3, y - 9, 6, 18), 1)

        # Antigravity propulsion beam beneath UFO (aliens only, not asteroids)
        if self.kind != "tank":
            beam_pulse = int(math.sin(self.age * 16.0) * 4)
            beam_color = (255, 95, 115, 110) if self.kind == "charger" else (80, 220, 255, 90)
            pygame.draw.polygon(
                surface,
                beam_color,
                [(x - 8, y + 10), (x - 14 - beam_pulse, y + 24), (x + 8 + beam_pulse, y + 24), (x + 8, y + 10)],
            )

        # Draw Asteroid (tank) or Alien UFO Sprite (other kinds)
        if self.kind == "tank":
            ast_base = _get_asteroid_sprite(self.radius)
            rot_angle = (self.age * 30.0) % 360
            rot_sprite = pygame.transform.rotate(ast_base, rot_angle)
            if flash:
                flash_surf = rot_sprite.copy()
                flash_surf.fill((210, 210, 210, 0), special_flags=pygame.BLEND_RGB_ADD)
                surface.blit(flash_surf, flash_surf.get_rect(center=(x, y)))
            else:
                surface.blit(rot_sprite, rot_sprite.get_rect(center=(x, y)))
        else:
            sprite = _get_ufo_sprite(self.kind, self.radius)
            if sprite:
                if flash:
                    flash_surf = sprite.copy()
                    flash_surf.fill((210, 210, 210, 0), special_flags=pygame.BLEND_RGB_ADD)
                    surface.blit(flash_surf, flash_surf.get_rect(center=(x, y)))
                else:
                    surface.blit(sprite, sprite.get_rect(center=(x, y)))

        # UPGRADED HOLOGRAPHIC ENEMY HEALTH BAR & UI BADGE
        show_bar = (self.health < self.max_health) or (self.kind in ("elite", "tank", "charger"))
        if show_bar:
            bar_w = max(40, r * 2 + 10)
            bar_h = 5
            bx = x - bar_w // 2
            by = y - r - 15

            # Micro archetype badge for Elite, Tank & Charger
            if self.kind in ("elite", "tank", "charger"):
                tag_font = _get_tag_font()
                badge_text = "ELITE" if self.kind == "elite" else "ASTEROID" if self.kind == "tank" else "CHARGER"
                badge_col = (255, 225, 90) if self.kind == "elite" else (175, 205, 240) if self.kind == "tank" else (255, 75, 95)
                rendered_badge = tag_font.render(badge_text, True, badge_col)
                bw, bh = rendered_badge.get_size()
                badge_x = x - bw // 2
                badge_y = by - bh - 2
                # Tiny backing panel
                pygame.draw.rect(surface, (12, 16, 38), (badge_x - 3, badge_y - 1, bw + 6, bh + 2), border_radius=3)
                pygame.draw.rect(surface, badge_col, (badge_x - 3, badge_y - 1, bw + 6, bh + 2), 1, border_radius=3)
                surface.blit(rendered_badge, (badge_x, badge_y))

            # Beveled high-tech dark slot
            pygame.draw.rect(surface, (8, 12, 32), (bx - 2, by - 2, bar_w + 4, bar_h + 4), border_radius=4)
            pygame.draw.rect(surface, (45, 65, 115), (bx - 2, by - 2, bar_w + 4, bar_h + 4), 1, border_radius=4)

            # Damage lag ghost bar (white/amber trailing bar)
            lag_pct = max(0.0, min(1.0, self.damage_lag_health / self.max_health))
            lag_w = int(bar_w * lag_pct)
            if lag_w > 0:
                pygame.draw.rect(surface, (255, 220, 140), (bx, by, lag_w, bar_h), border_radius=2)

            # Main health fill with dynamic color-shift
            hp_pct = max(0.0, min(1.0, self.health / self.max_health))
            fill_w = int(bar_w * hp_pct)
            if fill_w > 0:
                if hp_pct > 0.55:
                    hp_col = (65, 240, 190)  # Neon mint green
                elif hp_pct > 0.25:
                    hp_col = (255, 205, 60)  # Glowing gold
                else:
                    hp_col = (255, 70, 95)   # Critical crimson red
                pygame.draw.rect(surface, hp_col, (bx, by, fill_w, bar_h), border_radius=2)

            # Tech notches / segmentation dividers
            for div in (0.25, 0.50, 0.75):
                nx = bx + int(bar_w * div)
                pygame.draw.line(surface, (12, 16, 38), (nx, by), (nx, by + bar_h - 1), 1)

