#!/bin/bash

set -e

echo "Creating AppDir..."
mkdir -p build/AppDir/usr/bin
echo "Copying files from AppImage..."
cp AppImage/* build/AppDir
echo "Copying Útil paisagem internals..."
cp -r dist/utilpaisagem/_internal/ build/AppDir/usr/bin/
echo "Copying executable..."
cp dist/utilpaisagem/utilpaisagem build/AppDir/usr/bin/
echo "Creating AppImage..."
ARCH=x86_64 build/appimagetool-x86_64.AppImage build/AppDir dist/Util_paisagem.AppImage
echo "Deleting build directory..."
rm -r build/AppDir