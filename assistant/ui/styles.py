class ChatStyles:
    SCROLLBAR ="""
            QScrollArea {
                background-color: #ffffff;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #f5f5f5;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #d1d5db;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """
    
    INPUT_FIELD = """
            QTextEdit {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 12px;
                background-color: #FFFFFF;  /* White background */
                color: #111827;            /* Dark text color */
            }
            QTextEdit:focus {
                border: 2px solid #5A67D8;
            }
    """
    
    SEND_BUTTON = """
            QPushButton {
                background-color: #5A67D8;
                border-radius: 20px;
                border: none;
                color: white;            /* White arrow color */
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4C51BF;
            }
            QPushButton:pressed {
                background-color: #434190;
            }
            QPushButton:disabled {
                background-color: #A5B4FC;
            }
        """
