"""Логика таймера."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from gi.repository import GLib

from .store import MODE_LABELS, Store

if TYPE_CHECKING:
    from gi.repository import Gio


class TimerEngine:
    def __init__(
        self,
        store: Store,
        on_notify: Callable[[str, str], None] | None = None,
        on_alarm: Callable[[], None] | None = None,
        on_tick_sound: Callable[[], None] | None = None,
    ) -> None:
        self.store = store
        self._on_notify = on_notify
        self._on_alarm = on_alarm
        self._on_tick_sound = on_tick_sound
        self._source_id: int | None = None

    def start(self) -> None:
        if self.store.timer["status"] == "running":
            return
        self.store.update_timer(status="running")
        if self._source_id is None:
            self._source_id = GLib.timeout_add_seconds(1, self._tick)

    def pause(self) -> None:
        self.store.update_timer(status="paused")
        self._clear_source()

    def skip(self) -> None:
        self._clear_source()
        self._complete_session(skipped=True)

    def switch_mode(self, mode: str) -> None:
        self.pause()
        self.store.set_mode(mode)

    def _clear_source(self) -> None:
        if self._source_id is not None:
            GLib.source_remove(self._source_id)
            self._source_id = None

    def _tick(self) -> bool:
        timer = self.store.timer
        if timer["status"] != "running":
            return False

        settings = self.store.settings
        if settings["tick_sound_enabled"] and timer["seconds_left"] > 0 and self._on_tick_sound:
            self._on_tick_sound()

        if timer["seconds_left"] <= 1:
            self._on_timer_complete()
            return False

        self.store.update_timer(seconds_left=timer["seconds_left"] - 1)
        return True

    def _on_timer_complete(self) -> None:
        self._clear_source()
        timer = self.store.timer
        settings = self.store.settings

        if settings["sound_enabled"] and self._on_alarm:
            self._on_alarm()

        mode_label = MODE_LABELS.get(timer["mode"], timer["mode"])
        if self._on_notify:
            self._on_notify("Таймер завершён", f"{mode_label} окончен")

        self._complete_session(skipped=False)

    def _complete_session(self, skipped: bool) -> None:
        timer = self.store.timer
        settings = self.store.settings

        if timer["mode"] == "pomodoro" and not skipped:
            completed = timer["pomodoros_completed"] + 1
            self.store.increment_active_task_pomodoro()
            interval = int(settings["long_break_interval"])
            next_mode = "long_break" if completed % interval == 0 else "short_break"
            auto_start = settings["auto_start_breaks"]

            self.store.update_timer(
                pomodoros_completed=completed,
                mode=next_mode,
                status="running" if auto_start else "idle",
                seconds_left=self.store.minutes_for_mode(next_mode) * 60,
            )
            if auto_start:
                self._source_id = GLib.timeout_add_seconds(1, self._tick)
        elif timer["mode"] != "pomodoro":
            auto_start = settings["auto_start_pomodoros"]
            self.store.update_timer(
                mode="pomodoro",
                status="running" if auto_start else "idle",
                seconds_left=self.store.minutes_for_mode("pomodoro") * 60,
            )
            if auto_start:
                self._source_id = GLib.timeout_add_seconds(1, self._tick)
        else:
            self.store.update_timer(
                status="idle",
                seconds_left=self.store.minutes_for_mode("pomodoro") * 60,
            )
