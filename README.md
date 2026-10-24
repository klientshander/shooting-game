# COSMIC RIFT: Starfall — Endless Survival Mode

A high-intensity, procedurally rendered 2D arcade shooter built with Pygame. The gameplay is pure Python; an optional pybind11 extension accelerates circle collision checks in C++. No external art or audio assets are required.

## Features

- **Endless Mode With Progressive Difficulty:** Survive as long as you can against ever-adapting hostiles. Enemy health, damage, speed, spawn rates, and firing frequencies increase dynamically over survival time.
- **Automatic Continuous Shooting:** Weapons auto-fire towards the cursor with consistent timing so you can focus on maneuvering and evasive maneuvers.
- **Predictable Straight-Line Enemies:** Enemies spawn from designated positions and traverse the arena in straight lines while firing straight-line energy shots.
- **Cosmic Boss Milestones:** Formidable cosmic bosses emerge at survival milestones (every 2 minutes) with expanding bullet patterns and phase shifts.
- **Instant Restart & High Scores:** Die in the rift? Restart immediately with one click or keypress without picking difficulties. Best score and longest survival duration are saved locally.

## Requirements

- Python 3.10 or newer
- Pygame-compatible pygame-ce 2.5.8+
- Optional: a C++17 compiler and pybind11 to build the collision extension

## Install and Play

Open this folder in VS Code / PowerShell, then run:

```powershell
python -m pip install -r requirements.txt
python main.py
```

Or double-click `run_game.bat` on Windows.

## Build a Windows release

On Windows, install the build dependencies and create a standalone release folder:

```powershell
python -m pip install -r requirements-build.txt
.\build_windows.bat
```

The distributable is `dist/cosmic-rift-windows.zip` (or the `dist/Cosmic Rift/` folder). Recipients can extract the archive and launch `Cosmic Rift.exe` without installing Python. Save data is stored in `%LOCALAPPDATA%\Cosmic Rift\highscore.json`.

## Play in a web browser

The browser build is published to the `gh-pages` branch whenever changes are pushed to `main`. To enable the website the first time, open the repository's **Settings → Pages**, choose **Deploy from a branch**, select **gh-pages** and **/(root)**, then save. After GitHub Pages finishes deploying, play at:

<https://klientshander.github.io/shooting-game/>

The first visit may take a little while to load the browser runtime. Use WASD or the arrow keys to move, Shift to dash, Q for the rift pulse, and Escape to pause. Browser highscores and settings are stored in local browser storage.

To build and preview the browser version locally:

```powershell
python -m pip install pygbag
python -m pygbag main.py
```

Then open <http://localhost:8000>. The web build uses the Python collision fallback; the optional C++ extension is only for desktop builds.

## Controls

| Input | Action |
| --- | --- |
| **WASD** or arrow keys | Move ship |
| **Mouse Cursor** | Aim weapons (shooting is automatic and continuous) |
| **Shift** | Dash and briefly evade damage |
| **Q** | Rift pulse: damage nearby enemies and boss (9-second cooldown) |
| **Escape** | Pause / resume |
| **Enter / Space / R** | Select menu options / Quick restart on game over |

## Difficulty Progression

- **0–30s (Tier 1):** Basic scouts and slow heavy tanks with base health and speed.
- **30–60s (Tier 2):** Enemies gain additional health and move slightly faster; hunters begin appearing.
- **1–2 min (Tier 3):** Spawns accelerate, enemy energy bullets become more frequent, and bombers join the fray.
- **2–5 min (Tier 4):** Elite cruisers enter combat with heavy armor and burst fire; cosmic boss emerges at 2 minutes.
- **5+ min (Tier 5+):** Relentless survival challenge with high spawn density, increased damage, and milestone bosses every 2 minutes.

## Project Layout

```text
main.py                 Game loop, state management, auto-fire orchestration, and input
settings.py             Display dimensions, color constants, characters, and save paths
game/                   Player, straight-line enemies, boss, particles, audio, UI, waves
game/waves.py           Endless progression manager, time-based tier scaling & milestones
cpp/                    C++17 collision implementation, pybind11 binding, and build script
assets/saves/           Local high-score and survival records (JSON)
run_game.bat            Convenient Windows launcher
```
