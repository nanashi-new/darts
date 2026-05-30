from __future__ import annotations

from PySide6.QtWidgets import (
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.services.audit_log import AuditLogService, RECALC_ALL
from app.services.player_merge import PlayerMergeService
from app.services.recalculate_tournament import recalculate_all_tournaments
from app.ui.player_merge_dialog import PlayerMergeDialog
from app.ui.season_transfer_dialog import SeasonTransferDialog


class SettingsView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._connection = get_connection()
        self._audit_log_service = AuditLogService(self._connection)
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        root_layout.addWidget(scroll_area)

        content = QWidget(self)
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        scroll_area.setWidget(content)

        layout = QVBoxLayout(content)

        description = QLabel("Служебные действия для обслуживания базы и данных приложения.", self)
        description.setWordWrap(True)
        layout.addWidget(description)

        recalc_all_btn = QPushButton("Пересчитать рейтинг", self)
        recalc_all_btn.clicked.connect(self._recalculate_all)
        layout.addWidget(recalc_all_btn)

        merge_btn = QPushButton("Слияние дублей", self)
        merge_btn.clicked.connect(self._open_player_merge)
        layout.addWidget(merge_btn)

        season_transfer_btn = QPushButton("Сезонные переходы", self)
        season_transfer_btn.setToolTip("Рассчитать и применить сезонные переходы между лигами.")
        season_transfer_btn.clicked.connect(self._open_season_transfer)
        layout.addWidget(season_transfer_btn)

        layout.addStretch(1)

    def _recalculate_all(self) -> None:
        report = recalculate_all_tournaments(connection=self._connection)
        self._audit_log_service.log_event(
            RECALC_ALL,
            "Пересчет всех турниров (настройки)",
            (
                f"Турниров: {report.tournaments_processed}; "
                f"обновлено: {report.results_updated}; "
                f"warnings: {len(report.warnings)}; errors: {len(report.errors)}"
            ),
            level="error" if report.errors else "warning" if report.warnings else "info",
        )
        details = [
            f"Турниров: {report.tournaments_processed}",
            f"Обновлено результатов: {report.results_updated}",
            f"Предупреждений: {len(report.warnings)}",
            f"Ошибок: {len(report.errors)}",
        ]
        if report.warnings:
            details.append("\n".join(report.warnings[:3]))
        if report.errors:
            details.append("\n".join(report.errors[:3]))
        QMessageBox.information(self, "Пересчет рейтинга", "\n".join(details))

    def _open_player_merge(self) -> None:
        dialog = PlayerMergeDialog(PlayerMergeService(self._connection), self)
        dialog.exec()

    def _open_season_transfer(self) -> None:
        dialog = SeasonTransferDialog(self)
        dialog.exec()
