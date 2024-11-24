import sys
import os
import openai
from dotenv import load_dotenv
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QScrollArea, QFrame, QTextEdit,
    QFileDialog, QMessageBox, QComboBox, QInputDialog
)
from PyQt6.QtGui import QPixmap, QFont, QColor, QPalette, QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QSize
from datetime import datetime
import json
import logging
# Konfiguracja logowania
LOG_FILE = "app_debug_log.txt"
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)
    logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)

# Tworzymy dekorator
def log_function(func):
    def wrapper(*args, **kwargs):
        logging.debug(f"Wywołano funkcję: {func.__name__} z argumentami: {args} {kwargs}")
        try:
            result = func(*args, **kwargs)
            logging.debug(f"Zakończono funkcję: {func.__name__} z wynikiem: {result}")
            return result
        except Exception as e:
            logging.error(f"Błąd w funkcji: {func.__name__} - {e}")
            raise e  # Ponownie wyrzucamy błąd, żeby program mógł dalej reagować
    return wrapper
    
# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()

# Importowanie nowej klasy OpenAI
from openai import OpenAI

# Ścieżka do pliku z modelami
MODELS_FILE = "models.json"
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#---FUNKJA GLOBALNA: LOAD_MODELS------------------
#ŁADOWANIE MODELI Z PLIKU LUB TWORZENIE DOMYŚLNYCH
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
@log_function
def load_models():
    if not os.path.exists(MODELS_FILE):
        # Jeśli plik nie istnieje, stwórz domyślną listę modeli
        default_models = {
            "models": [
                {
                    "name": "gpt-4o",
                    "description": "High-intelligence flagship model for complex, multi-step tasks."
                },
                {
                    "name": "gpt-4o-mini",
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

#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#------FUNKCJA GLOBALNA: SAVE_MODELS--------------
#------ZAPIS MODELI DO MODELS.JSON----------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------

@log_function
def save_models(models):
    with open(MODELS_FILE, "w", encoding="utf-8") as f:
        json.dump({"models": models}, f, ensure_ascii=False, indent=4)

# Inicjalizacja klienta OpenAI
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    # Opcjonalnie, ustaw inne parametry jak base_url
)

# Sprawdzenie, czy klucz API został załadowany
if not client.api_key:
    print("Klucz API nie został załadowany. Sprawdź plik .env.")
    sys.exit(1)
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#------KLASA: OPENAITHREAD------------------------
#------WĄTEK DO KOMUNIKACJI Z API OPENAI----------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------

class OpenAIThread(QThread):
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
#-------------INICJALIZUJE WĄTEK------------------
#-NIE ZAPOMNIJ ŻE MASZ 2 INITY W KODZIE-----------
#-INIT DOTYCZY WĄTKU A NIE APKI!------------------
#INIT MAIN: def __init__(self, conversation, model)
    @log_function
    def __init__(self, conversation, model):
        super().__init__()
        self.conversation = conversation
        self.model = model

#-------------------------------------------------
#-------------------------------------------------
#-----RUN-----------------------------------------
#-----WYSYŁA ZAPYTANIE DO API---------------------
#-------def run(self):----------------------------
#-------------------------------------------------
#-------------------------------------------------
    @log_function
    def run(self):
        try:
            response = client.chat.completions.create(
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
            self.response_received.emit(ai_message)
        except Exception as e:
            error_message = "Wystąpił błąd podczas komunikacji z API. Spróbuj ponownie."
            self.error_occurred.emit(error_message)
            print(f"Błąd: {e}")
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-----KLASA: CHATAPP------------------------------
#-----GŁÓWNA APLIKACJA (UI I LOGIKA)--------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------

class ChatApp(QWidget):

#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-----INIT UI: def __init__(self):----------------
#-----INICJALIZUJE APLIKACJĘ----------------------
#-----NIE POMYL INIT Z INITEM W WĄTKU-------------
    @log_function
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat z OpenAI")
        self.setGeometry(100, 100, 800, 600)
        self.conversation = []
        self.models = load_models()

        self.init_ui()
        self.load_conversation()

#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------GŁÓWNY LAYOUT-------------
#-------------------------------------------------
#-------------------------------------------------
    @log_function
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-----LAYOUT CZATU--------------------------------
#-----TWORZY OBSZAR CZATU-------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------

        # Główny obszar czatu z przewijaniem
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_widget.setLayout(self.chat_layout)
        self.chat_area.setWidget(self.chat_widget)

        main_layout.addWidget(self.chat_area)

        # Pole wprowadzania wiadomości i przyciski
        input_layout = QHBoxLayout()

#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-----POLE WPROWADZANIA WIADOMOŚCI---------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Napisz wiadomość...")
        self.input_field.returnPressed.connect(self.handle_send)
        self.input_field.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ccc;
                border-radius: 20px;
                font-size: 16px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border: 2px solid #66afe9;
                outline: none;
                background-color: #f0f8ff;
            }
        """)

        # Dropdown do wyboru modelu
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
            QComboBox::down-arrow {
                image: url(dropdown_arrow.png);
            }
        """)
        self.model_dropdown.setMinimumWidth(250)

#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-----DODAWANIE PRZYCISKÓW MODELI----------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------

        # Przyciski do dodawania i usuwania modeli
        self.add_model_button = QPushButton("+")
        self.add_model_button.setToolTip("Dodaj nowy model")
        self.add_model_button.setFixedWidth(40)
        self.add_model_button.setStyleSheet("""
            QPushButton {
                background-color: #34a853;
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #0c7b29;
            }
        """)
        self.add_model_button.clicked.connect(self.add_model)

        self.remove_model_button = QPushButton("-")
        self.remove_model_button.setToolTip("Usuń wybrany model")
        self.remove_model_button.setFixedWidth(40)
        self.remove_model_button.setStyleSheet("""
            QPushButton {
                background-color: #d93025;
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #a50e1f;
            }
        """)
        self.remove_model_button.clicked.connect(self.remove_model)

        # Przyciski z ikonami
        self.send_button = QPushButton(QIcon("send_icon.png"), "")
        self.send_button.setToolTip("Wyślij wiadomość")
        self.send_button.setIconSize(QSize(24, 24))
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                border: none;
                border-radius: 10px;
                padding: 12px;
                min-width: 40px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.send_button.clicked.connect(self.handle_send)
        self.send_button.setCursor(Qt.CursorShape.PointingHandCursor)

#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-----OBSŁUGA ZAŁĄCZNIKÓW-------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------

        self.attach_button = QPushButton(QIcon("attach_icon.png"), "")
        self.attach_button.setToolTip("Załącz plik")
        self.attach_button.setIconSize(QSize(24, 24))
        self.attach_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                border: none;
                border-radius: 10px;
                padding: 12px;
                min-width: 40px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #1e7e34;
            }
        """)
        self.attach_button.clicked.connect(self.handle_attach)
        self.attach_button.setCursor(Qt.CursorShape.PointingHandCursor)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.model_dropdown)
        input_layout.addWidget(self.add_model_button)
        input_layout.addWidget(self.remove_model_button)
        input_layout.addWidget(self.attach_button)
        input_layout.addWidget(self.send_button)

        main_layout.addLayout(input_layout)

#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-----PRZEŁĄCZANIE MOTYWU-------------------------
#-----def toggle_theme--------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
        # Przycisk przełączający tryb jasny/ciemny
        theme_layout = QHBoxLayout()
        self.theme_button = QPushButton(QIcon("theme_icon.png"), "")
        self.theme_button.setToolTip("Przełącz tryb")
        self.theme_button.setIconSize(QSize(24, 24))
        self.theme_button.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px;
                min-width: 40px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #333;
            }
        """)
        self.theme_button.clicked.connect(self.toggle_theme)
        self.theme_button.setCursor(Qt.CursorShape.PointingHandCursor)
        theme_layout.addStretch()
        theme_layout.addWidget(self.theme_button)
        main_layout.addLayout(theme_layout)

        self.setLayout(main_layout)

        # Ustawienie domyślnego trybu jasnego
        self.set_light_theme()
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#--------UPDATE MODEL DROPDOWN--------------------
#--------AKTUALIZUJE LISTTE MODELI----------------
#-------------------------------------------------
    @log_function
    def update_model_dropdown(self):
        self.model_dropdown.clear()
        for model in self.models:
            self.model_dropdown.addItem(f"{model['name']}: {model['description']}")
        self.model_dropdown.setCurrentIndex(0)

#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#--------ADD MODEL--------------------------------
#--------DODAJE MODEL-----------------------------
#-------------------------------------------------
    @log_function
    def add_model(self):
        text, ok = QInputDialog.getText(self, "Dodaj Model", "Wprowadź nazwę modelu:")
        if ok and text.strip():
            description, ok_desc = QInputDialog.getText(self, "Opis Modelu", "Wprowadź opis modelu:")
            if ok_desc and description.strip():
                # Sprawdź, czy model już istnieje
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
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#--------REMOVE MODEL-----------------------------
#--------USUWA MODEL------------------------------
#-------------------------------------------------
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

#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#--------ADD MESSAGE------------------------------
#--------DODAJE WIADOMOŚĆ DO CZATU----------------
#-------------------------------------------------
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
            avatar_path = os.path.join("avatars", "user_avatar.png")
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
            avatar_path = os.path.join("avatars", "ai_avatar.png")
            avatar_label = self.create_avatar_label(avatar_path)
            if is_code:
                # Wiadomość zawiera fragment kodu
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
            # Nieznana rola, brak awatara
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

        # Usunięcie linii poniżej
        # message_frame.setLayout(message_layout)

        # Layout dla znacznika czasu
        timestamp_layout = QHBoxLayout()
        timestamp_layout.addStretch()
        timestamp_layout.addWidget(timestamp)
        timestamp_layout.setContentsMargins(0, 0, 0, 0)

        # Tworzenie głównego layoutu z wiadomością i znacznikiem czasu
        message_frame_with_timestamp = QVBoxLayout()
        message_frame_with_timestamp.setContentsMargins(0, 0, 0, 0)
        message_frame_with_timestamp.setSpacing(0)
        message_frame_with_timestamp.addLayout(message_layout)
        message_frame_with_timestamp.addLayout(timestamp_layout)

        container_frame = QFrame()
        container_frame.setLayout(message_frame_with_timestamp)
        container_frame.setWindowOpacity(0)  # Początkowa przezroczystość

        self.chat_layout.addWidget(container_frame)
        self.chat_layout.addSpacing(5)

        # Animacja pojawiania się wiadomości
        animation = QPropertyAnimation(container_frame, b"windowOpacity")
        animation.setDuration(500)  # Czas trwania animacji w ms
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.start()

        # Automatyczne przewijanie do najnowszej wiadomości
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )

#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#--------CREATE AVATAR LABEL LINIA----------------
#--------TWORZY AWATAR----------------------------
#-------------------------------------------------
    @log_function
    def create_avatar_label(self, relative_path):
        label = QLabel()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_dir, relative_path)
        if not os.path.exists(full_path):
            print(f"Avatar nie został znaleziony: {full_path}")
            # Użyj domyślnego awataru lub pozostaw pusty QLabel
            default_avatar = os.path.join(base_dir, "avatars", "default_avatar.png")
            if os.path.exists(default_avatar):
                pixmap = QPixmap(default_avatar)
                pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                label.setPixmap(pixmap)
            return label

        pixmap = QPixmap(full_path)
        if pixmap.isNull():
            print(f"Nie udało się załadować obrazu: {full_path}")
            return label

        pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(pixmap)
        return label

#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#--------HANDLE SEND LINIA------------------------
#--------OBSŁUGUJE WYSYŁANIE WIADOMOŚCI-----------
#-------------------------------------------------
    @log_function
    def handle_send(self):
        user_input = self.input_field.text().strip()
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

        # Pobranie wybranego modelu
        selected_model = self.get_selected_model()

        # Uruchomienie wątku do wywołania API
        self.thread = OpenAIThread(self.conversation.copy(), selected_model)
        self.thread.response_received.connect(self.handle_response)
        self.thread.error_occurred.connect(self.handle_error)
        self.thread.start()
        
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#--------GET SELECTED MODEL-----------------------
#--------POBIERA WYBRANY MODEL--------------------
#-------------------------------------------------
    @log_function
    def get_selected_model(self):
        current_text = self.model_dropdown.currentText()
        model_name = current_text.split(":")[0]  # Zakładając format "model_name: description"
        return model_name.strip()

#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#--------HANDLE RESPONSE--------------------------
#--------OBSŁUGUJE ODPOWIEDŹ API------------------
#-------------------------------------------------
    @log_function
    def handle_response(self, ai_message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Sprawdzenie, czy wiadomość zawiera fragment kodu
        if "```" in ai_message:
            is_code = True
        else:
            is_code = False

        self.conversation.append({
            "role": "assistant",
            "content": ai_message,
            "timestamp": timestamp
        })
        self.add_message(ai_message, "assistant", is_code)
        
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#--------HANDLE ERROR LINIA-----------------------
#--------OBSŁUGUJE BŁEDY API----------------------
#-------------------------------------------------
    
    @log_function
    def handle_error(self, error_message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conversation.append({
            "role": "assistant",
            "content": error_message,
            "timestamp": timestamp
        })
        self.add_message(error_message, "assistant")
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#--------TOGGLE THEME LINIA 727-------------------
#--------PRZEŁĄCZA TRYB JASNY/CIEMNY--------------
#-------------------------------------------------
    
    @log_function
    def toggle_theme(self):
        palette = self.palette()
        if palette.color(QPalette.ColorRole.Window) == QColor("#f0f0f0"):
            # Przełącz na tryb ciemny
            palette.setColor(QPalette.ColorRole.Window, QColor("#2c2c2c"))
            palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Base, QColor("#3c3c3c"))
            palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            self.set_dark_theme()
        else:
            # Przełącz na tryb jasny
            palette.setColor(QPalette.ColorRole.Window, QColor("#f0f0f0"))
            palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
            palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
            self.set_light_theme()

#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#--------SET LIGHT SCHEME-------------------------
#--------USTAWIA TRYB JASNY-----------------------
#-------------------------------------------------

    @log_function
    def set_light_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                color: black;
            }
            QLineEdit {
                background-color: #ffffff;
                color: black;
                border: 2px solid #ccc;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px;
                min-width: 40px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QTextEdit {
                background-color: #ffffff;
                color: black;
            }
            QComboBox {
                background-color: #ffffff;
                color: black;
                border: 2px solid #ccc;
                border-radius: 10px;
            }
        """)
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#--------SET LIGHT SCHEME-------------------------
#--------USTAWIA TRYB CIEMNY----------------------
#-------------------------------------------------

    @log_function
    def set_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2c2c2c;
                color: white;
            }
            QLineEdit {
                background-color: #3c3c3c;
                color: white;
                border: 2px solid #555;
            }
            QPushButton {
                background-color: #555;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px;
                min-width: 40px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #333;
            }
            QTextEdit {
                background-color: #3c3c3c;
                color: white;
            }
            QComboBox {
                background-color: #3c3c3c;
                color: white;
                border: 2px solid #555;
                border-radius: 10px;
            }
        """)
        
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#--------HANDLE ATTACH LINIA----------------------
#--------OBSŁUGUJE ZAŁĄCZANIE PLIKÓW--------------
#-------------------------------------------------

    @log_function
    def handle_attach(self):
        options = QFileDialog.Option.ReadOnly | QFileDialog.Option.DontUseNativeDialog
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Wybierz pliki do załączenia",
            "",
            "Wszystkie pliki (*);;Pliki tekstowe (*.txt *.py *.md);;Obrazy (*.png *.jpg *.jpeg *.bmp *.gif)",
            options=options
        )
        if file_paths:
            for file_path in file_paths:
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
                        # Obsługa plików graficznych
                        display_message = f"Załączono obraz: {file_name}"
                        self.add_message(display_message, "user")
                        self.conversation.append({
                            "role": "user",
                            "content": display_message,
                            "timestamp": timestamp
                        })
                        # Opcjonalnie, wyświetlanie obrazu w czacie
                        self.add_image(file_path, "user", timestamp)
                    else:
                        # Obsługa innych typów plików
                        display_message = f"Załączono plik: {file_name} (Typ pliku: {file_extension})"
                        self.add_message(display_message, "user")
                        self.conversation.append({
                            "role": "user",
                            "content": display_message,
                            "timestamp": timestamp
                        })

                    # Pobranie wybranego modelu
                    selected_model = self.get_selected_model()

                    # Uruchomienie wątku do wywołania API po załączeniu pliku
                    self.thread = OpenAIThread(self.conversation.copy(), selected_model)
                    self.thread.response_received.connect(self.handle_response)
                    self.thread.error_occurred.connect(self.handle_error)
                    self.thread.start()
                except Exception as e:
                    QMessageBox.critical(self, "Błąd", f"Nie udało się załączyć pliku: {e}")
                    
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#--------ADD IMAGE LINIA--------------------------
#--------DODAJE OBRAZ DO CZATU--------------------
#-------------------------------------------------

    @log_function
    def add_image(self, image_path, role, timestamp):
        message_frame = QFrame()
        message_layout = QHBoxLayout()
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(10)

        if role == "user":
            avatar_path = os.path.join("avatars", "user_avatar.png")
        else:
            avatar_path = os.path.join("avatars", "ai_avatar.png")

        avatar_label = self.create_avatar_label(avatar_path)

        image_label = QLabel()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
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

        # Usunięcie linii poniżej
        # message_frame.setLayout(message_layout)

        # Layout dla znacznika czasu
        timestamp_label = QLabel(timestamp)
        timestamp_label.setStyleSheet("""
            QLabel {
                color: gray;
                font-size: 10px;
            }
        """)
        timestamp_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Tworzenie głównego layoutu z wiadomością i znacznikiem czasu
        message_frame_with_timestamp = QVBoxLayout()
        message_frame_with_timestamp.setContentsMargins(0, 0, 0, 0)
        message_frame_with_timestamp.setSpacing(0)
        message_frame_with_timestamp.addLayout(message_layout)
        message_frame_with_timestamp.addLayout(timestamp_layout := QHBoxLayout())
        timestamp_layout.addStretch()
        timestamp_layout.addWidget(timestamp_label)
        timestamp_layout.setContentsMargins(0, 0, 0, 0)

        container_frame = QFrame()
        container_frame.setLayout(message_frame_with_timestamp)
        container_frame.setWindowOpacity(0)  # Początkowa przezroczystość

        self.chat_layout.addWidget(container_frame)
        self.chat_layout.addSpacing(5)

        # Animacja pojawiania się wiadomości
        animation = QPropertyAnimation(container_frame, b"windowOpacity")
        animation.setDuration(500)  # Czas trwania animacji w ms
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.start()

        # Automatyczne przewijanie do najnowszej wiadomości
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )
        
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#--------SAVE CONVERSATION------------------------
#--------ZAPISUJE HISTORIE DO PLIKU---------------
#-------------------------------------------------

    @log_function

    def save_conversation(self):
        try:
            with open("conversation_history.json", "w", encoding="utf-8") as f:
                json.dump(self.conversation, f, ensure_ascii=False, indent=4)
            logging.info("Rozmowa została pomyślnie zapisana.")
        except (OSError, IOError) as e:
            error_message = f"Nie udało się zapisać rozmowy: {e}"
            logging.error(error_message)
            print(error_message)  # Opcjonalne wypisanie w terminalu
            QMessageBox.critical(self, "Błąd zapisu", "Wystąpił problem podczas zapisywania rozmowy.")
            
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#--------LOAD CONVERSATION LINIA------------------
#--------WCZYTUJE HISTORIĘ CZATU------------------
#-------------------------------------------------

    @log_function
    def load_conversation(self):
        if os.path.exists("conversation_history.json"):
            try:
                with open("conversation_history.json", "r", encoding="utf-8") as f:
                    self.conversation = json.load(f)  # Próba załadowania JSON
                logging.info("Pomyślnie załadowano rozmowę z pliku JSON.")
                # Jeśli JSON poprawny, przetwarzamy wiadomości
                for msg in self.conversation:
                    if msg['role'] == "assistant" and "```" in msg['content']:
                        self.add_message(msg['content'], msg['role'], is_code=True)
                    elif msg['role'] == "user" and "Załączono obraz:" in msg['content']:
                        # Opcjonalnie, obsługa obrazów
                        continue
                    else:
                        self.add_message(msg['content'], msg['role'])
            except json.JSONDecodeError:
                error_message = "Plik JSON jest uszkodzony! Nie można załadować rozmowy."
                logging.error(error_message)
                print(error_message)  # Opcjonalnie wypisanie w terminalu
                self.conversation = []  # Resetujemy rozmowę w razie błędu
                QMessageBox.warning(self, "Błąd wczytywania", error_message)
            except Exception as e:
                error_message = f"Wystąpił nieoczekiwany błąd podczas wczytywania: {e}"
                logging.error(error_message)
                print(error_message)  # Opcjonalnie wypisanie w terminalu
                self.conversation = []  # Dla bezpieczeństwa resetujemy
                QMessageBox.critical(self, "Błąd krytyczny", error_message)
        else:
            info_message = "Nie znaleziono pliku z historią rozmów. Tworzenie nowej historii."
            logging.info(info_message)
            print(info_message)  # Opcjonalnie wypisanie w terminalu
            self.conversation = []  # Jeśli pliku nie ma, zaczynamy od pustej historii

    # Zapisanie rozmowy przy zamykaniu aplikacji
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#--------CLOSE EVENT LINIA------------------------
#--------ZAPIS PRZY ZAMKNIĘCIU--------------------
#-------------------------------------------------
    @log_function
    def closeEvent(self, event):
        self.save_conversation()
        event.accept()

#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
#--------FUNKCJA GLOBALNA MAIN--------------------
#--------URUCHOMIENIE APLIKACJI-------------------
#-------------------------------------------------
def main():
    app = QApplication(sys.argv)
    chat_app = ChatApp()
    chat_app.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
