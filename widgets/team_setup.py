from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox, QLineEdit, QScrollArea,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class TeamSetupWidget(QWidget):
    back_to_menu_signal = Signal()  # 👈 Новий сигнал повернення в меню

    def __init__(self, on_start_callback, parent=None):
        super().__init__(parent)
        self.on_start_callback = on_start_callback
        self.team_inputs = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 30, 50, 30)
        main_layout.setSpacing(15)

        title_label = QLabel("Налаштування команд")
        title_label.setFont(QFont("Comfortaa", 22))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.scroll_content = QWidget()
        self.teams_layout = QVBoxLayout(self.scroll_content)
        self.teams_layout.setAlignment(Qt.AlignTop)
        self.teams_layout.setSpacing(10)
        scroll_area.setWidget(self.scroll_content)

        main_layout.addWidget(scroll_area, stretch=1)

        self.add_team_btn = QPushButton("Додати команду")
        self.add_team_btn.setFont(QFont("Comfortaa", 12))
        self.add_team_btn.setFixedSize(350, 56)
        self.add_team_btn.clicked.connect(lambda: self.add_team_input(""))
        main_layout.addWidget(self.add_team_btn, alignment=Qt.AlignCenter)

        self.start_game_btn = QPushButton("Розпочати гру")
        self.start_game_btn.setFont(QFont("Comfortaa", 14))
        self.start_game_btn.setFixedSize(350, 56)
        self.start_game_btn.clicked.connect(self.confirm_and_start)
        main_layout.addWidget(self.start_game_btn, alignment=Qt.AlignCenter)

        # 👈 Кнопка повернення до головного меню
        self.back_btn = QPushButton("Повернутися в меню")
        self.back_btn.setFont(QFont("Comfortaa", 12))
        self.back_btn.setFixedSize(350, 56)
        self.back_btn.clicked.connect(self.back_to_menu_signal.emit)
        main_layout.addWidget(self.back_btn, alignment=Qt.AlignCenter)

        self.add_team_input("")
        self.add_team_input("")

    def add_team_input(self, default_name=""):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)

        line_edit = QLineEdit()
        line_edit.setFont(QFont("Comfortaa", 13))
        line_edit.setPlaceholderText(f"Назва команди {len(self.team_inputs) + 1}")
        if default_name:
            line_edit.setText(default_name)
        row_layout.addWidget(line_edit, stretch=1)

        remove_btn = QPushButton("Видалити")
        remove_btn.setFont(QFont("Comfortaa", 10))
        remove_btn.clicked.connect(lambda: self.remove_team_input(row_widget, line_edit))
        row_layout.addWidget(remove_btn)

        self.teams_layout.addWidget(row_widget)
        self.team_inputs.append((row_widget, line_edit))

    def remove_team_input(self, row_widget, line_edit):
        if len(self.team_inputs) <= 2:
            QMessageBox.warning(self, "Увага", "Дві команди мінімум")
            return

        self.team_inputs = [item for item in self.team_inputs if item[1] != line_edit]
        row_widget.deleteLater()

    def confirm_and_start(self):
        teams = []
        for _, line_edit in self.team_inputs:
            name = line_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Помилка", "Заповніть назви усіх команд")
                return
            teams.append(name)

        if len(set(teams)) != len(teams):
            QMessageBox.warning(self, "Помилка", "Є однакові назви команд")
            return

        self.on_start_callback(teams)