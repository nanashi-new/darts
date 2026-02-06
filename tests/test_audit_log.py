from pathlib import Path

from app.db.database import get_connection
from app.services.audit_log import AuditLogService, EXPORT_FILE, IMPORT_FILE


def test_log_event_writes_and_filters_records(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "app.db")
    service = AuditLogService(connection)

    service.log_event(IMPORT_FILE, "Импорт", "Файл A", context={"path": "A.xlsx"})
    service.log_event(EXPORT_FILE, "Экспорт", "Файл B", level="warning", context={"path": "B.xlsx"})

    all_events = service.list_events()
    assert len(all_events) == 2
    assert all_events[0].event_type == EXPORT_FILE

    import_events = service.list_events(event_type=IMPORT_FILE)
    assert len(import_events) == 1
    assert import_events[0].details == "Файл A"

    search_events = service.list_events(query="B")
    assert len(search_events) == 1
    assert search_events[0].level == "warning"


def test_export_log_creates_txt_file(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "app.db")
    service = AuditLogService(connection)

    service.log_event(IMPORT_FILE, "Импорт", "Импортировали test.xlsx")
    output_path = service.export_txt(tmp_path / "audit.txt")

    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "IMPORT_FILE" in content
    assert "Импортировали test.xlsx" in content
