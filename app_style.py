app_stylesheet = """
        QDialog {
            background-color: #FADADD;
        }

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