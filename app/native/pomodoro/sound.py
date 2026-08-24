"""Звук и системные уведомления."""

from __future__ import annotations

import shutil
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gi.repository import Adw


def play_alarm() -> None:
    for cmd in (
        ["canberra-gtk-play", "-i", "complete"],
        ["canberra-gtk-play", "-i", "bell"],
        ["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
    ):
        if shutil.which(cmd[0]):
            try:
                subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            except OSError:
                continue


def play_tick() -> None:
    if shutil.which("canberra-gtk-play"):
        try:
            subprocess.Popen(
                ["canberra-gtk-play", "-i", "click"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            pass


def send_notification(app: Adw.Application, title: str, body: str) -> None:
    from gi.repository import Gio

    notification = Gio.Notification.new(title)
    notification.set_body(body)
    app.send_notification("pomodoro-timer", notification)
