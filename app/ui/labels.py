"""Russian display labels for UI-facing technical values."""

from __future__ import annotations

from app.domain.tournament_lifecycle import TournamentStatus
from app.services.audit_log import (
    DIAGNOSTIC_BUNDLE_EXPORTED,
    ERROR,
    EXPORT_BATCH,
    EXPORT_FILE,
    IMPORT_FILE,
    IMPORT_FOLDER,
    IMPORT_REPORT,
    LEAGUE_TRANSFER_CREATED,
    MERGE_PLAYERS,
    NOTE_CREATED,
    PROFILE_RESET_REQUESTED,
    PROFILE_RESTORE_REQUESTED,
    PROFILE_RESTORED,
    RATING_SNAPSHOT_CREATED,
    RECALC_ALL,
    RECALC_TOURNAMENT,
    RESTORE_POINT_CREATED,
    SELF_CHECK_RUN,
    TOURNAMENT_CORRECTED,
    TOURNAMENT_CREATED,
    TOURNAMENT_DELETED,
    TOURNAMENT_PUBLISHED,
    TOURNAMENT_UPDATED,
    TRAINING_ENTRY_CREATED,
)


TOURNAMENT_STATUS_LABELS = {
    TournamentStatus.DRAFT.value: "Черновик",
    TournamentStatus.REVIEW.value: "На проверке",
    TournamentStatus.CONFIRMED.value: "Подтвержден",
    TournamentStatus.PUBLISHED.value: "Опубликован",
    TournamentStatus.ARCHIVED.value: "В архиве",
    TournamentStatus.CANCELED.value: "Отменен",
}

CATEGORY_LABELS = {
    "U12-M": "Юноши до 12 лет",
    "U12-W": "Девушки до 12 лет",
    "U15-M": "Юноши до 15 лет",
    "U15-W": "Девушки до 15 лет",
}

SCOPE_TYPE_LABELS = {
    "category": "Категория",
    "league": "Лига",
    "adult": "Взрослые",
}

ADULT_SCOPE_LABELS = {
    "overall": "Все взрослые",
    "men": "Мужчины",
    "women": "Женщины",
}

ENTITY_TYPE_LABELS = {
    "player": "Игрок",
    "tournament": "Турнир",
    "league": "Лига",
}

NOTE_TYPE_LABELS = {
    "player_note": "Заметка игрока",
    "coach_note": "Заметка тренера",
    "follow_up": "Контрольное действие",
    "tournament_note": "Заметка турнира",
    "league_note": "Заметка лиги",
}

VISIBILITY_LABELS = {
    "personal": "Личная",
    "internal_service": "Служебная",
    "coach_only": "Только тренеру",
    "follow_up": "Контроль",
}

PRIORITY_LABELS = {
    "low": "Низкий",
    "normal": "Обычный",
    "high": "Высокий",
}

SESSION_TYPE_LABELS = {
    "general": "Общая тренировка",
    "technique": "Техника",
    "match": "Игровая практика",
    "fitness": "Физическая подготовка",
}

GENDER_LABELS = {
    "M": "Мужской",
    "F": "Женский",
    "male": "Мужской",
    "female": "Женский",
}

IMPORT_APPLY_STATUS_LABELS = {
    "draft_applied": "Оставлен черновиком",
    "published": "Опубликован",
}

LEVEL_LABELS = {
    "debug": "Отладка",
    "info": "Информация",
    "warning": "Предупреждение",
    "error": "Ошибка",
    "critical": "Критично",
}

AUDIT_EVENT_LABELS = {
    IMPORT_FILE: "Импорт файла",
    IMPORT_FOLDER: "Импорт папки",
    IMPORT_REPORT: "Отчет импорта",
    RATING_SNAPSHOT_CREATED: "Снимок рейтинга",
    LEAGUE_TRANSFER_CREATED: "Переход между лигами",
    NOTE_CREATED: "Создание заметки",
    TRAINING_ENTRY_CREATED: "Запись тренировки",
    RESTORE_POINT_CREATED: "Точка восстановления",
    PROFILE_RESET_REQUESTED: "Запрошен сброс профиля",
    PROFILE_RESTORE_REQUESTED: "Запрошено восстановление профиля",
    PROFILE_RESTORED: "Профиль восстановлен",
    SELF_CHECK_RUN: "Самопроверка",
    DIAGNOSTIC_BUNDLE_EXPORTED: "Диагностический архив",
    RECALC_TOURNAMENT: "Пересчет турнира",
    RECALC_ALL: "Пересчет всех турниров",
    EXPORT_FILE: "Экспорт файла",
    EXPORT_BATCH: "Пакетный экспорт",
    ERROR: "Ошибка",
    MERGE_PLAYERS: "Слияние игроков",
    TOURNAMENT_CREATED: "Турнир создан",
    TOURNAMENT_UPDATED: "Турнир обновлен",
    TOURNAMENT_PUBLISHED: "Турнир опубликован",
    TOURNAMENT_CORRECTED: "Коррекция турнира",
    TOURNAMENT_DELETED: "Турнир удален",
}


def display_label(value: object, mapping: dict[str, str], *, empty: str = "-") -> str:
    if value is None:
        return empty
    key = str(value)
    if not key:
        return empty
    return mapping.get(key, key)


def tournament_status_label(value: object) -> str:
    return display_label(value, TOURNAMENT_STATUS_LABELS)


def category_label(value: object) -> str:
    return display_label(value, CATEGORY_LABELS)


def scope_type_label(value: object) -> str:
    return display_label(value, SCOPE_TYPE_LABELS)


def adult_scope_label(value: object) -> str:
    return display_label(value, ADULT_SCOPE_LABELS)


def entity_type_label(value: object) -> str:
    return display_label(value, ENTITY_TYPE_LABELS)


def note_type_label(value: object) -> str:
    return display_label(value, NOTE_TYPE_LABELS)


def visibility_label(value: object) -> str:
    return display_label(value, VISIBILITY_LABELS)


def priority_label(value: object) -> str:
    return display_label(value, PRIORITY_LABELS)


def session_type_label(value: object) -> str:
    return display_label(value, SESSION_TYPE_LABELS)


def gender_label(value: object) -> str:
    return display_label(value, GENDER_LABELS)


def import_apply_status_label(value: object) -> str:
    return display_label(value, IMPORT_APPLY_STATUS_LABELS)


def audit_event_label(value: object) -> str:
    return display_label(value, AUDIT_EVENT_LABELS)


def level_label(value: object) -> str:
    return display_label(value, LEVEL_LABELS)
