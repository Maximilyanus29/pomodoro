"""Главное окно приложения."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from .sound import play_alarm, play_tick, send_notification  # noqa: E402
from .store import MODE_LABELS, Store  # noqa: E402
from .timer import TimerEngine  # noqa: E402

MODE_CSS = {
    "pomodoro": "mode-pomodoro",
    "short_break": "mode-short-break",
    "long_break": "mode-long-break",
}

MODE_KEYS = list(MODE_CSS.keys())
EYE_REMINDER_INTERVAL_SECONDS = 5 * 60


class SettingsDialog(Adw.PreferencesWindow):
    def __init__(self, parent: Gtk.Window, store: Store) -> None:
        super().__init__(transient_for=parent, modal=True)
        self.set_title("Настройки")
        self.set_search_enabled(False)
        self.store = store

        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Интервалы")

        self._spinners: dict[str, Gtk.SpinButton] = {}
        for key, label, low, high in (
            ("pomodoro_minutes", "Pomodoro (мин)", 1, 60),
            ("short_break_minutes", "Короткий перерыв (мин)", 1, 30),
            ("long_break_minutes", "Длинный перерыв (мин)", 1, 60),
            ("long_break_interval", "Длинный перерыв каждые N помодоро", 2, 10),
        ):
            row = Adw.ActionRow(title=label)
            spin = Gtk.SpinButton.new_with_range(low, high, 1)
            spin.set_value(store.settings[key])
            spin.connect("value-changed", self._on_changed)
            row.add_suffix(spin)
            group.add(row)
            self._spinners[key] = spin

        page.add(group)

        toggles_group = Adw.PreferencesGroup(title="Поведение")
        self._switches: dict[str, Gtk.Switch] = {}
        for key, label in (
            ("auto_start_breaks", "Автостарт перерывов"),
            ("auto_start_pomodoros", "Автостарт помодоро"),
            ("sound_enabled", "Звук по окончании"),
            ("tick_sound_enabled", "Тикающий звук"),
        ):
            row = Adw.ActionRow(title=label)
            switch = Gtk.Switch(active=store.settings[key])
            switch.connect("state-set", self._on_switch)
            row.add_suffix(switch)
            toggles_group.add(row)
            self._switches[key] = switch

        page.add(toggles_group)
        self.add(page)

    def _on_changed(self, spin: Gtk.SpinButton) -> None:
        for key, widget in self._spinners.items():
            if widget is spin:
                self.store.update_settings(**{key: int(spin.get_value())})
                if self.store.timer["status"] == "idle":
                    self.store.reset_timer_for_current_mode()
                break

    def _on_switch(self, switch: Gtk.Switch, _state: bool) -> bool:
        for key, widget in self._switches.items():
            if widget is switch:
                self.store.update_settings(**{key: switch.get_active()})
                break
        return False


class TaskRow(Gtk.ListBoxRow):
    def __init__(self, task: dict, active: bool) -> None:
        super().__init__()
        self.task_id = task["id"]
        self.add_css_class("task-row")
        if active:
            self.add_css_class("task-active")

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(12)
        box.set_margin_end(12)

        self.check = Gtk.CheckButton(active=task["done"])
        self.check.set_tooltip_text("Отметить выполненной")
        box.append(self.check)

        title = Gtk.Label(label=task["title"], xalign=0, hexpand=True, wrap=True)
        if task["done"]:
            title.add_css_class("dim-label")
        box.append(title)

        meta = Gtk.Label(
            label=f"{task['completed']} / {task['estimate']}",
            css_classes=["dim-label"],
        )
        box.append(meta)

        delete_btn = Gtk.Button(icon_name="user-trash-symbolic")
        delete_btn.add_css_class("flat")
        delete_btn.set_tooltip_text("Удалить")
        delete_btn.set_valign(Gtk.Align.CENTER)
        box.append(delete_btn)

        self.set_child(box)
        self._title = title
        self._delete_btn = delete_btn


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application, store: Store) -> None:
        super().__init__(application=app)
        self.store = store
        self.set_title("Pomodoro")
        self.set_default_size(480, 720)
        self.add_css_class("pomodoro-window")

        self._timer = TimerEngine(
            store,
            on_notify=lambda t, b: send_notification(app, t, b),
            on_alarm=play_alarm,
            on_tick_sound=play_tick,
        )
        self._eye_reminder_dialog: Adw.MessageDialog | None = None
        self._eye_reminder_source_id = GLib.timeout_add_seconds(
            EYE_REMINDER_INTERVAL_SECONDS,
            self._show_eye_reminder,
        )

        self._updating = False
        self._build_ui()
        self._load_css()
        store.subscribe(self._refresh)
        self._refresh()

    def _load_css(self) -> None:
        css = Gtk.CssProvider()
        css.load_from_data(
            b"""
            .pomodoro-window.mode-pomodoro {
              background-color: #ba4949;
            }
            .pomodoro-window.mode-short-break {
              background-color: #397097;
            }
            .pomodoro-window.mode-long-break {
              background-color: #478859;
            }
            .pomodoro-window .timer-label {
              font-size: 72px;
              font-weight: 700;
              color: white;
            }
            .pomodoro-window .mode-label {
              color: rgba(255, 255, 255, 0.9);
              font-weight: 600;
            }
            .pomodoro-window .tasks-card {
              background-color: rgba(255, 255, 255, 0.12);
              border-radius: 12px;
              color: white;
              padding: 16px;
            }
            .pomodoro-window .tasks-card label {
              color: white;
            }
            .pomodoro-window .task-active {
              background-color: rgba(255, 255, 255, 0.15);
              border-left: 3px solid white;
            }
            .pomodoro-window headerbar {
              background-color: transparent;
              color: white;
            }
            .pomodoro-window headerbar button,
            .pomodoro-window headerbar label {
              color: white;
            }
            .pomodoro-window .start-btn {
              background-color: white;
              color: #333;
              font-weight: 600;
              padding: 10px 32px;
            }
            .pomodoro-window .ghost-btn {
              color: white;
              border: 2px solid rgba(255, 255, 255, 0.45);
            }
            .pomodoro-window .task-entry {
              background-color: rgba(0, 0, 0, 0.15);
              color: white;
            }
            .pomodoro-window .task-entry:focus-within {
              border-color: rgba(255, 255, 255, 0.5);
            }
            """
        )
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _build_ui(self) -> None:
        header = Adw.HeaderBar()
        header.add_css_class("flat")

        settings_btn = Gtk.Button(icon_name="emblem-system-symbolic")
        settings_btn.set_tooltip_text("Настройки")
        settings_btn.connect("clicked", self._on_settings)
        header.pack_end(settings_btn)

        self._mode_group = []
        modes_box = Gtk.Box(spacing=0)
        modes_box.add_css_class("linked")
        first_btn = None
        for mode in MODE_KEYS:
            btn = Gtk.ToggleButton(label=MODE_LABELS[mode])
            btn.set_css_classes(["flat"])
            btn.connect("toggled", self._on_mode_toggled, mode)
            if first_btn is None:
                first_btn = btn
                btn.set_active(True)
            else:
                btn.set_group(first_btn)
            modes_box.append(btn)
            self._mode_group.append(btn)
        header.set_title_widget(modes_box)

        self._timer_label = Gtk.Label(label="25:00", css_classes=["timer-label"])
        self._active_task_label = Gtk.Label(label="", xalign=0, css_classes=["dim-label"])

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12, halign=Gtk.Align.CENTER)
        self._start_btn = Gtk.Button(label="Старт", css_classes=["start-btn"])
        self._start_btn.connect("clicked", self._on_start)
        self._pause_btn = Gtk.Button(label="Пауза", css_classes=["start-btn"])
        self._pause_btn.connect("clicked", self._on_pause)
        self._pause_btn.set_visible(False)
        self._skip_btn = Gtk.Button(label="Пропустить", css_classes=["ghost-btn"])
        self._skip_btn.connect("clicked", self._on_skip)
        controls.append(self._start_btn)
        controls.append(self._pause_btn)
        controls.append(self._skip_btn)

        timer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        timer_box.set_margin_top(48)
        timer_box.append(self._timer_label)
        timer_box.append(controls)

        tasks_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        tasks_card.add_css_class("tasks-card")
        tasks_card.set_margin_top(24)
        tasks_card.set_margin_bottom(24)
        tasks_card.set_margin_start(24)
        tasks_card.set_margin_end(24)

        title = Gtk.Label(label="Задачи", xalign=0, css_classes=["title-3"])
        title.set_margin_bottom(4)
        tasks_card.append(title)
        tasks_card.append(self._active_task_label)

        self._task_list = Gtk.ListBox()
        self._task_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self._task_list.add_css_class("boxed-list")
        self._task_list.connect("row-activated", self._on_task_activated)
        tasks_card.append(self._task_list)

        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self._task_entry = Gtk.Entry(placeholder_text="Что делаем?")
        self._task_entry.add_css_class("task-entry")
        self._task_entry.connect("activate", self._on_add_task)
        form.append(self._task_entry)

        form_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        estimate_box = Gtk.Box(spacing=8)
        estimate_box.append(Gtk.Label(label="Оценка:"))
        self._estimate_spin = Gtk.SpinButton.new_with_range(1, 99, 1)
        self._estimate_spin.set_value(1)
        estimate_box.append(self._estimate_spin)
        form_row.append(estimate_box)
        form_row.append(Gtk.Box(hexpand=True))

        add_btn = Gtk.Button(label="Добавить", css_classes=["start-btn"])
        add_btn.connect("clicked", self._on_add_task)
        form_row.append(add_btn)
        form.append(form_row)
        tasks_card.append(form)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.append(timer_box)
        content.append(tasks_card)

        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_child(content)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.append(header)
        root.append(scroll)
        self.set_content(root)

    def _set_mode_class(self, mode: str) -> None:
        for css in MODE_CSS.values():
            self.remove_css_class(css)
        self.add_css_class(MODE_CSS.get(mode, "mode-pomodoro"))

    def _refresh(self) -> None:
        self._updating = True
        timer = self.store.timer
        minutes, seconds = divmod(int(timer["seconds_left"]), 60)
        self._timer_label.set_label(f"{minutes:02d}:{seconds:02d}")
        self.set_title(self.store.window_title())

        running = timer["status"] == "running"
        self._start_btn.set_visible(not running)
        self._pause_btn.set_visible(running)

        mode = timer["mode"]
        self._set_mode_class(mode)
        for btn, key in zip(self._mode_group, MODE_KEYS, strict=True):
            btn.set_active(key == mode)

        active = self.store.active_task()
        self._active_task_label.set_label(
            f"Сейчас: {active['title']}" if active else "Выберите задачу для фокуса"
        )

        while child := self._task_list.get_first_child():
            self._task_list.remove(child)

        if not self.store.tasks:
            row = Adw.ActionRow(title="Добавьте задачу, чтобы начать")
            row.set_sensitive(False)
            self._task_list.append(row)
        else:
            for task in self.store.tasks:
                row = TaskRow(task, task["id"] == timer["active_task_id"])
                row.check.connect("toggled", self._on_task_check, task["id"])
                row._delete_btn.connect("clicked", self._on_task_delete, task["id"])
                self._task_list.append(row)

        self._updating = False

    def _on_start(self, *_args) -> None:
        self._timer.start()

    def _on_pause(self, *_args) -> None:
        self._timer.pause()

    def _on_skip(self, *_args) -> None:
        self._timer.skip()

    def _show_eye_reminder(self) -> bool:
        if self._eye_reminder_dialog:
            return True

        dialog = Adw.MessageDialog.new(
            None,
            "Пора поморгать глазами",
            "Сделайте несколько мягких морганий, чтобы дать глазам отдохнуть.",
        )
        dialog.add_response("close", "Хорошо")
        dialog.set_default_response("close")
        dialog.set_close_response("close")
        dialog.connect("response", self._on_eye_reminder_response)
        self._eye_reminder_dialog = dialog
        dialog.present()
        return True

    def _on_eye_reminder_response(
        self, dialog: Adw.MessageDialog, _response: str
    ) -> None:
        dialog.close()
        self._eye_reminder_dialog = None

    def _on_mode_toggled(self, button: Gtk.ToggleButton, mode: str) -> None:
        if self._updating:
            return
        if button.get_active() and self.store.timer["mode"] != mode:
            self._timer.switch_mode(mode)

    def _on_settings(self, *_args) -> None:
        dialog = SettingsDialog(self, self.store)
        dialog.present()

    def _on_add_task(self, *_args) -> None:
        title = self._task_entry.get_text().strip()
        if not title:
            return
        estimate = int(self._estimate_spin.get_value())
        self.store.add_task(title, estimate)
        self._task_entry.set_text("")
        self._estimate_spin.set_value(1)

    def _on_task_activated(self, _listbox: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        if isinstance(row, TaskRow):
            self.store.set_active_task(row.task_id)

    def _on_task_check(self, check: Gtk.CheckButton, task_id: str) -> None:
        if self._updating:
            return
        self.store.toggle_task_done(task_id)

    def _on_task_delete(self, _btn: Gtk.Button, task_id: str) -> None:
        self.store.remove_task(task_id)
