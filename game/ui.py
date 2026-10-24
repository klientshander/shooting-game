"""Upgraded UI with glossy 3D skill/ultimate orbs, outlined typography, and advanced Boss & Enemy HUD."""

import math
import sys
from pathlib import Path

import pygame

_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from settings import CYAN, GOLD, HEIGHT, MAGENTA, ORANGE, PANEL, SKILLS, WHITE, WIDTH


class UI:
    def __init__(self):
        self.font = pygame.font.SysFont("segoeui", 23, bold=True)
        self.hud_med = pygame.font.SysFont("segoeui", 15, bold=True)
        self.skill_font = pygame.font.SysFont("segoeui", 28, bold=True)
        self.small = pygame.font.SysFont("segoeui", 16, bold=True)
        self.tiny = pygame.font.SysFont("segoeui", 13, bold=True)
        self.title = pygame.font.SysFont("segoeui", 56, bold=True)
        self.large = pygame.font.SysFont("segoeui", 38, bold=True)
        self._orb_cache = {}

    def text(self, surface, value, position, color=WHITE, font=None, center=False, outline=True):
        used_font = font or self.font
        text_str = str(value)
        rendered = used_font.render(text_str, True, color)
        rect = rendered.get_rect(center=position) if center else rendered.get_rect(topleft=position)
        if outline:
            shadow = used_font.render(text_str, True, (6, 8, 28))
            for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)):
                surface.blit(shadow, rect.move(ox, oy))
        surface.blit(rendered, rect)

    def panel(self, surface, rect, fill=PANEL, border=CYAN, alpha=225):
        panel_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (*fill, alpha), (0, 0, rect.width, rect.height), border_radius=14)
        pygame.draw.rect(
            panel_surf,
            (255, 255, 255, 28),
            (3, 3, rect.width - 6, max(8, rect.height // 3)),
            border_radius=10,
        )
        pygame.draw.rect(panel_surf, (*border, 240), (0, 0, rect.width, rect.height), 2, border_radius=14)
        surface.blit(panel_surf, rect.topleft)

    def glass_capsule(self, surface, rect, border=CYAN, alpha=150):
        glass = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(glass, (8, 14, 30, alpha), (0, 0, rect.width, rect.height), border_radius=10)
        pygame.draw.line(glass, (255, 255, 255, 38), (8, 1), (rect.width - 8, 1), 1)
        pygame.draw.rect(glass, (*border, 130), (0, 0, rect.width, rect.height), 1, border_radius=10)
        surface.blit(glass, rect.topleft)

    def _get_skill_orb(self, skill_id: str, theme: str, radius: int) -> pygame.Surface:
        key = (skill_id, theme, radius)
        if key in self._orb_cache:
            return self._orb_cache[key]

        size = radius * 2 + 12
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2

        # Outer dark rim
        pygame.draw.circle(surf, (4, 8, 28), (cx, cy), radius + 3)

        # Radial 3D glossy gradient fill
        for r in range(radius, 0, -1):
            t = 1.0 - (r / radius)
            if theme == "gold":
                col = (
                    int(160 + 95 * t),
                    int(90 + 135 * t),
                    int(15 + 65 * t),
                )
            elif theme == "blue":
                col = (
                    int(10 + 75 * t),
                    int(65 + 155 * t),
                    int(225 + 30 * t),
                )
            else:
                col = (
                    int(115 + 135 * t),
                    int(20 + 95 * (t ** 1.4)),
                    int(235 + 20 * t),
                )
            gx = cx - int((radius - r) * 0.16)
            gy = cy - int((radius - r) * 0.18)
            pygame.draw.circle(surf, col, (gx, gy), r)

        if theme == "gold":
            accent = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(accent, (255, 245, 140, 110), (cx + radius // 4, cy + radius // 4), int(radius * 0.65))
            surf.blit(accent, (0, 0))
        elif theme == "purple":
            accent = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(accent, (40, 190, 255, 95), (cx + radius // 4, cy + radius // 4), int(radius * 0.68))
            surf.blit(accent, (0, 0))

        s = radius / 48.0
        if skill_id == "attack_speed":
            bolt1 = [
                (cx - int(12 * s), cy - int(32 * s)),
                (cx - int(26 * s), cy + int(2 * s)),
                (cx - int(16 * s), cy - int(2 * s)),
                (cx - int(24 * s), cy + int(22 * s)),
                (cx - int(6 * s), cy - int(8 * s)),
                (cx - int(15 * s), cy - int(6 * s)),
            ]
            pygame.draw.polygon(surf, (235, 250, 255), bolt1)
            block = [
                (cx - int(18 * s), cy + int(12 * s)),
                (cx + int(6 * s), cy - int(12 * s)),
                (cx + int(22 * s), cy + int(2 * s)),
                (cx - int(2 * s), cy + int(26 * s)),
            ]
            pygame.draw.polygon(surf, (20, 45, 120), [(px + 2, py + 2) for px, py in block])
            pygame.draw.polygon(surf, (250, 252, 255), block)
            pygame.draw.polygon(surf, (255, 235, 145), block, max(1, int(2 * s)))
            bolt2 = [
                (cx - int(2 * s), cy + int(28 * s)),
                (cx + int(28 * s), cy + int(10 * s)),
                (cx + int(14 * s), cy + int(8 * s)),
                (cx + int(26 * s), cy - int(4 * s)),
            ]
            pygame.draw.polygon(surf, (235, 250, 255), bolt2)

        elif skill_id == "split_bullets":
            arrows = [
                (0.0, 0, -4, 1.08),
                (-0.38, -int(20 * s), int(6 * s), 0.78),
                (0.38, int(20 * s), int(6 * s), 0.78),
            ]
            for ang, ox, oy, scale in arrows:
                acx, acy = cx + ox, cy + oy
                cos_a, sin_a = math.cos(ang), math.sin(ang)

                def rot_pt(px, py):
                    rx = px * cos_a - py * sin_a
                    ry = px * sin_a + py * cos_a
                    return (int(acx + rx * s * scale), int(acy + ry * s * scale))

                pts = [
                    rot_pt(0, -28),
                    rot_pt(12, 10),
                    rot_pt(3, 6),
                    rot_pt(0, 22),
                    rot_pt(-3, 6),
                    rot_pt(-12, 10),
                ]
                pygame.draw.polygon(surf, (15, 40, 115), [(p[0] + 2, p[1] + 2) for p in pts])
                pygame.draw.polygon(surf, (255, 245, 150), pts)
                pygame.draw.polygon(surf, (255, 255, 255), [rot_pt(0, -26), rot_pt(6, 4), rot_pt(0, 12), rot_pt(-6, 4)])

        elif skill_id == "shield":
            def shield_poly(scale_f):
                return [
                    (cx, cy - int(28 * s * scale_f)),
                    (cx + int(24 * s * scale_f), cy - int(18 * s * scale_f)),
                    (cx + int(20 * s * scale_f), cy + int(6 * s * scale_f)),
                    (cx, cy + int(30 * s * scale_f)),
                    (cx - int(20 * s * scale_f), cy + int(6 * s * scale_f)),
                    (cx - int(24 * s * scale_f), cy - int(18 * s * scale_f)),
                ]

            pygame.draw.polygon(surf, (255, 240, 250), shield_poly(1.05))
            pygame.draw.polygon(surf, (105, 28, 165), shield_poly(0.84))
            pygame.draw.polygon(surf, (255, 235, 248), shield_poly(0.70), max(2, int(3 * s)))
            star_pts = []
            for i in range(10):
                ang = -math.pi / 2 + i * (math.pi / 5)
                sr = (12 * s) if i % 2 == 0 else (5 * s)
                star_pts.append((cx + int(math.cos(ang) * sr), cy + int(math.sin(ang) * sr)))
            pygame.draw.polygon(surf, (255, 240, 250), star_pts)

        elif skill_id == "meteor_explosion":
            spikes = []
            num_spikes = 14
            for i in range(num_spikes):
                ang = i * (math.tau / num_spikes)
                sr = (32 * s) if i % 2 == 0 else (15 * s)
                spikes.append((cx + int(math.cos(ang) * sr), cy + int(math.sin(ang) * sr)))
            pygame.draw.polygon(surf, (255, 245, 255), spikes)
            pygame.draw.polygon(surf, (165, 40, 225), spikes, max(2, int(2 * s)))
            rock = [
                (cx - int(22 * s), cy + int(6 * s)),
                (cx - int(8 * s), cy - int(8 * s)),
                (cx + int(6 * s), cy + int(4 * s)),
                (cx - int(4 * s), cy + int(24 * s)),
                (cx - int(20 * s), cy + int(20 * s)),
            ]
            pygame.draw.polygon(surf, (255, 250, 255), rock)
            pygame.draw.polygon(surf, (120, 35, 185), rock, max(1, int(2 * s)))

        elif skill_id == "piercing":
            # Piercing laser arrow passing straight through target barrier
            pygame.draw.ellipse(surf, (140, 220, 255), (cx - int(10 * s), cy - int(24 * s), int(20 * s), int(48 * s)), max(2, int(3 * s)))
            bolt_pts = [
                (cx - int(30 * s), cy - int(5 * s)),
                (cx + int(18 * s), cy - int(5 * s)),
                (cx + int(34 * s), cy),
                (cx + int(18 * s), cy + int(5 * s)),
                (cx - int(30 * s), cy + int(5 * s)),
                (cx - int(22 * s), cy),
            ]
            pygame.draw.polygon(surf, (15, 35, 110), [(px + 2, py + 2) for px, py in bolt_pts])
            pygame.draw.polygon(surf, (255, 255, 255), bolt_pts)
            pygame.draw.polygon(surf, (90, 235, 255), bolt_pts, max(1, int(2 * s)))

        elif skill_id in ("ultimate", "restore_energy"):
            for i in range(8):
                ang = i * (math.pi / 4)
                pygame.draw.line(
                    surf,
                    (255, 245, 180),
                    (cx, cy),
                    (cx + int(math.cos(ang) * (30 * s)), cy + int(math.sin(ang) * (30 * s))),
                    max(2, int(4 * s)),
                )
            pygame.draw.circle(surf, (255, 255, 255), (cx, cy), max(6, int(12 * s)))
            pygame.draw.circle(surf, (255, 215, 60), (cx, cy), max(9, int(18 * s)), 2)
            q_font = pygame.font.SysFont("segoeui", max(12, int(24 * s)), bold=True)
            q_txt = q_font.render("Q", True, (65, 20, 10))
            surf.blit(q_txt, q_txt.get_rect(center=(cx, cy)))

        arc_rect = pygame.Rect(cx - int(radius * 0.84), cy - int(radius * 0.84), int(radius * 1.68), int(radius * 1.68))
        pygame.draw.arc(surf, (255, 255, 255, 215), arc_rect, math.radians(28), math.radians(158), max(2, int(3 * s)))
        rim_color = (255, 225, 95) if theme == "gold" else (120, 225, 255) if theme == "blue" else (210, 130, 255)
        pygame.draw.circle(surf, rim_color, (cx, cy), radius, max(2, int(2.5 * s)))
        pygame.draw.circle(surf, (8, 14, 42), (cx, cy), radius + 2, 2)

        self._orb_cache[key] = surf
        return surf

    def draw_skill_orb(self, surface, skill_id: str, theme: str, center_pos: tuple[int, int], radius: int = 46, selected: bool = False):
        cx, cy = center_pos
        if selected:
            glow_r = radius + 14
            glow = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
            g_col = (255, 220, 80, 115) if theme == "gold" else (80, 220, 255, 110) if theme == "blue" else (235, 90, 255, 110)
            pygame.draw.circle(glow, g_col, (glow_r + 2, glow_r + 2), glow_r)
            surface.blit(glow, (cx - glow_r - 2, cy - glow_r - 2))
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), radius + 5, 2)

        orb = self._get_skill_orb(skill_id, theme, radius)
        surface.blit(orb, (cx - orb.get_width() // 2, cy - orb.get_height() // 2))

    def draw_menu(self, surface, options, selected, high_score, best_time="00:00"):
        self.text(surface, "COSMIC RIFT", (WIDTH // 2, 130), WHITE, self.title, True)
        self.text(surface, "E N D L E S S   S T A R F A L L", (WIDTH // 2, 188), MAGENTA, self.large, True)

        self.text(surface, "COLLECT RANDOM SKILL & ULTIMATE ORBS IN SPACE!", (WIDTH // 2, 238), GOLD, self.small, True)

        # Showcase the random floating orbs
        spacing = 80
        start_x = WIDTH // 2 - ((len(SKILLS) - 1) * spacing) // 2
        for i, skill in enumerate(SKILLS):
            self.draw_skill_orb(surface, skill["id"], skill["theme"], (start_x + i * spacing, 292), radius=26)

        for i, option in enumerate(options):
            color = CYAN if i == selected else WHITE
            label = f"[ {option.upper()} ]" if i == selected else option.upper()
            self.text(surface, label, (WIDTH // 2, 385 + i * 52), color, self.font, True)

        self.text(surface, f"BEST SCORE  {high_score:,}    •    BEST TIME  {best_time}", (WIDTH // 2, 605), GOLD, self.small, True)
        self.text(
            surface,
            "WASD: MOVE  •  AUTO-FIRE  •  SHIFT: DASH  •  Q: ULTIMATE  •  B: SWITCH BACKGROUND",
            (WIDTH // 2, 665),
            (175, 200, 245),
            self.small,
            True,
        )

    def draw_character(self, surface, characters, selected):
        self.text(surface, "CHOOSE YOUR STARBLADE", (WIDTH // 2, 170), WHITE, self.large, True)
        for i, character in enumerate(characters):
            x = 330 + i * 310
            active = i == selected
            color = character["color"]
            rect = pygame.Rect(x - 116, 280, 232, 240)
            self.panel(surface, rect, (21, 28, 82), color if active else (65, 78, 135))
            pygame.draw.polygon(surface, color, [(x + 37, 365), (x - 22, 345), (x - 5, 365), (x - 22, 385)])
            self.text(surface, character["name"], (x, 427), color, self.large, True)
            self.text(surface, character["description"], (x, 469), WHITE, self.small, True)
        self.text(surface, "A / D OR LEFT / RIGHT TO SELECT  •  ENTER TO LAUNCH ENDLESS RUN", (WIDTH // 2, 606), CYAN, self.small, True)

    def draw_settings(self, surface, fullscreen, selected, bg_mode="RANDOM"):
        self.text(surface, "SETTINGS", (WIDTH // 2, 190), WHITE, self.large, True)
        items = [
            f"DISPLAY MODE: {'FULLSCREEN' if fullscreen else 'WINDOWED'}",
            f"BACKGROUND: {bg_mode.upper()}",
            "BACK",
        ]
        for i, item in enumerate(items):
            self.text(surface, item, (WIDTH // 2, 310 + i * 65), CYAN if i == selected else WHITE, self.font, True)
        self.text(surface, "UP / DOWN SELECT  •  LEFT / RIGHT OR ENTER CHANGE", (WIDTH // 2, 540), (175, 198, 235), self.small, True)
        self.text(surface, "TIP: PRESS 'B' IN-GAME TO SWITCH BACKGROUND RANDOMLY", (WIDTH // 2, 580), GOLD, self.tiny, True)

    def draw_hud(self, surface, player, score, high_score, survival_time_str, tier, enemy_count, boss, combo, engine, message):
        # Top-left compact glass capsule (Survival & Score info)
        r_left = pygame.Rect(16, 8, 335, 46)
        self.glass_capsule(surface, r_left, (72, 185, 255))
        self.text(surface, f"TIME {survival_time_str}", (28, 11), GOLD, self.small)
        self.text(surface, f"SCORE {score:,}", (135, 12), WHITE, self.hud_med)
        self.text(surface, f"BEST {high_score:,}", (245, 13), (160, 205, 255), self.tiny)

        self.text(surface, f"THREAT TIER {tier}", (28, 30), CYAN, self.hud_med)
        for i in range(5):
            led_col = GOLD if i < min(5, tier) else (35, 45, 68)
            pygame.draw.rect(surface, led_col, (135 + i * 9, 34, 6, 9), border_radius=1)
        meteor_col = (255, 110, 110) if enemy_count >= 12 else CYAN
        self.text(surface, f">> {enemy_count} HOSTILES", (195, 30), meteor_col, self.hud_med)

        # Top-right compact glass capsule (Ship Vitals & Abilities)
        r_right = pygame.Rect(WIDTH - 346, 8, 330, 46)
        self.glass_capsule(surface, r_right, (72, 185, 255))
        self.text(surface, "HULL", (WIDTH - 334, 12), WHITE, self.hud_med)
        for i in range(player.max_health):
            pip_color = (255, 82, 138) if i < player.health else (55, 45, 88)
            pygame.draw.rect(surface, pip_color, (WIDTH - 290 + i * 16, 14, 12, 10), border_radius=2)

        shield_str = "SHIELD ACTIVE" if player.has_shield else "SHIELD --"
        shield_col = CYAN if player.has_shield else (140, 155, 185)
        self.text(surface, shield_str, (WIDTH - 180, 12), shield_col, self.hud_med)

        dash_str = "DASH READY" if player.dash_cooldown <= 0 else f"DASH {player.dash_cooldown:.1f}s"
        dash_col = (130, 245, 180) if player.dash_cooldown <= 0 else (180, 195, 220)
        self.text(surface, dash_str, (WIDTH - 334, 30), dash_col, self.hud_med)

        if player.ultimate_charges > 0:
            ult_col = GOLD
            ult_text = f"ULT [Q] (x{player.ultimate_charges}) READY!"
        else:
            ult_col = (130, 145, 180)
            ult_text = "ULT [Q] (FIND ORB)"
        self.text(surface, ult_text, (WIDTH - 205, 30), ult_col, self.hud_med)

        # Bottom-left Active Collected Skills Bar
        active_skills = []
        for sk in SKILLS:
            sk_id = sk["id"]
            if sk_id == "shield":
                if player.has_shield:
                    active_skills.append((sk_id, sk["theme"], None))
            elif sk_id in player.skill_timers and player.skill_timers[sk_id] > 0:
                active_skills.append((sk_id, sk["theme"], player.skill_timers[sk_id]))

        if active_skills:
            for idx, (sk_id, theme, remaining) in enumerate(active_skills):
                ox = 42 + idx * 78
                oy = HEIGHT - 42
                self.draw_skill_orb(surface, sk_id, theme, (ox, oy), radius=22, selected=True)
                if remaining is not None:
                    self.text(surface, f"{int(remaining)}s", (ox, oy + 26), GOLD, self.small, center=True)
                else:
                    self.text(surface, "ACTIVE", (ox, oy + 26), CYAN, self.small, center=True)

        # Pause button in bottom-right
        self.panel(surface, pygame.Rect(WIDTH - 126, HEIGHT - 57, 108, 30), (16, 26, 86), (72, 185, 255))
        self.text(surface, "||  PAUSE", (WIDTH - 72, HEIGHT - 42), WHITE, self.small, True)

        # UPGRADED BOSS HEALTH BAR & UI
        if boss:
            width = 460
            bar_h = 16
            bx = WIDTH // 2 - width // 2
            by = 33

            # Title banner above bar
            phase_tag = "PHASE 2 [ENRAGED]" if boss.phase == 2 else "PHASE 1 [SHIELDED]"
            tag_col = GOLD if boss.phase == 2 else MAGENTA
            self.text(surface, f"☠ COSMIC LEVIATHAN ☠   •   MILESTONE {boss.milestone}   •   {phase_tag}", (WIDTH // 2, 16), tag_col, self.small, center=True)

            # Angular outer tech container with metallic wings
            pygame.draw.rect(surface, (8, 12, 32), (bx - 4, by - 3, width + 8, bar_h + 6), border_radius=6)
            pygame.draw.rect(surface, (65, 30, 95), (bx - 4, by - 3, width + 8, bar_h + 6), 1, border_radius=6)

            # Flanking decorative angle wings
            wing_col = (255, 215, 80) if boss.phase == 2 else CYAN
            pygame.draw.polygon(surface, wing_col, [(bx - 12, by + bar_h // 2), (bx - 5, by - 1), (bx - 5, by + bar_h + 1)])
            pygame.draw.polygon(surface, wing_col, [(bx + width + 12, by + bar_h // 2), (bx + width + 5, by - 1), (bx + width + 5, by + bar_h + 1)])

            # Damage lag ghost bar (white/amber trailing bar)
            lag_pct = max(0.0, min(1.0, getattr(boss, "damage_lag_health", boss.health) / boss.max_health))
            lag_w = int(width * lag_pct)
            if lag_w > 0:
                pygame.draw.rect(surface, (255, 220, 140), (bx, by, lag_w, bar_h), border_radius=3)

            # Main health fill with gradient / pulse
            hp_pct = max(0.0, min(1.0, boss.health / boss.max_health))
            fill_w = int(width * hp_pct)
            if fill_w > 0:
                fill_col = (255, 185, 55) if boss.phase == 2 else MAGENTA
                pygame.draw.rect(surface, fill_col, (bx, by, fill_w, bar_h), border_radius=3)
                pygame.draw.rect(surface, (255, 255, 255, 80), (bx + 2, by + 1, max(0, fill_w - 4), bar_h // 3), border_radius=2)

            # Notch segmentation dividers every 10%
            for i in range(1, 10):
                nx = bx + int(width * (i / 10.0))
                pygame.draw.line(surface, (12, 16, 38), (nx, by), (nx, by + bar_h - 1), 1)

            # Inside numerical text with drop shadow outline
            hp_str = f"HP  {int(boss.health):,} / {boss.max_health:,}  ({int(hp_pct * 100)}%)"
            self.text(surface, hp_str, (WIDTH // 2, by + bar_h // 2), WHITE, self.small, center=True, outline=True)

        elif combo > 1:
            self.text(surface, f"{combo}x RIFT COMBO", (WIDTH // 2, 28), GOLD, self.font, True)

        if message:
            self.text(surface, message, (WIDTH // 2, 85), GOLD, self.font, True)

        self.text(surface, engine, (WIDTH - 145, HEIGHT - 18), (110, 135, 195), self.small)

    def draw_overlay(self, surface, heading, options, selected, subtitle, hint="ENTER / CLICK TO SELECT   •   ESC TO RESUME"):
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((6, 10, 44, 195))
        surface.blit(dim, (0, 0))
        self.text(surface, heading, (WIDTH // 2, 230), WHITE, self.title, True)
        self.text(surface, subtitle, (WIDTH // 2, 305), CYAN, self.font, True)

        for i, option in enumerate(options):
            color = MAGENTA if i == selected else WHITE
            label = f"[  {option}  ]" if i == selected else option
            self.text(surface, label, (WIDTH // 2, 390 + i * 54), color, self.font, True)

        self.text(surface, hint, (WIDTH // 2, 570), (175, 196, 235), self.small, True)
