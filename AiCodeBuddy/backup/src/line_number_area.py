# src/line_number_area.py

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import QSize, Qt, pyqtSignal

class LineNumberArea(QWidget):
    clicked = pyqtSignal(int, Qt.KeyboardModifier)

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
                    modifiers = event.modifiers()
                    self.clicked.emit(block_number, modifiers)
                    break
                block = block.next()
                top = bottom
                bottom = top + int(self.code_editor.blockBoundingRect(block).height())
                block_number += 1

        super().mousePressEvent(event)