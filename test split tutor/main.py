# main.py

import sys
import os
import json
import ast
import random
import logging
import pyttsx3
import keyword
import webbrowser
import re
import glob
import shutil

from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QSplitter,
    QMessageBox, QFileDialog, QPlainTextEdit, QStatusBar, QInputDialog,
    QColorDialog, QSlider, QDialog, QDialogButtonBox, QCheckBox, QComboBox, QSpinBox, QFormLayout,
    QTreeWidget, QTreeWidgetItem, QToolBar, QFontDialog, QListWidget, QListWidgetItem, QTabWidget, QLineEdit
)
from PyQt6.QtCore import Qt, QProcess, QSettings, QTimer, QRegularExpression, QThread, pyqtSignal
from PyQt6.QtGui import (
    QFont, QColor, QSyntaxHighlighter, QTextCharFormat, QIcon,
    QPainter, QTextCursor, QAction
)

# ---------------------------------------------
#            Configuration for Logging
# ---------------------------------------------
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ---------------------------------------------
#          TTS Worker Class for Async Processing
# ---------------------------------------------
class TTSWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, text, voice_id, rate):
        super().__init__()
        self.text = text
        self.voice_id = voice_id
        self.rate = rate
        self.engine = pyttsx3.init()

    def run(self):
        try:
            self.engine.setProperty('voice', self.voice_id)
            self.engine.setProperty('rate', self.rate)
            self.engine.say(self.text)
            self.engine.runAndWait()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

# ---------------------------------------------
#          Settings Dialog Class
# ---------------------------------------------
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.parent().translate("menu.Settings"))
        self.settings = QSettings("PythonTutorApp", "PythonTutor")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Creating settings form
        form_layout = QFormLayout()

        # Font
        font_button = QPushButton(self.parent().translate("labels.Change Font"))
        font_button.setToolTip(self.parent().translate("labels.Choose Application Font"))
        font_button.clicked.connect(self.change_font)
        form_layout.addRow(QLabel(self.parent().translate("labels.Application Font:")), font_button)

        # Font size
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 48)
        font_size = self.settings.value("font_size", 12, type=int)
        self.font_size_spinbox.setValue(font_size)
        self.font_size_spinbox.setToolTip(self.parent().translate("labels.Choose Font Size"))
        self.font_size_spinbox.valueChanged.connect(self.update_font_preview)
        form_layout.addRow(QLabel(self.parent().translate("labels.Font Size:")), self.font_size_spinbox)

        # Font preview
        self.font_preview_label = QLabel(self.parent().translate("labels.Sample Text"))
        self.update_font_preview()
        form_layout.addRow(QLabel(self.parent().translate("labels.Font Preview:")), self.font_preview_label)

        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItem(self.parent().translate("labels.Light Theme"), "light")
        self.theme_combo.addItem(self.parent().translate("labels.Dark Theme"), "dark")
        theme = self.settings.value("theme", "light")
        index = self.theme_combo.findData(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        self.theme_combo.setToolTip(self.parent().translate("labels.Choose Application Theme"))
        form_layout.addRow(QLabel(self.parent().translate("labels.Application Theme:")), self.theme_combo)

        # Interface scaling
        self.interface_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.interface_scale_slider.setRange(50, 200)
        interface_scale = self.settings.value("interface_scale", 100, type=int)
        self.interface_scale_slider.setValue(interface_scale)
        self.interface_scale_slider.setToolTip(self.parent().translate("labels.Adjust Interface Scale"))
        self.interface_scale_label = QLabel(f"{self.interface_scale_slider.value()}%")
        self.interface_scale_slider.valueChanged.connect(
            lambda value: self.interface_scale_label.setText(f"{value}%")
        )
        interface_scale_layout = QHBoxLayout()
        interface_scale_layout.addWidget(self.interface_scale_slider)
        interface_scale_layout.addWidget(self.interface_scale_label)
        form_layout.addRow(QLabel(self.parent().translate("labels.Interface Scale:")), interface_scale_layout)

        # Customizing colors
        color_buttons_layout = QHBoxLayout()
        bg_color_button = QPushButton(self.parent().translate("labels.Background Color"))
        bg_color_button.setToolTip(self.parent().translate("labels.Choose Background Color"))
        bg_color_button.clicked.connect(self.change_bg_color)
        color_buttons_layout.addWidget(bg_color_button)
        text_color_button = QPushButton(self.parent().translate("labels.Text Color"))
        text_color_button.setToolTip(self.parent().translate("labels.Choose Text Color"))
        text_color_button.clicked.connect(self.change_text_color)
        color_buttons_layout.addWidget(text_color_button)
        form_layout.addRow(QLabel(self.parent().translate("labels.Customize Colors:")), color_buttons_layout)

        # Color profile
        self.color_profile_combo = QComboBox()
        self.color_profile_combo.addItem(self.parent().translate("labels.Default"), "Default")
        self.color_profile_combo.addItem(self.parent().translate("labels.Protanopia"), "Protanopia")
        self.color_profile_combo.addItem(self.parent().translate("labels.Deuteranopia"), "Deuteranopia")
        self.color_profile_combo.addItem(self.parent().translate("labels.Tritanopia"), "Tritanopia")
        color_profile = self.settings.value("color_profile", "Default")
        index = self.color_profile_combo.findData(color_profile)
        if index >= 0:
            self.color_profile_combo.setCurrentIndex(index)
        self.color_profile_combo.setToolTip(self.parent().translate("labels.Choose Color Profile"))
        form_layout.addRow(QLabel(self.parent().translate("labels.Color Profile:")), self.color_profile_combo)

        # Language selection
        self.language_combo = QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Polski", "pl")
        self.language_combo.addItem("Deutsch", "de")
        self.language_combo.addItem("Français", "fr")
        current_language = self.settings.value("language", "en")
        index = self.language_combo.findData(current_language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        self.language_combo.setToolTip(self.parent().translate("labels.Choose Language"))
        form_layout.addRow(QLabel(self.parent().translate("labels.Language:")), self.language_combo)

        # Simple language mode
        self.simple_language_checkbox = QCheckBox(self.parent().translate("labels.Enabled"))
        simple_language = self.settings.value("simple_language", False, type=bool)
        self.simple_language_checkbox.setChecked(simple_language)
        self.simple_language_checkbox.setToolTip(self.parent().translate("labels.Enable Simple Language Mode"))
        form_layout.addRow(QLabel(self.parent().translate("labels.Simple Language Mode:")), self.simple_language_checkbox)

        # Debug mode
        self.debug_mode_checkbox = QCheckBox(self.parent().translate("labels.Enabled"))
        debug_mode = self.settings.value("debug_mode", False, type=bool)
        self.debug_mode_checkbox.setChecked(debug_mode)
        self.debug_mode_checkbox.setToolTip(self.parent().translate("labels.Enable Debug Mode"))
        form_layout.addRow(QLabel(self.parent().translate("labels.Debug Mode:")), self.debug_mode_checkbox)

        # Speech rate
        self.speech_rate_spinbox = QSpinBox()
        self.speech_rate_spinbox.setRange(50, 300)
        speech_rate = self.settings.value("speech_rate", 150, type=int)
        self.speech_rate_spinbox.setValue(speech_rate)
        self.speech_rate_spinbox.setToolTip(self.parent().translate("labels.Set Speech Rate"))
        form_layout.addRow(QLabel(self.parent().translate("labels.Speech Rate:")), self.speech_rate_spinbox)

        # Enable/Disable TTS
        self.tts_enabled_checkbox = QCheckBox(self.parent().translate("labels.Enabled"))
        tts_enabled = self.settings.value("tts_enabled", True, type=bool)
        self.tts_enabled_checkbox.setChecked(tts_enabled)
        self.tts_enabled_checkbox.setToolTip(self.parent().translate("labels.Enable Text-to-Speech"))
        form_layout.addRow(QLabel(self.parent().translate("labels.Text-to-Speech:")), self.tts_enabled_checkbox)

        # Dyslexia mode
        self.dyslexia_mode_checkbox = QCheckBox(self.parent().translate("labels.Enabled"))
        dyslexia_mode = self.settings.value("dyslexia_mode", False, type=bool)
        self.dyslexia_mode_checkbox.setChecked(dyslexia_mode)
        self.dyslexia_mode_checkbox.setToolTip(self.parent().translate("labels.Enable Dyslexia Mode"))
        form_layout.addRow(QLabel(self.parent().translate("labels.Dyslexia Mode:")), self.dyslexia_mode_checkbox)

        # Tremor mode
        self.tremor_mode_checkbox = QCheckBox(self.parent().translate("labels.Enabled"))
        tremor_mode = self.settings.value("tremor_mode", False, type=bool)
        self.tremor_mode_checkbox.setChecked(tremor_mode)
        self.tremor_mode_checkbox.setToolTip(self.parent().translate("labels.Enable Tremor Mode"))
        form_layout.addRow(QLabel(self.parent().translate("labels.Tremor Mode:")), self.tremor_mode_checkbox)

        # Autism mode
        self.autism_mode_checkbox = QCheckBox(self.parent().translate("labels.Enabled"))
        autism_mode = self.settings.value("autism_mode", False, type=bool)
        self.autism_mode_checkbox.setChecked(autism_mode)
        self.autism_mode_checkbox.setToolTip(self.parent().translate("labels.Enable Autism Mode"))
        form_layout.addRow(QLabel(self.parent().translate("labels.Autism Mode:")), self.autism_mode_checkbox)

        # Add form to layout
        layout.addLayout(form_layout)

        # Reset settings button
        reset_button = QPushButton(self.parent().translate("labels.Reset to Defaults"))
        reset_button.setToolTip(self.parent().translate("labels.Restore Default Settings"))
        reset_button.clicked.connect(self.reset_to_defaults)
        layout.addWidget(reset_button)

        # OK and Cancel buttons
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
            self.settings.setValue("font_size", font.pointSize())
            self.update_font_preview()
            logging.info(f"Font changed to: {font.family()}")

    def update_font_preview(self):
        font_family = self.settings.value("font_family", "Arial")
        font_size = self.font_size_spinbox.value()
        font = QFont(font_family, font_size)
        self.font_preview_label.setFont(font)

    def change_bg_color(self):
        bg_color = QColorDialog.getColor(title=self.parent().translate("titles.Select Background Color"))
        if bg_color.isValid():
            self.settings.setValue("bg_color", bg_color.name())
            logging.info(f"Background color changed to: {bg_color.name()}")

    def change_text_color(self):
        text_color = QColorDialog.getColor(title=self.parent().translate("titles.Select Text Color"))
        if text_color.isValid():
            self.settings.setValue("text_color", text_color.name())
            logging.info(f"Text color changed to: {text_color.name()}")

    def reset_to_defaults(self):
        reply = QMessageBox.question(
            self,
            self.parent().translate("labels.Reset Settings"),
            self.parent().translate("messages.Confirm Reset Settings"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.settings.clear()
            self.settings.sync()
            QMessageBox.information(self, self.parent().translate("labels.Reset Settings"), self.parent().translate("messages.Settings Reset"))
            self.initUI()
            logging.info("Settings have been reset to default.")

    def accept(self):
        # Save settings before closing
        self.settings.setValue("font_size", self.font_size_spinbox.value())
        self.settings.setValue("font_family", self.settings.value("font_family", "Arial"))
        self.settings.setValue("theme", self.theme_combo.currentData())
        self.settings.setValue("interface_scale", self.interface_scale_slider.value())
        self.settings.setValue("simple_language", self.simple_language_checkbox.isChecked())
        self.settings.setValue("debug_mode", self.debug_mode_checkbox.isChecked())
        self.settings.setValue("speech_rate", self.speech_rate_spinbox.value())
        self.settings.setValue("dyslexia_mode", self.dyslexia_mode_checkbox.isChecked())
        self.settings.setValue("color_profile", self.color_profile_combo.currentData())
        self.settings.setValue("tremor_mode", self.tremor_mode_checkbox.isChecked())
        self.settings.setValue("autism_mode", self.autism_mode_checkbox.isChecked())
        self.settings.setValue("tts_enabled", self.tts_enabled_checkbox.isChecked())
        selected_language = self.language_combo.currentData()
        self.settings.setValue("language", selected_language)

        # Voice selection
        self.settings.setValue("tts_voice", self.parent().engine.getProperty('voice'))

        super().accept()
        self.parent().load_language()
        self.parent().update_stylesheet()
        self.parent().apply_font_settings()
        self.parent().set_tts_voice()

# ---------------------------------------------
#          Syntax Highlighting Class
# ---------------------------------------------
class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#0000FF"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        keywords = keyword.kwlist

        for word in keywords:
            pattern = f"\\b{word}\\b"
            regex = QRegularExpression(pattern)
            self.highlighting_rules.append((regex, keyword_format))

        # Operators
        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor("#FF00FF"))
        operator_pattern = QRegularExpression(r"[+\-*/%=<>!]+")
        self.highlighting_rules.append((operator_pattern, operator_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#008000"))
        string_patterns = [
            QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'),
            QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'")
        ]
        for pattern in string_patterns:
            self.highlighting_rules.append((pattern, string_format))

        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#AAAAAA"))
        comment_pattern = QRegularExpression(r"#.*")
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
#          Line Number Area Class
# ---------------------------------------------
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QtCore.QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)

# ---------------------------------------------
#          Code Editor Class with Line Numbers
# ---------------------------------------------
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

# ---------------------------------------------
#          Main Application Class
# ---------------------------------------------
class PythonTutorApp(QMainWindow):
    def __init__(self, user_lessons_file='user_lessons.json', progress_file='progress.json'):
        super().__init__()
        self.settings = QSettings("PythonTutorApp", "PythonTutor")
        self.user_lessons_file = user_lessons_file
        self.progress_file = progress_file

        # Load language
        self.load_language()

        self.setWindowTitle(self.translate("app_title"))
        self.resize(1200, 800)
        self.lessons = []

        # Initialize pyttsx3 engine
        self.engine = pyttsx3.init()
        speech_rate = self.settings.value("speech_rate", 150, type=int)
        self.engine.setProperty('rate', speech_rate)  # Set speech rate

        # Set TTS voice based on language
        self.set_tts_voice()

        # Initialize TTS queue and state
        self.tts_queue = []
        self.tts_busy = False

        self.apply_tts_enabled()

        # Initialize progress
        self.completed_lessons = self.load_progress()

        self.initUI()
        self.load_lessons()
        self.load_user_lessons_from_file(self.user_lessons_file)  # Load user lessons

        # Load examples from file
        self.load_examples_from_file('examples.txt')

        # Initialize assistant
        self.assistant_steps = [
            self.translate("hints.Introduction"),
            self.translate("hints.Indentation and Code Structure"),
            self.translate("hints.Fix Errors in Code"),
            # Add more interactive steps as needed
        ]
        self.current_assistant_step = 0

        logging.info("Application has been initialized.")

    # ---------------------------------------------
    #         Loading Language File
    # ---------------------------------------------
    def load_language(self):
        language = self.settings.value("language", "en")
        language_file = os.path.join("languages", f"{language}.json")
        try:
            with open(language_file, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
            logging.info(f"Language loaded: {language}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot load language file:\n{e}")
            logging.error(f"Cannot load language file: {e}")
            self.translations = {}

    def translate(self, key):
        keys = key.split('.')
        result = self.translations
        for k in keys:
            result = result.get(k, {})
        if isinstance(result, str):
            return result
        else:
            return key  # If translation is missing, return the key

    # ---------------------------------------------
    #     Initializing the User Interface
    # ---------------------------------------------
    def initUI(self):
        # Main central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main horizontal layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Lesson panel
        self.lesson_tree = QTreeWidget()
        self.lesson_tree.setHeaderLabel(self.translate("labels.Lessons"))
        self.lesson_tree.itemClicked.connect(self.load_lesson)
        self.lesson_tree.setAccessibleName("Lesson List")

        # History panel
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.load_lesson_from_history)
        self.history_list.setAccessibleName("Lesson History List")

        # Buttons for lesson management
        lesson_button_layout = QHBoxLayout()
        add_lesson_button = QPushButton(self.translate("labels.New Lesson"))
        add_lesson_button.clicked.connect(self.add_new_lesson)
        add_lesson_button.setAccessibleName("Add New Lesson Button")
        edit_lesson_button = QPushButton(self.translate("labels.Edit Lesson"))
        edit_lesson_button.clicked.connect(self.edit_lesson)
        edit_lesson_button.setAccessibleName("Edit Lesson Button")
        delete_lesson_button = QPushButton(self.translate("labels.Delete Lesson"))
        delete_lesson_button.clicked.connect(self.delete_lesson)
        delete_lesson_button.setAccessibleName("Delete Lesson Button")
        delete_category_button = QPushButton(self.translate("labels.Delete Category"))
        delete_category_button.clicked.connect(self.delete_category)
        delete_category_button.setAccessibleName("Delete Category Button")

        lesson_button_layout.addWidget(add_lesson_button)
        lesson_button_layout.addWidget(edit_lesson_button)
        lesson_button_layout.addWidget(delete_lesson_button)
        lesson_button_layout.addWidget(delete_category_button)

        # Adding lesson tree and buttons to layout
        lesson_panel = QWidget()
        lesson_layout = QVBoxLayout()
        lesson_panel.setLayout(lesson_layout)
        lesson_layout.addWidget(self.lesson_tree)
        lesson_layout.addLayout(lesson_button_layout)

        # History panel
        history_panel = QWidget()
        history_layout = QVBoxLayout()
        history_panel.setLayout(history_layout)
        history_layout.addWidget(self.history_list)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(lesson_panel, self.translate("labels.Lessons"))
        self.tabs.addTab(history_panel, self.translate("labels.History"))
        self.tabs.setAccessibleName("Lesson and History Tabs")

        # Lesson content panel
        self.lesson_content = QTextEdit()
        self.lesson_content.setReadOnly(True)
        self.lesson_content.setAccessibleName("Lesson Content")

        # Buttons in the lesson content panel
        lesson_content_buttons = QHBoxLayout()
        play_content_button = QPushButton(self.translate("actions.Play Lesson Content"))
        play_content_button.clicked.connect(self.play_lesson_content)
        play_content_button.setAccessibleName("Play Lesson Content Button")
        lesson_content_buttons.addWidget(play_content_button)

        # Adding buttons to the lesson content layout
        lesson_content_widget = QWidget()
        lesson_content_widget.setLayout(lesson_content_buttons)

        # Code editor
        self.code_editor = CodeEditor()
        self.highlighter = PythonHighlighter(self.code_editor.document())
        self.code_editor.textChanged.connect(self.real_time_analysis)
        self.code_editor.setAccessibleName("Code Editor")

        # Output console
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setStyleSheet("background-color: black; color: white;")
        self.output_console.setAccessibleName("Output Console")

        # Font size adjustment buttons
        font_button_layout = QHBoxLayout()

        small_font_button = QPushButton("A-")
        small_font_button.setToolTip(self.translate("tooltips.Small Font"))
        small_font_button.clicked.connect(self.set_small_font)
        small_font_button.setAccessibleName("Decrease Font Size Button")

        normal_font_button = QPushButton("A")
        normal_font_button.setToolTip(self.translate("tooltips.Normal Font"))
        normal_font_button.clicked.connect(self.set_normal_font)
        normal_font_button.setAccessibleName("Normal Font Size Button")

        large_font_button = QPushButton("A+")
        large_font_button.setToolTip(self.translate("tooltips.Large Font"))
        large_font_button.clicked.connect(self.set_large_font)
        large_font_button.setAccessibleName("Increase Font Size Button")

        font_button_layout.addWidget(small_font_button)
        font_button_layout.addWidget(normal_font_button)
        font_button_layout.addWidget(large_font_button)

        # Control buttons
        self.run_button = QPushButton(self.translate("actions.Run Code"))
        self.run_button.clicked.connect(self.run_code)
        self.run_button.setAccessibleName("Run Code Button")
        self.hint_button = QPushButton(self.translate("actions.Show Hint"))
        self.hint_button.clicked.connect(self.show_hint)
        self.hint_button.setAccessibleName("Show Hint Button")
        self.step_button = QPushButton(self.translate("actions.Run Step by Step"))
        self.step_button.clicked.connect(self.run_step_by_step)
        self.step_button.setAccessibleName("Run Step by Step Button")
        self.new_example_button = QPushButton(self.translate("actions.New Example"))
        self.new_example_button.clicked.connect(self.load_new_indentation_example)
        self.new_example_button.hide()  # Initially hidden
        self.new_example_button.setAccessibleName("Load New Example Button")
        self.debug_button = QPushButton(self.translate("actions.Debug Code"))
        self.debug_button.clicked.connect(self.run_debugger)
        self.debug_button.setAccessibleName("Debug Code Button")

        # Add read output button
        self.read_output_button = QPushButton(self.translate("actions.Read Output"))
        self.read_output_button.clicked.connect(self.read_output_console)
        self.read_output_button.setAccessibleName("Read Output Button")

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.step_button)
        button_layout.addWidget(self.hint_button)
        button_layout.addWidget(self.new_example_button)
        button_layout.addWidget(self.debug_button)
        button_layout.addWidget(self.read_output_button)

        # Code editor and console layout
        code_layout = QVBoxLayout()
        self.code_label = QLabel(self.translate("labels.Code Editor:"))
        code_layout.addWidget(self.code_label)
        code_layout.addLayout(font_button_layout)
        code_layout.addWidget(self.code_editor)
        code_layout.addLayout(button_layout)
        self.output_label = QLabel(self.translate("labels.Output Console:"))
        code_layout.addWidget(self.output_label)
        code_layout.addWidget(self.output_console)

        # Splitter for lesson content and code editor
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.tabs)

        lesson_content_panel = QWidget()
        lesson_content_layout = QVBoxLayout()
        lesson_content_panel.setLayout(lesson_content_layout)
        lesson_content_layout.addWidget(QLabel(self.translate("labels.Lesson Content")))
        lesson_content_layout.addWidget(self.lesson_content)
        lesson_content_layout.addWidget(lesson_content_widget)  # Adding the widget with buttons

        code_panel = QWidget()
        code_panel.setLayout(code_layout)

        splitter.addWidget(lesson_content_panel)
        splitter.addWidget(code_panel)
        splitter.setSizes([200, 400, 600])

        main_layout.addWidget(splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Add progress label
        self.progress_label = QLabel()
        self.status_bar.addPermanentWidget(self.progress_label)

        # Main menu
        self.create_menu()

        # Toolbar
        self.create_toolbar()

        # Apply styles and load settings
        self.load_settings()

    # ---------------------------------------------
    #         Creating the Main Menu
    # ---------------------------------------------
    def create_menu(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu(self.translate("menu.File"))

        save_action = QAction(self.translate("actions.Save Code"), self)
        save_action.triggered.connect(self.save_user_code)
        save_action.setShortcut("Ctrl+S")
        file_menu.addAction(save_action)

        load_action = QAction(self.translate("actions.Open Code"), self)
        load_action.triggered.connect(self.load_user_code)
        load_action.setShortcut("Ctrl+O")
        file_menu.addAction(load_action)

        load_examples_action = QAction(self.translate("actions.Load Examples"), self)
        load_examples_action.triggered.connect(self.select_examples_file)  # Added method
        file_menu.addAction(load_examples_action)

        exit_action = QAction(self.translate("menu.Exit"), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help Menu
        help_menu = menubar.addMenu(self.translate("menu.Help"))

        assistant_action = QAction(self.translate("actions.Show Assistant"), self)
        assistant_action.triggered.connect(self.show_assistant)
        help_menu.addAction(assistant_action)

        about_action = QAction(self.translate("menu.About"), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # User Lessons Menu
        user_lessons_menu = menubar.addMenu(self.translate("menu.User Lessons"))

        export_lessons_action = QAction(self.translate("actions.Export Lessons"), self)
        export_lessons_action.triggered.connect(self.export_user_lessons)
        user_lessons_menu.addAction(export_lessons_action)

        import_lessons_action = QAction(self.translate("actions.Import Lessons"), self)
        import_lessons_action.triggered.connect(self.import_user_lessons)
        user_lessons_menu.addAction(import_lessons_action)

    # ---------------------------------------------
    #          Creating the Toolbar
    # ---------------------------------------------
    def create_toolbar(self):
        self.tool_bar = QToolBar("Main Toolbar")
        self.tool_bar.setMovable(False)
        self.addToolBar(self.tool_bar)

        # Styling the toolbar
        self.tool_bar.setStyleSheet("""
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
                background-color: #e0e0e0;
            }
        """)

        # Settings action
        settings_icon_path = "images/settings_icon.png"  # Ensure the 'settings_icon.png' file is in the 'images/' directory
        if os.path.exists(settings_icon_path):
            settings_icon = QIcon(settings_icon_path)
        else:
            settings_icon = QIcon()  # Empty icon if not found
            logging.warning(f"Settings icon not found at path: {settings_icon_path}")
        settings_action = QAction(settings_icon, self.translate("menu.Settings"), self)
        settings_action.setStatusTip(self.translate("menu.Settings"))
        settings_action.triggered.connect(self.open_settings_dialog)
        self.tool_bar.addAction(settings_action)

        # Documentation search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(self.translate("search_placeholder"))
        self.search_bar.returnPressed.connect(self.search_documentation)
        self.tool_bar.addWidget(self.search_bar)

        # Lessons search bar
        self.search_lessons_bar = QLineEdit()
        self.search_lessons_bar.setPlaceholderText(self.translate("search_placeholder_lessons"))
        self.search_lessons_bar.returnPressed.connect(self.search_lessons)
        self.tool_bar.addWidget(self.search_lessons_bar)

    # ---------------------------------------------
    #           Opening the Settings Dialog
    # ---------------------------------------------
    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.apply_settings()
            logging.info("Settings have been updated by the user.")

    # ---------------------------------------------
    #     Loading and Applying Settings
    # ---------------------------------------------
    def load_settings(self):
        self.update_stylesheet()
        self.load_font_settings()
        self.apply_interface_scale()
        logging.info("Settings have been loaded.")

    def apply_settings(self):
        self.update_stylesheet()
        self.load_font_settings()
        self.apply_interface_scale()
        self.set_tts_voice()
        logging.info("Settings have been applied.")

    def update_stylesheet(self):
        # Start with theme stylesheet
        theme = self.settings.value("theme", "light")
        if theme == "dark":
            stylesheet = self.dark_theme_stylesheet()
        else:
            stylesheet = self.light_theme_stylesheet()

        # Apply custom colors if set
        bg_color = self.settings.value("bg_color", None)
        text_color = self.settings.value("text_color", None)
        if bg_color and text_color:
            # Modify the base stylesheet with custom colors
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
            QLabel {{
                color: {text_color};
            }}
            QStatusBar {{
                background-color: {bg_color};
                color: {text_color};
            }}
            """
            stylesheet += custom_stylesheet

        # Apply color profile
        color_profile = self.settings.value("color_profile", "Default")
        if color_profile == "Protanopia":
            # Apply colors for protanopia
            color_profile_stylesheet = """
            /* Protanopia color adjustments */
            QListWidget::item:selected, QTreeWidget::item:selected {
                background-color: #FFD700;
                color: #000000;
            }
            """
            stylesheet += color_profile_stylesheet
        elif color_profile == "Deuteranopia":
            # Apply colors for deuteranopia
            color_profile_stylesheet = """
            /* Deuteranopia color adjustments */
            QListWidget::item:selected, QTreeWidget::item:selected {
                background-color: #FF69B4;
                color: #000000;
            }
            """
            stylesheet += color_profile_stylesheet
        elif color_profile == "Tritanopia":
            # Apply colors for tritanopia
            color_profile_stylesheet = """
            /* Tritanopia color adjustments */
            QListWidget::item:selected, QTreeWidget::item:selected {
                background-color: #87CEFA;
                color: #000000;
            }
            """
            stylesheet += color_profile_stylesheet
        # Else, no change

        # Apply tremor mode
        tremor_mode = self.settings.value("tremor_mode", False, type=bool)
        if tremor_mode:
            tremor_stylesheet = """
            QPushButton {
                padding: 20px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            """
            stylesheet += tremor_stylesheet

        # Apply dyslexia mode
        dyslexia_mode = self.settings.value("dyslexia_mode", False, type=bool)
        if dyslexia_mode:
            dyslexia_stylesheet = """
            QLabel, QLineEdit, QTextEdit, QPlainTextEdit, QListWidget, QTreeWidget {
                font-family: "Comic Sans MS";
            }
            """
            stylesheet += dyslexia_stylesheet

        # Apply autism mode
        autism_mode = self.settings.value("autism_mode", False, type=bool)
        if autism_mode:
            autism_stylesheet = """
            QLabel {
                font-weight: bold;
            }
            QToolButton {
                border: 2px solid #000000;
            }
            """
            stylesheet += autism_stylesheet

        # Apply custom button styles if not overridden by tremor mode
        if not tremor_mode:
            button_style = """
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
            """
            stylesheet += button_style

        # Set the final stylesheet
        self.setStyleSheet(stylesheet)

    def light_theme_stylesheet(self):
        return """
        QMainWindow {
            background-color: #ffffff;
            color: #000000;
        }
        QTextEdit, QPlainTextEdit, QListWidget, QTreeWidget {
            background-color: #f5f5f5;
            color: #000000;
        }
        QPushButton {
            background-color: #4CAF50;
            color: white;
            padding: 8px;
            border: none;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QLabel {
            color: #000000;
        }
        QStatusBar {
            background-color: #e0e0e0;
            color: #000000;
        }
        """

    def dark_theme_stylesheet(self):
        return """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QTextEdit, QPlainTextEdit, QListWidget, QTreeWidget {
            background-color: #3c3f41;
            color: #ffffff;
        }
        QPushButton {
            background-color: #555555;
            color: white;
            padding: 8px;
            border: none;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #777777;
        }
        QLabel {
            color: #ffffff;
        }
        QStatusBar {
            background-color: #444444;
            color: #ffffff;
        }
        """

    def set_tts_voice(self):
        selected_voice_id = self.settings.value("tts_voice", "")
        if selected_voice_id:
            self.engine.setProperty('voice', selected_voice_id)
            logging.info(f"TTS voice set to: {selected_voice_id}")
        else:
            # If no voice selected, use the default voice
            logging.warning("No TTS voice selected. Using default voice.")

    def apply_tts_enabled(self):
        self.tts_enabled = self.settings.value("tts_enabled", True, type=bool)

    def apply_interface_scale(self):
        interface_scale = self.settings.value("interface_scale", 100, type=int)
        factor = interface_scale / 100
        default_font_size = self.settings.value("font_size", 12, type=int)
        new_font_size = int(default_font_size * factor)
        font_family = self.settings.value("font_family", "Arial")
        font = QFont(font_family, new_font_size)
        QApplication.instance().setFont(font)
        self.apply_font_settings()
        logging.info(f"Interface scaling applied: {interface_scale}%, new font size: {new_font_size}")

    def apply_font_settings(self):
        # Ensure all relevant widgets use the application's font
        self.code_editor.setFont(QApplication.instance().font())
        self.output_console.setFont(QApplication.instance().font())
        self.lesson_content.setFont(QApplication.instance().font())
        self.setFont(QApplication.instance().font())  # Set the main window's font
        # Update other widgets if necessary

    def load_font_settings(self):
        # Load font family and size from settings
        font_family = self.settings.value("font_family", "Arial")
        font_size = self.settings.value("font_size", 12, type=int)
        font = QFont(font_family, font_size)
        self.code_editor.setFont(font)
        self.output_console.setFont(font)
        self.lesson_content.setFont(font)
        self.setFont(font)  # Apply to main window
        logging.info(f"Font settings loaded: {font_family}, {font_size}")

    # ---------------------------------------------
    #             Show Assistant
    # ---------------------------------------------
    def show_assistant(self):
        self.current_assistant_step = 0
        self.next_assistant_step()
        logging.info("Assistant has been started.")

    def next_assistant_step(self):
        if self.current_assistant_step < len(self.assistant_steps):
            message = self.assistant_steps[self.current_assistant_step]
            self.read_text_aloud(message)
            self.current_assistant_step += 1
            reply = QMessageBox.question(
                self,
                self.translate("labels.Assistant"),
                message + "\n\n" + self.translate("prompts.Continue Assistant"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.next_assistant_step()
            else:
                self.current_assistant_step = 0  # Reset assistant
                logging.info("Assistant was interrupted by the user.")
        else:
            self.current_assistant_step = 0  # Reset assistant
            logging.info("Assistant has completed the presentation.")

    # ---------------------------------------------
    #           Searching Documentation
    # ---------------------------------------------
    def search_documentation(self):
        query = self.search_bar.text().strip()
        if query:
            url = f"https://docs.python.org/3/search.html?q={query}"
            webbrowser.open(url)
            logging.info(f"Documentation opened for query: {query}")
        else:
            QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.Enter Search Query"))

    # ---------------------------------------------
    #          Searching Lessons
    # ---------------------------------------------
    def search_lessons(self):
        query = self.search_lessons_bar.text().strip().lower()
        if not query:
            QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.Enter Search Query"))
            return
        filtered_lessons = [
            lesson for lesson in self.lessons
            if query in lesson['title'].get(self.settings.value("language", "en"), '').lower() or
               query in lesson['content'].get(self.settings.value("language", "en"), '').lower()
        ]
        if not filtered_lessons:
            QMessageBox.information(self, self.translate("labels.Search Results"), self.translate("messages.No Lessons Found"))
            return
        # Display filtered lessons in the lesson tree
        self.lesson_tree.clear()
        categories = {}
        language = self.settings.value("language", "en")
        for lesson in filtered_lessons:
            category_name = lesson.get('category', {}).get(language, 'Other')
            if category_name not in categories:
                categories[category_name] = QTreeWidgetItem(self.lesson_tree)
                categories[category_name].setText(0, category_name)
            lesson_item = QTreeWidgetItem(categories[category_name])
            lesson_title = lesson['title'].get(language, lesson['title'].get('en', 'Untitled'))
            if lesson_title in self.completed_lessons:
                lesson_item.setText(0, f"{lesson_title} ✔")
            else:
                lesson_item.setText(0, lesson_title)
            lesson_item.setData(0, Qt.ItemDataRole.UserRole, lesson)
        self.lesson_tree.expandAll()
        logging.info(f"Lessons searched with query: {query}")

    # ---------------------------------------------
    #             Run Code Function
    # ---------------------------------------------
    def run_code(self):
        if hasattr(self, 'process') and self.process and self.process.state() == QProcess.ProcessState.Running:
            QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.Process Already Running"))
            return

        code = self.code_editor.toPlainText()
        error_message = self.analyze_code(code)
        if error_message:
            QMessageBox.critical(self, self.translate("Error"), error_message)
            self.read_text_aloud(f"{self.translate('Error')}: {error_message}")
            logging.error(f"Syntax error: {error_message}")
            return

        selected_item = self.lesson_tree.currentItem()
        if selected_item:
            lesson = selected_item.data(0, Qt.ItemDataRole.UserRole)
            language = self.settings.value("language", "en")
            lesson_title = lesson['title'].get(language, next(iter(lesson['title'].values()), ''))
            if lesson and lesson_title == self.translate("hints.Indentation and Code Structure"):
                QMessageBox.information(self, self.translate("messages.Congratulations"), self.translate("messages.Corrected Indentations"))
                self.read_text_aloud(self.translate("messages.Corrected Indentations"))
                logging.info("User successfully corrected indentations.")
                # Add lesson to completed
                if lesson_title not in self.completed_lessons:
                    self.completed_lessons.append(lesson_title)
                    self.save_progress()
                    self.update_lesson_list()
                return
            elif lesson and lesson_title == self.translate("hints.Fix Errors in Code"):
                try:
                    exec(code, {})
                    QMessageBox.information(self, self.translate("messages.Congratulations"), self.translate("messages.Fixed Code"))
                    self.read_text_aloud(self.translate("messages.Fixed Code"))
                    logging.info("User successfully fixed the code.")
                    # Add lesson to completed
                    if lesson_title not in self.completed_lessons:
                        self.completed_lessons.append(lesson_title)
                        self.save_progress()
                        self.update_lesson_list()
                    return
                except Exception as e:
                    QMessageBox.critical(self, self.translate("Error"), f"{self.translate('messages.Still Errors')}\n{e}")
                    logging.error(f"The program still contains errors: {e}")
                    return

        temp_file = "temp_code.py"
        try:
            with open(temp_file, "w", encoding='utf-8') as f:
                f.write(code)
        except Exception as e:
            QMessageBox.critical(self, self.translate("Error"), f"Cannot write to temporary file:\n{e}")
            logging.error(f"Cannot write to temporary file: {e}")
            return

        self.output_console.clear()

        self.process = QProcess()
        self.process.setProgram(sys.executable)
        self.process.setArguments([temp_file])
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.data_ready)
        self.process.finished.connect(lambda: self.cleanup_temp_file(temp_file))
        self.process.finished.connect(self.execution_finished)
        self.process.start()

        # Disable buttons while code is running
        self.run_button.setEnabled(False)
        self.step_button.setEnabled(False)
        self.debug_button.setEnabled(False)

        logging.info("Code has been executed.")

    def cleanup_temp_file(self, temp_file):
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logging.info(f"Temporary file {temp_file} removed.")
        except Exception as e:
            logging.error(f"Error removing temporary file {temp_file}: {e}")

    def execution_finished(self):
        # Re-enable buttons
        self.run_button.setEnabled(True)
        self.step_button.setEnabled(True)
        self.debug_button.setEnabled(True)

        output = self.output_console.toPlainText()
        if output:
            self.read_text_aloud(f"{self.translate('messages.Code Executed Successfully')}: {output}")
        else:
            self.read_text_aloud(self.translate("messages.Code Executed Successfully"))
        logging.info(self.translate("messages.Code Executed Successfully"))
        self.process = None  # Reset the process

        # Update progress
        selected_item = self.lesson_tree.currentItem()
        if selected_item:
            lesson = selected_item.data(0, Qt.ItemDataRole.UserRole)
            language = self.settings.value("language", "en")
            lesson_title = lesson['title'].get(language, next(iter(lesson['title'].values()), ''))
            if lesson and lesson_title not in self.completed_lessons:
                self.completed_lessons.append(lesson_title)
                self.save_progress()
                self.update_lesson_list()
                self.read_text_aloud(self.translate("messages.Lesson Completed").format(lesson_title=lesson_title))
                logging.info(self.translate("messages.Lesson Completed").format(lesson_title=lesson_title))

    def analyze_code(self, code):
        try:
            ast.parse(code)
            return None
        except SyntaxError as e:
            return f"{self.translate('Error')} {e.lineno}: {e.msg}"

    # ---------------------------------------------
    #       Real-Time Code Analysis
    # ---------------------------------------------
    def real_time_analysis(self):
        code = self.code_editor.toPlainText()
        error_message = self.analyze_code(code)
        if error_message:
            self.status_bar.showMessage(error_message)
        else:
            self.status_bar.clearMessage()

    # ---------------------------------------------
    #          Receiving Data from Process
    # ---------------------------------------------
    def data_ready(self):
        output = self.process.readAllStandardOutput().data().decode()
        self.output_console.append(output)
        # If there were errors, they will also be redirected to standard output
        if "Traceback" in output or "Error" in output or "Exception" in output:
            self.read_text_aloud(f"{self.translate('Error')}: {output}")

    # ---------------------------------------------
    #              Show Hint
    # ---------------------------------------------
    def show_hint(self):
        selected_item = self.lesson_tree.currentItem()
        if selected_item:
            lesson = selected_item.data(0, Qt.ItemDataRole.UserRole)
            if lesson:
                language = self.settings.value("language", "en")
                lesson_name = lesson['title'].get(language, next(iter(lesson['title'].values()), ''))
            else:
                lesson_name = self.translate("hints.Introduction")
        else:
            lesson_name = self.translate("hints.Introduction")

        hint = self.translations.get("hints", {}).get(lesson_name, self.translate("labels.No Hint Available"))

        QMessageBox.information(self, self.translate("labels.Hint"), hint)
        self.read_text_aloud(f"{self.translate('labels.Hint')}: {hint}")
        logging.info(f"{self.translate('labels.Hint')} for lesson: {lesson_name}")

    # ---------------------------------------------
    #       Running Code Step by Step
    # ---------------------------------------------
    def run_step_by_step(self):
        code = self.code_editor.toPlainText()
        self.lines = code.split('\n')
        self.current_line = 0
        self.output_console.clear()
        self.run_next_line()
        logging.info("Running code step by step.")

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
                self.output_console.append(f"Line {self.current_line+1}: {line}")
            except Exception as e:
                self.output_console.append(f"{self.translate('Error')} {self.current_line+1}: {e}")
                self.read_text_aloud(f"{self.translate('Error')} {self.current_line+1}: {e}")
                logging.error(f"Error on line {self.current_line+1}: {e}")
                return
            self.current_line += 1
            # Highlight the current line
            cursor = self.code_editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            for _ in range(self.current_line):
                cursor.movePosition(QTextCursor.MoveOperation.Down)
            self.code_editor.setTextCursor(cursor)
            # Run the next line after a short delay
            QTimer.singleShot(500, self.run_next_line)
        else:
            self.output_console.append(self.translate("messages.Code Executed Successfully"))
            self.read_text_aloud(self.translate("messages.Code Executed Successfully"))
            logging.info("Code has been executed step by step.")

    # ---------------------------------------------
    #               Debugging Code
    # ---------------------------------------------
    def run_debugger(self):
        if hasattr(self, 'process') and self.process and self.process.state() == QProcess.ProcessState.Running:
            QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.Process Already Running"))
            return

        code = self.code_editor.toPlainText()
        temp_file = "temp_debug.py"
        try:
            with open(temp_file, "w", encoding='utf-8') as f:
                f.write(code)
        except Exception as e:
            QMessageBox.critical(self, self.translate("Error"), f"Cannot write to temporary file:\n{e}")
            logging.error(f"Cannot write to temporary file: {e}")
            return

        self.output_console.clear()

        self.process = QProcess()
        self.process.setProgram(sys.executable)
        self.process.setArguments(['-m', 'pdb', temp_file])
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.data_ready)
        self.process.finished.connect(lambda: self.cleanup_temp_file(temp_file))
        self.process.finished.connect(self.execution_finished)
        self.process.start()

        # Disable buttons while debugger is running
        self.run_button.setEnabled(False)
        self.step_button.setEnabled(False)
        self.debug_button.setEnabled(False)

        logging.info("Debugger has been started.")

    # ---------------------------------------------
    #          Saving User Code
    # ---------------------------------------------
    def save_user_code(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, self.translate("actions.Save Code"), "", "Python Files (*.py)"
        )
        if file_name:
            try:
                code = self.code_editor.toPlainText()
                with open(file_name, "w", encoding='utf-8') as f:
                    f.write(code)
                logging.info(f"Code has been saved to file: {file_name}")
            except Exception as e:
                QMessageBox.critical(self, self.translate("Error"), f"Cannot save code to file:\n{e}")
                logging.error(f"Cannot save code to file: {e}")

    # ---------------------------------------------
    #          Loading User Code
    # ---------------------------------------------
    def load_user_code(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, self.translate("actions.Open Code"), "", "Python Files (*.py)"
        )
        if file_name:
            try:
                with open(file_name, "r", encoding='utf-8') as f:
                    code = f.read()
                self.code_editor.setPlainText(code)
                logging.info(f"Code has been loaded from file: {file_name}")
            except Exception as e:
                QMessageBox.critical(self, self.translate("Error"), f"Cannot load code from file:\n{e}")
                logging.error(f"Cannot load code from file: {e}")

    # ---------------------------------------------
    #                About Program
    # ---------------------------------------------
    def show_about(self):
        QMessageBox.information(self, self.translate("menu.About"), f"{self.translate('app_title')}\nVersion 1.0")

    # ---------------------------------------------
    #          Loading and Saving User Lessons
    # ---------------------------------------------
    def save_user_lessons_to_file(self, filename):
        # Filter out user lessons
        user_lessons = [lesson for lesson in self.lessons if lesson.get('type') == 'user']
        # Save user lessons to file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(user_lessons, f, ensure_ascii=False, indent=4)
            logging.info(f"User lessons have been saved to file: {filename}")
        except Exception as e:
            QMessageBox.critical(self, self.translate("Error"), f"Cannot save user lessons to file:\n{e}")
            logging.error(f"Cannot save user lessons to file: {e}")

    def load_user_lessons_from_file(self, filename):
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    user_lessons = json.load(f)
                self.lessons.extend(user_lessons)
                logging.info(f"User lessons have been loaded from file: {filename}")
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Error", f"JSON Decode Error in {filename}: {e}")
                logging.error(f"JSON Decode Error in {filename}: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Cannot load user lessons from file:\n{e}")
                logging.error(f"Cannot load user lessons from file: {e}")
        else:
            logging.warning(f"User lessons file not found: {filename}")
        self.update_lesson_list()  # Update the lesson list after loading

    # ---------------------------------------------
    #          Loading and Updating Lessons
    # ---------------------------------------------
    def load_lessons(self):
        self.lessons = []
        lessons_path = os.path.join('lessons', '**', '*.json')
        lesson_files = glob.glob(lessons_path, recursive=True)
        for file in lesson_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    lesson = json.load(f)
                    self.lessons.append(lesson)
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, self.translate("Error"), f"JSON Decode Error in {file}: {e}")
                logging.error(f"JSON Decode Error in {file}: {e}")
            except FileNotFoundError:
                QMessageBox.critical(self, self.translate("Error"), f"Lesson file not found: {file}")
                logging.error(f"Lesson file not found: {file}")
            except Exception as e:
                QMessageBox.critical(self, self.translate("Error"), f"Error loading {file}: {e}")
                logging.error(f"Error loading {file}: {e}")
        self.update_lesson_list()
        logging.info("Lessons have been loaded from JSON files.")

    def update_lesson_list(self):
        self.lesson_tree.clear()
        categories = {}
        language = self.settings.value("language", "en")
        for lesson in self.lessons:
            category_name = lesson.get('category', {}).get(language, 'Other')
            if category_name not in categories:
                categories[category_name] = QTreeWidgetItem(self.lesson_tree)
                categories[category_name].setText(0, category_name)
            lesson_item = QTreeWidgetItem(categories[category_name])
            lesson_title = lesson['title'].get(language, lesson['title'].get('en', 'Untitled'))
            if lesson_title in self.completed_lessons:
                lesson_item.setText(0, f"{lesson_title} ✔")
            else:
                lesson_item.setText(0, lesson_title)
            lesson_item.setData(0, Qt.ItemDataRole.UserRole, lesson)
        self.lesson_tree.expandAll()
        # Update progress
        total_lessons = len(self.lessons)
        completed = len(self.completed_lessons)
        progress_percent = (completed / total_lessons) * 100 if total_lessons > 0 else 0
        self.progress_label.setText(f"{self.translate('labels.Progress:')} {completed}/{total_lessons} ({progress_percent:.1f}%)")
        logging.info("Lesson list has been updated.")

        # Update history list
        self.history_list.clear()
        for lesson_title in self.completed_lessons:
            item = QListWidgetItem(lesson_title)
            self.history_list.addItem(item)

    # ---------------------------------------------
    #             Load Lesson
    # ---------------------------------------------
    def load_lesson(self, item):
        if item is None:
            return
        lesson = item.data(0, Qt.ItemDataRole.UserRole)
        if lesson:
            language = self.settings.value("language", "en")
            content = lesson['content'].get(language, lesson['content'].get('en', ''))
            simple_language = self.settings.value("simple_language", False, type=bool)
            if simple_language:
                content = self.simplify_language(content)
            self.lesson_content.setHtml(content)
            self.code_editor.clear()
            lesson_title = lesson['title'].get(language, lesson['title'].get('en', ''))
            if lesson_title == self.translate("hints.Indentation and Code Structure"):
                self.load_new_indentation_example()
                self.new_example_button.show()
            elif lesson_title == self.translate("hints.Fix Errors in Code"):
                self.load_buggy_code_example()
                self.new_example_button.hide()
            else:
                self.new_example_button.hide()
            logging.info(f"Lesson '{lesson_title}' has been loaded.")
        else:
            self.lesson_content.clear()
            self.code_editor.clear()
            self.new_example_button.hide()

    # ---------------------------------------------
    #          Load Lesson from History
    # ---------------------------------------------
    def load_lesson_from_history(self, item):
        lesson_title = item.text().replace(" ✔", "")
        for i in range(self.lesson_tree.topLevelItemCount()):
            category_item = self.lesson_tree.topLevelItem(i)
            for j in range(category_item.childCount()):
                lesson_item = category_item.child(j)
                if lesson_item.text(0).replace(" ✔", "") == lesson_title:
                    self.lesson_tree.setCurrentItem(lesson_item)
                    self.load_lesson(lesson_item)
                    return

    # ---------------------------------------------
    #          Simplify Language Content
    # ---------------------------------------------
    def simplify_language(self, content):
        # Simple replacement of difficult words with simpler ones
        replacements = {
            "implementacja": "wprowadzenie",
            "funkcja": "działanie",
            "definiowanie": "tworzenie",
            "parametr": "wartość",
            "argument": "wartość",
            "instrukcja": "polecenie",
            "operacja": "działanie",
            # Add more replacements as needed
        }
        for word, simple_word in replacements.items():
            content = content.replace(word, simple_word)
        return content

    # ---------------------------------------------
    #          Run Code Function
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Analyze User Code
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Real-Time Code Analysis
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Receive Data from Process
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #              Show Hint
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Run Step by Step Function
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #               Debugging Code
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Play Lesson Content Aloud
    # ---------------------------------------------
    def play_lesson_content(self):
        text = self.lesson_content.toPlainText()
        if not text.strip():
            # Extract text from HTML content
            html_content = self.lesson_content.toHtml()
            text = re.sub('<[^<]+?>', '', html_content)
        if text.strip():
            if self.tts_enabled:
                self.read_text_aloud(text)
                logging.info("Lesson content has been read aloud.")
            else:
                logging.info("TTS is disabled. Lesson content was not read aloud.")
        else:
            QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.No Content to Read"))
            logging.warning("Attempted to read empty content.")

    def read_output_console(self):
        text = self.output_console.toPlainText()
        if text.strip():
            if self.tts_enabled:
                self.read_text_aloud(text)
                logging.info("Console output has been read aloud.")
            else:
                logging.info("TTS is disabled. Console output was not read aloud.")
        else:
            QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.No Output to Read"))
            logging.warning("Attempted to read empty console output.")

    def read_text_aloud(self, text):
        if self.tts_enabled:
            self.tts_queue.append(text)
            if not self.tts_busy:
                self.process_tts_queue()

    def process_tts_queue(self):
        if self.tts_queue:
            self.tts_busy = True
            text_to_speak = self.tts_queue.pop(0)
            self.tts_worker = TTSWorker(text_to_speak, self.engine.getProperty('voice'), self.engine.getProperty('rate'))
            self.tts_worker.finished.connect(self.on_tts_finished)
            self.tts_worker.error.connect(self.on_tts_error)
            self.tts_worker.start()

    def on_tts_finished(self):
        self.tts_busy = False
        self.process_tts_queue()

    def on_tts_error(self, error_message):
        QMessageBox.critical(self, self.translate("Error"), f"TTS Error: {error_message}")
        logging.error(f"TTS Error: {error_message}")
        self.tts_busy = False
        self.process_tts_queue()

    # ---------------------------------------------
    #          Simplify Language Mode
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Select Examples File Method
    # ---------------------------------------------
    def select_examples_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, self.translate("actions.Load Examples"), "", "Text Files (*.txt);;All Files (*)"
        )
        if filename:
            self.load_examples_from_file(filename)
            QMessageBox.information(self, self.translate("messages.Success"), self.translate("messages.Examples Loaded"))
            logging.info(f"Examples loaded from file: {filename}")

    # ---------------------------------------------
    #          Load and Update Lessons
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Add New Lesson
    # ---------------------------------------------
    def add_new_lesson(self):
        language = self.settings.value("language", "en")
        title, ok = QInputDialog.getText(self, self.translate("labels.New Lesson"), self.translate("prompts.Enter Lesson Title"))
        if ok and title:
            if not self.validate_lesson_title(title):
                QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.Invalid Lesson Title"))
                return
            category, ok = QInputDialog.getText(self, self.translate("labels.New Lesson"), self.translate("prompts.Enter Lesson Category"))
            if not ok or not category:
                category = "Other"
            content, ok = QInputDialog.getMultiLineText(self, self.translate("labels.New Lesson"), self.translate("prompts.Enter Lesson Content"))
            if ok:
                if not self.validate_lesson_content(content):
                    QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.Invalid Lesson Content"))
                    return
                # Ensure 'en' key is always present
                new_lesson = {
                    "title": {language: title, 'en': title} if language != 'en' else {language: title},
                    "content": {language: content, 'en': content} if language != 'en' else {language: content},
                    "type": "user",
                    "category": {language: category, 'en': category} if language != 'en' else {language: category}
                }
                self.lessons.append(new_lesson)
                self.update_lesson_list()
                self.save_user_lessons_to_file(self.user_lessons_file)
                # Save the lesson to a separate JSON file
                self.save_lesson_to_file(new_lesson)
                logging.info(f"New lesson added: {title}")

    def save_lesson_to_file(self, lesson):
        # Create user_lessons directory if it doesn't exist
        user_lessons_dir = os.path.join('lessons', 'user_lessons')
        os.makedirs(user_lessons_dir, exist_ok=True)
        # Generate a unique filename
        existing_files = glob.glob(os.path.join(user_lessons_dir, 'user_lesson_*.json'))
        lesson_number = len(existing_files) + 1
        filename = os.path.join(user_lessons_dir, f'user_lesson_{lesson_number}.json')
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(lesson, f, ensure_ascii=False, indent=4)
            logging.info(f"User lesson saved to file: {filename}")
        except Exception as e:
            QMessageBox.critical(self, self.translate("Error"), f"Cannot save lesson to file:\n{e}")
            logging.error(f"Cannot save lesson to file: {e}")

    def validate_lesson_title(self, title):
        # Implement validation logic, e.g., no special characters
        return re.match("^[A-Za-z0-9 _-]+$", title) is not None

    def validate_lesson_content(self, content):
        # Implement validation logic, e.g., minimum length
        return len(content.strip()) > 10

    # ---------------------------------------------
    #          Editing Existing Lesson
    # ---------------------------------------------
    def edit_lesson(self):
        selected_item = self.lesson_tree.currentItem()
        if selected_item:
            lesson = selected_item.data(0, Qt.ItemDataRole.UserRole)
            if lesson and lesson['type'] == 'user':
                language = self.settings.value("language", "en")
                # Find lesson index in self.lessons
                try:
                    lesson_index = self.lessons.index(lesson)
                except ValueError:
                    QMessageBox.critical(self, self.translate("Error"), self.translate("messages.Lesson Not Found"))
                    logging.error("Selected lesson not found in the lessons list.")
                    return
                current_title = lesson['title'].get(language, next(iter(lesson['title'].values()), ''))
                new_title, ok = QInputDialog.getText(self, self.translate("labels.Edit Lesson"), self.translate("prompts.Edit Lesson Title"), text=current_title)
                if ok and new_title:
                    if not self.validate_lesson_title(new_title):
                        QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.Invalid Lesson Title"))
                        return
                    current_category = lesson['category'].get(language, next(iter(lesson['category'].values()), ''))
                    new_category, ok = QInputDialog.getText(self, self.translate("labels.Edit Lesson"), self.translate("prompts.Edit Lesson Category"), text=current_category)
                    if not ok or not new_category:
                        new_category = "Other"
                    current_content = lesson['content'].get(language, next(iter(lesson['content'].values()), ''))
                    new_content, ok = QInputDialog.getMultiLineText(self, self.translate("labels.Edit Lesson"), self.translate("prompts.Edit Lesson Content"), text=current_content)
                    if ok:
                        if not self.validate_lesson_content(new_content):
                            QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.Invalid Lesson Content"))
                            return
                        # Update lesson in self.lessons
                        lesson['title'][language] = new_title
                        if language != 'en':
                            lesson['title']['en'] = new_title  # Update 'en' key as well
                        lesson['content'][language] = new_content
                        if language != 'en':
                            lesson['content']['en'] = new_content
                        lesson['category'][language] = new_category
                        if language != 'en':
                            lesson['category']['en'] = new_category
                        self.update_lesson_list()
                        self.save_user_lessons_to_file(self.user_lessons_file)
                        # Update the lesson file
                        self.update_lesson_file(lesson)
                        logging.info(f"Lesson edited: {new_title}")
            else:
                QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.Cannot Edit Default Lesson"))
                logging.warning("Attempted to edit a default lesson.")
        else:
            QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.No Lesson Selected"))
            logging.warning("No lesson selected for editing.")

    def update_lesson_file(self, lesson):
        # Find the corresponding lesson file
        user_lessons_dir = os.path.join('lessons', 'user_lessons')
        lesson_files = glob.glob(os.path.join(user_lessons_dir, 'user_lesson_*.json'))
        for file in lesson_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    existing_lesson = json.load(f)
                if existing_lesson == lesson:
                    with open(file, 'w', encoding='utf-8') as f:
                        json.dump(lesson, f, ensure_ascii=False, indent=4)
                    logging.info(f"Lesson file updated: {file}")
                    return
            except Exception as e:
                logging.error(f"Error updating lesson file {file}: {e}")
        # If not found, save as a new file
        self.save_lesson_to_file(lesson)

    # ---------------------------------------------
    #          Deleting Existing Lesson
    # ---------------------------------------------
    def delete_lesson(self):
        selected_item = self.lesson_tree.currentItem()
        if selected_item:
            lesson = selected_item.data(0, Qt.ItemDataRole.UserRole)
            if lesson and lesson['type'] == 'user':
                language = self.settings.value("language", "en")
                lesson_title = lesson['title'].get(language, next(iter(lesson['title'].values()), ''))
                reply = QMessageBox.question(
                    self,
                    self.translate("labels.Delete Lesson"),
                    f"{self.translate('messages.Confirm Delete Lesson')} '{lesson_title}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.lessons.remove(lesson)
                    self.update_lesson_list()
                    self.save_user_lessons_to_file(self.user_lessons_file)
                    # Remove the lesson file
                    self.remove_lesson_file(lesson)
                    logging.info(f"Lesson deleted: {lesson_title}")
            else:
                QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.Cannot Delete Default Lesson"))
                logging.warning("Attempted to delete a default lesson.")
        else:
            QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.No Lesson Selected"))
            logging.warning("No lesson selected for deletion.")

    def remove_lesson_file(self, lesson):
        user_lessons_dir = os.path.join('lessons', 'user_lessons')
        lesson_files = glob.glob(os.path.join(user_lessons_dir, 'user_lesson_*.json'))
        for file in lesson_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    existing_lesson = json.load(f)
                if existing_lesson == lesson:
                    os.remove(file)
                    logging.info(f"Lesson file removed: {file}")
            except Exception as e:
                logging.error(f"Error removing lesson file {file}: {e}")

    # ---------------------------------------------
    #          Deleting Category
    # ---------------------------------------------
    def delete_category(self):
        selected_item = self.lesson_tree.currentItem()
        if selected_item:
            if selected_item.parent() is None:
                # This is a category
                category = selected_item.text(0)
                # Get lessons in this category
                lessons_in_category = [lesson for lesson in self.lessons if lesson.get('category', {}).get(self.settings.value("language", "en"), 'Other') == category]
                # Check if all lessons are user-created
                if all(lesson['type'] == 'user' for lesson in lessons_in_category):
                    reply = QMessageBox.question(
                        self,
                        self.translate("labels.Delete Category"),
                        f"{self.translate('messages.Confirm Delete Category')} '{category}'?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        # Remove lessons from this category
                        self.lessons = [lesson for lesson in self.lessons if lesson.get('category', {}).get(self.settings.value("language", "en"), 'Other') != category]
                        self.update_lesson_list()
                        self.save_user_lessons_to_file(self.user_lessons_file)
                        # Remove corresponding lesson files
                        self.remove_category_lesson_files(category)
                        logging.info(f"Category deleted: {category}")
                else:
                    QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.Cannot Delete Default Category"))
                    logging.warning("Attempted to delete a category containing default lessons.")
            else:
                QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.Select Category to Delete"))
        else:
            QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.No Category Selected"))

    def remove_category_lesson_files(self, category):
        user_lessons_dir = os.path.join('lessons', 'user_lessons')
        lesson_files = glob.glob(os.path.join(user_lessons_dir, 'user_lesson_*.json'))
        for file in lesson_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    lesson = json.load(f)
                if lesson.get('category', {}).get(self.settings.value("language", "en"), 'Other') == category:
                    os.remove(file)
                    logging.info(f"Lesson file removed: {file}")
            except Exception as e:
                logging.error(f"Error removing lesson file {file}: {e}")

    # ---------------------------------------------
    #          Load and Save Progress
    # ---------------------------------------------
    def load_progress(self):
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Error", f"JSON Decode Error in {self.progress_file}: {e}")
                logging.error(f"JSON Decode Error in {self.progress_file}: {e}")
                return []
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Cannot load progress from file:\n{e}")
                logging.error(f"Cannot load progress from file: {e}")
                return []
        else:
            return []

    def save_progress(self):
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.completed_lessons, f, ensure_ascii=False, indent=4)
            logging.info("Progress has been saved.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot save progress to file:\n{e}")
            logging.error(f"Cannot save progress to file: {e}")

    # ---------------------------------------------
    #          Load Examples from File
    # ---------------------------------------------
    def load_examples_from_file(self, filename):
        if not os.path.exists(filename):
            # If the file doesn't exist, create it with sample data
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("def example():\n    print('This is an example code')\n    print('Fix the indentations!')\n###")
        # Now load examples from the file
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            self.indentation_examples = content.strip().split('###')
            self.indentation_examples = [example.strip() for example in self.indentation_examples if example.strip()]
            logging.info("Indentation examples have been loaded.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot load examples from file:\n{e}")
            logging.error(f"Cannot load examples from file: {e}")

    # ---------------------------------------------
    #          Load and Update Lessons
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Add New Lesson
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Editing Existing Lesson
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Deleting Existing Lesson
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Deleting Category
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Load Buggy Code Example
    # ---------------------------------------------
    def load_buggy_code_example(self):
        buggy_code = """
def add(a, b)
    return a + b

print(add(5, '3'))
"""
        self.code_editor.setPlainText(buggy_code)
        self.output_console.clear()
        self.status_bar.clearMessage()

    # ---------------------------------------------
    #        Loading New Indentation Examples
    # ---------------------------------------------
    def load_new_indentation_example(self):
        if not hasattr(self, 'indentation_examples') or not self.indentation_examples:
            QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.No Indentation Examples"))
            logging.warning("No indentation examples available.")
            return
        example = random.choice(self.indentation_examples)
        self.code_editor.setPlainText(example)
        self.output_console.clear()
        self.status_bar.clearMessage()
        logging.info("New indentation example loaded.")

    # ---------------------------------------------
    #        Saving and Importing Lessons
    # ---------------------------------------------
    def export_user_lessons(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, self.translate("actions.Export Lessons"), "", "JSON Files (*.json)"
        )
        if file_name:
            try:
                user_lessons = [lesson for lesson in self.lessons if lesson.get('type') == 'user']
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(user_lessons, f, ensure_ascii=False, indent=4)
                QMessageBox.information(self, self.translate("messages.Success"), self.translate("messages.Lessons Exported Successfully"))
                logging.info(f"User lessons exported to {file_name}")
            except Exception as e:
                QMessageBox.critical(self, self.translate("Error"), f"{self.translate('messages.Export Failed')}: {e}")
                logging.error(f"Export failed: {e}")

    def import_user_lessons(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, self.translate("actions.Import Lessons"), "", "JSON Files (*.json)"
        )
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    imported_lessons = json.load(f)
                # Validate and add lessons
                for lesson in imported_lessons:
                    if 'title' in lesson and 'content' in lesson and 'category' in lesson:
                        self.lessons.append(lesson)
                        self.save_lesson_to_file(lesson)
                    else:
                        logging.warning(f"Invalid lesson format in {file_name}: {lesson}")
                self.update_lesson_list()
                self.save_user_lessons_to_file(self.user_lessons_file)
                QMessageBox.information(self, self.translate("messages.Success"), self.translate("messages.Lessons Imported Successfully"))
                logging.info(f"User lessons imported from {file_name}")
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, self.translate("Error"), f"JSON Decode Error: {e}")
                logging.error(f"JSON Decode Error during import: {e}")
            except Exception as e:
                QMessageBox.critical(self, self.translate("Error"), f"{self.translate('messages.Import Failed')}: {e}")
                logging.error(f"Import failed: {e}")

    # ---------------------------------------------
    #          Saving and Loading Progress
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Load Lesson
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Load Lesson from History
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Simplify Language Content
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Run Step by Step Function
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #               Debugging Code
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Play Lesson Content Aloud
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Set Font Size Methods
    # ---------------------------------------------
    def set_small_font(self):
        current_font = self.code_editor.font()
        new_size = max(8, current_font.pointSize() - 1)
        self.code_editor.setFont(QFont(current_font.family(), new_size))
        logging.info(f"Font size decreased to: {new_size}")

    def set_normal_font(self):
        default_size = self.settings.value("font_size", 12, type=int)
        font_family = self.settings.value("font_family", "Arial")
        self.code_editor.setFont(QFont(font_family, default_size))
        logging.info(f"Font size reset to default: {default_size}")

    def set_large_font(self):
        current_font = self.code_editor.font()
        new_size = current_font.pointSize() + 1
        self.code_editor.setFont(QFont(current_font.family(), new_size))
        logging.info(f"Font size increased to: {new_size}")

    # ---------------------------------------------
    #          Export and Import User Lessons
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Load and Update Lessons
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Add New Lesson
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Editing Existing Lesson
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Deleting Existing Lesson
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Deleting Category
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Load Buggy Code Example
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #        Loading New Indentation Examples
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Export and Import Lessons
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Load and Update Lessons
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Manage Assistant Steps
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Load Examples from File
    # ---------------------------------------------
    # Already implemented above

    # ---------------------------------------------
    #          Read Text Aloud Method
    # ---------------------------------------------
    def read_text_aloud(self, text):
        if self.tts_enabled:
            self.tts_queue.append(text)
            if not self.tts_busy:
                self.process_tts_queue()

    def process_tts_queue(self):
        if self.tts_queue:
            self.tts_busy = True
            text_to_speak = self.tts_queue.pop(0)
            self.tts_worker = TTSWorker(text_to_speak, self.engine.getProperty('voice'), self.engine.getProperty('rate'))
            self.tts_worker.finished.connect(self.on_tts_finished)
            self.tts_worker.error.connect(self.on_tts_error)
            self.tts_worker.start()

    def on_tts_finished(self):
        self.tts_busy = False
        self.process_tts_queue()

    def on_tts_error(self, error_message):
        QMessageBox.critical(self, self.translate("Error"), f"TTS Error: {error_message}")
        logging.error(f"TTS Error: {error_message}")
        self.tts_busy = False
        self.process_tts_queue()

# ---------------------------------------------
#          Syntax Highlighting Class
# ---------------------------------------------
# (Already implemented above)

# ---------------------------------------------
#          Line Number Area Class
# ---------------------------------------------
# (Already implemented above)

# ---------------------------------------------
#          Code Editor Class with Line Numbers
# ---------------------------------------------
# (Already implemented above)

# ---------------------------------------------
#          Main Execution
# ---------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PythonTutorApp()
    window.show()
    sys.exit(app.exec())
