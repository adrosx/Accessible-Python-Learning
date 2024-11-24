import sys
import os
import json
import ast
import random
import logging
import pyttsx3
import keyword

from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QSplitter,
    QMessageBox, QFileDialog, QPlainTextEdit, QStatusBar, QInputDialog,
    QColorDialog, QSlider, QDialog, QDialogButtonBox, QCheckBox, QComboBox, QSpinBox, QFormLayout,
    QTreeWidget, QTreeWidgetItem, QToolBar, QFontDialog
)
from PyQt6.QtCore import Qt, QProcess, QSettings, QTimer
from PyQt6.QtGui import (
    QFont, QColor, QSyntaxHighlighter, QTextCharFormat, QIcon,
    QPainter, QTextCursor, QAction
)

# ---------------------------------------------
#            Konfiguracja logowania
# ---------------------------------------------
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ---------------------------------------------
#           Klasa główna aplikacji
# ---------------------------------------------
class PythonTutorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Tutor")
        self.resize(1200, 800)
        self.lessons = []
        self.settings = QSettings("PythonTutorApp", "PythonTutor")
        self.initUI()
        self.load_lessons()

        # Wczytaj przykłady z pliku
        self.load_examples_from_file('examples.txt')

        # Inicjalizacja asystenta
        self.assistant_steps = [
            "Witaj w Python Tutor! Ta aplikacja pomoże Ci nauczyć się programować w Pythonie.",
            "Po lewej stronie widzisz listę lekcji. Wybierz lekcję, aby zobaczyć jej treść.",
            "W środku znajduje się treść lekcji z wyjaśnieniami i przykładami.",
            "Po prawej stronie masz edytor kodu, w którym możesz pisać i uruchamiać swój kod.",
            "Na dole znajduje się konsola wyjściowa, gdzie zobaczysz wyniki działania kodu.",
            "Możesz zmieniać rozmiar czcionki za pomocą przycisków u góry: A-, A, A+.",
            "Aby uruchomić kod, kliknij przycisk 'Uruchom kod'.",
            "Jeśli potrzebujesz pomocy, kliknij 'Pokaż wskazówkę' lub 'Pokaż asystenta' w menu Pomoc.",
            "Możesz dodawać własne lekcje, klikając 'Nowa lekcja', oraz wczytywać własne przykłady.",
            "To już wszystko! Powodzenia w nauce Pythona!"
        ]
        self.current_assistant_step = 0

        # Inicjalizacja silnika pyttsx3
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', self.settings.value("speech_rate", 150, int))  # Ustawienie prędkości mowy

        logging.info("Aplikacja została zainicjowana.")

    # ---------------------------------------------
    #     Inicjalizacja interfejsu użytkownika
    # ---------------------------------------------
    def initUI(self):
        # Główny widget centralny
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Główny układ poziomy
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Panel lekcji
        self.lesson_tree = QTreeWidget()
        self.lesson_tree.setHeaderLabel("Lekcje")
        self.lesson_tree.itemClicked.connect(self.load_lesson)

        # Przyciski do zarządzania lekcjami
        lesson_button_layout = QHBoxLayout()
        add_lesson_button = QPushButton("Nowa lekcja")
        add_lesson_button.clicked.connect(self.add_new_lesson)
        edit_lesson_button = QPushButton("Edytuj lekcję")
        edit_lesson_button.clicked.connect(self.edit_lesson)
        delete_lesson_button = QPushButton("Usuń lekcję")
        delete_lesson_button.clicked.connect(self.delete_lesson)

        lesson_button_layout.addWidget(add_lesson_button)
        lesson_button_layout.addWidget(edit_lesson_button)
        lesson_button_layout.addWidget(delete_lesson_button)

        # Dodajemy drzewo lekcji i przyciski do layoutu
        lesson_panel = QWidget()
        lesson_layout = QVBoxLayout()
        lesson_panel.setLayout(lesson_layout)
        lesson_layout.addWidget(self.lesson_tree)
        lesson_layout.addLayout(lesson_button_layout)

        # Panel treści lekcji
        self.lesson_content = QTextEdit()
        self.lesson_content.setReadOnly(True)

        # Przyciski w panelu treści lekcji
        lesson_content_buttons = QHBoxLayout()
        play_content_button = QPushButton("Odtwórz treść")
        play_content_button.clicked.connect(self.play_lesson_content)
        lesson_content_buttons.addWidget(play_content_button)

        # Dodajemy przyciski do układu panelu lekcji
        lesson_content_widget = QWidget()
        lesson_content_widget.setLayout(lesson_content_buttons)

        # Edytor kodu
        self.code_editor = CodeEditor()
        self.highlighter = PythonHighlighter(self.code_editor.document())
        self.code_editor.textChanged.connect(self.real_time_analysis)

        # Konsola wyjściowa
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setStyleSheet("background-color: black; color: white;")

        # Przyciski zmiany rozmiaru czcionki
        font_button_layout = QHBoxLayout()

        small_font_button = QPushButton("A-")
        small_font_button.setToolTip("Mała czcionka")
        small_font_button.clicked.connect(self.set_small_font)

        normal_font_button = QPushButton("A")
        normal_font_button.setToolTip("Normalna czcionka")
        normal_font_button.clicked.connect(self.set_normal_font)

        large_font_button = QPushButton("A+")
        large_font_button.setToolTip("Duża czcionka")
        large_font_button.clicked.connect(self.set_large_font)

        font_button_layout.addWidget(small_font_button)
        font_button_layout.addWidget(normal_font_button)
        font_button_layout.addWidget(large_font_button)

        # Przyciski sterujące
        run_button = QPushButton("Uruchom kod")
        run_button.clicked.connect(self.run_code)
        hint_button = QPushButton("Pokaż wskazówkę")
        hint_button.clicked.connect(self.show_hint)
        step_button = QPushButton("Uruchom krok po kroku")
        step_button.clicked.connect(self.run_step_by_step)
        self.new_example_button = QPushButton("Nowy przykład")
        self.new_example_button.clicked.connect(self.load_new_indentation_example)
        self.new_example_button.hide()  # Domyślnie ukryty

        # Dodaj przycisk odczytu konsoli
        read_output_button = QPushButton("Odtwórz wynik")
        read_output_button.clicked.connect(self.read_output_console)

        # Układ przycisków
        button_layout = QHBoxLayout()
        button_layout.addWidget(run_button)
        button_layout.addWidget(step_button)
        button_layout.addWidget(hint_button)
        button_layout.addWidget(self.new_example_button)
        button_layout.addWidget(read_output_button)

        # Układ edytora i konsoli
        code_layout = QVBoxLayout()
        code_layout.addWidget(QLabel("Edytor kodu:"))
        code_layout.addLayout(font_button_layout)
        code_layout.addWidget(self.code_editor)
        code_layout.addLayout(button_layout)
        code_layout.addWidget(QLabel("Konsola wyjściowa:"))
        code_layout.addWidget(self.output_console)

        # Splitter dla treści lekcji i edytora
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(lesson_panel)

        lesson_content_panel = QWidget()
        lesson_content_layout = QVBoxLayout()
        lesson_content_panel.setLayout(lesson_content_layout)
        lesson_content_layout.addWidget(QLabel("Treść lekcji:"))
        lesson_content_layout.addWidget(self.lesson_content)
        lesson_content_layout.addWidget(lesson_content_widget)  # Dodajemy widget z przyciskami

        code_panel = QWidget()
        code_panel.setLayout(code_layout)

        splitter.addWidget(lesson_content_panel)
        splitter.addWidget(code_panel)
        splitter.setSizes([200, 400, 600])

        main_layout.addWidget(splitter)

        # Pasek statusu
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Menu główne
        self.create_menu()

        # Pasek narzędzi
        self.create_toolbar()

        # Zastosowanie stylów i wczytanie ustawień
        self.load_settings()

    # ---------------------------------------------
    #           Tworzenie paska narzędzi
    # ---------------------------------------------
    def create_toolbar(self):
        toolbar = QToolBar("Główny pasek narzędzi")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Stylizacja paska narzędzi
        toolbar.setStyleSheet("""
            QToolBar {
                background: #f0f0f0;
                spacing: 10px;
                padding: 5px;
            }
            QToolButton {
                background: transparent;
                border: none;
            }
            QToolButton:hover {
                background: #e0e0e0;
            }
        """)

        # Akcja otwarcia ustawień
        settings_icon = QIcon("settings_icon.png")  # Upewnij się, że plik 'settings_icon.png' jest w tym samym katalogu
        settings_action = QAction(settings_icon, "Ustawienia", self)
        settings_action.setStatusTip("Otwórz ustawienia aplikacji")
        settings_action.triggered.connect(self.open_settings_dialog)
        toolbar.addAction(settings_action)

        # Możesz dodać inne przyciski do paska narzędzi według potrzeb

    # ---------------------------------------------
    #           Tworzenie menu głównego
    # ---------------------------------------------
    def create_menu(self):
        menubar = self.menuBar()

        # Menu Plik
        file_menu = menubar.addMenu("Plik")

        save_action = QAction("Zapisz kod", self)
        save_action.triggered.connect(self.save_user_code)
        save_action.setShortcut("Ctrl+S")
        file_menu.addAction(save_action)

        load_action = QAction("Otwórz kod", self)
        load_action.triggered.connect(self.load_user_code)
        load_action.setShortcut("Ctrl+O")
        file_menu.addAction(load_action)

        load_examples_action = QAction("Wczytaj przykłady", self)
        load_examples_action.triggered.connect(self.select_examples_file)
        file_menu.addAction(load_examples_action)

        exit_action = QAction("Wyjdź", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Usunięto menu "Ustawienia"

        # Menu Pomoc
        help_menu = menubar.addMenu("Pomoc")

        assistant_action = QAction("Pokaż asystenta", self)
        assistant_action.triggered.connect(self.show_assistant)
        help_menu.addAction(assistant_action)

        about_action = QAction("O programie", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    # ---------------------------------------------
    #           Otwarcie okna ustawień
    # ---------------------------------------------
    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.apply_settings()
            logging.info("Ustawienia zostały zaktualizowane przez użytkownika.")

    # ---------------------------------------------
    #         Wczytywanie i stosowanie ustawień
    # ---------------------------------------------
    def load_settings(self):
        self.load_font_settings()
        self.apply_theme()
        self.apply_interface_scale()
        self.apply_custom_colors_from_settings()
        self.apply_simple_language_mode()
        self.apply_debug_mode()
        self.apply_dyslexia_mode()

    def apply_settings(self):
        self.load_font_settings()
        self.apply_theme()
        self.apply_interface_scale()
        self.apply_custom_colors_from_settings()
        self.apply_simple_language_mode()
        self.apply_debug_mode()
        self.apply_dyslexia_mode()
        self.engine.setProperty('rate', self.settings.value("speech_rate", 150, int))

    def apply_theme(self):
        theme = self.settings.value("theme", "light")
        if theme == "dark":
            self.setStyleSheet(self.dark_theme_stylesheet())
        else:
            self.setStyleSheet(self.light_theme_stylesheet())

    def apply_interface_scale(self):
        interface_scale = self.settings.value("interface_scale", 100, int)
        factor = interface_scale / 100
        default_font_size = self.settings.value("font_size", 12, int)
        new_font_size = int(default_font_size * factor)
        font_family = self.settings.value("font_family", "Arial")
        font = QFont(font_family, new_font_size)
        QApplication.instance().setFont(font)
        logging.info(f"Zastosowano skalowanie interfejsu: {interface_scale}%, nowy rozmiar czcionki: {new_font_size}")

    def apply_custom_colors_from_settings(self):
        bg_color = self.settings.value("bg_color", None)
        text_color = self.settings.value("text_color", None)
        if bg_color and text_color:
            self.apply_custom_colors(bg_color, text_color)

    def apply_simple_language_mode(self):
        # Jeśli tryb prostego języka jest włączony, załaduj ponownie lekcję
        if self.settings.value("simple_language", False, bool):
            self.load_lesson(self.lesson_tree.currentItem())

    def apply_debug_mode(self):
        if self.settings.value("debug_mode", False, bool):
            logging.getLogger().setLevel(logging.DEBUG)
            logging.debug("Tryb debugowania włączony.")
        else:
            logging.getLogger().setLevel(logging.INFO)
            logging.info("Tryb debugowania wyłączony.")

    def apply_dyslexia_mode(self):
        if self.settings.value("dyslexia_mode", False, bool):
            # Zastosuj specjalne ustawienia dla trybu dysleksji
            font = QFont("Arial", 16)
            font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 120)
            QApplication.instance().setFont(font)
            self.apply_custom_colors("#FFFFCC", "#000000")  # Jasnożółte tło, czarny tekst
            logging.info("Tryb dysleksji włączony.")
        else:
            # Przywróć domyślne ustawienia czcionki
            self.load_font_settings()
            logging.info("Tryb dysleksji wyłączony.")

    # ---------------------------------------------
    #             Ładowanie treści lekcji
    # ---------------------------------------------
    def load_lessons(self):
        # Lekcje domyślne
        default_lessons = [
            {"title": "Wprowadzenie", "content": """
<h2>Wprowadzenie do Pythona</h2>
<p>Python to prosty i potężny język programowania, idealny dla początkujących.</p>
<p>W tej lekcji nauczysz się, jak wyświetlać tekst na ekranie.</p>
<p><b>Przykład:</b></p>
<pre>print("Witaj świecie!")</pre>
""", "type": "default", "category": "Podstawy"},
            {"title": "Zmienne", "content": """
<h2>Zmienne w Pythonie</h2>
<p>Zmienne służą do przechowywania danych. W Pythonie nie musisz deklarować typu zmiennej.</p>
<p><b>Przykład:</b></p>
<pre>x = 5
y = "Hello"
print(x)
print(y)</pre>
""", "type": "default", "category": "Podstawy"},
            {"title": "Pętle", "content": """
<h2>Pętle w Pythonie</h2>
<p>Pętle pozwalają na wykonywanie określonego bloku kodu wielokrotnie.</p>
<p><b>Przykład pętli for:</b></p>
<pre>for i in range(5):
    print("Iteracja:", i)</pre>
""", "type": "default", "category": "Podstawy"},
            {"title": "Funkcje", "content": """
<h2>Funkcje w Pythonie</h2>
<p>Funkcje pozwalają na grupowanie kodu, który można wielokrotnie używać.</p>
<p><b>Przykład funkcji:</b></p>
<pre>def dodaj(a, b):
    return a + b

wynik = dodaj(5, 3)
print(wynik)</pre>
""", "type": "default", "category": "Zaawansowane"},
            {"title": "Wcięcia i struktura kodu", "content": """
<h2>Wcięcia i struktura kodu w Pythonie</h2>
<p>W Pythonie wcięcia są kluczowe dla określenia struktury kodu. Bloki kodu, takie jak pętle czy funkcje, są definiowane przez wcięcia.</p>
<p>Twoim zadaniem jest poprawienie błędów w wcięciach w poniższym kodzie.</p>
<p>Możesz kliknąć przycisk <b>Nowy przykład</b>, aby otrzymać inny kod do poprawienia.</p>
""", "type": "default", "category": "Zaawansowane"},
            # ... dodaj kolejne lekcje według potrzeb ...
        ]

        # Wczytaj lekcje użytkownika
        user_lessons = self.load_user_lessons_from_file('user_lessons.json')

        self.lessons = default_lessons + user_lessons
        self.update_lesson_list()

        logging.info("Lekcje zostały wczytane.")

    def load_user_lessons_from_file(self, filename):
        if not os.path.exists(filename):
            return []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                user_lessons = json.load(f)
            for lesson in user_lessons:
                lesson['type'] = 'user'
            return user_lessons
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można wczytać lekcji użytkownika:\n{e}")
            logging.error(f"Nie można wczytać lekcji użytkownika: {e}")
            return []

    def save_user_lessons_to_file(self, filename):
        user_lessons = [lesson for lesson in self.lessons if lesson['type'] == 'user']
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(user_lessons, f, ensure_ascii=False, indent=4)
            logging.info("Lekcje użytkownika zostały zapisane.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można zapisać lekcji użytkownika:\n{e}")
            logging.error(f"Nie można zapisać lekcji użytkownika: {e}")

    def update_lesson_list(self):
        self.lesson_tree.clear()
        categories = {}
        for lesson in self.lessons:
            category = lesson.get('category', 'Inne')
            if category not in categories:
                categories[category] = QTreeWidgetItem(self.lesson_tree)
                categories[category].setText(0, category)
            lesson_item = QTreeWidgetItem(categories[category])
            lesson_item.setText(0, lesson['title'])
            lesson_item.setData(0, Qt.ItemDataRole.UserRole, lesson)
        self.lesson_tree.expandAll()
        logging.info("Lista lekcji została zaktualizowana.")

    def load_lesson(self, item):
        if item is None:
            return
        lesson = item.data(0, Qt.ItemDataRole.UserRole)
        if lesson:
            content = lesson['content']
            if self.settings.value("simple_language", False, bool):
                content = self.simplify_language(content)
            self.lesson_content.setHtml(content)
            self.code_editor.clear()
            if lesson['title'] == "Wcięcia i struktura kodu":
                self.load_new_indentation_example()
                self.new_example_button.show()
            else:
                self.new_example_button.hide()
            logging.info(f"Lekcja '{lesson['title']}' została wczytana.")
        else:
            self.lesson_content.clear()
            self.code_editor.clear()
            self.new_example_button.hide()

    def simplify_language(self, content):
        # Prosta zamiana trudnych słów na prostsze
        replacements = {
            "implementacja": "wprowadzenie",
            "funkcja": "działanie",
            "definiowanie": "tworzenie",
            "parametr": "wartość",
            "argument": "wartość",
            "instrukcja": "polecenie",
            "operacja": "działanie",
            # Dodaj więcej zamian według potrzeb
        }
        for word, simple_word in replacements.items():
            content = content.replace(word, simple_word)
        return content

    def add_new_lesson(self):
        title, ok = QInputDialog.getText(self, "Nowa lekcja", "Podaj tytuł lekcji:")
        if ok and title:
            category, ok = QInputDialog.getText(self, "Nowa lekcja", "Podaj kategorię lekcji:")
            if not ok or not category:
                category = "Inne"
            content, ok = QInputDialog.getMultiLineText(self, "Nowa lekcja", "Wprowadź treść lekcji:")
            if ok:
                new_lesson = {
                    "title": title,
                    "content": content,
                    "type": "user",
                    "category": category
                }
                self.lessons.append(new_lesson)
                self.update_lesson_list()
                self.save_user_lessons_to_file('user_lessons.json')
                logging.info(f"Dodano nową lekcję: {title}")

    def edit_lesson(self):
        selected_item = self.lesson_tree.currentItem()
        if selected_item:
            lesson = selected_item.data(0, Qt.ItemDataRole.UserRole)
            if lesson and lesson['type'] == 'user':
                new_title, ok = QInputDialog.getText(self, "Edytuj lekcję", "Edytuj tytuł lekcji:", text=lesson['title'])
                if ok and new_title:
                    new_category, ok = QInputDialog.getText(self, "Edytuj lekcję", "Edytuj kategorię lekcji:", text=lesson.get('category', 'Inne'))
                    if not ok or not new_category:
                        new_category = "Inne"
                    new_content, ok = QInputDialog.getMultiLineText(self, "Edytuj lekcję", "Edytuj treść lekcji:", text=lesson['content'])
                    if ok:
                        lesson['title'] = new_title
                        lesson['content'] = new_content
                        lesson['category'] = new_category
                        self.update_lesson_list()
                        self.save_user_lessons_to_file('user_lessons.json')
                        logging.info(f"Edytowano lekcję: {new_title}")
            else:
                QMessageBox.warning(self, "Uwaga", "Możesz edytować tylko własne lekcje.")
                logging.warning("Próba edycji lekcji domyślnej.")

    def delete_lesson(self):
        selected_item = self.lesson_tree.currentItem()
        if selected_item:
            lesson = selected_item.data(0, Qt.ItemDataRole.UserRole)
            if lesson and lesson['type'] == 'user':
                reply = QMessageBox.question(
                    self,
                    'Usuń lekcję',
                    f"Czy na pewno chcesz usunąć lekcję '{lesson['title']}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.lessons.remove(lesson)
                    self.update_lesson_list()
                    self.save_user_lessons_to_file('user_lessons.json')
                    logging.info(f"Usunięto lekcję: {lesson['title']}")
            else:
                QMessageBox.warning(self, "Uwaga", "Możesz usuwać tylko własne lekcje.")
                logging.warning("Próba usunięcia lekcji domyślnej.")

    # ---------------------------------------------
    #      Ładowanie nowych przykładów wcięć
    # ---------------------------------------------
    def load_new_indentation_example(self):
        if not hasattr(self, 'indentation_examples') or not self.indentation_examples:
            QMessageBox.warning(self, "Uwaga", "Brak dostępnych przykładów wcięć.")
            logging.warning("Brak dostępnych przykładów wcięć.")
            return
        example = random.choice(self.indentation_examples)
        self.code_editor.setPlainText(example)
        self.output_console.clear()
        self.status_bar.clearMessage()
        logging.info("Załadowano nowy przykład wcięć.")

    def load_examples_from_file(self, filename):
        if not os.path.exists(filename):
            # Jeśli plik nie istnieje, utwórz go z przykładowymi danymi
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("def przyklad():\nprint('To jest przykładowy kod')\n    print('Popraw wcięcia!')\n###")
        # Teraz wczytaj przykłady z pliku
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            self.indentation_examples = content.strip().split('###')
            self.indentation_examples = [example.strip() for example in self.indentation_examples if example.strip()]
            logging.info("Przykłady wcięć zostały wczytane.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można wczytać przykładów z pliku:\n{e}")
            logging.error(f"Nie można wczytać przykładów z pliku: {e}")

    def select_examples_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Wybierz plik z przykładami", "", "Pliki tekstowe (*.txt);;Wszystkie pliki (*)"
        )
        if filename:
            self.load_examples_from_file(filename)
            QMessageBox.information(self, "Sukces", "Przykłady zostały wczytane.")
            logging.info(f"Wczytano przykłady z pliku: {filename}")

    # ---------------------------------------------
    #             Uruchamianie kodu
    # ---------------------------------------------
    def run_code(self):
        code = self.code_editor.toPlainText()
        error_message = self.analyze_code(code)
        if error_message:
            QMessageBox.critical(self, "Błąd składni", error_message)
            self.read_text_aloud(f"Błąd składni: {error_message}")
            logging.error(f"Błąd składni: {error_message}")
            return

        # Sprawdzenie, czy jesteśmy w lekcji o wcięciach
        selected_item = self.lesson_tree.currentItem()
        if selected_item:
            lesson = selected_item.data(0, Qt.ItemDataRole.UserRole)
            if lesson and lesson['title'] == "Wcięcia i struktura kodu":
                QMessageBox.information(self, "Gratulacje", "Poprawnie poprawiłeś wcięcia!")
                self.read_text_aloud("Gratulacje, poprawnie poprawiłeś wcięcia!")
                logging.info("Użytkownik poprawnie poprawił wcięcia.")
                return

        temp_file = "temp_code.py"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(code)

        self.output_console.clear()

        self.process = QProcess()
        self.process.setProgram(sys.executable)
        self.process.setArguments([temp_file])
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.data_ready)
        self.process.readyReadStandardError.connect(self.data_ready)
        self.process.finished.connect(lambda: os.remove(temp_file))
        self.process.finished.connect(self.execution_finished)
        self.process.start()
        logging.info("Kod został uruchomiony.")

    def execution_finished(self):
        output = self.output_console.toPlainText()
        if output:
            self.read_text_aloud(f"Wynik działania kodu: {output}")
        else:
            self.read_text_aloud("Kod został wykonany bez komunikatów.")
        logging.info("Wykonanie kodu zakończone.")

    # ---------------------------------------------
    #            Analiza kodu użytkownika
    # ---------------------------------------------
    def analyze_code(self, code):
        try:
            ast.parse(code)
            return None
        except SyntaxError as e:
            return f"Błąd składni w linii {e.lineno}: {e.msg}"

    # ---------------------------------------------
    #       Analiza kodu w czasie rzeczywistym
    # ---------------------------------------------
    def real_time_analysis(self):
        code = self.code_editor.toPlainText()
        error_message = self.analyze_code(code)
        if error_message:
            self.status_bar.showMessage(error_message)
        else:
            self.status_bar.clearMessage()

    # ---------------------------------------------
    #          Odbieranie danych z procesu
    # ---------------------------------------------
    def data_ready(self):
        output = self.process.readAllStandardOutput().data().decode()
        error = self.process.readAllStandardError().data().decode()
        self.output_console.append(output)
        self.output_console.append(error)
        if error:
            self.read_text_aloud(f"Błąd podczas wykonania kodu: {error}")

    # ---------------------------------------------
    #              Pokaż wskazówkę
    # ---------------------------------------------
    def show_hint(self):
        selected_item = self.lesson_tree.currentItem()
        if selected_item:
            lesson = selected_item.data(0, Qt.ItemDataRole.UserRole)
            if lesson:
                lesson_name = lesson['title']
            else:
                lesson_name = "Wprowadzenie"
        else:
            lesson_name = "Wprowadzenie"

        hints = {
            "Wprowadzenie": "Spróbuj użyć funkcji print(), aby wyświetlić tekst.",
            "Zmienne": "Pamiętaj, że zmienne nie muszą być deklarowane z typem danych.",
            "Pętle": "Użyj pętli for z funkcją range().",
            "Funkcje": "Definiuj funkcję za pomocą słowa kluczowego def.",
            "Wcięcia i struktura kodu": "Upewnij się, że bloki kodu są poprawnie wcięte.",
            # ... pozostałe wskazówki ...
        }

        hint = hints.get(lesson_name, "Brak wskazówki dla tej lekcji.")
        QMessageBox.information(self, "Wskazówka", hint)
        self.read_text_aloud(f"Wskazówka: {hint}")
        logging.info(f"Wskazówka została wyświetlona dla lekcji: {lesson_name}")

    # ---------------------------------------------
    #       Uruchamianie kodu krok po kroku
    # ---------------------------------------------
    def run_step_by_step(self):
        code = self.code_editor.toPlainText()
        self.lines = code.split('\n')
        self.current_line = 0
        self.output_console.clear()
        self.run_next_line()
        logging.info("Uruchamianie kodu krok po kroku.")

    def run_next_line(self):
        if self.current_line < len(self.lines):
            line = self.lines[self.current_line]
            if line.strip() == '':
                self.current_line += 1
                self.run_next_line()
                return
            code = '\n'.join(self.lines[:self.current_line+1])
            try:
                exec(code, globals())
                self.output_console.append(f"Linia {self.current_line+1}: {line}")
            except Exception as e:
                self.output_console.append(f"Błąd w linii {self.current_line+1}: {e}")
                self.read_text_aloud(f"Błąd w linii {self.current_line+1}: {e}")
                logging.error(f"Błąd w linii {self.current_line+1}: {e}")
                return
            self.current_line += 1
            # Podświetlenie aktualnej linii
            cursor = self.code_editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            for _ in range(self.current_line):
                cursor.movePosition(QTextCursor.MoveOperation.Down)
            self.code_editor.setTextCursor(cursor)
            # Uruchom następną linię po krótkim czasie
            QTimer.singleShot(500, self.run_next_line)
        else:
            self.output_console.append("Wykonano cały kod.")
            self.read_text_aloud("Wykonano cały kod.")
            logging.info("Kod został wykonany krok po kroku.")

    # ---------------------------------------------
    #          Zapisywanie kodu użytkownika
    # ---------------------------------------------
    def save_user_code(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Zapisz kod", "", "Pliki Python (*.py)"
        )
        if file_name:
            code = self.code_editor.toPlainText()
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(code)
            logging.info(f"Kod został zapisany do pliku: {file_name}")

    # ---------------------------------------------
    #          Ładowanie kodu użytkownika
    # ---------------------------------------------
    def load_user_code(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Otwórz kod", "", "Pliki Python (*.py)"
        )
        if file_name:
            with open(file_name, "r", encoding="utf-8") as f:
                code = f.read()
            self.code_editor.setPlainText(code)
            logging.info(f"Kod został wczytany z pliku: {file_name}")

    # ---------------------------------------------
    #                O programie
    # ---------------------------------------------
    def show_about(self):
        QMessageBox.information(self, "O programie", "Python Tutor\nWersja 1.0")

    # ---------------------------------------------
    #             Funkcje zmiany czcionki
    # ---------------------------------------------
    def set_small_font(self):
        self.apply_font_size(10)
        logging.info("Ustawiono mały rozmiar czcionki.")

    def set_normal_font(self):
        self.apply_font_size(14)
        logging.info("Ustawiono normalny rozmiar czcionki.")

    def set_large_font(self):
        self.apply_font_size(18)
        logging.info("Ustawiono duży rozmiar czcionki.")

    def apply_font_size(self, size):
        font = QApplication.font()
        font.setPointSize(size)
        QApplication.instance().setFont(font)
        self.save_font_settings(font)
        logging.info(f"Zmieniono rozmiar czcionki na: {size}")

    def save_font_settings(self, font):
        self.settings.setValue("font_family", font.family())
        self.settings.setValue("font_size", font.pointSize())

    def load_font_settings(self):
        font_family = self.settings.value("font_family", "Arial")
        font_size = self.settings.value("font_size", 12, int)
        font = QFont(font_family, font_size)
        QApplication.instance().setFont(font)
        logging.info(f"Czcionka została załadowana: {font.family()}, rozmiar: {font.pointSize()}")

    # ---------------------------------------------
    #            Przełączanie motywu
    # ---------------------------------------------
    def light_theme_stylesheet(self):
        return """
        QMainWindow {
            background-color: #f0f0f0;
        }
        QListWidget, QTreeWidget {
            background-color: #ffffff;
            color: #000000;
            font-size: 14px;
        }
        QTextEdit, QPlainTextEdit {
            background-color: #ffffff;
            color: #000000;
            font-size: 14px;
        }
        QPushButton {
            background-color: #4CAF50;
            color: white;
            padding: 8px;
            font-size: 14px;
            border: none;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QLabel {
            font-size: 16px;
            font-weight: bold;
            color: #000000;
        }
        QStatusBar {
            background-color: #e0e0e0;
        }
        """

    def dark_theme_stylesheet(self):
        return """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QListWidget, QTreeWidget {
            background-color: #3c3c3c;
            color: #ffffff;
            font-size: 14px;
        }
        QTextEdit, QPlainTextEdit {
            background-color: #3c3c3c;
            color: #ffffff;
            font-size: 14px;
        }
        QPushButton {
            background-color: #6a8759;
            color: #ffffff;
        }
        QLabel {
            color: #ffffff;
            font-size: 16px;
            font-weight: bold;
        }
        QStatusBar {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        """

    # ---------------------------------------------
    #          Odtwarzanie treści na głos
    # ---------------------------------------------
    def play_lesson_content(self):
        text = self.lesson_content.toPlainText()
        if text:
            self.engine.say(text)
            self.engine.runAndWait()
            logging.info("Treść lekcji została odtworzona na głos.")
        else:
            QMessageBox.warning(self, "Uwaga", "Brak treści do odczytania.")
            logging.warning("Próba odczytania pustej treści.")

    def read_output_console(self):
        text = self.output_console.toPlainText()
        if text:
            self.engine.say(text)
            self.engine.runAndWait()
            logging.info("Treść konsoli została odtworzona na głos.")
        else:
            QMessageBox.warning(self, "Uwaga", "Brak treści do odczytania w konsoli.")
            logging.warning("Próba odczytania pustej konsoli.")

    def read_text_aloud(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    # ---------------------------------------------
    #         Dostosowanie kolorów interfejsu
    # ---------------------------------------------
    def apply_custom_colors(self, bg_color, text_color):
        custom_stylesheet = f"""
        QMainWindow {{
            background-color: {bg_color};
            color: {text_color};
        }}
        QListWidget, QTreeWidget {{
            background-color: {bg_color};
            color: {text_color};
            font-size: 14px;
        }}
        QTextEdit, QPlainTextEdit {{
            background-color: {bg_color};
            color: {text_color};
            font-size: 14px;
        }}
        QPushButton {{
            background-color: #4CAF50;
            color: {text_color};
            padding: 8px;
            font-size: 14px;
            border: none;
            border-radius: 5px;
        }}
        QPushButton:hover {{
            background-color: #45a049;
        }}
        QLabel {{
            font-size: 16px;
            font-weight: bold;
            color: {text_color};
        }}
        QStatusBar {{
            background-color: {bg_color};
            color: {text_color};
        }}
        """

        self.setStyleSheet(custom_stylesheet)

    # ---------------------------------------------
    #              Asystent aplikacji
    # ---------------------------------------------
    def show_assistant(self):
        self.current_assistant_step = 0
        self.next_assistant_step()
        logging.info("Asystent został uruchomiony.")

    def next_assistant_step(self):
        if self.current_assistant_step < len(self.assistant_steps):
            message = self.assistant_steps[self.current_assistant_step]
            self.read_text_aloud(message)
            self.current_assistant_step += 1
            reply = QMessageBox.question(
                self,
                "Asystent",
                message,
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Ok
            )
            if reply == QMessageBox.StandardButton.Ok:
                self.next_assistant_step()
            else:
                self.current_assistant_step = 0  # Resetuj asystenta
                logging.info("Asystent został przerwany przez użytkownika.")
        else:
            self.current_assistant_step = 0  # Resetuj asystenta
            logging.info("Asystent zakończył prezentację.")

# ---------------------------------------------
#          Klasa okna ustawień
# ---------------------------------------------
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ustawienia")
        self.settings = QSettings("PythonTutorApp", "PythonTutor")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Tworzenie formularza ustawień
        form_layout = QFormLayout()

        # Czcionka
        font_button = QPushButton("Wybierz czcionkę")
        font_button.setToolTip("Kliknij, aby wybrać czcionkę aplikacji.")
        font_button.clicked.connect(self.change_font)
        form_layout.addRow(QLabel("Czcionka aplikacji:"), font_button)

        # Rozmiar czcionki
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 48)
        self.font_size_spinbox.setValue(self.settings.value("font_size", 12, int))
        self.font_size_spinbox.setToolTip("Wybierz rozmiar czcionki aplikacji.")
        self.font_size_spinbox.valueChanged.connect(self.update_font_preview)
        form_layout.addRow(QLabel("Rozmiar czcionki:"), self.font_size_spinbox)

        # Podgląd czcionki
        self.font_preview_label = QLabel("Przykładowy tekst")
        self.update_font_preview()  # Wywołujemy po zdefiniowaniu self.font_size_spinbox
        form_layout.addRow(QLabel("Podgląd czcionki:"), self.font_preview_label)

        # Motyw
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setCurrentText(self.settings.value("theme", "light"))
        self.theme_combo.setToolTip("Wybierz motyw aplikacji: jasny lub ciemny.")
        form_layout.addRow(QLabel("Motyw aplikacji:"), self.theme_combo)

        # Skalowanie interfejsu
        self.interface_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.interface_scale_slider.setRange(50, 200)
        self.interface_scale_slider.setValue(self.settings.value("interface_scale", 100, int))
        self.interface_scale_slider.setToolTip("Dostosuj skalę interfejsu aplikacji.")
        self.interface_scale_label = QLabel(f"{self.interface_scale_slider.value()}%")
        self.interface_scale_slider.valueChanged.connect(
            lambda value: self.interface_scale_label.setText(f"{value}%")
        )
        interface_scale_layout = QHBoxLayout()
        interface_scale_layout.addWidget(self.interface_scale_slider)
        interface_scale_layout.addWidget(self.interface_scale_label)
        form_layout.addRow(QLabel("Skalowanie interfejsu:"), interface_scale_layout)

        # Dostosowanie kolorów
        color_buttons_layout = QHBoxLayout()
        bg_color_button = QPushButton("Kolor tła")
        bg_color_button.setToolTip("Wybierz kolor tła aplikacji.")
        bg_color_button.clicked.connect(self.change_bg_color)
        text_color_button = QPushButton("Kolor tekstu")
        text_color_button.setToolTip("Wybierz kolor tekstu aplikacji.")
        text_color_button.clicked.connect(self.change_text_color)
        color_buttons_layout.addWidget(bg_color_button)
        color_buttons_layout.addWidget(text_color_button)
        form_layout.addRow(QLabel("Dostosuj kolory:"), color_buttons_layout)

        # Tryb prostego języka
        self.simple_language_checkbox = QCheckBox("Włączony")
        self.simple_language_checkbox.setChecked(self.settings.value("simple_language", False, bool))
        self.simple_language_checkbox.setToolTip("Włącz lub wyłącz tryb prostego języka.")
        form_layout.addRow(QLabel("Tryb prostego języka:"), self.simple_language_checkbox)

        # Tryb debugowania
        self.debug_mode_checkbox = QCheckBox("Włączony")
        self.debug_mode_checkbox.setChecked(self.settings.value("debug_mode", False, bool))
        self.debug_mode_checkbox.setToolTip("Włącz lub wyłącz tryb debugowania.")
        form_layout.addRow(QLabel("Tryb debugowania:"), self.debug_mode_checkbox)

        # Prędkość mowy
        self.speech_rate_spinbox = QSpinBox()
        self.speech_rate_spinbox.setRange(50, 300)
        self.speech_rate_spinbox.setValue(self.settings.value("speech_rate", 150, int))
        self.speech_rate_spinbox.setToolTip("Ustaw prędkość mowy dla funkcji odtwarzania treści.")
        form_layout.addRow(QLabel("Prędkość mowy:"), self.speech_rate_spinbox)

        # Tryb dysleksji
        self.dyslexia_mode_checkbox = QCheckBox("Włączony")
        self.dyslexia_mode_checkbox.setChecked(self.settings.value("dyslexia_mode", False, bool))
        self.dyslexia_mode_checkbox.setToolTip("Włącz lub wyłącz tryb dla osób z dysleksją.")
        form_layout.addRow(QLabel("Tryb dysleksji:"), self.dyslexia_mode_checkbox)

        # Dodajemy formularz do układu
        layout.addLayout(form_layout)

        # Przycisk resetowania ustawień
        reset_button = QPushButton("Resetuj do domyślnych")
        reset_button.setToolTip("Przywróć ustawienia do wartości domyślnych.")
        reset_button.clicked.connect(self.reset_to_defaults)
        layout.addWidget(reset_button)

        # Przyciski OK i Anuluj
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def change_font(self):
        font, ok = QFontDialog.getFont(QApplication.font(), self)
        if ok:
            self.settings.setValue("font_family", font.family())
            self.update_font_preview()
            logging.info(f"Czcionka została zmieniona na: {font.family()}")

    def update_font_preview(self):
        font_family = self.settings.value("font_family", "Arial")
        font_size = self.font_size_spinbox.value()
        font = QFont(font_family, font_size)
        self.font_preview_label.setFont(font)

    def change_bg_color(self):
        bg_color = QColorDialog.getColor(title="Wybierz kolor tła")
        if bg_color.isValid():
            self.settings.setValue("bg_color", bg_color.name())
            logging.info(f"Kolor tła został zmieniony na: {bg_color.name()}")

    def change_text_color(self):
        text_color = QColorDialog.getColor(title="Wybierz kolor tekstu")
        if text_color.isValid():
            self.settings.setValue("text_color", text_color.name())
            logging.info(f"Kolor tekstu został zmieniony na: {text_color.name()}")

    def reset_to_defaults(self):
        self.settings.clear()
        self.settings.sync()
        QMessageBox.information(self, "Resetowanie ustawień", "Ustawienia zostały przywrócone do domyślnych.")
        self.initUI()
        logging.info("Ustawienia zostały zresetowane do domyślnych.")

    def accept(self):
        # Zapisz ustawienia przed zamknięciem
        self.settings.setValue("font_size", self.font_size_spinbox.value())
        self.settings.setValue("theme", self.theme_combo.currentText())
        self.settings.setValue("interface_scale", self.interface_scale_slider.value())
        self.settings.setValue("simple_language", self.simple_language_checkbox.isChecked())
        self.settings.setValue("debug_mode", self.debug_mode_checkbox.isChecked())
        self.settings.setValue("speech_rate", self.speech_rate_spinbox.value())
        self.settings.setValue("dyslexia_mode", self.dyslexia_mode_checkbox.isChecked())
        super().accept()

# ---------------------------------------------
#          Klasa edytora kodu z numeracją linii
# ---------------------------------------------
class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QtCore.QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def highlight_current_line(self):
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            line_color = QColor(Qt.GlobalColor.yellow).lighter(160)

            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextCharFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(Qt.GlobalColor.lightGray))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(Qt.GlobalColor.black))
                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 5,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:
            cursor = self.textCursor()
            indentation = self.get_indentation()
            cursor.insertText('\n' + indentation)
        else:
            super().keyPressEvent(event)

    def get_indentation(self):
        cursor = self.textCursor()
        block_text = cursor.block().text()
        indentation = ''
        for char in block_text:
            if char == ' ' or char == '\t':
                indentation += char
            else:
                break
        return indentation

    def paintEvent(self, event):
        super().paintEvent(event)
        # Dodatkowe malowanie, jeśli potrzebne

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QtCore.QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)

# ---------------------------------------------
#            Klasa podświetlania składni
# ---------------------------------------------
class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        # Słowa kluczowe
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#0000FF"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        keywords = keyword.kwlist

        for word in keywords:
            pattern = f"\\b{word}\\b"
            regex = QtCore.QRegularExpression(pattern)
            self.highlighting_rules.append((regex, keyword_format))

        # Operatory
        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor("#FF00FF"))
        operator_pattern = QtCore.QRegularExpression(r"[+\-*/%=<>!]+")
        self.highlighting_rules.append((operator_pattern, operator_format))

        # Łańcuchy znaków
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#008000"))
        string_patterns = [
            QtCore.QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'),
            QtCore.QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'")
        ]
        for pattern in string_patterns:
            self.highlighting_rules.append((pattern, string_format))

        # Komentarze
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#AAAAAA"))
        comment_pattern = QtCore.QRegularExpression(r"#.*")
        self.highlighting_rules.append((comment_pattern, comment_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            i = pattern.globalMatch(text)
            while i.hasNext():
                match = i.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, format)

# ---------------------------------------------
#             Uruchomienie aplikacji
# ---------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PythonTutorApp()
    window.show()
    sys.exit(app.exec())
