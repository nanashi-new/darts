# Release v1.3 Preparation

Дата: 2025-01-16

## Выполнено

1. Чистка кода:
   - Удалены 6 неиспользуемых импортов (ruff F401)
   - Удалён мёртвый файл app/ui/player_note_dialog.py
   - mypy чист: 46 source files
   - pytest: 151 тест проходит

2. Документация обновлена:
   - Release Notes: добавлены разделы v1.2.0 и v1.3.0
   - FAQ: 9 новых вопросов по новым функциям
   - SECURITY.md: реальная политика безопасности вместо шаблона
   - Roadmap: v1.2 и v1.3 отмечены как выполненные, добавлен v1.4
   - Release Checklist: добавлены gates для v1.3
   - Current State: обновлён на release-ready

3. Верификация:
   - python -m compileall app -q: OK
   - python -m mypy app: Success (46 files)
   - python -m pytest -q -rs: 151 passed
   - ruff check app/ --select F401: 0 errors
