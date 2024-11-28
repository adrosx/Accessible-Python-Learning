import sys
import subprocess
import re
import pygments
import pdfkit
import bisect
import ast
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QPlainTextEdit,
    QWidget,
    QVBoxLayout,
    QSplitter,
    QListWidget,
    QDialog,
    QInputDialog,
    QTextEdit,
    QTabWidget,
    QHBoxLayout,
    QLineEdit,
    QTabBar,
    QListWidgetItem)
from PyQt6.QtGui import (
    QFont, QColor, QTextFormat, QPainter, QSyntaxHighlighter,
    QTextCharFormat, QTextCursor, QKeySequence, QAction, QTextDocument
)
from PyQt6.QtCore import Qt, QRect, QProcess, pyqtSignal, QSize, QTimer, QObject, QThread
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.styles import get_style_by_name
import git
import unittest
import io
import contextlib
import os
slice

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
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                cwd=self.repo_path)
            output = result.stdout
            errors = []
            for line in output.strip().split('\n'):
                match = re.match(
                    rf"{re.escape(temp_file)}:(\d+):\d+:\s+(.*)", line)
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
            top = int(self.code_editor.blockBoundingGeometry(
                block).translated(self.code_editor.contentOffset()).top())
            bottom = top + \
                int(self.code_editor.blockBoundingRect(block).height())

            while block.isValid() and top <= y:
                if block.isVisible() and bottom >= y:
                    self.clicked.emit(block_number)
                    break
                block = block.next()
                top = bottom
                bottom = top + \
                    int(self.code_editor.blockBoundingRect(block).height())
                block_number += 1


class GenericHighlighter(QSyntaxHighlighter):
    def __init__(self, document, language='python'):
        super().__init__(document)
        self.formats = {}
        self.error_format = QTextCharFormat()
        self.error_format.setUnderlineColor(QColor("red"))
        self.error_format.setUnderlineStyle(
            QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
        self.error_lines = set()

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
            return

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
    # Sygnał zaktualizowanych funkcji i klas
    symbols_updated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Consolas", 12))

        # Inicjalizacja zmiennych
        self.breakpoints = set()
        self.file_path = None
        self.is_linting = False
        self.previous_errors = []

        # Highlighter
        self.highlighter = GenericHighlighter(
            self.document(), language='python')

        # Tworzenie LineNumberArea
        self.line_number_area = LineNumberArea(self)
        self.line_number_area.clicked.connect(self.toggle_breakpoint)

        # Podłączenie sygnałów
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.textChanged.connect(self.on_text_changed)

        # Ustawienia początkowe
        self.update_line_number_area_width(0)
        self.highlight_current_line()

        # Timer do aktualizacji panelu symboli
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

    def on_text_changed(self):
        self.symbols_update_timer.start()  # Restart timera aktualizacji symboli

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
            self.line_number_area.update(
                0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(
                cr.left(),
                cr.top(),
                self.line_number_area_width(),
                cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(240, 240, 240)
                         )  # Jasne tło dla numerów linii

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(
            self.blockBoundingGeometry(block).translated(
                self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                if block_number in self.breakpoints:
                    # Czerwony kolor dla breakpointów
                    painter.setPen(QColor(255, 0, 0))
                    painter.drawEllipse(2, top + 2, 10, 10)
                else:
                    painter.setPen(QColor("black"))
                    painter.drawText(
                        0,
                        top,
                        self.line_number_area.width() - 5,
                        self.fontMetrics().height(),
                        Qt.AlignmentFlag.AlignRight,
                        number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            # Jasne podświetlenie bieżącej linii
            line_color = QColor(232, 242, 254)
            selection.format.setBackground(line_color)
            selection.format.setProperty(
                QTextFormat.Property.FullWidthSelection, True)
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
                # Jasnoczerwone tło dla breakpointu
                selection.format.setBackground(QColor(255, 230, 230))
                extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Pobierz bieżący tekst przed kursorem
            cursor = self.textCursor()
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            current_line = cursor.selectedText()

            # Zidentyfikuj ilość spacji na początku linii
            indentation = re.match(r'\s*', current_line).group()

            # Jeśli linia kończy się dwukropkiem, dodaj dodatkowe wcięcie
            if current_line.rstrip().endswith(':'):
                indentation += '    '

            super().keyPressEvent(event)

            # Dodaj wcięcie do nowej linii
            cursor = self.textCursor()
            cursor.insertText(indentation)
            return
        elif event.key() == Qt.Key.Key_F and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.show_find_dialog()
            return
        else:
            super().keyPressEvent(event)

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
                    parent_window.output.appendPlainText(
                        f"Linia {line_num + 1}: {message}")
            else:
                parent_window.output.appendPlainText(
                    ">>> Brak błędów wykrytych przez linter.")

        if errors == self.previous_errors:
            return  # Nie aktualizuj highlightera, jeśli błędy się nie zmieniły
        self.previous_errors = errors  # Zapisz nowe błędy

        self.highlighter.error_lines = set(line for line, _ in errors)
        self.highlighter.rehighlight()

    def on_linter_error(self, error_message):
        self.is_linting = False  # Resetuj flagę
        self.linter_thread = None
        parent_window = self.window()
        if parent_window and hasattr(parent_window, 'output'):
            parent_window.output.clear()
            parent_window.output.appendPlainText(
                f">>> Błąd lintera: {error_message}")

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

        # Znajdź kolejne wystąpienie
        found = self.find(search_text, QTextDocument.FindFlag())

        if not found:
            # Powtórz od początku
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.setTextCursor(cursor)
            found = self.find(search_text, QTextDocument.FindFlag())

        if not found:
            QMessageBox.information(
                self, "Znajdź", f"Nie znaleziono: {search_text}")


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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prosty Edytor Python - MiniIDE")
        self.resize(1200, 800)

        # Inicjalizacja ścieżki repozytorium Git
        self.git_repo_path = '.'  # Domyślnie bieżący katalog

        # Przechowywanie ścieżek plików dla zakładek
        self.tab_paths = {}

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

    def add_new_tab(self, code="", filename="Untitled"):
        editor = CodeEditor()
        editor.setPlainText(code)
        editor.setParent(self.tab_widget)

        self.tab_widget.addTab(editor, filename)
        self.tab_widget.setCurrentWidget(editor)

        # Aktualizuj obecny edytor
        self.on_tab_changed(self.tab_widget.currentIndex())

        # Przechowywanie ścieżki plików (None dla nowych plików)
        current_index = self.tab_widget.currentIndex()
        self.tab_paths[current_index] = None

    def on_tab_changed(self, index):
        if hasattr(self, 'current_editor') and self.current_editor:
            # Zatrzymaj linter w poprzednim edytorze
            if self.current_editor.linter_thread is not None:
                self.current_editor.linter_thread.quit()
                self.current_editor.linter_thread.wait()
                self.current_editor.linter_thread = None
            # Odłącz sygnały
            try:
                self.current_editor.symbols_updated.disconnect(
                    self.navigator_panel.update_symbols)
            except TypeError:
                pass  # Sygnał już odłączony

        current_widget = self.tab_widget.widget(index)
        self.current_editor = current_widget  # Zakładamy, że widgetem jest CodeEditor

        if self.current_editor:
            self.current_editor.symbols_updated.connect(
                self.navigator_panel.update_symbols)
            self.current_editor.update_symbols_panel()
        else:
            self.navigator_panel.update_symbols(
                {'functions': [], 'classes': []})

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
            self.tab_paths = {
                i: path for i, path in enumerate(
                    self.tab_paths.values())}
        else:
            QMessageBox.warning(
                self,
                "Ostrzeżenie",
                "Nie można zamknąć ostatniej zakładki.")

    def on_tab_changed(self, index):
        if hasattr(self, 'current_editor') and self.current_editor:
            # Zatrzymaj linter w poprzednim edytorze
            if self.current_editor.linter_thread is not None:
                self.current_editor.linter_thread.quit()
                self.current_editor.linter_thread.wait()
                self.current_editor.linter_thread = None
            # Odłącz sygnały
            try:
                self.current_editor.symbols_updated.disconnect(
                    self.navigator_panel.update_symbols)
            except TypeError:
                pass  # Sygnał już odłączony

        current_widget = self.tab_widget.widget(index)
        self.current_editor = current_widget  # Zakładamy, że widgetem jest CodeEditor

        if self.current_editor:
            self.current_editor.symbols_updated.connect(
                self.navigator_panel.update_symbols)
            self.current_editor.update_symbols_panel()
        else:
            self.navigator_panel.update_symbols(
                {'functions': [], 'classes': []})

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
        path, _ = QFileDialog.getOpenFileName(
            self, "Otwórz plik", "", "Python Files (*.py);;JavaScript Files (*.js);;C++ Files (*.cpp *.hpp);;Go Files (*.go);;All Files (*)")
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
                QMessageBox.critical(
                    self, "Błąd", f"Nie można otworzyć pliku:\n{e}")

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
            path, _ = QFileDialog.getSaveFileName(
                self, "Zapisz plik jako", "", "Python Files (*.py);;JavaScript Files (*.js);;C++ Files (*.cpp *.hpp);;Go Files (*.go);;All Files (*)")
            if path:
                try:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(editor.toPlainText())
                    filename = os.path.basename(path)
                    current_index = self.tab_widget.currentIndex()
                    self.tab_widget.setTabText(current_index, filename)
                    # Aktualizacja ścieżki pliku
                    self.tab_paths[current_index] = path
                    QMessageBox.information(
                        self, "Zapisano", f"Plik zapisano: {path}")
                except Exception as e:
                    QMessageBox.critical(
                        self, "Błąd", f"Nie można zapisać pliku:\n{e}")

    def save_to_path(self, path, code):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(code)
            QMessageBox.information(self, "Zapisano", f"Plik zapisano: {path}")
        except Exception as e:
            QMessageBox.critical(
                self, "Błąd", f"Nie można zapisać pliku:\n{e}")

    def export_to_html(self):
        editor = self.get_current_editor()
        if editor:
            code = editor.toPlainText()
            language = editor.highlighter.lexer.name.lower()
            lexer = get_lexer_by_name(language)
            formatter = pygments.formatters.HtmlFormatter(
                full=True, linenos=True, style='friendly')
            html_code = pygments.highlight(code, lexer, formatter)

            path, _ = QFileDialog.getSaveFileName(
                self, "Eksportuj do HTML", "", "HTML Files (*.html);;All Files (*)")
            if path:
                try:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(html_code)
                    QMessageBox.information(
                        self, "Eksport", f"Projekt wyeksportowany do HTML: {path}")
                except Exception as e:
                    QMessageBox.critical(
                        self, "Eksport Błąd", f"Nie można wyeksportować do HTML:\n{e}")

    def export_to_pdf(self):
        editor = self.get_current_editor()
        if editor:
            code = editor.toPlainText()
            language = editor.highlighter.lexer.name.lower()
            lexer = get_lexer_by_name(language)
            formatter = pygments.formatters.HtmlFormatter(
                full=True, linenos=True, style='friendly')
            html_code = pygments.highlight(code, lexer, formatter)

            path, _ = QFileDialog.getSaveFileName(
                self, "Eksportuj do PDF", "", "PDF Files (*.pdf);;All Files (*)")
            if path:
                try:
                    # Konwertuj HTML do PDF
                    pdfkit.from_string(html_code, path)
                    QMessageBox.information(
                        self, "Eksport", f"Projekt wyeksportowany do PDF: {path}")
                except Exception as e:
                    QMessageBox.critical(
                        self, "Eksport Błąd", f"Nie można wyeksportować do PDF:\n{e}")

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
                    compile_process = subprocess.run(
                        ['g++', temp_file, '-o', 'temp_script'], capture_output=True, text=True)
                    if compile_process.returncode != 0:
                        self.output.appendPlainText(">>> Błąd kompilacji:")
                        self.output.appendPlainText(compile_process.stderr)
                        return
                    interpreter = executable
                    args = []
                elif language == 'go':
                    # Kompilacja i uruchomienie Go
                    executable = "temp_script" if sys.platform != 'win32' else "temp_script.exe"
                    compile_process = subprocess.run(
                        ['go', 'build', '-o', executable, temp_file], capture_output=True, text=True)
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
                QMessageBox.critical(
                    self, "Błąd", f"Nie można uruchomić skryptu:\n{e}")

    def debug_code(self):
        editor = self.get_current_editor()
        if editor:
            code = editor.toPlainText()
            language = editor.highlighter.lexer.name.lower()
            if language != 'python':
                QMessageBox.warning(
                    self,
                    "Debugowanie",
                    "Debugowanie jest obecnie dostępne tylko dla Pythona.")
                return

            temp_file = "temp_debug_script.py"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(code)

            try:
                # Sprawdź, czy debugpy jest zainstalowany
                subprocess.run([self.python_interpreter,
                                '-m',
                                'debugpy',
                                '--version'],
                               check=True,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                QMessageBox.critical(
                    self,
                    "Debugowanie Błąd",
                    "Moduł debugpy nie jest zainstalowany.")
                return
            except FileNotFoundError:
                QMessageBox.critical(
                    self,
                    "Debugowanie Błąd",
                    "Interpreter Python nie został znaleziony.")
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
                    QMessageBox.critical(
                        self, "Debugowanie Błąd", "Nie można uruchomić debuggera.")
                    return
                QMessageBox.information(
                    self,
                    "Debugowanie",
                    "Debugger uruchomiony. Podłącz się do portu 5678 za pomocą klienta debuggera (np. VSCode).")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Debugowanie Błąd",
                    f"Nie można uruchomić debuggera:\n{e}")

    def run_tests(self):
        editor = self.get_current_editor()
        if editor:
            code = editor.toPlainText()
            language = editor.highlighter.lexer.name.lower()
            if language != 'python':
                QMessageBox.warning(
                    self,
                    "Testowanie",
                    "Testowanie jest dostępne tylko dla Pythona.")
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
                    runner = unittest.TextTestRunner(
                        stream=test_output, verbosity=2)
                    runner.run(suite)

                output = test_output.getvalue()
                self.output.appendPlainText(">>> Testy:")
                self.output.appendPlainText(output)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Testowanie Błąd",
                    f"Wystąpił błąd podczas uruchamiania testów:\n{e}")

    def set_flake8_config(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Wybierz plik konfiguracyjny Flake8", "", "Config Files (*.ini *.cfg *.toml);;All Files (*)")
        if path:
            self.flake8_config = path
            QMessageBox.information(
                self,
                "Konfiguracja Flake8",
                f"Załadowano konfigurację: {self.flake8_config}")

    def select_interpreter(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Wybierz interpreter Pythona", "", "Python Executable (*.exe);;All Files (*)")
        if path:
            self.python_interpreter = path
            QMessageBox.information(
                self,
                "Interpreter",
                f"Wybrano interpreter: {self.python_interpreter}")

    # Operacje Git
    def git_commit(self):
        try:
            repo = git.Repo(self.git_repo_path)
            commit_message, ok = QInputDialog.getText(
                self, 'Commit', 'Wpisz wiadomość commit:')
            if ok and commit_message:
                repo.git.add('--all')
                repo.index.commit(commit_message)
                QMessageBox.information(self, "Commit", "Zatwierdzono zmiany.")
        except git.exc.InvalidGitRepositoryError:
            QMessageBox.critical(
                self,
                "Git Błąd",
                "Nie znaleziono repozytorium Git w wybranym katalogu.")
        except Exception as e:
            QMessageBox.critical(
                self, "Git Błąd", f"Wystąpił błąd podczas commitowania: {e}")

    def git_push(self):
        try:
            repo = git.Repo(self.git_repo_path)
            origin = repo.remote(name='origin')
            origin.push()
            QMessageBox.information(
                self, "Push", "Zmiany zostały wypchnięte na GitHub.")
        except git.exc.InvalidGitRepositoryError:
            QMessageBox.critical(
                self,
                "Git Błąd",
                "Nie znaleziono repozytorium Git w wybranym katalogu.")
        except Exception as e:
            QMessageBox.critical(
                self, "Git Błąd", f"Wystąpił błąd podczas pushowania: {e}")

    def git_pull(self):
        try:
            repo = git.Repo(self.git_repo_path)
            origin = repo.remote(name='origin')
            origin.pull()
            QMessageBox.information(
                self, "Pull", "Zmiany zostały pobrane z GitHub.")
        except git.exc.InvalidGitRepositoryError:
            QMessageBox.critical(
                self,
                "Git Błąd",
                "Nie znaleziono repozytorium Git w wybranym katalogu.")
        except Exception as e:
            QMessageBox.critical(
                self, "Git Błąd", f"Wystąpił błąd podczas pullowania: {e}")

    def git_create_branch(self):
        try:
            repo = git.Repo(self.git_repo_path)
            branch_name, ok = QInputDialog.getText(
                self, 'Create Branch', 'Wpisz nazwę nowego brancha:')
            if ok and branch_name:
                repo.git.checkout('-b', branch_name)
                QMessageBox.information(
                    self, "Branch", f"Utworzono i przełączono na branch: {branch_name}")
        except git.exc.InvalidGitRepositoryError:
            QMessageBox.critical(
                self,
                "Git Błąd",
                "Nie znaleziono repozytorium Git w wybranym katalogu.")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Git Błąd",
                f"Wystąpił błąd podczas tworzenia brancha: {e}")

    def git_merge_branch(self):
        try:
            repo = git.Repo(self.git_repo_path)
            branches = [head.name for head in repo.heads]
            branch, ok = QInputDialog.getItem(
                self, "Merge Branch", "Wybierz branch do mergowania:", branches, 0, False)
            if ok and branch:
                current = repo.active_branch.name
                repo.git.merge(branch)
                QMessageBox.information(
                    self, "Merge", f"Branch {branch} został zmergowany z {current}.")
        except git.exc.InvalidGitRepositoryError:
            QMessageBox.critical(
                self,
                "Git Błąd",
                "Nie znaleziono repozytorium Git w wybranym katalogu.")
        except git.exc.GitCommandError as e:
            QMessageBox.critical(
                self, "Git Błąd", f"Wystąpił błąd podczas mergowania: {e}")
        except Exception as e:
            QMessageBox.critical(
                self, "Git Błąd", f"Wystąpił błąd podczas mergowania: {e}")

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
            QMessageBox.critical(
                self,
                "Git Błąd",
                "Nie znaleziono repozytorium Git w wybranym katalogu.")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Git Błąd",
                f"Wystąpił błąd podczas pobierania logów: {e}")

    def select_git_repo(self):
        path = QFileDialog.getExistingDirectory(
            self, "Wybierz Repozytorium Git", "")
        if path:
            try:
                repo = git.Repo(path)
                self.git_repo_path = path
                QMessageBox.information(
                    self, "Git Repo", f"Wybrane repozytorium: {path}")
            except git.exc.InvalidGitRepositoryError:
                QMessageBox.critical(
                    self, "Git Błąd", "Wybrany folder nie jest repozytorium Git.")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
