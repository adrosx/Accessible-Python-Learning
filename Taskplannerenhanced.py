# ---------------------------------------------
#            Importing Libraries
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
#        Class Representing a Task
# ---------------------------------------------
class Task:
    def __init__(self, title, description, due_date, priority, status, images=None):
        # Here we store task information
        self.title = title  # Task title
        self.description = description  # Task description
        self.due_date = due_date  # Due date (QDateTime)
        self.priority = priority  # Priority ('Low', 'Medium', 'High')
        self.status = status  # Status ('To Do', 'In Progress', 'Completed')
        self.images = images or []  # List of images related to the task

    def to_dict(self):
        # Convert task to a dictionary to save it to a file
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
        # Create a task from a dictionary (e.g., when loading from a file)
        return Task(
            data['title'],
            data['description'],
            QDateTime.fromString(data['due_date'], Qt.DateFormat.ISODate),
            data['priority'],
            data['status'],
            data.get('images', [])
        )

# ---------------------------------------------
#          Main Application Class
# ---------------------------------------------
class TaskManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Main window settings
        self.setWindowTitle("My Beautiful Task Manager")
        self.setWindowIcon(QIcon("icon.png"))  # You can change the icon path
        self.resize(1200, 800)

        # Initialize data
        self.tasks = []  # List of tasks
        self.background_images = []  # List of planner images
        self.themes = self.load_themes()  # Available themes
        self.current_theme = 'Pastel Pink'  # Default theme

        # Initialize user interface
        self.initUI()

    # ---------------------------------------------
    #       Initialize User Interface
    # ---------------------------------------------
    def initUI(self):
        # Set application style based on the selected theme
        self.apply_theme(self.current_theme)

        # Create main UI elements
        self.create_widgets()
        self.create_menu()
        self.create_toolbar()
        self.create_layouts()

    # ---------------------------------------------
    #            Create Widgets
    # ---------------------------------------------
    def create_widgets(self):
        # Task list
        self.task_list = QListWidget()
        self.task_list.itemClicked.connect(self.display_task_details)
        self.task_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(self.show_task_context_menu)
        self.task_list.setDragDropMode(QListWidget.DragDropMode.NoDragDrop)

        # Fields for editing task details
        self.title_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setAcceptDrops(False)  # Disable drag and drop to text field
        self.due_date_edit = QDateTimeEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDateTime(QDateTime.currentDateTime())

        # ComboBoxes for priority and status
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(['Low', 'Medium', 'High'])

        self.status_combo = QComboBox()
        self.status_combo.addItems(['To Do', 'In Progress', 'Completed'])

        # Action buttons
        self.save_task_button = QPushButton("Save Task")
        self.save_task_button.clicked.connect(self.save_task)

        # Buttons to add images to the task
        self.add_image_from_disk_button = QPushButton("Add Image from Disk")
        self.add_image_from_disk_button.clicked.connect(self.add_image_from_disk)

        self.add_image_from_url_button = QPushButton("Add Image from URL")
        self.add_image_from_url_button.clicked.connect(self.add_image_from_url)

        # Instructions panel
        self.instructions_panel = QTextEdit()
        self.instructions_panel.setReadOnly(True)
        self.instructions_panel.setText(self.load_instructions())
        self.instructions_panel.setVisible(False)

        self.toggle_instructions_button = QPushButton("Show/Hide Instructions")
        self.toggle_instructions_button.clicked.connect(self.toggle_instructions)

        # Dropdown to change theme
        self.theme_dropdown = QComboBox()
        self.theme_dropdown.addItems(list(self.themes.keys()))
        self.theme_dropdown.setCurrentText(self.current_theme)
        self.theme_dropdown.currentTextChanged.connect(self.change_theme_dropdown)

    # ---------------------------------------------
    #               Create Menu
    # ---------------------------------------------
    def create_menu(self):
        menu_bar = self.menuBar()

        # "File" Menu
        file_menu = menu_bar.addMenu("File")

        save_action = QAction(QIcon("save.png"), "Save", self)
        save_action.triggered.connect(self.save_tasks)

        load_action = QAction(QIcon("load.png"), "Load", self)
        load_action.triggered.connect(self.load_tasks)

        exit_action = QAction(QIcon("exit.png"), "Exit", self)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(save_action)
        file_menu.addAction(load_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # "View" Menu
        view_menu = menu_bar.addMenu("View")

        manage_bg_images_action = QAction("Manage Planner Images", self)
        manage_bg_images_action.triggered.connect(self.manage_background_images)

        view_menu.addAction(manage_bg_images_action)

        # "Help" Menu
        help_menu = menu_bar.addMenu("Help")

        instructions_action = QAction("Instructions", self)
        instructions_action.triggered.connect(self.toggle_instructions)

        help_menu.addAction(instructions_action)

    # ---------------------------------------------
    #          Create Toolbar
    # ---------------------------------------------
    def create_toolbar(self):
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        add_task_action = QAction(QIcon("add_task.png"), "New Task", self)
        add_task_action.triggered.connect(self.clear_task_details)

        delete_task_action = QAction(QIcon("delete_task.png"), "Delete Task", self)
        delete_task_action.triggered.connect(self.delete_task)

        toolbar.addAction(add_task_action)
        toolbar.addAction(delete_task_action)

        # Add theme dropdown to the toolbar
        toolbar.addWidget(QLabel("  Theme: "))
        toolbar.addWidget(self.theme_dropdown)

    # ---------------------------------------------
    #        Set Up Layouts
    # ---------------------------------------------
    def create_layouts(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # Layout for the task list
        list_layout = QVBoxLayout()
        list_label = QLabel("Task List")
        list_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        list_layout.addWidget(list_label)
        list_layout.addWidget(self.task_list)

        # Layout for task details
        detail_layout = QVBoxLayout()
        detail_label = QLabel("Task Details")
        detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail_layout.addWidget(detail_label)
        detail_layout.addWidget(QLabel("Title"))
        detail_layout.addWidget(self.title_edit)
        detail_layout.addWidget(QLabel("Description"))
        detail_layout.addWidget(self.description_edit)
        detail_layout.addWidget(QLabel("Due Date"))
        detail_layout.addWidget(self.due_date_edit)
        detail_layout.addWidget(QLabel("Priority"))
        detail_layout.addWidget(self.priority_combo)
        detail_layout.addWidget(QLabel("Status"))
        detail_layout.addWidget(self.status_combo)

        # Buttons to add images to the task
        image_buttons_layout = QHBoxLayout()
        image_buttons_layout.addWidget(self.add_image_from_disk_button)
        image_buttons_layout.addWidget(self.add_image_from_url_button)
        detail_layout.addLayout(image_buttons_layout)

        detail_layout.addWidget(self.save_task_button)

        # Instructions panel
        detail_layout.addWidget(self.toggle_instructions_button)
        detail_layout.addWidget(self.instructions_panel)

        # Layout for planner image gallery
        self.bg_image_area = QScrollArea()
        self.bg_image_area.setWidgetResizable(True)
        self.bg_image_container = QWidget()
        self.bg_image_layout = QGridLayout()
        self.bg_image_container.setLayout(self.bg_image_layout)
        self.bg_image_area.setWidget(self.bg_image_container)

        # Button to add images to the planner
        self.add_bg_image_button = QPushButton("Add Image to Planner")
        self.add_bg_image_button.clicked.connect(self.add_image_to_planner)

        # Add button to the gallery layout
        bg_layout = QVBoxLayout()
        bg_layout.addWidget(self.bg_image_area)
        bg_layout.addWidget(self.add_bg_image_button)

        # Add all layouts to the main layout
        main_layout.addLayout(list_layout, 30)
        main_layout.addLayout(detail_layout, 40)
        main_layout.addLayout(bg_layout, 30)

        # Enable drag and drop of images
        self.setAcceptDrops(True)

    # ---------------------------------------------
    #         Load Instructions
    # ---------------------------------------------
    def load_instructions(self):
        instructions = """
**User Instructions:**

- **Adding a New Task:**
  1. Click the "New Task" icon on the toolbar.
  2. Enter the task details in the fields on the right.
  3. Click "Save Task".

- **Deleting a Task:**
  1. Select a task from the list.
  2. Click the "Delete Task" icon on the toolbar or select "Delete Task" from the context menu (right-click on the task).

- **Adding Images to a Task:**
  1. Select a task from the list.
  2. Use the "Add Image from Disk" or "Add Image from URL" buttons in the task details section.

- **Managing Task Images:**
  - Right-click on a task and select "Manage Task Images".
  - In the opened window, you can add or remove images assigned to the task.

- **Adding Images to the Planner:**
  - Use the "Add Image to Planner" button below the image gallery.
  - You can also drag and drop an image directly into the application.

- **Managing Planner Images:**
  - Select "View" → "Manage Planner Images" from the main menu.
  - In the opened window, you can add or remove planner images.

- **Opening Images in Full Size:**
  - Click on an image thumbnail in the gallery to open it in full size.

- **Changing the Theme:**
  - Use the "Theme" dropdown on the toolbar to select your preferred theme.

- **Showing/Hiding Instructions:**
  - Click the "Show/Hide Instructions" button in the task details section or select "Help" → "Instructions" from the main menu.

Enjoy using the application!
"""
        return instructions

    # ---------------------------------------------
    #          Show/Hide Instructions
    # ---------------------------------------------
    def toggle_instructions(self):
        # Show or hide the instructions panel
        visible = self.instructions_panel.isVisible()
        self.instructions_panel.setVisible(not visible)

    # ---------------------------------------------
    #              Load Themes
    # ---------------------------------------------
    def load_themes(self):
        # Define available application themes
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
    #           Apply Selected Theme
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
    #       Change Theme from Dropdown
    # ---------------------------------------------
    def change_theme_dropdown(self, theme_name):
        # Change the current theme
        self.current_theme = theme_name
        self.apply_theme(theme_name)

    # ---------------------------------------------
    #            Save Task
    # ---------------------------------------------
    def save_task(self):
        title = self.title_edit.text()
        if not title:
            QMessageBox.warning(self, "No Title", "Please enter a task title.")
            return

        selected_item = self.task_list.currentItem()
        if selected_item:
            # Update existing task
            index = self.task_list.row(selected_item)
            task = self.tasks[index]
        else:
            # Create a new task
            task = Task("", "", QDateTime.currentDateTime(), "", "")
            self.tasks.append(task)

        # Set task values
        task.title = title
        task.description = self.description_edit.toPlainText()
        task.due_date = self.due_date_edit.dateTime()
        task.priority = self.priority_combo.currentText()
        task.status = self.status_combo.currentText()

        # Refresh task list
        self.refresh_task_list()
        self.clear_task_details()

    # ---------------------------------------------
    #            Delete Task
    # ---------------------------------------------
    def delete_task(self):
        selected_item = self.task_list.currentItem()
        if selected_item:
            index = self.task_list.row(selected_item)
            del self.tasks[index]
            self.refresh_task_list()
            self.clear_task_details()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a task to delete.")

    # ---------------------------------------------
    #          Refresh Task List
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
    #    Display Selected Task Details
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
    #       Clear Task Details Fields
    # ---------------------------------------------
    def clear_task_details(self):
        self.task_list.clearSelection()
        self.title_edit.clear()
        self.description_edit.clear()
        self.due_date_edit.setDateTime(QDateTime.currentDateTime())
        self.priority_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)

    # ---------------------------------------------
    #          Save Tasks to File
    # ---------------------------------------------
    def save_tasks(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Tasks", "", "JSON Files (*.json)", options=options
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
                QMessageBox.information(self, "Success", "Tasks have been saved.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save tasks: {e}")

    # ---------------------------------------------
    #          Load Tasks from File
    # ---------------------------------------------
    def load_tasks(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Load Tasks", "", "JSON Files (*.json)", options=options
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
                QMessageBox.information(self, "Success", "Tasks have been loaded.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load tasks: {e}")

    # ---------------------------------------------
    #    Show Task Context Menu
    # ---------------------------------------------
    def show_task_context_menu(self, position):
        menu = QMenu()
        manage_images_action = QAction("Manage Task Images", self)
        manage_images_action.triggered.connect(self.manage_task_images)

        delete_task_action = QAction("Delete Task", self)
        delete_task_action.triggered.connect(self.delete_task)

        menu.addAction(manage_images_action)
        menu.addAction(delete_task_action)
        menu.exec(self.task_list.viewport().mapToGlobal(position))

    # ---------------------------------------------
    #      Manage Task Images
    # ---------------------------------------------
    def manage_task_images(self):
        selected_item = self.task_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a task.")
            return

        index = self.task_list.row(selected_item)
        task = self.tasks[index]

        dialog = ImageManagerDialog(task.images, "Task Images")
        dialog.exec()

    # ---------------------------------------------
    #      Manage Planner Images
    # ---------------------------------------------
    def manage_background_images(self):
        dialog = ImageManagerDialog(self.background_images, "Planner Images", refresh_callback=self.refresh_background_images)
        dialog.exec()

    # ---------------------------------------------
    #  Refresh Planner Image Gallery
    # ---------------------------------------------
    def refresh_background_images(self):
        # Remove old images
        for i in reversed(range(self.bg_image_layout.count())):
            widget = self.bg_image_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        col_count = 3  # Number of columns in the grid
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
    #    Handle Dragging Files into the Application
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
    #    Add Image to Task from Disk
    # ---------------------------------------------
    def add_image_from_disk(self):
        selected_item = self.task_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a task.")
            return

        task_index = self.task_list.row(selected_item)
        task = self.tasks[task_index]

        file_dialog = QFileDialog()
        file_names, _ = file_dialog.getOpenFileNames(
            self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_names:
            task.images.extend(file_names)
            QMessageBox.information(self, "Success", "Images have been added to the task.")

    # ---------------------------------------------
    #     Add Image to Task from URL
    # ---------------------------------------------
    def add_image_from_url(self):
        selected_item = self.task_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a task.")
            return

        task_index = self.task_list.row(selected_item)
        task = self.tasks[task_index]

        url, ok = QInputDialog.getText(self, "Add Image from URL", "Enter image URL:")
        if ok and url:
            self.download_and_add_image(url, task.images)

    # ---------------------------------------------
    #       Add Image to Planner
    # ---------------------------------------------
    def add_image_to_planner(self):
        options = ["Add from Disk", "Add from URL"]
        choice, ok = QInputDialog.getItem(self, "Add Image to Planner", "Select image source:", options, 0, False)
        if ok and choice:
            if choice == "Add from Disk":
                file_dialog = QFileDialog()
                file_names, _ = file_dialog.getOpenFileNames(
                    self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
                )
                if file_names:
                    self.background_images.extend(file_names)
                    self.refresh_background_images()
            elif choice == "Add from URL":
                url, ok = QInputDialog.getText(self, "Add Image from URL", "Enter image URL:")
                if ok and url:
                    self.download_and_add_image(url, self.background_images)

    # ---------------------------------------------
    #      Download Image from URL and Add
    # ---------------------------------------------
    def download_and_add_image(self, url, image_list):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # Save the image to a local directory
                image_data = response.content
                image_name = os.path.basename(url)
                save_path = os.path.join(os.getcwd(), image_name)
                with open(save_path, 'wb') as f:
                    f.write(image_data)
                image_list.append(save_path)
                self.refresh_background_images()
                QMessageBox.information(self, "Success", "Image has been downloaded and added.")
            else:
                QMessageBox.warning(self, "Error", "Failed to download image from the provided URL.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while downloading the image: {e}")

    # ---------------------------------------------
    #         Open Image in Full Size
    # ---------------------------------------------
    def open_full_image(self, image_path):
        dialog = ImageViewerDialog(image_path)
        dialog.exec()

# ---------------------------------------------
#       Dialog Class for Managing Images
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
    #   Initialize User Interface of the Dialog
    # ---------------------------------------------
    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Image grid
        self.image_grid = QGridLayout()
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.image_grid)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        self.refresh_image_list()

        # Action buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Images")
        add_button.clicked.connect(self.add_image)
        remove_button = QPushButton("Remove Selected Images")
        remove_button.clicked.connect(self.remove_selected_images)

        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)

        layout.addLayout(button_layout)

    # ---------------------------------------------
    #    Refresh Image List in the Dialog
    # ---------------------------------------------
    def refresh_image_list(self):
        # Remove old widgets
        for i in reversed(range(self.image_grid.count())):
            widget = self.image_grid.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        row = 0
        col = 0
        col_count = 3  # Number of columns in the grid
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
    #         Add Image in Dialog
    # ---------------------------------------------
    def add_image(self):
        options = ["Add from Disk", "Add from URL"]
        choice, ok = QInputDialog.getItem(self, "Add Image", "Select image source:", options, 0, False)
        if ok and choice:
            if choice == "Add from Disk":
                file_dialog = QFileDialog()
                file_names, _ = file_dialog.getOpenFileNames(
                    self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
                )
                if file_names:
                    self.image_list.extend(file_names)
                    self.refresh_image_list()
                    if self.refresh_callback:
                        self.refresh_callback()
            elif choice == "Add from URL":
                url, ok = QInputDialog.getText(self, "Add Image from URL", "Enter image URL:")
                if ok and url:
                    self.download_and_add_image(url)

    # ---------------------------------------------
    #      Remove Selected Images
    # ---------------------------------------------
    def remove_selected_images(self):
        for checkbox, image_path in self.checkboxes:
            if checkbox.isChecked():
                self.image_list.remove(image_path)
        self.refresh_image_list()
        if self.refresh_callback:
            self.refresh_callback()

    # ---------------------------------------------
    #    Download Image from URL in Dialog
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
                QMessageBox.information(self, "Success", "Image has been downloaded and added.")
            else:
                QMessageBox.warning(self, "Error", "Failed to download image from the provided URL.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while downloading the image: {e}")

    # ---------------------------------------------
    #   Open Image in Full Size
    # ---------------------------------------------
    def open_full_image(self, image_path):
        dialog = ImageViewerDialog(image_path)
        dialog.exec()

# ---------------------------------------------
#        Clickable Label Class
# ---------------------------------------------
class ClickableLabel(QLabel):
    clicked = pyqtSignal(str)  # Signal emitted when clicked

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path

    def mousePressEvent(self, event):
        self.clicked.emit(self.image_path)

# ---------------------------------------------
#       Image Viewer Dialog Class
# ---------------------------------------------
class ImageViewerDialog(QDialog):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Image Preview")
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
#          Run the Application
# ---------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskManagerApp()
    window.show()
    sys.exit(app.exec())
