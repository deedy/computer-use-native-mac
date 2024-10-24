import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import rumps
from dotenv import load_dotenv
from .windows.chat_window import ChatWindow
from .services.api_client import AnthropicClient
from .services.history_manager import HistoryManager

HISTORY_FILE = '~/Library/Application Support/MacAssistant/history.json'
ICON_PATH = "icon.png"

class MenuBarApp(rumps.App):
    def __init__(self):
        super().__init__("Assistant", icon=ICON_PATH)

        load_dotenv()

        # Initialize services
        self.history_manager = HistoryManager(HISTORY_FILE)
        self.api_client = AnthropicClient(os.getenv('ANTHROPIC_API_KEY'))

        # Initialize Qt application
        self.qt_app = QApplication(sys.argv)
        self.chat_window = ChatWindow(self.history_manager, self.api_client)

        # Show window immediately
        self.chat_window.show()
        self.chat_window.raise_()
        self.chat_window.activateWindow()

        # Menu items
        self.menu = [
            rumps.MenuItem("Show Window", callback=self.show_window),
            rumps.MenuItem("Clear History", callback=self.clear_history),
        ]

    def run(self):
        # Process Qt events while running rumps
        timer = QTimer()
        timer.timeout.connect(self.process_qt_events)
        timer.start(100)  # Check every 100ms

        super().run()

    def process_qt_events(self):
        self.qt_app.processEvents()

    def show_window(self, _):
        self.chat_window.show()
        self.chat_window.raise_()
        self.chat_window.activateWindow()

    def clear_history(self, _):
        self.history_manager.clear_history()
        if self.chat_window.isVisible():
            self.chat_window.load_chat_history()

    def quit_app(self, _):
        self.qt_app.quit()
        rumps.quit_application()

def main():
    app = MenuBarApp()
    app.run()

if __name__ == "__main__":
    main()
