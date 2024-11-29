from unittest.mock import MagicMock
import sys
import os
import pytest
from unittest.mock import MagicMock
from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtWidgets import QApplication

# Dodaj główny katalog projektu do sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import twoich klas
from main import LineNumberArea
from main import GenericHighlighter
from main import CodeEditor  # Importujemy CodeEditor zamiast QTextEdit

# Przygotowanie mocków
@pytest.fixture
def test_basic_functionality():
    print("Test uruchomiony")
    editor = CodeEditor()  # Tworzymy CodeEditor, a nie QTextEdit
    mock_highlighter = MagicMock()
    print("Highlighter stworzony")
    editor.setHighlighter(mock_highlighter)  # Teraz wywołujemy na CodeEditor
    print("Highlighter przypisany")
    assert mock_highlighter is not None

@pytest.fixture
def mock_code_editor():
    editor = CodeEditor()  # Tworzymy CodeEditor, a nie QTextEdit
    highlighter = MagicMock()  # Tworzymy mocka dla highlightera
    editor.setHighlighter(highlighter)  # Przypisujemy mockowanego highlightera do editor
    return editor

# Fixture uruchamiająca QApplication
@pytest.fixture(scope="module")
def app():
    app = QApplication([])  # Tworzymy QApplication tylko raz na całą sesję testową
    yield app
    app.quit()  # Kończymy aplikację po testach

# Testowanie LineNumberArea
def test_line_number_area_size_hint(mock_code_editor, app):
    area = LineNumberArea(mock_code_editor)
    assert area.sizeHint() == QSize(50, 0)

def test_line_number_area_paint_event(mock_code_editor, app):
    area = LineNumberArea(mock_code_editor)
    area.paintEvent(None)  # Sprawdzamy, czy wywoła się paintEvent, nie robimy asercji, bo to nie jest test widoku

def test_line_number_area_mouse_press_event(mock_code_editor, app):
    area = LineNumberArea(mock_code_editor)
    mock_clicked_signal = MagicMock()  # Mockujemy sygnał
    area.clicked.connect(mock_clicked_signal)
    # Test kliknięcia (symulacja kliknięcia w pierwszej linii)
    mock_event = MockMouseEvent(Qt.MouseButton.LeftButton, 10, 10)
    area.mousePressEvent(mock_event)
    # Sprawdzamy, czy sygnał clicked został wyemitowany z numerem linii
    mock_clicked_signal.emit.assert_called_with(1)

# Testowanie GenericHighlighter
def test_generic_highlighter_init(app):
    editor = CodeEditor()  # Używamy CodeEditor
    highlighter = GenericHighlighter(editor)
    assert highlighter.lexer is not None  # Sprawdzamy, czy lexer jest poprawnie ustawiony

def test_highlight_block(mock_code_editor, app):
    highlighter = GenericHighlighter(mock_code_editor)  # Przekazujemy mock_code_editor
    highlighter.highlightBlock("def test():")  # Prosty kod
    # Sprawdzamy, czy setFormat jest wywołane odpowiednio
    assert highlighter.setFormat.called

def test_highlight_block_with_error(mock_code_editor, app):
    highlighter = GenericHighlighter(mock_code_editor)  # Przekazujemy mock_code_editor
    highlighter.error_lines = {0: "Some error"}  # Dodajemy błąd do linii 0
    highlighter.highlightBlock("def test():")  # Błąd w linii
    # Sprawdzamy, czy wywołano setFormat z odpowiednimi parametrami
    highlighter.setFormat.assert_any_call(0, len("def test():"), highlighter.error_format)

class MockMouseEvent:
    def __init__(self, button, x, y):
        self.button = button
        self.x = x
        self.y = y
        self.position = MagicMock(return_value=QPoint(x, y))

    def button(self):
        return self.button
