# Pomodoro Timer

Pomodoro-таймер для Ubuntu — аналог [Pomofocus](https://pomofocus.io/). Нативное GTK4-приложение.

## Возможности

- Таймер Pomodoro / короткий / длинный перерыв
- Список задач с оценкой в помодоро
- Настройки интервалов и автостарта
- Звук и системные уведомления GNOME
- Сохранение в `~/.local/share/pomodoro/state.json`

## Зависимости (Ubuntu)

```bash
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 libcanberra-gtk3-module
```

## Запуск из исходников

```bash
./scripts/run.sh
```

## Сборка и установка .deb

```bash
./scripts/build-deb.sh
# или с версией:
./scripts/build-deb.sh 1.0.0
```

Установка:

```bash
sudo apt install ./build/pomodoro-timer_1.0.0_all.deb
```

После установки приложение доступно как `pomodoro-timer` в меню приложений.

## Структура

```
pomodoro/
├── app/native/pomodoro/   # GTK4-приложение
├── packaging/             # desktop-файл и иконка
├── scripts/
│   ├── run.sh
│   └── build-deb.sh
└── docs/
```

## Документация

- [PRODUCT_BRIEF](docs/PRODUCT_BRIEF.md)
- [ARCHITECTURE](docs/ARCHITECTURE.md)
- [STATE_MODEL](docs/STATE_MODEL.md)
# pomodoro
