# src/code_editor.py

import os
import uuid
import shutil
import subprocess
import atexit
import re
import ast

from PyQt6.QtWidgets import (
    QPlainTextEdit, QListWidget, QListWidgetItem, QTextEdit,
    QDialog, QHBoxLayout, QLineEdit, QLabel, QMessageBox, QApplication
)
from PyQt6.QtGui import (
    QFont, QColor, QTextFormat, QPainter, QTextCursor, QIcon, QTextCharFormat
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QRegularExpression, QRect
)

import jedi

# Importuj potrzebne klasy
from line_number_area import LineNumberArea
from syntax_highlighter import GenericHighlighter
from linter_worker import LinterWorker


class CodeEditor(QPlainTextEdit):
    """
    Główna klasa edytora kodu z funkcjami takimi jak:
    - Numeracja linii
    - Podświetlanie składni
    - Podświetlanie bieżącej linii
    - Breakpointy
    - Linter
    - Autouzupełnianie
    - Uruchamianie skryptu (F5)
    """
    symbols_updated = pyqtSignal(dict)  # Sygnał zaktualizowanych symboli

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Consolas", 12))
        self.highlighter = GenericHighlighter(self.document(), language='python')

        # Inicjalizacja zmiennych
        self.breakpoints = set()
        self.file_path = None
        self.is_linting = False
        self.previous_errors = []

        # Ścieżka do folderu tymczasowego
        self.temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)  # Tworzy folder temp, jeśli nie istnieje

        # Rejestracja funkcji czyszczącej dla plików tymczasowych
        atexit.register(self.cleanup_temp_files)

        # Tworzenie obszaru numerów linii
        self.line_number_area = LineNumberArea(self)
        self.line_number_area.clicked.connect(self.handle_line_number_clicked)

        # Podłączenie sygnałów
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.textChanged.connect(self.on_text_changed)

        # Panel symboli
        self.symbols_update_timer = QTimer()
        self.symbols_update_timer.setInterval(500)  # 500 ms
        self.symbols_update_timer.setSingleShot(True)
        self.symbols_update_timer.timeout.connect(self.update_symbols_panel)

        # Wątek lintera
        self.linter_thread = None
        self.linter_worker = None

        # Ustawienia domyślne
        self.settings = {
            'clean_paste': True,
            'smart_indent': True,
            'confirm_delete': True,
            'theme': 'Jasny',
            'font_size': 12,
            'auto_save': True,
            'focus_mode': False,
            'autocomplete_on_demand': False,
            'font_family': 'Consolas',
        }

        # Autouzupełnianie
        self.completion_list = QListWidget(self)
        self.completion_list.setWindowFlags(Qt.WindowType.ToolTip)
        self.completion_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.completion_list.itemClicked.connect(self.complete_text)
        self.completion_list.hide()

        # Dodajemy event filter
        self.installEventFilter(self)

        # Ikony dla autouzupełniania
        self.function_icon = QIcon('assets/icons/function.png')
        self.class_icon = QIcon('assets/icons/class.png')

        # Dodatkowe zmienne do podświetlania słów
        self.extra_selections = []
        self.word_highlight_selections = []

        # Podłączenie sygnału zmiany zaznaczenia
        self.selectionChanged.connect(self.highlight_word_occurrences)

        # Aktualizacja obszaru numerów linii i podświetlenie bieżącej linii
        self.update_line_number_area_width(0)
        self.highlight_current_line()

        # Timer do autouzupełniania
        self.completion_timer = QTimer()
        self.completion_timer.setSingleShot(True)
        self.completion_timer.setInterval(300)
        self.completion_timer.timeout.connect(self.show_completions)

    def cleanup_temp_files(self):
        """
        Usuwa folder temp wraz z wszystkimi plikami tymczasowymi.
        """
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                print(f"Usunięto folder tymczasowy: {self.temp_dir}")
            except Exception as e:
                print(f"Nie udało się usunąć folderu {self.temp_dir}: {e}")

    # ---------------------- Event Handlers ----------------------

    def eventFilter(self, obj, event):
        """
        Filtruje zdarzenia myszy, aby ukryć listę podpowiedzi autouzupełniania, jeśli kliknięto poza nią.
        """
        if event.type() == event.Type.MouseButtonPress:
            if self.completion_list.isVisible():
                if not self.completion_list.geometry().contains(self.mapToGlobal(event.position().toPoint())):
                    self.completion_list.hide()
        return super().eventFilter(obj, event)

    def focusOutEvent(self, event):
        """
        Ukrywa listę podpowiedzi autouzupełniania, gdy edytor traci fokus.
        """
        super().focusOutEvent(event)
        if self.completion_list.isVisible():
            self.completion_list.hide()

    # ---------------------- Bookmark and Breakpoint Handlers ----------------------

    def toggle_bookmark(self, block_number):
        """
        Przełącza zakładkę (bookmark) w danej linii.
        """
        if not hasattr(self, 'bookmarks'):
            self.bookmarks = set()
        if block_number in self.bookmarks:
            self.bookmarks.remove(block_number)
        else:
            self.bookmarks.add(block_number)
        self.highlight_current_line()
        self.line_number_area.update()

    # ---------------------- Settings and Theme Handlers ----------------------

    def apply_settings(self, settings):
        """
        Zastosuj ustawienia do edytora.
        """
        self.settings = settings

        # Aktualizacja rozmiaru i rodziny czcionki
        font = QFont(self.settings.get('font_family', 'Consolas'), self.settings.get('font_size', 12))
        self.setFont(font)

        # Aktualizacja motywu
        self.apply_theme(self.settings.get('theme', 'Jasny'))

    def apply_theme(self, theme):
        """
        Zastosuj wybrany motyw do edytora.
        """
        if theme == 'Ciemny':
            self.setStyleSheet("background-color: #2b2b2b; color: #f8f8f2;")
            self.highlighter.theme = 'monokai'  # Możesz zmienić na inny ciemny motyw
        elif theme == 'Monokai':
            self.setStyleSheet("background-color: #272822; color: #f8f8f2;")
            self.highlighter.theme = 'monokai'
        elif theme == 'Solarized Light':
            self.setStyleSheet("background-color: #fdf6e3; color: #657b83;")
            self.highlighter.theme = 'solarized-light'
        elif theme == 'Solarized Dark':
            self.setStyleSheet("background-color: #002b36; color: #839496;")
            self.highlighter.theme = 'solarized-dark'
        else:
            self.setStyleSheet("")  # Domyślny jasny motyw
            self.highlighter.theme = 'friendly'

        self.highlighter.load_pygments_styles()
        self.highlighter.rehighlight()
        self.update()

    # ---------------------- Paste Event Handler ----------------------

    def pasteEvent(self, event):
        """
        Obsługa wklejania z możliwością czyszczenia formatowania.
        """
        if self.settings.get('clean_paste', True):
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            cleaned_text = '\n'.join(line.strip() for line in text.split('\n'))
            self.insertPlainText(cleaned_text)
        else:
            super().pasteEvent(event)

    # ---------------------- Key Press Event Handler ----------------------

    def keyPressEvent(self, event):
        """
        Obsługa zdarzeń klawiatury, w tym inteligentnego wcięcia i autouzupełniania.
        """
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.settings.get('smart_indent', True):
                cursor = self.textCursor()
                cursor.select(QTextCursor.SelectionType.LineUnderCursor)
                current_line = cursor.selectedText()

                # Pobierz ilość spacji na początku linii
                indentation = re.match(r'\s*', current_line).group()

                # Jeśli linia kończy się dwukropkiem, dodaj dodatkowe wcięcie
                if current_line.rstrip().endswith(':'):
                    indentation += '    '

                # Wstaw nową linię
                super().keyPressEvent(event)

                # Dodaj wcięcie do nowej linii
                cursor = self.textCursor()
                cursor.insertText(indentation)
                return
            else:
                # Jeśli inteligentne wcięcie jest wyłączone, przetwórz Enter normalnie
                super().keyPressEvent(event)
                return
        elif event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            if self.settings.get('confirm_delete', True):
                if self.textCursor().hasSelection():
                    reply = QMessageBox.question(
                        self, 'Potwierdzenie Usunięcia',
                        'Czy na pewno chcesz usunąć zaznaczony fragment?',
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    if reply != QMessageBox.StandardButton.Yes:
                        event.ignore()
                        return
        elif event.key() == Qt.Key.Key_F and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.show_find_dialog()
            return
        elif event.key() == Qt.Key.Key_Space and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Wywołaj autouzupełnianie na żądanie
            self.show_completions()
            return

        # Obsługa autouzupełniania
        if self.completion_list.isVisible():
            if event.key() == Qt.Key.Key_Tab:
                self.accept_completion()
                return
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.accept_completion()
                return
            elif event.key() == Qt.Key.Key_Escape:
                self.completion_list.hide()
                return

        # Przetwórz pozostałe klawisze normalnie
        super().keyPressEvent(event)

        # Inicjalizacja autouzupełniania tylko dla znaków identyfikatorów
        if event.text().isidentifier():
            if self.settings.get('autocomplete', True) and not self.settings.get('autocomplete_on_demand', False):
                self.completion_timer.start()

    def accept_completion(self):
        """
        Akceptuje wybraną propozycję autouzupełniania.
        """
        selected_item = self.completion_list.currentItem()
        if selected_item:
            self.complete_text(selected_item)

    # ---------------------- Line Number Area Handlers ----------------------

    def handle_line_number_clicked(self, block_number, modifiers):
        """
        Obsługuje kliknięcia na obszarze numerów linii.
        """
        if modifiers == Qt.KeyboardModifier.NoModifier:
            # Przenosimy kursor do wybranej linii bez zaznaczania
            cursor = self.textCursor()
            block = self.document().findBlockByNumber(block_number)
            if block.isValid():
                cursor.setPosition(block.position())
                self.setTextCursor(cursor)
                self.centerCursor()
        elif modifiers & Qt.KeyboardModifier.ControlModifier:
            # Przełączamy breakpoint
            self.toggle_breakpoint(block_number)
        elif modifiers & Qt.KeyboardModifier.ShiftModifier:
            # Przełączamy zakładkę
            self.toggle_bookmark(block_number)

    def toggle_breakpoint(self, block_number):
        """
        Przełącza breakpoint w danej linii.
        """
        if block_number in self.breakpoints:
            self.breakpoints.remove(block_number)
        else:
            self.breakpoints.add(block_number)
        self.highlight_current_line()
        self.line_number_area.update()

    def line_number_area_width(self):
        """
        Oblicza szerokość obszaru numerów linii.
        """
        digits = len(str(max(1, self.blockCount())))
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def line_number_area_paint_event(self, event):
        """
        Rysuje numery linii oraz breakpointy i zakładki w obszarze numerów linii.
        """
        painter = QPainter(self.line_number_area)
        # Ustawienie tła
        if self.settings.get('theme', 'Jasny') == 'Ciemny':
            painter.fillRect(event.rect(), QColor(43, 43, 43))  # Ciemne tło
        else:
            painter.fillRect(event.rect(), QColor(240, 240, 240))  # Jasne tło

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("black") if self.settings.get('theme', 'Jasny') == 'Jasny' else QColor("white"))
                # Poprawione pozycjonowanie tekstu
                painter.drawText(0, int(top), self.line_number_area.width() - 5, self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, number)

                # Rysowanie breakpointu
                if block_number in self.breakpoints:
                    radius = 6
                    x = 4
                    y = int(top + (self.fontMetrics().height() - radius) / 2)
                    painter.setBrush(QColor(255, 0, 0))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(x, y, radius, radius)

                # Rysowanie zakładki
                if hasattr(self, 'bookmarks') and block_number in self.bookmarks:
                    x = 4
                    y = int(top + (self.fontMetrics().height() - 8) / 2)
                    painter.setBrush(QColor(0, 0, 255))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawRect(x, y, 8, 8)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def update_line_number_area_width(self, _):
        """
        Aktualizuje szerokość obszaru numerów linii.
        """
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """
        Aktualizuje obszar numerów linii podczas przewijania.
        """
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        """
        Obsługa zmiany rozmiaru okna.
        """
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    # ---------------------- Highlighting Handlers ----------------------

    def highlight_current_line(self):
        """
        Podświetla bieżącą linię, breakpointy i zakładki.
        """
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            line_color = QColor(232, 242, 254) if self.settings.get('theme', 'Jasny') == 'Jasny' else QColor(50, 50, 50)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        # Dodaj breakpointy
        for line in self.breakpoints:
            block = self.document().findBlockByNumber(line)
            if block.isValid():
                cursor = QTextCursor(block)
                selection = QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format.setBackground(QColor(255, 200, 200))  # Delikatny czerwony
                extra_selections.append(selection)

        # Dodaj zakładki
        if hasattr(self, 'bookmarks'):
            for line in self.bookmarks:
                block = self.document().findBlockByNumber(line)
                if block.isValid():
                    cursor = QTextCursor(block)
                    selection = QTextEdit.ExtraSelection()
                    selection.cursor = cursor
                    selection.format.setBackground(QColor(200, 200, 255))  # Delikatny niebieski
                    extra_selections.append(selection)

        self.extra_selections = extra_selections
        self.setExtraSelections(self.extra_selections + self.word_highlight_selections)

    def highlight_word_occurrences(self):
        """
        Podświetla wszystkie wystąpienia wybranego słowa.
        """
        cursor = self.textCursor()
        selected_text = cursor.selectedText()

        if selected_text and not selected_text.isspace() and len(selected_text.split()) == 1:
            word = selected_text
            self.word_highlight_selections = []
            highlight_format = QTextCharFormat()
            highlight_format.setBackground(QColor('yellow'))

            # Szukanie wszystkich wystąpień słowa
            pattern = QRegularExpression(r'\b{}\b'.format(re.escape(word)))
            start = 0
            while True:
                match = pattern.match(self.toPlainText(), start)
                if not match.hasMatch():
                    break
                cursor = self.textCursor()
                cursor.setPosition(match.capturedStart())
                cursor.setPosition(match.capturedEnd(), QTextCursor.MoveMode.KeepAnchor)
                selection = QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format = highlight_format
                self.word_highlight_selections.append(selection)
                start = match.capturedEnd()

            # Aktualizacja podświetleń
            self.setExtraSelections(self.extra_selections + self.word_highlight_selections)
        else:
            # Usunięcie wcześniejszych podświetleń
            self.word_highlight_selections = []
            self.setExtraSelections(self.extra_selections)

    # ---------------------- Text Change Handler ----------------------

    def on_text_changed(self):
        """
        Reakcja na zmianę tekstu - uruchamia timer aktualizacji symboli.
        """
        self.symbols_update_timer.start()

    # ---------------------- Linter Handlers ----------------------

    def run_linter(self):
        """
        Uruchamia linter w osobnym wątku.
        """
        if self.is_linting:
            return

        if self.linter_thread is not None:
            self.linter_thread.quit()
            self.linter_thread.wait()
            self.linter_thread = None

        self.is_linting = True
        code = self.toPlainText()

        parent_window = self.window()
        flake8_config = getattr(parent_window, 'flake8_config', None)
        repo_path = getattr(parent_window, 'git_repo_path', '.')

        self.linter_worker = LinterWorker(code, flake8_config, repo_path)
        self.linter_thread = QThread()
        self.linter_worker.moveToThread(self.linter_thread)
        self.linter_thread.started.connect(self.linter_worker.run)
        self.linter_worker.finished.connect(self.on_linter_finished)
        self.linter_worker.error.connect(self.on_linter_error)
        self.linter_worker.finished.connect(self.linter_thread.quit)
        self.linter_worker.finished.connect(self.linter_worker.deleteLater)
        self.linter_thread.finished.connect(self.linter_thread.deleteLater)
        self.linter_thread.finished.connect(self.cleanup_linter_thread)
        self.linter_thread.start()

    def cleanup_linter_thread(self):
        """
        Czyszczenie wątku lintera po zakończeniu.
        """
        self.linter_thread = None

    def on_linter_finished(self, errors):
        """
        Obsługa zakończenia lintera.
        """
        self.is_linting = False

        parent_window = self.window()
        if parent_window and hasattr(parent_window, 'output'):
            parent_window.output.clear()
            if errors:
                parent_window.output.appendPlainText(">>> Wyniki Lintera:")
                for line_num, message in errors:
                    parent_window.output.appendPlainText(f"Linia {line_num + 1}: {message}")
            else:
                parent_window.output.appendPlainText(">>> Brak błędów wykrytych przez linter.")

        if errors == self.previous_errors:
            return
        self.previous_errors = errors

        # Aktualizacja błędów w highlighterze
        self.highlighter.error_lines = {line: msg for line, msg in errors}
        self.highlighter.rehighlight()

    def on_linter_error(self, error_message):
        """
        Obsługa błędów lintera.
        """
        self.is_linting = False
        self.linter_thread = None
        parent_window = self.window()
        if parent_window and hasattr(parent_window, 'output'):
            parent_window.output.clear()
            parent_window.output.appendPlainText(f">>> Błąd lintera: {error_message}")

    # ---------------------- Symbol Panel Handlers ----------------------

    def update_symbols_panel(self):
        """
        Aktualizacja panelu symboli (funkcje, klasy).
        """
        code = self.toPlainText()
        symbols = self.extract_symbols(code)
        self.symbols_updated.emit(symbols)

    def extract_symbols(self, code):
        """
        Ekstrakcja symboli z kodu za pomocą modułu ast.
        """
        functions = []
        classes = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append((node.name, node.lineno - 1))
                elif isinstance(node, ast.ClassDef):
                    classes.append((node.name, node.lineno - 1))
        except SyntaxError:
            pass
        return {'functions': functions, 'classes': classes}

    # ---------------------- Find Dialog Handlers ----------------------

    def show_find_dialog(self):
        """
        Wyświetla dialog do wyszukiwania tekstu.
        """
        if not hasattr(self, 'find_dialog'):
            self.find_dialog = QDialog(self)
            self.find_dialog.setWindowTitle("Znajdź")
            layout = QHBoxLayout()
            self.find_input = QLineEdit()
            self.find_input.returnPressed.connect(self.find_next)
            layout.addWidget(QLabel("Znajdź:"))
            layout.addWidget(self.find_input)
            self.find_dialog.setLayout(layout)
        self.find_dialog.show()
        self.find_dialog.activateWindow()
        self.find_input.setFocus()

    def find_next(self):
        """
        Znajduje następne wystąpienie wyszukiwanego tekstu.
        """
        search_text = self.find_input.text()
        if not search_text:
            return
        cursor = self.textCursor()
        regex = QRegularExpression(search_text)
        found = self.find(regex)
        if not found:
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.setTextCursor(cursor)
            found = self.find(regex)
        if not found:
            QMessageBox.information(self, "Znajdź", f"Nie znaleziono: {search_text}")

    # ---------------------- Autocompletion Handlers ----------------------

    def show_completions(self):
        """
        Wyświetla listę podpowiedzi autouzupełniania na podstawie bieżącej pozycji kursora.
        """
        try:
            cursor = self.textCursor()
            # Zdobądź pozycję kursora
            line = cursor.blockNumber() + 1  # Linijki są 1-based w jedi
            column = cursor.positionInBlock()  # Kolumny są 0-based w jedi

            # Tworzenie unikalnej nazwy pliku tymczasowego
            temp_filename = f"temp_script_{uuid.uuid4().hex}.py"
            temp_filepath = os.path.join(self.temp_dir, temp_filename)

            # Zapisz bieżący kod do pliku tymczasowego
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                f.write(self.toPlainText())

            # Użyj ścieżki z atrybutu klasy
            script = jedi.Script(code=self.toPlainText(), path=temp_filepath)
            completions = script.complete(line, column)

            if completions:
                self.completion_list.clear()
                for comp in completions:
                    item = QListWidgetItem(comp.name)
                    item.setToolTip(comp.description)
                    if comp.type == 'function':
                        item.setIcon(self.function_icon)
                    elif comp.type == 'class':
                        item.setIcon(self.class_icon)
                    self.completion_list.addItem(item)

                # Pozycjonowanie listy
                cursor_rect = self.cursorRect()
                list_pos = self.mapToGlobal(cursor_rect.bottomRight())
                # Dopasuj pozycję, aby nie wykraczać poza ekran
                screen_rect = QApplication.primaryScreen().availableGeometry()
                if list_pos.x() + self.completion_list.width() > screen_rect.width():
                    list_pos.setX(screen_rect.width() - self.completion_list.width())
                if list_pos.y() + self.completion_list.height() > screen_rect.height():
                    list_pos.setY(list_pos.y() - self.completion_list.height() - cursor_rect.height())
                self.completion_list.move(list_pos)
                self.completion_list.resize(300, min(150, self.completion_list.sizeHintForRow(0) * len(completions) + 2))
                self.completion_list.show()
            else:
                self.completion_list.hide()
        except Exception as e:
            print(f"Autouzupełnianie błędów: {e}")
            self.completion_list.hide()

    def complete_text(self, item):
        """
        Wstawia wybraną propozycję autouzupełniania do edytora.
        """
        cursor = self.textCursor()
        # Usuń tekst przed kursorem do najbliższego nie-alfanumerycznego znaku
        while cursor.positionInBlock() > 0:
            cursor.movePosition(QTextCursor.MoveOperation.PreviousCharacter, QTextCursor.MoveMode.KeepAnchor)
            if not cursor.selectedText()[-1].isalnum() and cursor.selectedText()[-1] != '_':
                cursor.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.MoveAnchor)
                break
        cursor.removeSelectedText()
        cursor.insertText(item.text())
        self.setTextCursor(cursor)
        self.completion_list.hide()

    # ---------------------- Run Script Handler ----------------------

    def run_script(self):
        """
        Uruchamia napisany przez użytkownika skrypt w osobnym procesie.
        Tworzy unikalne pliki tymczasowe w folderze temp i usuwa je po zakończeniu.
        """
        try:
            # Generowanie unikalnej nazwy pliku tymczasowego
            temp_filename = f"temp_run_{uuid.uuid4().hex}.py"
            temp_filepath = os.path.join(self.temp_dir, temp_filename)

            # Zapisz bieżący kod do pliku tymczasowego
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                f.write(self.toPlainText())
            print(f"Zapisano skrypt do pliku tymczasowego: {temp_filepath}")

            # Uruchom skrypt w osobnym procesie
            process = subprocess.Popen(
                ['python', temp_filepath],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Odczytaj wyjście i błędy
            stdout, stderr = process.communicate()

            # Wyświetl wyniki w oknie output (zakładamy, że istnieje w parent_window)
            parent_window = self.window()
            if parent_window and hasattr(parent_window, 'output'):
                parent_window.output.clear()
                if stdout:
                    parent_window.output.appendPlainText(">>> Wyjście:")
                    parent_window.output.appendPlainText(stdout)
                if stderr:
                    parent_window.output.appendPlainText(">>> Błędy:")
                    parent_window.output.appendPlainText(stderr)
                if not stdout and not stderr:
                    parent_window.output.appendPlainText(">>> Skrypt zakończył się bez wyjścia.")
        except Exception as e:
            print(f"Błąd podczas uruchamiania skryptu: {e}")
            parent_window = self.window()
            if parent_window and hasattr(parent_window, 'output'):
                parent_window.output.clear()
                parent_window.output.appendPlainText(f">>> Błąd uruchamiania skryptu: {e}")
        finally:
            # Usunięcie pliku tymczasowego po zakończeniu
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                    print(f"Usunięto plik tymczasowy: {temp_filepath}")
                except Exception as e:
                    print(f"Nie udało się usunąć pliku {temp_filepath}: {e}")

    # ---------------------- Autocompletion Handlers ----------------------

    # Reszta metod pozostaje bez zmian

