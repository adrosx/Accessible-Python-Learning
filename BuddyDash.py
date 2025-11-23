#!/usr/bin/env python3
"""
BuddyDash - Project Dashboard for tracking multiple projects
A single-file PyQt6 application with Git integration
"""

#region Imports
import sys
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
import subprocess

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QScrollArea, QFrame, QLineEdit, QTextEdit,
    QComboBox, QProgressBar, QDialog, QFormLayout, QSpinBox,
    QDialogButtonBox, QFileDialog, QMessageBox, QListWidget,
    QListWidgetItem, QCheckBox, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QPoint
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPalette, QColor, QFont

try:
    from git import Repo, InvalidGitRepositoryError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    print("GitPython not available. Git integration disabled.")
#endregion

#region Data Models
class Project:
    """Represents a single project with all its metadata"""

    def __init__(self, name: str, path: str = "", status: str = "Planning",
                 priority: int = 3, progress: int = 0, notes: str = "",
                 todos: List[Dict] = None, created: str = None):
        self.name = name
        self.path = path
        self.status = status  # Active, Paused, Planning, Released
        self.priority = priority  # 1-5, 1 being highest
        self.progress = progress  # 0-100
        self.notes = notes
        self.todos = todos or []
        self.created = created or datetime.now().isoformat()
        self.last_updated = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convert project to dictionary for JSON storage"""
        return {
            'name': self.name,
            'path': self.path,
            'status': self.status,
            'priority': self.priority,
            'progress': self.progress,
            'notes': self.notes,
            'todos': self.todos,
            'created': self.created,
            'last_updated': self.last_updated
        }

    @staticmethod
    def from_dict(data: dict) -> 'Project':
        """Create project from dictionary"""
        return Project(**data)

    def update_timestamp(self):
        """Update the last_updated timestamp"""
        self.last_updated = datetime.now().isoformat()

    def get_git_info(self) -> Dict[str, str]:
        """Get Git information for this project"""
        if not GIT_AVAILABLE or not self.path or not os.path.exists(self.path):
            return {}

        try:
            repo = Repo(self.path)

            # Get current branch
            branch = repo.active_branch.name if not repo.head.is_detached else "DETACHED"

            # Get uncommitted changes count
            changed_files = len(repo.index.diff(None)) + len(repo.index.diff("HEAD"))
            untracked = len(repo.untracked_files)
            uncommitted = changed_files + untracked

            # Get last commit
            last_commit = ""
            if repo.head.is_valid():
                commit = repo.head.commit
                last_commit = f"{commit.hexsha[:7]} - {commit.message.split(chr(10))[0][:50]}"

            return {
                'branch': branch,
                'uncommitted': str(uncommitted),
                'last_commit': last_commit
            }
        except (InvalidGitRepositoryError, Exception) as e:
            return {'error': str(e)}
#endregion

#region Project Storage
class ProjectStorage:
    """Handles saving and loading projects from JSON"""

    def __init__(self, filename: str = "buddydash_projects.json"):
        self.filename = Path.home() / filename

    def save_projects(self, projects: List[Project]):
        """Save all projects to JSON file"""
        data = [p.to_dict() for p in projects]
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=2)

    def load_projects(self) -> List[Project]:
        """Load projects from JSON file"""
        if not self.filename.exists():
            return []

        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
            return [Project.from_dict(p) for p in data]
        except Exception as e:
            print(f"Error loading projects: {e}")
            return []
#endregion

#region Project Card Widget
class ProjectCard(QFrame):
    """Visual card representing a single project"""

    edit_requested = pyqtSignal(object)
    delete_requested = pyqtSignal(object)
    open_folder_requested = pyqtSignal(str)
    open_ide_requested = pyqtSignal(str)

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setup_ui()
        self.update_display()

    def setup_ui(self):
        """Setup the card UI"""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setLineWidth(2)

        layout = QVBoxLayout(self)

        # Header: Name and Priority
        header = QHBoxLayout()
        self.name_label = QLabel(self.project.name)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.name_label.setFont(font)
        header.addWidget(self.name_label)

        self.priority_label = QLabel()
        header.addWidget(self.priority_label)
        header.addStretch()

        layout.addLayout(header)

        # Status and Last Updated
        info_layout = QHBoxLayout()
        self.status_label = QLabel()
        self.status_label.setStyleSheet("padding: 4px 8px; border-radius: 4px;")
        info_layout.addWidget(self.status_label)

        self.last_updated_label = QLabel()
        info_layout.addWidget(self.last_updated_label)
        info_layout.addStretch()

        layout.addLayout(info_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # Git info section
        self.git_label = QLabel()
        self.git_label.setWordWrap(True)
        self.git_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.git_label)

        # Notes preview
        self.notes_label = QLabel()
        self.notes_label.setWordWrap(True)
        self.notes_label.setMaximumHeight(60)
        layout.addWidget(self.notes_label)

        # TODO count
        self.todo_label = QLabel()
        layout.addWidget(self.todo_label)

        # Action buttons
        btn_layout = QHBoxLayout()

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.project))
        btn_layout.addWidget(edit_btn)

        folder_btn = QPushButton("Open Folder")
        folder_btn.clicked.connect(lambda: self.open_folder_requested.emit(self.project.path))
        folder_btn.setEnabled(bool(self.project.path and os.path.exists(self.project.path)))
        btn_layout.addWidget(folder_btn)

        ide_btn = QPushButton("Open in IDE")
        ide_btn.clicked.connect(lambda: self.open_ide_requested.emit(self.project.path))
        ide_btn.setEnabled(bool(self.project.path and os.path.exists(self.project.path)))
        btn_layout.addWidget(ide_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("background-color: #8B0000; color: white;")
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.project))
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)

    def update_display(self):
        """Update all display elements with current project data"""
        # Priority
        priority_symbols = {1: "🔴 High", 2: "🟠 Med-High", 3: "🟡 Medium",
                          4: "🟢 Med-Low", 5: "🔵 Low"}
        self.priority_label.setText(priority_symbols.get(self.project.priority, "❓"))

        # Status with color
        status_colors = {
            "Active": "#28a745",
            "Paused": "#ffc107",
            "Planning": "#17a2b8",
            "Released": "#6f42c1"
        }
        color = status_colors.get(self.project.status, "#6c757d")
        self.status_label.setText(self.project.status)
        self.status_label.setStyleSheet(
            f"background-color: {color}; color: white; padding: 4px 8px; border-radius: 4px;"
        )

        # Last updated
        try:
            last_updated = datetime.fromisoformat(self.project.last_updated)
            time_str = last_updated.strftime("%Y-%m-%d %H:%M")
        except:
            time_str = "Unknown"
        self.last_updated_label.setText(f"Updated: {time_str}")

        # Progress
        self.progress_bar.setValue(self.project.progress)

        # Git info
        git_info = self.project.get_git_info()
        if git_info and 'branch' in git_info:
            git_text = f"Branch: {git_info['branch']} | "
            git_text += f"Uncommitted: {git_info['uncommitted']} | "
            git_text += f"Last: {git_info.get('last_commit', 'N/A')}"
            self.git_label.setText(git_text)
        elif git_info and 'error' in git_info:
            self.git_label.setText(f"Git: Not a repository")
        else:
            self.git_label.setText("Git: Not configured")

        # Notes
        notes_preview = self.project.notes[:100] + "..." if len(self.project.notes) > 100 else self.project.notes
        self.notes_label.setText(notes_preview if notes_preview else "No notes")

        # TODOs
        total_todos = len(self.project.todos)
        completed_todos = sum(1 for t in self.project.todos if t.get('done', False))
        self.todo_label.setText(f"TODOs: {completed_todos}/{total_todos} completed")
#endregion

#region Project Edit Dialog
class ProjectEditDialog(QDialog):
    """Dialog for editing/creating projects"""

    def __init__(self, project: Optional[Project] = None, parent=None):
        super().__init__(parent)
        self.project = project or Project("New Project")
        self.setWindowTitle("Edit Project" if project else "New Project")
        self.setMinimumWidth(600)
        self.setup_ui()

    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)

        # Form layout
        form = QFormLayout()

        # Name
        self.name_edit = QLineEdit(self.project.name)
        form.addRow("Name:", self.name_edit)

        # Path
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit(self.project.path)
        path_layout.addWidget(self.path_edit)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)
        form.addRow("Path:", path_layout)

        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Active", "Paused", "Planning", "Released"])
        self.status_combo.setCurrentText(self.project.status)
        form.addRow("Status:", self.status_combo)

        # Priority
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 5)
        self.priority_spin.setValue(self.project.priority)
        form.addRow("Priority (1=High):", self.priority_spin)

        # Progress
        self.progress_spin = QSpinBox()
        self.progress_spin.setRange(0, 100)
        self.progress_spin.setValue(self.project.progress)
        self.progress_spin.setSuffix("%")
        form.addRow("Progress:", self.progress_spin)

        layout.addLayout(form)

        # Notes
        layout.addWidget(QLabel("Notes:"))
        self.notes_edit = QTextEdit(self.project.notes)
        self.notes_edit.setMaximumHeight(100)
        layout.addWidget(self.notes_edit)

        # TODOs
        layout.addWidget(QLabel("Daily TODOs:"))

        # TODO list
        todo_layout = QHBoxLayout()
        self.todo_list = QListWidget()
        self.update_todo_list()
        todo_layout.addWidget(self.todo_list)

        # TODO buttons
        todo_btn_layout = QVBoxLayout()
        add_todo_btn = QPushButton("Add TODO")
        add_todo_btn.clicked.connect(self.add_todo)
        todo_btn_layout.addWidget(add_todo_btn)

        remove_todo_btn = QPushButton("Remove TODO")
        remove_todo_btn.clicked.connect(self.remove_todo)
        todo_btn_layout.addWidget(remove_todo_btn)

        toggle_todo_btn = QPushButton("Toggle Done")
        toggle_todo_btn.clicked.connect(self.toggle_todo)
        todo_btn_layout.addWidget(toggle_todo_btn)

        todo_btn_layout.addStretch()
        todo_layout.addLayout(todo_btn_layout)

        layout.addLayout(todo_layout)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def browse_path(self):
        """Browse for project path"""
        path = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if path:
            self.path_edit.setText(path)

    def update_todo_list(self):
        """Update the TODO list display"""
        self.todo_list.clear()
        for todo in self.project.todos:
            item = QListWidgetItem(f"{'✓' if todo.get('done') else '☐'} {todo['text']}")
            self.todo_list.addItem(item)

    def add_todo(self):
        """Add a new TODO"""
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "Add TODO", "TODO text:")
        if ok and text:
            self.project.todos.append({'text': text, 'done': False})
            self.update_todo_list()

    def remove_todo(self):
        """Remove selected TODO"""
        current_row = self.todo_list.currentRow()
        if current_row >= 0:
            self.project.todos.pop(current_row)
            self.update_todo_list()

    def toggle_todo(self):
        """Toggle TODO done status"""
        current_row = self.todo_list.currentRow()
        if current_row >= 0:
            todo = self.project.todos[current_row]
            todo['done'] = not todo.get('done', False)
            self.update_todo_list()

    def get_project(self) -> Project:
        """Get the edited project"""
        self.project.name = self.name_edit.text()
        self.project.path = self.path_edit.text()
        self.project.status = self.status_combo.currentText()
        self.project.priority = self.priority_spin.value()
        self.project.progress = self.progress_spin.value()
        self.project.notes = self.notes_edit.toPlainText()
        self.project.update_timestamp()
        return self.project
#endregion

#region Draggable Project List
class DraggableProjectList(QScrollArea):
    """Scrollable area containing draggable project cards"""

    projects_reordered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setAcceptDrops(True)

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.addStretch()
        self.setWidget(self.container)

        self.cards: List[ProjectCard] = []
        self.drag_start_pos = None

    def add_card(self, card: ProjectCard):
        """Add a project card"""
        card.installEventFilter(self)
        self.cards.append(card)
        self.layout.insertWidget(len(self.cards) - 1, card)

    def clear_cards(self):
        """Remove all cards"""
        for card in self.cards:
            card.setParent(None)
            card.deleteLater()
        self.cards.clear()

    def get_projects_order(self) -> List[Project]:
        """Get projects in current display order"""
        return [card.project for card in self.cards]

    def eventFilter(self, obj, event):
        """Handle drag events on cards"""
        if isinstance(obj, ProjectCard):
            if event.type() == event.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.drag_start_pos = event.pos()
            elif event.type() == event.Type.MouseMove:
                if (self.drag_start_pos and
                    (event.pos() - self.drag_start_pos).manhattanLength() > 20):
                    self.start_drag(obj)
                    self.drag_start_pos = None

        return super().eventFilter(obj, event)

    def start_drag(self, card: ProjectCard):
        """Start dragging a card"""
        drag = card.findChild(QWidget)  # Placeholder for drag implementation
        # Simple reordering: move card up or down
        # Full drag-and-drop would require QDrag implementation
        # For simplicity, we'll use button-based reordering

    def move_card_up(self, card: ProjectCard):
        """Move card up in the list"""
        idx = self.cards.index(card)
        if idx > 0:
            self.cards[idx], self.cards[idx-1] = self.cards[idx-1], self.cards[idx]
            self.refresh_layout()
            self.projects_reordered.emit()

    def move_card_down(self, card: ProjectCard):
        """Move card down in the list"""
        idx = self.cards.index(card)
        if idx < len(self.cards) - 1:
            self.cards[idx], self.cards[idx+1] = self.cards[idx+1], self.cards[idx]
            self.refresh_layout()
            self.projects_reordered.emit()

    def refresh_layout(self):
        """Refresh the layout after reordering"""
        for i, card in enumerate(self.cards):
            self.layout.removeWidget(card)
            self.layout.insertWidget(i, card)
#endregion

#region Main Window
class BuddyDashWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("BuddyDash - Project Dashboard")
        self.setGeometry(100, 100, 1200, 800)

        self.storage = ProjectStorage()
        self.projects: List[Project] = []
        self.filtered_projects: List[Project] = []

        self.setup_ui()
        self.apply_dark_theme()
        self.load_projects()
        self.refresh_display()

    def setup_ui(self):
        """Setup main window UI"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Title
        title = QLabel("🎯 BuddyDash")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Toolbar
        toolbar = QHBoxLayout()

        new_btn = QPushButton("➕ New Project")
        new_btn.clicked.connect(self.new_project)
        toolbar.addWidget(new_btn)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_display)
        toolbar.addWidget(refresh_btn)

        export_btn = QPushButton("📄 Export to Markdown")
        export_btn.clicked.connect(self.export_to_markdown)
        toolbar.addWidget(export_btn)

        toolbar.addStretch()

        # Filter by status
        toolbar.addWidget(QLabel("Filter Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Active", "Paused", "Planning", "Released"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        toolbar.addWidget(self.status_filter)

        # Filter by priority
        toolbar.addWidget(QLabel("Priority:"))
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["All", "1-High", "2", "3", "4", "5-Low"])
        self.priority_filter.currentTextChanged.connect(self.apply_filters)
        toolbar.addWidget(self.priority_filter)

        # Search
        toolbar.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search projects...")
        self.search_edit.textChanged.connect(self.apply_filters)
        toolbar.addWidget(self.search_edit)

        layout.addLayout(toolbar)

        # Project list
        self.project_list = DraggableProjectList()
        self.project_list.projects_reordered.connect(self.save_projects)
        layout.addWidget(self.project_list)

        # Status bar
        self.status_bar = self.statusBar()
        self.update_status_bar()

    def apply_dark_theme(self):
        """Apply dark theme to the application"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)

        self.setPalette(palette)

        # Additional stylesheet for better appearance
        self.setStyleSheet("""
            QFrame[frameShape="4"] {
                border: 2px solid #444;
                border-radius: 8px;
                background-color: #2d2d2d;
                margin: 5px;
                padding: 10px;
            }
            QPushButton {
                background-color: #0d6efd;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
            QPushButton:pressed {
                background-color: #0a58ca;
            }
            QProgressBar {
                border: 2px solid #444;
                border-radius: 5px;
                text-align: center;
                background-color: #1a1a1a;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
            QLineEdit, QTextEdit, QSpinBox, QComboBox {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                color: white;
            }
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 4px;
            }
        """)

    def load_projects(self):
        """Load projects from storage"""
        self.projects = self.storage.load_projects()
        self.filtered_projects = self.projects.copy()

    def save_projects(self):
        """Save projects to storage"""
        # Get current order from display
        self.projects = self.project_list.get_projects_order()
        self.storage.save_projects(self.projects)
        self.update_status_bar()

    def refresh_display(self):
        """Refresh the project display"""
        self.project_list.clear_cards()

        for project in self.filtered_projects:
            card = ProjectCard(project)
            card.edit_requested.connect(self.edit_project)
            card.delete_requested.connect(self.delete_project)
            card.open_folder_requested.connect(self.open_folder)
            card.open_ide_requested.connect(self.open_in_ide)
            self.project_list.add_card(card)

        self.update_status_bar()

    def apply_filters(self):
        """Apply status, priority, and search filters"""
        status_filter = self.status_filter.currentText()
        priority_filter = self.priority_filter.currentText()
        search_text = self.search_edit.text().lower()

        self.filtered_projects = []

        for project in self.projects:
            # Status filter
            if status_filter != "All" and project.status != status_filter:
                continue

            # Priority filter
            if priority_filter != "All":
                priority_num = int(priority_filter[0])
                if project.priority != priority_num:
                    continue

            # Search filter
            if search_text:
                if (search_text not in project.name.lower() and
                    search_text not in project.notes.lower()):
                    continue

            self.filtered_projects.append(project)

        self.refresh_display()

    def new_project(self):
        """Create a new project"""
        dialog = ProjectEditDialog(parent=self)
        if dialog.exec():
            project = dialog.get_project()
            self.projects.append(project)
            self.save_projects()
            self.apply_filters()

    def edit_project(self, project: Project):
        """Edit an existing project"""
        dialog = ProjectEditDialog(project, parent=self)
        if dialog.exec():
            updated_project = dialog.get_project()
            # Update in place
            idx = self.projects.index(project)
            self.projects[idx] = updated_project
            self.save_projects()
            self.refresh_display()

    def delete_project(self, project: Project):
        """Delete a project"""
        reply = QMessageBox.question(
            self, "Delete Project",
            f"Are you sure you want to delete '{project.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.projects.remove(project)
            self.save_projects()
            self.apply_filters()

    def open_folder(self, path: str):
        """Open project folder in file explorer"""
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Error", "Project path does not exist!")
            return

        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':
            subprocess.run(['open', path])
        else:
            subprocess.run(['xdg-open', path])

    def open_in_ide(self, path: str):
        """Open project in IDE (VS Code by default)"""
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Error", "Project path does not exist!")
            return

        # Try VS Code first
        try:
            subprocess.run(['code', path], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to opening folder
            self.open_folder(path)

    def export_to_markdown(self):
        """Export all projects to a markdown file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Projects", "buddydash_export.md", "Markdown Files (*.md)"
        )

        if not filename:
            return

        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# BuddyDash Project Export\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write(f"Total Projects: {len(self.projects)}\n\n")

            # Group by status
            statuses = ["Active", "Planning", "Paused", "Released"]
            for status in statuses:
                status_projects = [p for p in self.projects if p.status == status]
                if not status_projects:
                    continue

                f.write(f"## {status} ({len(status_projects)})\n\n")

                for project in status_projects:
                    f.write(f"### {project.name}\n\n")
                    f.write(f"- **Priority**: {project.priority}\n")
                    f.write(f"- **Progress**: {project.progress}%\n")
                    f.write(f"- **Path**: `{project.path}`\n")

                    # Git info
                    git_info = project.get_git_info()
                    if git_info and 'branch' in git_info:
                        f.write(f"- **Git Branch**: {git_info['branch']}\n")
                        f.write(f"- **Uncommitted Changes**: {git_info['uncommitted']}\n")

                    # Notes
                    if project.notes:
                        f.write(f"\n**Notes**:\n{project.notes}\n")

                    # TODOs
                    if project.todos:
                        f.write(f"\n**TODOs**:\n")
                        for todo in project.todos:
                            check = "x" if todo.get('done') else " "
                            f.write(f"- [{check}] {todo['text']}\n")

                    f.write("\n---\n\n")

        QMessageBox.information(self, "Export Complete", f"Projects exported to {filename}")

    def update_status_bar(self):
        """Update status bar with project counts"""
        total = len(self.projects)
        active = sum(1 for p in self.projects if p.status == "Active")
        self.status_bar.showMessage(
            f"Total Projects: {total} | Active: {active} | "
            f"Displayed: {len(self.filtered_projects)}"
        )
#endregion

#region Main Entry Point
def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("BuddyDash")

    # Check for GitPython
    if not GIT_AVAILABLE:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText("GitPython not installed")
        msg.setInformativeText("Git integration will be disabled. Install with: pip install GitPython")
        msg.setWindowTitle("Warning")
        msg.exec()

    window = BuddyDashWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
#endregion
