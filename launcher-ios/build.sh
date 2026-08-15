#!/bin/bash
set -e

cd "$(dirname "$0")"

xcodebuild -project NFCLauncher.xcodeproj \
  -scheme NFCLauncher \
  -configuration Release \
  -archivePath build/NFCLauncher.xcarchive \
  archive

xcodebuild -exportArchive \
  -archivePath build/NFCLauncher.xcarchive \
  -exportPath build \
  -exportOptionsPlist App/ExportOptions.plist
