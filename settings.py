"""Shared display, color palette, character, and skill definitions for COSMIC RIFT: Starfall."""

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

SAVE_PATH = "assets/saves/highscore.json"

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
        "duration": 16.0,
    },
    {
        "id": "split_bullets",
        "name": "Split bullets",
        "short_name": "SPLIT BULLETS",
        "theme": "blue",
        "duration": 16.0,
    },
    {
        "id": "shield",
        "name": "Shield",
        "short_name": "SHIELD",
        "theme": "purple",
        "duration": 16.0,
    },
    {
        "id": "meteor_explosion",
        "name": "Destroy meteor with small explosion",
        "short_name": "METEOR EXPLOSION",
        "theme": "purple",
        "duration": 16.0,
    },
    {
        "id": "ultimate",
        "name": "Ultimate Charge [Q]",
        "short_name": "ULTIMATE [Q]",
        "theme": "gold",
        "duration": 0.0,
    },
]
