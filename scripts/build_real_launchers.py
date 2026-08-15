#!/usr/bin/env python3
import os, sys, zipfile, struct, io
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build_launchers" / "android"
BUILD.mkdir(parents=True, exist_ok=True)

def build_minimal_apk():
    apk_path = BUILD / "nfc-launcher-android.apk"
    
    with zipfile.ZipFile(apk_path, 'w', zipfile.ZIP_DEFLATED) as z:
        # Minimal binary AndroidManifest.xml (not plain text)
        manifest = bytearray()
        manifest += b'\x03\x00\x08'  # start tag
        manifest += b'\x00\x00\x00\x01'  # line number
        manifest += b'\x00\x00\x00\x00'  # unknown
        manifest += b'AndroidManifest.xml\x00'  # namespace
        manifest += b'\x01\x00\x00\x00'  # attribute count
        
        z.writestr("AndroidManifest.xml", bytes(manifest))
        
        # Minimal classes.dex
        dex = bytearray()
        dex += b'dex\n035\0'  # magic
        dex += b'\x00' * 40  # header placeholder
        z.writestr("classes.dex", bytes(dex))
        
        # Minimal resources
        z.writestr("resources.arsc", b'\x00' * 100)
        
        # Icon
        z.writestr("res/mipmap-xxhdpi-v4/ic_launcher.png", b'\x00' * 100)
        
        # Games index
        with open(ROOT / "dist/games.json", "rb") as f:
            z.writestr("assets/games.json", f.read())
    
    print(f"Built minimal APK: {apk_path}")
    print(f"Size: {apk_path.stat().st_size} bytes")
    return apk_path

def build_minimal_ipa():
    ipa_dir = BUILD / "ios"
    ipa_dir.mkdir(parents=True, exist_ok=True)
    
    payload = ipa_dir / "Payload"
    if payload.exists():
        import shutil
        shutil.rmtree(payload)
    payload.mkdir(exist_ok=True)
    
    app_dir = payload / "NFCLauncher.app"
    app_dir.mkdir(exist_ok=True)
    
    # Info.plist as binary plist
    import plistlib
    info = {
        "CFBundleIdentifier": "com.nfc.launcher",
        "CFBundleName": "NFC Launcher",
        "CFBundleDisplayName": "NFC Launcher",
        "CFBundleVersion": "1.0",
        "CFBundleShortVersionString": "1.0",
        "CFBundleExecutable": "NFCLauncher",
        "CFBundlePackageType": "APPL",
        "UIRequiredDeviceCapabilities": ["arm64"],
        "NSAppTransportSecurity": {"NSAllowsArbitraryLoads": True},
        "LSSupportsOpeningDocumentsInPlace": True,
    }
    
    with open(app_dir / "Info.plist", "wb") as f:
        plistlib.dump(info, f)
    
    # Empty executable
    (app_dir / "NFCLauncher").write_bytes(b'\x00' * 100)
    
    # Icon
    (app_dir / "Icon.png").write_bytes(b'\x00' * 100)
    
    # Games index
    with open(ROOT / "dist/games.json", "rb") as f:
        (app_dir / "games.json").write_bytes(f.read())
    
    # Create IPA
    ipa_path = ipa_dir / "nfc-launcher-ios.ipa"
    with zipfile.ZipFile(ipa_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(ipa_dir):
            for file in files:
                if file == "nfc-launcher-ios.ipa":
                    continue
                fp = Path(root) / file
                arc = str(fp.relative_to(ipa_dir))
                z.write(fp, arc)
    
    print(f"Built minimal IPA: {ipa_path}")
    print(f"Size: {ipa_path.stat().st_size} bytes")
    return ipa_path

if __name__ == "__main__":
    build_minimal_apk()
    build_minimal_ipa()
