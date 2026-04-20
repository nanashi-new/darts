from __future__ import annotations

from dataclasses import dataclass

from app.db.repositories import NoteRepository
from app.services.audit_log import AuditLogService, NOTE_CREATED


@dataclass(frozen=True)
class NoteRecord:
    id: int
    entity_type: str
    entity_id: str
    note_type: str
    visibility: str
    author: str | None
    title: str
    body: str
    priority: str
    is_pinned: bool
    is_archived: bool
    created_at: str
    updated_at: str
    entity_label: str | None = None


@dataclass(frozen=True)
class EntityNoteDefaults:
    note_type: str
    visibility: str
    priority: str = "normal"
    author: str | None = None
    is_pinned: bool = False


def create_note(
    *,
    connection,
    entity_type: str,
    entity_id: str,
    note_type: str,
    visibility: str,
    title: str,
    body: str,
    priority: str = "normal",
    author: str | None = None,
    is_pinned: bool = False,
    is_archived: bool = False,
) -> int:
    normalized_title = title.strip()
    normalized_body = body.strip()
    if not normalized_title:
        raise ValueError("Note title is required.")
    if not normalized_body:
        raise ValueError("Note body is required.")

    repo = NoteRepository(connection)
    note_id = repo.create(
        {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "note_type": note_type,
            "visibility": visibility,
            "author": (author or "").strip() or None,
            "title": normalized_title,
            "body": normalized_body,
            "priority": priority,
            "is_pinned": is_pinned,
            "is_archived": is_archived,
        }
    )
    AuditLogService(connection).log_event(
        NOTE_CREATED,
        "Note created",
        f"Note ID: {note_id}; entity={entity_type}:{entity_id}; title={normalized_title}",
        context={
            "note_id": note_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "note_type": note_type,
            "visibility": visibility,
            "priority": priority,
            "is_pinned": bool(is_pinned),
        },
        entity_type=entity_type,
        entity_id=entity_id,
        source="notes",
    )
    return note_id


def list_entity_notes(
    *,
    connection,
    entity_type: str,
    entity_id: str,
    include_archived: bool = False,
    note_types: list[str] | None = None,
    visibilities: list[str] | None = None,
    query: str | None = None,
) -> list[NoteRecord]:
    repo = NoteRepository(connection)
    return [
        NoteRecord(
            id=int(row["id"]),
            entity_type=str(row["entity_type"]),
            entity_id=str(row["entity_id"]),
            note_type=str(row["note_type"]),
            visibility=str(row["visibility"]),
            author=str(row["author"]) if row["author"] is not None else None,
            title=str(row["title"]),
            body=str(row["body"]),
            priority=str(row["priority"]),
            is_pinned=bool(int(row["is_pinned"] or 0)),
            is_archived=bool(int(row["is_archived"] or 0)),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )
        for row in repo.list_for_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            include_archived=include_archived,
            note_types=note_types,
            visibilities=visibilities,
            query=query,
        )
    ]


def list_notes_hub(
    *,
    connection,
    include_archived: bool = False,
    entity_types: list[str] | None = None,
    note_types: list[str] | None = None,
    visibilities: list[str] | None = None,
    query: str | None = None,
) -> list[NoteRecord]:
    repo = NoteRepository(connection)
    records: list[NoteRecord] = []
    for row in repo.list_all(
        include_archived=include_archived,
        entity_types=entity_types,
        note_types=note_types,
        visibilities=visibilities,
        query=query,
    ):
        entity_label = _build_entity_label(row)
        records.append(
            NoteRecord(
                id=int(row["id"]),
                entity_type=str(row["entity_type"]),
                entity_id=str(row["entity_id"]),
                note_type=str(row["note_type"]),
                visibility=str(row["visibility"]),
                author=str(row["author"]) if row["author"] is not None else None,
                title=str(row["title"]),
                body=str(row["body"]),
                priority=str(row["priority"]),
                is_pinned=bool(int(row["is_pinned"] or 0)),
                is_archived=bool(int(row["is_archived"] or 0)),
                created_at=str(row["created_at"]),
                updated_at=str(row["updated_at"]),
                entity_label=entity_label,
            )
        )
    return records


def _build_entity_label(row: dict[str, object]) -> str | None:
    entity_type = str(row.get("entity_type") or "")
    if entity_type == "player":
        parts = [
            str(row.get("last_name") or "").strip(),
            str(row.get("first_name") or "").strip(),
            str(row.get("middle_name") or "").strip(),
        ]
        label = " ".join(part for part in parts if part)
        return label or None
    if entity_type == "tournament":
        name = str(row.get("tournament_name") or "").strip()
        return name or None
    if entity_type == "league":
        league_code = str(row.get("entity_id") or "").strip()
        return league_code or None
    return None
