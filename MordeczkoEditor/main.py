import sys
import os
import re
import subprocess
import bisect
import ast
import logging
from functools import wraps
import io
import contextlib
import git
import unittest
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit, QWidget, QVBoxLayout,
    QHBoxLayout, QDialog, QCheckBox, QLabel, QComboBox, QSpinBox,
    QPushButton, QFileDialog, QInputDialog, QMessageBox, QListWidget,
    QListWidgetItem, QSplitter, QTabWidget, QToolTip
)
from PyQt6.QtGui import (
    QFont, QColor, QTextFormat, QPainter, QSyntaxHighlighter,
    QTextCharFormat, QTextCursor, QAction, QKeySequence, QIcon
)
from PyQt6.QtCore import (
    Qt, QRect, QProcess, pyqtSignal, QSize, QTimer, QObject, QThread,
    QRegularExpression
)
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.styles import get_style_by_name
from PyQt6.QtWidgets import QTextEdit
import jedi

# Konfiguracja logowania
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    filemode='w'
)

class LinterWorker(QObject):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, code, flake8_config, repo_path):
        super().__init__()
        self.code = code
        self.flake8_config = flake8_config
        self.repo_path = repo_path

    def run(self):
        try:
            temp_file = "temp_script.py"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(self.code)

            args = ['flake8', temp_file]
            if self.flake8_config:
                args += ['--config', self.flake8_config]
            result = subprocess.run(args, capture_output=True, text=True, cwd=self.repo_path)
            output = result.stdout
            errors = []
            for line in output.strip().split('\n'):
                if line:
                    match = re.match(rf"{re.escape(temp_file)}:(\d+):\d+:\s+(.*)", line)
                    if match:
                        line_num = int(match.group(1)) - 1
                        message = match.group(2)
                        errors.append((line_num, message))
            self.finished.emit(errors)
        except Exception as e:
            self.error.emit(str(e))

class LineNumberArea(QWidget):
    clicked = pyqtSignal(int)

    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            y = event.position().y()
            block = self.code_editor.firstVisibleBlock()
            block_number = block.blockNumber()
            top = int(self.code_editor.blockBoundingGeometry(block).translated(self.code_editor.contentOffset()).top())
            bottom = top + int(self.code_editor.blockBoundingRect(block).height())

            while block.isValid() and top <= y:
                if block.isVisible() and bottom >= y:
                    self.clicked.emit(block_number)
                    break
                block = block.next()
                top = bottom
                bottom = top + int(self.code_editor.blockBoundingRect(block).height())
                block_number += 1

class GenericHighlighter(QSyntaxHighlighter):
    def __init__(self, document, language='python'):
        super().__init__(document)
        self.formats = {}
        self.error_format = QTextCharFormat()
        self.error_format.setUnderlineColor(QColor("red"))
        self.error_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
        self.error_lines = {}  # Słownik z komunikatami błędów

        for token, style in self.get_pygments_styles().items():
            qt_format = QTextCharFormat()
            if style:
                style_parts = style.split()
                for part in style_parts:
                    if re.match(r'^#[0-9A-Fa-f]{6}$', part):
                        qt_format.setForeground(QColor(part))
                    elif part.lower() == 'bold':
                        qt_format.setFontWeight(QFont.Weight.Bold)
                    elif part.lower() == 'italic':
                        qt_format.setFontItalic(True)
            self.formats[token] = qt_format

        self.set_language(language)

    def get_pygments_styles(self):
        style = get_style_by_name('friendly')  # Styl z jasnym tłem
        return style.styles

    def set_language(self, language):
        self.lexer = get_lexer_by_name(language)
        self.rehighlight()

    def highlightBlock(self, text):
        block_number = self.currentBlock().blockNumber()
        if block_number in self.error_lines:
            self.setFormat(0, len(text), self.error_format)

        current_position = 0
        for token, content in lex(text, self.lexer):
            if token in self.formats:
                length = len(content)
                self.setFormat(current_position, length, self.formats[token])
            else:
                default_format = QTextCharFormat()
                self.setFormat(current_position, len(content), default_format)
            current_position += len(content)

class CodeEditor(QPlainTextEdit):
    symbols_updated = pyqtSignal(dict)  # Sygnał zaktualizowanych funkcji i klas

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Consolas", 12))

        # Inicjalizacja zmiennych
        self.breakpoints = set()
        self.file_path = None
        self.is_linting = False
        self.previous_errors = []

        # Highlighter
        self.highlighter = GenericHighlighter(self.document(), language='python')

        # Tworzenie LineNumberArea
        self.line_number_area = LineNumberArea(self)
        self.line_number_area.clicked.connect(self.toggle_breakpoint)

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

        # Dla funkcji wyszukiwania
        self.find_dialog = None
        self.last_search_text = ""

        # Ustawienia domyślne
        self.settings = {
            'clean_paste': True,
            'smart_indent': True,
            'confirm_delete': True,
            'theme': 'Jasny',
            'font_size': 12,
            'auto_save': True,
            'focus_mode': False,
        }

        # Autouzupełnianie
        self.completion_list = QListWidget(self)
        self.completion_list.setWindowFlags(Qt.WindowType.Popup)
        self.completion_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.completion_list.itemClicked.connect(self.complete_text)
        self.completion_list.hide()

        # Załaduj ikony raz
        self.function_icon = QIcon('assets/icons/function.png')
        self.class_icon = QIcon('assets/icons/class.png')

        self.setMouseTracking(True)  # Włącz śledzenie ruchu myszy
        self.setToolTipDuration(0)  # Niech ToolTip pozostaje widoczny, dopóki użytkownik nie opuści linii

        # Update line number area
        self.update_line_number_area_width(0)
        self.highlight_current_line()

        # Debounce Timer dla Autouzupełniania
        self.completion_timer = QTimer()
        self.completion_timer.setSingleShot(True)
        self.completion_timer.setInterval(300)  # 300 ms opóźnienia
        self.completion_timer.timeout.connect(self.show_completions)

    def apply_settings(self, settings):
        self.settings = settings

        # Aktualizacja rozmiaru czcionki
        font = self.font()
        font.setPointSize(self.settings.get('font_size', 12))
        self.setFont(font)

        # Aktualizacja motywu
        self.highlighter.set_language('python')  # Możesz dodać obsługę innych języków

        self.update()

    def pasteEvent(self, event):
        if self.settings.get('clean_paste', True):
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            # Usuń nadmiarowe spacje na początku każdej linii
            cleaned_text = '\n'.join(line.strip() for line in text.split('\n'))
            self.insertPlainText(cleaned_text)
        else:
            super().pasteEvent(event)

    def keyPressEvent(self, event):
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

                super().keyPressEvent(event)

                # Dodaj wcięcie do nowej linii
                cursor = self.textCursor()
                cursor.insertText(indentation)
                return
        elif event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            if self.settings.get('confirm_delete', True):
                reply = QMessageBox.question(self, 'Potwierdzenie Usunięcia',
                                             'Czy na pewno chcesz usunąć ten fragment?',
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                             QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes:
                    event.ignore()
                    return
        elif event.key() == Qt.Key.Key_F and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.show_find_dialog()
            return

        # Obsługa autouzupełniania przed wywołaniem super()
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

        super().keyPressEvent(event)

        # Uruchomienie opóźnionego autouzupełniania
        if event.text().isidentifier() or event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            # Opóźnienie na 2000ms (2 sekundy), zmień wedle potrzeby
            self.completion_timer.start(2000)  # Opóźnienie wywołania autouzupełniania na 2 sekundy

    def accept_completion(self):
        selected_item = self.completion_list.currentItem()
        if selected_item:
            self.complete_text(selected_item)

    def toggle_breakpoint(self, block_number):
        if block_number in self.breakpoints:
            self.breakpoints.remove(block_number)
        else:
            self.breakpoints.add(block_number)
        self.highlight_current_line()
        self.line_number_area.update()

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
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        if self.settings.get('theme', 'Jasny') == 'Ciemny':
            painter.fillRect(event.rect(), QColor(43, 43, 43))  # Ciemne tło
        else:
            painter.fillRect(event.rect(), QColor(240, 240, 240))  # Jasne tło dla numerów linii

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                if block_number in self.breakpoints:
                    painter.setPen(QColor(255, 0, 0))  # Czerwony kolor dla breakpointów
                    painter.drawEllipse(2, top + 2, 10, 10)
                else:
                    painter.setPen(QColor("black") if self.settings.get('theme', 'Jasny') == 'Jasny' else QColor("white"))
                    painter.drawText(0, top, self.line_number_area.width() - 5, self.fontMetrics().height(),
                                     Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            line_color = QColor(232, 242, 254) if self.settings.get('theme', 'Jasny') == 'Jasny' else QColor(50, 50, 50)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        # Dodaj breakpointy jako dodatkowe selekcje
        for line in self.breakpoints:
            block = self.document().findBlockByNumber(line)
            if block.isValid():
                cursor = QTextCursor(block)
                selection = QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format.setBackground(QColor(255, 230, 230))  # Jasnoczerwone tło dla breakpointu
                extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def on_text_changed(self):
        self.symbols_update_timer.start()  # Restart timera aktualizacji symboli

    def run_linter(self):
        """Uruchamia linter na obecnym kodzie w osobnym wątku."""
        if self.is_linting:
            return  # Nie uruchamiaj nowego lintera, jeśli poprzedni jeszcze działa

        # Zatrzymaj poprzedni wątek lintera, jeśli istnieje
        if self.linter_thread is not None:
            self.linter_thread.quit()
            self.linter_thread.wait()
            self.linter_thread = None

        self.is_linting = True  # Ustaw flagę na True
        code = self.toPlainText()

        # Poprawione odnajdywanie MainWindow
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
        """Czyszczenie referencji do linter_thread po jego zakończeniu."""
        self.linter_thread = None

    def on_linter_finished(self, errors):
        self.is_linting = False  # Resetuj flagę

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
            return  # Nie aktualizuj highlightera, jeśli błędy się nie zmieniły
        self.previous_errors = errors  # Zapisz nowe błędy

        # Aktualizacja błędów w highlighterze
        self.highlighter.error_lines = {line: msg for line, msg in errors}
        self.highlighter.rehighlight()

    def on_linter_error(self, error_message):
        self.is_linting = False  # Resetuj flagę
        self.linter_thread = None
        parent_window = self.window()
        if parent_window and hasattr(parent_window, 'output'):
            parent_window.output.clear()
            parent_window.output.appendPlainText(f">>> Błąd lintera: {error_message}")

    def update_symbols_panel(self):
        code = self.toPlainText()
        symbols = self.extract_symbols(code)
        self.symbols_updated.emit(symbols)

    def extract_symbols(self, code):
        """Ekstrakcja symboli funkcji i klas z kodu za pomocą modułu ast."""
        functions = []
        classes = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # ast.lineno jest 1-based, QTextDocument blocks are 0-based
                    functions.append((node.name, node.lineno - 1))
                elif isinstance(node, ast.ClassDef):
                    classes.append((node.name, node.lineno - 1))
        except SyntaxError:
            # Możesz tutaj obsłużyć błędy składniowe, jeśli to konieczne
            pass
        return {'functions': functions, 'classes': classes}

    def get_line_number(self, position, line_start_positions):
        """Zwraca numer linii na podstawie pozycji w kodzie."""
        index = bisect.bisect_right(line_start_positions, position) - 1
        return index

    # Funkcja wyszukiwania
    def show_find_dialog(self):
        if not self.find_dialog:
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
        search_text = self.find_input.text()
        if not search_text:
            return
        # Rozpocznij od bieżącej pozycji kursora
        cursor = self.textCursor()

        if self.last_search_text != search_text:
            # Nowe wyszukiwanie, zacznij od początku
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.setTextCursor(cursor)
            self.last_search_text = search_text

        # Używamy QRegularExpression do wyszukiwania
        regex = QRegularExpression(search_text)

        # Znajdź kolejne wystąpienie
        found = self.find(regex)

        if not found:
            # Powtórz od początku
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.setTextCursor(cursor)
            found = self.find(regex)

        if not found:
            QMessageBox.information(self, "Znajdź", f"Nie znaleziono: {search_text}")

    def mouseMoveEvent(self, event):
        cursor = self.cursorForPosition(event.position().toPoint())
        block = cursor.block()
        block_number = block.blockNumber()
        highlighter = self.highlighter
        if block_number in highlighter.error_lines:
            # Pobierz komunikat błędu
            error_message = highlighter.error_lines.get(block_number, "")
            QToolTip.showText(event.globalPosition().toPoint(), error_message, self)
        else:
            QToolTip.hideText()
            super().mouseMoveEvent(event)

    def show_completions(self):
        try:
            cursor = self.textCursor()
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            prefix = cursor.selectedText()
            print(f"Prefix: {prefix}")  # Debug

            if not prefix:
                self.completion_list.hide()
                return

            # Pobierz numer linii i kolumnę
            block = cursor.block()
            line = cursor.blockNumber() + 1  # 1-based line number
            column = cursor.positionInBlock()  # 0-based column number

            # Pobierz całkowitą liczbę linii w dokumencie
            total_lines = self.document().blockCount()
            if line > total_lines:
                line = total_lines

            # Pobierz tekst bieżącej linii
            current_block_text = block.text()
            if column > len(current_block_text):
                column = len(current_block_text)

            print(f"Line: {line}, Column: {column}")  # Debug

            # Inicjalizacja Jedi Script z prawidłową ścieżką
            script = jedi.Script(code=self.toPlainText(), path='temp.py')
            completions = script.complete(line, column)
            print(f"Completions: {len(completions)}")  # Debug

            if completions:
                self.completion_list.clear()
                for comp in completions:
                    item = QListWidgetItem(comp.name)
                    # Dodanie opisu do listy
                    item.setToolTip(comp.description)
                    # Dodanie ikon (załadowane wcześniej)
                    if comp.type == 'function':
                        item.setIcon(self.function_icon)
                    elif comp.type == 'class':
                        item.setIcon(self.class_icon)
                    self.completion_list.addItem(item)

                # Pozycjonowanie listy
                cursor_rect = self.cursorRect()
                list_pos = self.mapToGlobal(cursor_rect.bottomRight())
                self.completion_list.move(list_pos)
                self.completion_list.resize(200, min(150, self.completion_list.sizeHintForRow(0) * len(completions) + 2))
                self.completion_list.show()
            else:
                self.completion_list.hide()
        except Exception as e:
            print(f"Autouzupełnianie błędów: {e}")
            self.completion_list.hide()
            
    def complete_text(self, item):
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.removeSelectedText()
        cursor.insertText(item.text())
        self.setTextCursor(cursor)
        self.completion_list.hide()

    def accept_completion(self):
        selected_item = self.completion_list.currentItem()
        if selected_item:
            self.complete_text(selected_item)
            
class CodeNavigatorPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        self.functions_list_widget = QListWidget()
        self.classes_list_widget = QListWidget()

        self.tab_widget.addTab(self.functions_list_widget, "Funkcje")
        self.tab_widget.addTab(self.classes_list_widget, "Klasy")

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
        self.setMaximumWidth(200)

        # Po kliknięciu na funkcję lub klasę, przenieś kursor do jej definicji
        self.functions_list_widget.itemClicked.connect(self.go_to_function)
        self.classes_list_widget.itemClicked.connect(self.go_to_class)

    def update_symbols(self, symbols):
        self.functions_list_widget.clear()
        self.classes_list_widget.clear()

        for func_name, line_number in symbols.get('functions', []):
            item = QListWidgetItem(func_name)
            item.setData(Qt.ItemDataRole.UserRole, line_number)
            self.functions_list_widget.addItem(item)

        for class_name, line_number in symbols.get('classes', []):
            item = QListWidgetItem(class_name)
            item.setData(Qt.ItemDataRole.UserRole, line_number)
            self.classes_list_widget.addItem(item)

    def go_to_function(self, item):
        line_number = item.data(Qt.ItemDataRole.UserRole)
        editor = self.main_window.get_current_editor()
        if editor:
            cursor = editor.textCursor()
            block = editor.document().findBlockByNumber(line_number)
            if block.isValid():
                cursor.setPosition(block.position())
                editor.setTextCursor(cursor)
                editor.centerCursor()
                editor.setFocus()
                editor.highlight_current_line()

    def go_to_class(self, item):
        line_number = item.data(Qt.ItemDataRole.UserRole)
        editor = self.main_window.get_current_editor()
        if editor:
            cursor = editor.textCursor()
            block = editor.document().findBlockByNumber(line_number)
            if block.isValid():
                cursor.setPosition(block.position())
                editor.setTextCursor(cursor)
                editor.centerCursor()
                editor.setFocus()
                editor.highlight_current_line()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ustawienia IDE")
        layout = QVBoxLayout()

        # Opcja włączania/wyłączania automatycznego czyszczenia wklejania
        self.clean_paste_checkbox = QCheckBox("Automatycznie czyść wklejany tekst")
        self.clean_paste_checkbox.setChecked(True)
        layout.addWidget(self.clean_paste_checkbox)

        # Opcja włączania/wyłączania inteligentnego wcięcia
        self.smart_indent_checkbox = QCheckBox("Inteligentne wcięcie")
        self.smart_indent_checkbox.setChecked(True)
        layout.addWidget(self.smart_indent_checkbox)

        # Opcja włączania/wyłączania potwierdzenia usunięcia
        self.confirm_delete_checkbox = QCheckBox("Potwierdzenie przed usunięciem")
        self.confirm_delete_checkbox.setChecked(True)
        layout.addWidget(self.confirm_delete_checkbox)

        # Opcja wyboru tematu
        self.theme_label = QLabel("Wybierz temat:")
        layout.addWidget(self.theme_label)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Jasny", "Ciemny"])
        layout.addWidget(self.theme_combo)

        # Opcja regulacji rozmiaru czcionki
        self.font_size_label = QLabel("Rozmiar czcionki:")
        layout.addWidget(self.font_size_label)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(12)
        layout.addWidget(self.font_size_spin)

        # Opcja włączania/wyłączania auto-save
        self.auto_save_checkbox = QCheckBox("Włącz auto-save (co 5 minut)")
        self.auto_save_checkbox.setChecked(True)
        layout.addWidget(self.auto_save_checkbox)

        # Opcja włączania/wyłączania trybu skupienia
        self.focus_mode_checkbox = QCheckBox("Tryb skupienia (ukryj panele boczne)")
        self.focus_mode_checkbox.setChecked(False)
        layout.addWidget(self.focus_mode_checkbox)

        # Przycisk Zapisz
        save_button = QPushButton("Zapisz")
        save_button.clicked.connect(self.accept)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def get_settings(self):
        return {
            'clean_paste': self.clean_paste_checkbox.isChecked(),
            'smart_indent': self.smart_indent_checkbox.isChecked(),
            'confirm_delete': self.confirm_delete_checkbox.isChecked(),
            'theme': self.theme_combo.currentText(),
            'font_size': self.font_size_spin.value(),
            'auto_save': self.auto_save_checkbox.isChecked(),
            'focus_mode': self.focus_mode_checkbox.isChecked(),
        }

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prosty Edytor Python - MiniIDE")
        self.resize(1200, 800)

        # Inicjalizacja ścieżki repozytorium Git
        self.git_repo_path = '.'  # Domyślnie bieżący katalog

        # Przechowywanie ścieżek plików dla zakładek
        self.tab_paths = {}

        # Pasek statusu
        self.status_bar = self.statusBar()

        # Główny widget z zakładkami
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # Panel wyjściowy
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumHeight(200)
        self.output.setFont(QFont("Consolas", 10))
        self.output.setStyleSheet("background-color: #f0f0f0;")

        # Panel nawigacji kodu
        self.navigator_panel = CodeNavigatorPanel(self)

        # Dodanie pierwszej zakładki
        self.current_editor = None  # Bieżący edytor
        self.add_new_tab()

        # Splitter do podziału edytora i paneli bocznych
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(self.navigator_panel)
        main_splitter.addWidget(self.tab_widget)
        main_splitter.setStretchFactor(1, 3)

        # Główny splitter do podziału edytora i wyjścia
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(main_splitter)
        splitter.addWidget(self.output)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

        self.create_menu()

        # Ustawienie domyślnego interpretera
        self.python_interpreter = sys.executable
        self.flake8_config = None

        # Inicjalizacja debuggera
        self.debugger = None

        # Timer Auto-Save
        self.auto_save_timer = QTimer()
        self.auto_save_timer.setInterval(300000)  # 5 minut
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start()

        # Aktualizacja paska statusu
        self.update_status_bar()

        # Ustawienia domyślne
        self.settings = {
            'clean_paste': True,
            'smart_indent': True,
            'confirm_delete': True,
            'theme': 'Jasny',
            'font_size': 12,
            'auto_save': True,
            'focus_mode': False,
        }

    def create_menu(self):
        menubar = self.menuBar()

        # Menu Plik
        file_menu = menubar.addMenu("Plik")

        new_action = QAction("Nowy", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("Otwórz", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Zapisz", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Zapisz jako...", self)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        # Eksport
        export_html_action = QAction("Eksportuj do HTML", self)
        export_html_action.triggered.connect(self.export_to_html)
        file_menu.addAction(export_html_action)

        export_pdf_action = QAction("Eksportuj do PDF", self)
        export_pdf_action.triggered.connect(self.export_to_pdf)
        file_menu.addAction(export_pdf_action)

        file_menu.addSeparator()

        exit_action = QAction("Wyjście", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menu Uruchom
        run_menu = menubar.addMenu("Uruchom")

        run_action = QAction("Uruchom Skrypt", self)
        run_action.setShortcut(QKeySequence("F5"))
        run_action.triggered.connect(self.run_code)
        run_menu.addAction(run_action)

        debug_action = QAction("Debuguj Skrypt", self)
        debug_action.setShortcut(QKeySequence("F6"))
        debug_action.triggered.connect(self.debug_code)
        run_menu.addAction(debug_action)

        # Menu Testy
        test_menu = menubar.addMenu("Testy")

        run_tests_action = QAction("Uruchom Testy", self)
        run_tests_action.setShortcut(QKeySequence("Ctrl+T"))
        run_tests_action.triggered.connect(self.run_tests)
        test_menu.addAction(run_tests_action)

        # Menu Środowisko
        env_menu = menubar.addMenu("Środowisko")

        select_env_action = QAction("Wybierz Interpreter", self)
        select_env_action.triggered.connect(self.select_interpreter)
        env_menu.addAction(select_env_action)

        # Menu Konfiguracja
        config_menu = menubar.addMenu("Konfiguracja")

        # Dodaj opcję "Sprawdź poprawność kodu"
        check_code_action = QAction("Sprawdź poprawność kodu", self)
        check_code_action.setShortcut(QKeySequence("Ctrl+L"))
        check_code_action.triggered.connect(self.run_code_linter)
        config_menu.addAction(check_code_action)

        set_flake8_config_action = QAction("Ustaw Konfigurację Flake8", self)
        set_flake8_config_action.triggered.connect(self.set_flake8_config)
        config_menu.addAction(set_flake8_config_action)

        # Dodaj opcję "Ustawienia IDE"
        settings_action = QAction("Ustawienia IDE", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self.open_settings_dialog)
        config_menu.addAction(settings_action)

        # Menu Git
        git_menu = menubar.addMenu("Git")

        select_git_repo_action = QAction("Wybierz Repozytorium Git", self)
        select_git_repo_action.triggered.connect(self.select_git_repo)
        git_menu.addAction(select_git_repo_action)

        commit_action = QAction("Commit", self)
        commit_action.triggered.connect(self.git_commit)
        git_menu.addAction(commit_action)

        push_action = QAction("Push", self)
        push_action.triggered.connect(self.git_push)
        git_menu.addAction(push_action)

        pull_action = QAction("Pull", self)
        pull_action.triggered.connect(self.git_pull)
        git_menu.addAction(pull_action)

        branch_action = QAction("Utwórz Branch", self)
        branch_action.triggered.connect(self.git_create_branch)
        git_menu.addAction(branch_action)

        merge_action = QAction("Merge Branch", self)
        merge_action.triggered.connect(self.git_merge_branch)
        git_menu.addAction(merge_action)

        log_action = QAction("Log Commitów", self)
        log_action.triggered.connect(self.git_show_log)
        git_menu.addAction(log_action)

    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        dialog.clean_paste_checkbox.setChecked(self.settings['clean_paste'])
        dialog.smart_indent_checkbox.setChecked(self.settings['smart_indent'])
        dialog.confirm_delete_checkbox.setChecked(self.settings['confirm_delete'])
        dialog.theme_combo.setCurrentText(self.settings['theme'])
        dialog.font_size_spin.setValue(self.settings['font_size'])
        dialog.auto_save_checkbox.setChecked(self.settings['auto_save'])
        dialog.focus_mode_checkbox.setChecked(self.settings['focus_mode'])

        if dialog.exec():
            self.settings = dialog.get_settings()
            # Przekaż ustawienia do wszystkich otwartych edytorów
            for i in range(self.tab_widget.count()):
                editor = self.tab_widget.widget(i)
                editor.apply_settings(self.settings)
            # Zastosuj ustawienia motywu do całego okna
            self.apply_theme(self.settings['theme'])
            # Zastosuj tryb skupienia
            self.apply_settings(self.settings)
            # Aktualizacja ustawień auto-save
            if self.settings.get('auto_save', True):
                self.auto_save_timer.start()
            else:
                self.auto_save_timer.stop()

    def apply_theme(self, theme):
        if theme == "Ciemny":
            self.setStyleSheet("""
                QPlainTextEdit, QListWidget, QLineEdit, QTabWidget, QDialog {
                    background-color: #2b2b2b;
                    color: #f8f8f2;
                }
                QMenuBar, QMenu, QMenu::item {
                    background-color: #2b2b2b;
                    color: #f8f8f2;
                }
                QTabWidget::pane { /* The tab widget frame */
                    border-top: 2px solid #C2C7CB;
                }
                QTabBar::tab:selected {
                    background: #3C3F41;
                    color: white;
                }
                QTabBar::tab {
                    background: #2b2b2b;
                    color: #f8f8f2;
                }
            """)
        else:
            self.setStyleSheet("")  # Domyślny jasny motyw

    def apply_settings(self, settings):
        # Tryb skupienia
        if settings.get('focus_mode', False):
            self.navigator_panel.hide()
            self.output.hide()
        else:
            self.navigator_panel.show()
            self.output.show()
        # Zaktualizuj pasek statusu
        self.update_status_bar()

    def update_status_bar(self):
        editor = self.get_current_editor()
        if editor:
            undo_available = editor.document().isUndoAvailable()
            redo_available = editor.document().isRedoAvailable()
            status_text = f"Undo: {'Tak' if undo_available else 'Nie'}, Redo: {'Tak' if redo_available else 'Nie'}"
            self.status_bar.showMessage(status_text)
        else:
            self.status_bar.showMessage("Brak aktywnego edytora.")

    def add_new_tab(self, code="", filename="Untitled"):
        editor = CodeEditor()
        editor.setPlainText(code)
        editor.setParent(self.tab_widget)

        self.tab_widget.addTab(editor, filename)
        self.tab_widget.setCurrentWidget(editor)

        # Aktualizuj obecny edytor
        self.on_tab_changed(self.tab_widget.currentIndex())

        # Przechowywanie ścieżek plików (None dla nowych plików)
        current_index = self.tab_widget.currentIndex()
        self.tab_paths[current_index] = None

        # Połączenie sygnałów do aktualizacji paska statusu
        editor.textChanged.connect(self.update_status_bar)
        editor.undoAvailable.connect(self.update_status_bar)
        editor.redoAvailable.connect(self.update_status_bar)

    def on_tab_changed(self, index):
        if hasattr(self, 'current_editor') and self.current_editor:
            # Zatrzymaj linter w poprzednim edytorze
            if self.current_editor.linter_thread is not None:
                self.current_editor.linter_thread.quit()
                self.current_editor.linter_thread.wait()
                self.current_editor.linter_thread = None
            # Odłącz sygnały
            try:
                self.current_editor.symbols_updated.disconnect(self.navigator_panel.update_symbols)
            except TypeError:
                pass  # Sygnał już odłączony

        current_widget = self.tab_widget.widget(index)
        self.current_editor = current_widget  # Zakładamy, że widgetem jest CodeEditor

        if self.current_editor:
            self.current_editor.symbols_updated.connect(self.navigator_panel.update_symbols)
            self.current_editor.update_symbols_panel()
        else:
            self.navigator_panel.update_symbols({'functions': [], 'classes': []})

        self.update_status_bar()

    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            # Zatrzymaj linter w edytorze, który jest zamykany
            editor = self.tab_widget.widget(index)
            if editor.linter_thread is not None:
                editor.linter_thread.quit()
                editor.linter_thread.wait()
                editor.linter_thread = None

            self.tab_widget.removeTab(index)
            # Usunięcie przechowywanej ścieżki
            if index in self.tab_paths:
                del self.tab_paths[index]
            # Aktualizacja kluczy w słowniku
            self.tab_paths = {i: path for i, path in enumerate(self.tab_paths.values())}
        else:
            QMessageBox.warning(self, "Ostrzeżenie", "Nie można zamknąć ostatniej zakładki.")

    def get_current_editor(self):
        return self.current_editor

    def run_code_linter(self):
        """Metoda wywołująca linter w CodeEditor"""
        editor = self.get_current_editor()
        if editor:
            editor.run_linter()
        else:
            QMessageBox.warning(self, "Linter", "Brak aktywnego edytora.")

    def new_file(self):
        self.add_new_tab()

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Otwórz plik", "",
            "Python Files (*.py);;JavaScript Files (*.js);;C++ Files (*.cpp *.hpp);;Go Files (*.go);;All Files (*)")
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    code = f.read()
                filename = os.path.basename(path)  # Pobranie nazwy pliku
                self.add_new_tab(code, filename)
                # Przechowywanie ścieżki pliku
                current_index = self.tab_widget.currentIndex()
                self.tab_paths[current_index] = path
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nie można otworzyć pliku:\n{e}")

    def save_file(self):
        editor = self.get_current_editor()
        if editor:
            current_index = self.tab_widget.currentIndex()
            file_path = self.tab_paths.get(current_index)
            if file_path is None:
                self.save_file_as()
            else:
                self.save_to_path(file_path, editor.toPlainText())

    def save_file_as(self):
        editor = self.get_current_editor()
        if editor:
            path, _ = QFileDialog.getSaveFileName(self, "Zapisz plik jako", "",
                "Python Files (*.py);;JavaScript Files (*.js);;C++ Files (*.cpp *.hpp);;Go Files (*.go);;All Files (*)")
            if path:
                try:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(editor.toPlainText())
                    filename = os.path.basename(path)
                    current_index = self.tab_widget.currentIndex()
                    self.tab_widget.setTabText(current_index, filename)
                    self.tab_paths[current_index] = path  # Aktualizacja ścieżki pliku
                    QMessageBox.information(self, "Zapisano", f"Plik zapisano: {path}")
                except Exception as e:
                    QMessageBox.critical(self, "Błąd", f"Nie można zapisać pliku:\n{e}")

    def save_to_path(self, path, code):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(code)
            QMessageBox.information(self, "Zapisano", f"Plik zapisano: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można zapisać pliku:\n{e}")

    def export_to_html(self):
        editor = self.get_current_editor()
        if editor:
            code = editor.toPlainText()
            language = editor.highlighter.lexer.name.lower()
            lexer = get_lexer_by_name(language)
            formatter = pygments.formatters.HtmlFormatter(full=True, linenos=True, style='friendly')
            html_code = pygments.highlight(code, lexer, formatter)

            path, _ = QFileDialog.getSaveFileName(self, "Eksportuj do HTML", "", "HTML Files (*.html);;All Files (*)")
            if path:
                try:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(html_code)
                    QMessageBox.information(self, "Eksport", f"Projekt wyeksportowany do HTML: {path}")
                except Exception as e:
                    QMessageBox.critical(self, "Eksport Błąd", f"Nie można wyeksportować do HTML:\n{e}")

    def export_to_pdf(self):
        editor = self.get_current_editor()
        if editor:
            code = editor.toPlainText()
            language = editor.highlighter.lexer.name.lower()
            lexer = get_lexer_by_name(language)
            formatter = pygments.formatters.HtmlFormatter(full=True, linenos=True, style='friendly')
            html_code = pygments.highlight(code, lexer, formatter)

            path, _ = QFileDialog.getSaveFileName(self, "Eksportuj do PDF", "", "PDF Files (*.pdf);;All Files (*)")
            if path:
                try:
                    # Konwertuj HTML do PDF za pomocą wkhtmltopdf
                    temp_html = "temp_export.html"
                    with open(temp_html, 'w', encoding='utf-8') as f:
                        f.write(html_code)
                    subprocess.run(['wkhtmltopdf', temp_html, path], check=True)
                    os.remove(temp_html)  # Usuń tymczasowy plik HTML
                    QMessageBox.information(self, "Eksport", f"Projekt wyeksportowany do PDF: {path}")
                except Exception as e:
                    QMessageBox.critical(self, "Eksport Błąd", f"Nie można wyeksportować do PDF:\n{e}")

    def run_code(self):
        editor = self.get_current_editor()
        if editor:
            code = editor.toPlainText()
            language = editor.highlighter.lexer.name.lower()
            try:
                # Zapisz tymczasowy plik
                if language == 'python':
                    temp_file = "temp_script.py"
                elif language == 'javascript':
                    temp_file = "temp_script.js"
                elif language == 'cpp':
                    temp_file = "temp_script.cpp"
                elif language == 'go':
                    temp_file = "temp_script.go"
                else:
                    temp_file = "temp_script.py"  # Domyślny interpreter

                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(code)

                # Uruchom skrypt
                process = QProcess(self)
                if language == 'python':
                    interpreter = self.python_interpreter
                    args = [temp_file]
                elif language == 'javascript':
                    interpreter = 'node'  # Upewnij się, że Node.js jest zainstalowany
                    args = [temp_file]
                elif language == 'cpp':
                    # Kompilacja i uruchomienie C++
                    executable = "temp_script.exe" if sys.platform == 'win32' else "./temp_script"
                    compile_process = subprocess.run(['g++', temp_file, '-o', 'temp_script'], capture_output=True, text=True)
                    if compile_process.returncode != 0:
                        self.output.appendPlainText(">>> Błąd kompilacji:")
                        self.output.appendPlainText(compile_process.stderr)
                        return
                    interpreter = executable
                    args = []
                elif language == 'go':
                    # Kompilacja i uruchomienie Go
                    executable = "temp_script" if sys.platform != 'win32' else "temp_script.exe"
                    compile_process = subprocess.run(['go', 'build', '-o', executable, temp_file], capture_output=True, text=True)
                    if compile_process.returncode != 0:
                        self.output.appendPlainText(">>> Błąd kompilacji:")
                        self.output.appendPlainText(compile_process.stderr)
                        return
                    interpreter = os.path.abspath(executable)
                    args = []
                else:
                    interpreter = self.python_interpreter
                    args = [temp_file]

                process.setProgram(interpreter)
                process.setArguments(args)
                process.start()
                process.waitForFinished()

                output = process.readAllStandardOutput().data().decode()
                error = process.readAllStandardError().data().decode()

                if output:
                    self.output.appendPlainText(">>> Wynik:")
                    self.output.appendPlainText(output)
                if error:
                    self.output.appendPlainText(">>> Błąd:")
                    self.output.appendPlainText(error)
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nie można uruchomić skryptu:\n{e}")

    def debug_code(self):
        editor = self.get_current_editor()
        if editor:
            code = editor.toPlainText()
            language = editor.highlighter.lexer.name.lower()
            if language != 'python':
                QMessageBox.warning(self, "Debugowanie", "Debugowanie jest obecnie dostępne tylko dla Pythona.")
                return

            temp_file = "temp_debug_script.py"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(code)

            try:
                # Sprawdź, czy debugpy jest zainstalowany
                subprocess.run([self.python_interpreter, '-m', 'debugpy', '--version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                QMessageBox.critical(self, "Debugowanie Błąd", "Moduł debugpy nie jest zainstalowany.")
                return
            except FileNotFoundError:
                QMessageBox.critical(self, "Debugowanie Błąd", "Interpreter Python nie został znaleziony.")
                return

            try:
                # Uruchomienie debuggera w osobnym procesie
                self.debugger = QProcess(self)
                self.debugger.setProgram(self.python_interpreter)
                self.debugger.setArguments([
                    "-m", "debugpy",
                    "--listen", "5678",
                    "--wait-for-client",
                    temp_file
                ])
                self.debugger.start()
                if not self.debugger.waitForStarted(3000):
                    QMessageBox.critical(self, "Debugowanie Błąd", "Nie można uruchomić debuggera.")
                    return
                QMessageBox.information(self, "Debugowanie", "Debugger uruchomiony. Podłącz się do portu 5678 za pomocą klienta debuggera (np. VSCode).")
            except Exception as e:
                QMessageBox.critical(self, "Debugowanie Błąd", f"Nie można uruchomić debuggera:\n{e}")

    def run_tests(self):
        editor = self.get_current_editor()
        if editor:
            code = editor.toPlainText()
            language = editor.highlighter.lexer.name.lower()
            if language != 'python':
                QMessageBox.warning(self, "Testowanie", "Testowanie jest dostępne tylko dla Pythona.")
                return

            temp_file = "temp_test_script.py"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(code)

            try:
                # Uruchomienie testów
                test_output = io.StringIO()
                with contextlib.redirect_stdout(test_output):
                    loader = unittest.TestLoader()
                    suite = loader.discover('.', pattern='temp_test_script.py')
                    runner = unittest.TextTestRunner(stream=test_output, verbosity=2)
                    runner.run(suite)

                output = test_output.getvalue()
                self.output.appendPlainText(">>> Testy:")
                self.output.appendPlainText(output)
            except Exception as e:
                QMessageBox.critical(self, "Testowanie Błąd", f"Wystąpił błąd podczas uruchamiania testów:\n{e}")

    def set_flake8_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "Wybierz plik konfiguracyjny Flake8", "", "Config Files (*.ini *.cfg *.toml);;All Files (*)")
        if path:
            self.flake8_config = path
            QMessageBox.information(self, "Konfiguracja Flake8", f"Załadowano konfigurację: {self.flake8_config}")

    def select_interpreter(self):
        path, _ = QFileDialog.getOpenFileName(self, "Wybierz interpreter Pythona", "", "Python Executable (*.exe);;All Files (*)")
        if path:
            self.python_interpreter = path
            QMessageBox.information(self, "Interpreter", f"Wybrano interpreter: {self.python_interpreter}")

    # Operacje Git
    def git_commit(self):
        try:
            repo = git.Repo(self.git_repo_path)
            commit_message, ok = QInputDialog.getText(self, 'Commit', 'Wpisz wiadomość commit:')
            if ok and commit_message:
                repo.git.add('--all')
                repo.index.commit(commit_message)
                QMessageBox.information(self, "Commit", "Zatwierdzono zmiany.")
        except git.exc.InvalidGitRepositoryError:
            QMessageBox.critical(self, "Git Błąd", "Nie znaleziono repozytorium Git w wybranym katalogu.")
        except Exception as e:
            QMessageBox.critical(self, "Git Błąd", f"Wystąpił błąd podczas commitowania: {e}")

    def git_push(self):
        try:
            repo = git.Repo(self.git_repo_path)
            origin = repo.remote(name='origin')
            origin.push()
            QMessageBox.information(self, "Push", "Zmiany zostały wypchnięte na GitHub.")
        except git.exc.InvalidGitRepositoryError:
            QMessageBox.critical(self, "Git Błąd", "Nie znaleziono repozytorium Git w wybranym katalogu.")
        except Exception as e:
            QMessageBox.critical(self, "Git Błąd", f"Wystąpił błąd podczas pushowania: {e}")

    def git_pull(self):
        try:
            repo = git.Repo(self.git_repo_path)
            origin = repo.remote(name='origin')
            origin.pull()
            QMessageBox.information(self, "Pull", "Zmiany zostały pobrane z GitHub.")
        except git.exc.InvalidGitRepositoryError:
            QMessageBox.critical(self, "Git Błąd", "Nie znaleziono repozytorium Git w wybranym katalogu.")
        except Exception as e:
            QMessageBox.critical(self, "Git Błąd", f"Wystąpił błąd podczas pullowania: {e}")

    def git_create_branch(self):
        try:
            repo = git.Repo(self.git_repo_path)
            branch_name, ok = QInputDialog.getText(self, 'Create Branch', 'Wpisz nazwę nowego brancha:')
            if ok and branch_name:
                repo.git.checkout('-b', branch_name)
                QMessageBox.information(self, "Branch", f"Utworzono i przełączono na branch: {branch_name}")
        except git.exc.InvalidGitRepositoryError:
            QMessageBox.critical(self, "Git Błąd", "Nie znaleziono repozytorium Git w wybranym katalogu.")
        except Exception as e:
            QMessageBox.critical(self, "Git Błąd", f"Wystąpił błąd podczas tworzenia brancha: {e}")

    def git_merge_branch(self):
        try:
            repo = git.Repo(self.git_repo_path)
            branches = [head.name for head in repo.heads]
            branch, ok = QInputDialog.getItem(self, "Merge Branch", "Wybierz branch do mergowania:", branches, 0, False)
            if ok and branch:
                current = repo.active_branch.name
                repo.git.merge(branch)
                QMessageBox.information(self, "Merge", f"Branch {branch} został zmergowany z {current}.")
        except git.exc.InvalidGitRepositoryError:
            QMessageBox.critical(self, "Git Błąd", "Nie znaleziono repozytorium Git w wybranym katalogu.")
        except git.exc.GitCommandError as e:
            QMessageBox.critical(self, "Git Błąd", f"Wystąpił błąd podczas mergowania: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Git Błąd", f"Wystąpił błąd podczas mergowania: {e}")

    def git_show_log(self):
        try:
            repo = git.Repo(self.git_repo_path)
            logs = repo.git.log('--oneline', '--graph', '--all')
            log_dialog = QDialog(self)
            log_dialog.setWindowTitle("Log Commitów")
            layout = QVBoxLayout()
            log_text = QPlainTextEdit()
            log_text.setReadOnly(True)
            log_text.setPlainText(logs)
            layout.addWidget(log_text)
            log_dialog.setLayout(layout)
            log_dialog.resize(600, 400)
            log_dialog.exec()
        except git.exc.InvalidGitRepositoryError:
            QMessageBox.critical(self, "Git Błąd", "Nie znaleziono repozytorium Git w wybranym katalogu.")
        except Exception as e:
            QMessageBox.critical(self, "Git Błąd", f"Wystąpił błąd podczas pobierania logów: {e}")

    def select_git_repo(self):
        path = QFileDialog.getExistingDirectory(self, "Wybierz Repozytorium Git", "")
        if path:
            try:
                repo = git.Repo(path)
                self.git_repo_path = path
                QMessageBox.information(self, "Git Repo", f"Wybrane repozytorium: {path}")
            except git.exc.InvalidGitRepositoryError:
                QMessageBox.critical(self, "Git Błąd", "Wybrany folder nie jest repozytorium Git.")

    def auto_save(self):
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            file_path = self.tab_paths.get(i)
            if file_path and self.settings.get('auto_save', True):
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(editor.toPlainText())
                    print(f"Auto-saved: {file_path}")
                except Exception as e:
                    print(f"Auto-save failed for {file_path}: {e}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
