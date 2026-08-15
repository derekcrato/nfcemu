#!/usr/bin/env python3
import os, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROMS_DIR = ROOT / "roms"
OUTPUT_DIR = ROOT / "dist"
CONFIG = {}

SYSTEM_CORES = {
    "gba": "mgba",
    "gbx": "gambatte",
    "md": "genesis_plus_gx",
    "ms": "genesis_plus_gx",
    "nes": "fceumm",
    "snes": "snes9x",
    "ps1": "mednafen_psx",
}

SYSTEM_EXT = {
    "gba": ["gba"],
    "gbx": ["gb", "gbc"],
    "md": ["md", "gen", "bin", "iso"],
    "ms": ["sms", "bin"],
    "nes": ["nes", "zip"],
    "snes": ["sfc", "smc", "zip"],
    "ps1": ["iso", "cue", "bin", "chd"],
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

for system, folder in sorted(SYSTEM_CORES.items()):
    system_dir = ROMS_DIR / system
    if not system_dir.is_dir():
        continue
    for fname in sorted(system_dir.iterdir()):
        if not fname.is_file():
            continue
        base, ext = os.path.splitext(fname.name)
        ext = ext.lower().lstrip(".")
        if ext not in SYSTEM_EXT[system]:
            continue
        game_id = f"{system}-{base}".replace(" ", "_").replace("(", "").replace(")", "").replace("'", "")
        game_config = {
            "id": game_id,
            "name": base,
            "system": system,
            "core": SYSTEM_CORES[system],
            "rom": f"roms/{system}/{fname.name}",
            "icon": f"icons/{game_id}.png",
            "bundle": f"com.nfc.game.{game_id.lower()}",
            "url": f"https://raw.githubusercontent.com/{os.environ.get('GITHUB_REPOSITORY', 'derekcrato/nfcemu')}/main/roms/{system}/{fname.name}",
        }
        CONFIG[game_id] = game_config

with open(OUTPUT_DIR / "games.json", "w", encoding="utf-8") as f:
    json.dump(CONFIG, f, indent=2, ensure_ascii=False)

print(f"Generated {len(CONFIG)} game entries in {OUTPUT_DIR}/games.json")
