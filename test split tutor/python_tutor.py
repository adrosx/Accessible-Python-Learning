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
#          Konfiguracja logowania
# ---------------------------------------------
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ---------------------------------------------
#          Klasa Worker TTS dla asynchronicznego przetwarzania
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
#          Klasa Dialogu Ustawień
# ---------------------------------------------
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.parent().translate("menu.Settings"))
        self.settings = QSettings("PythonTutorApp", "PythonTutor")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Tworzenie formularza ustawień
        form_layout = QFormLayout()

        # Czcionka aplikacji
        font_button = QPushButton(self.parent().translate("labels.Change Font"))
        font_button.setToolTip(self.parent().translate("labels.Choose Application Font"))
        font_button.clicked.connect(self.change_font)
        form_layout.addRow(QLabel(self.parent().translate("labels.Application Font:")), font_button)

        # Rozmiar czcionki
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 48)
        font_size = self.settings.value("font_size", 12, type=int)
        self.font_size_spinbox.setValue(font_size)
        self.font_size_spinbox.setToolTip(self.parent().translate("labels.Choose Font Size"))
        self.font_size_spinbox.valueChanged.connect(self.update_font_preview)
        form_layout.addRow(QLabel(self.parent().translate("labels.Font Size:")), self.font_size_spinbox)

        # Podgląd czcionki
        self.font_preview_label = QLabel(self.parent().translate("labels.Sample Text"))
        self.update_font_preview()
        form_layout.addRow(QLabel(self.parent().translate("labels.Font Preview:")), self.font_preview_label)

        # Motyw aplikacji
        self.theme_combo = QComboBox()
        self.theme_combo.addItem(self.parent().translate("labels.Light Theme"), "light")
        self.theme_combo.addItem(self.parent().translate("labels.Dark Theme"), "dark")
        theme = self.settings.value("theme", "light")
        index = self.theme_combo.findData(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        self.theme_combo.setToolTip(self.parent().translate("labels.Choose Application Theme"))
        form_layout.addRow(QLabel(self.parent().translate("labels.Application Theme:")), self.theme_combo)

        # Skalowanie interfejsu
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

        # Dostosowywanie kolorów
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

        # Profil kolorów
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

        # Wybór języka
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

        # Tryb prostego języka
        self.simple_language_checkbox = QCheckBox(self.parent().translate("labels.Enabled"))
        simple_language = self.settings.value("simple_language", False, type=bool)
        self.simple_language_checkbox.setChecked(simple_language)
        self.simple_language_checkbox.setToolTip(self.parent().translate("labels.Enable Simple Language Mode"))
        form_layout.addRow(QLabel(self.parent().translate("labels.Simple Language Mode:")), self.simple_language_checkbox)

        # Tryb debugowania
        self.debug_mode_checkbox = QCheckBox(self.parent().translate("labels.Enabled"))
        debug_mode = self.settings.value("debug_mode", False, type=bool)
        self.debug_mode_checkbox.setChecked(debug_mode)
        self.debug_mode_checkbox.setToolTip(self.parent().translate("labels.Enable Debug Mode"))
        form_layout.addRow(QLabel(self.parent().translate("labels.Debug Mode:")), self.debug_mode_checkbox)

        # Szybkość mowy
        self.speech_rate_spinbox = QSpinBox()
        self.speech_rate_spinbox.setRange(50, 300)
        speech_rate = self.settings.value("speech_rate", 150, type=int)
        self.speech_rate_spinbox.setValue(speech_rate)
        self.speech_rate_spinbox.setToolTip(self.parent().translate("labels.Set Speech Rate"))
        form_layout.addRow(QLabel(self.parent().translate("labels.Speech Rate:")), self.speech_rate_spinbox)

        # Włącz/wyłącz TTS
        self.tts_enabled_checkbox = QCheckBox(self.parent().translate("labels.Enabled"))
        tts_enabled = self.settings.value("tts_enabled", True, type=bool)
        self.tts_enabled_checkbox.setChecked(tts_enabled)
        self.tts_enabled_checkbox.setToolTip(self.parent().translate("labels.Enable Text-to-Speech"))
        form_layout.addRow(QLabel(self.parent().translate("labels.Text-to-Speech:")), self.tts_enabled_checkbox)

        # Tryb dysleksji
        self.dyslexia_mode_checkbox = QCheckBox(self.parent().translate("labels.Enabled"))
        dyslexia_mode = self.settings.value("dyslexia_mode", False, type=bool)
        self.dyslexia_mode_checkbox.setChecked(dyslexia_mode)
        self.dyslexia_mode_checkbox.setToolTip(self.parent().translate("labels.Enable Dyslexia Mode"))
        form_layout.addRow(QLabel(self.parent().translate("labels.Dyslexia Mode:")), self.dyslexia_mode_checkbox)

        # Tryb drżenia
        self.tremor_mode_checkbox = QCheckBox(self.parent().translate("labels.Enabled"))
        tremor_mode = self.settings.value("tremor_mode", False, type=bool)
        self.tremor_mode_checkbox.setChecked(tremor_mode)
        self.tremor_mode_checkbox.setToolTip(self.parent().translate("labels.Enable Tremor Mode"))
        form_layout.addRow(QLabel(self.parent().translate("labels.Tremor Mode:")), self.tremor_mode_checkbox)

        # Tryb autyzmu
        self.autism_mode_checkbox = QCheckBox(self.parent().translate("labels.Enabled"))
        autism_mode = self.settings.value("autism_mode", False, type=bool)
        self.autism_mode_checkbox.setChecked(autism_mode)
        self.autism_mode_checkbox.setToolTip(self.parent().translate("labels.Enable Autism Mode"))
        form_layout.addRow(QLabel(self.parent().translate("labels.Autism Mode:")), self.autism_mode_checkbox)

        # Dodanie formularza do layoutu
        layout.addLayout(form_layout)

        # Przycisk resetowania ustawień
        reset_button = QPushButton(self.parent().translate("labels.Reset to Defaults"))
        reset_button.setToolTip(self.parent().translate("labels.Restore Default Settings"))
        reset_button.clicked.connect(self.reset_to_defaults)
        layout.addWidget(reset_button)

        # Przycisk OK i Anuluj
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
            logging.info(f"Zmieniono czcionkę na: {font.family()}")

    def update_font_preview(self):
        font_family = self.settings.value("font_family", "Arial")
        font_size = self.font_size_spinbox.value()
        font = QFont(font_family, font_size)
        self.font_preview_label.setFont(font)

    def change_bg_color(self):
        bg_color = QColorDialog.getColor(title=self.parent().translate("titles.Select Background Color"))
        if bg_color.isValid():
            self.settings.setValue("bg_color", bg_color.name())
            logging.info(f"Zmieniono kolor tła na: {bg_color.name()}")

    def change_text_color(self):
        text_color = QColorDialog.getColor(title=self.parent().translate("titles.Select Text Color"))
        if text_color.isValid():
            self.settings.setValue("text_color", text_color.name())
            logging.info(f"Zmieniono kolor tekstu na: {text_color.name()}")

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
            logging.info("Ustawienia zostały przywrócone do domyślnych.")

    def accept(self):
        # Zapisz ustawienia przed zamknięciem
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

        # Wybór głosu TTS
        self.settings.setValue("tts_voice", self.parent().engine.getProperty('voice'))

        super().accept()
        self.parent().load_language()
        self.parent().update_stylesheet()
        self.parent().apply_font_settings()
        self.parent().set_tts_voice()

# ---------------------------------------------
#          Klasa Wyróżniania Składni Pythona
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
            regex = QRegularExpression(pattern)
            self.highlighting_rules.append((regex, keyword_format))

        # Operatory
        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor("#FF00FF"))
        operator_pattern = QRegularExpression(r"[+\-*/%=<>!]+")
        self.highlighting_rules.append((operator_pattern, operator_format))

        # Ciągi znaków
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#008000"))
        string_patterns = [
            QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'),
            QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'")
        ]
        for pattern in string_patterns:
            self.highlighting_rules.append((pattern, string_format))

        # Komentarze
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
#          Klasa Obszaru Numerów Linii
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
#          Klasa Edytora Kodu z Numerami Linii
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
#          Klasa Głównej Aplikacji
# ---------------------------------------------
class PythonTutorApp(QMainWindow):
    def __init__(self, user_lessons_file='user_lessons.json', progress_file='progress.json'):
        super().__init__()
        self.settings = QSettings("PythonTutorApp", "PythonTutor")
        self.user_lessons_file = user_lessons_file
        self.progress_file = progress_file

        # Wczytanie języka
        self.load_language()

        self.setWindowTitle(self.translate("app_title"))
        self.resize(1200, 800)
        self.lessons = []

        # Inicjalizacja silnika pyttsx3
        self.engine = pyttsx3.init()
        speech_rate = self.settings.value("speech_rate", 150, type=int)
        self.engine.setProperty('rate', speech_rate)  # Ustawienie szybkości mowy

        # Ustawienie głosu TTS na podstawie języka
        self.set_tts_voice()

        # Inicjalizacja kolejki TTS i stanu
        self.tts_queue = []
        self.tts_busy = False

        self.apply_tts_enabled()

        # Inicjalizacja postępu
        self.completed_lessons = self.load_progress()

        self.initUI()
        self.load_lessons()
        self.load_user_lessons_from_file(self.user_lessons_file)  # Wczytaj lekcje użytkownika

        # Wczytanie przykładów z pliku
        self.load_examples_from_file('examples.txt')

        # Inicjalizacja asystenta
        self.assistant_steps = [
            self.translate("hints.Introduction"),
            self.translate("hints.Indentation and Code Structure"),
            self.translate("hints.Fix Errors in Code"),
            # Dodaj więcej kroków asystenta w razie potrzeby
        ]
        self.current_assistant_step = 0

        logging.info("Aplikacja została zainicjalizowana.")

    # ---------------------------------------------
    #          Wczytywanie pliku językowego
    # ---------------------------------------------
    def load_language(self):
        language = self.settings.value("language", "en")
        language_file = os.path.join("languages", f"{language}.json")
        try:
            with open(language_file, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
            logging.info(f"Załadowano język: {language}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Nie można załadować pliku językowego:\n{e}")
            logging.error(f"Nie można załadować pliku językowego: {e}")
            self.translations = {}

    def translate(self, key):
        keys = key.split('.')
        result = self.translations
        for k in keys:
            result = result.get(k, {})
        if isinstance(result, str):
            return result
        else:
            return key  # Jeśli tłumaczenie jest brakujące, zwróć klucz

    # ---------------------------------------------
    #     Inicjalizacja interfejsu użytkownika
    # ---------------------------------------------
    def initUI(self):
        # Główny widget centralny
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Główny poziomy layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Panel lekcji
        self.lesson_tree = QTreeWidget()
        self.lesson_tree.setHeaderLabel(self.translate("labels.Lessons"))
        self.lesson_tree.itemClicked.connect(self.load_lesson)
        self.lesson_tree.setAccessibleName("Lesson List")

        # Panel historii
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.load_lesson_from_history)
        self.history_list.setAccessibleName("Lesson History List")

        # Przyciski zarządzania lekcjami
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

        # Dodanie drzewa lekcji i przycisków do layoutu
        lesson_panel = QWidget()
        lesson_layout = QVBoxLayout()
        lesson_panel.setLayout(lesson_layout)
        lesson_layout.addWidget(self.lesson_tree)
        lesson_layout.addLayout(lesson_button_layout)

        # Panel historii
        history_panel = QWidget()
        history_layout = QVBoxLayout()
        history_panel.setLayout(history_layout)
        history_layout.addWidget(self.history_list)

        # Zakładki
        self.tabs = QTabWidget()
        self.tabs.addTab(lesson_panel, self.translate("labels.Lessons"))
        self.tabs.addTab(history_panel, self.translate("labels.History"))
        self.tabs.setAccessibleName("Lesson and History Tabs")

        # Panel treści lekcji
        self.lesson_content = QTextEdit()
        self.lesson_content.setReadOnly(True)
        self.lesson_content.setAccessibleName("Lesson Content")

        # Przyciski w panelu treści lekcji
        lesson_content_buttons = QHBoxLayout()
        play_content_button = QPushButton(self.translate("actions.Play Lesson Content"))
        play_content_button.clicked.connect(self.play_lesson_content)
        play_content_button.setAccessibleName("Play Lesson Content Button")
        lesson_content_buttons.addWidget(play_content_button)

        # Dodanie przycisków do layoutu
        lesson_content_widget = QWidget()
        lesson_content_widget.setLayout(lesson_content_buttons)

        # Edytor kodu
        self.code_editor = CodeEditor()
        self.highlighter = PythonHighlighter(self.code_editor.document())
        self.code_editor.textChanged.connect(self.real_time_analysis)
        self.code_editor.setAccessibleName("Code Editor")

        # Konsola wyjścia
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setStyleSheet("background-color: black; color: white;")
        self.output_console.setAccessibleName("Output Console")

        # Przyciski do regulacji rozmiaru czcionki
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

        # Przyciski kontrolne
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
        self.new_example_button.hide()  # Początkowo ukryty
        self.new_example_button.setAccessibleName("Load New Example Button")
        self.debug_button = QPushButton(self.translate("actions.Debug Code"))
        self.debug_button.clicked.connect(self.run_debugger)
        self.debug_button.setAccessibleName("Debug Code Button")

        # Przyciski do odczytu wyjścia
        self.read_output_button = QPushButton(self.translate("actions.Read Output"))
        self.read_output_button.clicked.connect(self.read_output_console)
        self.read_output_button.setAccessibleName("Read Output Button")

        # Układ przycisków
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.step_button)
        button_layout.addWidget(self.hint_button)
        button_layout.addWidget(self.new_example_button)
        button_layout.addWidget(self.debug_button)
        button_layout.addWidget(self.read_output_button)

        # Układ edytora kodu i konsoli
        code_layout = QVBoxLayout()
        self.code_label = QLabel(self.translate("labels.Code Editor:"))
        code_layout.addWidget(self.code_label)
        code_layout.addLayout(font_button_layout)
        code_layout.addWidget(self.code_editor)
        code_layout.addLayout(button_layout)
        self.output_label = QLabel(self.translate("labels.Output Console:"))
        code_layout.addWidget(self.output_label)
        code_layout.addWidget(self.output_console)

        # Rozdzielacz dla treści lekcji i edytora kodu
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.tabs)

        lesson_content_panel = QWidget()
        lesson_content_layout = QVBoxLayout()
        lesson_content_panel.setLayout(lesson_content_layout)
        lesson_content_layout.addWidget(QLabel(self.translate("labels.Lesson Content")))
        lesson_content_layout.addWidget(self.lesson_content)
        lesson_content_layout.addWidget(lesson_content_widget)  # Dodanie widgetu z przyciskami

        code_panel = QWidget()
        code_panel.setLayout(code_layout)

        splitter.addWidget(lesson_content_panel)
        splitter.addWidget(code_panel)
        splitter.setSizes([200, 400, 600])

        main_layout.addWidget(splitter)

        # Pasek statusu
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Dodanie etykiety postępu
        self.progress_label = QLabel()
        self.status_bar.addPermanentWidget(self.progress_label)

        # Główne menu
        self.create_menu()

        # Pasek narzędzi
        self.create_toolbar()

        # Zastosowanie stylów i wczytanie ustawień
        self.load_settings()

    # ---------------------------------------------
    #          Tworzenie Głównego Menu
    # ---------------------------------------------
    def create_menu(self):
        menubar = self.menuBar()

        # Menu Plik
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
        load_examples_action.triggered.connect(self.select_examples_file)  # Dodana metoda
        file_menu.addAction(load_examples_action)

        exit_action = QAction(self.translate("menu.Exit"), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menu Pomoc
        help_menu = menubar.addMenu(self.translate("menu.Help"))

        assistant_action = QAction(self.translate("actions.Show Assistant"), self)
        assistant_action.triggered.connect(self.show_assistant)
        help_menu.addAction(assistant_action)

        about_action = QAction(self.translate("menu.About"), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # Menu Lekcje Użytkownika
        user_lessons_menu = menubar.addMenu(self.translate("menu.User Lessons"))

        export_lessons_action = QAction(self.translate("actions.Export Lessons"), self)
        export_lessons_action.triggered.connect(self.export_user_lessons)
        user_lessons_menu.addAction(export_lessons_action)

        import_lessons_action = QAction(self.translate("actions.Import Lessons"), self)
        import_lessons_action.triggered.connect(self.import_user_lessons)
        user_lessons_menu.addAction(import_lessons_action)

    # ---------------------------------------------
    #          Tworzenie Paska Narzędzi
    # ---------------------------------------------
    def create_toolbar(self):
        self.tool_bar = QToolBar("Main Toolbar")
        self.tool_bar.setMovable(False)
        self.addToolBar(self.tool_bar)

        # Stylizacja paska narzędzi
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

        # Akcja ustawień
        settings_icon_path = "images/settings_icon.png"  # Upewnij się, że plik 'settings_icon.png' znajduje się w katalogu 'images/'
        if os.path.exists(settings_icon_path):
            settings_icon = QIcon(settings_icon_path)
        else:
            settings_icon = QIcon()  # Pusty ikona, jeśli nie znaleziono
            logging.warning(f"Ikona ustawień nie została znaleziona na ścieżce: {settings_icon_path}")
        settings_action = QAction(settings_icon, self.translate("menu.Settings"), self)
        settings_action.setStatusTip(self.translate("menu.Settings"))
        settings_action.triggered.connect(self.open_settings_dialog)
        self.tool_bar.addAction(settings_action)

        # Pasek wyszukiwania dokumentacji
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(self.translate("search_placeholder"))
        self.search_bar.returnPressed.connect(self.search_documentation)
        self.tool_bar.addWidget(self.search_bar)

        # Pasek wyszukiwania lekcji
        self.search_lessons_bar = QLineEdit()
        self.search_lessons_bar.setPlaceholderText(self.translate("search_placeholder_lessons"))
        self.search_lessons_bar.returnPressed.connect(self.search_lessons)
        self.tool_bar.addWidget(self.search_lessons_bar)

    # ---------------------------------------------
    #          Otwieranie Dialogu Ustawień
    # ---------------------------------------------
    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.apply_settings()
            logging.info("Ustawienia zostały zaktualizowane przez użytkownika.")

    # ---------------------------------------------
    #          Ładowanie i Zastosowanie Ustawień
    # ---------------------------------------------
    def load_settings(self):
        self.update_stylesheet()
        self.load_font_settings()
        self.apply_interface_scale()
        logging.info("Ustawienia zostały wczytane.")

    def apply_settings(self):
        self.update_stylesheet()
        self.load_font_settings()
        self.apply_interface_scale()
        self.set_tts_voice()
        logging.info("Ustawienia zostały zastosowane.")

    def update_stylesheet(self):
        # Rozpoczęcie od stylu motywu
        theme = self.settings.value("theme", "light")
        if theme == "dark":
            stylesheet = self.dark_theme_stylesheet()
        else:
            stylesheet = self.light_theme_stylesheet()

        # Zastosowanie niestandardowych kolorów, jeśli są ustawione
        bg_color = self.settings.value("bg_color", None)
        text_color = self.settings.value("text_color", None)
        if bg_color and text_color:
            # Modyfikacja podstawowego stylu motywu z niestandardowymi kolorami
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

        # Zastosowanie profilu kolorów
        color_profile = self.settings.value("color_profile", "Default")
        if color_profile == "Protanopia":
            # Zastosowanie kolorów dla protanopii
            color_profile_stylesheet = """
            /* Protanopia - dostosowanie kolorów */
            QListWidget::item:selected, QTreeWidget::item:selected {
                background-color: #FFD700;
                color: #000000;
            }
            """
            stylesheet += color_profile_stylesheet
        elif color_profile == "Deuteranopia":
            # Zastosowanie kolorów dla deuteranopii
            color_profile_stylesheet = """
            /* Deuteranopia - dostosowanie kolorów */
            QListWidget::item:selected, QTreeWidget::item:selected {
                background-color: #FF69B4;
                color: #000000;
            }
            """
            stylesheet += color_profile_stylesheet
        elif color_profile == "Tritanopia":
            # Zastosowanie kolorów dla tritanopii
            color_profile_stylesheet = """
            /* Tritanopia - dostosowanie kolorów */
            QListWidget::item:selected, QTreeWidget::item:selected {
                background-color: #87CEFA;
                color: #000000;
            }
            """
            stylesheet += color_profile_stylesheet
        # W przeciwnym razie brak zmian

        # Zastosowanie trybu drżenia
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

        # Zastosowanie trybu dysleksji
        dyslexia_mode = self.settings.value("dyslexia_mode", False, type=bool)
        if dyslexia_mode:
            dyslexia_stylesheet = """
            QLabel, QLineEdit, QTextEdit, QPlainTextEdit, QListWidget, QTreeWidget {
                font-family: "Comic Sans MS";
            }
            """
            stylesheet += dyslexia_stylesheet

        # Zastosowanie trybu autyzmu
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

        # Zastosowanie niestandardowego stylu przycisków, jeśli nie jest nadpisany przez tryb drżenia
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

        # Ustawienie finalnego stylu
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
            logging.info(f"Ustawiono głos TTS na: {selected_voice_id}")
        else:
            # Jeśli nie wybrano głosu, użyj domyślnego
            logging.warning("Nie wybrano głosu TTS. Używany jest domyślny głos.")

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
        logging.info(f"Zastosowano skalowanie interfejsu: {interface_scale}%, nowy rozmiar czcionki: {new_font_size}")

    def apply_font_settings(self):
        # Upewnij się, że wszystkie odpowiednie widgety używają czcionki aplikacji
        self.code_editor.setFont(QApplication.instance().font())
        self.output_console.setFont(QApplication.instance().font())
        self.lesson_content.setFont(QApplication.instance().font())
        self.setFont(QApplication.instance().font())  # Ustaw czcionkę głównego okna

    def load_font_settings(self):
        # Wczytaj rodzinę czcionek i rozmiar z ustawień
        font_family = self.settings.value("font_family", "Arial")
        font_size = self.settings.value("font_size", 12, type=int)
        font = QFont(font_family, font_size)
        self.code_editor.setFont(font)
        self.output_console.setFont(font)
        self.lesson_content.setFont(font)
        self.setFont(font)  # Zastosuj do głównego okna
        logging.info(f"Wczytano ustawienia czcionki: {font_family}, {font_size}")

    # ---------------------------------------------
    #          Pokazanie Asystenta
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
                self.translate("labels.Assistant"),
                message + "\n\n" + self.translate("prompts.Continue Assistant"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.next_assistant_step()
            else:
                self.current_assistant_step = 0  # Zresetuj asystenta
                logging.info("Asystent został przerwany przez użytkownika.")
        else:
            self.current_assistant_step = 0  # Zresetuj asystenta
            logging.info("Asystent zakończył prezentację.")

    # ---------------------------------------------
    #          Wyszukiwanie Dokumentacji
    # ---------------------------------------------
    def search_documentation(self):
        query = self.search_bar.text().strip()
        if query:
            url = f"https://docs.python.org/3/search.html?q={query}"
            webbrowser.open(url)
            logging.info(f"Otworzono dokumentację dla zapytania: {query}")
        else:
            QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.Enter Search Query"))

    # ---------------------------------------------
    #          Wyszukiwanie Lekcji
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
        # Wyświetlenie przefiltrowanych lekcji w drzewie lekcji
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
        logging.info(f"Wyszukano lekcje z zapytaniem: {query}")

    # ---------------------------------------------
    #          Uruchomienie Kodowania
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
            logging.error(f"Błąd składni: {error_message}")
            return

        selected_item = self.lesson_tree.currentItem()
        if selected_item:
            lesson = selected_item.data(0, Qt.ItemDataRole.UserRole)
            language = self.settings.value("language", "en")
            lesson_title = lesson['title'].get(language, next(iter(lesson['title'].values()), ''))
            if lesson and lesson_title == self.translate("hints.Indentation and Code Structure"):
                QMessageBox.information(self, self.translate("messages.Congratulations"), self.translate("messages.Corrected Indentations"))
                self.read_text_aloud(self.translate("messages.Corrected Indentations"))
                logging.info("Użytkownik poprawił wcięcia.")
                # Dodaj lekcję do ukończonych
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
                    logging.info("Użytkownik naprawił kod.")
                    # Dodaj lekcję do ukończonych
                    if lesson_title not in self.completed_lessons:
                        self.completed_lessons.append(lesson_title)
                        self.save_progress()
                        self.update_lesson_list()
                    return
                except Exception as e:
                    QMessageBox.critical(self, self.translate("Error"), f"{self.translate('messages.Still Errors')}\n{e}")
                    logging.error(f"Program nadal zawiera błędy: {e}")
                    return

        temp_file = "temp_code.py"
        try:
            with open(temp_file, "w", encoding='utf-8') as f:
                f.write(code)
        except Exception as e:
            QMessageBox.critical(self, self.translate("Error"), f"Nie można zapisać do pliku tymczasowego:\n{e}")
            logging.error(f"Nie można zapisać do pliku tymczasowego: {e}")
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

        # Wyłącz przyciski podczas uruchamiania kodu
        self.run_button.setEnabled(False)
        self.step_button.setEnabled(False)
        self.debug_button.setEnabled(False)

        logging.info("Kod został uruchomiony.")

    def cleanup_temp_file(self, temp_file):
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logging.info(f"Plik tymczasowy {temp_file} został usunięty.")
        except Exception as e:
            logging.error(f"Błąd przy usuwaniu pliku tymczasowego {temp_file}: {e}")

    def execution_finished(self):
        # Ponownie włącz przyciski
        self.run_button.setEnabled(True)
        self.step_button.setEnabled(True)
        self.debug_button.setEnabled(True)

        output = self.output_console.toPlainText()
        if output:
            self.read_text_aloud(f"{self.translate('messages.Code Executed Successfully')}: {output}")
        else:
            self.read_text_aloud(self.translate("messages.Code Executed Successfully"))
        logging.info(self.translate("messages.Code Executed Successfully"))
        self.process = None  # Zresetuj proces

        # Aktualizacja postępu
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
    #       Analiza Kodu w Czasie Rzeczywistym
    # ---------------------------------------------
    def real_time_analysis(self):
        code = self.code_editor.toPlainText()
        error_message = self.analyze_code(code)
        if error_message:
            self.status_bar.showMessage(error_message)
        else:
            self.status_bar.clearMessage()

    # ---------------------------------------------
    #       Odbieranie Danych z Procesu
    # ---------------------------------------------
    def data_ready(self):
        output = self.process.readAllStandardOutput().data().decode()
        self.output_console.append(output)
        # Jeśli wystąpiły błędy, zostaną przekierowane do standardowego wyjścia
        if "Traceback" in output or "Error" in output or "Exception" in output:
            self.read_text_aloud(f"{self.translate('Error')}: {output}")

    # ---------------------------------------------
    #               Pokazanie Podpowiedzi
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
        logging.info(f"Pokazano podpowiedź dla lekcji: {lesson_name}")

    # ---------------------------------------------
    #       Uruchamianie Kodowania Krok po Kroku
    # ---------------------------------------------
    def run_step_by_step(self):
        code = self.code_editor.toPlainText()
        self.lines = code.split('\n')
        self.current_line = 0
        self.output_console.clear()
        self.run_next_line()
        logging.info("Uruchomiono kod krok po kroku.")

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
                self.output_console.append(f"{self.translate('Error')} {self.current_line+1}: {e}")
                self.read_text_aloud(f"{self.translate('Error')} {self.current_line+1}: {e}")
                logging.error(f"Błąd na linii {self.current_line+1}: {e}")
                return
            self.current_line += 1
            # Podświetlenie bieżącej linii
            cursor = self.code_editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            for _ in range(self.current_line):
                cursor.movePosition(QTextCursor.MoveOperation.Down)
            self.code_editor.setTextCursor(cursor)
            # Uruchomienie następnej linii po krótkim opóźnieniu
            QTimer.singleShot(500, self.run_next_line)
        else:
            self.output_console.append(self.translate("messages.Code Executed Successfully"))
            self.read_text_aloud(self.translate("messages.Code Executed Successfully"))
            logging.info("Kod został wykonany krok po kroku.")

    # ---------------------------------------------
    #               Debugowanie Kodu
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
            QMessageBox.critical(self, self.translate("Error"), f"Nie można zapisać do pliku tymczasowego:\n{e}")
            logging.error(f"Nie można zapisać do pliku tymczasowego: {e}")
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

        # Wyłącz przyciski podczas uruchamiania debugera
        self.run_button.setEnabled(False)
        self.step_button.setEnabled(False)
        self.debug_button.setEnabled(False)

        logging.info("Rozpoczęto debugowanie kodu.")

    # ---------------------------------------------
    #          Zapisywanie Kodów Użytkownika
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
                logging.info(f"Zapisano kod do pliku: {file_name}")
            except Exception as e:
                QMessageBox.critical(self, self.translate("Error"), f"Nie można zapisać kodu do pliku:\n{e}")
                logging.error(f"Nie można zapisać kodu do pliku: {e}")

    # ---------------------------------------------
    #          Wczytywanie Kodów Użytkownika
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
                logging.info(f"Wczytano kod z pliku: {file_name}")
            except Exception as e:
                QMessageBox.critical(self, self.translate("Error"), f"Nie można wczytać kodu z pliku:\n{e}")
                logging.error(f"Nie można wczytać kodu z pliku: {e}")

    # ---------------------------------------------
    #                Informacje o Programie
    # ---------------------------------------------
    def show_about(self):
        QMessageBox.information(self, self.translate("menu.About"), f"{self.translate('app_title')}\nWersja 1.0")

    # ---------------------------------------------
    #          Zapisywanie i Wczytywanie Lekcji Użytkownika
    # ---------------------------------------------
    def save_user_lessons_to_file(self, filename):
        # Filtracja lekcji użytkownika
        user_lessons = [lesson for lesson in self.lessons if lesson.get('type') == 'user']
        # Zapis lekcji użytkownika do pliku
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(user_lessons, f, ensure_ascii=False, indent=4)
            logging.info(f"Lekcje użytkownika zostały zapisane do pliku: {filename}")
        except Exception as e:
            QMessageBox.critical(self, self.translate("Error"), f"Nie można zapisać lekcji użytkownika do pliku:\n{e}")
            logging.error(f"Nie można zapisać lekcji użytkownika do pliku: {e}")

    def load_user_lessons_from_file(self, filename):
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    user_lessons = json.load(f)
                self.lessons.extend(user_lessons)
                logging.info(f"Lekcje użytkownika zostały wczytane z pliku: {filename}")
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Error", f"Błąd dekodowania JSON w {filename}: {e}")
                logging.error(f"Błąd dekodowania JSON w {filename}: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Nie można wczytać lekcji użytkownika z pliku:\n{e}")
                logging.error(f"Nie można wczytać lekcji użytkownika z pliku: {e}")
        else:
            logging.warning(f"Plik lekcji użytkownika nie został znaleziony: {filename}")
        self.update_lesson_list()  # Aktualizacja listy lekcji po wczytaniu

    # ---------------------------------------------
    #          Ładowanie i Aktualizacja Lekcji
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
                QMessageBox.critical(self, self.translate("Error"), f"Błąd dekodowania JSON w {file}: {e}")
                logging.error(f"Błąd dekodowania JSON w {file}: {e}")
            except FileNotFoundError:
                QMessageBox.critical(self, self.translate("Error"), f"Plik lekcji nie został znaleziony: {file}")
                logging.error(f"Plik lekcji nie został znaleziony: {file}")
            except Exception as e:
                QMessageBox.critical(self, self.translate("Error"), f"Błąd podczas ładowania {file}: {e}")
                logging.error(f"Błąd podczas ładowania {file}: {e}")
        self.update_lesson_list()
        logging.info("Lekcje zostały wczytane z plików JSON.")

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
        # Aktualizacja postępu
        total_lessons = len(self.lessons)
        completed = len(self.completed_lessons)
        progress_percent = (completed / total_lessons) * 100 if total_lessons > 0 else 0
        self.progress_label.setText(f"{self.translate('labels.Progress:')} {completed}/{total_lessons} ({progress_percent:.1f}%)")
        logging.info("Lista lekcji została zaktualizowana.")

        # Aktualizacja listy historii
        self.history_list.clear()
        for lesson_title in self.completed_lessons:
            item = QListWidgetItem(lesson_title)
            self.history_list.addItem(item)

    # ---------------------------------------------
    #             Ładowanie Lekcji
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
            logging.info(f"Załadowano lekcję: {lesson_title}")
        else:
            self.lesson_content.clear()
            self.code_editor.clear()
            self.new_example_button.hide()

    # ---------------------------------------------
    #          Ładowanie Lekcji z Historii
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
    #          Simplifikacja Treści Lekcji
    # ---------------------------------------------
    def simplify_language(self, content):
        # Proste zastępowanie trudnych słów na prostsze
        replacements = {
            "implementacja": "wprowadzenie",
            "funkcja": "działanie",
            "definiowanie": "tworzenie",
            "parametr": "wartość",
            "argument": "wartość",
            "instrukcja": "polecenie",
            "operacja": "działanie",
            # Dodaj więcej zamienników w razie potrzeby
        }
        for word, simple_word in replacements.items():
            content = content.replace(word, simple_word)
        return content

    # ---------------------------------------------
    #          Wczytywanie Przykładów z Pliku
    # ---------------------------------------------
    def load_examples_from_file(self, filename):
        if not os.path.exists(filename):
            # Jeśli plik nie istnieje, stwórz go z przykładowymi danymi
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("def example():\n    print('To jest przykładowy kod')\n    print('Popraw wcięcia!')\n###")
        # Teraz wczytaj przykłady z pliku
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            self.indentation_examples = content.strip().split('###')
            self.indentation_examples = [example.strip() for example in self.indentation_examples if example.strip()]
            logging.info("Przykłady wcięć zostały wczytane.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Nie można wczytać przykładów z pliku:\n{e}")
            logging.error(f"Nie można wczytać przykładów z pliku: {e}")

    # ---------------------------------------------
    #          Aktualizacja Listy Lekcji
    # ---------------------------------------------
    # Metoda już zaimplementowana powyżej

    # ---------------------------------------------
    #          Dodawanie Nowej Lekcji
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
                # Upewnij się, że klucz 'en' jest zawsze obecny
                new_lesson = {
                    "title": {language: title, 'en': title} if language != 'en' else {language: title},
                    "content": {language: content, 'en': content} if language != 'en' else {language: content},
                    "type": "user",
                    "category": {language: category, 'en': category} if language != 'en' else {language: category}
                }
                self.lessons.append(new_lesson)
                self.update_lesson_list()
                self.save_user_lessons_to_file(self.user_lessons_file)
                # Zapisz lekcję do oddzielnego pliku JSON
                self.save_lesson_to_file(new_lesson)
                logging.info(f"Dodano nową lekcję: {title}")

    def save_lesson_to_file(self, lesson):
        # Stwórz katalog user_lessons, jeśli nie istnieje
        user_lessons_dir = os.path.join('lessons', 'user_lessons')
        os.makedirs(user_lessons_dir, exist_ok=True)
        # Generuj unikalną nazwę pliku
        existing_files = glob.glob(os.path.join(user_lessons_dir, 'user_lesson_*.json'))
        lesson_number = len(existing_files) + 1
        filename = os.path.join(user_lessons_dir, f'user_lesson_{lesson_number}.json')
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(lesson, f, ensure_ascii=False, indent=4)
            logging.info(f"Lekcja użytkownika została zapisana do pliku: {filename}")
        except Exception as e:
            QMessageBox.critical(self, self.translate("Error"), f"Nie można zapisać lekcji do pliku:\n{e}")
            logging.error(f"Nie można zapisać lekcji do pliku: {e}")

    def validate_lesson_title(self, title):
        # Implementacja logiki walidacji, np. brak znaków specjalnych
        return re.match("^[A-Za-z0-9 _-]+$", title) is not None

    def validate_lesson_content(self, content):
        # Implementacja logiki walidacji, np. minimalna długość
        return len(content.strip()) > 10

    # ---------------------------------------------
    #          Edytowanie Istniejącej Lekcji
    # ---------------------------------------------
    def edit_lesson(self):
        selected_item = self.lesson_tree.currentItem()
        if selected_item:
            lesson = selected_item.data(0, Qt.ItemDataRole.UserRole)
            if lesson and lesson['type'] == 'user':
                language = self.settings.value("language", "en")
                # Znajdź indeks lekcji w self.lessons
                try:
                    lesson_index = self.lessons.index(lesson)
                except ValueError:
                    QMessageBox.critical(self, self.translate("Error"), self.translate("messages.Lesson Not Found"))
                    logging.error("Wybrana lekcja nie została znaleziona na liście lekcji.")
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
                        # Aktualizacja lekcji w self.lessons
                        lesson['title'][language] = new_title
                        if language != 'en':
                            lesson['title']['en'] = new_title  # Aktualizacja klucza 'en' również
                        lesson['content'][language] = new_content
                        if language != 'en':
                            lesson['content']['en'] = new_content
                        lesson['category'][language] = new_category
                        if language != 'en':
                            lesson['category']['en'] = new_category
                        self.update_lesson_list()
                        self.save_user_lessons_to_file(self.user_lessons_file)
                        # Aktualizacja pliku lekcji
                        self.update_lesson_file(lesson)
                        logging.info(f"Edytowano lekcję: {new_title}")
            else:
                QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.Cannot Edit Default Lesson"))
                logging.warning("Próba edytowania domyślnej lekcji.")
        else:
            QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.No Lesson Selected"))
            logging.warning("Nie wybrano lekcji do edycji.")

    def update_lesson_file(self, lesson):
        # Znajdź odpowiadający plik lekcji
        user_lessons_dir = os.path.join('lessons', 'user_lessons')
        lesson_files = glob.glob(os.path.join(user_lessons_dir, 'user_lesson_*.json'))
        for file in lesson_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    existing_lesson = json.load(f)
                if existing_lesson == lesson:
                    with open(file, 'w', encoding='utf-8') as f:
                        json.dump(lesson, f, ensure_ascii=False, indent=4)
                    logging.info(f"Plik lekcji został zaktualizowany: {file}")
                    return
            except Exception as e:
                logging.error(f"Błąd podczas aktualizacji pliku lekcji {file}: {e}")
        # Jeśli nie znaleziono, zapisz jako nowy plik
        self.save_lesson_to_file(lesson)

    # ---------------------------------------------
    #          Usuwanie Istniejącej Lekcji
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
                    # Usuń plik lekcji
                    self.remove_lesson_file(lesson)
                    logging.info(f"Usunięto lekcję: {lesson_title}")
            else:
                QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.Cannot Delete Default Lesson"))
                logging.warning("Próba usunięcia domyślnej lekcji.")
        else:
            QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.No Lesson Selected"))
            logging.warning("Nie wybrano lekcji do usunięcia.")

    def remove_lesson_file(self, lesson):
        user_lessons_dir = os.path.join('lessons', 'user_lessons')
        lesson_files = glob.glob(os.path.join(user_lessons_dir, 'user_lesson_*.json'))
        for file in lesson_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    existing_lesson = json.load(f)
                if existing_lesson == lesson:
                    os.remove(file)
                    logging.info(f"Usunięto plik lekcji: {file}")
            except Exception as e:
                logging.error(f"Błąd podczas usuwania pliku lekcji {file}: {e}")

    # ---------------------------------------------
    #          Usuwanie Kategorii Lekcji
    # ---------------------------------------------
    def delete_category(self):
        selected_item = self.lesson_tree.currentItem()
        if selected_item:
            if selected_item.parent() is None:
                # To jest kategoria
                category = selected_item.text(0)
                # Pobierz lekcje w tej kategorii
                lessons_in_category = [lesson for lesson in self.lessons if lesson.get('category', {}).get(self.settings.value("language", "en"), 'Other') == category]
                # Sprawdź, czy wszystkie lekcje są tworzone przez użytkownika
                if all(lesson['type'] == 'user' for lesson in lessons_in_category):
                    reply = QMessageBox.question(
                        self,
                        self.translate("labels.Delete Category"),
                        f"{self.translate('messages.Confirm Delete Category')} '{category}'?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        # Usuń lekcje z tej kategorii
                        self.lessons = [lesson for lesson in self.lessons if lesson.get('category', {}).get(self.settings.value("language", "en"), 'Other') != category]
                        self.update_lesson_list()
                        self.save_user_lessons_to_file(self.user_lessons_file)
                        # Usuń odpowiadające pliki lekcji
                        self.remove_category_lesson_files(category)
                        logging.info(f"Usunięto kategorię: {category}")
                else:
                    QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.Cannot Delete Default Category"))
                    logging.warning("Próba usunięcia kategorii zawierającej domyślne lekcje.")
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
                    logging.info(f"Usunięto plik lekcji: {file}")
            except Exception as e:
                logging.error(f"Błąd podczas usuwania pliku lekcji {file}: {e}")

    # ---------------------------------------------
    #          Ładowanie i Zapisywanie Postępu
    # ---------------------------------------------
    def load_progress(self):
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Error", f"Błąd dekodowania JSON w {self.progress_file}: {e}")
                logging.error(f"Błąd dekodowania JSON w {self.progress_file}: {e}")
                return []
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Nie można wczytać postępu z pliku:\n{e}")
                logging.error(f"Nie można wczytać postępu z pliku: {e}")
                return []
        else:
            return []

    def save_progress(self):
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.completed_lessons, f, ensure_ascii=False, indent=4)
            logging.info("Postęp został zapisany.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Nie można zapisać postępu do pliku:\n{e}")
            logging.error(f"Nie można zapisać postępu do pliku: {e}")

    # ---------------------------------------------
    #          Wczytywanie Przykładów Indentacji
    # ---------------------------------------------
    def load_new_indentation_example(self):
        if not hasattr(self, 'indentation_examples') or not self.indentation_examples:
            QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.No Indentation Examples"))
            logging.warning("Brak dostępnych przykładów wcięć.")
            return
        example = random.choice(self.indentation_examples)
        self.code_editor.setPlainText(example)
        self.output_console.clear()
        self.status_bar.clearMessage()
        logging.info("Załadowano nowy przykład wcięcia.")

    # ---------------------------------------------
    #          Ładowanie Przykładowego Kodowania z Błędami
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
    #          Eksportowanie Lekcji Użytkownika
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
                logging.info(f"Lekcje użytkownika zostały wyeksportowane do {file_name}")
            except Exception as e:
                QMessageBox.critical(self, self.translate("Error"), f"{self.translate('messages.Export Failed')}: {e}")
                logging.error(f"Eksportowanie lekcji nie powiodło się: {e}")

    # ---------------------------------------------
    #          Importowanie Lekcji Użytkownika
    # ---------------------------------------------
    def import_user_lessons(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, self.translate("actions.Import Lessons"), "", "JSON Files (*.json)"
        )
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    imported_lessons = json.load(f)
                # Walidacja i dodanie lekcji
                for lesson in imported_lessons:
                    if 'title' in lesson and 'content' in lesson and 'category' in lesson:
                        self.lessons.append(lesson)
                        self.save_lesson_to_file(lesson)
                    else:
                        logging.warning(f"Nieprawidłowy format lekcji w {file_name}: {lesson}")
                self.update_lesson_list()
                self.save_user_lessons_to_file(self.user_lessons_file)
                QMessageBox.information(self, self.translate("messages.Success"), self.translate("messages.Lessons Imported Successfully"))
                logging.info(f"Lekcje użytkownika zostały zaimportowane z {file_name}")
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, self.translate("Error"), f"Błąd dekodowania JSON: {e}")
                logging.error(f"Błąd dekodowania JSON podczas importu: {e}")
            except Exception as e:
                QMessageBox.critical(self, self.translate("Error"), f"{self.translate('messages.Import Failed')}: {e}")
                logging.error(f"Importowanie lekcji nie powiodło się: {e}")

    # ---------------------------------------------
    #          Zapisywanie i Ładowanie Postępu
    # ---------------------------------------------
    # Metoda już zaimplementowana powyżej

    # ---------------------------------------------
    #          Pokazanie Lekcji
    # ---------------------------------------------
    # Metoda już zaimplementowana powyżej

    # ---------------------------------------------
    #          Pokazanie Lekcji z Historii
    # ---------------------------------------------
    # Metoda już zaimplementowana powyżej

    # ---------------------------------------------
    #          Prosty Tryb Języka
    # ---------------------------------------------
    # Metoda już zaimplementowana powyżej

    # ---------------------------------------------
    #          Uruchamianie Kodowania Krok po Kroku
    # ---------------------------------------------
    # Metoda już zaimplementowana powyżej

    # ---------------------------------------------
    #          Uruchamianie Debuggera
    # ---------------------------------------------
    # Metoda już zaimplementowana powyżej

    # ---------------------------------------------
    #          Odtwarzanie Treści Lekcji Głośno
    # ---------------------------------------------
    def play_lesson_content(self):
        text = self.lesson_content.toPlainText()
        if not text.strip():
            # Wyodrębnienie tekstu z treści HTML
            html_content = self.lesson_content.toHtml()
            text = re.sub('<[^<]+?>', '', html_content)
        if text.strip():
            if self.tts_enabled:
                self.read_text_aloud(text)
                logging.info("Treść lekcji została odczytana głośno.")
            else:
                logging.info("TTS jest wyłączone. Treść lekcji nie została odczytana.")
        else:
            QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.No Content to Read"))
            logging.warning("Próba odczytania pustej treści.")

    def read_output_console(self):
        text = self.output_console.toPlainText()
        if text.strip():
            if self.tts_enabled:
                self.read_text_aloud(text)
                logging.info("Wyjście konsoli zostało odczytane głośno.")
            else:
                logging.info("TTS jest wyłączone. Wyjście konsoli nie zostało odczytane.")
        else:
            QMessageBox.warning(self, self.translate("Warning"), self.translate("messages.No Output to Read"))
            logging.warning("Próba odczytania pustego wyjścia konsoli.")

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
        QMessageBox.critical(self, self.translate("Error"), f"Błąd TTS: {error_message}")
        logging.error(f"Błąd TTS: {error_message}")
        self.tts_busy = False
        self.process_tts_queue()

    # ---------------------------------------------
    #          Validacja Nazwy i Treści Lekcji
    # ---------------------------------------------
    # Metody już zaimplementowane powyżej

    # ---------------------------------------------
    #          Odtwarzanie Tekstu Głośno
    # ---------------------------------------------
    # Metody już zaimplementowane powyżej

    # ---------------------------------------------
    #          Główne Wykonanie Aplikacji
    # ---------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PythonTutorApp()  # Tworzymy tutaj!
    window.show()
    sys.exit(app.exec())
