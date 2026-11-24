#!/bin/bash

set -e

echo "Deleting old files..."
if [ -e "dist/Util_paisagem-x86_64.AppImage" ]; then
    rm dist/Util_paisagem-x86_64.AppImage
fi
if [ -e "dist/Util_paisagem-x86_64.AppImage.zsync" ]; then
    rm dist/Util_paisagem-x86_64.AppImage.zsync
fi
if [ -e "build/AppDir" ]; then
    rm -r build/AppDir
fi
echo "Downloading latest appimagetool..."
wget https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
echo "Creating AppDir..."
mkdir -p build/AppDir/usr/bin
echo "Copying files from AppImage..."
cp -r AppImage/* build/AppDir
echo "Copying Útil paisagem internals..."
cp -r dist/utilpaisagem/_internal/ build/AppDir/usr/bin/
echo "Copying executable..."
cp dist/utilpaisagem/utilpaisagem build/AppDir/usr/bin/
echo "Creating AppImage..."
ARCH=x86_64 ./appimagetool-x86_64.AppImage -u "gh-releases-zsync|leandroarndt|util-paisagem|latest|Util_paisagem-x86_64.AppImage.zsync" build/AppDir dist/Util_paisagem-x86_64.AppImage
echo "Moving zsync file..."
mv Util_paisagem-x86_64.AppImage.zsync dist
echo "Deleting build directory..."
rm -r build/AppDir
echo "Deleting appimagetool..."
rm appimagetool-x86_64.AppImage