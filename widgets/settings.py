import glob
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QCheckBox, QSpinBox, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class SettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Налаштування гри")
        self.setFixedSize(450, 360)
        self.setModal(True)
        self.settings = current_settings.copy()

        self.setStyleSheet("""
            QDialog {
                background-color: #966FD6;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 13pt;
            }
            QCheckBox {
                color: #FFFFFF;
                font-size: 12pt;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border: 2px solid #FF758F;
                border-radius: 6px;
                background-color: #3E245D;
            }
            QCheckBox::indicator:checked {
                background-color: #10B981;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(18)

        title = QLabel("Параметри гри")
        title.setFont(QFont("Comfortaa", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        lbl_file = QLabel("Файл із питаннями:")
        layout.addWidget(lbl_file)

        self.file_combo = QComboBox()
        json_files = glob.glob("quizes/*.json")
        if not json_files:
            json_files = ["quizes/questions.json"]
        self.file_combo.addItems(json_files)
        if self.settings.get("questions_file") in json_files:
            self.file_combo.setCurrentText(self.settings.get("questions_file"))
        layout.addWidget(self.file_combo)

        self.penalty_check = QCheckBox("Штрафувати за невірну відповідь")
        self.penalty_check.setChecked(self.settings.get("penalty_enabled", True))
        layout.addWidget(self.penalty_check)

        timer_layout = QHBoxLayout()
        lbl_timer = QLabel("Таймер на питання (сек):")
        self.timer_spin = QSpinBox()
        self.timer_spin.setRange(5, 180)
        self.timer_spin.setValue(self.settings.get("timer_seconds", 30))
        self.timer_spin.setFixedWidth(90)
        timer_layout.addWidget(lbl_timer)
        timer_layout.addWidget(self.timer_spin)
        layout.addLayout(timer_layout)

        layout.addStretch()

        btn_save = QPushButton("Зберегти")
        btn_save.setFixedHeight(56)
        btn_save.clicked.connect(self.save_and_close)
        layout.addWidget(btn_save)

    def save_and_close(self):
        self.settings["questions_file"] = self.file_combo.currentText()
        self.settings["penalty_enabled"] = self.penalty_check.isChecked()
        self.settings["timer_seconds"] = self.timer_spin.value()
        self.accept()