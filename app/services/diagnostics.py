from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from app.build_info import BuildInfo, load_build_info
from app.db.schema import SCHEMA_VERSION
from app.runtime_paths import RuntimePaths, get_bundled_resource_path, get_runtime_paths
from app.services.audit_log import (
    AuditLogService,
    DIAGNOSTIC_BUNDLE_EXPORTED,
    SELF_CHECK_RUN,
)
from app.settings import get_norms_xlsx_path, set_last_self_check


@dataclass(frozen=True)
class SelfCheckIssue:
    code: str
    severity: str
    message: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SelfCheckReport:
    created_at: str
    ok: bool
    issues: list[SelfCheckIssue]
    build_info: BuildInfo
    runtime_paths: RuntimePaths

    def to_dict(self) -> dict[str, object]:
        return {
            "created_at": self.created_at,
            "ok": self.ok,
            "issues": [issue.to_dict() for issue in self.issues],
            "build_info": self.build_info.to_dict(),
            "runtime_paths": self.runtime_paths.to_dict(),
        }


@dataclass(frozen=True)
class DiagnosticBundleResult:
    bundle_path: str
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_self_check(*, connection=None) -> SelfCheckReport:
    runtime_paths = get_runtime_paths()
    build_info = load_build_info()
    issues: list[SelfCheckIssue] = []

    for label, path in runtime_paths.to_dict().items():
        if label.endswith("_dir") or label == "profile_root":
            if not Path(path).exists():
                issues.append(
                    SelfCheckIssue(
                        code=f"paths.{label}",
                        severity="error",
                        message=f"Не найден обязательный путь: {path}",
                    )
                )

    if build_info.schema_version != str(SCHEMA_VERSION):
        issues.append(
            SelfCheckIssue(
                code="build.schema_version",
                severity="warning",
                message="Версия схемы в метаданных сборки не совпадает с текущей схемой приложения.",
            )
        )
    if not build_info.generated:
        issues.append(
            SelfCheckIssue(
                code="build_info.fallback",
                severity="warning",
                message="Метаданные сборки не найдены; используется режим разработки.",
            )
        )

    norms_path = Path(get_norms_xlsx_path())
    bundled_template = get_bundled_resource_path("resources/norms.xlsx.b64")
    if not norms_path.exists() and not bundled_template.exists():
        issues.append(
            SelfCheckIssue(
                code="norms.unavailable",
                severity="warning",
                message="Файл norms.xlsx отсутствует, а встроенный шаблон недоступен.",
            )
        )

    try:
        active_connection = connection
        if active_connection is None:
            from app.db.database import get_connection

            active_connection = get_connection(runtime_paths.db_path)
        integrity_row = active_connection.execute("PRAGMA integrity_check").fetchone()
        integrity_status = str(integrity_row[0]) if integrity_row else "unknown"
        if integrity_status.lower() != "ok":
            issues.append(
                SelfCheckIssue(
                    code="db.integrity",
                    severity="error",
                    message=f"Проверка целостности SQLite вернула: {integrity_status}",
                )
            )
    except sqlite3.DatabaseError as exc:
        issues.append(
            SelfCheckIssue(
                code="db.open",
                severity="error",
                message=f"Не удалось открыть базу данных: {exc}",
            )
        )

    report = SelfCheckReport(
        created_at=_current_timestamp(),
        ok=not any(issue.severity == "error" for issue in issues),
        issues=issues,
        build_info=build_info,
        runtime_paths=runtime_paths,
    )
    if connection is not None:
        AuditLogService(connection).log_event(
            SELF_CHECK_RUN,
            "Выполнена самопроверка",
            f"Проблем: {len(report.issues)}",
            level="error" if not report.ok else "warning" if report.issues else "info",
            context=report.to_dict(),
            source="diagnostics",
        )
    set_last_self_check(report.to_dict())
    return report


def export_diagnostic_bundle(*, connection=None, self_check: SelfCheckReport | None = None) -> DiagnosticBundleResult:
    runtime_paths = get_runtime_paths()
    report = self_check or run_self_check(connection=connection)
    bundle_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bundle_path = runtime_paths.diagnostics_dir / f"diagnostic-bundle-{bundle_timestamp}.zip"

    with ZipFile(bundle_path, mode="w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "build_info.json",
            json.dumps(report.build_info.to_dict(), ensure_ascii=False, indent=2),
        )
        archive.writestr(
            "self_check.json",
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        )
        archive.writestr(
            "runtime_paths.json",
            json.dumps(runtime_paths.to_dict(), ensure_ascii=False, indent=2),
        )
        for log_file in sorted(runtime_paths.logs_dir.glob("*.log")):
            archive.write(log_file, arcname=f"logs/{log_file.name}")

    result = DiagnosticBundleResult(
        bundle_path=str(bundle_path),
        created_at=_current_timestamp(),
    )
    if connection is not None:
        AuditLogService(connection).log_event(
            DIAGNOSTIC_BUNDLE_EXPORTED,
            "Экспортирован диагностический архив",
            bundle_path.name,
            context=result.to_dict(),
            source="diagnostics",
        )
    return result


def format_self_check_summary(report: SelfCheckReport) -> str:
    if not report.issues:
        return "Самопроверка: все в порядке"
    return f"Самопроверка: проблем - {len(report.issues)}"


def _current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
