"""Qt-интерфейс GOSTDoc Studio (PySide6, опционально).

Запуск: gostdoc-gui  или  python -m gostdoc.gui
"""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path


def run_gui() -> int:
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QCheckBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
            QMainWindow, QMessageBox, QPlainTextEdit, QPushButton,
            QVBoxLayout, QWidget,
        )
    except ImportError:
        print("PySide6 не установлен. Установка: pip install 'gostdoc[gui]'")
        return 1

    from .cli import build_docs

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("GOSTDoc Studio — документация по ГОСТ для C++/Qt")
            self.resize(760, 520)
            central = QWidget()
            self.setCentralWidget(central)
            lay = QVBoxLayout(central)

            self.ed_project = QLineEdit("examples/sample")
            self.ed_out = QLineEdit("docs")
            self.ed_name = QLineEdit()
            self.ed_author = QLineEdit()
            self.ed_org = QLineEdit()

            def row(label, field, browse=None):
                r = QHBoxLayout()
                r.addWidget(QLabel(label))
                r.addWidget(field, 1)
                if browse:
                    btn = QPushButton("…")
                    btn.clicked.connect(browse)
                    r.addWidget(btn)
                lay.addLayout(r)

            def browse_project():
                p = QFileDialog.getExistingDirectory(self, "Каталог исходников")
                if p:
                    self.ed_project.setText(p)

            def browse_out():
                p = QFileDialog.getExistingDirectory(self, "Каталог результата")
                if p:
                    self.ed_out.setText(p)

            row("Проект", self.ed_project, browse_project)
            row("Вывод", self.ed_out, browse_out)
            row("Название", self.ed_name)
            row("Разработчик", self.ed_author)
            row("Организация", self.ed_org)

            self.cb_pdf = QCheckBox("PDF")
            self.cb_docx = QCheckBox("DOCX"); self.cb_docx.setChecked(True)
            self.cb_txt = QCheckBox("TXT")
            self.cb_json = QCheckBox("JSON")
            self.cb_nn = QCheckBox("23 нейросети")
            lay.addLayout(self._fmt_row())

            self.btn = QPushButton("Сгенерировать документацию")
            self.btn.clicked.connect(self.generate)
            lay.addWidget(self.btn)

            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            lay.addWidget(self.log, 1)

        def _fmt_row(self):
            r = QHBoxLayout()
            r.addWidget(QLabel("Форматы:"))
            for cb in (self.cb_pdf, self.cb_docx, self.cb_txt, self.cb_json, self.cb_nn):
                r.addWidget(cb)
            r.addStretch(1)
            return r

        def generate(self):
            fmt = [name for cb, name in
                   ((self.cb_pdf, "pdf"), (self.cb_docx, "docx"),
                    (self.cb_txt, "txt"), (self.cb_json, "json"))
                   if cb.isChecked()]
            if not fmt:
                QMessageBox.warning(self, "GOSTDoc", "Выберите хотя бы один формат")
                return
            buf = io.StringIO()
            try:
                with redirect_stdout(buf):
                    build_docs(self.ed_project.text().strip() or ".",
                               self.ed_out.text().strip() or "docs",
                               tuple(fmt),
                               name=self.ed_name.text().strip(),
                               author=self.ed_author.text().strip(),
                               organisation=self.ed_org.text().strip(),
                               nn=self.cb_nn.isChecked())
            except Exception as e:  # noqa: BLE001
                buf.write(f"\nОшибка: {e}")
            self.log.setPlainText(buf.getvalue())

    app = __import__("PySide6.QtWidgets", fromlist=["QApplication"]).QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run_gui())
