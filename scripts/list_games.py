#!/usr/bin/env python3
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMES_JSON = ROOT / "dist" / "games.json"

with open(GAMES_JSON, "r", encoding="utf-8") as f:
    GAMES = json.load(f)

print("Games disponiveis para build standalone:")
for gid, cfg in GAMES.items():
    print(f"  {gid:40s} -> {cfg['rom']}")
