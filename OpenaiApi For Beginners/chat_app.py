import sys
import os
import json
import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QScrollArea, QFrame,
    QFileDialog, QMessageBox, QComboBox, QInputDialog,
    QToolBar, QSizePolicy, QDockWidget, QColorDialog, QDialog,
    QTabWidget, QLineEdit
)
from PyQt6.QtGui import (
    QPixmap, QFont, QColor, QPalette, QIcon, QAction, QDragEnterEvent, QDropEvent         
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QSize, QEvent
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import openai
from dotenv import load_dotenv, set_key
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Constants for paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(CURRENT_DIR, "icons")  # Assuming icons are in 'icons' folder
LOG_FILE = os.path.join(CURRENT_DIR, "app_debug_log.txt")
ICON_SEND = os.path.join(ICONS_DIR, "send_icon.png")
ICON_ATTACH = os.path.join(ICONS_DIR, "attach_icon.png")
ICON_THEME = os.path.join(ICONS_DIR, "theme_icon.png")
USER_AVATAR = os.path.join(ICONS_DIR, "user_avatar.png")
AI_AVATAR = os.path.join(ICONS_DIR, "ai_avatar.png")
DEFAULT_AVATAR = os.path.join(ICONS_DIR, "default_avatar.png")

# Icons for style toolbar
STYLE1_ICON = os.path.join(ICONS_DIR, "style1_icon.png")
STYLE2_ICON = os.path.join(ICONS_DIR, "style2_icon.png")
STYLE3_ICON = os.path.join(ICONS_DIR, "style3_icon.png")
STYLE4_ICON = os.path.join(ICONS_DIR, "style4_icon.png")

# Icons for resize toolbar
RESIZE_IN_ICON = os.path.join(ICONS_DIR, "resize_in_icon.png")
RESIZE_OUT_ICON = os.path.join(ICONS_DIR, "resize_out_icon.png")

TOKEN_FILE = os.path.join(CURRENT_DIR, "tokens.json")  # File to save tokens
CONFIG_FILE = os.path.join(CURRENT_DIR, "config.json")  # Config file

# -------------------------------------------------
# --- GLOBAL LOGGING FUNCTION --------------------
# -------------------------------------------------

# Configure logging
if os.path.exists(LOG_FILE):
    logging.shutdown()
    os.remove(LOG_FILE)
    print("Stary plik logów został usunięty.")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)
logging.debug("Plik logów został utworzony.")

# -------------------------------------------------
# --- LOGGING DECORATOR FUNCTION -------------------
# -------------------------------------------------

def log_function(func):
    def wrapper(*args, **kwargs):
        # Sprawdź, czy pierwszy argument to instancja klasy (self)
        if len(args) > 0 and hasattr(args[0], '__class__'):
            # Zakładamy, że jest to metoda klasy
            self = args[0]
            logging.debug(f"Wywołano metodę: {func.__name__} z argumentami: {args[1:]} {kwargs}")
        else:
            # Zakładamy, że jest to funkcja niezależna
            logging.debug(f"Wywołano funkcję: {func.__name__} z argumentami: {args} {kwargs}")
        try:
            result = func(*args, **kwargs)
            logging.debug(f"Zakończono funkcję/metodę: {func.__name__} z wynikiem: {result}")
            return result
        except Exception as e:
            logging.error(f"Błąd w funkcji/metodzie: {func.__name__} - {e}")
            raise e
    return wrapper

# -------------------------------------------------
# --- LOAD OPENAI API KEY -------------------------
# -------------------------------------------------

load_dotenv()

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')

if not openai.api_key:
    logging.warning("Klucz API OpenAI nie został znaleziony w pliku .env.")
    # Użyj QApplication do pokazania QMessageBox tylko jeśli aplikacja jest już uruchomiona
    app_instance = QApplication.instance()
    if app_instance:
        QMessageBox.warning(None, "Brak klucza API", "Klucz API OpenAI nie został ustawiony w pliku .env. Niektóre funkcje mogą być niedostępne.")

# Podobnie dla innych zmiennych środowiskowych:
SMTP_SENDER_EMAIL = os.getenv("SMTP_SENDER_EMAIL", "default_sender@example.com")
SMTP_RECEIVER_EMAIL = os.getenv("SMTP_RECEIVER_EMAIL", "default_receiver@example.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
TRELLO_API_KEY = os.getenv("TRELLO_API_KEY", "")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN", "")
TRELLO_BOARD_ID = os.getenv("TRELLO_BOARD_ID", "")
TRELLO_LIST_ID = os.getenv("TRELLO_LIST_ID", "")
EXPORT_DEFAULT_PATH = os.getenv("EXPORT_DEFAULT_PATH", os.getcwd())  # Domyślna ścieżka eksportu to bieżący katalog
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "")
GOOGLE_SHEETS_NAME = os.getenv("GOOGLE_SHEETS_NAME", "Default Sheet Name")

# -------------------------------------------------
# --- LOAD MODELS ---------------------------------
# -------------------------------------------------

MODELS_FILE = "models.json"

@log_function
def load_models():
    if not os.path.exists(MODELS_FILE):
        default_models = {
            "models": [
                {
                    "name": "gpt-4",
                    "description": "High-intelligence flagship model for complex, multi-step tasks."
                },
                {
                    "name": "gpt-4-mini",
                    "description": "Affordable and intelligent small model for fast, lightweight tasks."
                },
                {
                    "name": "gpt-4-turbo",
                    "description": "Latest GPT-4 Turbo model with vision capabilities."
                },
                {
                    "name": "gpt-3.5-turbo",
                    "description": "Fast, inexpensive model for simple tasks."
                }
            ]
        }
        with open(MODELS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_models, f, ensure_ascii=False, indent=4)
        return default_models["models"]
    else:
        with open(MODELS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("models", [])

# -------------------------------------------------
# --- SAVE MODELS FUNCTION ------------------------
# -------------------------------------------------

@log_function
def save_models(models):
    with open(MODELS_FILE, "w", encoding="utf-8") as f:
        json.dump({"models": models}, f, ensure_ascii=False, indent=4)

# -------------------------------------------------
# --- QTextEditLogger CLASS -----------------------
# -------------------------------------------------

class QTextEditLogger(logging.Handler):
    def __init__(self, parent=None):
        super().__init__()
        self.widget = parent

    def emit(self, record):
        msg = self.format(record)
        self.widget.append(msg)

# -------------------------------------------------
# --- OPENAI THREAD CLASS --------------------------
# -------------------------------------------------

from openai import APIError, RateLimitError, AuthenticationError, APIConnectionError

class OpenAIThread(QThread):
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    tokens_used = pyqtSignal(int, int)  # Signal for token usage

    @log_function
    def __init__(self, conversation, model, retry=3):
        super().__init__()
        self.conversation = conversation
        self.model = model
        self.retry = retry  # Number of retries on error

    @log_function
    def run(self):
        attempts = 0
        while attempts < self.retry:
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=self.conversation,
                    temperature=0.7,
                    max_tokens=150,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0.6,
                    stop=["\n", " User:", " AI:"],
                )
                ai_message = response.choices[0].message.content.strip()
                total_tokens = response.usage.total_tokens
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                self.tokens_used.emit(prompt_tokens, completion_tokens)
                self.response_received.emit(ai_message)
                break  # If success, break the loop
            except RateLimitError:
                attempts += 1
                logging.warning(f"RateLimitError: Próba {attempts} z {self.retry}")
                if attempts >= self.retry:
                    error_message = "Przekroczono limit zapytań. Spróbuj ponownie później."
                    self.error_occurred.emit(error_message)
            except AuthenticationError:
                error_message = "Błąd uwierzytelniania API. Sprawdź swój klucz API."
                self.error_occurred.emit(error_message)
                break
            except APIConnectionError:
                attempts += 1
                logging.warning(f"APIConnectionError: Próba {attempts} z {self.retry}")
                if attempts >= self.retry:
                    error_message = "Problem z połączeniem z API. Spróbuj ponownie później."
                    self.error_occurred.emit(error_message)
            except APIError as e:
                error_message = f"Wystąpił błąd API: {e}"
                self.error_occurred.emit(error_message)
                logging.error(f"Błąd API: {e}")
                break
            except Exception as e:
                error_message = "Wystąpił nieoczekiwany błąd."
                self.error_occurred.emit(error_message)
                logging.error(f"Nieoczekiwany błąd: {e}")
                break

# -------------------------------------------------
# --- TokenPlot CLASS ------------------------------
# -------------------------------------------------

class TokenPlot(FigureCanvas):
    def __init__(self, history=None, parent=None):
        import matplotlib
        matplotlib.use('QtAgg')  # Set backend to QtAgg
        fig = Figure(figsize=(6, 3), dpi=100)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)
        self.history = history if history else []
        self.plot_initial()

    def plot_initial(self):
        self.axes.clear()
        self.axes.set_title("Użycie Tokenów")
        self.axes.set_xlabel("Wiadomości")
        self.axes.set_ylabel("Tokeny")
        self.axes.set_ylim(0, 10000)
        self.axes.grid(True)
        self.draw()

    @log_function
    def update_plot(self, history):
        self.history = history
        self.axes.clear()
        self.axes.set_title("Użycie Tokenów")
        self.axes.set_xlabel("Wiadomości")
        self.axes.set_ylabel("Tokeny")
        self.axes.set_ylim(0, max(10000, max(self.history, default=10000) + 1000))
        self.axes.plot(range(1, len(self.history)+1), self.history, marker='o', linestyle='-')
        self.axes.grid(True)
        self.draw()

# -------------------------------------------------
# --- PythonQuizDialog CLASS -----------------------
# -------------------------------------------------

class PythonQuizDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Python Quiz")
        self.setGeometry(150, 150, 400, 300)
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.question_label = QLabel("Pytanie pojawi się tutaj.")
        self.layout.addWidget(self.question_label)
        
        self.answer_input = QTextEdit()
        self.answer_input.setFixedHeight(50)
        self.layout.addWidget(self.answer_input)
        
        self.submit_button = QPushButton("Zatwierdź Odpowiedź")
        self.submit_button.clicked.connect(self.submit_answer)
        self.layout.addWidget(self.submit_button)
        
        self.next_button = QPushButton("Następne Pytanie")
        self.next_button.clicked.connect(self.next_question)
        self.next_button.setEnabled(False)
        self.layout.addWidget(self.next_button)
        
        self.score_label = QLabel("Wynik: 0")
        self.layout.addWidget(self.score_label)
        
        self.score = 0
        self.current_question = None
        
        self.get_new_question()
    
    def get_new_question(self):
        # Wysyłanie zapytania do AI o nowe pytanie
        prompt = "Zadaj mi pytanie z zakresu Pythona na poziomie średnio zaawansowanym."
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=150,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0.6,
            )
            self.current_question = response.choices[0].message.content.strip()
            self.question_label.setText(self.current_question)
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się pobrać pytania: {e}")
    
    def submit_answer(self):
        user_answer = self.answer_input.toPlainText().strip()
        if not user_answer:
            QMessageBox.warning(self, "Uwaga", "Proszę wpisać odpowiedź.")
            return
        
        # Ocena odpowiedzi przez AI
        prompt = f"Oceniam odpowiedź użytkownika na poniższe pytanie z Pythona.\n\nPytanie: {self.current_question}\nOdpowiedź: {user_answer}\n\nCzy odpowiedź jest poprawna? Jeśli tak, wyjaśnij dlaczego. Jeśli nie, popraw odpowiedź."
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=200,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )
            evaluation = response.choices[0].message.content.strip()
            QMessageBox.information(self, "Ocena Odpowiedzi", evaluation)
            
            if "nie" not in evaluation.lower() and "zła" not in evaluation.lower():
                self.score += 1
                self.score_label.setText(f"Wynik: {self.score}")
            
            self.submit_button.setEnabled(False)
            self.next_button.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się ocenić odpowiedzi: {e}")
    
    def next_question(self):
        self.answer_input.clear()
        self.submit_button.setEnabled(True)
        self.next_button.setEnabled(False)
        self.get_new_question()

# -------------------------------------------------
# --- ConversationHistoryDialog CLASS --------------
# -------------------------------------------------

class ConversationHistoryDialog(QDialog):
    def __init__(self, conversation, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historia Rozmów")
        self.setGeometry(250, 250, 600, 500)
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Wyszukiwanie
        search_layout = QHBoxLayout()
        self.search_label = QLabel("Szukaj:")
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_conversations)
        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_input)
        self.layout.addLayout(search_layout)
        
        # Lista rozmów
        self.conversations_display = QTextEdit()
        self.conversations_display.setReadOnly(True)
        self.layout.addWidget(self.conversations_display)
        
        # Przyciski
        buttons_layout = QHBoxLayout()
        self.close_button = QPushButton("Zamknij")
        self.close_button.clicked.connect(self.accept)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_button)
        self.layout.addLayout(buttons_layout)
        
        self.all_conversations = conversation
        self.display_conversations(conversation)
    
    def display_conversations(self, conversations):
        self.conversations_display.clear()
        for msg in conversations:
            role = msg['role'].capitalize()
            content = msg['content']
            timestamp = msg['timestamp']
            self.conversations_display.append(f"[{timestamp}] {role}: {content}\n")
    
    def filter_conversations(self, text):
        if not text:
            self.display_conversations(self.all_conversations)
            return
        
        filtered = [msg for msg in self.all_conversations if text.lower() in msg['content'].lower()]
        self.display_conversations(filtered)

# -------------------------------------------------
# --- SettingsDialog CLASS -------------------------
# -------------------------------------------------

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ustawienia")
        self.setGeometry(200, 200, 500, 400)
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Zakładka API
        self.api_tab = QWidget()
        self.tabs.addTab(self.api_tab, "API")
        self.api_layout = QVBoxLayout()
        self.api_tab.setLayout(self.api_layout)
        
        self.api_key_label = QLabel("OpenAI API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setText(os.getenv("OPENAI_API_KEY", ""))
        self.api_layout.addWidget(self.api_key_label)
        self.api_layout.addWidget(self.api_key_input)
        
        # Zakładka Integracje
        self.integrations_tab = QWidget()
        self.tabs.addTab(self.integrations_tab, "Integracje")
        self.integrations_layout = QVBoxLayout()
        self.integrations_tab.setLayout(self.integrations_layout)
        
        # Przykład: Integracja z Trello
        self.trello_api_label = QLabel("Trello API Key:")
        self.trello_api_input = QLineEdit()
        self.trello_api_input.setText(os.getenv("TRELLO_API_KEY", ""))
        
        self.trello_token_label = QLabel("Trello Token:")
        self.trello_token_input = QLineEdit()
        self.trello_token_input.setText(os.getenv("TRELLO_TOKEN", ""))
        
        self.trello_board_label = QLabel("Trello Board ID:")
        self.trello_board_input = QLineEdit()
        self.trello_board_input.setText(os.getenv("TRELLO_BOARD_ID", ""))
        
        self.trello_list_label = QLabel("Trello List ID:")
        self.trello_list_input = QLineEdit()
        self.trello_list_input.setText(os.getenv("TRELLO_LIST_ID", ""))
        
        self.integrations_layout.addWidget(self.trello_api_label)
        self.integrations_layout.addWidget(self.trello_api_input)
        self.integrations_layout.addWidget(self.trello_token_label)
        self.integrations_layout.addWidget(self.trello_token_input)
        self.integrations_layout.addWidget(self.trello_board_label)
        self.integrations_layout.addWidget(self.trello_board_input)
        self.integrations_layout.addWidget(self.trello_list_label)
        self.integrations_layout.addWidget(self.trello_list_input)
        
        # Zakładka Motywy
        self.themes_tab = QWidget()
        self.tabs.addTab(self.themes_tab, "Motywy")
        self.themes_layout = QVBoxLayout()
        self.themes_tab.setLayout(self.themes_layout)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Jasny", "Ciemny", "Styl 1", "Styl 2", "Styl 3", "Styl 4"])
        current_theme = self.get_current_theme()
        self.theme_combo.setCurrentText(current_theme)
        self.themes_layout.addWidget(QLabel("Wybierz Motyw:"))
        self.themes_layout.addWidget(self.theme_combo)
        
        # Zakładka Eksport
        self.export_tab = QWidget()
        self.tabs.addTab(self.export_tab, "Eksport")
        self.export_layout = QVBoxLayout()
        self.export_tab.setLayout(self.export_layout)
        
        self.export_default_path_label = QLabel("Domyślna ścieżka eksportu:")
        self.export_default_path_input = QLineEdit()
        self.export_default_path_input.setText(os.getenv("EXPORT_DEFAULT_PATH", ""))
        self.export_layout.addWidget(self.export_default_path_label)
        self.export_layout.addWidget(self.export_default_path_input)
        
        # Zakładka Logowanie
        self.logging_tab = QWidget()
        self.tabs.addTab(self.logging_tab, "Logowanie")
        self.logging_layout = QVBoxLayout()
        self.logging_tab.setLayout(self.logging_layout)
        
        self.enable_logging_checkbox = QCheckBox("Włącz logowanie")
        self.enable_logging_checkbox.setChecked(True if os.path.exists(LOG_FILE) else False)
        self.logging_layout.addWidget(self.enable_logging_checkbox)
        
        # Przyciski Save i Cancel
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Zapisz")
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        self.layout.addLayout(buttons_layout)
    
    def get_current_theme(self):
        # Logika do pobrania aktualnego motywu, np. z pliku konfiguracyjnego
        # Na przykład:
        config = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except json.JSONDecodeError:
                logging.warning("Plik config.json jest uszkodzony! Resetowanie konfiguracji.")
        style_number = config.get("style", 1)
        theme_map = {
            0: "Ciemny",
            1: "Jasny",
            2: "Styl 1",
            3: "Styl 2",
            4: "Styl 3",
            5: "Styl 4"
        }
        return theme_map.get(style_number, "Jasny")
    
    @log_function
    def save_settings(self):
        # Zapisz ustawienia do pliku .env lub innego źródła
        api_key = self.api_key_input.text().strip()
        trello_key = self.trello_api_input.text().strip()
        trello_token = self.trello_token_input.text().strip()
        trello_board = self.trello_board_input.text().strip()
        trello_list = self.trello_list_input.text().strip()
        
        # Motyw
        selected_theme = self.theme_combo.currentText()
        style_number = 1  # Default to light
        theme_map_reverse = {
            "Ciemny": 0,
            "Jasny": 1,
            "Styl 1": 2,
            "Styl 2": 3,
            "Styl 3": 4,
            "Styl 4": 5
        }
        style_number = theme_map_reverse.get(selected_theme, 1)
        
        # Eksport
        export_path = self.export_default_path_input.text().strip()
        
        # Aktualizacja pliku .env
        dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        if os.path.exists(dotenv_path):
            set_key(dotenv_path, "OPENAI_API_KEY", api_key)
            set_key(dotenv_path, "TRELLO_API_KEY", trello_key)
            set_key(dotenv_path, "TRELLO_TOKEN", trello_token)
            set_key(dotenv_path, "TRELLO_BOARD_ID", trello_board)
            set_key(dotenv_path, "TRELLO_LIST_ID", trello_list)
            set_key(dotenv_path, "EXPORT_DEFAULT_PATH", export_path)
        else:
            # Jeśli plik .env nie istnieje, stwórz go
            with open(dotenv_path, "w", encoding="utf-8") as f:
                f.write(f"OPENAI_API_KEY={api_key}\n")
                f.write(f"TRELLO_API_KEY={trello_key}\n")
                f.write(f"TRELLO_TOKEN={trello_token}\n")
                f.write(f"TRELLO_BOARD_ID={trello_board}\n")
                f.write(f"TRELLO_LIST_ID={trello_list}\n")
                f.write(f"EXPORT_DEFAULT_PATH={export_path}\n")
        
        # Zapisz wybrany motyw do config.json
        self.parent().save_style_to_config(style_number)
        
        # Logowanie
        if self.enable_logging_checkbox.isChecked():
            if not os.path.exists(LOG_FILE):
                open(LOG_FILE, 'w').close()
            logging.getLogger().addHandler(QTextEditLogger(self.parent().log_widget))
            logging.info("Logowanie włączone.")
        else:
            # Usuń handler logowania
            handlers = logging.getLogger().handlers[:]
            for handler in handlers:
                if isinstance(handler, QTextEditLogger):
                    logging.getLogger().removeHandler(handler)
            logging.info("Logowanie wyłączone.")
        
        QMessageBox.information(self, "Sukces", "Ustawienia zostały zapisane.")
        self.accept()

# -------------------------------------------------
# --- ChatApp CLASS --------------------------------
# -------------------------------------------------

class ChatApp(QMainWindow):

    @log_function
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat z OpenAI")
        self.setGeometry(100, 100, 1000, 800)  # Increased window size
        self.conversation = []
        self.models = load_models()
        self.total_tokens = 10000  # Example total tokens
        self.used_tokens = 0
        self.token_history = []  # Token usage history

        self.load_icons()      # First, load icons
        self.init_ui()         # Then initialize UI
        self.load_conversation()
        self.load_tokens()
        self.setWindowIcon(QIcon(ICON_SEND))  # Assuming ICON_SEND is the main icon
        print("Funkcja load_icons została wywołana!")

        # Enable drag and drop
        self.setAcceptDrops(True)

    # -------------------------------------------------
    # --- LOAD ICONS FUNCTION ------------------------
    # -------------------------------------------------

    def load_icons(self):
        try:
            # Initialize icons dictionary
            self.icons = {}
            icon_files = {
                "send": ICON_SEND,
                "attach": ICON_ATTACH,
                "theme": ICON_THEME,
                "style1": STYLE1_ICON,
                "style2": STYLE2_ICON,
                "style3": STYLE3_ICON,
                "style4": STYLE4_ICON,
                "resize_in": RESIZE_IN_ICON,
                "resize_out": RESIZE_OUT_ICON,
                "user_avatar": USER_AVATAR,
                "ai_avatar": AI_AVATAR,
                "default_avatar": DEFAULT_AVATAR
            }

            for key, path in icon_files.items():
                if os.path.exists(path):
                    pixmap = QPixmap(path)
                    if pixmap.isNull():
                        logging.warning(f"Nie udało się załadować ikony {key} z pliku: {path}")
                        self.icons[key] = QIcon()  # Empty icon
                    else:
                        self.icons[key] = QIcon(pixmap)
                        logging.debug(f"Załadowano ikonę: {path}")
                else:
                    logging.warning(f"Brak pliku ikony {key}: {path}")
                    self.icons[key] = QIcon()  # Empty icon or use default
        except Exception as e:
            logging.error(f"Błąd podczas ładowania ikon: {e}")

    # -------------------------------------------------
    # --- INIT UI FUNCTION ----------------------------
    # -------------------------------------------------

    @log_function
    def init_ui(self):
        # Set main widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        central_widget.setLayout(main_layout)

        # Create toolbar
        toolbar = QToolBar("Toolbar")
        toolbar.setIconSize(QSize(24, 24))  # Set icon size in toolbar
        main_layout.addWidget(toolbar)

        # Add actions to change styles
        style1_action = QAction(QIcon(self.icons.get("style1")), "Styl 1", self)
        style1_action.setStatusTip("Zastosuj Styl 1")
        style1_action.triggered.connect(lambda checked: self.apply_custom_style(1))
        toolbar.addAction(style1_action)

        style2_action = QAction(QIcon(self.icons.get("style2")), "Styl 2", self)
        style2_action.setStatusTip("Zastosuj Styl 2")
        style2_action.triggered.connect(lambda checked: self.apply_custom_style(2))
        toolbar.addAction(style2_action)

        style3_action = QAction(QIcon(self.icons.get("style3")), "Styl 3", self)
        style3_action.setStatusTip("Zastosuj Styl 3")
        style3_action.triggered.connect(lambda checked: self.apply_custom_style(3))
        toolbar.addAction(style3_action)

        style4_action = QAction(QIcon(self.icons.get("style4")), "Styl 4", self)
        style4_action.setStatusTip("Zastosuj Styl 4")
        style4_action.triggered.connect(lambda checked: self.apply_custom_style(4))
        toolbar.addAction(style4_action)

        toolbar.addSeparator()

        # Add actions to resize text area
        resize_in_action = QAction(QIcon(self.icons.get("resize_in")), "Powiększ pole tekstowe", self)
        resize_in_action.setStatusTip("Powiększ pole tekstowe")
        resize_in_action.triggered.connect(self.increase_text_edit_size)
        toolbar.addAction(resize_in_action)

        resize_out_action = QAction(QIcon(self.icons.get("resize_out")), "Zmniejsz pole tekstowe", self)
        resize_out_action.setStatusTip("Zmniejsz pole tekstowe")
        resize_out_action.triggered.connect(self.decrease_text_edit_size)
        toolbar.addAction(resize_out_action)

        toolbar.addSeparator()

        # Add action to toggle theme
        theme_action = QAction(QIcon(self.icons.get("theme")), "Przełącz tryb", self)
        theme_action.setStatusTip("Przełącz tryb jasny/ciemny")
        theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(theme_action)

        # Add action to attach files
        attach_action = QAction(QIcon(self.icons.get("attach")), "Załącz plik", self)
        attach_action.setStatusTip("Załącz plik do rozmowy")
        attach_action.triggered.connect(self.handle_attach)
        toolbar.addAction(attach_action)

        toolbar.addSeparator()

        # Add action to open logs
        open_logs_action = QAction("Logi", self)
        open_logs_action.setStatusTip("Otwórz okno logów")
        open_logs_action.triggered.connect(self.toggle_log_view)
        toolbar.addAction(open_logs_action)

        # Add action to open settings
        settings_action = QAction("Ustawienia", self)
        settings_action.setStatusTip("Otwórz panel ustawień")
        settings_action.triggered.connect(self.open_settings_panel)
        toolbar.addAction(settings_action)

        # Add action to start Python Quiz
        quiz_action = QAction("Python Quiz", self)
        quiz_action.setStatusTip("Rozpocznij quiz z Pythonem")
        quiz_action.triggered.connect(self.start_python_quiz)
        toolbar.addAction(quiz_action)

        # Add action to open conversation history
        history_action = QAction("Historia Rozmów", self)
        history_action.setStatusTip("Przeglądaj historię rozmów")
        history_action.triggered.connect(self.open_conversation_history)
        toolbar.addAction(history_action)

        # Add main chat area with scroll
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_widget.setLayout(self.chat_layout)
        self.chat_area.setWidget(self.chat_widget)

        main_layout.addWidget(self.chat_area)

        # Add input field and send button
        input_layout = QHBoxLayout()

        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Napisz wiadomość...")
        self.input_field.setFixedHeight(40)
        self.input_field.setMaximumHeight(200)
        self.input_field.setMinimumHeight(40)
        self.input_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.input_field.textChanged.connect(self.adjust_text_edit_height)
        self.input_field.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                border: 2px solid #ccc;
                border-radius: 20px;
                font-size: 16px;
                background-color: #ffffff;
            }
            QTextEdit:focus {
                border: 2px solid #66afe9;
                outline: none;
                background-color: #f0f8ff;
            }
        """)

        # Add send button
        self.send_button = QPushButton()
        self.send_button.setIcon(QIcon(self.icons.get("send")))
        self.send_button.setToolTip("Wyślij wiadomość")
        self.send_button.clicked.connect(lambda checked: self.handle_send())
        self.send_button.setFixedSize(40, 40)  # Set button size
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)  # Add button to layout

        main_layout.addLayout(input_layout)

        # Add model dropdown
        self.model_dropdown = QComboBox()
        self.update_model_dropdown()
        self.model_dropdown.setToolTip("Wybierz model językowy")
        self.model_dropdown.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 2px solid #ccc;
                border-radius: 10px;
                font-size: 14px;
                background-color: #ffffff;
            }
            QComboBox:editable {
                background: white;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
            }
        """)
        self.model_dropdown.setMinimumWidth(250)

        # Add model dropdown to layout
        main_layout.addWidget(self.model_dropdown)

        # Add token counters
        tokens_layout = QHBoxLayout()
        self.tokens_remaining_label = QLabel(f"Pozostałe tokeny: {self.total_tokens - self.used_tokens}")
        self.tokens_total_label = QLabel(f"Całkowite tokeny: {self.total_tokens}")
        tokens_layout.addWidget(self.tokens_remaining_label)
        tokens_layout.addStretch()
        tokens_layout.addWidget(self.tokens_total_label)
        main_layout.addLayout(tokens_layout)

        # Add token usage plot
        self.token_plot = TokenPlot(self.token_history)
        main_layout.addWidget(self.token_plot)

        # Add export buttons
        export_layout = QHBoxLayout()
        self.export_pdf_button = QPushButton("Eksportuj do PDF")
        self.export_pdf_button.setToolTip("Eksportuj historię rozmów do pliku PDF")
        self.export_pdf_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: black;
                border: none;
                border-radius: 10px;
                padding: 6px 12px;
                min-width: 100px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        self.export_pdf_button.clicked.connect(lambda checked: self.export_to_pdf())

        self.export_html_button = QPushButton("Eksportuj do HTML")
        self.export_html_button.setToolTip("Eksportuj historię rozmów do pliku HTML")
        self.export_html_button.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 6px 12px;
                min-width: 100px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #117a8b;
            }
        """)
        self.export_html_button.clicked.connect(lambda checked: self.export_to_html())

        export_layout.addWidget(self.export_pdf_button)
        export_layout.addWidget(self.export_html_button)
        export_layout.addStretch()
        main_layout.addLayout(export_layout)

        # Add logs to main window (QDockWidget)
        self.log_dock = QDockWidget("Logi", self)
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_dock.setWidget(self.log_widget)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_dock)
        self.log_dock.hide()  # Hide on start

        # Add log handler to QTextEdit
        log_handler = QTextEditLogger(self.log_widget)
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(log_handler)

        # Load style from config
        self.load_style_from_config()

        # Add event filter for Enter key
        self.input_field.installEventFilter(self)

        # -------------------------------------------------
        # --- ADDITIONAL BUTTONS -------------------------
        # -------------------------------------------------

        # Button to add custom themes
        add_theme_action = QAction("Dodaj Motyw", self)
        add_theme_action.setStatusTip("Dodaj własny motyw kolorystyczny")
        add_theme_action.triggered.connect(self.add_custom_theme)
        toolbar.addAction(add_theme_action)

        # Button to add custom icons
        add_icon_action = QAction("Dodaj Ikonę", self)
        add_icon_action.setStatusTip("Dodaj własne ikony do toolbaru")
        add_icon_action.triggered.connect(self.add_custom_icon)
        toolbar.addAction(add_icon_action)

        # Add option to send conversation via email
        self.add_send_email_option()

        # Add word counter
        self.add_word_counter()

        # Add developer mode
        self.add_developer_mode()

    # -------------------------------------------------
    # --- EVENT FILTER FOR ENTER KEY -------------------
    # -------------------------------------------------

    def eventFilter(self, source, event):
        if (source is self.input_field and
            event.type() == QEvent.Type.KeyPress and
            event.key() == Qt.Key.Key_Return and
            not event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.handle_send()
            return True
        return super().eventFilter(source, event)

    # -------------------------------------------------
    # --- ADJUST TEXT EDIT HEIGHT ----------------------
    # -------------------------------------------------

    @log_function
    def adjust_text_edit_height(self):
        document = self.input_field.document()
        doc_height = document.size().height()
        new_height = max(40, min(int(doc_height + 20), 200))
        self.input_field.setFixedHeight(new_height)

    # -------------------------------------------------
    # --- INCREASE TEXT EDIT SIZE ---------------------
    # -------------------------------------------------

    @log_function
    def increase_text_edit_size(self, checked=False):
        current_height = self.input_field.height()
        new_height = min(current_height + 20, 200)
        self.input_field.setFixedHeight(new_height)

    # -------------------------------------------------
    # --- DECREASE TEXT EDIT SIZE ---------------------
    # -------------------------------------------------

    @log_function
    def decrease_text_edit_size(self, checked=False):
        current_height = self.input_field.height()
        new_height = max(current_height - 20, 40)
        self.input_field.setFixedHeight(new_height)

    # -------------------------------------------------
    # --- UPDATE MODEL DROPDOWN FUNCTION ---------------
    # -------------------------------------------------

    @log_function
    def update_model_dropdown(self):
        self.model_dropdown.clear()
        for model in self.models:
            self.model_dropdown.addItem(f"{model['name']}: {model['description']}")
        self.model_dropdown.setCurrentIndex(0)

    # -------------------------------------------------
    # --- ADD MODEL FUNCTION ---------------------------
    # -------------------------------------------------

    @log_function
    def add_model(self):
        text, ok = QInputDialog.getText(self, "Dodaj Model", "Wprowadź nazwę modelu:")
        if ok and text.strip():
            description, ok_desc = QInputDialog.getText(self, "Opis Modelu", "Wprowadź opis modelu:")
            if ok_desc and description.strip():
                existing_names = [model['name'] for model in self.models]
                if text.strip() in existing_names:
                    QMessageBox.warning(self, "Uwaga", f"Model '{text.strip()}' już istnieje.")
                    return

                new_model = {
                    "name": text.strip(),
                    "description": description.strip()
                }
                self.models.append(new_model)
                save_models(self.models)
                self.update_model_dropdown()
                QMessageBox.information(self, "Sukces", f"Model '{text.strip()}' został dodany.")
            else:
                QMessageBox.warning(self, "Uwaga", "Opis modelu jest wymagany.")
        elif ok:
            QMessageBox.warning(self, "Uwaga", "Nazwa modelu jest wymagana.")

    # -------------------------------------------------
    # --- REMOVE MODEL FUNCTION ------------------------
    # -------------------------------------------------

    @log_function
    def remove_model(self):
        current_index = self.model_dropdown.currentIndex()
        if current_index == -1:
            QMessageBox.warning(self, "Uwaga", "Brak modelu do usunięcia.")
            return
        model = self.models[current_index]
        reply = QMessageBox.question(
            self,
            "Potwierdzenie",
            f"Czy na pewno chcesz usunąć model '{model['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            del self.models[current_index]
            save_models(self.models)
            self.update_model_dropdown()
            QMessageBox.information(self, "Sukces", f"Model '{model['name']}' został usunięty.")

    # -------------------------------------------------
    # --- ADD MESSAGE FUNCTION -------------------------
    # -------------------------------------------------

    @log_function
    def add_message(self, message, role, is_code=False):
        message_frame = QFrame()
        message_layout = QHBoxLayout()
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(10)

        timestamp = QLabel(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        timestamp.setStyleSheet("""
            QLabel {
                color: gray;
                font-size: 10px;
            }
        """)
        timestamp.setAlignment(Qt.AlignmentFlag.AlignRight)

        if role == "user":
            avatar_path = USER_AVATAR
            avatar_label = self.create_avatar_label(avatar_path)
            message_label = QLabel(message)
            message_label.setStyleSheet("""
                QLabel {
                    background-color: #007bff;
                    color: white;
                    padding: 10px;
                    border-radius: 15px;
                    font-size: 14px;
                }
            """)
            message_label.setWordWrap(True)
            message_label.setFont(QFont("Arial", 12))
            message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            message_label.setTextFormat(Qt.TextFormat.PlainText)
            message_layout.addStretch()
            message_layout.addWidget(message_label)
            message_layout.addWidget(avatar_label)

        elif role == "assistant":
            avatar_path = AI_AVATAR
            avatar_label = self.create_avatar_label(avatar_path)
            if is_code:
                message_label = QTextEdit()
                message_label.setReadOnly(True)
                message_label.setStyleSheet("""
                    QTextEdit {
                        background-color: #e5e5ea;
                        color: black;
                        padding: 10px;
                        border-radius: 15px;
                        font-size: 14px;
                    }
                """)
                message_label.setFont(QFont("Courier", 12))
                message_label.setText(message)
                message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                message_label.setTextFormat(Qt.TextFormat.RichText)
            else:
                message_label = QLabel(message)
                message_label.setStyleSheet("""
                    QLabel {
                        background-color: #e5e5ea;
                        color: black;
                        padding: 10px;
                        border-radius: 15px;
                        font-size: 14px;
                    }
                """)
                message_label.setWordWrap(True)
                message_label.setFont(QFont("Arial", 12))
                message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                message_label.setTextFormat(Qt.TextFormat.PlainText)

            message_layout.addWidget(avatar_label)
            message_layout.addWidget(message_label)
            message_layout.addStretch()

        else:
            avatar_label = QLabel()
            message_label = QLabel(message)
            message_label.setStyleSheet("""
                QLabel {
                    background-color: #cccccc;
                    color: black;
                    padding: 10px;
                    border-radius: 15px;
                    font-size: 14px;
                }
            """)
            message_label.setWordWrap(True)
            message_label.setFont(QFont("Arial", 12))
            message_layout.addWidget(avatar_label)
            message_layout.addWidget(message_label)
            message_layout.addStretch()

        # Layout for timestamp
        timestamp_layout = QHBoxLayout()
        timestamp_layout.addStretch()
        timestamp_layout.addWidget(timestamp)
        timestamp_layout.setContentsMargins(0, 0, 0, 0)

        # Combine message and timestamp
        message_frame_with_timestamp = QVBoxLayout()
        message_frame_with_timestamp.setContentsMargins(0, 0, 0, 0)
        message_frame_with_timestamp.setSpacing(0)
        message_frame_with_timestamp.addLayout(message_layout)
        message_frame_with_timestamp.addLayout(timestamp_layout)

        container_frame = QFrame()
        container_frame.setLayout(message_frame_with_timestamp)
        container_frame.setWindowOpacity(0)  # Initial opacity

        self.chat_layout.addWidget(container_frame)
        self.chat_layout.addSpacing(5)

        # Animation for message appearance
        animation = QPropertyAnimation(container_frame, b"windowOpacity")
        animation.setDuration(500)  # Duration in ms
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.start()

        # Auto scroll to the latest message
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )

    # -------------------------------------------------
    # --- CREATE AVATAR LABEL FUNCTION ---------------
    # -------------------------------------------------

    @log_function
    def create_avatar_label(self, relative_path):
        label = QLabel()
        if relative_path and os.path.exists(relative_path):
            pixmap = QPixmap(relative_path)
            if pixmap.isNull():
                logging.warning(f"Nie udało się załadować obrazu: {relative_path}")
                pixmap = QPixmap(self.icons.get("default_avatar").pixmap(40, 40))
        else:
            logging.warning(f"Avatar nie został znaleziony lub ścieżka jest pusta: {relative_path}")
            pixmap = QPixmap(self.icons.get("default_avatar").pixmap(40, 40))

        if not pixmap.isNull():
            pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            label.setPixmap(pixmap)
        else:
            logging.warning(f"Nie udało się załadować awatara: {relative_path}")

        return label

    # -------------------------------------------------
    # --- HANDLE SEND FUNCTION ------------------------
    # -------------------------------------------------

    @log_function
    def handle_send(self, checked=False):
        user_input = self.input_field.toPlainText().strip()
        if user_input == "":
            return

        self.input_field.clear()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.add_message(user_input, "user")
        self.conversation.append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp
        })

        selected_model = self.get_selected_model()

        # Start OpenAI API thread
        self.thread = OpenAIThread(self.conversation.copy(), selected_model)
        self.thread.response_received.connect(self.handle_response)
        self.thread.error_occurred.connect(self.handle_error)
        self.thread.tokens_used.connect(self.update_token_counter)
        self.thread.start()

    # -------------------------------------------------
    # --- GET SELECTED MODEL FUNCTION -----------------
    # -------------------------------------------------

    @log_function
    def get_selected_model(self):
        current_text = self.model_dropdown.currentText()
        model_name = current_text.split(":")[0]
        return model_name.strip()

    # -------------------------------------------------
    # --- HANDLE RESPONSE FUNCTION ---------------------
    # -------------------------------------------------

    @log_function
    def handle_response(self, ai_message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if "```" in ai_message:
            is_code = True
        else:
            is_code = False

        self.conversation.append({
            "role": "assistant",
            "content": ai_message,
            "timestamp": timestamp
        })
        self.add_message(ai_message, "assistant", is_code=is_code)

    # -------------------------------------------------
    # --- HANDLE ERROR FUNCTION ------------------------
    # -------------------------------------------------

    @log_function
    def handle_error(self, error_message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conversation.append({
            "role": "assistant",
            "content": error_message,
            "timestamp": timestamp
        })
        self.add_message(error_message, "assistant")

    # -------------------------------------------------
    # --- TOGGLE THEME FUNCTION ------------------------
    # -------------------------------------------------

    @log_function
    def toggle_theme(self, checked=False):
        palette = self.palette()
        if palette.color(QPalette.ColorRole.Window) == QColor("#f0f0f0"):
            palette.setColor(QPalette.ColorRole.Window, QColor("#2c2c2c"))
            palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Base, QColor("#3c3c3c"))
            palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            self.set_dark_theme()
            self.save_style_to_config(0)  # 0 for dark mode
        else:
            palette.setColor(QPalette.ColorRole.Window, QColor("#f0f0f0"))
            palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
            palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
            self.set_light_theme()
            self.save_style_to_config(1)  # 1 for light mode

    # -------------------------------------------------
    # --- SET LIGHT THEME FUNCTION ---------------------
    # -------------------------------------------------

    @log_function
    def set_light_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                color: black;
            }
            QTextEdit {
                background-color: #ffffff;
                color: black;
                border: 2px solid #ccc;
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 4px;  /* Adjusted padding */
                min-width: 40px;
                min-height: 40px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QComboBox {
                background-color: #ffffff;
                color: black;
                border: 2px solid #ccc;
                border-radius: 10px;
            }
        """)

    # -------------------------------------------------
    # --- SET DARK THEME FUNCTION ----------------------
    # -------------------------------------------------

    @log_function
    def set_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2c2c2c;
                color: white;
            }
            QTextEdit {
                background-color: #3c3c3c;
                color: white;
                border: 2px solid #555;
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton {
                background-color: #555;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 4px;  /* Adjusted padding */
                min-width: 40px;
                min-height: 40px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #333;
            }
            QComboBox {
                background-color: #3c3c3c;
                color: white;
                border: 2px solid #555;
                border-radius: 10px;
            }
        """)

    # -------------------------------------------------
    # --- APPLY CUSTOM STYLE FUNCTION ------------------
    # -------------------------------------------------

    @log_function
    def apply_custom_style(self, style_number, checked=False):
        if style_number == 1:
            self.setStyleSheet("""
                QWidget {
                    background-color: #ffffff;
                    color: #343a40;
                }
                QTextEdit {
                    background-color: #f8f9fa;
                    color: #343a40;
                    border: 2px solid #6f42c1;
                    border-radius: 20px;
                    font-size: 16px;
                }
                QPushButton {
                    background-color: #6f42c1;
                    color: white;
                    border: none;
                    border-radius: 20px;
                    padding: 4px;  /* Adjusted padding */
                    min-width: 40px;
                    min-height: 40px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #5a32a3;
                }
                QComboBox {
                    background-color: #f8f9fa;
                    color: #343a40;
                    border: 2px solid #6f42c1;
                    border-radius: 10px;
                }
            """)
            self.save_style_to_config(style_number)
        elif style_number == 2:
            self.setStyleSheet("""
                QWidget {
                    background-color: #fff3cd;
                    color: #856404;
                }
                QTextEdit {
                    background-color: #fff8e1;
                    color: #856404;
                    border: 2px solid #fd7e14;
                    border-radius: 20px;
                    font-size: 16px;
                }
                QPushButton {
                    background-color: #fd7e14;
                    color: white;
                    border: none;
                    border-radius: 20px;
                    padding: 4px;  /* Adjusted padding */
                    min-width: 40px;
                    min-height: 40px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #e06b0f;
                }
                QComboBox {
                    background-color: #fff8e1;
                    color: #856404;
                    border: 2px solid #fd7e14;
                    border-radius: 10px;
                }
            """)
            self.save_style_to_config(style_number)
        elif style_number == 3:
            self.setStyleSheet("""
                QWidget {
                    background-color: #e9f7ef;
                    color: #155724;
                }
                QTextEdit {
                    background-color: #d4edda;
                    color: #155724;
                    border: 2px solid #20c997;
                    border-radius: 20px;
                    font-size: 16px;
                }
                QPushButton {
                    background-color: #20c997;
                    color: white;
                    border: none;
                    border-radius: 20px;
                    padding: 4px;  /* Adjusted padding */
                    min-width: 40px;
                    min-height: 40px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #17a085;
                }
                QComboBox {
                    background-color: #d4edda;
                    color: #155724;
                    border: 2px solid #20c997;
                    border-radius: 10px;
                }
            """)
            self.save_style_to_config(style_number)
        elif style_number == 4:
            self.setStyleSheet("""
                QWidget {
                    background-color: #f8d7da;
                    color: #721c24;
                }
                QTextEdit {
                    background-color: #f5c6cb;
                    color: #721c24;
                    border: 2px solid #dc3545;
                    border-radius: 20px;
                    font-size: 16px;
                }
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 20px;
                    padding: 4px;  /* Adjusted padding */
                    min-width: 40px;
                    min-height: 40px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
                QComboBox {
                    background-color: #f5c6cb;
                    color: #721c24;
                    border: 2px solid #dc3545;
                    border-radius: 10px;
                }
            """)
            self.save_style_to_config(style_number)

    # -------------------------------------------------
    # --- SAVE STYLE TO CONFIG FUNCTION ---------------
    # -------------------------------------------------

    @log_function
    def save_style_to_config(self, style_number):
        config = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except json.JSONDecodeError:
                logging.warning("Plik config.json jest uszkodzony! Resetowanie konfiguracji.")
        config["style"] = style_number
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            logging.debug(f"Zapisano styl {style_number} do config.json")
        except Exception as e:
            logging.error(f"Nie udało się zapisać konfiguracji: {e}")

    # -------------------------------------------------
    # --- LOAD STYLE FROM CONFIG FUNCTION -------------
    # -------------------------------------------------

    @log_function
    def load_style_from_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                style_number = config.get("style", 1)
                self.apply_custom_style(style_number)
                logging.debug(f"Załadowano styl {style_number} z config.json")
            except json.JSONDecodeError:
                logging.warning("Plik config.json jest uszkodzony! Ustawianie domyślnego stylu.")
            except Exception as e:
                logging.error(f"Błąd podczas ładowania stylu z config.json: {e}")

    # -------------------------------------------------
    # --- ADD IMAGE FUNCTION ---------------------------
    # -------------------------------------------------

    @log_function
    def add_image(self, image_path, role, timestamp):
        message_frame = QFrame()
        message_layout = QHBoxLayout()
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(10)

        if role == "user":
            avatar_path = USER_AVATAR
        else:
            avatar_path = AI_AVATAR

        avatar_label = self.create_avatar_label(avatar_path)

        image_label = QLabel()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(pixmap)
            image_label.setStyleSheet("""
                QLabel {
                    border: 2px solid #ccc;
                    border-radius: 10px;
                }
            """)
        else:
            image_label.setText("Nie udało się załadować obrazu.")
            image_label.setStyleSheet("""
                QLabel {
                    color: red;
                    font-size: 14px;
                }
            """)

        if role == "user":
            message_layout.addStretch()
            message_layout.addWidget(image_label)
            message_layout.addWidget(avatar_label)
        else:
            message_layout.addWidget(avatar_label)
            message_layout.addWidget(image_label)
            message_layout.addStretch()

        # Layout for timestamp
        timestamp_label = QLabel(timestamp)
        timestamp_label.setStyleSheet("""
            QLabel {
                color: gray;
                font-size: 10px;
            }
        """)
        timestamp_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Combine message and timestamp
        message_frame_with_timestamp = QVBoxLayout()
        message_frame_with_timestamp.setContentsMargins(0, 0, 0, 0)
        message_frame_with_timestamp.setSpacing(0)
        message_frame_with_timestamp.addLayout(message_layout)
        timestamp_layout = QHBoxLayout()
        timestamp_layout.addStretch()
        timestamp_layout.addWidget(timestamp_label)
        timestamp_layout.setContentsMargins(0, 0, 0, 0)
        message_frame_with_timestamp.addLayout(timestamp_layout)

        container_frame = QFrame()
        container_frame.setLayout(message_frame_with_timestamp)
        container_frame.setWindowOpacity(0)  # Initial opacity

        self.chat_layout.addWidget(container_frame)
        self.chat_layout.addSpacing(5)

        # Animation for message appearance
        animation = QPropertyAnimation(container_frame, b"windowOpacity")
        animation.setDuration(500)  # Duration in ms
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.start()

        # Auto scroll to the latest message
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )

    # -------------------------------------------------
    # --- SAVE CONVERSATION FUNCTION -------------------
    # -------------------------------------------------

    @log_function
    def save_conversation(self):
        try:
            with open("conversation_history.json", "w", encoding="utf-8") as f:
                json.dump(self.conversation, f, ensure_ascii=False, indent=4)
            logging.info("Rozmowa została pomyślnie zapisana.")
        except (OSError, IOError) as e:
            error_message = f"Nie udało się zapisać rozmowy: {e}"
            logging.error(error_message)
            print(error_message)
            QMessageBox.critical(self, "Błąd zapisu", "Wystąpił problem podczas zapisywania rozmowy.")

    # -------------------------------------------------
    # --- LOAD CONVERSATION FUNCTION -------------------
    # -------------------------------------------------

    @log_function
    def load_conversation(self):
        if os.path.exists("conversation_history.json"):
            try:
                with open("conversation_history.json", "r", encoding="utf-8") as f:
                    self.conversation = json.load(f)
                logging.info("Pomyślnie załadowano rozmowę z pliku JSON.")
                for msg in self.conversation:
                    if msg['role'] == "assistant" and "```" in msg['content']:
                        self.add_message(msg['content'], msg['role'], is_code=True)
                    elif msg['role'] == "user" and "Załączono obraz:" in msg['content']:
                        # Handle images
                        self.add_image(msg['content'].split(": ", 1)[1], "user", msg['timestamp'])
                    elif msg['role'] == "user" and "Załączono plik audio:" in msg['content']:
                        self.add_message(msg['content'], msg['role'])
                        # Add audio file handling here
                    elif msg['role'] == "user" and "Załączono plik wideo:" in msg['content']:
                        self.add_message(msg['content'], msg['role'])
                        # Add video preview handling here
                    else:
                        self.add_message(msg['content'], msg['role'])
            except json.JSONDecodeError:
                error_message = "Plik JSON jest uszkodzony! Nie można załadować rozmowy."
                logging.error(error_message)
                print(error_message)
                self.conversation = []
                QMessageBox.warning(self, "Błąd wczytywania", error_message)
            except Exception as e:
                error_message = f"Wystąpił nieoczekiwany błąd podczas wczytywania: {e}"
                logging.error(error_message)
                print(error_message)
                self.conversation = []
                QMessageBox.critical(self, "Błąd krytyczny", error_message)
        else:
            info_message = "Nie znaleziono pliku z historią rozmów. Tworzenie nowej historii."
            logging.info(info_message)
            print(info_message)
            self.conversation = []

    # -------------------------------------------------
    # --- SAVE TOKENS FUNCTION ------------------------
    # -------------------------------------------------

    @log_function
    def save_tokens(self):
        try:
            with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "total_tokens": self.total_tokens,
                    "used_tokens": self.used_tokens
                }, f, ensure_ascii=False, indent=4)
            logging.info("Stan tokenów został pomyślnie zapisany.")
        except (OSError, IOError) as e:
            error_message = f"Nie udało się zapisać tokenów: {e}"
            logging.error(error_message)
            print(error_message)
            QMessageBox.critical(self, "Błąd zapisu", "Wystąpił problem podczas zapisywania tokenów.")

    # -------------------------------------------------
    # --- LOAD TOKENS FUNCTION ------------------------
    # -------------------------------------------------

    @log_function
    def load_tokens(self):
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                    tokens = json.load(f)
                self.total_tokens = tokens.get("total_tokens", 10000)
                self.used_tokens = tokens.get("used_tokens", 0)
                remaining = self.total_tokens - self.used_tokens
                self.tokens_remaining_label.setText(f"Pozostałe tokeny: {remaining}")
                self.tokens_total_label.setText(f"Całkowite tokeny: {self.total_tokens}")
                logging.info("Stan tokenów został pomyślnie załadowany.")
            except json.JSONDecodeError:
                error_message = "Plik tokenów jest uszkodzony! Resetowanie liczników tokenów."
                logging.error(error_message)
                print(error_message)
                self.total_tokens = 10000
                self.used_tokens = 0
                QMessageBox.warning(self, "Błąd wczytywania", error_message)
            except Exception as e:
                error_message = f"Wystąpił nieoczekiwany błąd podczas wczytywania tokenów: {e}"
                logging.error(error_message)
                print(error_message)
                self.total_tokens = 10000
                self.used_tokens = 0
                QMessageBox.critical(self, "Błąd krytyczny", error_message)
        else:
            logging.info("Plik tokenów nie istnieje. Ustawianie domyślnych wartości.")
            self.total_tokens = 10000
            self.used_tokens = 0

    # -------------------------------------------------
    # --- CLOSE EVENT FUNCTION -------------------------
    # -------------------------------------------------

    @log_function
    def closeEvent(self, event):
        self.save_conversation()
        self.save_tokens()
        event.accept()

    # -------------------------------------------------
    # --- UPDATE TOKEN COUNTER FUNCTION ---------------
    # -------------------------------------------------

    @log_function
    def update_token_counter(self, prompt_tokens, completion_tokens):
        self.used_tokens += completion_tokens
        remaining = self.total_tokens - self.used_tokens
        self.tokens_remaining_label.setText(f"Pozostałe tokeny: {remaining}")
        self.tokens_total_label.setText(f"Całkowite tokeny: {self.total_tokens}")
        self.token_history.append(self.used_tokens)
        self.token_plot.update_plot(self.token_history)

    # -------------------------------------------------
    # --- EXPORT TO PDF FUNCTION ------------------------
    # -------------------------------------------------

    @log_function
    def export_to_pdf(self, checked=False):
        try:
            options = QFileDialog.Option.DontUseNativeDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Eksportuj do PDF",
                "",
                "PDF Files (*.pdf)",
                options=options
            )
            if file_path:
                html_content = self.generate_html_conversation()
                # Ensure wkhtmltopdf is installed and in PATH
                import pdfkit
                pdfkit.from_string(html_content, file_path)
                QMessageBox.information(self, "Sukces", f"Rozmowa została wyeksportowana do {file_path}")
                logging.info(f"Rozmowa została wyeksportowana do PDF: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wyeksportować do PDF: {e}")
            logging.error(f"Nie udało się wyeksportować do PDF: {e}")

    # -------------------------------------------------
    # --- EXPORT TO HTML FUNCTION -----------------------
    # -------------------------------------------------

    @log_function
    def export_to_html(self, checked=False):
        try:
            options = QFileDialog.Option.DontUseNativeDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Eksportuj do HTML",
                "",
                "HTML Files (*.html)",
                options=options
            )
            if file_path:
                html_content = self.generate_html_conversation()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                QMessageBox.information(self, "Sukces", f"Rozmowa została wyeksportowana do {file_path}")
                logging.info(f"Rozmowa została wyeksportowana do HTML: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wyeksportować do HTML: {e}")
            logging.error(f"Nie udało się wyeksportować do HTML: {e}")

    # -------------------------------------------------
    # --- GENERATE HTML CONVERSATION FUNCTION --------
    # -------------------------------------------------

    @log_function
    def generate_html_conversation(self):
        html = """
        <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body { font-family: Arial, sans-serif; background-color: #f0f0f0; padding: 20px; }
                    .message { margin-bottom: 15px; }
                    .user { text-align: right; }
                    .assistant { text-align: left; }
                    .user .content { background-color: #007bff; color: white; display: inline-block; padding: 10px; border-radius: 15px; }
                    .assistant .content { background-color: #e5e5ea; color: black; display: inline-block; padding: 10px; border-radius: 15px; }
                    .timestamp { font-size: 10px; color: gray; }
                    img { max-width: 300px; border: 2px solid #ccc; border-radius: 10px; }
                </style>
            </head>
            <body>
        """
        for msg in self.conversation:
            role = msg['role']
            content = msg['content']
            timestamp = msg['timestamp']
            if role == "user":
                # Escape HTML characters
                content_escaped = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                html += f"""
                <div class="message user">
                    <div class="content">{content_escaped}</div>
                    <div class="timestamp">{timestamp}</div>
                </div>
                """
            elif role == "assistant":
                # Check if the message contains an image
                if content.startswith("Załączono obraz:"):
                    # Expecting the image path
                    image_path = content.split(": ", 1)[1]
                    if os.path.exists(image_path):
                        img_src = os.path.abspath(image_path).replace("\\", "/")  # For Windows paths
                        img_tag = f'<img src="file:///{img_src}" alt="Załączony obraz">'
                    else:
                        img_tag = "Załączony obraz nie jest dostępny."
                    html += f"""
                    <div class="message assistant">
                        <div class="content">{img_tag}</div>
                        <div class="timestamp">{timestamp}</div>
                    </div>
                    """
                else:
                    # Escape HTML characters
                    content_escaped = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    html += f"""
                    <div class="message assistant">
                        <div class="content">{content_escaped}</div>
                        <div class="timestamp">{timestamp}</div>
                    </div>
                    """
            else:
                # Escape HTML characters
                content_escaped = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                html += f"""
                <div class="message">
                    <div class="content">{content_escaped}</div>
                    <div class="timestamp">{timestamp}</div>
                </div>
                """

        html += """
            </body>
        </html>
        """
        return html

    # -------------------------------------------------
    # --- DRAG ENTER EVENT FUNCTION --------------------
    # -------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    # -------------------------------------------------
    # --- DROP EVENT FUNCTION --------------------------
    # -------------------------------------------------

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        file_paths = [url.toLocalFile() for url in urls]
        for file_path in file_paths:
            if os.path.isfile(file_path):
                self.handle_attach_file(file_path)

    # -------------------------------------------------
    # --- HANDLE ATTACH FUNCTION -----------------------
    # -------------------------------------------------

    @log_function
    def handle_attach(self, checked=False):
        options = QFileDialog.Option.ReadOnly | QFileDialog.Option.DontUseNativeDialog
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Wybierz pliki do załączenia",
            "",
            "Wszystkie pliki (*);;Pliki tekstowe (*.txt *.py *.md);;Obrazy (*.png *.jpg *.jpeg *.bmp *.gif);;Pliki audio (*.mp3 *.wav);;Pliki wideo (*.mp4 *.avi *.mov)",
            options=options
        )
        if file_paths:
            for file_path in file_paths:
                self.handle_attach_file(file_path)

    # -------------------------------------------------
    # --- HANDLE ATTACH FILE FUNCTION -------------------
    # -------------------------------------------------

    @log_function
    def handle_attach_file(self, file_path):
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            file_name = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if file_extension in ['.txt', '.py', '.md']:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                display_message = f"Załączono plik: {file_name}\n{content}"
                self.add_message(display_message, "user")
                self.conversation.append({
                    "role": "user",
                    "content": display_message,
                    "timestamp": timestamp
                })
            elif file_extension in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
                display_message = f"Załączono obraz: {file_path}"  # Use full path
                self.add_message(display_message, "user")
                self.conversation.append({
                    "role": "user",
                    "content": display_message,
                    "timestamp": timestamp
                })
                self.add_image(file_path, "user", timestamp)
            elif file_extension in ['.mp3', '.wav']:
                display_message = f"Załączono plik audio: {file_path}"
                self.add_message(display_message, "user")
                self.conversation.append({
                    "role": "user",
                    "content": display_message,
                    "timestamp": timestamp
                })
                # Add audio playback handling here
            elif file_extension in ['.mp4', '.avi', '.mov']:
                display_message = f"Załączono plik wideo: {file_path}"
                self.add_message(display_message, "user")
                self.conversation.append({
                    "role": "user",
                    "content": display_message,
                    "timestamp": timestamp
                })
                # Add video preview handling here
            else:
                display_message = f"Załączono plik: {file_name} (Typ pliku: {file_extension})"
                self.add_message(display_message, "user")
                self.conversation.append({
                    "role": "user",
                    "content": display_message,
                    "timestamp": timestamp
                })

            selected_model = self.get_selected_model()

            self.thread = OpenAIThread(self.conversation.copy(), selected_model)
            self.thread.response_received.connect(self.handle_response)
            self.thread.error_occurred.connect(self.handle_error)
            self.thread.tokens_used.connect(self.update_token_counter)
            self.thread.start()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się załączyć pliku: {e}")

    # -------------------------------------------------
    # --- TOGGLE LOG VIEW FUNCTION ---------------------
    # -------------------------------------------------

    @log_function
    def toggle_log_view(self, checked=False):
        if self.log_dock.isVisible():
            self.log_dock.hide()
        else:
            self.log_dock.show()

    # -------------------------------------------------
    # --- ADD CUSTOM THEME FUNCTION ---------------------
    # -------------------------------------------------

    @log_function
    def add_custom_theme(self, checked=False):
        color = QColorDialog.getColor()
        if color.isValid():
            # Get current style
            current_style = self.styleSheet()
            # Add new theme
            new_style = f"""
                QWidget {{
                    background-color: {color.name()};
                    color: black;
                }}
                QTextEdit {{
                    background-color: #ffffff;
                    color: black;
                    border: 2px solid #ccc;
                    border-radius: 20px;
                    font-size: 16px;
                }}
                QPushButton {{
                    background-color: #28a745;
                    color: white;
                    border: none;
                    border-radius: 20px;
                    padding: 4px;
                    min-width: 40px;
                    min-height: 40px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: #218838;
                }}
                QComboBox {{
                    background-color: #ffffff;
                    color: black;
                    border: 2px solid #ccc;
                    border-radius: 10px;
                }}
            """
            self.setStyleSheet(new_style)
            QMessageBox.information(self, "Sukces", "Własny motyw został zastosowany.")
            logging.info("Dodano własny motyw kolorystyczny.")

    # -------------------------------------------------
    # --- ADD CUSTOM ICON FUNCTION ---------------------
    # -------------------------------------------------

    @log_function
    def add_custom_icon(self, checked=False):
        options = QFileDialog.Option.ReadOnly | QFileDialog.Option.DontUseNativeDialog
        icon_path, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz ikonę do dodania",
            "",
            "Obrazy (*.png *.jpg *.jpeg *.bmp *.gif)",
            options=options
        )
        if icon_path:
            # Let the user choose which button to add the icon to
            buttons = ["Styl 1", "Styl 2", "Styl 3", "Styl 4", "Resize In", "Resize Out", "Przełącz tryb", "Załącz plik"]
            button, ok = QInputDialog.getItem(self, "Wybierz przycisk", "Do którego przycisku chcesz dodać ikonę?", buttons, 0, False)
            if ok and button:
                # Find the corresponding QAction and set the new icon
                for action in self.findChildren(QAction):
                    if action.text() == button:
                        action.setIcon(QIcon(QPixmap(icon_path)))
                        QMessageBox.information(self, "Sukces", f"Ikona została dodana do przycisku '{button}'.")
                        logging.info(f"Dodano ikonę do przycisku '{button}'.")
                        break
            else:
                QMessageBox.warning(self, "Uwaga", "Nie udało się znaleźć odpowiedniego przycisku.")
                logging.warning(f"Nie udało się znaleźć przycisku dla ikony: {button}")

    # -------------------------------------------------
    # --- SEND CONVERSATION VIA EMAIL FUNCTION --------
    # -------------------------------------------------

    @log_function
    def send_conversation_via_email(self, checked=False):
        try:
            # Email configuration
            sender_email = os.getenv("SMTP_SENDER_EMAIL")
            receiver_email = os.getenv("SMTP_RECEIVER_EMAIL")
            password = os.getenv("SMTP_PASSWORD")

            if not sender_email or not receiver_email or not password:
                QMessageBox.warning(self, "Uwaga", "Brak danych konfiguracyjnych email. Sprawdź plik .env.")
                return

            message = MIMEMultipart("alternative")
            message["Subject"] = "Historia Rozmów z ChatApp"
            message["From"] = sender_email
            message["To"] = receiver_email

            # Generate email content
            html_content = self.generate_html_conversation()
            part = MIMEText(html_content, "html")
            message.attach(part)

            # Send email
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, password)
                server.sendmail(
                    sender_email, receiver_email, message.as_string()
                )

            QMessageBox.information(self, "Sukces", "Rozmowa została wysłana na email.")
            logging.info("Rozmowa została wysłana na email.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wysłać rozmowy na email: {e}")
            logging.error(f"Nie udało się wysłać rozmowy na email: {e}")

    # -------------------------------------------------
    # --- ADD SEND EMAIL OPTION FUNCTION --------------
    # -------------------------------------------------

    @log_function
    def add_send_email_option(self):
        send_email_action = QAction("Wyślij rozmowę na Email", self)
        send_email_action.setStatusTip("Wyślij historię rozmów na wybrany adres email")
        send_email_action.triggered.connect(self.send_conversation_via_email)
        toolbar = self.findChild(QToolBar, "Toolbar")
        if toolbar:
            toolbar.addAction(send_email_action)

    # -------------------------------------------------
    # --- ADD WORD COUNTER FUNCTION --------------------
    # -------------------------------------------------

    @log_function
    def add_word_counter(self):
        # Add word counters for user and AI
        self.user_word_count = 0
        self.ai_word_count = 0

        word_layout = QHBoxLayout()
        self.user_word_label = QLabel(f"Użytkownik napisał: {self.user_word_count} słów")
        self.ai_word_label = QLabel(f"AI odpowiedziało: {self.ai_word_count} słów")
        word_layout.addWidget(self.user_word_label)
        word_layout.addStretch()
        word_layout.addWidget(self.ai_word_label)
        self.centralWidget().layout().addLayout(word_layout)

    # -------------------------------------------------
    # --- INTEGRATE WITH TRELLO FUNCTION --------------
    # -------------------------------------------------

    @log_function
    def integrate_with_trello(self, checked=False):
        # Pobierz klucz API, token i ID tablicy z pliku .env
        trello_key = TRELLO_API_KEY
        trello_token = TRELLO_TOKEN
        trello_board_id = TRELLO_BOARD_ID
        trello_list_id = TRELLO_LIST_ID  # ID listy, do której będą dodawane karty

        if not trello_key or not trello_token or not trello_board_id or not trello_list_id:
            QMessageBox.warning(self, "Uwaga", "Brak danych konfiguracyjnych Trello. Sprawdź plik .env.")
            logging.warning("Brak danych konfiguracyjnych Trello. Integracja została pominięta.")
            return

        try:
            # Przykład: Dodanie karty na Trello z ostatnią wiadomością
            last_message = self.conversation[-1] if self.conversation else None
            if last_message:
                card_name = f"{last_message['role'].capitalize()} - {last_message['timestamp']}"
                card_desc = last_message['content']

                url = "https://api.trello.com/1/cards"
                query = {
                    'key': trello_key,
                    'token': trello_token,
                    'idList': trello_list_id,
                    'name': card_name,
                    'desc': card_desc
                }
                response = requests.post(url, params=query)
                if response.status_code == 200:
                    QMessageBox.information(self, "Sukces", "Rozmowa została dodana do Trello.")
                    logging.info("Rozmowa została dodana do Trello.")
                else:
                    QMessageBox.critical(self, "Błąd", f"Nie udało się dodać karty do Trello: {response.text}")
                    logging.error(f"Nie udało się dodać karty do Trello: {response.text}")
            else:
                QMessageBox.warning(self, "Uwaga", "Brak wiadomości do dodania do Trello.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się zintegrować z Trello: {e}")
            logging.error(f"Nie udało się zintegrować z Trello: {e}")

    # -------------------------------------------------
    # --- INTEGRATE WITH GOOGLE SHEETS FUNCTION -------
    # -------------------------------------------------

    @log_function
    def integrate_with_google_sheets(self, checked=False):
        # Konfiguracja poświadczeń
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials_path = GOOGLE_SHEETS_CREDENTIALS
        if not credentials_path or not os.path.exists(credentials_path):
            QMessageBox.warning(self, "Uwaga", "Brak pliku poświadczeń Google Sheets. Sprawdź plik .env.")
            return
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
        client = gspread.authorize(creds)

        try:
            sheet_name = GOOGLE_SHEETS_NAME
            if not sheet_name:
                QMessageBox.warning(self, "Uwaga", "Brak nazwy arkusza Google Sheets. Sprawdź plik .env.")
                return
            sheet = client.open(sheet_name).sheet1
            last_message = self.conversation[-1] if self.conversation else None
            if last_message:
                sheet.append_row([last_message['role'], last_message['content'], last_message['timestamp']])
                QMessageBox.information(self, "Sukces", "Rozmowa została dodana do Google Sheets.")
                logging.info("Rozmowa została dodana do Google Sheets.")
            else:
                QMessageBox.warning(self, "Uwaga", "Brak wiadomości do dodania do Google Sheets.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się zintegrować z Google Sheets: {e}")
            logging.error(f"Nie udało się zintegrować z Google Sheets: {e}")

    # -------------------------------------------------
    # --- ADD MINIGAME FUNCTION ------------------------
    # -------------------------------------------------

    @log_function
    def add_minigame(self, checked=False):
        # Implement minigame like Snake or Tic-Tac-Toe
        # Placeholder for future implementation
        QMessageBox.information(self, "Minigame", "Funkcja minigame jeszcze nie została zaimplementowana.")

    # -------------------------------------------------
    # --- ADD DEVELOPER MODE FUNCTION ------------------
    # -------------------------------------------------

    @log_function
    def add_developer_mode(self):
        developer_action = QAction("Tryb Developer", self)
        developer_action.setStatusTip("Włącz tryb deweloperski")
        developer_action.triggered.connect(self.toggle_developer_mode)
        toolbar = self.findChild(QToolBar, "Toolbar")
        if toolbar:
            toolbar.addAction(developer_action)
        self.developer_mode = False

    @log_function
    def toggle_developer_mode(self, checked=False):
        self.developer_mode = not self.developer_mode
        if self.developer_mode:
            # Add additional info in developer mode
            developer_info = QLabel("Tryb Developer: Szczegóły zapytań API, liczba tokenów, czas odpowiedzi.")
            developer_info.setObjectName("developer_info")
            developer_info.setStyleSheet("""
                QLabel#developer_info {
                    color: #ffcc00;
                    font-size: 12px;
                }
            """)
            self.centralWidget().layout().addWidget(developer_info)
            logging.info("Tryb deweloperski został włączony.")
        else:
            # Remove additional info in developer mode
            developer_info = self.findChild(QLabel, "developer_info")
            if developer_info:
                self.centralWidget().layout().removeWidget(developer_info)
                developer_info.deleteLater()
            logging.info("Tryb deweloperski został wyłączony.")

    # -------------------------------------------------
    # --- ADD IMAGE FUNCTION (Extended) ---------------
    # -------------------------------------------------

    # Here you can extend the add_message function to handle more types of content if needed.

    # -------------------------------------------------
    # --- OTHER FUNCTIONS ------------------------------
    # -------------------------------------------------

    # Add other functions like Google Sheets integration, audio recording, video handling, minigames, etc.
    # You can add these functions here as needed.

    # -------------------------------------------------
    # --- OPEN SETTINGS PANEL FUNCTION -----------------
    # -------------------------------------------------

    @log_function
    def open_settings_panel(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec()

    # -------------------------------------------------
    # --- OPEN PYTHON QUIZ FUNCTION --------------------
    # -------------------------------------------------

    @log_function
    def start_python_quiz(self, checked=False):
        quiz_dialog = PythonQuizDialog(self)
        quiz_dialog.exec()

    # -------------------------------------------------
    # --- OPEN CONVERSATION HISTORY FUNCTION ----------
    # -------------------------------------------------

    @log_function
    def open_conversation_history(self, checked=False):
        history_dialog = ConversationHistoryDialog(self.conversation, self)
        history_dialog.exec()

    # -------------------------------------------------
    # --- INTEGRATE WITH TRELLO FUNCTION --------------
    # -------------------------------------------------

    @log_function
    def integrate_with_trello(self, checked=False):
        # Implementacja jak powyżej...
        # Ta metoda została już przeniesiona do klasy ChatApp
        pass

    # -------------------------------------------------
    # --- INTEGRATE WITH GOOGLE SHEETS FUNCTION -------
    # -------------------------------------------------

    @log_function
    def integrate_with_google_sheets(self, checked=False):
        # Implementacja jak powyżej...
        # Ta metoda została już przeniesiona do klasy ChatApp
        pass

    # -------------------------------------------------
    # --- ADD MINIGAME FUNCTION (Already Implemented) ---
    # -------------------------------------------------

    # Ta metoda została już przeniesiona do klasy ChatApp

    # -------------------------------------------------
    # --- ADD WORD COUNTER FUNCTION (Extended) ---------
    # -------------------------------------------------

    # Możesz dodać logikę do aktualizacji liczników słów tutaj

    # -------------------------------------------------
    # --- ADD CUSTOM THEME FUNCTION (Already Implemented) ---
    # -------------------------------------------------

    # Ta metoda została już przeniesiona do klasy ChatApp

    # -------------------------------------------------
    # --- ADD CUSTOM ICON FUNCTION (Already Implemented) ---
    # -------------------------------------------------

    # Ta metoda została już przeniesiona do klasy ChatApp

    # -------------------------------------------------
    # --- SEND CONVERSATION VIA EMAIL FUNCTION (Already Implemented) ---
    # -------------------------------------------------

    # Ta metoda została już przeniesiona do klasy ChatApp

    # -------------------------------------------------
    # --- ADD SEND EMAIL OPTION FUNCTION (Already Implemented) ---
    # -------------------------------------------------

    # Ta metoda została już przeniesiona do klasy ChatApp

    # -------------------------------------------------
    # --- ADD WORD COUNTER FUNCTION (Already Implemented) ---
    # -------------------------------------------------

    # Ta metoda została już przeniesiona do klasy ChatApp

    # -------------------------------------------------
    # --- GENERATE HTML CONVERSATION FUNCTION (Already Implemented) ---
    # -------------------------------------------------

    # Ta metoda została już przeniesiona do klasy ChatApp

# -------------------------------------------------
# --- MAIN FUNCTION ---------------------------------
# -------------------------------------------------

def main():
    app = QApplication(sys.argv)
    chat_app = ChatApp()
    chat_app.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()







