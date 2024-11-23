import sys
import os
import json
import ast
import random
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QSplitter, QListWidget,
    QMessageBox, QFileDialog, QPlainTextEdit, QStatusBar, QInputDialog
)
from PyQt6.QtCore import Qt, QProcess
from PyQt6.QtGui import QFont, QColor, QSyntaxHighlighter, QTextCharFormat, QIcon, QAction, QPainter, QTextCursor

import keyword

# ---------------------------------------------
#           Klasa główna aplikacji
# ---------------------------------------------
class PythonTutorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Tutor")
        self.resize(1200, 800)
        self.lessons = []
        self.initUI()
        self.load_lessons()

        # Wczytaj przykłady z pliku
        self.load_examples_from_file('examples.txt')

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
        self.lesson_list = QListWidget()
        self.lesson_list.currentItemChanged.connect(self.load_lesson)

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

        # Dodajemy listę i przyciski do layoutu
        lesson_panel = QWidget()
        lesson_layout = QVBoxLayout()
        lesson_layout.addWidget(QLabel("Lista lekcji:"))
        lesson_layout.addWidget(self.lesson_list)
        lesson_layout.addLayout(lesson_button_layout)
        lesson_panel.setLayout(lesson_layout)

        # Panel treści lekcji
        self.lesson_content = QTextEdit()
        self.lesson_content.setReadOnly(True)

        # Edytor kodu
        self.code_editor = CodeEditor()
        self.code_editor.setFont(QFont("Courier", 12))
        self.highlighter = PythonHighlighter(self.code_editor.document())
        self.code_editor.textChanged.connect(self.real_time_analysis)

        # Konsola wyjściowa
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setFont(QFont("Courier", 12))
        self.output_console.setStyleSheet("background-color: black; color: white;")

        # Przyciski sterujące
        run_button = QPushButton(QIcon("icons/run.png"), "Uruchom kod")
        run_button.clicked.connect(self.run_code)
        hint_button = QPushButton(QIcon("icons/hint.png"), "Pokaż wskazówkę")
        hint_button.clicked.connect(self.show_hint)
        step_button = QPushButton("Uruchom krok po kroku")
        step_button.clicked.connect(self.run_step_by_step)
        self.new_example_button = QPushButton("Nowy przykład")
        self.new_example_button.clicked.connect(self.load_new_indentation_example)

        # Układ przycisków
        button_layout = QHBoxLayout()
        button_layout.addWidget(run_button)
        button_layout.addWidget(step_button)
        button_layout.addWidget(hint_button)
        button_layout.addWidget(self.new_example_button)

        # Układ edytora i konsoli
        code_layout = QVBoxLayout()
        code_layout.addWidget(QLabel("Edytor kodu:"))
        code_layout.addWidget(self.code_editor)
        code_layout.addLayout(button_layout)
        code_layout.addWidget(QLabel("Konsola wyjściowa:"))
        code_layout.addWidget(self.output_console)

        # Splitter dla treści lekcji i edytora
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(lesson_panel)

        lesson_content_panel = QWidget()
        lesson_layout = QVBoxLayout()
        lesson_layout.addWidget(QLabel("Treść lekcji:"))
        lesson_layout.addWidget(self.lesson_content)
        lesson_content_panel.setLayout(lesson_layout)

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

        # Zastosowanie stylów
        self.apply_styles()

    # ---------------------------------------------
    #           Tworzenie menu głównego
    # ---------------------------------------------
    def create_menu(self):
        menubar = self.menuBar()

        # Menu Plik
        file_menu = menubar.addMenu("Plik")

        save_action = QAction(QIcon("icons/save.png"), "Zapisz kod", self)
        save_action.triggered.connect(self.save_user_code)
        file_menu.addAction(save_action)

        load_action = QAction(QIcon("icons/open.png"), "Otwórz kod", self)
        load_action.triggered.connect(self.load_user_code)
        file_menu.addAction(load_action)

        load_examples_action = QAction("Wczytaj przykłady", self)
        load_examples_action.triggered.connect(self.select_examples_file)
        file_menu.addAction(load_examples_action)

        exit_action = QAction("Wyjdź", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menu Pomoc
        help_menu = menubar.addMenu("Pomoc")

        about_action = QAction("O programie", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    # ---------------------------------------------
    #              Zastosowanie stylów
    # ---------------------------------------------
    def apply_styles(self):
        self.setStyleSheet("""
        QMainWindow {
            background-color: #f0f0f0;
        }
        QListWidget {
            background-color: #ffffff;
            font-size: 14px;
        }
        QTextEdit, QPlainTextEdit {
            background-color: #ffffff;
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
        }
        QStatusBar {
            background-color: #e0e0e0;
        }
        """)

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
""", "type": "default"},
            {"title": "Zmienne", "content": """
<h2>Zmienne w Pythonie</h2>
<p>Zmienne służą do przechowywania danych. W Pythonie nie musisz deklarować typu zmiennej.</p>
<p><b>Przykład:</b></p>
<pre>x = 5
y = "Hello"
print(x)
print(y)</pre>
""", "type": "default"},
            {"title": "Pętle", "content": """
<h2>Pętle w Pythonie</h2>
<p>Pętle pozwalają na wykonywanie określonego bloku kodu wielokrotnie.</p>
<p><b>Przykład pętli for:</b></p>
<pre>for i in range(5):
    print("Iteracja:", i)</pre>
""", "type": "default"},
            {"title": "Funkcje", "content": """
<h2>Funkcje w Pythonie</h2>
<p>Funkcje pozwalają na grupowanie kodu, który można wielokrotnie używać.</p>
<p><b>Przykład funkcji:</b></p>
<pre>def dodaj(a, b):
    return a + b

wynik = dodaj(5, 3)
print(wynik)</pre>
""", "type": "default"},
            {"title": "Wcięcia i struktura kodu", "content": """
<h2>Wcięcia i struktura kodu w Pythonie</h2>
<p>W Pythonie wcięcia są kluczowe dla określenia struktury kodu. Bloki kodu, takie jak pętle czy funkcje, są definiowane przez wcięcia.</p>
<p>Twoim zadaniem jest poprawienie błędów w wcięciach w poniższym kodzie.</p>
<p>Możesz kliknąć przycisk <b>Nowy przykład</b>, aby otrzymać inny kod do poprawienia.</p>
""", "type": "default"},
            {"title": "Zmienne vs Funkcje", "content": """
<h2>Zmienne vs Funkcje</h2>
<p>Zrozumienie różnicy między zmiennymi a funkcjami jest kluczowe w programowaniu.</p>
<p><b>Przykład:</b></p>
<pre>x = 5  # zmienna
def x():
    print("To jest funkcja")  # funkcja o nazwie x

print(x)</pre>
<p>Co się stanie, gdy uruchomisz ten kod?</p>
""", "type": "default"},
            {"title": "Operatory i porównania", "content": """
<h2>Operatory i porównania w Pythonie</h2>
<p>Operatory pozwalają na wykonywanie operacji na danych.</p>
<p><b>Przykład:</b></p>
<pre>a = 10
b = 5
print(a + b)  # dodawanie
print(a == b)  # porównanie</pre>
""", "type": "default"},
            {"title": "Praca z plikami", "content": """
<h2>Praca z plikami w Pythonie</h2>
<p>Python pozwala na łatwe odczytywanie i zapisywanie plików.</p>
<p><b>Przykład:</b></p>
<pre># Zapisywanie do pliku
with open('plik.txt', 'w') as f:
    f.write('Hello, world!')

# Odczytywanie z pliku
with open('plik.txt', 'r') as f:
    zawartość = f.read()
    print(zawartość)</pre>
""", "type": "default"},
            {"title": "Moduły i pakiety", "content": """
<h2>Moduły i pakiety w Pythonie</h2>
<p>Moduły pozwalają na organizowanie kodu w oddzielne pliki i ponowne jego wykorzystanie.</p>
<p><b>Przykład:</b></p>
<pre># W pliku module.py
def funkcja():
    print("To jest funkcja z modułu")

# W pliku main.py
import module
module.funkcja()</pre>
""", "type": "default"},
            {"title": "Klasy i obiekty", "content": """
<h2>Klasy i obiekty w Pythonie</h2>
<p>Python jest językiem obiektowym. Klasy pozwalają na tworzenie własnych typów danych.</p>
<p><b>Przykład:</b></p>
<pre>class Zwierze:
    def __init__(self, imie):
        self.imie = imie

    def przedstaw_sie(self):
        print("Jestem", self.imie)

pies = Zwierze("Burek")
pies.przedstaw_sie()</pre>
""", "type": "default"},
            {"title": "Dzielenie kodu na moduły", "content": """
<h2>Dzielenie kodu na moduły</h2>
<p>W tej lekcji nauczysz się, jak podzielić duży plik Pythona na mniejsze, bardziej zarządzalne moduły.</p>
<p>Dzięki temu Twój kod będzie bardziej czytelny i łatwiejszy w utrzymaniu.</p>
<p><b>Przykład:</b></p>
<pre># W pliku main.py
from module_a import funkcja_a
funkcja_a()

# W pliku module_a.py
def funkcja_a():
    print("To jest funkcja z modułu A")</pre>
""", "type": "default"},
            {"title": "Unikanie cyrkularnych importów", "content": """
<h2>Unikanie cyrkularnych importów</h2>
<p>Dowiesz się, czym są cyrkularne importy i jak ich unikać podczas strukturyzacji kodu w modułach.</p>
<p><b>Przykład cyrkularnego importu:</b></p>
<pre># module_a.py
from module_b import funkcja_b
def funkcja_a():
    funkcja_b()

# module_b.py
from module_a import funkcja_a
def funkcja_b():
    funkcja_a()</pre>
<p>Taki kod spowoduje błąd <code>ImportError</code>.</p>
<p><b>Rozwiązanie:</b></p>
<p>Przenieś wspólne funkcje do innego modułu lub użyj importów lokalnych.</p>
""", "type": "default"},
            # Możesz dodać więcej lekcji tutaj...
        ]

        # Wczytaj lekcje użytkownika
        user_lessons = self.load_user_lessons_from_file('user_lessons.json')

        self.lessons = default_lessons + user_lessons
        self.update_lesson_list()

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
            return []

    def save_user_lessons_to_file(self, filename):
        user_lessons = [lesson for lesson in self.lessons if lesson['type'] == 'user']
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(user_lessons, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można zapisać lekcji użytkownika:\n{e}")

    def update_lesson_list(self):
        self.lesson_list.clear()
        for lesson in self.lessons:
            self.lesson_list.addItem(lesson['title'])

    def load_lesson(self):
        current_row = self.lesson_list.currentRow()
        if current_row >= 0:
            lesson = self.lessons[current_row]
            self.lesson_content.setHtml(lesson['content'])
            self.code_editor.clear()
            if lesson['title'] == "Wcięcia i struktura kodu":
                self.load_new_indentation_example()
                self.new_example_button.show()
            else:
                self.new_example_button.hide()
        else:
            self.lesson_content.clear()
            self.code_editor.clear()
            self.new_example_button.hide()

    def add_new_lesson(self):
        title, ok = QInputDialog.getText(self, "Nowa lekcja", "Podaj tytuł lekcji:")
        if ok and title:
            content, ok = QInputDialog.getMultiLineText(self, "Nowa lekcja", "Wprowadź treść lekcji:")
            if ok:
                new_lesson = {
                    "title": title,
                    "content": content,
                    "type": "user"
                }
                self.lessons.append(new_lesson)
                self.update_lesson_list()
                self.save_user_lessons_to_file('user_lessons.json')

    def edit_lesson(self):
        current_row = self.lesson_list.currentRow()
        if current_row >= 0 and self.lessons[current_row]['type'] == 'user':
            lesson = self.lessons[current_row]
            new_title, ok = QInputDialog.getText(self, "Edytuj lekcję", "Edytuj tytuł lekcji:", text=lesson['title'])
            if ok and new_title:
                new_content, ok = QInputDialog.getMultiLineText(self, "Edytuj lekcję", "Edytuj treść lekcji:", text=lesson['content'])
                if ok:
                    lesson['title'] = new_title
                    lesson['content'] = new_content
                    self.update_lesson_list()
                    self.save_user_lessons_to_file('user_lessons.json')
        else:
            QMessageBox.warning(self, "Uwaga", "Możesz edytować tylko własne lekcje.")

    def delete_lesson(self):
        current_row = self.lesson_list.currentRow()
        if current_row >= 0 and self.lessons[current_row]['type'] == 'user':
            reply = QMessageBox.question(
                self, 
                'Usuń lekcję', 
                f"Czy na pewno chcesz usunąć lekcję '{self.lessons[current_row]['title']}'?", 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                del self.lessons[current_row]
                self.update_lesson_list()
                self.save_user_lessons_to_file('user_lessons.json')
        else:
            QMessageBox.warning(self, "Uwaga", "Możesz usuwać tylko własne lekcje.")

    # ---------------------------------------------
    #      Ładowanie nowych przykładów wcięć
    # ---------------------------------------------
    def load_new_indentation_example(self):
        if not hasattr(self, 'indentation_examples') or not self.indentation_examples:
            QMessageBox.warning(self, "Uwaga", "Brak dostępnych przykładów wcięć.")
            return
        example = random.choice(self.indentation_examples)
        self.code_editor.setPlainText(example)
        self.output_console.clear()
        self.status_bar.clearMessage()

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
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można wczytać przykładów z pliku:\n{e}")

    def select_examples_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Wybierz plik z przykładami", "", "Pliki tekstowe (*.txt);;Wszystkie pliki (*)"
        )
        if filename:
            self.load_examples_from_file(filename)
            QMessageBox.information(self, "Sukces", "Przykłady zostały wczytane.")

    # ---------------------------------------------
    #             Uruchamianie kodu
    # ---------------------------------------------
    def run_code(self):
        code = self.code_editor.toPlainText()
        error_message = self.analyze_code(code)
        if error_message:
            QMessageBox.critical(self, "Błąd składni", error_message)
            return

        # Sprawdzenie, czy jesteśmy w lekcji o wcięciach
        current_row = self.lesson_list.currentRow()
        if current_row >= 0 and self.lessons[current_row]['title'] == "Wcięcia i struktura kodu":
            QMessageBox.information(self, "Gratulacje", "Poprawnie poprawiłeś wcięcia!")
            return

        temp_file = "temp_code.py"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(code)

        self.output_console.clear()

        self.process = QProcess()
        self.process.setProgram("python")
        self.process.setArguments([temp_file])
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.data_ready)
        self.process.readyReadStandardError.connect(self.data_ready)
        self.process.finished.connect(lambda: os.remove(temp_file))
        self.process.start()

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

    # ---------------------------------------------
    #              Pokaż wskazówkę
    # ---------------------------------------------
    def show_hint(self):
        current_row = self.lesson_list.currentRow()
        if current_row >= 0:
            lesson_name = self.lessons[current_row]['title']
        else:
            lesson_name = "Wprowadzenie"

        hints = {
            "Wprowadzenie": "Spróbuj użyć funkcji print(), aby wyświetlić tekst.",
            "Zmienne": "Pamiętaj, że zmienne nie muszą być deklarowane z typem danych.",
            "Pętle": "Użyj pętli for z funkcją range().",
            "Funkcje": "Definiuj funkcję za pomocą słowa kluczowego def.",
            "Wcięcia i struktura kodu": "Upewnij się, że bloki kodu są poprawnie wcięte.",
            "Zmienne vs Funkcje": "Zwróć uwagę na różnicę między przypisaniem wartości a wywołaniem funkcji.",
            "Operatory i porównania": "Pamiętaj, że '=' służy do przypisania, a '==' do porównania."
        }

        hint = hints.get(lesson_name, "Brak wskazówki dla tej lekcji.")
        QMessageBox.information(self, "Wskazówka", hint)

    # ---------------------------------------------
    #       Uruchamianie kodu krok po kroku
    # ---------------------------------------------
    def run_step_by_step(self):
        code = self.code_editor.toPlainText()
        self.lines = code.split('\n')
        self.current_line = 0
        self.output_console.clear()
        self.run_next_line()

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
                return
            self.current_line += 1
            # Podświetlenie aktualnej linii
            cursor = self.code_editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            for _ in range(self.current_line):
                cursor.movePosition(QTextCursor.MoveOperation.Down)
            self.code_editor.setTextCursor(cursor)
        else:
            self.output_console.append("Wykonano cały kod.")

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

    # ---------------------------------------------
    #                O programie
    # ---------------------------------------------
    def show_about(self):
        QMessageBox.information(self, "O programie", "Python Tutor\nWersja 1.0")

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
                painter.drawText(0, top, self.line_number_area.width() - 5, self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:
            cursor = self.textCursor()
            cursor.insertText('\n' + self.get_indentation())
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
