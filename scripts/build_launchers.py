#!/usr/bin/env python3
import os, sys, json, shutil, subprocess, zipfile, plistlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAUNCHER_ANDROID = ROOT / "launcher-android"
LAUNCHER_IOS = ROOT / "launcher-ios"
BUILD = ROOT / "build_launchers"

def build_android():
    print("Building Android launcher...")
    
    # Create minimal APK structure
    apk_dir = BUILD / "android"
    apk_dir.mkdir(parents=True, exist_ok=True)
    
    apk_path = apk_dir / "nfc-launcher-android.apk"
    
    with zipfile.ZipFile(apk_path, 'w', zipfile.ZIP_DEFLATED) as z:
        # AndroidManifest.xml
        manifest = b'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.nfc.launcher"
    android:versionCode="1"
    android:versionName="1.0">
    <uses-permission android:name="android.permission.NFC" />
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-feature android:name="android.hardware.nfc" android:required="true" />
    <application
        android:label="NFC Launcher"
        android:icon="@mipmap/ic_launcher">
        <activity
            android:name="com.nfc.launcher.MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
            <intent-filter>
                <action android:name="android.nfc.action.NDEF_DISCOVERED" />
                <category android:name="android.intent.category.DEFAULT" />
                <data android:scheme="https"
                      android:host="derekcrato.github.io"
                      android:pathPrefix="/nfcemu/" />
            </intent-filter>
            <intent-filter>
                <action android:name="android.intent.action.VIEW" />
                <category android:name="android.intent.category.DEFAULT" />
                <category android:name="android.intent.category.BROWSABLE" />
                <data android:scheme="com.nfc.launcher" />
            </intent-filter>
        </activity>
    </application>
</manifest>'''
        z.writestr("AndroidManifest.xml", manifest)
        
        # Empty classes.dex
        z.writestr("classes.dex", b"\x00" * 100)
        
        # Resources
        z.writestr("resources.arsc", b"\x00" * 100)
        
        # Icon
        z.writestr("res/mipmap-xxhdpi-v4/ic_launcher.png", b"\x00" * 100)
        
        # Games index
        with open(ROOT / "dist/games.json", "rb") as f:
            z.writestr("assets/games.json", f.read())
    
    # Align
    aligned = apk_dir / "aligned.apk"
    if shutil.which("zipalign"):
        subprocess.run(["zipalign", "-v", "4", str(apk_path), str(aligned)], check=True)
        apk_path.unlink()
        aligned.rename(apk_path)
    
    print(f"Built Android launcher: {apk_path}")
    return apk_path

def build_ios():
    print("Building iOS launcher...")
    
    # Create minimal IPA structure
    ipa_dir = BUILD / "ios"
    ipa_dir.mkdir(parents=True, exist_ok=True)
    
    payload = ipa_dir / "Payload"
    payload.mkdir(exist_ok=True)
    
    app_dir = payload / "NFCLauncher.app"
    app_dir.mkdir(exist_ok=True)
    
    # Info.plist
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
        "CFBundleURLTypes": [
            {
                "CFBundleURLName": "com.nfc.launcher",
                "CFBundleURLSchemes": ["com.nfc.launcher"]
            }
        ]
    }
    
    with open(app_dir / "Info.plist", "wb") as f:
        plistlib.dump(info, f)
    
    # Empty executable
    (app_dir / "NFCLauncher").write_bytes(b"\x00" * 100)
    
    # Icon
    (app_dir / "Icon.png").write_bytes(b"\x00" * 100)
    
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
    
    print(f"Built iOS launcher: {ipa_path}")
    return ipa_path

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if target in ("all", "android"):
        build_android()
    if target in ("all", "ios"):
        build_ios()

if __name__ == "__main__":
    main()
