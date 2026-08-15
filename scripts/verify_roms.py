#!/usr/bin/env python3
import os, sys, hashlib, json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
ROMS = PROJECT / "roms"
REPORT = PROJECT / "roms_integrity.json"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    if not ROMS.exists():
        print("PASTA ROMS AUSENTE")
        sys.exit(1)

    files = sorted([p for p in ROMS.rglob("*") if p.is_file()])
    data = {}
    for p in files:
        rel = str(p.relative_to(PROJECT)).replace("\\", "/")
        try:
            data[rel] = {
                "size": p.stat().st_size,
                "sha256": sha256(p)
            }
        except Exception as e:
            data[rel] = {"error": str(e)}

    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Verificadas {len(data)} ROMs em {REPORT}")
    for rel, info in data.items():
        if "error" in info:
            print(f"  ERRO: {rel} -> {info['error']}")
        else:
            print(f"  OK: {rel} ({info['size']} bytes)")

    sys.exit(0 if all("error" not in v for v in data.values()) else 2)

if __name__ == "__main__":
    main()
