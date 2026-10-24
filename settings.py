"""Shared display, color palette, character, and skill definitions for COSMIC RIFT: Starfall."""

import os
import sys
from pathlib import Path

WIDTH = 1280
HEIGHT = 720
FPS = 60
TITLE = "COSMIC RIFT: Starfall"

# Deep royal space palette
BACKGROUND = (6, 10, 48)
PANEL = (14, 20, 64)
WHITE = (245, 248, 255)
CYAN = (72, 230, 255)
MAGENTA = (235, 75, 245)
GOLD = (255, 215, 80)
ORANGE = (255, 130, 45)

if getattr(sys, "frozen", False):
    SAVE_PATH = str(
        Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        / "Cosmic Rift"
        / "highscore.json"
    )
else:
    SAVE_PATH = "assets/saves/highscore.json"

_ASSET_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "assets"


def asset_path(filename: str) -> str:
    return str(_ASSET_ROOT / filename)

CHARACTERS = [
    {"name": "ASTRA", "color": (88, 231, 255), "description": "Balanced Starblade", "health": 4, "speed": 1.0, "damage": 1},
    {"name": "NOVA", "color": (255, 105, 220), "description": "Swift Rift Dancer", "health": 3, "speed": 1.16, "damage": 1},
    {"name": "SOL", "color": (255, 198, 93), "description": "Solar Striker", "health": 5, "speed": 0.92, "damage": 2},
]

# The random in-game skill orbs
SKILLS = [
    {
        "id": "attack_speed",
        "name": "Increase attack speed",
        "short_name": "ATTACK SPEED",
        "theme": "blue",
        "duration": 20.0,
    },
    {
        "id": "split_bullets",
        "name": "Shotgun split bullets",
        "short_name": "SHOTGUN",
        "theme": "blue",
        "duration": 30.0,
    },
    {
        "id": "piercing",
        "name": "Piercing bullets (Pass through enemies)",
        "short_name": "PIERCING",
        "theme": "blue",
        "duration": 20.0,
    },
    {
        "id": "shield",
        "name": "Shield",
        "short_name": "SHIELD",
        "theme": "purple",
        "duration": 0.0,
    },
    {
        "id": "meteor_explosion",
        "name": "Destroy meteor with small explosion",
        "short_name": "METEOR EXPLOSION",
        "theme": "purple",
        "duration": 20.0,
    },
    {
        "id": "ultimate",
        "name": "Ultimate Charge [Q]",
        "short_name": "ULTIMATE [Q]",
        "theme": "gold",
        "duration": 0.0,
    },
]
