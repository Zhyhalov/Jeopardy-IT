import sys
import json
import os
import glob
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QGraphicsOpacityEffect, QFrame, QSlider,
    QStackedWidget, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QUrl, QTimer, QTime
from PySide6.QtGui import QFont, QPixmap, QFontDatabase
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


from widgets.score_board import ScoreBoardWindow
from widgets.save import SaveSelectionWidget
from widgets.log_board import HistoryDialog
from widgets.team_setup import TeamSetupWidget
from widgets.settings import SettingsDialog
from widgets.results import FinalResultsWidget

from app_style import app_stylesheet


class QuestionOverlay(QFrame):
    def __init__(self, on_result_callback, parent=None):
        super().__init__(parent)
        self.on_result_callback = on_result_callback
        self.current_question = None
        self.active_button = None
        self.category_name = ""
        self.all_teams = []
        self.attempted_teams = set()
        self.selected_team = None

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
        layout.setContentsMargins(40, 25, 40, 25)
        layout.setSpacing(12)

        # 1. Верхня плашка: Заголовок + Таймер
        top_header_layout = QHBoxLayout()

        self.value_label = QLabel("")
        self.value_label.setFont(QFont("Comfortaa", 24, QFont.Bold))
        self.value_label.setStyleSheet("color: #ff6e40;")
        top_header_layout.addWidget(self.value_label)

        top_header_layout.addStretch()

        self.q_timer_seconds = 30
        self.q_time_left = 30
        self.q_timer = QTimer(self)
        self.q_timer.timeout.connect(self.update_q_timer)

        self.q_timer_btn = QPushButton("Старт")
        self.q_timer_btn.setFixedSize(160, 44)
        self.q_timer_btn.setFont(QFont("Comfortaa", 11, QFont.Bold))
        self.q_timer_btn.setStyleSheet("""
            QPushButton {
                background-color: #3E245D; color: #FFFFFF; border: 2px solid #FF758F; border-radius: 10px;
            }
            QPushButton:hover { background-color: #590D22; }
        """)
        self.q_timer_btn.clicked.connect(self.toggle_q_timer)
        top_header_layout.addWidget(self.q_timer_btn)

        self.q_timer_display = QLabel("30s")
        self.q_timer_display.setFont(QFont("Comfortaa", 16, QFont.Bold))
        self.q_timer_display.setStyleSheet("color: #FFD1DC; padding-left: 8px;")
        top_header_layout.addWidget(self.q_timer_display)

        layout.addLayout(top_header_layout)

        self.top_spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(self.top_spacer)

        # 2. Текст питання
        self.text_label = QLabel("")
        self.text_label.setFont(QFont("Comfortaa", 20))
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)
        layout.addWidget(self.text_label)

        # 3. Медіа
        self.media_image_label = QLabel("")
        self.media_image_label.setAlignment(Qt.AlignCenter)
        self.media_image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.media_image_label.setVisible(False)
        layout.addWidget(self.media_image_label)

        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.media_player.setAudioOutput(self.audio_output)

        self.video_widget = QVideoWidget(self)
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_widget.setVisible(False)
        self.media_player.setVideoOutput(self.video_widget)
        layout.addWidget(self.video_widget)

        self.video_controls = QWidget(self)
        video_ctrl_layout = QHBoxLayout(self.video_controls)
        video_ctrl_layout.setContentsMargins(0, 0, 0, 0)
        video_ctrl_layout.setSpacing(10)

        self.play_pause_btn = QPushButton("Pause")
        self.play_pause_btn.setFont(QFont("Comfortaa", 10))
        self.play_pause_btn.clicked.connect(self.toggle_video_play)
        video_ctrl_layout.addWidget(self.play_pause_btn)

        self.video_slider = QSlider(Qt.Horizontal)
        self.video_slider.sliderMoved.connect(self.set_video_position)
        video_ctrl_layout.addWidget(self.video_slider)

        self.volume_label = QLabel("🎧")
        self.volume_label.setFont(QFont("Comfortaa", 11))
        video_ctrl_layout.addWidget(self.volume_label)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        video_ctrl_layout.addWidget(self.volume_slider)

        self.video_controls.setVisible(False)
        layout.addWidget(self.video_controls)

        self.media_player.positionChanged.connect(self.update_video_slider)
        self.media_player.durationChanged.connect(self.update_video_duration)

        self.bottom_spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(self.bottom_spacer)

        # 4. Вибір команди, яка відповідає
        self.team_selection_box = QWidget()
        self.team_selection_layout = QVBoxLayout(self.team_selection_box)
        self.team_selection_layout.setContentsMargins(0, 0, 0, 0)
        self.team_selection_layout.setSpacing(6)

        self.team_select_title = QLabel("Оберіть команду, яка відповідає:")
        self.team_select_title.setFont(QFont("Comfortaa", 12, QFont.Bold))
        self.team_select_title.setAlignment(Qt.AlignCenter)
        self.team_select_title.setStyleSheet("color: #FFD1DC;")
        self.team_selection_layout.addWidget(self.team_select_title)

        self.team_buttons_layout = QHBoxLayout()
        self.team_buttons_layout.setSpacing(8)
        self.team_selection_layout.addLayout(self.team_buttons_layout)
        layout.addWidget(self.team_selection_box)

        # 5. Кнопки зарахування (з'являються ТІЛЬКИ після кліку по команді)
        self.validation_container = QWidget()
        validation_layout = QHBoxLayout(self.validation_container)
        validation_layout.setContentsMargins(0, 0, 0, 0)
        validation_layout.setSpacing(15)

        self.btn_correct = QPushButton("Відповідь зарахована")
        self.btn_correct.setFont(QFont("Comfortaa", 12, QFont.Bold))
        self.btn_correct.setStyleSheet("""
            QPushButton { background-color: #10B981; color: white; border-radius: 8px; padding: 10px 15px; }
            QPushButton:hover { background-color: #059669; }
        """)
        self.btn_correct.clicked.connect(lambda: self.submit_result(True))

        self.btn_incorrect = QPushButton("Відповідь не зарахована")
        self.btn_incorrect.setFont(QFont("Comfortaa", 12, QFont.Bold))
        self.btn_incorrect.setStyleSheet("""
            QPushButton { background-color: #EF4444; color: white; border-radius: 8px; padding: 10px 15px; }
            QPushButton:hover { background-color: #DC2626; }
        """)
        self.btn_incorrect.clicked.connect(lambda: self.submit_result(False))

        validation_layout.addWidget(self.btn_correct)
        validation_layout.addWidget(self.btn_incorrect)

        self.validation_container.setVisible(False)
        layout.addWidget(self.validation_container)

        # 6. Відповідь
        self.answer_label = QLabel("")
        font_ans = QFont("Comfortaa", 15)
        font_ans.setItalic(True)
        self.answer_label.setFont(font_ans)
        self.answer_label.setAlignment(Qt.AlignCenter)
        self.answer_label.setStyleSheet("color: #4CAF50;")
        self.answer_label.setVisible(False)
        layout.addWidget(self.answer_label)

        # 7. Нижні кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        self.show_ans_btn = QPushButton("Показати відповідь")
        self.show_ans_btn.setFont(QFont("Comfortaa", 12))
        self.show_ans_btn.setStyleSheet("""
            QPushButton { background-color: #0284c7; color: white; border-radius: 8px; padding: 10px 20px; }
            QPushButton:hover { background-color: #0369a1; }
        """)
        self.show_ans_btn.clicked.connect(self.toggle_answer)
        btn_layout.addWidget(self.show_ans_btn)

        self.close_btn = QPushButton("Закрити без оцінки")
        self.close_btn.setFont(QFont("Comfortaa", 12))
        self.close_btn.setStyleSheet("""
            QPushButton { background-color: #64748b; color: white; border-radius: 8px; padding: 10px 20px; }
            QPushButton:hover { background-color: #475569; }
        """)
        self.close_btn.clicked.connect(self.close_without_scoring)
        btn_layout.addWidget(self.close_btn)

        self.close_question_btn = QPushButton("Закрити питання")
        self.close_question_btn.setFont(QFont("Comfortaa", 12))
        self.close_question_btn.setStyleSheet("""
                    QPushButton { background-color: #991b1b; color: white; border-radius: 8px; padding: 10px 20px; }
                    QPushButton:hover { background-color: #7f1d1d; }
                """)
        self.close_question_btn.clicked.connect(self.close_question_permanently)
        btn_layout.addWidget(self.close_question_btn)

        layout.addLayout(btn_layout)

    def set_timer_duration(self, seconds):
        self.q_timer_seconds = seconds
        self.q_time_left = seconds
        self.q_timer_display.setText(f"{self.q_time_left}s")

    def toggle_q_timer(self):
        if self.q_timer.isActive():
            self.q_timer.stop()
            self.q_timer_btn.setText("Продовжити")
        else:
            self.q_timer.start(1000)
            self.q_timer_btn.setText("Пауза")

    def update_q_timer(self):
        if self.q_time_left > 0:
            self.q_time_left -= 1
            self.q_timer_display.setText(f"{self.q_time_left}s")
            if self.q_time_left <= 5:
                self.q_timer_display.setStyleSheet("color: #EF4444; font-weight: bold;")
        else:
            self.q_timer.stop()
            self.q_timer_btn.setText("Час вийшов!")
            self.q_timer_btn.setEnabled(False)

    def set_volume(self, value):
        self.audio_output.setVolume(value / 100.0)

    def show_question(self, question, target_button, category_name="", teams=None, read_only=False):
        self.current_question = question
        self.active_button = target_button
        self.category_name = category_name
        self.all_teams = teams or []
        self.attempted_teams.clear()
        self.selected_team = None

        prefix = " [Перегляд] " if read_only else ""
        self.value_label.setText(f"{prefix}Питання на {question.get('value', 0)} балів")
        self.text_label.setText(question.get('text', ''))
        self.answer_label.setText(f"Правильна відповідь: {question.get('answer', '')}")

        # У режимі перегляду ховаємо таймер
        self.q_timer.stop()
        self.q_timer_btn.setVisible(not read_only)
        self.q_timer_display.setVisible(not read_only)
        if not read_only:
            self.q_time_left = self.q_timer_seconds
            self.q_timer_display.setText(f"{self.q_time_left}s")
            self.q_timer_display.setStyleSheet("color: #FFD1DC;")
            self.q_timer_btn.setText("Старт")
            self.q_timer_btn.setEnabled(True)

        # Керування кнопками оцінювання та вибору команд
        self.team_selection_box.setVisible(not read_only)
        self.validation_container.setVisible(False)
        self.close_question_btn.setVisible(not read_only)

        if read_only:
            # У режимі перегляду відразу показуємо правильну відповідь
            self.answer_label.setVisible(True)
            self.show_ans_btn.setText("Приховати відповідь")
            self.close_btn.setText("Закрити перегляд")
        else:
            self.answer_label.setVisible(False)
            self.show_ans_btn.setText("Показати відповідь")
            self.close_btn.setText("Закрити без оцінки")

        self.media_image_label.setVisible(False)
        self.video_widget.setVisible(False)
        self.video_controls.setVisible(False)

        if self.media_player.playbackState() != QMediaPlayer.StoppedState:
            self.media_player.stop()

        self.set_volume(self.volume_slider.value())

        # Рендеримо команди тільки для звичайної гри
        if not read_only:
            self.rebuild_team_buttons()

        media_type = question.get("media_type", "none")
        media_path = question.get("media_path", None)
        layout = self.layout()

        if media_type == "video" and media_path and os.path.exists(media_path):
            self.media_player.setSource(QUrl.fromLocalFile(os.path.abspath(media_path)))
            self.video_widget.setVisible(True)
            self.video_controls.setVisible(True)
            self.play_pause_btn.setText("Pause")
            self.media_player.play()

            self.top_spacer.changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Minimum)
            self.bottom_spacer.changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Minimum)
            layout.setStretchFactor(self.video_widget, 10)
            layout.setStretchFactor(self.media_image_label, 0)
        elif media_type == "image" and media_path and os.path.exists(media_path):
            pixmap = QPixmap(media_path).scaled(800, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.media_image_label.setPixmap(pixmap)
            self.media_image_label.setVisible(True)

            self.top_spacer.changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Minimum)
            self.bottom_spacer.changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Minimum)
            layout.setStretchFactor(self.media_image_label, 10)
            layout.setStretchFactor(self.video_widget, 0)
        elif media_type == "audio" and media_path and os.path.exists(media_path):
            self.media_player.setSource(QUrl.fromLocalFile(os.path.abspath(media_path)))
            self.video_controls.setVisible(True)
            self.play_pause_btn.setText("Pause")
            self.media_player.play()

            self.top_spacer.changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
            self.bottom_spacer.changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
            layout.setStretchFactor(self.video_widget, 0)
            layout.setStretchFactor(self.media_image_label, 0)
        else:
            self.top_spacer.changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
            self.bottom_spacer.changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
            layout.setStretchFactor(self.video_widget, 0)
            layout.setStretchFactor(self.media_image_label, 0)

        layout.invalidate()

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

    def rebuild_team_buttons(self):
        # Очищуємо старі кнопки
        while self.team_buttons_layout.count():
            item = self.team_buttons_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self.team_btn_dict = {}
        for team in self.all_teams:
            btn = QPushButton(team)
            btn.setFont(QFont("Comfortaa", 11, QFont.Bold))
            btn.setFixedHeight(42)

            if team in self.attempted_teams:
                # Вже помилилися на цьому питанні
                btn.setEnabled(False)
                btn.setStyleSheet("background-color: #475569; color: #94a3b8; border: 1px solid #334155; border-radius: 8px;")
            elif team == self.selected_team:
                # Вибрана зараз
                btn.setStyleSheet("background-color: #D81B60; color: white; border: 2px solid #FFFFFF; border-radius: 8px;")
            else:
                btn.setStyleSheet("background-color: #1E293B; color: #F8FAFC; border: 1px solid #475569; border-radius: 8px;")

            btn.clicked.connect(lambda _, t=team: self.select_team(t))
            self.team_buttons_layout.addWidget(btn)
            self.team_btn_dict[team] = btn

    def select_team(self, team_name):
        self.selected_team = team_name
        self.rebuild_team_buttons()
        # Показуємо кнопки оцінки тільки після вибору команди
        self.validation_container.setVisible(True)

    def submit_result(self, is_correct: bool):
        if not self.selected_team:
            return

        value = self.current_question.get('value', 0) if self.current_question else 0
        q_title = f"{self.category_name} {value}"

        if is_correct:
            # Правильна відповідь: закриваємо картку питання та блокуємо кнопку на дошці
            self.hide_animated()
            self.on_result_callback(self.selected_team, is_correct, value, self.active_button, q_title, is_final=True)
        else:
            # Неправильна відповідь: штрафуємо, блокуємо цю команду, питання залишається активним
            self.attempted_teams.add(self.selected_team)
            wrong_team = self.selected_team
            self.selected_team = None
            self.validation_container.setVisible(False)

            # Сповіщаємо додаток про списання балів без закриття питання на дошці
            self.on_result_callback(wrong_team, False, value, self.active_button, q_title, is_final=False)

            # Якщо всі команди спробували і помилилися — автоматично закриваємо
            if len(self.attempted_teams) >= len(self.all_teams):
                self.hide_animated()
                self.on_result_callback(wrong_team, False, 0, self.active_button, q_title, is_final=True)
            else:
                self.rebuild_team_buttons()

    def close_without_scoring(self):
        # Закриття без зарахування (питання залишається доступним на дошці)
        self.hide_animated()

    def close_question_permanently(self):
        """Остаточне закриття питання без нарахування балів (п. 9, 10 ТЗ)."""
        self.hide_animated()
        q_title = f"{self.category_name} {self.current_question.get('value', 0)}" if self.current_question else ""
        # Викликаємо callback з is_correct=False, value=0 та is_final=True для блокування кнопки
        current_team = self.selected_team if self.selected_team else (self.all_teams[0] if self.all_teams else "")
        self.on_result_callback(current_team, False, 0, self.active_button, q_title, is_final=True)

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
        new_state = not self.answer_label.isVisible()
        self.answer_label.setVisible(new_state)
        self.show_ans_btn.setText("Приховати відповідь" if new_state else "Показати відповідь")

    def hide_animated(self):
        self.q_timer.stop()
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
    def __init__(self, json_file_path="quizes/questions.json"):
        super().__init__()
        self.setWindowTitle("Jeopardy! Game")

        self.game_settings = {
            "questions_file": json_file_path,
            "penalty_enabled": True,
            "timer_seconds": 30
        }

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            self.resize(geo.width() - 20, geo.height() - 50)

        self.game_data = self.load_questions(json_file_path)
        if not self.game_data:
            sys.exit(1)

        self.teams = []
        self.team_scores = {}
        self.current_team_idx = 0
        self.game_history = []
        self.buttons_map = {}

        self.time_seconds = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        self.stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)

        self.menu_widget = SaveSelectionWidget(saves_dir="saves")
        self.menu_widget.start_new_game_signal.connect(self.open_team_setup)
        self.menu_widget.load_game_signal.connect(self.load_game_from_save)
        self.menu_widget.open_settings_signal.connect(self.open_settings_dialog)
        self.stacked_widget.addWidget(self.menu_widget)

        # 2. Налаштування команд
        self.setup_widget = TeamSetupWidget(on_start_callback=self.start_game)
        # 👈 Підключаємо перехід назад до стартового меню
        self.setup_widget.back_to_menu_signal.connect(
            lambda: self.stacked_widget.setCurrentWidget(self.menu_widget))
        self.stacked_widget.addWidget(self.setup_widget)

        self.game_widget = QWidget()
        self.stacked_widget.addWidget(self.game_widget)

        # 👈 Фінальний екран гри
        self.results_widget = FinalResultsWidget()
        self.stacked_widget.addWidget(self.results_widget)

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


    def open_settings_dialog(self):
        dialog = SettingsDialog(self.game_settings, parent=self)
        if dialog.exec():
            self.game_settings = dialog.settings
            self.game_data = self.load_questions(self.game_settings["questions_file"])

            # 👈 Якщо оверлей уже створений, передаємо йому новий час
            if hasattr(self, 'overlay') and self.overlay is not None:
                self.overlay.set_timer_duration(self.game_settings.get("timer_seconds", 30))

    def open_team_setup(self):
        self.stacked_widget.setCurrentWidget(self.setup_widget)

    def start_game(self, teams):
        self.teams = teams
        self.team_scores = {team: 0 for team in teams}
        self.current_team_idx = 0
        self.game_history.clear()

        self.time_seconds = 0

        # Спочатку створюємо весь інтерфейс (зокрема self.timer_label)
        self.init_game_ui()
        self.stacked_widget.setCurrentWidget(self.game_widget)

        # Тільки тепер запускаємо таймер
        self.timer.start(1000)

    def load_game_from_save(self, timestamp):
        history_path = f"saves/save_history_{timestamp}.json"
        teams_path = f"saves/save_teams_{timestamp}.json"
        settings_path = f"saves/save_settings_{timestamp}.json"

        if not os.path.exists(history_path) or not os.path.exists(teams_path):
            QMessageBox.warning(self, "Помилка", "Файли збереження не знайдено!")
            return

        try:
            # 1. Відновлення налаштувань (якщо файл існує)
            if os.path.exists(settings_path):
                with open(settings_path, "r", encoding="utf-8") as f:
                    self.game_settings = json.load(f)
                # Оновлюємо базу питань на випадок, якщо грали за іншим файлом
                self.game_data = self.load_questions(self.game_settings.get("questions_file", "questions.json"))

            # 2. Відновлення команд та історії
            with open(teams_path, "r", encoding="utf-8") as f:
                self.team_scores = json.load(f)
                self.teams = list(self.team_scores.keys())

            with open(history_path, "r", encoding="utf-8") as f:
                loaded_history = json.load(f)

            # Будуємо ігрове поле за відновленими налаштуваннями
            self.init_game_ui()

            # 3. Синхронізуємо тривалість таймера в оверлеї
            if hasattr(self, 'overlay') and self.overlay is not None:
                self.overlay.set_timer_duration(self.game_settings.get("timer_seconds", 30))

            # 4. Відновлюємо історію та стан зіграних кнопок
            self.game_history = []
            for entry in loaded_history:
                btn = self.buttons_map.get(entry["question"])
                entry["button"] = btn
                self.game_history.append(entry)

                if entry["is_correct"] and btn:
                    btn.setEnabled(False)
                    btn.setStyleSheet("""
                        QPushButton { background-color: #94a3b8; color: #64748b; border: 1px solid #cbd5e1; border-radius: 6px; }
                    """)

            if self.game_history:
                last_entry = self.game_history[-1]
                if last_entry["is_correct"]:
                    self.current_team_idx = last_entry["team_idx"]
                else:
                    self.current_team_idx = (last_entry["team_idx"] + 1) % len(self.teams)

            self.update_score_button_text()
            self.timer.start(1000)
            self.stacked_widget.setCurrentWidget(self.game_widget)

        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити збереження:\n{e}")

    def update_timer(self):
        if hasattr(self, 'timer_label') and self.timer_label is not None:
            self.time_seconds += 1
            time_obj = QTime(0, 0, 0).addSecs(self.time_seconds)
            self.timer_label.setText(f"{time_obj.toString('mm:ss')}")

    def update_score_button_text(self):
        if self.teams:
            current_team_name = self.teams[self.current_team_idx]
            self.scores_btn.setText(f"Рахунок")
            self.scores_btn.setMinimumSize(300, 100)

    def show_score_board(self):
        dialog = ScoreBoardWindow(
            teams=self.teams,
            scores=self.team_scores,
            current_team_idx=self.current_team_idx,
            parent=self
        )
        dialog.exec()

    def show_history_dialog(self):
        dialog = HistoryDialog(
            history=self.game_history,
            teams=self.teams,
            scores=self.team_scores,
            on_undo_callback=self.undo_last_action,
            on_manual_score_callback=self.handle_manual_score,
            on_reopen_question_callback=self.reopen_question_for_view,
            parent=self
        )
        dialog.exec()

    def handle_manual_score(self, team: str, delta: int, is_direct_set: bool = False):
        """Ручне редагування балів ведучим (п. 13, 15 ТЗ)."""
        current_time_str = QTime(0, 0, 0).addSecs(self.time_seconds).toString("mm:ss")
        self.team_scores[team] = self.team_scores.get(team, 0) + delta

        entry = {
            "time": current_time_str,
            "team": team,
            "team_idx": self.teams.index(team) if team in self.teams else 0,
            "question": "Ручне редагування" if not is_direct_set else "Встановлення рахунку",
            "is_correct": False,
            "is_manual": True,
            "value": delta,
            "button": None
        }
        self.game_history.append(entry)
        self.update_score_button_text()
        self.auto_save_game()

    def reopen_question_for_view(self, question_title: str):
        """Перегляд питання без права оцінювання (Read-Only режим)."""
        target_q = None
        target_cat = ""
        for cat in self.game_data.get("categories", []):
            cat_name = cat.get("name", "")
            for q in cat.get("questions", []):
                val = q.get("value", 0)
                if f"{cat_name} {val}" == question_title:
                    target_q = q
                    target_cat = cat_name
                    break
            if target_q:
                break

        if target_q:
            btn = self.buttons_map.get(question_title)
            # 👈 Вмикаємо read_only=True
            self.overlay.show_question(target_q, btn, target_cat, teams=self.teams, read_only=True)
        else:
            QMessageBox.information(self, "Інформація", "Дані цього питання не знайдено для перегляду.")

    def save_game_history(self):
        os.makedirs("saves", exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        clean_history = []
        for entry in self.game_history:
            clean_entry = {
                "time": entry["time"],
                "team": entry["team"],
                "team_idx": entry["team_idx"],
                "question": entry["question"],
                "is_correct": entry["is_correct"],
                "value": entry["value"]
            }
            clean_history.append(clean_entry)

        # 1. Збереження історії та балів команд
        with open(f"saves/save_history_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(clean_history, f, ensure_ascii=False, indent=4)

        with open(f"saves/save_teams_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(self.team_scores, f, ensure_ascii=False, indent=4)

        # 2. Збереження активних налаштувань гри
        with open(f"saves/save_settings_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(self.game_settings, f, ensure_ascii=False, indent=4)

        # 3. Очищення старих сейвів (залишаємо 3 найновіших набори файлів)
        MAX_SAVES = 3
        history_files = sorted(glob.glob("saves/save_history_*.json"), key=os.path.getmtime)
        team_files = sorted(glob.glob("saves/save_teams_*.json"), key=os.path.getmtime)
        settings_files = sorted(glob.glob("saves/save_settings_*.json"), key=os.path.getmtime)

        while len(history_files) > MAX_SAVES:
            os.remove(history_files.pop(0))

        while len(team_files) > MAX_SAVES:
            os.remove(team_files.pop(0))

        while len(settings_files) > MAX_SAVES:
            os.remove(settings_files.pop(0))

        QApplication.quit()

    def init_game_ui(self):
        if self.game_widget.layout():
            QWidget().setLayout(self.game_widget.layout())

        main_layout = QVBoxLayout(self.game_widget)

        top_bar = QHBoxLayout()
        self.overlay = QuestionOverlay(on_result_callback=self.handle_answer_result, parent=self.game_widget)
        self.overlay.set_timer_duration(self.game_settings.get("timer_seconds", 30))
        self.history_btn = QPushButton("Лог гри")
        self.history_btn.setMinimumSize(300, 100)
        self.history_btn.setFont(QFont("Comfortaa",11))
        self.history_btn.clicked.connect(self.show_history_dialog)
        top_bar.addWidget(self.history_btn, alignment=Qt.AlignLeft)

        top_bar.addStretch()

        self.timer_label = QLabel("00:00")
        self.timer_label.setFont(QFont("Comfortaa", 20, QFont.Bold))
        self.timer_label.setAlignment(Qt.AlignCenter)

        self.timer_label.setFixedSize(140, 52)

        self.timer_label.setStyleSheet("""
                    QLabel {
                        background-color: #F19CBB;
                        color: #FFFFFF;
                        border: 3px solid #FF758F;
                        border-radius: 14px;
                        padding: 0px; /* При фіксованому розмірі внутрішній відступ краще обнулити */
                    }
                """)
        top_bar.addWidget(self.timer_label, alignment=Qt.AlignCenter)

        top_bar.addStretch()

        self.scores_btn = QPushButton()
        self.scores_btn.setFont(QFont("Comfortaa",11))
        self.scores_btn.clicked.connect(self.show_score_board)
        self.update_score_button_text()
        top_bar.addWidget(self.scores_btn, alignment=Qt.AlignRight)

        main_layout.addLayout(top_bar)

        self.save_btn = QPushButton("Зберегти та вийти")
        self.save_btn.setFixedSize(400, 50)
        self.save_btn.setFont(QFont("Comfortaa",11))
        self.save_btn.clicked.connect(self.save_game_history)

        # Замінюємо save_place на спільну панель дій
        # Спільна панель дій під верхнім рядком
        action_bar = QHBoxLayout()
        action_bar.setSpacing(15)

        # 1. Кнопка збереження та виходу
        self.save_btn = QPushButton("Зберегти та вийти")
        self.save_btn.setFixedHeight(50)
        self.save_btn.setFont(QFont("Comfortaa", 11))
        self.save_btn.clicked.connect(self.save_game_history)
        action_bar.addWidget(self.save_btn)  # 👈 Додаємо кнопку збереження

        # 2. Кнопка завершення гри
        self.finish_btn = QPushButton("Завершити гру")
        self.finish_btn.setFixedHeight(50)
        self.finish_btn.setFont(QFont("Comfortaa", 11))
        self.finish_btn.clicked.connect(self.confirm_finish_game)
        action_bar.addWidget(self.finish_btn)

        main_layout.addLayout(action_bar)

        board_container = QWidget()
        grid_layout = QGridLayout(board_container)
        grid_layout.setSpacing(10)
        grid_layout.setContentsMargins(0, 10, 0, 0)

        categories = self.game_data.get("categories", [])
        self.buttons_map.clear()

        for col_idx, category in enumerate(categories):
            cat_name = category.get("name", "")
            cat_label = QLabel(cat_name)
            cat_label.setFont(QFont("Comfortaa",18))
            cat_label.setStyleSheet(
                "background-color: #C3CDE6; color: #1e3d59; padding: 12px; border: 2px solid #1e3d59; border-radius: 6px;"
            )
            cat_label.setAlignment(Qt.AlignCenter)
            cat_label.setFixedHeight(60)
            cat_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            grid_layout.addWidget(cat_label, 0, col_idx)

            for row_idx, question in enumerate(category.get("questions", []), start=1):
                value = question.get("value", 100)
                btn = QPushButton(str(value))
                btn.setFont(QFont("Comfortaa",14))
                btn.setFixedHeight(55)
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ABCDEF; color: #1e3d59; border: 2px solid #1e3d59; border-radius: 6px;
                    }
                    QPushButton:hover { background-color: #3b82f6; color: white; }
                """)

                q_title = f"{cat_name} {value}"
                self.buttons_map[q_title] = btn
                btn.clicked.connect(lambda _, q=question, b=btn, c=cat_name: self.on_question_click(q, b, c))
                grid_layout.addWidget(btn, row_idx, col_idx)

        main_layout.addWidget(board_container)
        main_layout.addStretch()

        self.overlay = QuestionOverlay(on_result_callback=self.handle_answer_result, parent=self.game_widget)
        # 👈 Задаємо тривалість таймера з актуальних налаштувань
        self.overlay.set_timer_duration(self.game_settings.get("timer_seconds", 30))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'overlay') and self.overlay.isVisible():
            margin = 40
            self.overlay.setGeometry(self.game_widget.rect().adjusted(margin, margin, -margin, -margin))

    def on_question_click(self, question, button, category_name):
        # Передаємо список команд у вікно питання
        self.overlay.show_question(question, button, category_name, teams=self.teams)

    def handle_answer_result(self, team: str, is_correct: bool, value: int, button: QPushButton, question_title: str,
                             is_final: bool = True):
        current_time_str = QTime(0, 0, 0).addSecs(self.time_seconds).toString("mm:ss")
        team_idx = self.teams.index(team) if team in self.teams else 0

        history_entry = {
            "time": current_time_str,
            "team": team,
            "team_idx": team_idx,
            "question": question_title,
            "is_correct": is_correct,
            "value": value,
            "button": button
        }
        self.game_history.append(history_entry)

        if is_correct:
            self.team_scores[team] += value
            # Наступний хід передається команді, яка правильно відповіла
            self.current_team_idx = team_idx
        else:
            if self.game_settings.get("penalty_enabled", True):
                self.team_scores[team] -= value

        # Блокуємо кнопку питання на дошці тільки якщо питання завершене
        if is_final and button:
            button.setEnabled(False)
            button.setStyleSheet("""
                QPushButton { background-color: #94a3b8; color: #64748b; border: 1px solid #cbd5e1; border-radius: 6px; }
            """)

        self.update_score_button_text()

    def confirm_finish_game(self):
        reply = QMessageBox.question(
            self,
            "Підтвердження",
            "Ви дійсно хочете завершити гру та переглянути результати?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.finish_game()

    def finish_game(self):
        self.timer.stop()
        self.results_widget.set_results(self.team_scores, self.game_history)
        self.stacked_widget.setCurrentWidget(self.results_widget)

    def undo_last_action(self):
        if not self.game_history:
            return

        last_action = self.game_history.pop()
        team = last_action["team"]
        value = last_action["value"]
        is_correct = last_action["is_correct"]
        button = last_action["button"]

        if is_correct:
            self.team_scores[team] -= value
        else:
            self.team_scores[team] += value

        self.current_team_idx = last_action["team_idx"]

        if button:
            button.setEnabled(True)
            button.setStyleSheet("""
                QPushButton { background-color: #ABCDEF; color: #1e3d59; border: 2px solid #1e3d59; border-radius: 6px; }
                QPushButton:hover { background-color: #3b82f6; color: white; }
            """)

        self.update_score_button_text()


if __name__ == "__main__":
    if __name__ == "__main__":
        app = QApplication(sys.argv)

        font_path = "fonts/Comfortaa-VariableFont_wght.ttf"
        font_id = QFontDatabase.addApplicationFont(font_path)

        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                app_font_family = families[0]
                app.setFont(QFont(app_font_family, 11))
        else:
            print(f"Не вдалося завантажити шрифт із {font_path}")

        window = JeopardyApp("quizes/questions.json")
        window.setStyleSheet(app_stylesheet)
        window.show()

        sys.exit(app.exec())