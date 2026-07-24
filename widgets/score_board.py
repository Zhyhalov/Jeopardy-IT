from PySide6.QtWidgets import (QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class ScoreBoardWindow(QDialog):
    def __init__(self, teams, scores, current_team_idx, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Поточний рахунок")
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Таблиця команд")
        title.setFont(QFont("Inter", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)

        for idx, team in enumerate(teams):
            score = scores.get(team, 0)
            is_current = (idx == current_team_idx)

            row_layout = QHBoxLayout()

            prefix = "-> " if is_current else "   "
            name_label = QLabel(f"{prefix}{team}")
            name_label.setFont(QFont("Inter", 13, QFont.Bold if is_current else QFont.Normal))

            # if is_current:
            #     name_label.setStyleSheet("color: #007FFF;")

            score_label = QLabel(f"{score} балів")
            score_label.setFont(QFont("Inter", 13, QFont.Bold))
            score_label.setAlignment(Qt.AlignRight)

            row_layout.addWidget(name_label)
            row_layout.addStretch()
            row_layout.addWidget(score_label)

            layout.addLayout(row_layout)
            grid_layout.addWidget(name_label, idx, 0, Qt.AlignLeft | Qt.AlignVCenter)
            grid_layout.addWidget(score_label, idx, 1, Qt.AlignRight | Qt.AlignVCenter)

        grid_layout.setColumnStretch(0, 1)

        layout.addLayout(grid_layout)
        layout.addStretch()
        close_btn = QPushButton("Закрити")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
