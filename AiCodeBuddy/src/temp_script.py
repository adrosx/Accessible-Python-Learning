# ---------------------------------------------
#            Importowanie bibliotek
# ---------------------------------------------
import sys
import json
import os
import requests
import csv
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QLabel, QLineEdit,
    QTextEdit, QMessageBox, QDateTimeEdit, QComboBox, QFileDialog,
    QDialog, QGridLayout, QScrollArea, QMenu, QToolBar, QInputDialog,
    QCheckBox, QCalendarWidget, QSystemTrayIcon, QStyle, QProgressBar,
    QColorDialog, QTabWidget, QFormLayout, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QDateTime, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import (
    QIcon, QAction, QPixmap, QFont, QKeySequence, QShortcut, QColor
)
ssss
# ---------------------------------------------
#        Klasa reprezentująca projekt
# ---------------------------------------------
class Project:
    def __init__(self, name, description, notes=''):
        self.name = name
        self.description = description
        self.notes = notes
        self.tasks = []

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'notes': self.notes,
            'tasks': [task.to_dict() for task in self.tasks]
        }

    @staticmethod
    def from_dict(data):
        project = Project(data['name'], data['description'], data.get('notes', ''))
        project.tasks = [Task.from_dict(task_data) for task_data in data.get('tasks', [])]
        return project

# ---------------------------------------------
#        Klasa reprezentująca zadanie
# ---------------------------------------------
class Task:
    def __init__(self, title, description, due_date, priority, status, tags=None, images=None):
        self.title = title
        self.description = description
        self.due_date = due_date
        self.priority = priority
        self.status = status
        self.tags = tags or []
        self.images = images or []

    def to_dict(self):
        return {
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.toString(Qt.DateFormat.ISODate),
            'priority': self.priority,
            'status': self.status,
            'tags': self.tags,
            'images': self.images
        }

    @staticmethod
    def from_dict(data):
        return Task(
            data['title'],
            data['description'],
            QDateTime.fromString(data['due_date'], Qt.DateFormat.ISODate),
            data['priority'],
            data['status'],
            data.get('tags', []),
            data.get('images', [])
        )

# ---------------------------------------------
#          Główna klasa aplikacji
# ---------------------------------------------
class TaskManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mój Piękny Menedżer Zadań")
        self.setWindowIcon(QIcon("icon.png"))
        self.resize(1200, 800)

        # Inicjalizacja danych
        self.projects = []  # Lista projektów
        self.current_project = None  # Aktualnie wybrany projekt
        self.background_images = []
        self.themes = self.load_themes()
        self.current_theme = 'Pastel Pink'
        self.dark_mode_enabled = False
        self.custom_theme = {}  # Słownik przechowujący kolory niestandardowego motywu

        # Ustawienia interfejsu
        self.interface_settings = {
            'show_description': True,
            'show_notes': True,
            'show_due_date': True,
            'show_tags': True,
            'show_priority': True,
            'show_status': True,
            'show_images': True,
            'show_instructions': True,
            'show_projects_section': True,
            'show_tasks_section': True
        }

        # Inicjalizacja interfejsu
        self.initUI()

        # Ustawienie powiadomień
        self.setup_notifications()

    # ---------------------------------------------
    #       Inicjalizacja interfejsu użytkownika
    # ---------------------------------------------
    def initUI(self):
        self.create_widgets()
        self.create_menu()
        self.create_toolbar()
        self.create_layouts()
        self.apply_theme(self.current_theme)
        self.update_interface()

        # Skróty klawiszowe
        self.create_shortcuts()

    # ---------------------------------------------
    #            Tworzenie widżetów
    # ---------------------------------------------
    def create_widgets(self):
        # Lista projektów
        self.project_list = QListWidget()
        self.project_list.itemClicked.connect(self.display_project_details)
        self.project_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.project_list.customContextMenuRequested.connect(self.show_project_context_menu)
        self.project_list.setMaximumWidth(200)

        # Lista zadań
        self.task_list = QListWidget()
        self.task_list.itemClicked.connect(self.display_task_details)
        self.task_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(self.show_task_context_menu)
        self.task_list.setDragDropMode(QListWidget.DragDropMode.NoDragDrop)

        # Pola do edycji szczegółów projektu
        self.project_name_edit = QLineEdit()
        self.project_description_edit = QTextEdit()
        self.project_notes_edit = QTextEdit()

        # Pola do edycji szczegółów zadania
        self.title_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.due_date_edit = QDateTimeEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDateTime(QDateTime.currentDateTime())

        # ComboBoxy dla priorytetu i statusu
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(['Niski', 'Średni', 'Wysoki'])

        self.status_combo = QComboBox()
        self.status_combo.addItems(['Do zrobienia', 'W trakcie', 'Zakończone'])

        # Pole do wprowadzania tagów
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Wprowadź tagi oddzielone przecinkami")

        # Pole wyszukiwania
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Wyszukaj zadania...")
        self.search_edit.textChanged.connect(self.search_tasks)

        # Opcje sortowania
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['Brak', 'Priorytet', 'Status', 'Data'])
        self.sort_combo.currentTextChanged.connect(self.sort_tasks)

        # Przycisk do zapisywania zadania
        self.save_task_button = QPushButton("Zapisz zadanie")
        self.save_task_button.clicked.connect(self.save_task)

        # Przyciski do dodawania obrazów do zadania
        self.add_image_from_disk_button = QPushButton("Dodaj obraz z dysku")
        self.add_image_from_disk_button.clicked.connect(self.add_image_from_disk)

        self.add_image_from_url_button = QPushButton("Dodaj obraz z URL")
        self.add_image_from_url_button.clicked.connect(self.add_image_from_url)

        # Panel instrukcji
        self.instructions_panel = QTextEdit()
        self.instructions_panel.setReadOnly(True)
        self.instructions_panel.setText(self.load_instructions())

        self.toggle_instructions_button = QPushButton("Pokaż/Ukryj instrukcje")
        self.toggle_instructions_button.clicked.connect(self.toggle_instructions)

        # Przełącznik trybu ciemnego
        self.dark_mode_toggle = QAction("Tryb ciemny", self)
        self.dark_mode_toggle.setCheckable(True)
        self.dark_mode_toggle.triggered.connect(self.toggle_dark_mode)

        # Widok kalendarza
        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self.show_tasks_on_date)

        # Pasek postępu projektu
        self.project_progress_bar = QProgressBar()
        self.project_progress_bar.setValue(0)

        # Lista projektów do wyboru przy tworzeniu zadania
        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self.change_current_project)

        # Rozwijane menu z motywami
        self.theme_dropdown = QComboBox()
        self.theme_dropdown.addItems(list(self.themes.keys()) + ['Niestandardowy'])
        self.theme_dropdown.setCurrentText(self.current_theme)
        self.theme_dropdown.currentTextChanged.connect(self.change_theme_dropdown)

    # ---------------------------------------------
    #               Tworzenie menu
    # ---------------------------------------------
    def create_menu(self):
        menu_bar = self.menuBar()

        # Menu "Plik"
        file_menu = menu_bar.addMenu("Plik")

        save_action = QAction(QIcon("save.png"), "Zapisz", self)
        save_action.triggered.connect(self.save_projects)

        load_action = QAction(QIcon("load.png"), "Wczytaj", self)
        load_action.triggered.connect(self.load_projects)

        export_csv_action = QAction("Eksportuj do CSV", self)
        export_csv_action.triggered.connect(self.export_tasks_to_csv)

        exit_action = QAction(QIcon("exit.png"), "Wyjdź", self)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(save_action)
        file_menu.addAction(load_action)
        file_menu.addAction(export_csv_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # Menu "Widok"
        view_menu = menu_bar.addMenu("Widok")

        manage_bg_images_action = QAction("Zarządzaj obrazami planera", self)
        manage_bg_images_action.triggered.connect(self.manage_background_images)

        view_menu.addAction(manage_bg_images_action)
        view_menu.addAction(self.dark_mode_toggle)

        # Menu "Ustawienia"
        settings_menu = menu_bar.addMenu("Ustawienia")

        settings_action = QAction("Ustawienia", self)
        settings_action.triggered.connect(self.open_settings_dialog)

        settings_menu.addAction(settings_action)

        # Menu "Pomoc"
        help_menu = menu_bar.addMenu("Pomoc")

        instructions_action = QAction("Instrukcje", self)
        instructions_action.triggered.connect(self.toggle_instructions)

        help_menu.addAction(instructions_action)

    # ---------------------------------------------
    #          Tworzenie paska narzędzi
    # ---------------------------------------------
    def create_toolbar(self):
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # Akcje dla projektów
        add_project_action = QAction(QIcon("add_project.png"), "Nowy projekt", self)
        add_project_action.triggered.connect(self.create_new_project)
        add_project_action.setShortcut(QKeySequence("Ctrl+Shift+N"))

        delete_project_action = QAction(QIcon("delete_project.png"), "Usuń projekt", self)
        delete_project_action.triggered.connect(self.delete_project)

        # Akcje dla zadań
        add_task_action = QAction(QIcon("add_task.png"), "Nowe zadanie", self)
        add_task_action.triggered.connect(self.clear_task_details)
        add_task_action.setShortcut(QKeySequence("Ctrl+N"))

        delete_task_action = QAction(QIcon("delete_task.png"), "Usuń zadanie", self)
        delete_task_action.triggered.connect(self.delete_task)
        delete_task_action.setShortcut(QKeySequence("Ctrl+D"))

        toolbar.addAction(add_project_action)
        toolbar.addAction(delete_project_action)
        toolbar.addSeparator()
        toolbar.addAction(add_task_action)
        toolbar.addAction(delete_task_action)

        # Dodanie rozwijanego menu z motywami
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("  Motyw: "))
        toolbar.addWidget(self.theme_dropdown)

    # ---------------------------------------------
    #        Ustawienie układów interfejsu
    # ---------------------------------------------
    def create_layouts(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        self.main_layout = QHBoxLayout()
        main_widget.setLayout(self.main_layout)

        # Układ dla listy projektów
        self.project_section = QWidget()
        project_layout = QVBoxLayout()
        self.project_section.setLayout(project_layout)

        project_label = QLabel("Projekty")
        project_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        project_layout.addWidget(project_label)
        project_layout.addWidget(self.project_list)

        # Układ dla szczegółów projektu
        project_detail_label = QLabel("Szczegóły projektu")
        project_detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        project_layout.addWidget(project_detail_label)
        project_layout.addWidget(QLabel("Nazwa"))
        project_layout.addWidget(self.project_name_edit)
        project_layout.addWidget(QLabel("Opis"))
        project_layout.addWidget(self.project_description_edit)
        project_layout.addWidget(QLabel("Notatki"))
        project_layout.addWidget(self.project_notes_edit)
        project_layout.addWidget(QLabel("Postęp projektu"))
        project_layout.addWidget(self.project_progress_bar)

        # Układ dla listy zadań
        self.task_section = QWidget()
        task_layout = QVBoxLayout()
        self.task_section.setLayout(task_layout)

        task_layout.addWidget(self.search_edit)
        task_layout.addWidget(self.sort_combo)
        task_layout.addWidget(self.task_list)

        # Układ dla szczegółów zadania
        detail_label = QLabel("Szczegóły zadania")
        detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        task_layout.addWidget(detail_label)
        task_layout.addWidget(QLabel("Tytuł"))
        task_layout.addWidget(self.title_edit)
        task_layout.addWidget(QLabel("Opis"))
        task_layout.addWidget(self.description_edit)
        task_layout.addWidget(QLabel("Data"))
        task_layout.addWidget(self.due_date_edit)
        task_layout.addWidget(QLabel("Priorytet"))
        task_layout.addWidget(self.priority_combo)
        task_layout.addWidget(QLabel("Status"))
        task_layout.addWidget(self.status_combo)
        task_layout.addWidget(QLabel("Tagi"))
        task_layout.addWidget(self.tags_edit)

        # Przyciski do dodawania obrazów
        image_buttons_layout = QHBoxLayout()
        image_buttons_layout.addWidget(self.add_image_from_disk_button)
        image_buttons_layout.addWidget(self.add_image_from_url_button)
        task_layout.addLayout(image_buttons_layout)

        task_layout.addWidget(self.save_task_button)

        # Przycisk do instrukcji
        task_layout.addWidget(self.toggle_instructions_button)
        task_layout.addWidget(self.instructions_panel)

        # Układ dla widoku kalendarza
        calendar_layout = QVBoxLayout()
        calendar_label = QLabel("Kalendarz")
        calendar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        calendar_layout.addWidget(calendar_label)
        calendar_layout.addWidget(self.calendar)

        # Dodanie układów do głównego układu
        self.main_layout.addWidget(self.project_section, 20)
        self.main_layout.addWidget(self.task_section, 50)
        self.main_layout.addLayout(calendar_layout, 30)

        # Akceptacja przeciągania i upuszczania
        self.setAcceptDrops(True)

    # ---------------------------------------------
    #        Aktualizacja interfejsu użytkownika
    # ---------------------------------------------
    def update_interface(self):
        # Show or hide widgets based on interface settings
        self.description_edit.parentWidget().setVisible(self.interface_settings['show_description'])
        self.due_date_edit.parentWidget().setVisible(self.interface_settings['show_due_date'])
        self.priority_combo.parentWidget().setVisible(self.interface_settings['show_priority'])
        self.status_combo.parentWidget().setVisible(self.interface_settings['show_status'])
        self.tags_edit.parentWidget().setVisible(self.interface_settings['show_tags'])
        self.project_notes_edit.parentWidget().setVisible(self.interface_settings['show_notes'])
        self.add_image_from_disk_button.setVisible(self.interface_settings['show_images'])
        self.add_image_from_url_button.setVisible(self.interface_settings['show_images'])
        self.instructions_panel.setVisible(self.interface_settings['show_instructions'])
        self.toggle_instructions_button.setVisible(self.interface_settings['show_instructions'])

        # Ukrywanie sekcji projektów i zadań
        self.project_section.setVisible(self.interface_settings['show_projects_section'])
        self.task_section.setVisible(self.interface_settings['show_tasks_section'])

    # ---------------------------------------------
    #           Tworzenie skrótów klawiszowych
    # ---------------------------------------------
    def create_shortcuts(self):
        # Nowe zadanie
        new_task_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_task_shortcut.activated.connect(self.clear_task_details)

        # Edycja zadania
        edit_task_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        edit_task_shortcut.activated.connect(self.edit_task)

    # ---------------------------------------------
    #          Wczytywanie instrukcji
    # ---------------------------------------------
    def load_instructions(self):
        instructions = """
**Instrukcje użytkownika:**

- **Dodawanie nowego projektu:**
  1. Kliknij ikonę "Nowy projekt" na pasku narzędzi.
  2. Wprowadź nazwę i opis projektu.
  3. Projekt zostanie dodany do listy projektów.

- **Dodawanie nowego zadania:**
  1. Wybierz projekt z listy.
  2. Kliknij ikonę "Nowe zadanie" na pasku narzędzi.
  3. Wprowadź szczegóły zadania.
  4. Kliknij "Zapisz zadanie".

- **Filtrowanie i sortowanie zadań:**
  - Użyj pola wyszukiwania, aby filtrować zadania.
  - Wybierz kryterium sortowania z rozwijanego menu.

- **Tryb ciemny:**
  - Przełącz tryb ciemny z menu "Widok" lub klikając odpowiednią opcję.

- **Dostosowywanie motywu:**
  - W menu "Ustawienia" wybierz "Ustawienia", aby dostosować motyw i interfejs.

- **Ukrywanie elementów interfejsu:**
  - W menu "Ustawienia" możesz ukryć niektóre pola, jeśli nie są Ci potrzebne.

- **Eksport zadań:**
  - Wybierz "Plik" → "Eksportuj do CSV", aby wyeksportować zadania do pliku CSV.

- **Powiadomienia:**
  - Aplikacja automatycznie powiadomi Cię o nadchodzących terminach.

Miłego użytkowania aplikacji!
"""
        return instructions

    # ---------------------------------------------
    #          Pokazanie/Ukrycie instrukcji
    # ---------------------------------------------
    def toggle_instructions(self):
        visible = self.instructions_panel.isVisible()
        self.instructions_panel.setVisible(not visible)

    # ---------------------------------------------
    #              Wczytywanie motywów
    # ---------------------------------------------
    def load_themes(self):
        themes = {
            'Pastel Pink': {
                'background_color': '#ffe4e1',
                'text_color': '#8b0000',
                'button_color': '#ff69b4',
                'hover_color': '#ff1493',
                'task_item_background': '#fff0f5',
                'task_item_text_color': '#8b0000'
            },
            'Ocean Blue': {
                'background_color': '#e0ffff',
                'text_color': '#00008b',
                'button_color': '#00bfff',
                'hover_color': '#1e90ff',
                'task_item_background': '#f0f8ff',
                'task_item_text_color': '#00008b'
            },
            'Mint Green': {
                'background_color': '#f5fff5',
                'text_color': '#006400',
                'button_color': '#32cd32',
                'hover_color': '#2e8b57',
                'task_item_background': '#f0fff0',
                'task_item_text_color': '#006400'
            },
            'Lavender': {
                'background_color': '#e6e6fa',
                'text_color': '#4b0082',
                'button_color': '#9370db',
                'hover_color': '#8a2be2',
                'task_item_background': '#f8f8ff',
                'task_item_text_color': '#4b0082'
            },
            'Sunny Yellow': {
                'background_color': '#ffffe0',
                'text_color': '#daa520',
                'button_color': '#ffd700',
                'hover_color': '#ffc107',
                'task_item_background': '#fffacd',
                'task_item_text_color': '#daa520'
            },
            'Peach': {
                'background_color': '#ffdab9',
                'text_color': '#cd5b45',
                'button_color': '#ff7f50',
                'hover_color': '#ff6347',
                'task_item_background': '#ffefd5',
                'task_item_text_color': '#cd5b45'
            },
            'Coral': {
                'background_color': '#fff0f5',
                'text_color': '#8b008b',
                'button_color': '#ff69b4',
                'hover_color': '#ff1493',
                'task_item_background': '#fff5ee',
                'task_item_text_color': '#8b008b'
            },
            'Sky Gray': {
                'background_color': '#f0f0f0',
                'text_color': '#2f4f4f',
                'button_color': '#a9a9a9',
                'hover_color': '#808080',
                'task_item_background': '#dcdcdc',
                'task_item_text_color': '#2f4f4f'
            },
            'Cream': {
                'background_color': '#fffdd0',
                'text_color': '#8b4513',
                'button_color': '#deb887',
                'hover_color': '#d2b48c',
                'task_item_background': '#f5f5dc',
                'task_item_text_color': '#8b4513'
            },
            'Lilac': {
                'background_color': '#f3e5f5',
                'text_color': '#6a1b9a',
                'button_color': '#ba68c8',
                'hover_color': '#9c27b0',
                'task_item_background': '#ede7f6',
                'task_item_text_color': '#6a1b9a'
            },
            'Dark Mode': {
                'background_color': '#121212',
                'text_color': '#ffffff',
                'button_color': '#1e1e1e',
                'hover_color': '#333333',
                'task_item_background': '#1e1e1e',
                'task_item_text_color': '#ffffff'
            },
        }
        return themes

    # ---------------------------------------------
    #           Zastosowanie wybranego motywu
    # ---------------------------------------------
    def apply_theme(self, theme_name):
        if theme_name == 'Niestandardowy':
            theme = self.custom_theme
        else:
            theme = self.themes.get(theme_name, self.themes['Pastel Pink'])

        if not theme:
            QMessageBox.warning(self, "Brak motywu", "Brak zdefiniowanego motywu niestandardowego.")
            return

        # Upewnij się, że wszystkie klucze są obecne
        default_theme = self.themes['Pastel Pink']
        for key in default_theme:
            if key not in theme or not theme[key]:
                theme[key] = default_theme[key]

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme['background_color']};
            }}
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {theme['text_color']};
            }}
            QLineEdit, QTextEdit, QDateTimeEdit, QComboBox {{
                background-color: #ffffff;
                border: 1px solid {theme['button_color']};
                border-radius: 5px;
                padding: 5px;
                font-size: 13px;
            }}
            QPushButton {{
                background-color: {theme['button_color']};
                color: #ffffff;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {theme['hover_color']};
            }}
            QListWidget {{
                background-color: #ffffff;
                border: 1px solid {theme['button_color']};
                border-radius: 5px;
                font-size: 13px;
            }}
            QListWidget::item {{
                background-color: {theme['task_item_background']};
                color: {theme['task_item_text_color']};
                padding: 10px;
            }}
            QListWidget::item:selected {{
                background-color: {theme['button_color']};
                color: #ffffff;
            }}
            QMenuBar, QMenu, QToolBar {{
                background-color: {theme['background_color']};
                color: {theme['text_color']};
            }}
            QMenuBar::item, QMenu::item {{
                background-color: {theme['background_color']};
                color: {theme['text_color']};
            }}
            QMenuBar::item:selected, QMenu::item:selected {{
                background-color: {theme['hover_color']};
            }}
        """)
        self.dark_mode_enabled = (theme_name == 'Dark Mode')

    # ---------------------------------------------
    #       Zmiana motywu z rozwijanego menu
    # ---------------------------------------------
    def change_theme_dropdown(self, theme_name):
        self.current_theme = theme_name
        if theme_name == 'Niestandardowy':
            self.open_settings_dialog()
        else:
            self.apply_theme(theme_name)

    # ---------------------------------------------
    #             Przełączanie trybu ciemnego
    # ---------------------------------------------
    def toggle_dark_mode(self):
        if self.dark_mode_enabled:
            self.current_theme = 'Pastel Pink'
        else:
            self.current_theme = 'Dark Mode'
        self.apply_theme(self.current_theme)
        self.theme_dropdown.setCurrentText(self.current_theme)
        self.dark_mode_enabled = not self.dark_mode_enabled

    # ---------------------------------------------
    #         Otwieranie okna ustawień
    # ---------------------------------------------
    def open_settings_dialog(self):
        dialog = SettingsDialog(self.custom_theme, self.interface_settings)
        if dialog.exec():
            self.custom_theme = dialog.get_custom_theme()
            self.interface_settings = dialog.get_interface_settings()
            if dialog.theme_changed:
                self.apply_theme('Niestandardowy')
                self.theme_dropdown.setCurrentText('Niestandardowy')
            self.update_interface()

    # ---------------------------------------------
    #          Tworzenie nowego projektu
    # ---------------------------------------------
    def create_new_project(self):
        name, ok = QInputDialog.getText(self, "Nowy projekt", "Wprowadź nazwę projektu:")
        if ok and name:
            description, ok = QInputDialog.getMultiLineText(self, "Nowy projekt", "Wprowadź opis projektu:")
            if ok:
                project = Project(name, description)
                self.projects.append(project)
                self.refresh_project_list()
                self.project_combo.addItem(project.name)
                QMessageBox.information(self, "Sukces", "Projekt został dodany.")

    # ---------------------------------------------
    #            Usuwanie projektu
    # ---------------------------------------------
    def delete_project(self):
        selected_item = self.project_list.currentItem()
        if selected_item:
            index = self.project_list.row(selected_item)
            project = self.projects.pop(index)
            self.refresh_project_list()
            self.project_combo.removeItem(self.project_combo.findText(project.name))
            QMessageBox.information(self, "Sukces", "Projekt został usunięty.")
            self.current_project = None
            self.refresh_task_list()
        else:
            QMessageBox.warning(self, "Brak wyboru", "Wybierz projekt do usunięcia.")

    # ---------------------------------------------
    #        Wyświetlanie szczegółów projektu
    # ---------------------------------------------
    def display_project_details(self, item):
        index = self.project_list.row(item)
        project = self.projects[index]
        self.current_project = project

        self.project_name_edit.setText(project.name)
        self.project_description_edit.setPlainText(project.description)
        self.project_notes_edit.setPlainText(project.notes)

        self.refresh_task_list()
        self.update_project_progress()
        self.project_combo.setCurrentText(project.name)

    # ---------------------------------------------
    #        Odświeżanie listy projektów
    # ---------------------------------------------
    def refresh_project_list(self):
        self.project_list.clear()
        for project in self.projects:
            item = QListWidgetItem(project.name)
            item.setData(Qt.ItemDataRole.UserRole, project)
            item.setFont(QFont('Arial', 12))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.project_list.addItem(item)

    # ---------------------------------------------
    #             Zmiana bieżącego projektu
    # ---------------------------------------------
    def change_current_project(self):
        project_name = self.project_combo.currentText()
        for project in self.projects:
            if project.name == project_name:
                self.current_project = project
                self.refresh_task_list()
                self.update_project_progress()
                break

    # ---------------------------------------------
    #            Zapisywanie zadania
    # ---------------------------------------------
    def save_task(self):
        if not self.current_project:
            QMessageBox.warning(self, "Brak projektu", "Wybierz projekt przed dodaniem zadania.")
            return

        title = self.title_edit.text()
        if not title:
            QMessageBox.warning(self, "Brak tytułu", "Wprowadź tytuł zadania.")
            return

        selected_item = self.task_list.currentItem()
        if selected_item:
            index = self.task_list.row(selected_item)
            task = self.current_project.tasks[index]
        else:
            task = Task("", "", QDateTime.currentDateTime(), "", "", [])
            self.current_project.tasks.append(task)

        task.title = title
        task.description = self.description_edit.toPlainText() if self.interface_settings['show_description'] else ""
        task.due_date = self.due_date_edit.dateTime() if self.interface_settings['show_due_date'] else QDateTime.currentDateTime()
        task.priority = self.priority_combo.currentText() if self.interface_settings['show_priority'] else "Niski"
        task.status = self.status_combo.currentText() if self.interface_settings['show_status'] else "Do zrobienia"
        task.tags = [tag.strip() for tag in self.tags_edit.text().split(',')] if self.interface_settings['show_tags'] else []

        self.refresh_task_list()
        self.clear_task_details()
        self.update_project_progress()

    # ---------------------------------------------
    #            Usuwanie zadania
    # ---------------------------------------------
    def delete_task(self):
        if not self.current_project:
            QMessageBox.warning(self, "Brak projektu", "Wybierz projekt.")
            return

        selected_item = self.task_list.currentItem()
        if selected_item:
            index = self.task_list.row(selected_item)
            del self.current_project.tasks[index]
            self.refresh_task_list()
            self.clear_task_details()
            self.update_project_progress()
        else:
            QMessageBox.warning(self, "Brak wyboru", "Wybierz zadanie do usunięcia.")

    # ---------------------------------------------
    #          Odświeżanie listy zadań
    # ---------------------------------------------
    def refresh_task_list(self):
        self.task_list.clear()
        if not self.current_project:
            return

        for task in self.current_project.tasks:
            item = QListWidgetItem(f"{task.title} ({task.status})")
            item.setData(Qt.ItemDataRole.UserRole, task)
            item.setFont(QFont('Arial', 12))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.task_list.addItem(item)

    # ---------------------------------------------
    #    Wyświetlanie szczegółów wybranego zadania
    # ---------------------------------------------
    def display_task_details(self, item):
        index = self.task_list.row(item)
        task = self.current_project.tasks[index]

        self.title_edit.setText(task.title)
        self.description_edit.setPlainText(task.description)
        self.due_date_edit.setDateTime(task.due_date)
        self.priority_combo.setCurrentText(task.priority)
        self.status_combo.setCurrentText(task.status)
        self.tags_edit.setText(', '.join(task.tags))

    # ---------------------------------------------
    #          Czyszczenie pól zadania
    # ---------------------------------------------
    def clear_task_details(self):
        self.task_list.clearSelection()
        self.title_edit.clear()
        self.description_edit.clear()
        self.due_date_edit.setDateTime(QDateTime.currentDateTime())
        self.priority_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self.tags_edit.clear()

    # ---------------------------------------------
    #            Zapisywanie projektów
    # ---------------------------------------------
    def save_projects(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Zapisz projekty", "", "JSON Files (*.json)", options=options
        )
        if file_name:
            data = {
                'projects': [project.to_dict() for project in self.projects],
                'background_images': self.background_images,
                'current_theme': self.current_theme,
                'custom_theme': self.custom_theme,
                'interface_settings': self.interface_settings
            }
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                QMessageBox.information(self, "Sukces", "Projekty zostały zapisane.")
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać projektów: {e}")

    # ---------------------------------------------
    #           Wczytywanie projektów
    # ---------------------------------------------
    def load_projects(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Wczytaj projekty", "", "JSON Files (*.json)", options=options
        )
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.projects = [Project.from_dict(proj_data) for proj_data in data.get('projects', [])]
                self.background_images = data.get('background_images', [])
                self.current_theme = data.get('current_theme', self.current_theme)
                self.custom_theme = data.get('custom_theme', {})
                self.interface_settings = data.get('interface_settings', self.interface_settings)
                self.apply_theme(self.current_theme)
                self.theme_dropdown.setCurrentText(self.current_theme)
                self.refresh_project_list()
                self.refresh_task_list()
                self.refresh_background_images()
                self.update_interface()
                QMessageBox.information(self, "Sukces", "Projekty zostały wczytane.")
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nie udało się wczytać projektów: {e}")

    # ---------------------------------------------
    #           Eksport zadań do CSV
    # ---------------------------------------------
    def export_tasks_to_csv(self):
        if not self.current_project:
            QMessageBox.warning(self, "Brak projektu", "Wybierz projekt do eksportu zadań.")
            return

        file_name, _ = QFileDialog.getSaveFileName(self, "Eksportuj zadania", "", "CSV Files (*.csv)")
        if file_name:
            try:
                with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Tytuł', 'Opis', 'Data', 'Priorytet', 'Status', 'Tagi'])
                    for task in self.current_project.tasks:
                        writer.writerow([
                            task.title,
                            task.description,
                            task.due_date.toString(Qt.DateFormat.ISODate),
                            task.priority,
                            task.status,
                            ','.join(task.tags)
                        ])
                QMessageBox.information(self, "Sukces", "Zadania zostały wyeksportowane do CSV.")
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nie udało się wyeksportować zadań: {e}")

    # ---------------------------------------------
    #    Pokazanie menu kontekstowego dla zadań
    # ---------------------------------------------
    def show_task_context_menu(self, position):
        menu = QMenu()
        if self.interface_settings['show_images']:
            manage_images_action = QAction("Zarządzaj obrazami zadania", self)
            manage_images_action.triggered.connect(self.manage_task_images)
            menu.addAction(manage_images_action)

        delete_task_action = QAction("Usuń zadanie", self)
        delete_task_action.triggered.connect(self.delete_task)

        menu.addAction(delete_task_action)
        menu.exec(self.task_list.viewport().mapToGlobal(position))

    # ---------------------------------------------
    #  Pokazanie menu kontekstowego dla projektów
    # ---------------------------------------------
    def show_project_context_menu(self, position):
        menu = QMenu()
        delete_project_action = QAction("Usuń projekt", self)
        delete_project_action.triggered.connect(self.delete_project)

        menu.addAction(delete_project_action)
        menu.exec(self.project_list.viewport().mapToGlobal(position))

    # ---------------------------------------------
    #          Zarządzanie obrazami zadania
    # ---------------------------------------------
    def manage_task_images(self):
        selected_item = self.task_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Brak wyboru", "Wybierz zadanie.")
            return

        index = self.task_list.row(selected_item)
        task = self.current_project.tasks[index]

        dialog = ImageManagerDialog(task.images, "Obrazy zadania")
        dialog.exec()

    # ---------------------------------------------
    #         Zarządzanie obrazami planera
    # ---------------------------------------------
    def manage_background_images(self):
        dialog = ImageManagerDialog(self.background_images, "Obrazy planera", refresh_callback=self.refresh_background_images)
        dialog.exec()

    # ---------------------------------------------
    #   Odświeżanie galerii obrazów planera
    # ---------------------------------------------
    def refresh_background_images(self):
        pass  # Implementacja odświeżania galerii

    # ---------------------------------------------
    #    Obsługa przeciągania plików do aplikacji
    # ---------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                self.background_images.append(file_path)
                self.refresh_background_images()

    # ---------------------------------------------
    #    Dodawanie obrazu do zadania z dysku
    # ---------------------------------------------
    def add_image_from_disk(self):
        selected_item = self.task_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Brak wyboru", "Wybierz zadanie.")
            return

        task_index = self.task_list.row(selected_item)
        task = self.current_project.tasks[task_index]

        file_dialog = QFileDialog()
        file_names, _ = file_dialog.getOpenFileNames(
            self, "Wybierz obrazy", "", "Obrazy (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_names:
            task.images.extend(file_names)
            QMessageBox.information(self, "Sukces", "Obrazy zostały dodane do zadania.")

    # ---------------------------------------------
    #     Dodawanie obrazu do zadania z URL
    # ---------------------------------------------
    def add_image_from_url(self):
        selected_item = self.task_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Brak wyboru", "Wybierz zadanie.")
            return

        task_index = self.task_list.row(selected_item)
        task = self.current_project.tasks[task_index]

        url, ok = QInputDialog.getText(self, "Dodaj obraz z URL", "Wprowadź URL obrazu:")
        if ok and url:
            self.download_and_add_image(url, task.images)

    # ---------------------------------------------
    #    Pobieranie obrazu z URL i dodawanie
    # ---------------------------------------------
    def download_and_add_image(self, url, image_list):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                image_data = response.content
                image_name = os.path.basename(url)
                save_path = os.path.join(os.getcwd(), image_name)
                with open(save_path, 'wb') as f:
                    f.write(image_data)
                image_list.append(save_path)
                QMessageBox.information(self, "Sukces", "Obraz został pobrany i dodany.")
            else:
                QMessageBox.warning(self, "Błąd", "Nie udało się pobrać obrazu z podanego URL.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas pobierania obrazu: {e}")

    # ---------------------------------------------
    #         Wyszukiwanie zadań
    # ---------------------------------------------
    def search_tasks(self, text):
        if not self.current_project:
            return

        filtered_tasks = [
            task for task in self.current_project.tasks
            if text.lower() in task.title.lower()
            or text.lower() in task.description.lower()
            or any(text.lower() in tag.lower() for tag in task.tags)
        ]

        self.task_list.clear()
        for task in filtered_tasks:
            item = QListWidgetItem(f"{task.title} ({task.status})")
            item.setData(Qt.ItemDataRole.UserRole, task)
            item.setFont(QFont('Arial', 12))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.task_list.addItem(item)

    # ---------------------------------------------
    #         Sortowanie zadań
    # ---------------------------------------------
    def sort_tasks(self, criterion):
        if not self.current_project:
            return

        if criterion == 'Priorytet':
            priority_order = {'Niski': 1, 'Średni': 2, 'Wysoki': 3}
            self.current_project.tasks.sort(key=lambda task: priority_order.get(task.priority, 0))
        elif criterion == 'Status':
            status_order = {'Do zrobienia': 1, 'W trakcie': 2, 'Zakończone': 3}
            self.current_project.tasks.sort(key=lambda task: status_order.get(task.status, 0))
        elif criterion == 'Data':
            self.current_project.tasks.sort(key=lambda task: task.due_date)
        self.refresh_task_list()

    # ---------------------------------------------
    #      Wyświetlanie zadań na wybraną datę
    # ---------------------------------------------
    def show_tasks_on_date(self):
        if not self.current_project:
            return

        selected_date = self.calendar.selectedDate()
        tasks_on_date = [
            task for task in self.current_project.tasks
            if task.due_date.date() == selected_date
        ]

        self.task_list.clear()
        for task in tasks_on_date:
            item = QListWidgetItem(f"{task.title} ({task.status})")
            item.setData(Qt.ItemDataRole.UserRole, task)
            item.setFont(QFont('Arial', 12))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.task_list.addItem(item)

    # ---------------------------------------------
    #          Ustawienie powiadomień
    # ---------------------------------------------
    def setup_notifications(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_deadlines)
        self.timer.start(3600000)  # Sprawdzaj co godzinę

    # ---------------------------------------------
    #            Sprawdzanie terminów
    # ---------------------------------------------
    def check_deadlines(self):
        for project in self.projects:
            for task in project.tasks:
                if task.due_date <= QDateTime.currentDateTime().addSecs(86400) and task.status != 'Zakończone':
                    QMessageBox.warning(self, "Nadchodzący termin", f"Zadanie '{task.title}' w projekcie '{project.name}' ma termin w ciągu 24 godzin.")

    # ---------------------------------------------
    #        Aktualizacja postępu projektu
    # ---------------------------------------------
    def update_project_progress(self):
        if not self.current_project:
            self.project_progress_bar.setValue(0)
            return

        total_tasks = len(self.current_project.tasks)
        if total_tasks == 0:
            self.project_progress_bar.setValue(0)
            return

        completed_tasks = len([task for task in self.current_project.tasks if task.status == 'Zakończone'])
        progress = int((completed_tasks / total_tasks) * 100)
        self.project_progress_bar.setValue(progress)

    # ---------------------------------------------
    #          Edycja wybranego zadania
    # ---------------------------------------------
    def edit_task(self):
        selected_item = self.task_list.currentItem()
        if selected_item:
            self.display_task_details(selected_item)
        else:
            QMessageBox.warning(self, "Brak wyboru", "Wybierz zadanie do edycji.")

# ---------------------------------------------
#       Klasa dialogu ustawień
# ---------------------------------------------
class SettingsDialog(QDialog):
    def __init__(self, custom_theme, interface_settings):
        super().__init__()
        self.setWindowTitle("Ustawienia")
        self.resize(500, 500)

        self.custom_theme = custom_theme.copy()
        self.interface_settings = interface_settings.copy()
        self.theme_changed = False

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Zakładki
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Dodanie ikon do zakładek
        theme_icon = QIcon("theme_icon.png")
        interface_icon = QIcon("interface_icon.png")

        # Zakładka motywu
        theme_tab = QWidget()
        theme_layout = QVBoxLayout()
        theme_tab.setLayout(theme_layout)

        # Przyciski do wyboru kolorów
        self.background_color_button = QPushButton("Kolor tła")
        self.background_color_button.clicked.connect(self.choose_background_color)

        self.text_color_button = QPushButton("Kolor tekstu")
        self.text_color_button.clicked.connect(self.choose_text_color)

        self.button_color_button = QPushButton("Kolor przycisków")
        self.button_color_button.clicked.connect(self.choose_button_color)

        self.hover_color_button = QPushButton("Kolor po najechaniu")
        self.hover_color_button.clicked.connect(self.choose_hover_color)

        self.task_item_background_button = QPushButton("Kolor tła elementów")
        self.task_item_background_button.clicked.connect(self.choose_task_item_background_color)

        self.task_item_text_color_button = QPushButton("Kolor tekstu elementów")
        self.task_item_text_color_button.clicked.connect(self.choose_task_item_text_color)

        theme_layout.addWidget(self.background_color_button)
        theme_layout.addWidget(self.text_color_button)
        theme_layout.addWidget(self.button_color_button)
        theme_layout.addWidget(self.hover_color_button)
        theme_layout.addWidget(self.task_item_background_button)
        theme_layout.addWidget(self.task_item_text_color_button)
        theme_layout.addStretch()

        # Zakładka interfejsu
        interface_tab = QWidget()
        interface_layout = QVBoxLayout()
        interface_tab.setLayout(interface_layout)

        self.show_description_checkbox = QCheckBox("Pokaż pole opisu")
        self.show_description_checkbox.setChecked(self.interface_settings['show_description'])

        self.show_notes_checkbox = QCheckBox("Pokaż pole notatek")
        self.show_notes_checkbox.setChecked(self.interface_settings['show_notes'])

        self.show_due_date_checkbox = QCheckBox("Pokaż pole daty")
        self.show_due_date_checkbox.setChecked(self.interface_settings['show_due_date'])

        self.show_tags_checkbox = QCheckBox("Pokaż pole tagów")
        self.show_tags_checkbox.setChecked(self.interface_settings['show_tags'])

        self.show_priority_checkbox = QCheckBox("Pokaż pole priorytetu")
        self.show_priority_checkbox.setChecked(self.interface_settings['show_priority'])

        self.show_status_checkbox = QCheckBox("Pokaż pole statusu")
        self.show_status_checkbox.setChecked(self.interface_settings['show_status'])

        self.show_images_checkbox = QCheckBox("Pokaż przyciski obrazów")
        self.show_images_checkbox.setChecked(self.interface_settings['show_images'])

        self.show_instructions_checkbox = QCheckBox("Pokaż panel instrukcji")
        self.show_instructions_checkbox.setChecked(self.interface_settings['show_instructions'])

        # Nowe checkboxy do ukrywania sekcji
        self.show_projects_section_checkbox = QCheckBox("Pokaż sekcję projektów")
        self.show_projects_section_checkbox.setChecked(self.interface_settings['show_projects_section'])

        self.show_tasks_section_checkbox = QCheckBox("Pokaż sekcję zadań")
        self.show_tasks_section_checkbox.setChecked(self.interface_settings['show_tasks_section'])

        interface_layout.addWidget(self.show_description_checkbox)
        interface_layout.addWidget(self.show_notes_checkbox)
        interface_layout.addWidget(self.show_due_date_checkbox)
        interface_layout.addWidget(self.show_tags_checkbox)
        interface_layout.addWidget(self.show_priority_checkbox)
        interface_layout.addWidget(self.show_status_checkbox)
        interface_layout.addWidget(self.show_images_checkbox)
        interface_layout.addWidget(self.show_instructions_checkbox)
        interface_layout.addWidget(self.show_projects_section_checkbox)
        interface_layout.addWidget(self.show_tasks_section_checkbox)
        interface_layout.addStretch()

        # Dodanie zakładek z ikonami
        tabs.addTab(theme_tab, theme_icon, "Motyw")
        tabs.addTab(interface_tab, interface_icon, "Interfejs")

        # Przyciski akcji
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Zapisz")
        self.save_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.clicked.connect(self.reject)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

        # Stylizacja okna ustawień
        self.setStyleSheet("""
            QDialog {{
                background-color: {bg_color};
            }}
            QPushButton {{
                background-color: {btn_color};
                color: #ffffff;
                border-radius: 5px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QCheckBox {{
                font-size: 14px;
                color: {text_color};
            }}
            QTabWidget::pane {{
                border: 1px solid {btn_color};
            }}
            QTabBar::tab {{
                background: {bg_color};
                color: {text_color};
                padding: 10px;
            }}
            QTabBar::tab:selected {{
                background: {btn_color};
                color: #ffffff;
            }}
        """.format(
            bg_color=self.custom_theme.get('background_color', '#ffe4e1'),
            btn_color=self.custom_theme.get('button_color', '#ff69b4'),
            hover_color=self.custom_theme.get('hover_color', '#ff1493'),
            text_color=self.custom_theme.get('text_color', '#8b0000')
        ))

    def choose_background_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.custom_theme['background_color'] = color.name()
            self.theme_changed = True

    def choose_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.custom_theme['text_color'] = color.name()
            self.theme_changed = True

    def choose_button_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.custom_theme['button_color'] = color.name()
            self.theme_changed = True

    def choose_hover_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.custom_theme['hover_color'] = color.name()
            self.theme_changed = True

    def choose_task_item_background_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.custom_theme['task_item_background'] = color.name()
            self.theme_changed = True

    def choose_task_item_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.custom_theme['task_item_text_color'] = color.name()
            self.theme_changed = True

    def get_custom_theme(self):
        return self.custom_theme

    def get_interface_settings(self):
        return {
            'show_description': self.show_description_checkbox.isChecked(),
            'show_notes': self.show_notes_checkbox.isChecked(),
            'show_due_date': self.show_due_date_checkbox.isChecked(),
            'show_tags': self.show_tags_checkbox.isChecked(),
            'show_priority': self.show_priority_checkbox.isChecked(),
            'show_status': self.show_status_checkbox.isChecked(),
            'show_images': self.show_images_checkbox.isChecked(),
            'show_instructions': self.show_instructions_checkbox.isChecked(),
            'show_projects_section': self.show_projects_section_checkbox.isChecked(),
            'show_tasks_section': self.show_tasks_section_checkbox.isChecked()
        }

# ---------------------------------------------
#       Klasa dialogu zarządzania obrazami
# ---------------------------------------------
# (Pozostaje bez zmian)

# ---------------------------------------------
#          Uruchomienie aplikacji
# ---------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskManagerApp()
    window.show()
    sys.exit(app.exec())
