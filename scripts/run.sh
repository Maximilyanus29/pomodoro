#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
NATIVE_DIR="$ROOT_DIR/app/native"

if ! python3 -c "import gi; gi.require_version('Gtk','4.0'); gi.require_version('Adw','1')" 2>/dev/null; then
  echo "Установите зависимости:" >&2
  echo "  sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1" >&2
  exit 1
fi

cd "$NATIVE_DIR"
exec python3 -m pomodoro
