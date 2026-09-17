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
        /* Градієнт від світло-жовтого/оранжевого зверху до насиченого червоно-оранжевого знизу */
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop: 0.0 #FFE5EC,
            stop: 0.2 #FF758F,
            stop: 0.8 #FF4D6D,
            stop: 1.0 #C9184A
        );
        
        /* Товста темно-коричнева/бордова обводка */
        border: 4px solid #4A0E00;
        border-radius: 25px; /* Напівкруглі краї */
        
        /* Шрифт: білий товстий текст */
        color: #FFFFFF;
        font-size: 22px;
        font-weight: 700;
        font-family: "Comfortaa", sans-serif;
        
        /* Відступи всередині кнопки */
        padding: 10px 30px;
    }
    
    /* Ефект при наведенні мишкою (робимо кнопку трохи яскравішою) */
    QPushButton:hover {
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
        stop: 0.0 #FFFFFF, /* Більш біло-кремовий блиск зверху */
        stop: 0.3 #FF8DA1, /* Світліший яскраво-рожевий */
        stop: 0.7 #FF6680, /* Світліший соковитий ягідний */
        stop: 1.0 #DC2254  /* Світліший бордово-малиновий */
        );
        border-color: #5C1300;
    }
    
    /* Ефект при натисканні (кнопка зміщується і стає темнішою) */
    QPushButton:pressed {
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
        stop: 0.0 #FF758F,
        stop: 0.4 #FF4D6D,
        stop: 0.8 #C9184A,
        stop: 1.0 #800F2F
        );
        border-color: #330A00;
        
        /* Візуальне западання кнопки при кліку */
        padding-top: 13px;
        padding-bottom: 7px;
    }
    """