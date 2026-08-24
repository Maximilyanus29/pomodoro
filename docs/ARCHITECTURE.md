# ARCHITECTURE

## Обзор
Нативное GTK4 + Libadwaita приложение на Python (PyGObject).

```
app/native/pomodoro/
  main.py      # Adw.Application
  window.py    # главное окно и настройки
  store.py     # состояние + ~/.local/share/pomodoro/state.json
  timer.py     # GLib.timeout таймер
  sound.py     # canberra-gtk-play + Gio.Notification
```

## Установка
`./scripts/build-deb.sh` → `sudo apt install ./build/pomodoro-timer_*_all.deb`

Файлы пакета:
- `/usr/bin/pomodoro-timer` — launcher
- `/usr/lib/pomodoro-timer/pomodoro/` — код приложения
- `/usr/share/applications/io.pomodoro.Timer.desktop`
- `/usr/share/icons/hicolor/scalable/apps/io.pomodoro.Timer.svg`
