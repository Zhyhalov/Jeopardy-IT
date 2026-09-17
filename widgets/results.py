import csv
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class FinalResultsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scores = {}
        self.history = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(18)

        self.title_label = QLabel("Гра завершена!")
        self.title_label.setFont(QFont("Comfortaa", 26, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: #FF758F;")
        layout.addWidget(self.title_label)

        self.winner_label = QLabel("")
        self.winner_label.setFont(QFont("Comfortaa", 20, QFont.Bold))
        self.winner_label.setAlignment(Qt.AlignCenter)
        self.winner_label.setStyleSheet("color: #10B981;")
        layout.addWidget(self.winner_label)

        # Таблиця підсумкових місць
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Місце", "Команда", "Бали"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E38;
                color: #FFFFFF;
                gridline-color: #334155;
                border: 2px solid #FF758F;
                border-radius: 10px;
                font-size: 13pt;
            }
            QHeaderView::section {
                background-color: #3E245D;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
        """)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        self.btn_csv = QPushButton("Завантажити CSV-лог")
        self.btn_csv.setFixedHeight(56)
        self.btn_csv.setFont(QFont("Comfortaa", 12, QFont.Bold))
        self.btn_csv.setStyleSheet("""
            QPushButton {
                background-color: #0284c7; color: white; border-radius: 12px; padding: 10px 20px;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        self.btn_csv.clicked.connect(self.export_csv)
        btn_layout.addWidget(self.btn_csv)

        self.btn_exit = QPushButton("Вихід")
        self.btn_exit.setFixedHeight(56)
        self.btn_exit.setFont(QFont("Comfortaa", 12, QFont.Bold))
        self.btn_exit.clicked.connect(QApplication.quit)
        btn_layout.addWidget(self.btn_exit)

        layout.addLayout(btn_layout)

    def set_results(self, scores: dict, history: list):
        self.scores = scores
        self.history = history

        # Сортування за балами від найбільшого
        sorted_teams = sorted(scores.items(), key=lambda item: item[1], reverse=True)

        if sorted_teams:
            top_score = sorted_teams[0][1]
            winners = [team for team, score in sorted_teams if score == top_score]
            if len(winners) > 1:
                self.winner_label.setText(f"Нічия між командами: {', '.join(winners)} ({top_score} балів)!")
            else:
                self.winner_label.setText(f"Переможець: {winners[0]} ({top_score} балів)!")
        else:
            self.winner_label.setText("Результати відсутні")

        self.table.setRowCount(len(sorted_teams))
        for place, (team, score) in enumerate(sorted_teams, start=1):
            place_item = QTableWidgetItem(f"#{place}")
            place_item.setTextAlignment(Qt.AlignCenter)
            team_item = QTableWidgetItem(team)
            team_item.setTextAlignment(Qt.AlignCenter)
            score_item = QTableWidgetItem(f"{score} балів")
            score_item.setTextAlignment(Qt.AlignCenter)

            if place == 1:
                place_item.setForeground(Qt.yellow)
                team_item.setForeground(Qt.yellow)
                score_item.setForeground(Qt.yellow)

            self.table.setItem(place - 1, 0, place_item)
            self.table.setItem(place - 1, 1, team_item)
            self.table.setItem(place - 1, 2, score_item)

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Зберегти CSV лог", "game_log.csv", "CSV Files (*.csv)")
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Час", "Команда", "Питання", "Результат", "Зміна балів"])
                for entry in self.history:
                    res = "Правильно" if entry.get("is_correct") else ("Ручна зміна" if entry.get("is_manual") else "Неправильно")
                    val = entry.get("value", 0)
                    change = f"+{val}" if entry.get("is_correct") or val > 0 else f"{val}"
                    writer.writerow([
                        entry.get("time", ""),
                        entry.get("team", ""),
                        entry.get("question", ""),
                        res,
                        change
                    ])

                writer.writerow([])
                writer.writerow(["Підсумковий рахунок:"])
                for team, score in sorted(self.scores.items(), key=lambda x: x[1], reverse=True):
                    writer.writerow([team, score])

            QMessageBox.information(self, "+", "Лог гри збережено")
        except Exception as e:
            QMessageBox.critical(self, "-а", f"Не вдалося експортувати лог:\n{e}")