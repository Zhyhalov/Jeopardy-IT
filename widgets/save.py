import os
import glob
from datetime import datetime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QApplication
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

class SaveSelectionWidget(QWidget):
    start_new_game_signal = Signal()
    load_game_signal = Signal(str)
    open_settings_signal = Signal()  # 👈 Новий сигнал

    def __init__(self, saves_dir="saves", parent=None):
        super().__init__(parent)
        self.saves_dir = saves_dir
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        title_label = QLabel("BBQ: Jeopardy!")
        title_label.setFont(QFont("Comfortaa", 30))
        title_label.setStyleSheet("color: #FF007F;")
        layout.addWidget(title_label, alignment=Qt.AlignCenter)

        # Кнопка «Нова гра»
        btn_new_game = QPushButton("Нова гра")
        btn_new_game.setFixedHeight(55)
        btn_new_game.setMinimumWidth(320)
        btn_new_game.setFont(QFont("Comfortaa", 13))
        btn_new_game.clicked.connect(self.start_new_game_signal.emit)
        layout.addWidget(btn_new_game)

        # Кнопка «Налаштування»
        btn_settings = QPushButton("Налаштування")
        btn_settings.setFixedHeight(55)
        btn_settings.setMinimumWidth(320)
        btn_settings.setFont(QFont("Comfortaa", 12))
        btn_settings.clicked.connect(self.open_settings_signal.emit)
        layout.addWidget(btn_settings)

        # 👈 Нова кнопка: «Вихід» з програми
        btn_exit = QPushButton("Вихід")
        btn_exit.setFixedHeight(55)
        btn_exit.setMinimumWidth(320)
        btn_exit.setFont(QFont("Comfortaa", 12))
        btn_exit.clicked.connect(QApplication.quit)
        layout.addWidget(btn_exit)

        saves_label = QLabel("Завантажити збережену гру:")
        saves_label.setStyleSheet("color: #94a3b8; font-size: 14px; margin-top: 15px;")
        layout.addWidget(saves_label, alignment=Qt.AlignCenter)

        recent_timestamps = self._get_latest_save_timestamps(limit=3)

        if not recent_timestamps:
            no_saves_lbl = QLabel("Немає збережених ігор")
            no_saves_lbl.setStyleSheet("color: #64748b; font-style: italic;")
            layout.addWidget(no_saves_lbl, alignment=Qt.AlignCenter)
        else:
            for ts in recent_timestamps:
                formatted_date = self._format_timestamp(ts)
                btn_load = QPushButton(f"{formatted_date}")
                btn_load.setFixedHeight(48)
                btn_load.setMinimumWidth(320)
                btn_load.setFont(QFont("Comfortaa", 11))
                btn_load.setStyleSheet("""
                    QPushButton {
                        background-color: #1e293b; color: #f8fafc; border-radius: 10px; border: 1px solid #475569;
                    }
                    QPushButton:hover { background-color: #334155; border-color: #38bdf8; }
                """)
                btn_load.clicked.connect(lambda checked=False, t=ts: self.load_game_signal.emit(t))
                layout.addWidget(btn_load)

    def _get_latest_save_timestamps(self, limit=3):
        if not os.path.exists(self.saves_dir):
            return []
        search_pattern = os.path.join(self.saves_dir, "save_history_*.json")
        history_files = glob.glob(search_pattern)
        history_files.sort(key=os.path.getmtime, reverse=True)
        timestamps = []
        for file_path in history_files[:limit]:
            filename = os.path.basename(file_path)
            ts = filename.replace("save_history_", "").replace(".json", "")
            timestamps.append(ts)
        return timestamps

    def _format_timestamp(self, ts):
        try:
            dt = datetime.strptime(ts, "%Y-%m-%d_%H-%M-%S")
            return dt.strftime("%d.%m.%Y, %H:%M:%S")
        except ValueError:
            return ts