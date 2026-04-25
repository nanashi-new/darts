from __future__ import annotations

from app.ui.labels import (
    adult_scope_label,
    audit_event_label,
    category_label,
    import_apply_status_label,
    gender_label,
    note_type_label,
    priority_label,
    scope_type_label,
    session_type_label,
    tournament_status_label,
    visibility_label,
)


def test_ui_labels_translate_known_technical_codes() -> None:
    assert tournament_status_label("draft") == "Черновик"
    assert tournament_status_label("published") == "Опубликован"
    assert tournament_status_label("canceled") == "Отменен"
    assert category_label("U12-M") == "Юноши до 12 лет"
    assert scope_type_label("adult") == "Взрослые"
    assert adult_scope_label("women") == "Женщины"
    assert note_type_label("coach_note") == "Заметка тренера"
    assert visibility_label("coach_only") == "Только тренеру"
    assert priority_label("high") == "Высокий"
    assert session_type_label("general") == "Общая тренировка"
    assert gender_label("M") == "Мужской"
    assert import_apply_status_label("draft_applied") == "Оставлен черновиком"
    assert audit_event_label("IMPORT_FILE") == "Импорт файла"


def test_ui_labels_keep_unknown_codes_visible_for_diagnostics() -> None:
    assert tournament_status_label("custom_status") == "custom_status"
    assert note_type_label("custom_note") == "custom_note"
