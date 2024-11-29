import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QPlainTextEdit, QFileDialog, QMessageBox, QTabWidget, QSplitter, QVBoxLayout, QWidget, QMenu, QDialog, QInputDialog
)
from PyQt6.QtGui import QIcon, QKeySequence, QAction, QFont
from PyQt6.QtCore import Qt, QTimer, QSettings, QProcess

# Importuj klasy z innych modułów
from code_editor import CodeEditor
from navigator_panel import CodeNavigatorPanel
from settings_dialog import SettingsDialog
# Importuj inne potrzebne moduły
import subprocess
import io
import contextlib
import unittest
import git
import mimetypes

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AiCodeBuddy")
        self.resize(1200, 800)

        # Inicjalizacja ścieżki repozytorium Git
        self.git_repo_path = '.'
        self.settings = {}
        self.load_settings()

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
        self.current_editor = None
        self.add_new_tab()

        # Panel nawigacji kodu
        self.navigator_panel = CodeNavigatorPanel(self)

        # Podłączenie sygnału symbols_updated
        self.current_editor.symbols_updated.connect(self.navigator_panel.update_symbols)
        self.current_editor.update_symbols_panel()

        # Splitter do podziału edytora i paneli bocznych
        # W konstruktorze MainWindow
        # Splitter do podziału edytora i paneli bocznych
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(self.navigator_panel)
        main_splitter.addWidget(self.tab_widget)
        main_splitter.setStretchFactor(0, 1)  # Navigator panel
        main_splitter.setStretchFactor(1, 4)  # Tab widget

        # Główny splitter do podziału edytora i wyjścia
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(main_splitter)
        splitter.addWidget(self.output)
        splitter.setStretchFactor(0, 4)  # Main editor area
        splitter.setStretchFactor(1, 1)  # Output panel


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
        self.load_settings()
        # Zastosuj ustawienia do edytorów
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            editor.apply_settings(self.settings)
        # Zastosuj motyw
        self.apply_theme(self.settings['theme'])
    def create_menu(self):
        """
        Tworzy menu aplikacji.
        """
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

        delete_branch_action = QAction("Usuń Branch", self)
        delete_branch_action.triggered.connect(self.git_delete_branch)
        git_menu.addAction(delete_branch_action)

        checkout_branch_action = QAction("Przełącz Branch", self)
        checkout_branch_action.triggered.connect(self.git_checkout_branch)
        git_menu.addAction(checkout_branch_action)

        reset_commit_action = QAction("Resetuj do Commita", self)
        reset_commit_action.triggered.connect(self.git_reset_commit)
        git_menu.addAction(reset_commit_action)


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
            # Zastosuj wszystkie ustawienia w jednym miejscu
            self.apply_settings(self.settings)

    def load_settings(self):
        settings = QSettings('AiCodeBuddy', 'Settings')
        self.settings['clean_paste'] = settings.value('clean_paste', True, type=bool)
        self.settings['smart_indent'] = settings.value('smart_indent', True, type=bool)
        self.settings['confirm_delete'] = settings.value('confirm_delete', True, type=bool)
        self.settings['theme'] = settings.value('theme', 'Jasny')
        self.settings['font_size'] = settings.value('font_size', 12, type=int)
        self.settings['auto_save'] = settings.value('auto_save', True, type=bool)
        self.settings['focus_mode'] = settings.value('focus_mode', False, type=bool)
        self.settings['git_repo_path'] = settings.value('git_repo_path', '', type=str)
        if self.settings['git_repo_path']:
            self.git_repo_path = self.settings['git_repo_path']

    def save_settings(self):
        settings = QSettings('AiCodeBuddy', 'Settings')
        settings.setValue('clean_paste', self.settings['clean_paste'])
        settings.setValue('smart_indent', self.settings['smart_indent'])
        settings.setValue('confirm_delete', self.settings['confirm_delete'])
        settings.setValue('theme', self.settings['theme'])
        settings.setValue('font_size', self.settings['font_size'])
        settings.setValue('auto_save', self.settings['auto_save'])
        settings.setValue('focus_mode', self.settings['focus_mode'])
        settings.setValue('git_repo_path', self.settings.get('git_repo_path', ''))
    
    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

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
            self.setStyleSheet("")  # Resetuj styl dla jasnego motywu

        # Zastosuj motyw w edytorach
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            editor.apply_theme(theme)
        # Zastosuj motyw w panelu nawigacji
        self.navigator_panel.apply_theme(theme)

    def apply_settings(self, settings):
        self.settings = settings
        # Zastosuj motyw
        self.apply_theme(settings['theme'])
        # Przekaż ustawienia do wszystkich otwartych edytorów
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            editor.apply_settings(settings)
        # Zastosuj tryb skupienia
        if settings.get('focus_mode', False):
            self.navigator_panel.hide()
            self.output.hide()
        else:
            self.navigator_panel.show()
            self.output.show()
        # Aktualizacja ustawień auto-save
        if settings.get('auto_save', True):
            self.auto_save_timer.start()
        else:
            self.auto_save_timer.stop()
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

        # Połączenie sygnałów do aktualizacji paska statusu i tytułu zakładki
        editor.textChanged.connect(self.update_status_bar)
        editor.undoAvailable.connect(self.update_status_bar)
        editor.redoAvailable.connect(self.update_status_bar)
        editor.document().modificationChanged.connect(lambda:
        self.update_tab_title(editor))

    def update_tab_title(self, editor):
        index = self.tab_widget.indexOf(editor)
        if index != -1:
            filename = self.tab_widget.tabText(index).rstrip(' *')
            if editor.document().isModified():
                self.tab_widget.setTabText(index, filename + ' *')
            else:
                self.tab_widget.setTabText(index, filename)

    def on_tab_changed(self, index):
        # Odłącz sygnał z poprzedniego edytora
        if hasattr(self, 'current_editor') and self.current_editor:
            try:
                self.current_editor.symbols_updated.disconnect(self.navigator_panel.update_symbols)
            except TypeError:
                pass  # Sygnał już odłączony lub niepodłączony

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
                # Ustal język na podstawie rozszerzenia
                _, ext = os.path.splitext(path)
                language = self.get_language_from_extension(ext)
                # Dodaj nową zakładkę z edytorem
                editor = CodeEditor()
                editor.setPlainText(code)
                editor.highlighter.set_language(language)
                self.tab_widget.addTab(editor, filename)
                self.tab_widget.setCurrentWidget(editor)
                # Przechowywanie ścieżki pliku
                current_index = self.tab_widget.currentIndex()
                self.tab_paths[current_index] = path
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nie można otworzyć pliku:\n{e}")
    
    def get_language_from_extension(self, ext):
        ext = ext.lower()
        if ext == '.py':
            return 'python'
        elif ext in ('.js', '.jsx'):
            return 'javascript'
        elif ext in ('.cpp', '.hpp', '.cc', '.cxx', '.h'):
            return 'cpp'
        elif ext == '.go':
            return 'go'
        else:
            return 'plaintext'  # Domyślny język dla nieobsługiwanych plików

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
            current_branch = repo.active_branch
            # Sprawdź, czy branch ma ustawiony upstream
            if current_branch.tracking_branch() is None:
                # Ustaw upstream
                origin.push(refspec='{}:{}'.format(current_branch.name, current_branch.name), set_upstream=True)
            else:
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

    def git_delete_branch(self):
        try:
            repo = git.Repo(self.git_repo_path)
            branches = [head.name for head in repo.branches if head.name != repo.active_branch.name]
            if not branches:
                QMessageBox.information(self, "Git", "Brak innych branchy do usunięcia.")
                return
            branch, ok = QInputDialog.getItem(self, "Usuń Branch", "Wybierz branch do usunięcia:", branches, 0, False)
            if ok and branch:
                repo.delete_head(branch, force=True)
                QMessageBox.information(self, "Git", f"Branch {branch} został usunięty.")
            else:
                QMessageBox.warning(self, "Git", "Nie wybrano brancha do usunięcia.")
        except Exception as e:
            QMessageBox.critical(self, "Git Błąd", f"Wystąpił błąd podczas usuwania brancha: {e}")

    def git_checkout_branch(self):
        try:
            repo = git.Repo(self.git_repo_path)
            branches = [head.name for head in repo.heads]
            branch, ok = QInputDialog.getItem(self, "Przełącz Branch", "Wybierz branch do przełączenia:", branches, 0, False)
            if ok and branch:
                repo.git.checkout(branch)
                QMessageBox.information(self, "Git", f"Przełączono na branch: {branch}")
        except Exception as e:
            QMessageBox.critical(self, "Git Błąd", f"Wystąpił błąd podczas przełączania brancha: {e}")

    def git_reset_commit(self):
        try:
            repo = git.Repo(self.git_repo_path)
            commits = list(repo.iter_commits())
            commit_messages = [f"{commit.hexsha[:7]} - {commit.message.strip()}" for commit in commits]
            commit, ok = QInputDialog.getItem(self, "Reset do Commita", "Wybierz commit do resetu:", commit_messages, 0, False)
            if ok and commit:
                sha = commit.split(' - ')[0]
                repo.git.reset('--hard', sha)
                QMessageBox.information(self, "Git", f"Zresetowano do commita: {sha}")
        except Exception as e:
            QMessageBox.critical(self, "Git Błąd", f"Wystąpił błąd podczas resetowania: {e}")


    def select_git_repo(self):
        path = QFileDialog.getExistingDirectory(self, "Wybierz Repozytorium Git", "")
        if path:
            try:
                repo = git.Repo(path)
                self.git_repo_path = path
                # Zapisz ścieżkę do ustawień
                self.settings['git_repo_path'] = path
                self.save_settings()
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