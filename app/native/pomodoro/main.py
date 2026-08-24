"""Точка входа GTK-приложения."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

import sys

from gi.repository import Adw, Gio

from .store import Store
from .window import MainWindow

APP_ID = "io.pomodoro.Timer"


class PomodoroApp(Adw.Application):
    def __init__(self) -> None:
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.store = Store()
        self.connect("activate", self._on_activate)
        self.connect("shutdown", self._on_shutdown)

    def _on_activate(self, _app: Adw.Application) -> None:
        window = self.props.active_window
        if not window:
            window = MainWindow(self, self.store)
        window.present()

    def _on_shutdown(self, _app: Adw.Application) -> None:
        self.store._save()


def main() -> int:
    Adw.init()
    app = PomodoroApp()
    return app.run(sys.argv)
