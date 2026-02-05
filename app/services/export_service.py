from __future__ import annotations

import os
from datetime import date
from typing import Iterable

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QPainter, QRegion
from PySide6.QtGui import QPageSize
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import QTableView


class ExportService:
    def export_table_pdf(
        self,
        table: QTableView,
        path: str,
        header_lines: Iterable[str],
    ) -> None:
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        printer.setPageOrientation(QPrinter.Landscape)
        printer.setPageSize(QPageSize(QPageSize.A4))
        self._render_table_to_printer(table, printer, list(header_lines))
        if not os.path.exists(path):
            raise OSError("Не удалось сохранить PDF файл.")

    def print_table(
        self,
        table: QTableView,
        parent,
        header_lines: Iterable[str],
    ) -> bool:
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageOrientation(QPrinter.Landscape)
        printer.setPageSize(QPageSize(QPageSize.A4))
        dialog = QPrintDialog(printer, parent)
        if dialog.exec() != QPrintDialog.Accepted:
            return False
        self._render_table_to_printer(table, printer, list(header_lines))
        return True

    def export_table_xlsx(
        self,
        table: QTableView,
        path: str,
        header_lines: Iterable[str],
    ) -> None:
        model = table.model()
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Экспорт"

        header_lines_list = list(header_lines)
        current_row = 1
        for line in header_lines_list:
            sheet.cell(row=current_row, column=1, value=line)
            current_row += 1

        header_row = current_row
        for column in range(model.columnCount()):
            header_text = model.headerData(column, Qt.Horizontal)
            cell = sheet.cell(row=header_row, column=column + 1, value=header_text)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center")

        current_row += 1
        alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        for row in range(model.rowCount()):
            for column in range(model.columnCount()):
                value = model.index(row, column).data()
                cell = sheet.cell(row=current_row, column=column + 1, value=value)
                cell.alignment = alignment
            current_row += 1

        sheet.freeze_panes = sheet.cell(row=header_row + 1, column=1)

        for column_cells in sheet.columns:
            max_length = 0
            column = column_cells[0].column
            for cell in column_cells:
                if cell.value is None:
                    continue
                max_length = max(max_length, len(str(cell.value)))
            sheet.column_dimensions[get_column_letter(column)].width = max_length + 2

        workbook.save(path)

    def save_table_image(self, table: QTableView, path: str) -> None:
        pixmap = table.viewport().grab()
        if not pixmap.save(path, "PNG"):
            raise OSError("Не удалось сохранить изображение.")

    def _render_table_to_printer(
        self,
        table: QTableView,
        printer: QPrinter,
        header_lines: list[str],
    ) -> None:
        painter = QPainter(printer)
        original_size = table.size()
        try:
            table_size = self._calculate_table_size(table)
            table.resize(table_size)
            table.updateGeometry()

            page_rect = printer.pageRect(QPrinter.DevicePixel)
            header_height = self._draw_header(painter, page_rect, header_lines)

            available_height = page_rect.height() - header_height
            scale = min(page_rect.width() / table_size.width(), 1.0)
            source_page_height = available_height / scale

            y_offset = 0.0
            page_index = 0
            while y_offset < table_size.height():
                if page_index > 0:
                    printer.newPage()

                painter.save()
                painter.translate(page_rect.x(), page_rect.y() + header_height)
                painter.scale(scale, scale)

                source_rect = QRect(
                    0,
                    int(y_offset),
                    table_size.width(),
                    int(min(source_page_height, table_size.height() - y_offset)),
                )
                table.render(painter, QPoint(0, 0), QRegion(source_rect))
                painter.restore()

                y_offset += source_page_height
                page_index += 1
        finally:
            table.resize(original_size)
            painter.end()

    @staticmethod
    def _calculate_table_size(table: QTableView) -> QSize:
        horizontal_header = table.horizontalHeader()
        vertical_header = table.verticalHeader()
        frame = table.frameWidth() * 2
        width = vertical_header.width() + horizontal_header.length() + frame
        height = horizontal_header.height() + vertical_header.length() + frame
        return QSize(width, height)

    @staticmethod
    def _draw_header(
        painter: QPainter, page_rect: QRect, header_lines: list[str]
    ) -> int:
        if not header_lines:
            return 0
        font = painter.font()
        font.setPointSize(12)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        line_height = metrics.height()
        y_offset = page_rect.y() + line_height
        for line in header_lines:
            painter.drawText(page_rect.x(), y_offset, line)
            y_offset += line_height
        return y_offset - page_rect.y() + line_height // 2

    @staticmethod
    def format_date_label() -> str:
        return date.today().strftime("%d.%m.%Y")
