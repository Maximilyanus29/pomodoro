# STATE MODEL

## TimerState (между сессиями сохраняются)
| Поле | Тип | Описание |
|------|-----|----------|
| mode | `pomodoro \| short_break \| long_break` | Текущий режим |
| pomodoros_completed | number | Счётчик завершённых помодоро |
| active_task_id | string \| null | ID активной задачи |

## TimerState (только в памяти, сбрасывается при запуске)
| Поле | Тип | Описание |
|------|-----|----------|
| status | `idle \| running \| paused` | Состояние таймера |
| seconds_left | number | Оставшиеся секунды |

## Task
| Поле | Тип | Описание |
|------|-----|----------|
| id | string | UUID |
| title | string | Название |
| estimate | number | Оценка в помодоро |
| completed | number | Завершено помодоро |
| done | boolean | Задача выполнена |

## Settings
| Поле | По умолчанию |
|------|--------------|
| pomodoro_minutes | 25 |
| short_break_minutes | 5 |
| long_break_minutes | 15 |
| long_break_interval | 4 |
| auto_start_breaks | false |
| auto_start_pomodoros | false |
| sound_enabled | true |
| tick_sound_enabled | false |

## Хранение
`~/.local/share/pomodoro/state.json`
