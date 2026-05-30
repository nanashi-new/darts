from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.services.profile_manager import ProfileManager


class ProfileSelectorDialog(QDialog):
    """Dialog for managing and selecting profiles."""

    def __init__(
        self, profile_manager: ProfileManager, parent: object = None
    ) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self.setWindowTitle("Управление профилями")
        self.setMinimumWidth(500)
        self.setMinimumHeight(350)
        self._profile_manager = profile_manager
        self._selected_path: Path | None = None
        self._build_ui()
        self._refresh_list()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._list_widget = QListWidget(self)
        layout.addWidget(self._list_widget)

        button_row = QHBoxLayout()

        self._open_btn = QPushButton("Открыть", self)
        self._open_btn.setToolTip("Открыть выбранный профиль")
        self._open_btn.clicked.connect(self._on_open)
        button_row.addWidget(self._open_btn)

        self._create_btn = QPushButton("Создать новый", self)
        self._create_btn.setToolTip("Создать новый профиль")
        self._create_btn.clicked.connect(self._on_create)
        button_row.addWidget(self._create_btn)

        self._delete_btn = QPushButton("Удалить", self)
        self._delete_btn.setToolTip("Удалить выбранный профиль")
        self._delete_btn.clicked.connect(self._on_delete)
        button_row.addWidget(self._delete_btn)

        self._close_btn = QPushButton("Закрыть", self)
        self._close_btn.clicked.connect(self.reject)
        button_row.addWidget(self._close_btn)

        layout.addLayout(button_row)

    def _refresh_list(self) -> None:
        self._list_widget.clear()
        profiles = self._profile_manager.list_profiles()
        for profile in profiles:
            modified_text = profile.last_modified[:10] if profile.last_modified else "-"
            text = f"{profile.name}  |  {profile.path}  |  {modified_text}"
            item = QListWidgetItem(text)
            item.setData(256, str(profile.path))  # Qt.ItemDataRole.UserRole = 256
            self._list_widget.addItem(item)

    def _on_open(self) -> None:
        item = self._list_widget.currentItem()
        if item is None:
            return
        path_str = item.data(256)
        if path_str:
            self._selected_path = Path(path_str)
            self._profile_manager.set_last_used_profile(self._selected_path)
            QMessageBox.information(
                self,
                "Профиль выбран",
                f"Профиль '{self._selected_path.name}' будет использован "
                "при следующем запуске.",
            )
            self.accept()

    def _on_create(self) -> None:
        name, ok = QInputDialog.getText(
            self, "Новый профиль", "Имя профиля:"
        )
        if ok and name.strip():
            self._profile_manager.create_profile(name.strip())
            self._refresh_list()

    def _on_delete(self) -> None:
        item = self._list_widget.currentItem()
        if item is None:
            return
        path_str = item.data(256)
        if not path_str:
            return
        profile_path = Path(path_str)
        reply = QMessageBox.question(
            self,
            "Удаление профиля",
            f"Удалить профиль '{profile_path.name}'?\n\nВсе данные будут потеряны!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            success = self._profile_manager.delete_profile(profile_path)
            if not success:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Невозможно удалить текущий активный профиль.",
                )
            else:
                self._refresh_list()

    def selected_profile_path(self) -> Path | None:
        """Return the selected profile path, or None if no selection was made."""
        return self._selected_path
