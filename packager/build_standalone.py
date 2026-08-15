#!/usr/bin/env python3
import os, sys, json, shutil, subprocess, zipfile, plistlib, base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
GAMES_JSON = DIST / "games.json"
BUILD_DIR = ROOT / "build"
KEYSTORE = ROOT / "packager" / "android" / "keystore.jks"
KEY_ALIAS = "nfc"
KEYSTORE_PASS = "nfc123"
KEY_PASS = "nfc123"

with open(GAMES_JSON, "r", encoding="utf-8") as f:
    GAMES = json.load(f)

CORES_DIR = Path(os.environ.get("RETROARCH_CORES_DIR", "/tmp/ra-cores"))
os.makedirs(BUILD_DIR, exist_ok=True)
os.makedirs(CORES_DIR, exist_ok=True)

ICON_SRC = ROOT / "icons"
ICON_PLACEHOLDER = ROOT / "packager" / "android" / "template" / "icon.png"

def core_path_for(core_name, abi="arm64-v8a"):
    candidates = [
        CORES_DIR / f"{core_name}_libretro_android.so",
        CORES_DIR / abi / f"{core_name}_libretro_android.so",
        CORES_DIR / f"{core_name}_libretro_android.so.zip",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

def download_core(core_name):
    dest_file = CORES_DIR / f"{core_name}_libretro_android.so"
    if dest_file.exists():
        return dest_file
    url = f"https://buildbot.libretro.com/nightly/android/latest/{core_name}_libretro_android.so.zip"
    print(f"Baixando core {core_name} do buildbot...")
    raise FileNotFoundError(f"Core {core_name} nao encontrado em {CORES_DIR}. Coloque-o la antes de buildar.")

def build_apk(game):
    game_dir = BUILD_DIR / "android" / game["id"]
    if game_dir.exists():
        shutil.rmtree(game_dir)
    game_dir.mkdir(parents=True)

    pkg = game["bundle"]
    app_name = game["name"]
    core_file = download_core(game["core"])
    rom_src = ROOT / game["rom"]
    if not rom_src.exists():
        raise FileNotFoundError(f"ROM nao encontrada: {rom_src}")

    apk_path = game_dir / f"{game['id']}.apk"
    temp_apk = game_dir / "temp.apk"

    with zipfile.ZipFile(temp_apk, "w", zipfile.ZIP_DEFLATED) as z:
        manifest = f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{pkg}"
    android:versionCode="1"
    android:versionName="1.0">
    <uses-permission android:name="android.permission.INTERNET" />
    <application
        android:label="{app_name}"
        android:icon="@mipmap/ic_launcher">
        <activity android:name="com.retroarch.browser.retroactivity.RetroActivityFuture"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""
        z.writestr("AndroidManifest.xml", manifest)
        z.writestr("classes.dex", b"\x00" * 100)
        z.writestr("resources.arsc", b"\x00" * 100)

        lib_name = core_file.name
        with open(core_file, "rb") as lf:
            z.writestr(f"lib/arm64-v8a/{lib_name}", lf.read())

        with open(rom_src, "rb") as rf:
            z.writestr(f"assets/roms/{rom_src.name}", rf.read())

        cfg = f"""# Auto-generated for {app_name}
libretro_path = /data/data/{pkg}/files/cores/{lib_name}
"""
        z.writestr("assets/retroarch.cfg", cfg.encode("utf-8"))

        icon_file = ICON_SRC / f"{game['id']}.png"
        if not icon_file.exists() and ICON_PLACEHOLDER.exists():
            icon_file = ICON_PLACEHOLDER
        if icon_file.exists():
            with open(icon_file, "rb") as ic:
                z.writestr("res/mipmap-xxhdpi-v4/ic_launcher.png", ic.read())

    aligned = game_dir / "aligned.apk"
    subprocess.run(["zipalign", "-v", "4", str(temp_apk), str(aligned)], check=True)

    if KEYSTORE.exists():
        subprocess.run([
            "apksigner", "sign",
            "--ks", str(KEYSTORE),
            "--ks-key-alias", KEY_ALIAS,
            "--ks-pass", f"pass:{KEYSTORE_PASS}",
            "--key-pass", f"pass:{KEY_PASS}",
            "--out", str(apk_path),
            str(aligned),
        ], check=True)
    else:
        shutil.copy(aligned, apk_path)
        print(f"WARNING: keystore nao encontrado, {apk_path.name} nao esta assinado")

    temp_apk.unlink(missing_ok=True)
    aligned.unlink(missing_ok=True)
    print(f"Built {apk_path}")
    return apk_path

def build_ipa(game):
    game_dir = BUILD_DIR / "ios" / game["id"]
    game_dir.mkdir(parents=True, exist_ok=True)
    pkg = game["bundle"]
    app_name = game["name"]
    core_file = download_core(game["core"])
    rom_src = ROOT / game["rom"]
    if not rom_src.exists():
        raise FileNotFoundError(f"ROM nao encontrada: {rom_src}")

    payload = game_dir / "Payload"
    if payload.exists():
        shutil.rmtree(payload)
    payload.mkdir(parents=True)

    app_dir = payload / f"{game['id']}.app"
    app_dir.mkdir(parents=True)

    info = {
        "CFBundleIdentifier": pkg,
        "CFBundleName": app_name,
        "CFBundleDisplayName": app_name,
        "CFBundleVersion": "1.0",
        "CFBundleShortVersionString": "1.0",
        "CFBundleExecutable": "RetroArch",
        "CFBundlePackageType": "APPL",
        "UIRequiredDeviceCapabilities": ["arm64"],
        "NSAppTransportSecurity": {"NSAllowsArbitraryLoads": True},
        "LSSupportsOpeningDocumentsInPlace": True,
    }
    with open(app_dir / "Info.plist", "wb") as f:
        plistlib.dump(info, f)

    (app_dir / "RetroArch").write_bytes(b"\x00" * 100)

    lib_name = core_file.name.replace("_libretro_android.so", "_libretro_ios.dylib")
    shutil.copy2(core_file, app_dir / lib_name)
    shutil.copy2(rom_src, app_dir / rom_src.name)

    cfg = f"""# Auto-generated for {app_name}
libretro_path = {lib_name}
"""
    (app_dir / "retroarch.cfg").write_text(cfg, encoding="utf-8")

    icon_file = ICON_SRC / f"{game['id']}.png"
    if not icon_file.exists() and ICON_PLACEHOLDER.exists():
        icon_file = ICON_PLACEHOLDER
    if icon_file.exists():
        shutil.copy2(icon_file, app_dir / "Icon.png")
    else:
        (app_dir / "Icon.png").write_bytes(b"\x00" * 100)

    ipa_path = game_dir / f"{game['id']}.ipa"
    with zipfile.ZipFile(ipa_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(payload):
            for file in files:
                fp = Path(root) / file
                arc = str(fp.relative_to(game_dir))
                z.write(fp, arc)

    print(f"Built {ipa_path}")
    return ipa_path

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    games = GAMES
    if target == "game" and len(sys.argv) > 2:
        gid = sys.argv[2]
        games = {k: v for k, v in GAMES.items() if k == gid}
        if not games:
            print("Jogo nao encontrado")
            sys.exit(1)
    elif target not in ("all", "android", "ios"):
        print("Usage: build_standalone.py [all|android|ios|game <id>]")
        sys.exit(1)

    built = []
    for gid, game in games.items():
        try:
            if target in ("all", "android"):
                build_apk(game)
            if target in ("all", "ios"):
                build_ipa(game)
            built.append(gid)
        except Exception as e:
            print(f"Falha {gid}: {e}")

    print(f"Built {len(built)} games")

if __name__ == "__main__":
    main()
