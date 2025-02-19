#_________________________#
#   Created By Seuriin    #
#   DB Logic by AlT4lR    #
#_________________________#
import os
import sys
import json
import uuid
import asyncio
import sqlite3
import markdown
import configparser
from characterai import aiocai
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QPixmap, QColor, QPainter, QFont
from qasync import QEventLoop, QApplication, asyncClose, asyncSlot
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QWidget, QHBoxLayout, QLabel, QVBoxLayout, QSizePolicy
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyCharacterAI import Client as PyClient
from PyQt5.QtCore import QUrl

CONFIG_FILE = 'config.ini'
DB_FILE = 'chat_sessions.db'
# I'm pretty sure you know how to get these values :)
DEFAULT_CHAR_ID = "YOUR_CHAR_ID" 
DEFAULT_TOKEN = 'YOUR_CAI_TOKEN'
CHAT_HISTORY_FILE = 'chat_history.json'
VOICES_FOLDER = "voices"
VOICE_NAME = "girl"  # AUTO SEARCHES VOICE NAMES --> REPLACE IT IF YOU WANT
DARK_MODE = False


def load_config():
    """Loads config.ini or sets defaults."""
    config = configparser.ConfigParser()
    config['DEFAULT'] = {'token': DEFAULT_TOKEN, 'char_id': DEFAULT_CHAR_ID}
    config.read(CONFIG_FILE)
    return config


def save_config(config):
    """Saves config to config.ini."""
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


config = load_config()
TOKEN = config['DEFAULT']['token']
CHAR_ID = config['DEFAULT']['char_id']
characterai_client = aiocai.Client(TOKEN)
py_client = PyClient()
if not os.path.exists(VOICES_FOLDER):
    os.makedirs(VOICES_FOLDER)


def initialize_db():
    """Initializes the SQLite database for chat sessions."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS chat_sessions (user_id INTEGER PRIMARY KEY, chat_id TEXT)")
    conn.commit()
    conn.close()


async def save_chat_session(user_id, chat_id):
    """Saves or updates a chat session ID in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO chat_sessions (user_id, chat_id) VALUES (?, ?)", (user_id, chat_id))
    conn.commit()
    conn.close()


async def get_chat_session(user_id):
    """Retrieves a chat session ID from the database for a given user."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT chat_id FROM chat_sessions WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def load_chat_history():
    """Loads chat history from a JSON file."""
    try:
        with open(CHAT_HISTORY_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_chat_history(history):
    """Saves chat history to a JSON file."""
    with open(CHAT_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)


async def generate_speech(chat_id, turn_key, candidate_id):
    """Generates speech from the AI response using PyCharacterAI. Ts so hard! PyQt5's loop is brainwracking, bruh."""
    try:
        voices = await py_client.utils.search_voices(VOICE_NAME)
        if not voices:
            print("No voices found.")
            return None
        voice_id = voices[0].voice_id
        turn_id = turn_key.turn_id
        speech = await py_client.utils.generate_speech(chat_id, turn_id, candidate_id, voice_id)
        filepath = os.path.join(VOICES_FOLDER, f"{uuid.uuid4()}.mp3")
        with open(filepath, 'wb') as f:
            f.write(speech)
        return filepath
    except Exception as e:
        print(f"Speech generation error: {e}")
        return None


class ChatBotUI(QtWidgets.QWidget):
    """<-- Main UI class for the ChatBot -->"""

    def __init__(self, event_loop, dark_mode):
        super().__init__()
        self.event_loop = event_loop
        self.dark_mode = dark_mode
        self.setWindowTitle("Chat with AI")
        self.setGeometry(100, 100, 500, 700)
        self.media_player = QMediaPlayer()
        self.user_id = 1
        self.chat_history = load_chat_history()

        self.setStyleSheet(self.get_stylesheet())
        self.init_ui()
        self.event_loop.create_task(self.authenticate_py_client())

    def get_stylesheet(self):
        """Returns stylesheet based on dark mode setting."""
        if self.dark_mode:
            return """
                background-color: #282c34;
                color: #abb2bf;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            """
        else:
            return """
                background-color: #f5f6fa;
                color: black;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            """

    def init_ui(self):
        """Initializes the UI elements and layout."""
        self.layout = QtWidgets.QVBoxLayout(self)
        self.chat_display = QtWidgets.QScrollArea(self)
        self.chat_area = QtWidgets.QWidget()
        self.chat_layout = QtWidgets.QVBoxLayout(self.chat_area)
        self.chat_layout.setAlignment(QtCore.Qt.AlignTop)
        self.chat_area.setStyleSheet(self.get_chat_area_style())
        self.chat_display.setWidget(self.chat_area)
        self.chat_display.setWidgetResizable(True)

        self.input_area = QWidget()
        self.input_area_layout = QVBoxLayout()
        self.generating_label = QtWidgets.QLabel("Generating...", self)
        self.generating_label.setAlignment(QtCore.Qt.AlignCenter)
        self.generating_label.hide()

        self.input_layout = QHBoxLayout()
        self.message_input = QtWidgets.QLineEdit(self)
        self.message_input.setPlaceholderText("Type your message...")
        self.message_input.returnPressed.connect(self.send_message)

        self.send_button = QtWidgets.QPushButton("Send", self)
        self.send_button.clicked.connect(self.send_message)
        self.voice_toggle = QtWidgets.QCheckBox("Voice Output", self)

        self.set_input_style()
        self.input_layout.addWidget(self.message_input)
        self.input_layout.addWidget(self.send_button)
        self.input_area_layout.addWidget(self.generating_label)
        self.input_area_layout.addLayout(self.input_layout)
        self.input_area_layout.addWidget(self.voice_toggle)
        self.input_area.setLayout(self.input_area_layout)

        self.layout.addWidget(self.chat_display)
        self.layout.addWidget(self.input_area)

        for message in self.chat_history:
            self.add_message_to_chat(
                message['message'], message['sender'], initial_load=True)

        QtCore.QTimer.singleShot(0, self.scroll_to_bottom)

    def get_chat_area_style(self):
        if self.dark_mode:
            return "background-color: #3e4451; border-radius: 10px; padding: 10px; color: #abb2bf;"
        else:
            return "background-color: #ffffff; border-radius: 10px; padding: 10px;"

    def set_input_style(self):
        """Dark mode"""
        if self.dark_mode:
            self.message_input.setStyleSheet("""border: 1px solid #5c6370; border-radius: 25px; padding: 10px 20px;
                                                 background-color: #3e4451; color: #abb2bf; font-size: 14px;""")
            self.send_button.setStyleSheet("""background-color: #61afef; color: white; border-radius: 25px;
                                                padding: 10px 20px; font-size: 14px; border: none;""")
            self.voice_toggle.setStyleSheet("color: #abb2bf;")
        else:
            self.message_input.setStyleSheet("""border: 1px solid #ddd; border-radius: 25px; padding: 10px 20px;
                                                 background-color: #f0f0f5; font-size: 14px;""")
            self.send_button.setStyleSheet("""background-color: #4CAF50; color: white; border-radius: 25px;
                                                padding: 10px 20px; font-size: 14px; border: none;""")

    async def authenticate_py_client(self):
        """Authenticates the PyCharacterAI client."""
        try:
            await py_client.authenticate(TOKEN)
            print("PyCharacterAI Authentication Successful!")
        except Exception as e:
            print(f"PyCharacterAI Authentication Failed: {e}")

    async def handle_characterai_command(self, message, user_id):
        """Handles sending messages to Character AI and retrieving responses."""
        try:
            chat_id = await get_chat_session(user_id)
            if not chat_id:
                chat = await characterai_client.connect()
                new_chat, _ = await chat.new_chat(CHAR_ID, (await characterai_client.get_me()).id)
                chat_id = new_chat.chat_id
                await save_chat_session(user_id, chat_id)
            chat = await characterai_client.connect()
            response = await chat.send_message(CHAR_ID, chat_id, message)
            candidate_id = response.candidates[0].candidate_id if response.candidates else None
            turn_key = response.turn_key
            return response.text, candidate_id, turn_key, chat_id
        except Exception as e:
            print(f"Content generation error: {e}")
            return f"Error: {e}", None, None, None

    def add_message_to_chat(self, message, sender, initial_load=False):
        """Adds a message bubble to the chat display."""
        message_html = markdown.markdown(message)
        message_label = QtWidgets.QLabel(message_html)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(
            QtCore.Qt.TextSelectableByMouse | QtCore.Qt.TextSelectableByKeyboard)
        message_label.setOpenExternalLinks(True)
        message_label.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)

        message_bubble = QtWidgets.QWidget()
        bubble_effect = QGraphicsDropShadowEffect()
        bubble_effect.setBlurRadius(15)
        bubble_effect.setOffset(3, 3)
        bubble_effect.setColor(QColor(0, 0, 0, 80))
        message_bubble.setGraphicsEffect(bubble_effect)

        if sender == "user":
            bubble_style = "background-color: #0084FF; color: white; border-radius: 20px;"
        else:
            if self.dark_mode:
                bubble_style = "background-color: #5c6370; color: #d2daeb; border-radius: 20px;"
            else:
                bubble_style = "background-color: #E4E6EB; color: black; border-radius: 20px;"

        message_bubble.setStyleSheet(bubble_style)

        profile_pic_size = 48
        profile_pic_widget = RoundedProfilePicture(profile_pic_size)
        profile_pic_path = "user.jpg" if sender == "user" else "ai.jpg"
        profile_pic_widget.set_profile_picture(profile_pic_path)

        message_container = QtWidgets.QWidget()
        container_layout = QtWidgets.QVBoxLayout(message_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        sender_name_label = QLabel(
            "You" if sender == "user" else "AI", self)  # Rename "You", okay?
        sender_name_label.setFont(QFont("Segoe UI", 8))

        if self.dark_mode:
            sender_name_label.setStyleSheet("color: #abb2bf;")
        else:
            sender_name_label.setStyleSheet("color: gray;")

        sender_name_label.setAlignment(
            QtCore.Qt.AlignRight if sender == "user" else QtCore.Qt.AlignLeft)
        container_layout.addWidget(sender_name_label)

        horizontal_layout = QtWidgets.QHBoxLayout()
        horizontal_layout.setContentsMargins(0, 0, 0, 0)
        horizontal_layout.setSpacing(10)
        pic_alignment = QtCore.Qt.AlignTop

        if sender == "user":
            horizontal_layout.addStretch(1)
            horizontal_layout.addWidget(message_bubble)
            horizontal_layout.addWidget(
                profile_pic_widget, alignment=pic_alignment)
            horizontal_layout.setAlignment(QtCore.Qt.AlignRight)
        else:
            horizontal_layout.addWidget(
                profile_pic_widget, alignment=pic_alignment)
            horizontal_layout.addWidget(message_bubble)
            horizontal_layout.addStretch(1)
            horizontal_layout.setAlignment(QtCore.Qt.AlignLeft)

        message_layout = QtWidgets.QHBoxLayout(message_bubble)
        message_layout.setContentsMargins(10, 10, 10, 10)
        message_layout.addWidget(message_label)

        if sender == "user":
            message_layout.setAlignment(QtCore.Qt.AlignRight)
        else:
            message_layout.setAlignment(QtCore.Qt.AlignLeft)

        container_layout.addLayout(horizontal_layout)
        container_layout.addSpacing(9)

        padding_widget = QWidget()
        padding_widget.setFixedHeight(5)
        self.chat_layout.addWidget(message_container)
        self.chat_layout.addWidget(padding_widget)

    @asyncSlot()
    async def send_message(self):
        """Sends the user message and displays the AI's response."""
        message = self.message_input.text().strip()
        if message:
            self.add_message_to_chat(message, "user")
            self.chat_history.append({'message': message, 'sender': 'user'})
            save_chat_history(self.chat_history)
            self.message_input.clear()
            self.generating_label.show()
            response, candidate_id, turn_key, chat_id = await self.handle_characterai_command(message, self.user_id)
            self.add_ai_response(response, candidate_id, turn_key, chat_id)

    def add_ai_response(self, response, candidate_id, turn_key, chat_id):
        """Adds the AI's response to the chat and handles voice playback."""
        self.generating_label.hide()
        self.add_message_to_chat(response, "ai")
        self.chat_history.append({'message': response, 'sender': 'ai'})
        save_chat_history(self.chat_history)
        if self.voice_toggle.isChecked():
            if candidate_id and turn_key and chat_id:
                self.event_loop.create_task(
                    self.play_ai_voice(chat_id, turn_key, candidate_id))
            else:
                print("Missing info. No voice.")

    async def play_ai_voice(self, chat_id, turn_key, candidate_id):
        """Plays the AI's voice response."""
        voice_file = await generate_speech(chat_id, turn_key, candidate_id)
        if voice_file:
            try:
                file_path = os.path.abspath(voice_file)
                media_content = QMediaContent(QUrl.fromLocalFile(file_path))
                self.media_player.setMedia(media_content)
                self.media_player.play()
            except Exception as e:
                print(f"Voice playback error: {e}")

    @asyncClose
    async def closeEvent(self, event):
        print("Closing application")

    def scroll_to_bottom(self):
        """Latest message view at start-up"""
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum())


class RoundedProfilePicture(QWidget):
    """Literally :P"""

    def __init__(self, size):
        super().__init__()
        self.size = size
        self.setFixedSize(size, size)
        self.profile_pic = None

    def set_profile_picture(self, image_path):
        self.profile_pic = image_path
        self.update()

    def paintEvent(self, event):
        if not self.profile_pic:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        round_rect = QtCore.QRectF(0, 0, self.size, self.size)
        path = QtGui.QPainterPath()
        path.addRoundedRect(round_rect, self.size / 2, self.size / 2)
        pixmap = QPixmap(self.profile_pic)
        pixmap = pixmap.scaled(
            self.size, self.size, QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)


def main():
    """<-- Main function of the app -->"""
    global DARK_MODE
    if len(sys.argv) > 1 and sys.argv[1] == "--dark":
        DARK_MODE = True
    initialize_db()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)
    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)
    window = ChatBotUI(event_loop, DARK_MODE)
    window.show()
    with event_loop:
        event_loop.run_until_complete(app_close_event.wait())


if __name__ == "__main__":
    main()
