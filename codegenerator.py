import sys
import os
import random
import string
import ast
import subprocess
import tempfile
import re

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QFileDialog, QMessageBox,
    QCheckBox, QPlainTextEdit, QTextEdit
)
from PyQt6.QtGui import (
    QFont, QColor, QTextFormat, QTextCursor, QSyntaxHighlighter, QTextCharFormat,
    QPainter, QKeySequence, QShortcut
)
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSlot

# Definicja motywów
THEMES = {
    "Dark": {
        "bg": QColor("#2b2b2b"),
        "fg": QColor("#ffffff"),
        "line_bg": QColor("#1e1e1e"),
        "line_fg": QColor("#c0c0c0"),
        "keyword": QColor("#569CD6"),
        "string": QColor("#D69D85"),
        "comment": QColor("#6A9955"),
        "decorator": QColor("#C586C0"),
        "function": QColor("#DCDCAA"),
        "class": QColor("#4EC9B0"),
        "number": QColor("#B5CEA8"),
    },
    "Light": {
        "bg": QColor("#ffffff"),
        "fg": QColor("#000000"),
        "line_bg": QColor("#f0f0f0"),
        "line_fg": QColor("#000000"),
        "keyword": QColor("#0000FF"),
        "string": QColor("#A31515"),
        "comment": QColor("#008000"),
        "decorator": QColor("#B000B0"),
        "function": QColor("#795E26"),
        "class": QColor("#267f99"),
        "number": QColor("#098658"),
    }
}

current_theme = "Dark"  # Domyślny motyw

# Mapa konstrukcji do wymaganych importów
CONSTRUCT_IMPORTS = {
    'def': 'import os',
    'try': 'import sys',
    'decorator': 'import functools',
    'async': 'import asyncio',
    'inheritance': 'from another_module import AnotherClass',
    # Dodaj inne konstrukcje i ich importy tutaj
}

# Funkcja generująca losowe nazwy funkcji
def random_function_name(prefix='func_'):
    return prefix + ''.join(random.choices(string.ascii_lowercase, k=5))

# Funkcja generująca losowe nazwy zmiennych
def random_variable_name():
    return ''.join(random.choices(string.ascii_lowercase, k=7))

# Funkcja ładowania modułów z określonej ścieżki
def load_available_modules(module_path):
    available_modules = []
    try:
        for item in os.listdir(module_path):
            if item.endswith('.py') and not item.startswith('_'):
                module_name = os.path.splitext(item)[0]
                available_modules.append(module_name)
            elif os.path.isdir(os.path.join(module_path, item)):
                # Sprawdzenie, czy folder jest modułem pakietu
                if os.path.isfile(os.path.join(module_path, item, '__init__.py')):
                    available_modules.append(item)
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Błąd podczas ładowania modułów: {e}")
    return available_modules

# Funkcja generująca losowy kod z ograniczeniem liczby linii
def generate_code(num_lines, available_modules, introduce_indent_errors=False):
    imports = set()  # Zaczynamy od pustego zbioru importów
    code_body = []
    indent = '    '
    generated_functions = []  # Lista wygenerowanych funkcji jako tuple (nazwa, is_async)
    generated_lines = 0

    # Dodajemy definicję some_coroutine na początku, jeśli asyncio jest dostępne
    if 'asyncio' in available_modules:
        coroutine_def = '''async def some_coroutine():
    await asyncio.sleep(1)'''
        coroutine_lines = coroutine_def.count('\n') + 1
        if generated_lines + coroutine_lines > num_lines:
            coroutine_def = '\n'.join(coroutine_def.split('\n')[:num_lines - generated_lines])
            generated_lines = num_lines
        else:
            code_body.append(coroutine_def)
            generated_lines += coroutine_lines
        imports.add('import asyncio')
        generated_functions.append(('some_coroutine', True))

    while generated_lines < num_lines:
        choice = random.choice(['def', 'async', 'for', 'if', 'variable', 'class', 'try', 'with', 'decorator', 'inheritance'])

        construct_lines = 0
        construct_code = []

        if choice == 'def':
            func_name = random_function_name()
            params = ', '.join([random_variable_name() for _ in range(random.randint(1, 3))])
            construct_code.append(f'def {func_name}({params}):')
            # Dodajemy kilka linii wewnątrz funkcji
            num_var_lines = random.randint(1, 3)
            for _ in range(num_var_lines):
                var = random_variable_name()
                value = random.randint(1, 100)
                line = f'{indent}{var} = {value}'
                if introduce_indent_errors and random.choice([True, False]):
                    # Mieszanie spacji: zamiana indentu na losową liczbę spacji (1-3)
                    line = line.replace(indent, ' ' * random.randint(1, 3))
                construct_code.append(line)
            construct_code.append(f'{indent}pass  # TODO: implement function')
            construct_lines = 2 + num_var_lines  # def + variables + pass

            # Dodaj wymagane importy
            import_statement = CONSTRUCT_IMPORTS.get('def', '')
            if import_statement:
                imports.update(import_statement.split())

            if generated_lines + construct_lines > num_lines:
                remaining = num_lines - generated_lines
                if remaining <= 0:
                    break
                # Dodajemy tylko potrzebne linie
                construct_code = construct_code[:remaining]
                generated_lines += len(construct_code)
                code_body.extend(construct_code)
                break
            else:
                code_body.extend(construct_code)
                generated_lines += construct_lines
                generated_functions.append((func_name, False))

def generate_code(num_lines, available_modules, introduce_indent_errors=False):
    imports = set()  # Zaczynamy od pustego zbioru importów
    code_body = []
    indent = '    '
    generated_functions = []  # Lista wygenerowanych funkcji jako tuple (nazwa, is_async)
    generated_lines = 0

    # Dodajemy definicję some_coroutine na początku, jeśli asyncio jest dostępne
    if 'asyncio' in available_modules:
        coroutine_def = '''async def some_coroutine():
    await asyncio.sleep(1)'''
        coroutine_lines = coroutine_def.count('\n') + 1
        if generated_lines + coroutine_lines > num_lines:
            coroutine_def = '\n'.join(coroutine_def.split('\n')[:num_lines - generated_lines])
            generated_lines = num_lines
        else:
            code_body.append(coroutine_def)
            generated_lines += coroutine_lines
        imports.add('import asyncio')
        generated_functions.append(('some_coroutine', True))

    while generated_lines < num_lines:
        choice = random.choice([
            'def', 'async', 'for', 'if', 'variable',
            'class', 'try', 'with', 'decorator', 'inheritance'
        ])

        construct_lines = 0
        construct_code = []

        # Przetwarzanie różnych typów konstrukcji
        if choice == 'def':
            func_name = random_function_name()
            params = ', '.join([random_variable_name() for _ in range(random.randint(1, 3))])
            construct_code.append(f'def {func_name}({params}):')

            num_var_lines = random.randint(1, 3)
            for _ in range(num_var_lines):
                var = random_variable_name()
                value = random.randint(1, 100)
                line = f'{indent}{var} = {value}'
                if introduce_indent_errors and random.choice([True, False]):
                    line = line.replace(indent, ' ' * random.randint(1, 3))
                construct_code.append(line)

            construct_code.append(f'{indent}pass  # TODO: implement function')
            construct_lines = 2 + num_var_lines

            # Dodaj wymagane importy
            import_statement = CONSTRUCT_IMPORTS.get('def', '')
            if import_statement:
                imports.add(import_statement)

        elif choice == 'async':
            if 'asyncio' not in available_modules:
                continue
            func_name = random_function_name()
            params = ', '.join([random_variable_name() for _ in range(random.randint(1, 3))])
            construct_code.append(f'async def {func_name}({params}):')

            num_var_lines = random.randint(1, 3)
            for _ in range(num_var_lines):
                var = random_variable_name()
                value = random.randint(1, 100)
                line = f'{indent}{var} = {value}'
                construct_code.append(line)

            construct_code.append(f'{indent}pass  # TODO: implement async function')
            construct_lines = 2 + num_var_lines

            # Dodaj wymagane importy
            import_statement = CONSTRUCT_IMPORTS.get('async', '')
            if import_statement:
                imports.add(import_statement)

            generated_functions.append((func_name, True))

        elif choice == 'for':
            var = random_variable_name()
            iterable = random_variable_name()
            construct_code.append(f'for {var} in {iterable}:')
            line = f'{indent}pass  # TODO: implement loop'
            construct_code.append(line)
            construct_lines = 2

        elif choice == 'if':
            condition_var = random_variable_name()
            condition_value = random.randint(1, 100)
            construct_code.append(f'if {condition_var} == {condition_value}:')
            line = f'{indent}pass  # TODO: implement condition'
            construct_code.append(line)
            construct_lines = 2

        elif choice == 'variable':
            var = random_variable_name()
            value = random.randint(1, 100)
            construct_code.append(f'{var} = {value}')
            construct_lines = 1

        elif choice == 'class':
            class_name = ''.join(random.choices(string.ascii_uppercase, k=1)) + ''.join(random.choices(string.ascii_lowercase, k=5))
            construct_code.append(f'class {class_name}:')
            construct_code.append(f'{indent}def __init__(self):')
            line = f'{indent*2}pass  # TODO: implement constructor'
            construct_code.append(line)
            construct_lines = 3

        elif choice == 'try':
            construct_code.append('try:')
            line = f'{indent}pass  # TODO: implement try block'
            construct_code.append(line)
            construct_code.append('except Exception as e:')
            construct_code.append(f'{indent}print(e)')
            construct_lines = 4

        elif choice == 'with':
            resource = random_variable_name()
            construct_code.append(f'with open("{resource}", "r") as f:')
            construct_code.append(f'{indent}data = f.read()')
            construct_lines = 2

        elif choice == 'decorator':
            decorator_name = random_function_name(prefix='decorator_')
            construct_code.append(f'@{decorator_name}')
            func_name = random_function_name()
            params = ', '.join([random_variable_name() for _ in range(random.randint(1, 3))])
            construct_code.append(f'def {func_name}({params}):')
            construct_code.append(f'{indent}pass  # TODO: implement decorated function')
            construct_lines = 3
            generated_functions.append((func_name, False))

        elif choice == 'inheritance':
            parent_class = random.choice(['BaseClass', 'AnotherClass'])
            child_class = ''.join(random.choices(string.ascii_uppercase, k=1)) + ''.join(random.choices(string.ascii_lowercase, k=5))
            construct_code.append(f'class {child_class}({parent_class}):')
            construct_code.append(f'{indent}def __init__(self):')
            construct_code.append(f'{indent*2}super().__init__()')
            construct_code.append(f'{indent*2}pass  # TODO: implement child class')
            construct_lines = 4
            generated_functions.append((child_class, False))

        # Dodawanie kodu do body
        if generated_lines + construct_lines > num_lines:
            remaining = num_lines - generated_lines
            construct_code = construct_code[:remaining]
            code_body.extend(construct_code)
            break
        else:
            code_body.extend(construct_code)
            generated_lines += construct_lines

    # Generowanie sekcji importów
    import_section = '\n'.join(sorted(imports)) + '\n\n'

    # Tworzenie funkcji main
    main_def = '\n\nasync def main():\n'
    for func, is_async in generated_functions[:10]:
        if is_async:
            main_def += f'{indent}await {func}()\n'
        else:
            main_def += f'{indent}{func}()\n'

    # Jeśli dostępne asyncio, dodaj jego uruchomienie
    if 'asyncio' in available_modules:
        main_def += '\nasyncio.run(main())\n'

    # Składanie pełnego kodu
    full_code = f'{import_section}' + '\n'.join(code_body) + main_def
    return full_code
def validate_code(code):
    try:
        ast.parse(code)
        return True, "Kod jest poprawny."
    except SyntaxError as se:
        return False, f"Błąd składni: {se}"

# Klasa do obsługi numeracji linii
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.lineNumberAreaPaintEvent(event)

# Klasa do obsługi wysokiego poziomu edytora kodu
class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        # Zastąpienie width() przez horizontalAdvance()
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

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)
        theme = THEMES[current_theme]
        painter.fillRect(event.rect(), theme["line_bg"])

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(theme["line_fg"])
                painter.drawText(0, top, self.line_number_area.width()-5, self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            
            # Stworzenie koloru podświetlenia
            theme = THEMES[current_theme]
            line_color = theme["line_bg"].lighter(120) if current_theme == "Light" else theme["line_bg"].darker(120)

            # Tworzenie formatowania linii
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            
            # Ustawienie kursora na aktualną linię
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            
            # Dodanie do listy selekcji
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

# Klasa do kolorowania składni
class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = THEMES[current_theme]
        self.highlighting_rules = []

        # Definicje tagów
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(self.theme["keyword"])
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = r'\b(import|from|def|class|async|await|for|in|if|elif|else|try|except|with|as|pass|break|continue|return|yield|raise)\b'
        self.highlighting_rules.append((re.compile(keywords), keyword_format))

        string_format = QTextCharFormat()
        string_format.setForeground(self.theme["string"])
        strings = r'(\"\"\".*?\"\"\"|\'\'\'.*?\'\'\'|\".*?\"|\'.*?\')'
        self.highlighting_rules.append((re.compile(strings, re.DOTALL), string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(self.theme["comment"])
        comments = r'#.*'
        self.highlighting_rules.append((re.compile(comments), comment_format))

        decorator_format = QTextCharFormat()
        decorator_format.setForeground(self.theme["decorator"])
        decorators = r'@\w+'
        self.highlighting_rules.append((re.compile(decorators), decorator_format))

        number_format = QTextCharFormat()
        number_format.setForeground(self.theme["number"])
        numbers = r'\b\d+\b'
        self.highlighting_rules.append((re.compile(numbers), number_format))

        function_format = QTextCharFormat()
        function_format.setForeground(self.theme["function"])
        functions = r'\bdef\s+(\w+)'
        self.highlighting_rules.append((re.compile(functions), function_format))

        class_format = QTextCharFormat()
        class_format.setForeground(self.theme["class"])
        classes = r'\bclass\s+(\w+)'
        self.highlighting_rules.append((re.compile(classes), class_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                if match.lastindex:
                    # Jeśli jest grupa, użyj jej zakresu
                    start, end = match.span(1)
                self.setFormat(start, end - start, fmt)

        self.setCurrentBlockState(0)

    def set_theme(self, theme):
        self.theme = THEMES[theme]
        self.highlighting_rules.clear()

        # Aktualizacja definicji tagów
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(self.theme["keyword"])
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = r'\b(import|from|def|class|async|await|for|in|if|elif|else|try|except|with|as|pass|break|continue|return|yield|raise)\b'
        self.highlighting_rules.append((re.compile(keywords), keyword_format))

        string_format = QTextCharFormat()
        string_format.setForeground(self.theme["string"])
        strings = r'(\"\"\".*?\"\"\"|\'\'\'.*?\'\'\'|\".*?\"|\'.*?\')'
        self.highlighting_rules.append((re.compile(strings, re.DOTALL), string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(self.theme["comment"])
        comments = r'#.*'
        self.highlighting_rules.append((re.compile(comments), comment_format))

        decorator_format = QTextCharFormat()
        decorator_format.setForeground(self.theme["decorator"])
        decorators = r'@\w+'
        self.highlighting_rules.append((re.compile(decorators), decorator_format))

        number_format = QTextCharFormat()
        number_format.setForeground(self.theme["number"])
        numbers = r'\b\d+\b'
        self.highlighting_rules.append((re.compile(numbers), number_format))

        function_format = QTextCharFormat()
        function_format.setForeground(self.theme["function"])
        functions = r'\bdef\s+(\w+)'
        self.highlighting_rules.append((re.compile(functions), function_format))

        class_format = QTextCharFormat()
        class_format.setForeground(self.theme["class"])
        classes = r'\bclass\s+(\w+)'
        self.highlighting_rules.append((re.compile(classes), class_format))

        self.rehighlight()

# Główna klasa okna aplikacji
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Code Generator")
        self.setGeometry(100, 100, 1200, 900)

        # Centralny widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout główny
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Ramka do wyboru liczby linii, opcji i ścieżki modułów
        frame_options = QHBoxLayout()

        label_lines = QLabel("Wybierz liczbę linii:")
        frame_options.addWidget(label_lines)

        self.line_option = QComboBox()
        self.line_option.addItems(["100", "200", "300", "500", "1000"])
        self.line_option.setCurrentIndex(0)
        frame_options.addWidget(self.line_option)

        self.indent_error_var = QCheckBox("Generuj z błędami w wcięciach")
        frame_options.addWidget(self.indent_error_var)

        self.generate_button = QPushButton("Generuj Kod")
        self.generate_button.clicked.connect(self.generate_code_handler)
        frame_options.addWidget(self.generate_button)

        self.save_button = QPushButton("Zapisz do Pliku")
        self.save_button.clicked.connect(self.save_code_handler)
        frame_options.addWidget(self.save_button)

        self.run_button = QPushButton("Uruchom Kod")
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(self.run_code_handler)
        frame_options.addWidget(self.run_button)

        self.module_path_button = QPushButton("Wybierz Ścieżkę Modułów")
        self.module_path_button.clicked.connect(self.choose_module_path)
        frame_options.addWidget(self.module_path_button)

        self.format_button = QPushButton("Sformatuj Kod (black)")
        self.format_button.clicked.connect(self.format_code)
        frame_options.addWidget(self.format_button)

        frame_options.addStretch()
        main_layout.addLayout(frame_options)

        # Edytor kodu z numeracją linii
        self.output_editor = CodeEditor()
        self.output_editor.setFont(QFont("Consolas", 12))
        self.highlighter = Highlighter(self.output_editor.document())
        main_layout.addWidget(self.output_editor)

        # Skrót Ctrl+A
        self.output_editor.shortcut = QShortcut(QKeySequence("Ctrl+A"), self.output_editor)
        self.output_editor.shortcut.activated.connect(self.select_all)

        # Inicjalizacja ścieżki do modułów
        self.module_path = self.get_default_module_path()
        self.available_modules = load_available_modules(self.module_path)

        # Menu motywów
        self.create_menu()

    def get_default_module_path(self):
        default_module_path = r"C:\Python skrypty\venv\Lib\site-packages"  # Poprawiona ścieżka do site-packages
        if not os.path.exists(default_module_path):
            default_module_path = QFileDialog.getExistingDirectory(self, "Wybierz Ścieżkę do site-packages")
        return default_module_path

    def create_menu(self):
        menu_bar = self.menuBar()
        theme_menu = menu_bar.addMenu("Motyw")

        for theme in THEMES:
            action = theme_menu.addAction(theme)
            action.triggered.connect(lambda checked, t=theme: self.switch_theme(t))

    def switch_theme(self, theme_name):
        global current_theme
        current_theme = theme_name
        theme = THEMES[theme_name]

        # Ustawienie kolorów edytora
        self.output_editor.setStyleSheet(f"QPlainTextEdit {{ background-color: {theme['bg'].name()}; color: {theme['fg'].name()}; }}")
        self.output_editor.line_number_area.setStyleSheet(f"background-color: {theme['line_bg'].name()}; color: {theme['line_fg'].name()};")

        # Aktualizacja highlightera
        self.highlighter.set_theme(theme_name)

    def select_all(self):
        cursor = self.output_editor.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        self.output_editor.setTextCursor(cursor)

    def generate_code_handler(self):
        try:
            num_lines = int(self.line_option.currentText())
            introduce_indent_errors = self.indent_error_var.isChecked()
            code = generate_code(num_lines, self.available_modules, introduce_indent_errors)

            # Walidacja kodu przed wyświetleniem
            is_valid, message = validate_code(code)
            self.output_editor.setPlainText(code)
            if is_valid:
                self.run_button.setEnabled(True)
                QMessageBox.information(self, "Walidacja", message)
            else:
                self.run_button.setEnabled(False)
                QMessageBox.critical(self, "Walidacja", message)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Wystąpił błąd: {e}")

    def save_code_handler(self):
        try:
            code = self.output_editor.toPlainText()
            if not code.strip():
                QMessageBox.warning(self, "Warning", "Brak kodu do zapisania.")
                return
            filename, _ = QFileDialog.getSaveFileName(self, "Zapisz Kod", "", "Python Files (*.py);;All Files (*)")
            if filename:
                with open(filename, 'w') as f:
                    f.write(code)
                QMessageBox.information(self, "Sukces", f"Kod zapisany do {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Wystąpił błąd podczas zapisywania: {e}")

    def run_code_handler(self):
        try:
            code = self.output_editor.toPlainText()
            if not code.strip():
                QMessageBox.warning(self, "Warning", "Brak kodu do uruchomienia.")
                return

            # Ostrzeżenie o bezpieczeństwie
            confirm = QMessageBox.question(
                self, "Ostrzeżenie",
                "Czy na pewno chcesz uruchomić wygenerowany kod?\nUpewnij się, że rozumiesz, co robi kod.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return

            # Zapisz kod do tymczasowego pliku
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode='w') as tmp_file:
                tmp_file.write(code)
                tmp_filename = tmp_file.name

            # Uruchom kod w nowym procesie
            result = subprocess.run([sys.executable, tmp_filename], capture_output=True, text=True)

            # Usuń tymczasowy plik
            os.remove(tmp_filename)

            # Wyświetl wyniki
            output = ""
            if result.stdout:
                output += f"Output:\n{result.stdout}\n"
            if result.stderr:
                output += f"Błędy:\n{result.stderr}\n"
            if output:
                QMessageBox.information(self, "Wynik Uruchomienia", output)
            else:
                QMessageBox.information(self, "Wynik Uruchomienia", "Kod został uruchomiony bez wyjścia.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Wystąpił błąd podczas uruchamiania kodu: {e}")

    def format_code(self):
        try:
            code = self.output_editor.toPlainText()
            if not code.strip():
                QMessageBox.warning(self, "Warning", "Brak kodu do sformatowania.")
                return
            # Zapisz kod do tymczasowego pliku
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode='w') as tmp_file:
                tmp_file.write(code)
                tmp_filename = tmp_file.name

            # Uruchom black na tym pliku
            result = subprocess.run(['black', tmp_filename], capture_output=True, text=True)

            if result.returncode != 0:
                QMessageBox.critical(self, "Formatowanie", f"Błąd podczas formatowania kodu:\n{result.stderr}")
                os.remove(tmp_filename)
                return

            # Odczytaj sformatowany kod
            with open(tmp_filename, 'r') as f:
                formatted_code = f.read()

            # Usuń tymczasowy plik
            os.remove(tmp_filename)

            # Wyświetl sformatowany kod
            self.output_editor.setPlainText(formatted_code)
            QMessageBox.information(self, "Formatowanie", "Kod został sformatowany przy użyciu black.")
        except FileNotFoundError:
            QMessageBox.critical(self, "Formatowanie", "Narzędzie 'black' nie jest zainstalowane.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Wystąpił błąd podczas formatowania kodu: {e}")

    def choose_module_path(self):
        try:
            selected_path = QFileDialog.getExistingDirectory(self, "Wybierz Ścieżkę do site-packages")
            if selected_path:
                self.module_path = selected_path
                self.available_modules = load_available_modules(self.module_path)
                QMessageBox.information(self, "Moduły", f"Załadowano {len(self.available_modules)} modułów z {self.module_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Wystąpił błąd: {e}")

# Uruchomienie aplikacji
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
