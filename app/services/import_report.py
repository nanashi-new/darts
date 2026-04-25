from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from typing import Any

from app.db.repositories import TournamentRepository
from app.services.audit_log import AuditLogService, IMPORT_REPORT
from app.services.import_xlsx import ImportApplyReport

IMPORT_APPLY_STATUSES = {"draft_applied", "published"}


@dataclass(frozen=True)
class ImportSessionReport:
    operation_group_id: str
    tournament_id: int
    tournament_name: str
    category_code: str | None
    tournament_status: str
    apply_status: str
    files_processed: int
    tables_processed: int
    rows_read: int
    rows_imported: int
    rows_skipped: int
    players_created: int
    players_reused: int
    players_matched_manually: int
    warnings: list[str]
    warnings_count: int
    errors_count: int
    source_files: list[str]


@dataclass(frozen=True)
class ImportSessionReportRecord:
    audit_event_id: int
    created_at: str
    report: ImportSessionReport


def build_import_session_report(
    *,
    connection: sqlite3.Connection,
    apply_report: ImportApplyReport,
    apply_status: str,
) -> ImportSessionReport:
    normalized_status = str(apply_status).strip().lower()
    if normalized_status not in IMPORT_APPLY_STATUSES:
        raise ValueError(f"Неподдерживаемый статус применения импорта: {apply_status}")

    tournament = TournamentRepository(connection).get(apply_report.tournament_id) or {}
    warnings = list(apply_report.warnings)

    category_code_raw = tournament.get("category_code")
    category_code = str(category_code_raw).strip() if category_code_raw is not None else None
    tournament_status = str(tournament.get("status") or apply_report.tournament_status)

    return ImportSessionReport(
        operation_group_id=apply_report.operation_group_id,
        tournament_id=apply_report.tournament_id,
        tournament_name=apply_report.tournament_name,
        category_code=category_code or None,
        tournament_status=tournament_status,
        apply_status=normalized_status,
        files_processed=apply_report.files_processed,
        tables_processed=apply_report.tables_processed,
        rows_read=apply_report.rows_read,
        rows_imported=apply_report.imported_rows,
        rows_skipped=apply_report.skipped_rows,
        players_created=apply_report.players_created,
        players_reused=apply_report.players_reused,
        players_matched_manually=apply_report.players_matched_manually,
        warnings=warnings,
        warnings_count=len(warnings),
        errors_count=0,
        source_files=list(apply_report.source_files),
    )


def persist_import_session_report(
    *,
    connection: sqlite3.Connection,
    report: ImportSessionReport,
) -> int:
    audit_log_service = AuditLogService(connection)
    payload = asdict(report)
    return audit_log_service.log_event(
        IMPORT_REPORT,
        "Сохранен отчет сессии импорта",
        (
            f"Турнир ID: {report.tournament_id}; "
            f"apply_status={report.apply_status}; "
            f"импортировано={report.rows_imported}; "
            f"пропущено={report.rows_skipped}"
        ),
        context=payload,
        entity_type="tournament",
        entity_id=str(report.tournament_id),
        operation_group_id=report.operation_group_id or None,
        source="import_report",
    )


def list_import_reports(connection: sqlite3.Connection) -> list[ImportSessionReportRecord]:
    audit_log_service = AuditLogService(connection)
    records: list[ImportSessionReportRecord] = []
    for event in audit_log_service.list_events(event_type=IMPORT_REPORT):
        try:
            report = _report_from_payload(event.context)
        except (KeyError, TypeError, ValueError):
            continue
        records.append(
            ImportSessionReportRecord(
                audit_event_id=event.id,
                created_at=event.created_at,
                report=report,
            )
        )
    return records


def render_import_report_text(report: ImportSessionReport) -> str:
    lines = [
        "Отчет сессии импорта",
        f"Турнир: {report.tournament_name}",
        f"ID турнира: {report.tournament_id}",
        f"Категория: {report.category_code or '-'}",
        f"Статус турнира: {_tournament_status_label(report.tournament_status)}",
        f"Статус применения: {_apply_status_label(report.apply_status)}",
        f"Группа операции: {report.operation_group_id or '-'}",
        f"Обработано файлов: {report.files_processed}",
        f"Обработано таблиц: {report.tables_processed}",
        f"Прочитано строк: {report.rows_read}",
        f"Импортировано строк: {report.rows_imported}",
        f"Пропущено строк: {report.rows_skipped}",
        f"Создано игроков: {report.players_created}",
        f"Переиспользовано игроков: {report.players_reused}",
        f"Сопоставлено вручную: {report.players_matched_manually}",
        f"Предупреждений: {report.warnings_count}",
        f"Ошибок: {report.errors_count}",
    ]
    if report.source_files:
        lines.append("Исходные файлы:")
        lines.extend(f"- {path}" for path in report.source_files)
    if report.warnings:
        lines.append("Предупреждения:")
        lines.extend(f"- {warning}" for warning in report.warnings)
    return "\n".join(lines)


def render_import_report_json(report: ImportSessionReport) -> str:
    return json.dumps(asdict(report), ensure_ascii=False, indent=2)


def _report_from_payload(payload: dict[str, Any]) -> ImportSessionReport:
    warnings = _coerce_str_list(payload.get("warnings"))
    source_files = _coerce_str_list(payload.get("source_files"))
    return ImportSessionReport(
        operation_group_id=str(payload.get("operation_group_id") or ""),
        tournament_id=_coerce_int(payload["tournament_id"]),
        tournament_name=str(payload["tournament_name"]),
        category_code=_coerce_optional_str(payload.get("category_code")),
        tournament_status=str(payload["tournament_status"]),
        apply_status=str(payload["apply_status"]),
        files_processed=_coerce_int(payload["files_processed"]),
        tables_processed=_coerce_int(payload["tables_processed"]),
        rows_read=_coerce_int(payload["rows_read"]),
        rows_imported=_coerce_int(payload["rows_imported"]),
        rows_skipped=_coerce_int(payload["rows_skipped"]),
        players_created=_coerce_int(payload["players_created"]),
        players_reused=_coerce_int(payload["players_reused"]),
        players_matched_manually=_coerce_int(payload["players_matched_manually"]),
        warnings=warnings,
        warnings_count=_coerce_int(payload.get("warnings_count", len(warnings))),
        errors_count=_coerce_int(payload.get("errors_count", 0)),
        source_files=source_files,
    )


def _coerce_int(value: object) -> int:
    if isinstance(value, int):
        return value
    return int(str(value))


def _coerce_optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _apply_status_label(value: str) -> str:
    return {
        "draft_applied": "Оставлен черновиком",
        "published": "Опубликован",
    }.get(value, value)


def _tournament_status_label(value: str) -> str:
    return {
        "draft": "Черновик",
        "review": "На проверке",
        "confirmed": "Подтвержден",
        "published": "Опубликован",
        "archived": "В архиве",
    }.get(value, value)
