#!/bin/bash

# Execute from repository's base dir

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
echo "Downloading latest quick-sharun.sh"
wget https://raw.githubusercontent.com/pkgforge-dev/Anylinux-AppImages/refs/heads/main/useful-tools/quick-sharun.sh
chmod +x quick-sharun.sh
echo "Wrapping libraries with quick sharun..." 
DESKTOP=AppImage/Util_paisagem.desktop ICON=AppImage/utilpaisagem.png OUTPUT_APPIMAGE=0 DEPLOY_GLIBC=1 APPDIR=build/AppDir \
USE_HOST_DRIVERS=1 ./quick-sharun.sh dist/utilpaisagem-appimage/Util_paisagem
echo "Copying Útil paisagem internals to AppDir..."
cp -r dist/utilpaisagem-appimage/_internal/ build/AppDir/shared/bin
echo "Copying Útil paisagem meta info to Appdir..."
mkdir -p build/Appdir/usr/share/metainfo/
cp AppImage/usr/share/metainfo/io.github.leandroarndt.Util_paisagem.metainfo.xml build/Appdir/usr/share/metainfo/
echo "Creating AppImage..."
ARCH=x86_64 ./appimagetool-x86_64.AppImage -u "gh-releases-zsync|leandroarndt|util-paisagem|latest|Util_paisagem-x86_64.AppImage.zsync" build/AppDir dist/Util_paisagem-x86_64.AppImage
echo "Moving zsync file..."
mv Util_paisagem-x86_64.AppImage.zsync dist
echo "Deleting build directory..."
rm -r build/AppDir
echo "Deleting appimagetool..."
rm appimagetool-x86_64.AppImage
echo "Deleting quick sharun script..."
rm quick-sharun.sh