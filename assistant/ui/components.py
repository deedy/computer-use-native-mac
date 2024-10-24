import os
from datetime import datetime
from PyQt6.QtWidgets import (QTextEdit, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QPushButton, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QSize, QRectF, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter, QPainterPath, QColor, QBrush, QTextDocument, QKeyEvent
from .styles import ChatStyles

class StyledChatArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)

        # Container widget
        container = QWidget()
        self.setWidget(container)
        self.layout = QVBoxLayout(container)
        self.layout.setSpacing(24)
        self.layout.setContentsMargins(24, 24, 24, 24)

        # Style the scroll area
        self.setStyleSheet("""
            QScrollArea {
                background-color: #151518;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #27272A;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #3F3F46;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)

        self.current_message = None

    def scroll_to_bottom(self):
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        self.widget().updateGeometry()

    def append_message(self, is_assistant: bool, message: str, timestamp: str = None,
                      tool_name: str = None, command_output: str = None):

        print("Debug: ", is_assistant, message, tool_name, command_output)
        """Add or update a message in the chat area"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%I:%M %p · %b %d, %Y")

        # For new messages
        if not self.current_message or not is_assistant:
            self.current_message = MessageWidget(is_assistant, message, timestamp, tool_name, command_output)
            self.layout.addWidget(self.current_message)
        # For updating existing assistant message
        elif is_assistant:
            if not tool_name and not command_output:
                self.current_message.update_message(message)
            else:
                self.current_message = MessageWidget(is_assistant, message, timestamp, tool_name, command_output)
                self.layout.addWidget(self.current_message)

        # Reset current_message for non-assistant messages
        if not is_assistant:
            self.current_message = None

        # Scroll to bottom
        self.scroll_to_bottom()

class CircularAvatarLabel(QLabel):
    def __init__(self, is_assistant: bool, size: int = 38):
        super().__init__()
        self.setFixedSize(size, size)

        # Create base pixmap
        target = QPixmap(size, size)
        target.fill(Qt.GlobalColor.transparent)

        # Setup painter
        painter = QPainter(target)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background circle
        bg_color = QColor("#4F46E5") if is_assistant else QColor("#52525B")
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, size, size)

        # Load and process icon
        icon_path = os.path.join(os.path.dirname(__file__),
                               "assistant_icon.png" if is_assistant else "user_icon.png")
        original_icon = QPixmap(icon_path)

        # Calculate icon size (smaller than container)
        icon_size = int(size * 0.6)  # Icon takes up 60% of the circle
        icon_padding = (size - icon_size) // 2

        # Scale icon
        scaled_icon = original_icon.scaled(
            icon_size,
            icon_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Draw the icon in the center
        painter.drawPixmap(
            icon_padding,
            icon_padding,
            scaled_icon
        )

        painter.end()

        self.setPixmap(target)
        self.setStyleSheet("""
            QLabel {
                background: transparent;
            }
        """)

class MessageWidget(QFrame):
    def __init__(self, is_assistant: bool, message: str, timestamp: str = None,
                 tool_name: str = None, command_output: str = None):
        super().__init__()
        self.is_assistant = is_assistant
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(12)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Timestamp
        if timestamp:
            time_label = QLabel(timestamp)
            time_label.setStyleSheet("""
                QLabel {
                    color: #71717A;
                    font-size: 13px;
                    font-weight: 400;
                    font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
                }
            """)
            self.main_layout.addWidget(time_label)

        # Message container
        message_container = QWidget()
        message_layout = QHBoxLayout(message_container)
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(16)

        # Avatar
        avatar_label = CircularAvatarLabel(is_assistant)
        message_layout.addWidget(avatar_label)

        # Content container
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        # Role label
        role_label = QLabel("Assistant" if is_assistant else "You")
        role_label.setStyleSheet("""
            QLabel {
                color: #E4E4E7;
                font-size: 15px;
                font-weight: 600;
                font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
            }
        """)
        content_layout.addWidget(role_label)

        # Message text
        self.message_label = QLabel(message)
        self.message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self.message_label.setStyleSheet("""
            QLabel {
                color: #E4E4E7;
                font-size: 15px;
                line-height: 1.5;
                font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
                background: transparent;
            }
            QLabel::selected {
                background-color: #4F46E5;
                color: white;
            }
        """)
        content_layout.addWidget(self.message_label)

        # Tool use indication
        if tool_name:
            tool_widget = QWidget()
            tool_layout = QHBoxLayout(tool_widget)
            tool_layout.setContentsMargins(0, 8, 0, 8)

            tool_icon = QLabel("🔧")
            tool_icon.setFixedSize(16, 16)
            tool_layout.addWidget(tool_icon)

            tool_label = QLabel(f"Using {tool_name}")
            tool_label.setStyleSheet("""
                QLabel {
                    color: #A1A1AA;
                    font-size: 13px;
                    font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
                }
            """)
            tool_layout.addWidget(tool_label)
            tool_layout.addStretch()
            content_layout.addWidget(tool_widget)

        message_layout.addWidget(content_widget)
        message_layout.addStretch()
        self.main_layout.addWidget(message_container)

        # Add command output if provided
        if command_output:
            self.add_command_output(command_output)

    def update_message(self, message: str):
        """Update the message text"""
        self.message_label.setText(message)

    def add_command_output(self, command_output: str):
        """Add command output to the message with conditional scrolling"""
        # Create command output container
        output_container = QWidget()
        output_layout = QVBoxLayout(output_container)
        output_layout.setContentsMargins(0, 8, 0, 0)

        # Create a temporary QTextDocument to count lines
        doc = QTextDocument()
        doc.setPlainText(command_output)
        line_count = doc.lineCount()

        # Command output text area
        output_text = QTextEdit()
        output_text.setReadOnly(True)
        output_text.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        output_text.setFont(QFont("Menlo", 13))

        # Calculate the height based on line count
        line_height = output_text.fontMetrics().lineSpacing()
        padding = 32  # 16px padding top + 16px padding bottom

        if line_count <= 10:
            # For 10 lines or less, set fixed height with no scrolling
            output_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            height = (line_height * line_count) + padding
            output_text.setFixedHeight(height)
        else:
            # For more than 10 lines, set fixed height with scrolling
            height = (line_height * 10) + padding
            output_text.setFixedHeight(height)
            output_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        output_text.setStyleSheet("""
            QTextEdit {
                background-color: #27272A;
                border: 1px solid #3F3F46;
                border-radius: 6px;
                padding: 16px;
                color: #E4E4E7;
                font-family: Menlo, Monaco, 'Courier New', monospace;
            }
            QScrollBar:vertical {
                border: none;
                background: #3F3F46;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #52525B;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        output_text.setText(command_output)
        output_layout.addWidget(output_text)

        self.main_layout.addWidget(output_container)

class StyledInputField(QTextEdit):
    enterPressed = pyqtSignal()  # New signal for enter key

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(48)
        self.setMaximumHeight(96)
        self.setFont(QFont("SF Pro Display", 15))  # Matching message font
        self.setStyleSheet("""
            QTextEdit {
                border: 1px solid #3F3F46;
                border-radius: 12px;
                padding: 16px;
                background-color: #27272A;
                color: #E4E4E7;
                font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
            }
            QTextEdit:focus {
                border: 2px solid #4F46E5;
                background-color: #27272A;
            }
        """)

        self.setPlaceholderText("Message Claude...")

    def keyPressEvent(self, event: QKeyEvent):
        # Check for Enter or Return key
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # If shift is not pressed, emit signal and prevent new line
            if not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.enterPressed.emit()
                return
        super().keyPressEvent(event)


class StyledSendButton(QPushButton):
    def __init__(self):
        super().__init__()
        self.setFixedSize(48, 48)  # Square button
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setEnabled(False)  # Initially disabled
        self.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #4338CA;
            }
            QPushButton:pressed {
                background-color: #3730A3;
            }
            QPushButton:disabled {
                background-color: #3F3F46;
            }
        """)
        self.setText("→")  # Arrow icon
