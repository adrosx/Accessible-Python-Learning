# src/syntax_highlighter.py

from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.styles import get_style_by_name
import re
import json

class GenericHighlighter(QSyntaxHighlighter):
    def __init__(self, document, language='python', theme='friendly'):
        super().__init__(document)
        self.formats = {}
        self.error_format = QTextCharFormat()
        self.error_format.setUnderlineColor(QColor("red"))
        self.error_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
        self.error_lines = {}

        self.theme = theme
        # Ładowanie stylów Pygments
        self.load_pygments_styles()

        self.set_language(language)

    def load_pygments_styles(self):
        """
        Ładuje style Pygments dla wybranego motywu.
        """
        self.formats = {}
        style = get_style_by_name(self.theme)
        for token, style_def in style.styles.items():
            qt_format = QTextCharFormat()
            if style_def:
                style_parts = style_def.split()
                for part in style_parts:
                    if re.match(r'^#[0-9A-Fa-f]{6}$', part):
                        qt_format.setForeground(QColor(part))
                    elif part.lower() == 'bold':
                        qt_format.setFontWeight(QFont.Weight.Bold)
                    elif part.lower() == 'italic':
                        qt_format.setFontItalic(True)
            self.formats[token] = qt_format

    def set_language(self, language):
        try:
            self.lexer = get_lexer_by_name(language)
        except Exception:
            self.lexer = get_lexer_by_name('text')
        self.rehighlight()

    def highlightBlock(self, text):
        """
        Podświetla blok tekstu.
        """
        current_position = 0
        for token, content in lex(text, self.lexer):
            length = len(content)
            if token in self.formats:
                self.setFormat(current_position, length, self.formats[token])
            current_position += length

        # Podświetlanie błędów po podświetleniu składni
        block_number = self.currentBlock().blockNumber()
        if block_number in self.error_lines:
            error_format = QTextCharFormat()
            error_format.setUnderlineColor(QColor("red"))
            error_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
            self.setFormat(0, len(text), error_format)