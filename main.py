import sys
import json
import os
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QGraphicsOpacityEffect, QFrame, QSlider, QLineEdit, QScrollArea,
    QStackedWidget, QSizePolicy, QDialog, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QUrl, QTimer, QTime
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


class ScoreBoardDialog(QDialog):
    def __init__(self, teams, scores, current_team_idx, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Поточний рахунок")
        self.setMinimumSize(700, 500)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E38;
                border: 2px solid #D81B60;
                border-radius: 12px;
            }
            QLabel {
                color: #FFFFFF;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Таблиця команд")
        title.setFont(QFont("Inter", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        for idx, team in enumerate(teams):
            score = scores.get(team, 0)
            is_current = (idx == current_team_idx)

            row_layout = QHBoxLayout()

            prefix = "-> " if is_current else "   "
            name_label = QLabel(f"{prefix}{team}")
            name_label.setFont(QFont("Inter", 13, QFont.Bold if is_current else QFont.Normal))

            if is_current:
                name_label.setStyleSheet("color: #FBBF24;")

            score_label = QLabel(f"{score} балів")
            score_label.setFont(QFont("Inter", 13, QFont.Bold))
            score_label.setAlignment(Qt.AlignRight)

            row_layout.addWidget(name_label)
            row_layout.addStretch()
            row_layout.addWidget(score_label)

            layout.addLayout(row_layout)

        close_btn = QPushButton("Закрити")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)


class HistoryDialog(QDialog):
    def __init__(self, history, on_undo_callback, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Історія дій")
        self.setMinimumSize(700, 500)
        self.setModal(True)
        self.history = history
        self.on_undo_callback = on_undo_callback

        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E38;
                border: 2px solid #0284c7;
                border-radius: 12px;
            }
            QLabel {
                color: white;
            }
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
                padding: 5px;
                border: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Лог гри")
        title.setFont(QFont("Inter", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Таблиця
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Час", "Команда", "Питання", "Результат", "Зміна"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.populate_table()
        layout.addWidget(self.table)

        # Нижні кнопки
        btn_layout = QHBoxLayout()

        self.undo_btn = QPushButton("Скасувати останню дію")
        self.undo_btn.setStyleSheet("background-color: #e11d48;")
        self.undo_btn.setEnabled(len(self.history) > 0)
        self.undo_btn.clicked.connect(self.handle_undo)
        btn_layout.addWidget(self.undo_btn)

        close_btn = QPushButton("Закрити")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def populate_table(self):
        self.table.setRowCount(len(self.history))
        for row, entry in enumerate(self.history):
            self.table.setItem(row, 0, QTableWidgetItem(entry["time"]))
            self.table.setItem(row, 1, QTableWidgetItem(entry["team"]))
            self.table.setItem(row, 2, QTableWidgetItem(entry["question"]))

            res_item = QTableWidgetItem("Правильно" if entry["is_correct"] else "Неправильно")
            res_item.setForeground(Qt.green if entry["is_correct"] else Qt.red)
            self.table.setItem(row, 3, res_item)

            change_str = f"+{entry['value']}" if entry["is_correct"] else f"-{entry['value']}"
            self.table.setItem(row, 4, QTableWidgetItem(change_str))

    def handle_undo(self):
        self.on_undo_callback()
        self.populate_table()
        self.undo_btn.setEnabled(len(self.history) > 0)


class TeamSetupWidget(QWidget):
    def __init__(self, on_start_callback, parent=None):
        super().__init__(parent)
        self.on_start_callback = on_start_callback
        self.team_inputs = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 40, 50, 40)
        main_layout.setSpacing(20)

        title_label = QLabel("Налаштування команд")
        title_label.setFont(QFont("Inter", 22, QFont.Bold))
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
        self.add_team_btn.setFont(QFont("Inter", 12, QFont.Bold))
        self.add_team_btn.clicked.connect(self.add_team_input)
        main_layout.addWidget(self.add_team_btn)

        self.start_game_btn = QPushButton("Розпочати гру")
        self.start_game_btn.setFont(QFont("Inter", 14, QFont.Bold))
        self.start_game_btn.clicked.connect(self.confirm_and_start)
        main_layout.addWidget(self.start_game_btn)

        self.add_team_input("Команда 1")
        self.add_team_input("Команда 2")

    def add_team_input(self, default_name=""):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)

        line_edit = QLineEdit()
        line_edit.setFont(QFont("Inter", 13))
        line_edit.setPlaceholderText(f"Назва команди {len(self.team_inputs) + 1}")
        if default_name:
            line_edit.setText(default_name)
        row_layout.addWidget(line_edit, stretch=1)

        remove_btn = QPushButton("Видалити")
        remove_btn.setFont(QFont("Inter", 10, QFont.Bold))
        remove_btn.clicked.connect(lambda: self.remove_team_input(row_widget, line_edit))
        row_layout.addWidget(remove_btn)

        self.teams_layout.addWidget(row_widget)
        self.team_inputs.append((row_widget, line_edit))

    def remove_team_input(self, row_widget, line_edit):
        if len(self.team_inputs) <= 1:
            QMessageBox.warning(self, "Увага", "Потрібно залишити хоча б одну команду!")
            return

        self.team_inputs = [item for item in self.team_inputs if item[1] != line_edit]
        row_widget.deleteLater()

    def confirm_and_start(self):
        teams = []
        for _, line_edit in self.team_inputs:
            name = line_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Помилка", "Будь ласка, заповніть назви всіх команд!")
                return
            teams.append(name)

        self.on_start_callback(teams)


class QuestionOverlay(QFrame):
    def __init__(self, on_result_callback, parent=None):
        super().__init__(parent)
        self.on_result_callback = on_result_callback
        self.current_question = None
        self.active_button = None
        self.category_name = ""

        self.setVisible(False)
        self.setStyleSheet("""
            QFrame#OverlayFrame {
                background-color: rgba(15, 23, 42, 0.96);
                border: 3px solid #ff6e40;
                border-radius: 15px;
            }
            QLabel { color: white; }
        """)
        self.setObjectName("OverlayFrame")

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        self.value_label = QLabel("")
        self.value_label.setFont(QFont("Inter", 18, QFont.Bold))
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("color: #ff6e40;")
        layout.addWidget(self.value_label)

        self.text_label = QLabel("")
        self.text_label.setFont(QFont("Inter", 16))
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)
        layout.addWidget(self.text_label)

        # 1. Зображення
        self.media_image_label = QLabel("")
        self.media_image_label.setAlignment(Qt.AlignCenter)
        self.media_image_label.setVisible(False)
        layout.addWidget(self.media_image_label, stretch=1)

        # 2. Відео
        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.media_player.setAudioOutput(self.audio_output)

        self.video_widget = QVideoWidget(self)
        self.video_widget.setMinimumSize(400, 250)
        self.video_widget.setVisible(False)
        self.media_player.setVideoOutput(self.video_widget)
        layout.addWidget(self.video_widget, stretch=1)

        self.video_controls = QWidget(self)
        video_ctrl_layout = QHBoxLayout(self.video_controls)
        video_ctrl_layout.setContentsMargins(0, 0, 0, 0)

        self.play_pause_btn = QPushButton("Pause")
        self.play_pause_btn.setFont(QFont("Inter", 10, QFont.Bold))
        self.play_pause_btn.clicked.connect(self.toggle_video_play)
        video_ctrl_layout.addWidget(self.play_pause_btn)

        self.video_slider = QSlider(Qt.Horizontal)
        self.video_slider.sliderMoved.connect(self.set_video_position)
        video_ctrl_layout.addWidget(self.video_slider)

        self.video_controls.setVisible(False)
        layout.addWidget(self.video_controls)

        self.media_player.positionChanged.connect(self.update_video_slider)
        self.media_player.durationChanged.connect(self.update_video_duration)

        # 3. Відповідь
        self.answer_label = QLabel("")
        font_ans = QFont("Inter", 15)
        font_ans.setItalic(True)
        self.answer_label.setFont(font_ans)
        self.answer_label.setAlignment(Qt.AlignCenter)
        self.answer_label.setStyleSheet("color: #4CAF50;")
        self.answer_label.setVisible(False)
        layout.addWidget(self.answer_label)

        # Кнопки валідації
        self.validation_container = QWidget()
        validation_layout = QHBoxLayout(self.validation_container)
        validation_layout.setContentsMargins(0, 0, 0, 0)

        self.btn_correct = QPushButton("✅ Відповідь зарахована")
        self.btn_correct.setFont(QFont("Inter", 12, QFont.Bold))
        self.btn_correct.setStyleSheet("""
            QPushButton { background-color: #10B981; color: white; border-radius: 8px; padding: 10px 15px; }
            QPushButton:hover { background-color: #059669; }
        """)
        self.btn_correct.clicked.connect(lambda: self.submit_result(True))

        self.btn_incorrect = QPushButton("❌ Відповідь не зарахована")
        self.btn_incorrect.setFont(QFont("Inter", 12, QFont.Bold))
        self.btn_incorrect.setStyleSheet("""
            QPushButton { background-color: #EF4444; color: white; border-radius: 8px; padding: 10px 15px; }
            QPushButton:hover { background-color: #DC2626; }
        """)
        self.btn_incorrect.clicked.connect(lambda: self.submit_result(False))

        validation_layout.addWidget(self.btn_correct)
        validation_layout.addWidget(self.btn_incorrect)

        self.validation_container.setVisible(False)
        layout.addWidget(self.validation_container)

        btn_layout = QHBoxLayout()

        self.show_ans_btn = QPushButton("Показати відповідь")
        self.show_ans_btn.setFont(QFont("Inter", 12, QFont.Bold))
        self.show_ans_btn.setStyleSheet("""
            QPushButton { background-color: #0284c7; color: white; border-radius: 8px; padding: 10px 20px; }
            QPushButton:hover { background-color: #0369a1; }
        """)
        self.show_ans_btn.clicked.connect(self.toggle_answer)
        btn_layout.addWidget(self.show_ans_btn)

        self.close_btn = QPushButton("Закрити без оцінки")
        self.close_btn.setFont(QFont("Inter", 12, QFont.Bold))
        self.close_btn.setStyleSheet("""
            QPushButton { background-color: #64748b; color: white; border-radius: 8px; padding: 10px 20px; }
            QPushButton:hover { background-color: #475569; }
        """)
        self.close_btn.clicked.connect(self.hide_animated)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def show_question(self, question, target_button, category_name=""):
        self.current_question = question
        self.active_button = target_button
        self.category_name = category_name

        self.value_label.setText(f"Питання на {question.get('value', 0)} балів")
        self.text_label.setText(question.get('text', ''))
        self.answer_label.setText(f"Правильна відповідь: {question.get('answer', '')}")

        self.answer_label.setVisible(False)
        self.validation_container.setVisible(False)
        self.show_ans_btn.setText("Показати відповідь")

        self.media_image_label.setVisible(False)
        self.video_widget.setVisible(False)
        self.video_controls.setVisible(False)

        media_type = question.get("media_type", "none")
        media_path = question.get("media_path", None)

        if media_type == "image" and media_path:
            if os.path.exists(media_path):
                pixmap = QPixmap(media_path)
                scaled_pixmap = pixmap.scaled(500, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.media_image_label.setPixmap(scaled_pixmap)
                self.media_image_label.setVisible(True)

        elif media_type == "video" and media_path:
            if os.path.exists(media_path):
                abs_path = os.path.abspath(media_path)
                self.media_player.setSource(QUrl.fromLocalFile(abs_path))
                self.video_widget.setVisible(True)
                self.video_controls.setVisible(True)
                self.play_pause_btn.setText("Pause")
                self.media_player.play()
        # 3. Аудіо (Новий блок)
        elif media_type == "audio" and media_path:
            if os.path.exists(media_path):
                abs_path = os.path.abspath(media_path)
                self.media_player.setSource(QUrl.fromLocalFile(abs_path))
                # Показуємо панель керування (Play/Pause та слайдер), але ховаємо відеоекрани
                self.video_controls.setVisible(True)
                self.play_pause_btn.setText("Pause")
                self.media_player.play()
            else:
                self.media_image_label.setText(f"[Помилка: Аудіофайл '{media_path}' не знайдено]")
                self.media_image_label.setVisible(True)

        margin = 40
        parent_rect = self.parent().rect()
        target_rect = parent_rect.adjusted(margin, margin, -margin, -margin)
        self.setGeometry(target_rect)
        self.raise_()
        self.setVisible(True)

        self.anim_fade = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_fade.setDuration(350)
        self.anim_fade.setStartValue(0.0)
        self.anim_fade.setEndValue(1.0)
        self.anim_fade.setEasingCurve(QEasingCurve.OutCubic)

        center_point = target_rect.center()
        start_rect = QRect(center_point.x() - 50, center_point.y() - 50, 100, 100)
        self.anim_geom = QPropertyAnimation(self, b"geometry")
        self.anim_geom.setDuration(350)
        self.anim_geom.setStartValue(start_rect)
        self.anim_geom.setEndValue(target_rect)
        self.anim_geom.setEasingCurve(QEasingCurve.OutBack)

        self.anim_fade.start()
        self.anim_geom.start()

    def toggle_video_play(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_pause_btn.setText("Play")
        else:
            self.media_player.play()
            self.play_pause_btn.setText("Pause")

    def set_video_position(self, position):
        self.media_player.setPosition(position)

    def update_video_slider(self, position):
        self.video_slider.setValue(position)

    def update_video_duration(self, duration):
        self.video_slider.setRange(0, duration)

    def toggle_answer(self):
        is_visible = self.answer_label.isVisible()
        new_state = not is_visible
        self.answer_label.setVisible(new_state)
        self.validation_container.setVisible(new_state)
        self.show_ans_btn.setText("Приховати відповідь" if new_state else "Показати відповідь")

    def submit_result(self, is_correct: bool):
        value = self.current_question.get('value', 0) if self.current_question else 0
        q_title = f"{self.category_name} {value}"
        self.hide_animated()
        self.on_result_callback(is_correct, value, self.active_button, q_title)

    def hide_animated(self):
        if self.media_player.playbackState() != QMediaPlayer.StoppedState:
            self.media_player.stop()

        self.video_widget.setVisible(False)
        self.video_controls.setVisible(False)

        self.anim_fade = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_fade.setDuration(250)
        self.anim_fade.setStartValue(1.0)
        self.anim_fade.setEndValue(0.0)
        self.anim_fade.setEasingCurve(QEasingCurve.InCubic)
        self.anim_fade.finished.connect(lambda: self.setVisible(False))
        self.anim_fade.start()


class JeopardyApp(QMainWindow):
    def __init__(self, json_file_path="questions.json"):
        super().__init__()
        self.setWindowTitle("Jeopardy Game")
        self.resize(1100, 750)

        self.game_data = self.load_questions(json_file_path)
        if not self.game_data:
            sys.exit(1)

        self.teams = []
        self.team_scores = {}
        self.current_team_idx = 0
        self.game_history = []  # Список дій гри

        # Таймер
        self.time_seconds = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        self.stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)

        self.setup_widget = TeamSetupWidget(on_start_callback=self.start_game)
        self.stacked_widget.addWidget(self.setup_widget)

        self.game_widget = QWidget()
        self.stacked_widget.addWidget(self.game_widget)

    def load_questions(self, file_path):
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "Помилка", f"Файл {file_path} не знайдено!")
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Помилка JSON", f"Некоректний формат JSON:\n{e}")
            return None

    def start_game(self, teams):
        self.teams = teams
        self.team_scores = {team: 0 for team in teams}
        self.current_team_idx = 0
        self.game_history.clear()

        # Запуск секундного таймера
        self.time_seconds = 0
        self.timer.start(1000)

        self.init_game_ui()
        self.stacked_widget.setCurrentWidget(self.game_widget)

    def update_timer(self):
        """Оновлення динамічного таймеру в центрі заголовка"""
        self.time_seconds += 1
        time_obj = QTime(0, 0, 0).addSecs(self.time_seconds)
        self.timer_label.setText(f"{time_obj.toString('mm:ss')}")

    def update_score_button_text(self):
        current_team_name = self.teams[self.current_team_idx]
        self.scores_btn.setText(f"Команди ({current_team_name})")
        self.scores_btn.setMinimumSize(200, 100)

    def show_score_board(self):
        dialog = ScoreBoardDialog(
            teams=self.teams,
            scores=self.team_scores,
            current_team_idx=self.current_team_idx,
            parent=self
        )
        dialog.exec()

    def show_history_dialog(self):
        """Відкриває вікно історії дій з можливістю скасування"""
        dialog = HistoryDialog(
            history=self.game_history,
            on_undo_callback=self.undo_last_action,
            parent=self
        )
        dialog.exec()

    def init_game_ui(self):
        main_layout = QVBoxLayout(self.game_widget)

        # --- ВЕРХНЯ ПАНЕЛЬ СТРУКТУРИ ---
        top_bar = QHBoxLayout()

        # 1. Зліва: Кнопка «Історія дій»
        self.history_btn = QPushButton("Історія дій")
        self.history_btn.setMinimumSize(200, 100)
        self.history_btn.setFont(QFont("Inter", 11, QFont.Bold))
        self.history_btn.setStyleSheet("""
            QPushButton { background-color: #0284c7; color: white; border-radius: 8px; padding: 8px 16px; }
            QPushButton:hover { background-color: #0369a1; }
        """)
        self.history_btn.clicked.connect(self.show_history_dialog)
        top_bar.addWidget(self.history_btn, alignment=Qt.AlignLeft)

        # Пружина для вирівнювання
        top_bar.addStretch()

        # 2. По центру: Динамічний таймер
        self.timer_label = QLabel("00:00")
        self.timer_label.setFont(QFont("Inter", 16, QFont.Bold))
        self.timer_label.setStyleSheet("color: #1E1E38; font-weight: bold;")
        top_bar.addWidget(self.timer_label, alignment=Qt.AlignCenter)

        # Пружина для вирівнювання
        top_bar.addStretch()

        # 3. Зправа у кутку: Кнопка списку команд
        self.scores_btn = QPushButton()
        self.scores_btn.setFont(QFont("Inter", 11, QFont.Bold))
        self.scores_btn.clicked.connect(self.show_score_board)
        self.update_score_button_text()
        top_bar.addWidget(self.scores_btn, alignment=Qt.AlignRight)

        main_layout.addLayout(top_bar)

        # --- ІГРОВА ДОШКА ---
        board_container = QWidget()
        grid_layout = QGridLayout(board_container)
        grid_layout.setSpacing(10)
        grid_layout.setContentsMargins(0, 10, 0, 0)

        categories = self.game_data.get("categories", [])

        for col_idx, category in enumerate(categories):
            cat_name = category.get("name", "")
            cat_label = QLabel(cat_name)
            cat_label.setFont(QFont("Inter", 20, QFont.Bold))
            cat_label.setStyleSheet(
                "background-color: #C3CDE6; padding: 12px; border: 2px solid #1e3d59; border-radius: 6px;")
            cat_label.setAlignment(Qt.AlignCenter)
            cat_label.setFixedHeight(60)
            cat_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            grid_layout.addWidget(cat_label, 0, col_idx)

            for row_idx, question in enumerate(category.get("questions", []), start=1):
                value = question.get("value", 100)
                btn = QPushButton(str(value))
                btn.setFont(QFont("Inter", 14))
                btn.setFixedHeight(60)
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ABCDEF; color: #1e3d59; border: 2px solid #1e3d59; border-radius: 6px;
                    }
                    QPushButton:hover { color: white; }
                """)
                btn.clicked.connect(lambda _, q=question, b=btn, c=cat_name: self.on_question_click(q, b, c))
                grid_layout.addWidget(btn, row_idx, col_idx)

        main_layout.addWidget(board_container)
        main_layout.addStretch()

        self.overlay = QuestionOverlay(on_result_callback=self.handle_answer_result, parent=self.game_widget)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'overlay') and self.overlay.isVisible():
            margin = 40
            self.overlay.setGeometry(self.game_widget.rect().adjusted(margin, margin, -margin, -margin))

    def on_question_click(self, question, button, category_name):
        self.overlay.show_question(question, button, category_name)

    def handle_answer_result(self, is_correct: bool, value: int, button: QPushButton, question_title: str):
        """Обробка відповіді та додавання запису до історії"""
        current_team = self.teams[self.current_team_idx]
        current_time_str = QTime(0, 0, 0).addSecs(self.time_seconds).toString("mm:ss")

        # Фіксуємо подію в історії
        history_entry = {
            "time": current_time_str,
            "team": current_team,
            "team_idx": self.current_team_idx,
            "question": question_title,
            "is_correct": is_correct,
            "value": value,
            "button": button
        }
        self.game_history.append(history_entry)

        if is_correct:
            self.team_scores[current_team] += value
            if button:
                button.setEnabled(False)
                button.setStyleSheet("""
                    QPushButton { background-color: #94a3b8; color: #64748b; border: 1px solid #cbd5e1; border-radius: 6px; }
                """)
        else:
            self.team_scores[current_team] -= value
            self.current_team_idx = (self.current_team_idx + 1) % len(self.teams)
            if button:
                button.setEnabled(True)
                button.setStyleSheet("""
                    QPushButton { background-color: #ABCDEF; color: #1e3d59; border: 2px solid #1e3d59; border-radius: 6px; }
                    QPushButton:hover { color: white; }
                """)

        self.update_score_button_text()

    def undo_last_action(self):
        """Відкат останньої дії з історії"""
        if not self.game_history:
            return

        last_action = self.game_history.pop()
        team = last_action["team"]
        value = last_action["value"]
        is_correct = last_action["is_correct"]
        button = last_action["button"]

        # Відновлюємо бали та хід
        if is_correct:
            self.team_scores[team] -= value
        else:
            self.team_scores[team] += value
            self.current_team_idx = last_action["team_idx"]

        # Відновлюємо активність кнопки
        if button:
            button.setEnabled(True)
            button.setStyleSheet("""
                QPushButton { background-color: #ABCDEF; color: #1e3d59; border: 2px solid #1e3d59; border-radius: 6px; }
                QPushButton:hover { color: white; }
            """)

        self.update_score_button_text()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = JeopardyApp("questions.json")

    app_stylesheet = """
        QMainWindow, QStackedWidget, TeamSetupWidget {
            background-color: #FFD1DC;
        }

        QScrollArea, QScrollArea > QWidget > QWidget {
            background-color: transparent;
            border: none;
        }

        QLabel {
            color: #1E1E38;
            background-color: transparent;
        }

        QLineEdit {
            background-color: #FFFFFF;
            color: #1E1E38;
            border: 2px solid #E8B8C4;
            border-radius: 8px;
            padding: 8px;
        }

        QLineEdit:focus {
            border-color: #D81B60;
        }

        QPushButton {
            background-color: #D81B60;
            color: #FFFFFF;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #AD1457;
        }

        QPushButton:pressed {
            background-color: #880E4F;
        }
    """

    window.setStyleSheet(app_stylesheet)
    window.show()
    sys.exit(app.exec())