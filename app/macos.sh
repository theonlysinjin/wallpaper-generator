#!/bin/bash

# Install required packages
pip3 install -r requirements.txt

# Clean previous builds more thoroughly
rm -rf build dist *.pkg

# Force remove any lingering files
if [ -d "build" ]; then
    chmod -R 755 build
    rm -rf build
fi
if [ -d "dist" ]; then
    chmod -R 755 dist
    rm -rf dist
fi

# Build the app bundle
python3 setup.py py2app || {
    echo "Failed to build app bundle"
    exit 1
}

# Find the actual app name in dist directory
ls -lah dist
APP_NAME=$(ls dist | grep '\.app$')
if [ -z "$APP_NAME" ]; then
    echo "Error: No .app bundle found in dist directory"
    exit 1
fi

# Create package
pkgbuild --root "dist/$APP_NAME" \
         --identifier com.theonlysinjin.wallpaper-generator \
         --install-location "/Applications/$APP_NAME" \
         --version 1.0.0 \
         AIWallpaper.pkg
