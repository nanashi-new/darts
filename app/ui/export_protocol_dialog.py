from __future__ import annotations

import os

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.services.export_protocol_docx import export_protocol_docx
from app.services.export_protocol_xlsx import ProtocolData, export_protocol_xlsx
from app.settings import get_organization_profile


class ExportProtocolDialog(QDialog):
    def __init__(
        self,
        tournament: dict[str, object],
        results: list[dict[str, object]],
        parent=None,  # noqa: ANN001
    ) -> None:
        super().__init__(parent)
        self._tournament = tournament
        self._results = results
        self.setWindowTitle("\u042d\u043a\u0441\u043f\u043e\u0440\u0442 \u043f\u0440\u043e\u0442\u043e\u043a\u043e\u043b\u0430")
        self.resize(700, 600)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Competition title
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0441\u043e\u0440\u0435\u0432\u043d\u043e\u0432\u0430\u043d\u0438\u044f:"))
        self._competition_title_edit = QLineEdit(self)
        self._competition_title_edit.setText(str(self._tournament.get("name", "")))
        row2.addWidget(self._competition_title_edit)
        layout.addLayout(row2)

        # Category
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f:"))
        self._category_edit = QLineEdit(self)
        self._category_edit.setText(str(self._tournament.get("category_code", "")))
        row3.addWidget(self._category_edit)
        layout.addLayout(row3)

        # Format type
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("\u0424\u043e\u0440\u043c\u0430\u0442:"))
        self._format_type_combo = QComboBox(self)
        self._format_type_combo.addItems([
            "\u041a\u043b\u0430\u0441\u0441\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f",
            "501 - \u043e\u0434\u0438\u043d\u043e\u0447\u043d\u044b\u0439 \u0440\u0430\u0437\u0440\u044f\u0434",
            "\u0421\u0434\u0430\u0447\u0430 \u043d\u043e\u0440\u043c\u0430\u0442\u0438\u0432\u043e\u0432",
        ])
        row4.addWidget(self._format_type_combo)
        layout.addLayout(row4)

        # Export format
        row5 = QHBoxLayout()
        row5.addWidget(QLabel("\u0424\u043e\u0440\u043c\u0430\u0442 \u0444\u0430\u0439\u043b\u0430:"))
        self._export_format_combo = QComboBox(self)
        self._export_format_combo.addItems(["XLSX", "DOCX"])
        row5.addWidget(self._export_format_combo)
        layout.addLayout(row5)

        # Include logo
        self._include_logo_check = QCheckBox("\u0412\u043a\u043b\u044e\u0447\u0438\u0442\u044c \u043b\u043e\u0433\u043e\u0442\u0438\u043f", self)
        layout.addWidget(self._include_logo_check)

        # Jury table
        layout.addWidget(QLabel("\u0421\u0443\u0434\u0435\u0439\u0441\u043a\u0430\u044f \u043a\u043e\u043b\u043b\u0435\u0433\u0438\u044f:"))
        self._jury_table = QTableWidget(self)
        self._jury_table.setColumnCount(4)
        self._jury_table.setHorizontalHeaderLabels([
            "\u0414\u043e\u043b\u0436\u043d\u043e\u0441\u0442\u044c",
            "\u0424\u0418\u041e",
            "\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f",
            "\u0413\u043e\u0440\u043e\u0434",
        ])
        self._jury_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._jury_table)

        # Jury buttons
        jury_btn_row = QHBoxLayout()
        add_jury_btn = QPushButton("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c", self)
        add_jury_btn.clicked.connect(self._add_jury_row)
        remove_jury_btn = QPushButton("\u0423\u0434\u0430\u043b\u0438\u0442\u044c", self)
        remove_jury_btn.clicked.connect(self._remove_jury_row)
        jury_btn_row.addWidget(add_jury_btn)
        jury_btn_row.addWidget(remove_jury_btn)
        jury_btn_row.addStretch(1)
        layout.addLayout(jury_btn_row)

        # Export button
        self._export_btn = QPushButton("\u042d\u043a\u0441\u043f\u043e\u0440\u0442", self)
        self._export_btn.clicked.connect(self._do_export)
        layout.addWidget(self._export_btn)

        # Load organization profile
        self._load_profile()

    def _load_profile(self) -> None:
        profile = get_organization_profile()
        jury_members = profile.get("jury_members")
        if isinstance(jury_members, list):
            self._jury_table.setRowCount(len(jury_members))
            for row_idx, member in enumerate(jury_members):
                if isinstance(member, dict):
                    self._jury_table.setItem(row_idx, 0, QTableWidgetItem(str(member.get("position", ""))))
                    self._jury_table.setItem(row_idx, 1, QTableWidgetItem(str(member.get("name", ""))))
                    self._jury_table.setItem(row_idx, 2, QTableWidgetItem(str(member.get("category", ""))))
                    self._jury_table.setItem(row_idx, 3, QTableWidgetItem(str(member.get("city", ""))))

    def _add_jury_row(self) -> None:
        row = self._jury_table.rowCount()
        self._jury_table.insertRow(row)
        for col in range(4):
            self._jury_table.setItem(row, col, QTableWidgetItem(""))

    def _remove_jury_row(self) -> None:
        row = self._jury_table.currentRow()
        if row >= 0:
            self._jury_table.removeRow(row)

    def _collect_jury(self) -> list[dict[str, str]]:
        jury: list[dict[str, str]] = []
        for row_idx in range(self._jury_table.rowCount()):
            position = (self._jury_table.item(row_idx, 0) or QTableWidgetItem("")).text()
            name = (self._jury_table.item(row_idx, 1) or QTableWidgetItem("")).text()
            category = (self._jury_table.item(row_idx, 2) or QTableWidgetItem("")).text()
            city = (self._jury_table.item(row_idx, 3) or QTableWidgetItem("")).text()
            if position or name:
                jury.append({"position": position, "name": name, "category": category, "city": city})
        return jury

    def _do_export(self) -> None:
        # Determine format type
        format_type_map = {
            0: "classification",
            1: "501",
            2: "norms",
        }
        format_type = format_type_map.get(self._format_type_combo.currentIndex(), "classification")

        export_format = self._export_format_combo.currentText().lower()
        ext = ".xlsx" if export_format == "xlsx" else ".docx"
        filter_str = "Excel (*.xlsx)" if export_format == "xlsx" else "Word (*.docx)"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c \u043f\u0440\u043e\u0442\u043e\u043a\u043e\u043b",
            f"protocol{ext}",
            filter_str,
        )
        if not path:
            return

        profile = get_organization_profile()
        logo_path: str | None = None
        if self._include_logo_check.isChecked():
            lp = profile.get("logo_path")
            if lp:
                logo_path = str(lp)
                # Warn user if logo file does not exist before export
                if not os.path.isfile(logo_path):
                    QMessageBox.warning(
                        self,
                        "\u041b\u043e\u0433\u043e\u0442\u0438\u043f",
                        "\u0424\u0430\u0439\u043b \u043b\u043e\u0433\u043e\u0442\u0438\u043f\u0430 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d, "
                        "\u044d\u043a\u0441\u043f\u043e\u0440\u0442 \u0431\u0443\u0434\u0435\u0442 \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d \u0431\u0435\u0437 \u043b\u043e\u0433\u043e\u0442\u0438\u043f\u0430.",
                    )

        # Map results
        mapped_results: list[dict[str, object]] = []
        for r in self._results:
            last_name = str(r.get("last_name", ""))
            first_name = str(r.get("first_name", ""))
            middle_name = str(r.get("middle_name", ""))
            fio = " ".join(part for part in [last_name, first_name, middle_name] if part)

            birth_date = str(r.get("birth_date", ""))
            birth_year = birth_date[:4] if len(birth_date) >= 4 else birth_date

            # Region is set from organization profile city. This is by design:
            # the player data model has no per-player region field, and in the
            # Tver federation context all participants are from the same region.
            mapped_results.append({
                "place": r.get("place", ""),
                "fio": fio,
                "birth_year": birth_year,
                "coach": str(r.get("coach", "")),
                "score_set": r.get("score_set", ""),
                "score_sector20": r.get("score_sector20", ""),
                "score_big_round": r.get("score_big_round", ""),
                "points_total": r.get("points_total", ""),
                "rank_achieved": str(r.get("rank_achieved", "")),
                "current_rank": str(r.get("current_rank", "")),
                "region": str(profile.get("city", "")),
            })

        data = ProtocolData(
            tournament_name=str(self._tournament.get("name", "")),
            competition_title=self._competition_title_edit.text(),
            category=self._category_edit.text(),
            format_type=format_type,
            date=str(self._tournament.get("date", "")),
            venue=str(profile.get("default_venue", "")),
            city=str(profile.get("city", "")),
            org_name=str(profile.get("org_name", "")),
            logo_path=logo_path,
            jury=self._collect_jury(),
            results=mapped_results,
        )

        try:
            if export_format == "xlsx":
                export_protocol_xlsx(path, data)
            else:
                export_protocol_docx(path, data)
            QMessageBox.information(self, "\u042d\u043a\u0441\u043f\u043e\u0440\u0442", f"\u0413\u043e\u0442\u043e\u0432\u043e: {path}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "\u041e\u0448\u0438\u0431\u043a\u0430 \u044d\u043a\u0441\u043f\u043e\u0440\u0442\u0430", str(exc))
