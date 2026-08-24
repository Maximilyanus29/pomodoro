"""Состояние приложения и персистентность."""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

DEFAULT_SETTINGS = {
    "pomodoro_minutes": 25,
    "short_break_minutes": 5,
    "long_break_minutes": 15,
    "long_break_interval": 4,
    "auto_start_breaks": False,
    "auto_start_pomodoros": False,
    "sound_enabled": True,
    "tick_sound_enabled": False,
}

DEFAULT_TIMER = {
    "mode": "pomodoro",
    "status": "idle",
    "seconds_left": 25 * 60,
    "pomodoros_completed": 0,
    "active_task_id": None,
}

MODE_LABELS = {
    "pomodoro": "Pomodoro",
    "short_break": "Короткий перерыв",
    "long_break": "Длинный перерыв",
}


class Store:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (
            Path.home() / ".local" / "share" / "pomodoro" / "state.json"
        )
        self._listeners: list[Callable[[], None]] = []
        self.settings: dict[str, Any] = {}
        self.timer: dict[str, Any] = {}
        self.tasks: list[dict[str, Any]] = []
        self._load()

    def subscribe(self, callback: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(callback)

        def unsubscribe() -> None:
            if callback in self._listeners:
                self._listeners.remove(callback)

        return unsubscribe

    def _notify(self) -> None:
        self._save()
        for listener in list(self._listeners):
            listener()

    def _load(self) -> None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self.settings = {**DEFAULT_SETTINGS, **data.get("settings", {})}
                self.timer = {**DEFAULT_TIMER, **data.get("timer", {})}
                self.tasks = list(data.get("tasks", []))
                self._reset_timer_session()
                return
            except (json.JSONDecodeError, OSError):
                pass
        self.settings = deepcopy(DEFAULT_SETTINGS)
        self.timer = deepcopy(DEFAULT_TIMER)
        self.tasks = []

    def _reset_timer_session(self) -> None:
        """Новый запуск — полный интервал, без сохранённого отсчёта."""
        self.timer["status"] = "idle"
        self.timer["seconds_left"] = self.minutes_for_mode() * 60

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        timer_saved = {
            "mode": self.timer["mode"],
            "pomodoros_completed": self.timer["pomodoros_completed"],
            "active_task_id": self.timer["active_task_id"],
        }
        payload = {
            "settings": self.settings,
            "timer": timer_saved,
            "tasks": self.tasks,
        }
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def minutes_for_mode(self, mode: str | None = None) -> int:
        mode = mode or self.timer["mode"]
        if mode == "short_break":
            return int(self.settings["short_break_minutes"])
        if mode == "long_break":
            return int(self.settings["long_break_minutes"])
        return int(self.settings["pomodoro_minutes"])

    def update_settings(self, **kwargs: Any) -> None:
        self.settings.update(kwargs)
        self._notify()

    def update_timer(self, **kwargs: Any) -> None:
        self.timer.update(kwargs)
        self._notify()

    def set_mode(self, mode: str) -> None:
        minutes = self.minutes_for_mode(mode)
        self.timer.update(
            {
                "mode": mode,
                "status": "idle",
                "seconds_left": minutes * 60,
            }
        )
        self._notify()

    def reset_timer_for_current_mode(self) -> None:
        self.timer["seconds_left"] = self.minutes_for_mode() * 60
        self.timer["status"] = "idle"
        self._notify()

    def add_task(self, title: str, estimate: int) -> dict[str, Any]:
        task = {
            "id": str(uuid.uuid4()),
            "title": title.strip(),
            "estimate": max(1, estimate),
            "completed": 0,
            "done": False,
        }
        self.tasks.append(task)
        if not self.timer["active_task_id"]:
            self.timer["active_task_id"] = task["id"]
        self._notify()
        return task

    def remove_task(self, task_id: str) -> None:
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        if self.timer["active_task_id"] == task_id:
            nxt = next((t for t in self.tasks if not t["done"]), None)
            self.timer["active_task_id"] = nxt["id"] if nxt else None
        self._notify()

    def toggle_task_done(self, task_id: str) -> None:
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if not task:
            return
        task["done"] = not task["done"]
        if task["done"] and self.timer["active_task_id"] == task_id:
            nxt = next((t for t in self.tasks if not t["done"]), None)
            self.timer["active_task_id"] = nxt["id"] if nxt else None
        self._notify()

    def set_active_task(self, task_id: str) -> None:
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if not task or task["done"]:
            return
        self.timer["active_task_id"] = task_id
        self._notify()

    def increment_active_task_pomodoro(self) -> None:
        task_id = self.timer["active_task_id"]
        if not task_id:
            return
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if not task:
            return
        task["completed"] += 1
        if task["completed"] >= task["estimate"]:
            task["done"] = True
            nxt = next((t for t in self.tasks if not t["done"]), None)
            self.timer["active_task_id"] = nxt["id"] if nxt else None
        self._notify()

    def active_task(self) -> dict[str, Any] | None:
        task_id = self.timer["active_task_id"]
        if not task_id:
            return None
        return next((t for t in self.tasks if t["id"] == task_id), None)

    def window_title(self) -> str:
        timer = self.timer
        minutes, seconds = divmod(int(timer["seconds_left"]), 60)
        time_str = f"{minutes:02d}:{seconds:02d}"
        label = MODE_LABELS.get(timer["mode"], timer["mode"])
        task = self.active_task()
        task_part = f" — {task['title']}" if task else ""
        return f"{time_str} | {label}{task_part}"
