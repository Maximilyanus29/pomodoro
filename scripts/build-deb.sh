#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${1:-1.0.0}"
PKG_NAME="pomodoro-timer"
BUILD_DIR="$ROOT_DIR/build/deb-root"
OUTPUT="$ROOT_DIR/build/${PKG_NAME}_${VERSION}_all.deb"

rm -rf "$ROOT_DIR/build"
mkdir -p \
  "$BUILD_DIR/DEBIAN" \
  "$BUILD_DIR/usr/bin" \
  "$BUILD_DIR/usr/lib/pomodoro-timer/pomodoro" \
  "$BUILD_DIR/usr/share/applications" \
  "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps"

cp "$ROOT_DIR/app/native/pomodoro/"*.py "$BUILD_DIR/usr/lib/pomodoro-timer/pomodoro/"
cp "$ROOT_DIR/packaging/io.pomodoro.Timer.desktop" "$BUILD_DIR/usr/share/applications/"
cp "$ROOT_DIR/packaging/icons/io.pomodoro.Timer.svg" \
  "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/"

cat > "$BUILD_DIR/usr/bin/pomodoro-timer" <<'EOF'
#!/bin/sh
export PYTHONPATH=/usr/lib/pomodoro-timer
exec python3 -m pomodoro "$@"
EOF
chmod 755 "$BUILD_DIR/usr/bin/pomodoro-timer"

cat > "$BUILD_DIR/DEBIAN/control" <<EOF
Package: ${PKG_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1, libcanberra-gtk3-module
Maintainer: Pomodoro Timer <pomodoro@localhost>
Description: Pomodoro timer for Ubuntu
 Native GTK4 pomodoro timer inspired by Pomofocus.
 Includes task list, notifications and customizable intervals.
EOF

fakeroot dpkg-deb --build "$BUILD_DIR" "$OUTPUT"
echo "Собран пакет: $OUTPUT"
