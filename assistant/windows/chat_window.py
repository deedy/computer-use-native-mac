from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject
from ..ui.components import StyledChatArea, StyledInputField, StyledSendButton
from ..services.api_client import AnthropicClient
from ..services.command_executor import CommandExecutor
from ..services.history_manager import HistoryManager
import json
import pyautogui
from PIL import Image

class MessageWorker(QObject):
    """Worker for processing messages in a background thread"""
    finished = pyqtSignal()
    response_chunk = pyqtSignal(str)
    command_output = pyqtSignal(str, str, str)  # message, tool_name, output

    def __init__(self, message: str, api_client: AnthropicClient, command_executor: CommandExecutor):
        super().__init__()
        self.message = message
        self.api_client = api_client
        self.command_executor = command_executor
        self.current_response = ""

    def process_message(self):
        try:
            for response in self.api_client.stream_response(self.message):
                if response.text:
                    self.current_response += response.text
                    self.response_chunk.emit(self.current_response)
                import pdb; pdb.set_trace()
                if response.tool == "bash":
                    if response.command:
                        try:
                            command_json = json.loads(response.command)
                            stdout, stderr = self.command_executor.execute_command(command_json["command"])
                            if stdout or stderr:
                                self.command_output.emit(
                                    "",
                                    response.tool,
                                    stdout + stderr
                                )
                        except json.JSONDecodeError:
                            pass
                elif response.tool == "computer":
                    if response.command:
                        try:
                            input_json = json.loads(response.command)
                            if input_json["input"]["action"] == "screenshot":
                                screenshot = pyautogui.screenshot()
                                resized_image = screenshot.resize((1024, 768), Image.Resampling.LANCZOS)

                        except json.JSONDecodeError:
                            pass
            self.finished.emit()
        except Exception as e:
            print(f"Error processing message: {e}")
            self.finished.emit()

class ChatWindow(QMainWindow):
    message_sent = pyqtSignal(str)

    def __init__(self, history_manager: HistoryManager, api_client: AnthropicClient):
        super().__init__()
        self.history_manager = history_manager
        self.api_client = api_client
        self.command_executor = CommandExecutor()
        self.worker = None
        self.thread = None

        self.setWindowTitle("Mac Assistant")
        self.setMinimumSize(800, 600)

        self.init_ui()
        self.load_chat_history()

    def send_message(self):
        message = self.input_field.toPlainText().strip()
        if not message or self.thread:  # Prevent multiple threads
            return

        # Disable input while processing
        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)

        # Show user message
        self.chat_area.append_message(is_assistant=False, message=message)
        self.chat_area.scroll_to_bottom()

        # Create thread and worker
        self.thread = QThread()
        self.worker = MessageWorker(message, self.api_client, self.command_executor)
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.process_message)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda: self.on_processing_complete(message))

        # Connect message handling signals
        self.worker.response_chunk.connect(self.handle_response)
        self.worker.command_output.connect(self.handle_command)

        # Start processing
        self.thread.start()

    def handle_response(self, response: str):
        """Handle streaming response chunks"""
        self.chat_area.append_message(
            is_assistant=True,
            message=response,
        )
        self.chat_area.scroll_to_bottom()

    def handle_command(self, message: str, tool_name: str, command_output: str):
        """Handle command output"""
        self.chat_area.append_message(
            is_assistant=True,
            message=message,
            tool_name=tool_name,
            command_output=command_output
        )
        self.chat_area.scroll_to_bottom()

    def on_processing_complete(self, original_message: str):
        """Clean up after processing is complete"""
        # Save the conversation
        if self.worker:
            self.history_manager.save_conversation(original_message, self.worker.current_response)

        # Reset thread-related variables
        self.thread = None
        self.worker = None

        # Re-enable input
        self.input_field.setEnabled(True)
        self.update_send_button_state()

    def closeEvent(self, event):
        """Ensure clean thread shutdown when closing window"""
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        event.ignore()
        self.hide()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(16)  # Add spacing between chat area and input
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins

        # Chat area
        self.chat_area = StyledChatArea()
        layout.addWidget(self.chat_area)

        # Input container with fixed height
        input_container = QWidget()
        input_container.setFixedHeight(120)
        input_container.setStyleSheet("""
            QWidget {
                background-color: #1C1C1F;
                border-top: 1px solid #27272A;
            }
        """)

        # Input container layout with padding
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(24, 16, 24, 16)  # Add padding
        input_layout.setSpacing(16)  # Space between input and button

        # Input field and send button
        self.input_field = StyledInputField()
        self.send_button = StyledSendButton()
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)

        layout.addWidget(input_container)

        # Connect signals
        self.send_button.clicked.connect(self.send_message)
        self.input_field.textChanged.connect(self.update_send_button_state)

    def update_send_button_state(self):
        self.send_button.setEnabled(bool(self.input_field.toPlainText().strip()))

    def load_chat_history(self):
        for conversation in self.history_manager.load_history():
            self.chat_area.append_message(
                is_assistant=False,
                message=conversation['message'],
                timestamp=conversation['timestamp']
            )
            self.chat_area.append_message(
                is_assistant=True,
                message=conversation['response'],
                timestamp=conversation['timestamp']
            )
        self.chat_area.scroll_to_bottom()
