"""Procedural sci-fi synthesizer sound engine for COSMIC RIFT.

Generates CD-quality (44.1 kHz, 16-bit stereo) arcade sound effects entirely in memory
with zero external audio file dependencies.
"""

from __future__ import annotations

import math
import random
import struct

import pygame


class Audio:
    RATE = 44100

    def __init__(self, master_volume: float = 0.85):
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.master_volume = max(0.0, min(1.0, master_volume))

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.RATE, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(16)
            self._synthesize_all()
        except pygame.error:
            self.sounds = {}

    def _pack_stereo(self, left: list[float], right: list[float], volume: float = 1.0) -> pygame.mixer.Sound:
        vol = max(0.0, min(1.0, volume * self.master_volume))
        packed = bytearray()
        for l_val, r_val in zip(left, right):
            sl = max(-32767, min(32767, int(l_val * vol)))
            sr = max(-32767, min(32767, int(r_val * vol)))
            packed.extend(struct.pack("<hh", sl, sr))
        return pygame.mixer.Sound(buffer=bytes(packed))

    def _synthesize_all(self) -> None:
        rng = random.Random(1337)
        rate = self.RATE

        # ------------------------------------------------------------------
        # 1. SHOOT: Snappy arcade plasma laser (exponential pitch drop + warm body)
        # ------------------------------------------------------------------
        dur = 0.082
        n = int(rate * dur)
        l, r = [], []
        for i in range(n):
            t = i / rate
            u = i / n
            freq = 960.0 * math.exp(-3.6 * u) + 120.0
            phase = 2.0 * math.pi * freq * t
            env = (1.0 - u) ** 1.35
            # 75% sine + 25% square harmonic for that punchy plasma bite
            sq = 1.0 if math.sin(phase) > 0.0 else -1.0
            raw = (0.78 * math.sin(phase) + 0.22 * sq) * env
            val = math.tanh(raw * 1.6) * 31000 * 0.28
            l.append(val)
            r.append(val)
        self.sounds["shoot"] = self._pack_stereo(l, r, volume=0.55)

        # ------------------------------------------------------------------
        # 2. EXPLOSION: Deep space detonation (punch transient + sub-rumble + filtered debris)
        # ------------------------------------------------------------------
        dur = 0.38
        n = int(rate * dur)
        l, r = [], []
        noise_state = 0.0
        for i in range(n):
            t = i / rate
            u = i / n
            env = (1.0 - u) ** 1.75
            # Sub-bass pitch sweep
            f_sub = 160.0 * math.exp(-2.6 * u) + 32.0
            sub = math.sin(2.0 * math.pi * f_sub * t) * 0.75
            # Filtered noise crunch (hull debris)
            raw_noise = rng.uniform(-1.0, 1.0)
            noise_state += (raw_noise - noise_state) * (0.16 + 0.40 * (1.0 - u))
            # Initial sharp detonation crack
            crack = math.exp(-u * 38.0) * rng.uniform(-1.0, 1.0) * 0.70
            s = (sub + noise_state * 0.55 + crack) * env
            val = math.tanh(s * 1.5) * 32000 * 0.52
            l.append(val)
            r.append(val)
        self.sounds["explosion"] = self._pack_stereo(l, r, volume=0.75)

        # ------------------------------------------------------------------
        # 3. DAMAGE: Hull breach impact & hazard warning (dissonant dual-tone crunch)
        # ------------------------------------------------------------------
        dur = 0.19
        n = int(rate * dur)
        l, r = [], []
        noise_state = 0.0
        for i in range(n):
            t = i / rate
            u = i / n
            env = (1.0 - u) ** 1.4
            f1 = 185.0 * (1.0 - u * 0.35)
            f2 = 132.0 * (1.0 - u * 0.35)
            dual = (math.sin(2.0 * math.pi * f1 * t) + math.sin(2.0 * math.pi * f2 * t)) * 0.5
            raw_noise = rng.uniform(-1.0, 1.0)
            noise_state += (raw_noise - noise_state) * 0.28
            s = (dual * 0.65 + noise_state * 0.35) * env
            val = math.tanh(s * 1.7) * 32000 * 0.48
            l.append(val)
            r.append(val)
        self.sounds["damage"] = self._pack_stereo(l, r, volume=0.68)

        # ------------------------------------------------------------------
        # 4. SPECIAL: Cosmic Rift Ultimate Pulse (holographic riser + harmonic shimmer + sub blast)
        # ------------------------------------------------------------------
        dur = 0.58
        n = int(rate * dur)
        l, r = [], []
        for i in range(n):
            t = i / rate
            u = i / n
            env = (1.0 - u) ** 1.15
            f_rise = 130.0 + 780.0 * (u ** 1.55)
            riser = math.sin(2.0 * math.pi * f_rise * t) * 0.46
            shimmer = math.sin(2.0 * math.pi * (f_rise * 2.01) * t) * 0.26 * math.sin(2.0 * math.pi * 15.0 * t)
            sub = math.sin(2.0 * math.pi * 46.0 * t) * 0.55 * math.exp(-u * 3.5)
            s = (riser + shimmer + sub) * env
            val = math.tanh(s * 1.5) * 32000 * 0.60
            pan = 0.5 + 0.35 * math.sin(2.0 * math.pi * 3.5 * t)
            l.append(val * (1.0 - pan))
            r.append(val * pan)
        self.sounds["special"] = self._pack_stereo(l, r, volume=0.85)

        # ------------------------------------------------------------------
        # 5. BOSS: Dread war horn / braam (deep 62 Hz fundamental + ominous tremolo)
        # ------------------------------------------------------------------
        dur = 0.76
        n = int(rate * dur)
        l, r = [], []
        for i in range(n):
            t = i / rate
            u = i / n
            attack = min(1.0, u * 9.0)
            decay = (1.0 - u) ** 1.25
            env = attack * decay
            tremolo = 0.84 + 0.16 * math.sin(2.0 * math.pi * 5.5 * t)
            f = 62.0
            horn = (
                math.sin(2.0 * math.pi * f * t) * 0.55
                + math.sin(2.0 * math.pi * (f * 2.008) * t) * 0.30
                + math.sin(2.0 * math.pi * (f * 3.015) * t) * 0.15
            )
            s = horn * tremolo * env
            val = math.tanh(s * 1.8) * 32000 * 0.65
            l.append(val)
            r.append(val)
        self.sounds["boss"] = self._pack_stereo(l, r, volume=0.80)

        # ------------------------------------------------------------------
        # 6. PICKUP: Celestial crystal chime (ascending 4-note arpeggio C6-E6-G6-C7)
        # ------------------------------------------------------------------
        dur = 0.28
        n = int(rate * dur)
        l, r = [], []
        notes = [1046.5, 1318.5, 1568.0, 2093.0]
        for i in range(n):
            t = i / rate
            s = 0.0
            for idx, freq in enumerate(notes):
                note_start = idx * 0.048
                if t >= note_start:
                    dt_note = t - note_start
                    note_env = math.exp(-dt_note * 17.0)
                    s += (
                        math.sin(2.0 * math.pi * freq * dt_note)
                        + 0.22 * math.sin(2.0 * math.pi * freq * 2.0 * dt_note)
                    ) * note_env
            val = max(-32767, min(32767, int(s * 11500)))
            l.append(val)
            r.append(val)
        self.sounds["pickup"] = self._pack_stereo(l, r, volume=0.62)

        # ------------------------------------------------------------------
        # 7. DASH: Warp thruster whoosh (filtered noise sweep + stereo pan)
        # ------------------------------------------------------------------
        dur = 0.16
        n = int(rate * dur)
        l, r = [], []
        noise_state = 0.0
        for i in range(n):
            t = i / rate
            u = i / n
            env = math.sin(u * math.pi)
            f = 580.0 * math.exp(-4.2 * u) + 65.0
            tone = math.sin(2.0 * math.pi * f * t) * 0.42
            raw_noise = rng.uniform(-1.0, 1.0)
            noise_state += (raw_noise - noise_state) * 0.36
            s = (tone + noise_state * 0.58) * env
            val = math.tanh(s * 1.5) * 32000 * 0.42
            l.append(val * (1.0 - u * 0.6))
            r.append(val * (0.4 + u * 0.6))
        self.sounds["dash"] = self._pack_stereo(l, r, volume=0.60)

        # ------------------------------------------------------------------
        # 8. HIT: Snappy armor impact tick (metallic high-frequency transient)
        # ------------------------------------------------------------------
        dur = 0.038
        n = int(rate * dur)
        l, r = [], []
        for i in range(n):
            t = i / rate
            u = i / n
            env = math.exp(-u * 28.0)
            f = 1200.0 * math.exp(-6.5 * u) + 280.0
            s = math.sin(2.0 * math.pi * f * t) * env
            val = max(-32767, min(32767, int(s * 14000)))
            l.append(val)
            r.append(val)
        self.sounds["hit"] = self._pack_stereo(l, r, volume=0.38)

        # ------------------------------------------------------------------
        # 9. CLICK: Crisp holographic interface button tap
        # ------------------------------------------------------------------
        dur = 0.045
        n = int(rate * dur)
        l, r = [], []
        for i in range(n):
            t = i / rate
            u = i / n
            env = math.exp(-u * 24.0)
            f = 1450.0 + 820.0 * (1.0 - u)
            s = (math.sin(2.0 * math.pi * f * t) * 0.72 + math.sin(2.0 * math.pi * f * 2.1 * t) * 0.28) * env
            val = max(-32767, min(32767, int(s * 24000)))
            l.append(val)
            r.append(val)
        self.sounds["click"] = self._pack_stereo(l, r, volume=0.70)

        # ------------------------------------------------------------------
        # 10. SELECT: Bright two-tone confirmation chime
        # ------------------------------------------------------------------
        dur = 0.088
        n = int(rate * dur)
        l, r = [], []
        for i in range(n):
            t = i / rate
            u = i / n
            env = (1.0 - u) ** 1.6
            f = 920.0 if u < 0.38 else 1380.0
            s = (math.sin(2.0 * math.pi * f * t) * 0.75 + math.sin(2.0 * math.pi * f * 2.0 * t) * 0.25) * env
            val = max(-32767, min(32767, int(s * 25000)))
            l.append(val)
            r.append(val)
        self.sounds["select"] = self._pack_stereo(l, r, volume=0.72)

        # ------------------------------------------------------------------
        # 11. HOVER: Soft tactile micro-blip
        # ------------------------------------------------------------------
        dur = 0.024
        n = int(rate * dur)
        l, r = [], []
        for i in range(n):
            t = i / rate
            u = i / n
            env = math.exp(-u * 32.0)
            f = 1950.0 * (1.0 - u * 0.25)
            s = math.sin(2.0 * math.pi * f * t) * env
            val = max(-32767, min(32767, int(s * 16000)))
            l.append(val)
            r.append(val)
        self.sounds["hover"] = self._pack_stereo(l, r, volume=0.45)

    def play(self, name: str) -> None:
        sound = self.sounds.get(name)
        if sound is not None:
            sound.play()

    def set_volume(self, volume: float) -> None:
        self.master_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.master_volume)
