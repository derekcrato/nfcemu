#!/usr/bin/env python3
import os, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.json"

with open(CONFIG, "r", encoding="utf-8") as f:
    cfg = json.load(f)

repo = cfg.get("github_repo", "")
if not repo or repo == "user/nfc":
    print("Edite config.json e defina github_repo com seu repositorio, ex: meuuser/nfc")
    sys.exit(1)

# Update games.json if exists
games_json = ROOT / "dist" / "games.json"
if games_json.exists():
    with open(games_json, "r", encoding="utf-8") as f:
        games = json.load(f)
    for k in games:
        games[k]["url"] = f"https://raw.githubusercontent.com/{repo}/main/{games[k]['rom']}"
    with open(games_json, "w", encoding="utf-8") as f:
        json.dump(games, f, indent=2, ensure_ascii=False)
    print(f"Updated {len(games)} game URLs to repo {repo}")
else:
    print("Execute generate_nfc_links.py primeiro")
