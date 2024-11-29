# ---------------------------------------------
#            Importowanie bibliotek
# ---------------------------------------------
# Importujemy wszystkie niezbędne moduły i biblioteki, które będą używane w programie.

import sys        # Moduł sys pozwala na interakcję z interpreterem Pythona.
import json       # Moduł json umożliwia kodowanie i dekodowanie danych w formacie JSON.
import os         # Moduł os pozwala na interakcję z systemem operacyjnym.
import requests   # Biblioteka requests umożliwia wysyłanie zapytań HTTP, np. do pobierania obrazów z internetu.

# Importujemy klasy i funkcje z biblioteki PyQt6, które są potrzebne do stworzenia interfejsu graficznego aplikacji.
from PyQt6.QtWidgets import (
    QApplication,       # Podstawowa klasa aplikacji PyQt.
    QMainWindow,        # Główne okno aplikacji.
    QWidget,            # Podstawowy widget PyQt.
    QVBoxLayout,        # Układ pionowy do rozmieszczania widgetów.
    QHBoxLayout,        # Układ poziomy do rozmieszczania widgetów.
    QPushButton,        # Przycisk.
    QListWidget,        # Widget listy.
    QListWidgetItem,    # Pojedynczy element w QListWidget.
    QLabel,             # Etykieta tekstowa.
    QLineEdit,          # Pole do wprowadzania pojedynczej linii tekstu.
    QTextEdit,          # Pole do wprowadzania wielolinijkowego tekstu.
    QMessageBox,        # Okno dialogowe do wyświetlania komunikatów.
    QDateTimeEdit,      # Pole do wyboru daty i czasu.
    QComboBox,          # Pole wyboru z listą rozwijaną.
    QFileDialog,        # Okno dialogowe do otwierania i zapisywania plików.
    QDialog,            # Podstawowe okno dialogowe.
    QGridLayout,        # Układ siatki do rozmieszczania widgetów.
    QScrollArea,        # Obszar przewijania dla widgetów.
    QMenu,              # Menu kontekstowe.
    QToolBar,           # Pasek narzędzi.
    QInputDialog,       # Okno dialogowe do wprowadzania danych przez użytkownika.
    QCheckBox           # Pole wyboru (checkbox).
)

from PyQt6.QtCore import Qt, QDateTime, QSize, pyqtSignal
# Qt: Zawiera różne stałe i enumeracje.
# QDateTime: Klasa do obsługi daty i czasu.
# QSize: Klasa reprezentująca rozmiar.
# pyqtSignal: Służy do tworzenia własnych sygnałów w PyQt.

from PyQt6.QtGui import QIcon, QAction, QPixmap, QFont
# QIcon: Klasa do obsługi ikon.
# QAction: Reprezentuje akcję w interfejsie (np. w menu lub pasku narzędzi).
# QPixmap: Klasa do przechowywania i manipulowania obrazami.
# QFont: Klasa do obsługi czcionek.

# ---------------------------------------------
#        Klasa reprezentująca zadanie
# ---------------------------------------------
class Task:
    def __init__(self, title, description, due_date, priority, status, images=None):
        # Konstruktor klasy Task. Inicjalizuje nowe zadanie z podanymi parametrami.
        self.title = title                # Tytuł zadania (np. "Zrobić zakupy").
        self.description = description    # Opis zadania (np. "Kupić mleko, chleb i masło").
        self.due_date = due_date          # Termin wykonania zadania (obiekt QDateTime).
        self.priority = priority          # Priorytet zadania (np. 'Niska', 'Średnia', 'Wysoka').
        self.status = status              # Status zadania (np. 'Do zrobienia', 'W trakcie', 'Zakończone').
        self.images = images or []        # Lista ścieżek do obrazów związanych z zadaniem. Jeśli nie podano, tworzy pustą listę.

    def to_dict(self):
        # Metoda konwertuje obiekt Task na słownik, aby móc go zapisać w pliku JSON.
        return {
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.toString(Qt.DateFormat.ISODate),  # Konwertujemy QDateTime na string.
            'priority': self.priority,
            'status': self.status,
            'images': self.images
        }

    @staticmethod
    def from_dict(data):
        # Metoda statyczna tworzy obiekt Task na podstawie słownika (np. podczas wczytywania z pliku).
        return Task(
            data['title'],
            data['description'],
            QDateTime.fromString(data['due_date'], Qt.DateFormat.ISODate),  # Konwertujemy string na QDateTime.
            data['priority'],
            data['status'],
            data.get('images', [])
        )

# ---------------------------------------------
#          Główna klasa aplikacji
# ---------------------------------------------
class TaskManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()  # Wywołujemy konstruktor klasy nadrzędnej (QMainWindow).

        # Ustawienia okna głównego aplikacji.
        self.setWindowTitle("Mój Piękny Menedżer Zadań")  # Ustawiamy tytuł okna.
        self.setWindowIcon(QIcon("icon.png"))  # Ustawiamy ikonę okna (jeśli nie masz pliku "icon.png", możesz usunąć tę linię lub zmienić ścieżkę).
        self.resize(1200, 800)  # Ustawiamy początkowy rozmiar okna na 1200x800 pikseli.

        # Inicjalizacja danych aplikacji.
        self.tasks = []  # Lista, w której będziemy przechowywać zadania.
        self.background_images = []  # Lista ścieżek do obrazów planera.
        self.themes = self.load_themes()  # Wczytujemy dostępne motywy.
        self.current_theme = 'Pastel Pink'  # Ustawiamy domyślny motyw aplikacji.

        # Inicjalizacja interfejsu użytkownika.
        self.initUI()  # Wywołujemy metodę inicjującą UI.

    # ---------------------------------------------
    #       Inicjalizacja interfejsu użytkownika
    # ---------------------------------------------
    def initUI(self):
        # Zastosowanie domyślnego motywu.
        self.apply_theme(self.current_theme)

        # Tworzenie głównych elementów interfejsu.
        self.create_widgets()   # Tworzymy widgety (przyciski, pola tekstowe itp.).
        self.create_menu()      # Tworzymy menu aplikacji.
        self.create_toolbar()   # Tworzymy pasek narzędzi.
        self.create_layouts()   # Ustawiamy układ elementów w oknie.

    # ---------------------------------------------
    #            Tworzenie widgetów
    # ---------------------------------------------
    def create_widgets(self):
        # Lista zadań.
        self.task_list = QListWidget()  # Tworzymy widget listy zadań.
        self.task_list.itemClicked.connect(self.display_task_details)  # Po kliknięciu na zadanie wyświetlamy jego szczegóły.
        self.task_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # Ustawiamy własne menu kontekstowe (prawy przycisk myszy).
        self.task_list.customContextMenuRequested.connect(self.show_task_context_menu)  # Łączymy sygnał z metodą obsługi menu kontekstowego.
        self.task_list.setDragDropMode(QListWidget.DragDropMode.NoDragDrop)  # Wyłączamy możliwość przeciągania elementów na liście.

        # Pola do edycji szczegółów zadania.
        self.title_edit = QLineEdit()  # Pole tekstowe do wprowadzania tytułu zadania.
        self.description_edit = QTextEdit()  # Pole tekstowe do wprowadzania opisu zadania.
        self.description_edit.setAcceptDrops(False)  # Wyłączamy możliwość przeciągania plików do pola tekstowego (aby uniknąć przypadkowego wklejenia pliku zamiast tekstu).
        self.due_date_edit = QDateTimeEdit()  # Pole do wyboru daty i czasu.
        self.due_date_edit.setCalendarPopup(True)  # Umożliwiamy wyświetlenie kalendarza po kliknięciu.
        self.due_date_edit.setDateTime(QDateTime.currentDateTime())  # Ustawiamy domyślną datę i czas na bieżący.

        # Pola wyboru priorytetu i statusu.
        self.priority_combo = QComboBox()  # Pole wyboru priorytetu.
        self.priority_combo.addItems(['Niska', 'Średnia', 'Wysoka'])  # Dodajemy opcje priorytetu.

        self.status_combo = QComboBox()  # Pole wyboru statusu.
        self.status_combo.addItems(['Do zrobienia', 'W trakcie', 'Zakończone'])  # Dodajemy opcje statusu.

        # Przyciski akcji.
        self.save_task_button = QPushButton("Zapisz zadanie")  # Przycisk do zapisywania zadania.
        self.save_task_button.clicked.connect(self.save_task)  # Po kliknięciu wywołujemy metodę save_task.

        # Przyciski dodawania obrazów do zadania.
        self.add_image_from_disk_button = QPushButton("Dodaj obraz z dysku")  # Przycisk do dodawania obrazu z dysku.
        self.add_image_from_disk_button.clicked.connect(self.add_image_from_disk)

        self.add_image_from_url_button = QPushButton("Dodaj obraz z URL")  # Przycisk do dodawania obrazu z internetu.
        self.add_image_from_url_button.clicked.connect(self.add_image_from_url)

        # Panel instrukcji.
        self.instructions_panel = QTextEdit()  # Pole tekstowe do wyświetlania instrukcji.
        self.instructions_panel.setReadOnly(True)  # Ustawiamy na tylko do odczytu.
        self.instructions_panel.setText(self.load_instructions())  # Wczytujemy treść instrukcji.
        self.instructions_panel.setVisible(False)  # Ukrywamy panel instrukcji na starcie.

        self.toggle_instructions_button = QPushButton("Pokaż/Ukryj instrukcje")  # Przycisk do pokazywania/ukrywania instrukcji.
        self.toggle_instructions_button.clicked.connect(self.toggle_instructions)

        # Pole wyboru motywu.
        self.theme_dropdown = QComboBox()  # Tworzymy pole wyboru.
        self.theme_dropdown.addItems(list(self.themes.keys()))  # Dodajemy nazwy dostępnych motywów.
        self.theme_dropdown.setCurrentText(self.current_theme)  # Ustawiamy domyślny motyw.
        self.theme_dropdown.currentTextChanged.connect(self.change_theme_dropdown)  # Po zmianie motywu wywołujemy metodę apply_theme.

    # ---------------------------------------------
    #               Tworzenie menu
    # ---------------------------------------------
    def create_menu(self):
        menu_bar = self.menuBar()  # Pobieramy pasek menu.

        # Menu "Plik".
        file_menu = menu_bar.addMenu("Plik")  # Tworzymy menu "Plik".

        # Akcja "Zapisz".
        save_action = QAction(QIcon("save.png"), "Zapisz", self)  # Tworzymy akcję z ikoną.
        save_action.triggered.connect(self.save_tasks)  # Po kliknięciu wywołujemy metodę save_tasks.

        # Akcja "Wczytaj".
        load_action = QAction(QIcon("load.png"), "Wczytaj", self)
        load_action.triggered.connect(self.load_tasks)

        # Akcja "Wyjdź".
        exit_action = QAction(QIcon("exit.png"), "Wyjdź", self)
        exit_action.triggered.connect(self.close)  # Zamykamy aplikację.

        # Dodajemy akcje do menu "Plik".
        file_menu.addAction(save_action)
        file_menu.addAction(load_action)
        file_menu.addSeparator()  # Dodajemy separator.
        file_menu.addAction(exit_action)

        # Menu "Widok".
        view_menu = menu_bar.addMenu("Widok")

        # Akcja "Zarządzaj obrazami planera".
        manage_bg_images_action = QAction("Zarządzaj obrazami planera", self)
        manage_bg_images_action.triggered.connect(self.manage_background_images)

        view_menu.addAction(manage_bg_images_action)

        # Menu "Pomoc".
        help_menu = menu_bar.addMenu("Pomoc")

        # Akcja "Instrukcje".
        instructions_action = QAction("Instrukcje", self)
        instructions_action.triggered.connect(self.toggle_instructions)

        help_menu.addAction(instructions_action)

    # ---------------------------------------------
    #          Tworzenie paska narzędzi
    # ---------------------------------------------
    def create_toolbar(self):
        toolbar = QToolBar()  # Tworzymy pasek narzędzi.
        self.addToolBar(toolbar)  # Dodajemy pasek narzędzi do głównego okna.

        # Akcja "Nowe zadanie".
        add_task_action = QAction(QIcon("add_task.png"), "Nowe zadanie", self)
        add_task_action.triggered.connect(self.clear_task_details)  # Czyścimy pola i przygotowujemy do dodania nowego zadania.

        # Akcja "Usuń zadanie".
        delete_task_action = QAction(QIcon("delete_task.png"), "Usuń zadanie", self)
        delete_task_action.triggered.connect(self.delete_task)  # Usuwamy wybrane zadanie.

        # Dodajemy akcje do paska narzędzi.
        toolbar.addAction(add_task_action)
        toolbar.addAction(delete_task_action)

        # Dodajemy pole wyboru motywu na pasku narzędzi.
        toolbar.addWidget(QLabel("  Motyw: "))
        toolbar.addWidget(self.theme_dropdown)

    # ---------------------------------------------
    #        Ustawienie układów (layoutów)
    # ---------------------------------------------
    def create_layouts(self):
        main_widget = QWidget()  # Tworzymy główny widget.
        self.setCentralWidget(main_widget)  # Ustawiamy go jako centralny widget okna.

        main_layout = QHBoxLayout()  # Główny układ poziomy.
        main_widget.setLayout(main_layout)  # Ustawiamy układ dla głównego widgetu.

        # Layout dla listy zadań.
        list_layout = QVBoxLayout()  # Układ pionowy.
        list_label = QLabel("Lista zadań")  # Etykieta.
        list_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Wyśrodkowanie tekstu.
        list_layout.addWidget(list_label)
        list_layout.addWidget(self.task_list)

        # Layout dla szczegółów zadania.
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

        # Przyciski dodawania obrazów do zadania.
        image_buttons_layout = QHBoxLayout()
        image_buttons_layout.addWidget(self.add_image_from_disk_button)
        image_buttons_layout.addWidget(self.add_image_from_url_button)
        detail_layout.addLayout(image_buttons_layout)

        detail_layout.addWidget(self.save_task_button)

        # Panel instrukcji.
        detail_layout.addWidget(self.toggle_instructions_button)
        detail_layout.addWidget(self.instructions_panel)

        # Layout dla galerii obrazów planera.
        self.bg_image_area = QScrollArea()  # Obszar przewijania.
        self.bg_image_area.setWidgetResizable(True)
        self.bg_image_container = QWidget()
        self.bg_image_layout = QGridLayout()
        self.bg_image_container.setLayout(self.bg_image_layout)
        self.bg_image_area.setWidget(self.bg_image_container)

        # Przycisk dodawania obrazów do planera.
        self.add_bg_image_button = QPushButton("Dodaj obraz do planera")
        self.add_bg_image_button.clicked.connect(self.add_image_to_planner)

        # Układ dla galerii obrazów.
        bg_layout = QVBoxLayout()
        bg_layout.addWidget(self.bg_image_area)
        bg_layout.addWidget(self.add_bg_image_button)

        # Dodajemy layouty do głównego układu.
        main_layout.addLayout(list_layout, 30)   # Lista zadań zajmuje 30% szerokości.
        main_layout.addLayout(detail_layout, 40) # Szczegóły zadania zajmują 40% szerokości.
        main_layout.addLayout(bg_layout, 30)     # Galeria obrazów zajmuje 30% szerokości.

        # Umożliwiamy przeciąganie i upuszczanie plików do aplikacji.
        self.setAcceptDrops(True)

    # ---------------------------------------------
    #         Załadowanie instrukcji
    # ---------------------------------------------
    def load_instructions(self):
        # Wczytujemy instrukcje użytkowania aplikacji.
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
        # Metoda przełącza widoczność panelu instrukcji.
        visible = self.instructions_panel.isVisible()  # Sprawdzamy, czy panel jest widoczny.
        self.instructions_panel.setVisible(not visible)  # Ustawiamy przeciwną wartość.

    # ---------------------------------------------
    #              Załadowanie motywów
    # ---------------------------------------------
    def load_themes(self):
        # Definiujemy dostępne motywy aplikacji.
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
        # Metoda ustawia styl aplikacji zgodnie z wybranym motywem.
        theme = self.themes.get(theme_name, self.themes['Pastel Pink'])  # Pobieramy motyw. Jeśli nie istnieje, używamy domyślnego.
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
        # Metoda zmienia motyw aplikacji po wybraniu z dropdownu.
        self.current_theme = theme_name  # Ustawiamy aktualny motyw.
        self.apply_theme(theme_name)     # Zastosowujemy nowy motyw.

    # ---------------------------------------------
    #            Zapisanie zadania
    # ---------------------------------------------
    def save_task(self):
        # Metoda zapisuje bieżące zadanie (nowe lub edytowane).
        title = self.title_edit.text()  # Pobieramy tytuł z pola tekstowego.
        if not title:
            # Jeśli tytuł jest pusty, wyświetlamy ostrzeżenie.
            QMessageBox.warning(self, "Brak tytułu", "Proszę podać tytuł zadania.")
            return

        selected_item = self.task_list.currentItem()  # Pobieramy aktualnie wybrane zadanie z listy.
        if selected_item:
            # Jeśli edytujemy istniejące zadanie.
            index = self.task_list.row(selected_item)
            task = self.tasks[index]
        else:
            # Jeśli tworzymy nowe zadanie.
            task = Task("", "", QDateTime.currentDateTime(), "", "")
            self.tasks.append(task)

        # Ustawiamy wartości zadania na podstawie wprowadzonych danych.
        task.title = title
        task.description = self.description_edit.toPlainText()
        task.due_date = self.due_date_edit.dateTime()
        task.priority = self.priority_combo.currentText()
        task.status = self.status_combo.currentText()

        # Odświeżamy listę zadań.
        self.refresh_task_list()
        self.clear_task_details()

    # ---------------------------------------------
    #            Usunięcie zadania
    # ---------------------------------------------
    def delete_task(self):
        # Metoda usuwa wybrane zadanie.
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
        # Metoda odświeża wyświetlaną listę zadań.
        self.task_list.clear()
        for task in self.tasks:
            item = QListWidgetItem(f"{task.title} ({task.status})")  # Tworzymy nowy element listy.
            item.setData(Qt.ItemDataRole.UserRole, task)
            item.setFont(QFont('Arial', 12))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.task_list.addItem(item)

    # ---------------------------------------------
    #    Wyświetlenie szczegółów wybranego zadania
    # ---------------------------------------------
    def display_task_details(self, item):
        # Metoda wyświetla szczegóły wybranego zadania w polach edycji.
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
        # Metoda czyści pola edycji zadania, przygotowując do dodania nowego.
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
        # Metoda zapisuje wszystkie zadania do pliku JSON.
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
        # Metoda wczytuje zadania z pliku JSON.
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
        # Metoda wyświetla menu kontekstowe po kliknięciu prawym przyciskiem na zadaniu.
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
        # Metoda otwiera okno dialogowe do zarządzania obrazami przypisanymi do zadania.
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
        # Metoda otwiera okno dialogowe do zarządzania obrazami planera.
        dialog = ImageManagerDialog(self.background_images, "Obrazy planera", refresh_callback=self.refresh_background_images)
        dialog.exec()

    # ---------------------------------------------
    #  Odświeżenie galerii obrazów planera
    # ---------------------------------------------
    def refresh_background_images(self):
        # Metoda odświeża wyświetlaną galerię obrazów planera.
        # Usuwamy stare widgety z layoutu.
        for i in reversed(range(self.bg_image_layout.count())):
            widget = self.bg_image_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        col_count = 3  # Liczba kolumn w siatce.
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
        # Metoda jest wywoływana, gdy plik jest przeciągany nad okno aplikacji.
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        # Metoda jest wywoływana, gdy plik jest upuszczany w oknie aplikacji.
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                self.background_images.append(file_path)
                self.refresh_background_images()

    # ---------------------------------------------
    #    Dodanie obrazu do zadania z dysku
    # ---------------------------------------------
    def add_image_from_disk(self):
        # Metoda dodaje obrazy do zadania z plików na dysku.
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
        # Metoda dodaje obraz do zadania z podanego URL.
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
        # Metoda dodaje obraz do galerii obrazów planera.
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
        # Metoda pobiera obraz z podanego URL i dodaje go do podanej listy obrazów.
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # Jeśli pobieranie się powiodło.
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
        # Metoda otwiera obraz w nowym oknie dialogowym w pełnym rozmiarze.
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

        # Siatka obrazów.
        self.image_grid = QGridLayout()
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.image_grid)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        self.refresh_image_list()

        # Przyciski akcji.
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
        # Usuwamy stare widgety z siatki.
        for i in reversed(range(self.image_grid.count())):
            widget = self.image_grid.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        row = 0
        col = 0
        col_count = 3  # Liczba kolumn w siatce.
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
        # Metoda dodaje obrazy do listy w dialogu.
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
        # Metoda usuwa zaznaczone obrazy z listy.
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
        # Metoda pobiera obraz z URL i dodaje go do listy.
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
        # Metoda otwiera obraz w nowym oknie dialogowym.
        dialog = ImageViewerDialog(image_path)
        dialog.exec()

# ---------------------------------------------
#        Klasa etykiety z możliwością kliknięcia
# ---------------------------------------------
class ClickableLabel(QLabel):
    # Klasa QLabel rozszerzona o możliwość obsługi kliknięć.
    clicked = pyqtSignal(str)  # Definiujemy własny sygnał, który będzie emitowany po kliknięciu.

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path  # Przechowujemy ścieżkę do obrazu.

    def mousePressEvent(self, event):
        # Metoda jest wywoływana po kliknięciu na etykietę.
        self.clicked.emit(self.image_path)  # Emitujemy sygnał z informacją o ścieżce do obrazu.

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
    app = QApplication(sys.argv)  # Tworzymy obiekt aplikacji.
    window = TaskManagerApp()     # Tworzymy główne okno aplikacji.
    window.show()                 # Wyświetlamy okno.
    sys.exit(app.exec())          # Uruchamiamy główną pętlę aplikacji.
