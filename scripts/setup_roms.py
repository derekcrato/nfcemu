#!/usr/bin/env python3
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = Path(__file__).resolve().parent
RES_DIR = DATA_DIR / "res"

icons = {
    "gba": "Game Boy Advance",
    "gbx": "Game Boy",
    "md": "Mega Drive",
    "ms": "Master System",
    "nes": "NES",
    "snes": "SNES",
    "ps1": "PlayStation",
}

for folder, label in icons.items():
    path = RES_DIR / folder
    path.mkdir(parents=True, exist_ok=True)
    print(f"{folder:4s} -> {path}")
