from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.services.player_merge import PlayerMergeService


class PlayerMergeDialog(QDialog):
    def __init__(self, merge_service: PlayerMergeService, parent=None) -> None:
        super().__init__(parent)
        self._merge_service = merge_service
        self._groups = self._merge_service.find_possible_duplicates()

        self.setWindowTitle("Слияние дублей игроков")
        self.resize(980, 520)

        layout = QHBoxLayout(self)

        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("Группы дублей", self))
        self.groups_list = QListWidget(self)
        self.groups_list.currentRowChanged.connect(self._on_group_selected)
        left_panel.addWidget(self.groups_list)

        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Игроки в выбранной группе", self))
        self.players_list = QListWidget(self)
        right_panel.addWidget(self.players_list)

        right_panel.addWidget(QLabel("Primary (оставить)", self))
        self.primary_combo = QComboBox(self)
        self.primary_combo.currentIndexChanged.connect(self._update_transfer_count)
        right_panel.addWidget(self.primary_combo)

        right_panel.addWidget(QLabel("Duplicate (удалить)", self))
        self.duplicate_combo = QComboBox(self)
        self.duplicate_combo.currentIndexChanged.connect(self._update_transfer_count)
        right_panel.addWidget(self.duplicate_combo)

        self.stats_label = QLabel("", self)
        right_panel.addWidget(self.stats_label)

        merge_btn = QPushButton("Слить", self)
        merge_btn.clicked.connect(self._merge_selected)
        right_panel.addWidget(merge_btn)

        close_btn = QPushButton("Закрыть", self)
        close_btn.clicked.connect(self.accept)
        right_panel.addWidget(close_btn)
        right_panel.addStretch(1)

        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 2)

        self._load_groups()

    def _load_groups(self) -> None:
        self.groups_list.clear()
        for group in self._groups:
            self.groups_list.addItem(f"{group.normalized_fio} ({len(group.players)})")
        if self._groups:
            self.groups_list.setCurrentRow(0)
        else:
            self.stats_label.setText("Дубли не найдены.")

    def _on_group_selected(self, index: int) -> None:
        self.players_list.clear()
        self.primary_combo.clear()
        self.duplicate_combo.clear()
        self.stats_label.clear()

        if index < 0 or index >= len(self._groups):
            return

        group = self._groups[index]
        for player in group.players:
            player_id = int(player["id"])
            fio = " ".join(
                part
                for part in (
                    player.get("last_name"),
                    player.get("first_name"),
                    player.get("middle_name"),
                )
                if part
            )
            birth = str(player.get("birth_date") or "—")
            coach = str(player.get("coach") or "—")
            club = str(player.get("club") or "—")
            self.players_list.addItem(f"#{player_id} | {fio} | ДР: {birth} | Клуб: {club} | Тренер: {coach}")
            label = f"#{player_id} — {fio}"
            self.primary_combo.addItem(label, player_id)
            self.duplicate_combo.addItem(label, player_id)

        if self.duplicate_combo.count() > 1:
            self.duplicate_combo.setCurrentIndex(1)
        self._update_transfer_count()

    def _update_transfer_count(self) -> None:
        primary_id = self.primary_combo.currentData()
        duplicate_id = self.duplicate_combo.currentData()
        if not primary_id or not duplicate_id:
            self.stats_label.setText("")
            return
        if int(primary_id) == int(duplicate_id):
            self.stats_label.setText("Выберите разных игроков для слияния.")
            return

        count = self._merge_service.count_results_for_player(int(duplicate_id))
        self.stats_label.setText(f"Будет перенесено результатов: {count}")

    def _merge_selected(self) -> None:
        primary_id = self.primary_combo.currentData()
        duplicate_id = self.duplicate_combo.currentData()
        if primary_id is None or duplicate_id is None:
            QMessageBox.warning(self, "Слияние", "Выберите игроков для слияния.")
            return
        if int(primary_id) == int(duplicate_id):
            QMessageBox.warning(self, "Слияние", "Нельзя объединить игрока с самим собой.")
            return

        results_to_move = self._merge_service.count_results_for_player(int(duplicate_id))
        confirm = QMessageBox.question(
            self,
            "Подтверждение",
            (
                f"Перенести {results_to_move} результатов от игрока #{int(duplicate_id)} "
                f"к игроку #{int(primary_id)} и удалить дубль?"
            ),
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            result = self._merge_service.merge_players(int(primary_id), int(duplicate_id), "prefer_primary")
        except ValueError as exc:
            QMessageBox.warning(self, "Слияние", str(exc))
            return

        QMessageBox.information(
            self,
            "Слияние",
            (
                f"Готово. Перенесено: {result.results_transferred}. "
                f"Удалено дублирующих результатов: {result.duplicate_results_removed}."
            ),
        )
        self._groups = self._merge_service.find_possible_duplicates()
        self._load_groups()
