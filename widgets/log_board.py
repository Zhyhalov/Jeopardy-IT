from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog,
    QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class HistoryDialog(QDialog):
    def __init__(self, history, teams, scores, on_undo_callback, on_manual_score_callback,
                 on_reopen_question_callback=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Історія дій та керування балами")
        self.setMinimumSize(850, 560)
        self.setModal(True)
        self.history = history
        self.teams = teams
        self.scores = scores
        self.on_undo_callback = on_undo_callback
        self.on_manual_score_callback = on_manual_score_callback
        self.on_reopen_question_callback = on_reopen_question_callback

        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E38;
                border: 2px solid #0284c7;
                border-radius: 12px;
            }
            QLabel { color: white; }
            QTableWidget {
                background-color: #0f172a;
                color: white;
                gridline-color: #334155;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Лог гри та керування")
        title.setFont(QFont("Comfortaa", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Таблиця історії з розширеними стовпцями за ТЗ
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Час", "Команда", "Питання", "Результат", "Зміна"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.cellDoubleClicked.connect(self.handle_row_double_click)

        self.populate_table()
        layout.addWidget(self.table)

        # Панель ручного редагування балів
        edit_layout = QHBoxLayout()
        edit_layout.setSpacing(10)

        lbl_team = QLabel("Команда:")
        lbl_team.setFont(QFont("Comfortaa", 11))
        edit_layout.addWidget(lbl_team)

        self.team_combo = QComboBox()
        self.team_combo.setFont(QFont("Comfortaa", 10))
        self.team_combo.addItems(self.teams)
        self.team_combo.setMinimumWidth(150)
        self.team_combo.setStyleSheet("""
            QComboBox { background-color: #0f172a; color: white; border: 1px solid #38bdf8; border-radius: 6px; padding: 4px; }
        """)
        edit_layout.addWidget(self.team_combo)

        btn_add = QPushButton("+ Додати")
        btn_add.setStyleSheet("background-color: #10B981; color: white; padding: 6px 12px; border-radius: 6px;")
        btn_add.clicked.connect(lambda: self.adjust_points("add"))
        edit_layout.addWidget(btn_add)

        btn_sub = QPushButton("− Відняти")
        btn_sub.setStyleSheet("background-color: #EF4444; color: white; padding: 6px 12px; border-radius: 6px;")
        btn_sub.clicked.connect(lambda: self.adjust_points("sub"))
        edit_layout.addWidget(btn_sub)

        btn_set = QPushButton("Встановити")
        btn_set.setStyleSheet("background-color: #0284c7; color: white; padding: 6px 12px; border-radius: 6px;")
        btn_set.clicked.connect(lambda: self.adjust_points("set"))
        edit_layout.addWidget(btn_set)

        layout.addLayout(edit_layout)

        # Нижні кнопки керування
        btn_layout = QHBoxLayout()

        self.view_q_btn = QPushButton("Переглянути питання")
        self.view_q_btn.setStyleSheet("background-color: #3b82f6; color: white; padding: 8px; border-radius: 6px;")
        self.view_q_btn.clicked.connect(self.view_selected_question)
        btn_layout.addWidget(self.view_q_btn)

        self.undo_btn = QPushButton("Скасувати останню дію")
        self.undo_btn.setStyleSheet("background-color: #e11d48; color: white; padding: 8px; border-radius: 6px;")
        self.undo_btn.setEnabled(len(self.history) > 0)
        self.undo_btn.clicked.connect(self.handle_undo)
        btn_layout.addWidget(self.undo_btn)

        close_btn = QPushButton("Закрити")
        close_btn.setStyleSheet("background-color: #64748b; color: white; padding: 8px; border-radius: 6px;")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def populate_table(self):
        self.table.setRowCount(len(self.history))
        for row, entry in enumerate(self.history):
            self.table.setItem(row, 0, QTableWidgetItem(str(entry.get("time", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(entry.get("team", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(str(entry.get("question", ""))))

            is_correct = entry.get("is_correct", False)
            res_text = "Правильно" if is_correct else ("Ручна зміна" if entry.get("is_manual") else "Неправильно")
            res_item = QTableWidgetItem(res_text)

            if entry.get("is_manual"):
                res_item.setForeground(Qt.yellow)
            else:
                res_item.setForeground(Qt.green if is_correct else Qt.red)
            self.table.setItem(row, 3, res_item)

            val = entry.get("value", 0)
            change_str = f"+{val}" if is_correct or val > 0 else f"{val}"
            self.table.setItem(row, 4, QTableWidgetItem(change_str))

    def handle_undo(self):
        self.on_undo_callback()
        self.populate_table()
        self.undo_btn.setEnabled(len(self.history) > 0)

    def adjust_points(self, mode):
        team = self.team_combo.currentText()
        if not team:
            return

        current_score = self.scores.get(team, 0)

        if mode == "add":
            val, ok = QInputDialog.getInt(self, "Додати бали", f"Скільки балів додати для «{team}»?", 100, 1, 10000, 50)
            if ok:
                self.on_manual_score_callback(team, val)
        elif mode == "sub":
            val, ok = QInputDialog.getInt(self, "Відняти бали", f"Скільки балів відняти у «{team}»?", 100, 1, 10000, 50)
            if ok:
                self.on_manual_score_callback(team, -val)
        elif mode == "set":
            val, ok = QInputDialog.getInt(self, "Встановити рахунок",
                                          f"Встановіть новий рахунок для «{team}» (було {current_score}):",
                                          current_score, -50000, 50000, 50)
            if ok:
                delta = val - current_score
                self.on_manual_score_callback(team, delta, is_direct_set=True)

        self.populate_table()
        self.undo_btn.setEnabled(len(self.history) > 0)

    def handle_row_double_click(self, row, column):
        self.view_question_at_row(row)

    def view_selected_question(self):
        row = self.table.currentRow()
        if row >= 0:
            self.view_question_at_row(row)
        else:
            QMessageBox.information(self, "Увага", "Оберіть рядок з питанням у таблиці.")

    def view_question_at_row(self, row):
        if row < len(self.history):
            entry = self.history[row]
            q_title = entry.get("question", "")
            if self.on_reopen_question_callback:
                self.on_reopen_question_callback(q_title)