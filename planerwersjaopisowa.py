# ---------------------------------------------
#            Importowanie bibliotek
# ---------------------------------------------
import sys
import json
import os
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QLabel, QLineEdit,
    QTextEdit, QMessageBox, QDateTimeEdit, QComboBox, QFileDialog,
    QDialog, QGridLayout, QScrollArea, QMenu, QToolBar, QInputDialog,
    QCheckBox
)
from PyQt6.QtCore import Qt, QDateTime, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QAction, QPixmap, QFont

# ---------------------------------------------
#        Klasa reprezentująca zadanie
# ---------------------------------------------
class Task:
    def __init__(self, title, description, due_date, priority, status, images=None):
        # Tutaj przechowujemy informacje o zadaniu
        self.title = title  # Tytuł zadania
        self.description = description  # Opis zadania
        self.due_date = due_date  # Termin wykonania (QDateTime)
        self.priority = priority  # Priorytet ('Niska', 'Średnia', 'Wysoka')
        self.status = status  # Status ('Do zrobienia', 'W trakcie', 'Zakończone')
        self.images = images or []  # Lista obrazów związanych z zadaniem

    def to_dict(self):
        # Konwertujemy zadanie na słownik, aby móc je zapisać w pliku
        return {
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.toString(Qt.DateFormat.ISODate),
            'priority': self.priority,
            'status': self.status,
            'images': self.images
        }

    @staticmethod
    def from_dict(data):
        # Tworzymy zadanie na podstawie słownika (np. przy wczytywaniu z pliku)
        return Task(
            data['title'],
            data['description'],
            QDateTime.fromString(data['due_date'], Qt.DateFormat.ISODate),
            data['priority'],
            data['status'],
            data.get('images', [])
        )

# ---------------------------------------------
#          Główna klasa aplikacji
# ---------------------------------------------
class TaskManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Ustawienia okna głównego
        self.setWindowTitle("Mój Piękny Menedżer Zadań")
        self.setWindowIcon(QIcon("icon.png"))  # Możesz zmienić ścieżkę do ikony
        self.resize(1200, 800)

        # Inicjalizacja danych
        self.tasks = []  # Lista zadań
        self.background_images = []  # Lista obrazów planera
        self.themes = self.load_themes()  # Dostępne motywy
        self.current_theme = 'Pastel Pink'  # Domyślny motyw

        # Inicjalizacja interfejsu użytkownika
        self.initUI()

    # ---------------------------------------------
    #       Inicjalizacja interfejsu użytkownika
    # ---------------------------------------------
    def initUI(self):
        # Ustawiamy styl aplikacji według wybranego motywu
        self.apply_theme(self.current_theme)

        # Tworzymy główne elementy interfejsu
        self.create_widgets()
        self.create_menu()
        self.create_toolbar()
        self.create_layouts()

    # ---------------------------------------------
    #            Tworzenie widgetów
    # ---------------------------------------------
    def create_widgets(self):
        # Lista zadań
        self.task_list = QListWidget()
        self.task_list.itemClicked.connect(self.display_task_details)
        self.task_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(self.show_task_context_menu)
        self.task_list.setDragDropMode(QListWidget.DragDropMode.NoDragDrop)

        # Pola do edycji szczegółów zadania
        self.title_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setAcceptDrops(False)  # Wyłączamy przeciąganie do pola tekstowego
        self.due_date_edit = QDateTimeEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDateTime(QDateTime.currentDateTime())

        # ComboBoxy dla priorytetu i statusu
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(['Niska', 'Średnia', 'Wysoka'])

        self.status_combo = QComboBox()
        self.status_combo.addItems(['Do zrobienia', 'W trakcie', 'Zakończone'])

        # Przyciski akcji
        self.save_task_button = QPushButton("Zapisz zadanie")
        self.save_task_button.clicked.connect(self.save_task)

        # Przyciski dodawania obrazów do zadania
        self.add_image_from_disk_button = QPushButton("Dodaj obraz z dysku")
        self.add_image_from_disk_button.clicked.connect(self.add_image_from_disk)

        self.add_image_from_url_button = QPushButton("Dodaj obraz z URL")
        self.add_image_from_url_button.clicked.connect(self.add_image_from_url)

        # Panel instrukcji
        self.instructions_panel = QTextEdit()
        self.instructions_panel.setReadOnly(True)
        self.instructions_panel.setText(self.load_instructions())
        self.instructions_panel.setVisible(False)

        self.toggle_instructions_button = QPushButton("Pokaż/Ukryj instrukcje")
        self.toggle_instructions_button.clicked.connect(self.toggle_instructions)

        # Dropdown do zmiany motywu
        self.theme_dropdown = QComboBox()
        self.theme_dropdown.addItems(list(self.themes.keys()))
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
        save_action.triggered.connect(self.save_tasks)

        load_action = QAction(QIcon("load.png"), "Wczytaj", self)
        load_action.triggered.connect(self.load_tasks)

        exit_action = QAction(QIcon("exit.png"), "Wyjdź", self)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(save_action)
        file_menu.addAction(load_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # Menu "Widok"
        view_menu = menu_bar.addMenu("Widok")

        manage_bg_images_action = QAction("Zarządzaj obrazami planera", self)
        manage_bg_images_action.triggered.connect(self.manage_background_images)

        view_menu.addAction(manage_bg_images_action)

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

        add_task_action = QAction(QIcon("add_task.png"), "Nowe zadanie", self)
        add_task_action.triggered.connect(self.clear_task_details)

        delete_task_action = QAction(QIcon("delete_task.png"), "Usuń zadanie", self)
        delete_task_action.triggered.connect(self.delete_task)

        toolbar.addAction(add_task_action)
        toolbar.addAction(delete_task_action)

        # Dodajemy dropdown do zmiany motywu na pasku narzędzi
        toolbar.addWidget(QLabel("  Motyw: "))
        toolbar.addWidget(self.theme_dropdown)

    # ---------------------------------------------
    #        Ustawienie układów (layoutów)
    # ---------------------------------------------
    def create_layouts(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # Layout dla listy zadań
        list_layout = QVBoxLayout()
        list_label = QLabel("Lista zadań")
        list_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        list_layout.addWidget(list_label)
        list_layout.addWidget(self.task_list)

        # Layout dla szczegółów zadania
        detail_layout = QVBoxLayout()
        detail_label = QLabel("Szczegóły zadania")
        detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail_layout.addWidget(detail_label)
        detail_layout.addWidget(QLabel("Tytuł"))
        detail_layout.addWidget(self.title_edit)
        detail_layout.addWidget(QLabel("Opis"))
        detail_layout.addWidget(self.description_edit)
        detail_layout.addWidget(QLabel("Termin"))
        detail_layout.addWidget(self.due_date_edit)
        detail_layout.addWidget(QLabel("Priorytet"))
        detail_layout.addWidget(self.priority_combo)
        detail_layout.addWidget(QLabel("Status"))
        detail_layout.addWidget(self.status_combo)

        # Przyciski dodawania obrazów do zadania
        image_buttons_layout = QHBoxLayout()
        image_buttons_layout.addWidget(self.add_image_from_disk_button)
        image_buttons_layout.addWidget(self.add_image_from_url_button)
        detail_layout.addLayout(image_buttons_layout)

        detail_layout.addWidget(self.save_task_button)

        # Panel instrukcji
        detail_layout.addWidget(self.toggle_instructions_button)
        detail_layout.addWidget(self.instructions_panel)

        # Layout dla galerii obrazów planera
        self.bg_image_area = QScrollArea()
        self.bg_image_area.setWidgetResizable(True)
        self.bg_image_container = QWidget()
        self.bg_image_layout = QGridLayout()
        self.bg_image_container.setLayout(self.bg_image_layout)
        self.bg_image_area.setWidget(self.bg_image_container)

        # Przycisk dodawania obrazów do planera
        self.add_bg_image_button = QPushButton("Dodaj obraz do planera")
        self.add_bg_image_button.clicked.connect(self.add_image_to_planner)

        # Dodajemy przycisk do layoutu galerii
        bg_layout = QVBoxLayout()
        bg_layout.addWidget(self.bg_image_area)
        bg_layout.addWidget(self.add_bg_image_button)

        # Dodajemy wszystkie layouty do głównego układu
        main_layout.addLayout(list_layout, 30)
        main_layout.addLayout(detail_layout, 40)
        main_layout.addLayout(bg_layout, 30)

        # Umożliwiamy przeciąganie i upuszczanie obrazów
        self.setAcceptDrops(True)

    # ---------------------------------------------
    #         Załadowanie instrukcji
    # ---------------------------------------------
    def load_instructions(self):
        instructions = """
**Instrukcje użytkowania:**

- **Dodawanie nowego zadania:**
  1. Kliknij na ikonę "Nowe zadanie" na pasku narzędzi.
  2. Wprowadź szczegóły zadania w polach po prawej stronie.
  3. Kliknij "Zapisz zadanie".

- **Usuwanie zadania:**
  1. Wybierz zadanie z listy.
  2. Kliknij ikonę "Usuń zadanie" na pasku narzędzi lub wybierz "Usuń zadanie" z menu kontekstowego (prawy przycisk myszy na zadaniu).

- **Dodawanie obrazów do zadania:**
  1. Wybierz zadanie z listy.
  2. Użyj przycisków "Dodaj obraz z dysku" lub "Dodaj obraz z URL" w sekcji szczegółów zadania.

- **Zarządzanie obrazami zadania:**
  - Kliknij prawym przyciskiem myszy na zadaniu i wybierz "Zarządzaj obrazami zadania".
  - W otwartym oknie możesz dodawać lub usuwać obrazy przypisane do zadania.

- **Dodawanie obrazów do planera:**
  - Użyj przycisku "Dodaj obraz do planera" poniżej galerii obrazów.
  - Możesz również przeciągnąć i upuścić obraz bezpośrednio do aplikacji.

- **Zarządzanie obrazami planera:**
  - Wybierz "Widok" → "Zarządzaj obrazami planera" z menu głównego.
  - W otwartym oknie możesz dodawać lub usuwać obrazy planera.

- **Otwieranie obrazów w pełnym rozmiarze:**
  - Kliknij na miniaturę obrazu w galerii, aby otworzyć go w pełnym rozmiarze.

- **Zmiana motywu:**
  - Użyj dropdownu "Motyw" na pasku narzędzi, aby wybrać preferowany motyw.

- **Pokazywanie/Ukrywanie instrukcji:**
  - Kliknij przycisk "Pokaż/Ukryj instrukcje" w sekcji szczegółów zadania lub wybierz "Pomoc" → "Instrukcje" z menu głównego.

Miłego korzystania z aplikacji!
"""
        return instructions

    # ---------------------------------------------
    #          Pokazywanie instrukcji
    # ---------------------------------------------
    def toggle_instructions(self):
        # Pokazujemy lub ukrywamy panel instrukcji
        visible = self.instructions_panel.isVisible()
        self.instructions_panel.setVisible(not visible)

    # ---------------------------------------------
    #              Załadowanie motywów
    # ---------------------------------------------
    def load_themes(self):
        # Definiujemy dostępne motywy aplikacji
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
        }
        return themes

    # ---------------------------------------------
    #           Zastosowanie wybranego motywu
    # ---------------------------------------------
    def apply_theme(self, theme_name):
        theme = self.themes.get(theme_name, self.themes['Pastel Pink'])
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

    # ---------------------------------------------
    #       Zmiana motywu z dropdownu
    # ---------------------------------------------
    def change_theme_dropdown(self, theme_name):
        # Zmieniamy aktualny motyw
        self.current_theme = theme_name
        self.apply_theme(theme_name)

    # ---------------------------------------------
    #            Zapisanie zadania
    # ---------------------------------------------
    def save_task(self):
        title = self.title_edit.text()
        if not title:
            QMessageBox.warning(self, "Brak tytułu", "Proszę podać tytuł zadania.")
            return

        selected_item = self.task_list.currentItem()
        if selected_item:
            # Aktualizujemy istniejące zadanie
            index = self.task_list.row(selected_item)
            task = self.tasks[index]
        else:
            # Tworzymy nowe zadanie
            task = Task("", "", QDateTime.currentDateTime(), "", "")
            self.tasks.append(task)

        # Ustawiamy wartości zadania
        task.title = title
        task.description = self.description_edit.toPlainText()
        task.due_date = self.due_date_edit.dateTime()
        task.priority = self.priority_combo.currentText()
        task.status = self.status_combo.currentText()

        # Odświeżamy listę zadań
        self.refresh_task_list()
        self.clear_task_details()

    # ---------------------------------------------
    #            Usunięcie zadania
    # ---------------------------------------------
    def delete_task(self):
        selected_item = self.task_list.currentItem()
        if selected_item:
            index = self.task_list.row(selected_item)
            del self.tasks[index]
            self.refresh_task_list()
            self.clear_task_details()
        else:
            QMessageBox.warning(self, "Brak wyboru", "Proszę wybrać zadanie do usunięcia.")

    # ---------------------------------------------
    #          Odświeżenie listy zadań
    # ---------------------------------------------
    def refresh_task_list(self):
        self.task_list.clear()
        for task in self.tasks:
            item = QListWidgetItem(f"{task.title} ({task.status})")
            item.setData(Qt.ItemDataRole.UserRole, task)
            item.setFont(QFont('Arial', 12))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.task_list.addItem(item)

    # ---------------------------------------------
    #    Wyświetlenie szczegółów wybranego zadania
    # ---------------------------------------------
    def display_task_details(self, item):
        index = self.task_list.row(item)
        task = self.tasks[index]

        self.title_edit.setText(task.title)
        self.description_edit.setPlainText(task.description)
        self.due_date_edit.setDateTime(task.due_date)
        self.priority_combo.setCurrentText(task.priority)
        self.status_combo.setCurrentText(task.status)

    # ---------------------------------------------
    #       Wyczyść pola szczegółów zadania
    # ---------------------------------------------
    def clear_task_details(self):
        self.task_list.clearSelection()
        self.title_edit.clear()
        self.description_edit.clear()
        self.due_date_edit.setDateTime(QDateTime.currentDateTime())
        self.priority_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)

    # ---------------------------------------------
    #          Zapisanie zadań do pliku
    # ---------------------------------------------
    def save_tasks(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Zapisz zadania", "", "Pliki JSON (*.json)", options=options
        )
        if file_name:
            data = {
                'tasks': [task.to_dict() for task in self.tasks],
                'background_images': self.background_images,
                'current_theme': self.current_theme
            }
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                QMessageBox.information(self, "Sukces", "Zadania zostały zapisane.")
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać zadań: {e}")

    # ---------------------------------------------
    #          Wczytanie zadań z pliku
    # ---------------------------------------------
    def load_tasks(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Wczytaj zadania", "", "Pliki JSON (*.json)", options=options
        )
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.tasks = [Task.from_dict(task_data) for task_data in data.get('tasks', [])]
                self.background_images = data.get('background_images', [])
                self.current_theme = data.get('current_theme', self.current_theme)
                self.apply_theme(self.current_theme)
                self.theme_dropdown.setCurrentText(self.current_theme)
                self.refresh_task_list()
                self.refresh_background_images()
                QMessageBox.information(self, "Sukces", "Zadania zostały wczytane.")
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nie udało się wczytać zadań: {e}")

    # ---------------------------------------------
    #    Wyświetlenie menu kontekstowego zadania
    # ---------------------------------------------
    def show_task_context_menu(self, position):
        menu = QMenu()
        manage_images_action = QAction("Zarządzaj obrazami zadania", self)
        manage_images_action.triggered.connect(self.manage_task_images)

        delete_task_action = QAction("Usuń zadanie", self)
        delete_task_action.triggered.connect(self.delete_task)

        menu.addAction(manage_images_action)
        menu.addAction(delete_task_action)
        menu.exec(self.task_list.viewport().mapToGlobal(position))

    # ---------------------------------------------
    #      Zarządzanie obrazami zadania
    # ---------------------------------------------
    def manage_task_images(self):
        selected_item = self.task_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Brak wyboru", "Proszę wybrać zadanie.")
            return

        index = self.task_list.row(selected_item)
        task = self.tasks[index]

        dialog = ImageManagerDialog(task.images, "Obrazy zadania")
        dialog.exec()

    # ---------------------------------------------
    #      Zarządzanie obrazami planera
    # ---------------------------------------------
    def manage_background_images(self):
        dialog = ImageManagerDialog(self.background_images, "Obrazy planera", refresh_callback=self.refresh_background_images)
        dialog.exec()

    # ---------------------------------------------
    #  Odświeżenie galerii obrazów planera
    # ---------------------------------------------
    def refresh_background_images(self):
        # Usuwamy stare obrazki
        for i in reversed(range(self.bg_image_layout.count())):
            widget = self.bg_image_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        col_count = 3  # Liczba kolumn w siatce
        row = 0
        col = 0

        for image_path in self.background_images:
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                label = ClickableLabel(image_path)
                label.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio))
                label.clicked.connect(self.open_full_image)
                self.bg_image_layout.addWidget(label, row, col)
                col += 1
                if col >= col_count:
                    col = 0
                    row += 1

    # ---------------------------------------------
    #     Obsługa przeciągania plików do aplikacji
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
    #    Dodanie obrazu do zadania z dysku
    # ---------------------------------------------
    def add_image_from_disk(self):
        selected_item = self.task_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Brak wyboru", "Proszę wybrać zadanie.")
            return

        task_index = self.task_list.row(selected_item)
        task = self.tasks[task_index]

        file_dialog = QFileDialog()
        file_names, _ = file_dialog.getOpenFileNames(
            self, "Wybierz obrazy", "", "Obrazy (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_names:
            task.images.extend(file_names)
            QMessageBox.information(self, "Sukces", "Obrazy zostały dodane do zadania.")

    # ---------------------------------------------
    #     Dodanie obrazu do zadania z URL
    # ---------------------------------------------
    def add_image_from_url(self):
        selected_item = self.task_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Brak wyboru", "Proszę wybrać zadanie.")
            return

        task_index = self.task_list.row(selected_item)
        task = self.tasks[task_index]

        url, ok = QInputDialog.getText(self, "Dodaj obraz z URL", "Podaj URL obrazu:")
        if ok and url:
            self.download_and_add_image(url, task.images)

    # ---------------------------------------------
    #       Dodanie obrazu do planera
    # ---------------------------------------------
    def add_image_to_planner(self):
        options = ["Dodaj z dysku", "Dodaj z URL"]
        choice, ok = QInputDialog.getItem(self, "Dodaj obraz do planera", "Wybierz źródło obrazu:", options, 0, False)
        if ok and choice:
            if choice == "Dodaj z dysku":
                file_dialog = QFileDialog()
                file_names, _ = file_dialog.getOpenFileNames(
                    self, "Wybierz obrazy", "", "Obrazy (*.png *.jpg *.jpeg *.bmp *.gif)"
                )
                if file_names:
                    self.background_images.extend(file_names)
                    self.refresh_background_images()
            elif choice == "Dodaj z URL":
                url, ok = QInputDialog.getText(self, "Dodaj obraz z URL", "Podaj URL obrazu:")
                if ok and url:
                    self.download_and_add_image(url, self.background_images)

    # ---------------------------------------------
    #      Pobranie obrazu z URL i dodanie
    # ---------------------------------------------
    def download_and_add_image(self, url, image_list):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # Zapisujemy obraz w katalogu lokalnym
                image_data = response.content
                image_name = os.path.basename(url)
                save_path = os.path.join(os.getcwd(), image_name)
                with open(save_path, 'wb') as f:
                    f.write(image_data)
                image_list.append(save_path)
                self.refresh_background_images()
                QMessageBox.information(self, "Sukces", "Obraz został pobrany i dodany.")
            else:
                QMessageBox.warning(self, "Błąd", "Nie udało się pobrać obrazu z podanego URL.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas pobierania obrazu: {e}")

    # ---------------------------------------------
    #         Otworzenie obrazu w pełnym rozmiarze
    # ---------------------------------------------
    def open_full_image(self, image_path):
        dialog = ImageViewerDialog(image_path)
        dialog.exec()

# ---------------------------------------------
#       Klasa dialogowa do zarządzania obrazami
# ---------------------------------------------
class ImageManagerDialog(QDialog):
    def __init__(self, image_list, title, refresh_callback=None):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(600, 400)

        self.image_list = image_list
        self.refresh_callback = refresh_callback

        self.initUI()

    # ---------------------------------------------
    #   Inicjalizacja interfejsu użytkownika dialogu
    # ---------------------------------------------
    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Siatka obrazów
        self.image_grid = QGridLayout()
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.image_grid)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        self.refresh_image_list()

        # Przyciski akcji
        button_layout = QHBoxLayout()
        add_button = QPushButton("Dodaj obrazy")
        add_button.clicked.connect(self.add_image)
        remove_button = QPushButton("Usuń zaznaczone obrazy")
        remove_button.clicked.connect(self.remove_selected_images)

        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)

        layout.addLayout(button_layout)

    # ---------------------------------------------
    #    Odświeżenie listy obrazów w dialogu
    # ---------------------------------------------
    def refresh_image_list(self):
        # Usuwamy stare widgety
        for i in reversed(range(self.image_grid.count())):
            widget = self.image_grid.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        row = 0
        col = 0
        col_count = 3  # Liczba kolumn w siatce
        self.checkboxes = []
        for image_path in self.image_list:
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                label = ClickableLabel(image_path)
                label.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
                label.clicked.connect(self.open_full_image)
                checkbox = QCheckBox()
                self.checkboxes.append((checkbox, image_path))
                container = QVBoxLayout()
                container.addWidget(label)
                container.addWidget(checkbox)
                widget = QWidget()
                widget.setLayout(container)
                self.image_grid.addWidget(widget, row, col)
                col += 1
                if col >= col_count:
                    col = 0
                    row += 1

    # ---------------------------------------------
    #         Dodanie obrazu w dialogu
    # ---------------------------------------------
    def add_image(self):
        options = ["Dodaj z dysku", "Dodaj z URL"]
        choice, ok = QInputDialog.getItem(self, "Dodaj obraz", "Wybierz źródło obrazu:", options, 0, False)
        if ok and choice:
            if choice == "Dodaj z dysku":
                file_dialog = QFileDialog()
                file_names, _ = file_dialog.getOpenFileNames(
                    self, "Wybierz obrazy", "", "Obrazy (*.png *.jpg *.jpeg *.bmp *.gif)"
                )
                if file_names:
                    self.image_list.extend(file_names)
                    self.refresh_image_list()
                    if self.refresh_callback:
                        self.refresh_callback()
            elif choice == "Dodaj z URL":
                url, ok = QInputDialog.getText(self, "Dodaj obraz z URL", "Podaj URL obrazu:")
                if ok and url:
                    self.download_and_add_image(url)

    # ---------------------------------------------
    #      Usunięcie zaznaczonych obrazów
    # ---------------------------------------------
    def remove_selected_images(self):
        for checkbox, image_path in self.checkboxes:
            if checkbox.isChecked():
                self.image_list.remove(image_path)
        self.refresh_image_list()
        if self.refresh_callback:
            self.refresh_callback()

    # ---------------------------------------------
    #    Pobranie obrazu z URL w dialogu
    # ---------------------------------------------
    def download_and_add_image(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                image_data = response.content
                image_name = os.path.basename(url)
                save_path = os.path.join(os.getcwd(), image_name)
                with open(save_path, 'wb') as f:
                    f.write(image_data)
                self.image_list.append(save_path)
                self.refresh_image_list()
                if self.refresh_callback:
                    self.refresh_callback()
                QMessageBox.information(self, "Sukces", "Obraz został pobrany i dodany.")
            else:
                QMessageBox.warning(self, "Błąd", "Nie udało się pobrać obrazu z podanego URL.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas pobierania obrazu: {e}")

    # ---------------------------------------------
    #   Otworzenie obrazu w pełnym rozmiarze
    # ---------------------------------------------
    def open_full_image(self, image_path):
        dialog = ImageViewerDialog(image_path)
        dialog.exec()

# ---------------------------------------------
#        Klasa etykiety z możliwością kliknięcia
# ---------------------------------------------
class ClickableLabel(QLabel):
    clicked = pyqtSignal(str)  # Sygnał emitowany po kliknięciu

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path

    def mousePressEvent(self, event):
        self.clicked.emit(self.image_path)

# ---------------------------------------------
#       Klasa wyświetlająca obraz w dialogu
# ---------------------------------------------
class ImageViewerDialog(QDialog):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Podgląd obrazu")
        self.initUI(image_path)

    def initUI(self, image_path):
        layout = QVBoxLayout()
        self.setLayout(layout)

        pixmap = QPixmap(image_path)
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        max_width = screen_size.width() * 0.8
        max_height = screen_size.height() * 0.8

        pixmap = pixmap.scaled(max_width, max_height, Qt.AspectRatioMode.KeepAspectRatio)

        label = QLabel()
        label.setPixmap(pixmap)
        layout.addWidget(label)

# ---------------------------------------------
#          Uruchomienie aplikacji
# ---------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskManagerApp()
    window.show()
    sys.exit(app.exec())
