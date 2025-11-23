#!/usr/bin/env python3
"""
BuddyDash - Windows-optimized Project Dashboard
A single-file monolithic WCETL-style desktop app for managing multiple projects.
"""

# ============================================================
# REGION 100: IMPORTS & GLOBAL CONSTANTS
# ============================================================

import sys
import os
import json
import logging
import subprocess
import uuid
from pathlib import Path
from typing import Optional, List, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from enum import Enum
from logging.handlers import RotatingFileHandler

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QScrollArea,
    QDialog, QDialogButtonBox, QFormLayout, QFileDialog,
    QMessageBox, QProgressBar, QCheckBox, QPlainTextEdit,
    QListWidget, QListWidgetItem, QGroupBox, QSplitter, QToolBar,
    QFrame
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QRect, QPoint
)
from PyQt6.QtGui import (
    QPalette, QColor, QFont, QDrag, QPainter, QAction
)

# Try to import GitPython
try:
    import git  # type: ignore
    GIT_AVAILABLE = True
except ImportError:
    git = None
    GIT_AVAILABLE = False

# Constants
DEFAULT_IDE_COMMAND = ["code"]  # VS Code by default
APP_NAME = "BuddyDash"
CONFIG_DIR_NAME = "BuddyDash"

# Logging setup
def setup_logging() -> None:
    """Setup logging to both console and file."""
    config_dir = get_config_dir()
    log_file = config_dir / "BuddyDash.log"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    # File handler
    file_handler = RotatingFileHandler(
        log_file, maxBytes=1024*1024, backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


# ============================================================
# REGION 200: DATA MODELS
# ============================================================

class ProjectStatus(Enum):
    """Project status enumeration."""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    PLANNING = "PLANNING"
    RELEASED = "RELEASED"


class ProjectPriority(Enum):
    """Project priority enumeration."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class DailyTodo:
    """Daily TODO item for a project."""
    id: str
    project_id: str
    title: str
    is_done: bool
    date: str  # ISO format date string

    @staticmethod
    def create(project_id: str, title: str) -> 'DailyTodo':
        """Create a new TODO for today."""
        return DailyTodo(
            id=str(uuid.uuid4()),
            project_id=project_id,
            title=title,
            is_done=False,
            date=date.today().isoformat()
        )


@dataclass
class GitStatusInfo:
    """Git repository status information."""
    branch: Optional[str] = None
    is_dirty: bool = False
    last_commit_summary: Optional[str] = None
    last_commit_datetime: Optional[str] = None  # ISO format


@dataclass
class Project:
    """Project data model."""
    id: str
    name: str
    status: str  # ProjectStatus value
    priority: str  # ProjectPriority value
    last_updated: str  # ISO format datetime
    progress: int  # 0-100
    project_path: str
    git_repo_path: Optional[str]
    notes: str
    order_index: int
    daily_todos: List[dict] = field(default_factory=list)

    @staticmethod
    def create(
        name: str,
        status: ProjectStatus,
        priority: ProjectPriority,
        project_path: Path,
        git_repo_path: Optional[Path] = None,
        order_index: int = 0
    ) -> 'Project':
        """Create a new project."""
        return Project(
            id=str(uuid.uuid4()),
            name=name,
            status=status.value,
            priority=priority.value,
            last_updated=datetime.now().isoformat(),
            progress=0,
            project_path=str(project_path),
            git_repo_path=str(git_repo_path) if git_repo_path else None,
            notes="",
            order_index=order_index,
            daily_todos=[]
        )

    def get_status_enum(self) -> ProjectStatus:
        """Get status as enum."""
        return ProjectStatus(self.status)

    def get_priority_enum(self) -> ProjectPriority:
        """Get priority as enum."""
        return ProjectPriority(self.priority)

    def get_todos(self) -> List[DailyTodo]:
        """Get todos as DailyTodo objects."""
        return [DailyTodo(**t) for t in self.daily_todos]

    def set_todos(self, todos: List[DailyTodo]) -> None:
        """Set todos from DailyTodo objects."""
        self.daily_todos = [asdict(t) for t in todos]

    def update_timestamp(self) -> None:
        """Update the last_updated timestamp."""
        self.last_updated = datetime.now().isoformat()


# ============================================================
# REGION 300: PERSISTENCE & STORAGE LAYER
# ============================================================

def get_config_dir() -> Path:
    """Get the configuration directory path."""
    if os.name == 'nt':  # Windows
        appdata = os.environ.get('APPDATA')
        if appdata:
            config_dir = Path(appdata) / CONFIG_DIR_NAME
        else:
            config_dir = Path.home() / '.config' / CONFIG_DIR_NAME
    else:
        config_dir = Path.home() / '.config' / CONFIG_DIR_NAME

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_file() -> Path:
    """Get the configuration file path."""
    return get_config_dir() / "config.json"


def load_projects() -> List[Project]:
    """Load projects from JSON configuration file."""
    config_file = get_config_file()

    if not config_file.exists():
        logging.info("No configuration file found, starting with empty project list.")
        return []

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        projects = [Project(**p) for p in data.get('projects', [])]
        logging.info(f"Loaded {len(projects)} projects from {config_file}")
        return projects

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logging.error(f"Error loading configuration: {e}")
        QMessageBox.warning(
            None,
            "Configuration Error",
            f"Failed to load configuration file:\n{e}\n\nStarting with empty project list."
        )
        return []


def save_projects(projects: List[Project]) -> None:
    """Save projects to JSON configuration file."""
    config_file = get_config_file()

    try:
        data = {
            'projects': [asdict(p) for p in projects],
            'last_saved': datetime.now().isoformat()
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logging.info(f"Saved {len(projects)} projects to {config_file}")

    except Exception as e:
        logging.error(f"Error saving configuration: {e}")
        QMessageBox.critical(
            None,
            "Save Error",
            f"Failed to save configuration:\n{e}"
        )


def export_projects_to_markdown(projects: List[Project], target_path: Path) -> None:
    """Export projects to a Markdown file."""
    try:
        lines = ["# BuddyDash Projects\n\n"]
        lines.append(f"*Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")

        # Table header
        lines.append("| Name | Status | Priority | Progress | Last Updated | Path | Git Branch | Dirty | Last Commit |\n")
        lines.append("|------|--------|----------|----------|--------------|------|------------|-------|-------------|\n")

        # Sort projects by order_index
        sorted_projects = sorted(projects, key=lambda p: p.order_index)

        for project in sorted_projects:
            name = project.name
            status = project.status
            priority = project.priority
            progress = f"{project.progress}%"

            # Format last updated
            try:
                dt = datetime.fromisoformat(project.last_updated)
                last_updated = dt.strftime('%Y-%m-%d %H:%M')
            except:
                last_updated = project.last_updated

            path = project.project_path

            # Git info (will be populated by git helpers)
            git_branch = "N/A"
            git_dirty = "N/A"
            git_commit = "N/A"

            if project.git_repo_path and GIT_AVAILABLE:
                git_info = get_git_status(Path(project.git_repo_path))
                git_branch = git_info.branch or "N/A"
                git_dirty = "Yes" if git_info.is_dirty else "No"
                git_commit = git_info.last_commit_summary or "N/A"

            lines.append(
                f"| {name} | {status} | {priority} | {progress} | "
                f"{last_updated} | {path} | {git_branch} | {git_dirty} | {git_commit} |\n"
            )

        # Write to file
        with open(target_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        logging.info(f"Exported {len(projects)} projects to {target_path}")

    except Exception as e:
        logging.error(f"Error exporting to Markdown: {e}")
        raise


# ============================================================
# REGION 400: GIT INTEGRATION HELPERS
# ============================================================

def get_git_status(repo_path: Path) -> GitStatusInfo:
    """Get git status for a repository."""
    if not GIT_AVAILABLE:
        return GitStatusInfo()

    try:
        if not repo_path.exists():
            return GitStatusInfo()

        repo = git.Repo(repo_path)

        # Get current branch
        try:
            branch = repo.active_branch.name
        except:
            branch = None

        # Check if dirty
        is_dirty = repo.is_dirty(untracked_files=True)

        # Get last commit
        last_commit_summary = None
        last_commit_datetime = None

        try:
            last_commit = repo.head.commit
            last_commit_summary = last_commit.summary
            last_commit_datetime = datetime.fromtimestamp(
                last_commit.committed_date
            ).isoformat()
        except:
            pass

        return GitStatusInfo(
            branch=branch,
            is_dirty=is_dirty,
            last_commit_summary=last_commit_summary,
            last_commit_datetime=last_commit_datetime
        )

    except Exception as e:
        logging.debug(f"Git status error for {repo_path}: {e}")
        return GitStatusInfo()


class GitStatusWorker(QThread):
    """Background worker for fetching git status."""
    status_ready = pyqtSignal(str, GitStatusInfo)  # project_id, status

    def __init__(self, project_id: str, repo_path: Path):
        super().__init__()
        self.project_id = project_id
        self.repo_path = repo_path

    def run(self) -> None:
        """Fetch git status in background."""
        status = get_git_status(self.repo_path)
        self.status_ready.emit(self.project_id, status)


# ============================================================
# REGION 500: THEME & STYLING (DARK THEME)
# ============================================================

def setup_dark_palette() -> QPalette:
    """Create and return a dark color palette."""
    palette = QPalette()

    # Base colors
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(35, 35, 35))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Button, QColor(40, 40, 40))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

    return palette


DARK_QSS = """
QMainWindow {
    background-color: #1e1e1e;
}

QToolBar {
    background-color: #2d2d2d;
    border: none;
    spacing: 5px;
    padding: 5px;
}

QPushButton {
    background-color: #3c3c3c;
    color: #dcdcdc;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #4c4c4c;
    border: 1px solid #666666;
}

QPushButton:pressed {
    background-color: #2a2a2a;
}

QLineEdit {
    background-color: #252525;
    color: #dcdcdc;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 5px;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #2a82da;
}

QComboBox {
    background-color: #3c3c3c;
    color: #dcdcdc;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 5px;
    font-size: 13px;
}

QComboBox:hover {
    border: 1px solid #666666;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    color: #dcdcdc;
    selection-background-color: #2a82da;
    border: 1px solid #555555;
}

QScrollArea {
    border: none;
    background-color: #1e1e1e;
}

QGroupBox {
    background-color: #252525;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 10px;
    font-size: 13px;
    font-weight: bold;
}

QGroupBox::title {
    color: #dcdcdc;
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

QListWidget {
    background-color: #252525;
    color: #dcdcdc;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
}

QListWidget::item {
    padding: 4px;
}

QListWidget::item:hover {
    background-color: #3c3c3c;
}

QListWidget::item:selected {
    background-color: #2a82da;
}

QPlainTextEdit {
    background-color: #252525;
    color: #dcdcdc;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
}

QProgressBar {
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    text-align: center;
    background-color: #252525;
    color: #dcdcdc;
}

QProgressBar::chunk {
    background-color: #2a82da;
    border-radius: 3px;
}

QCheckBox {
    color: #dcdcdc;
    spacing: 5px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #555555;
    border-radius: 3px;
    background-color: #252525;
}

QCheckBox::indicator:checked {
    background-color: #2a82da;
    border: 1px solid #2a82da;
}

QLabel {
    color: #dcdcdc;
}

QFrame {
    background-color: transparent;
}
"""


def get_priority_color(priority: ProjectPriority) -> str:
    """Get color for priority."""
    colors = {
        ProjectPriority.LOW: "#4a9eff",
        ProjectPriority.MEDIUM: "#ffa500",
        ProjectPriority.HIGH: "#ff6b6b",
        ProjectPriority.CRITICAL: "#ff0000",
    }
    return colors.get(priority, "#808080")


def get_status_color(status: ProjectStatus) -> str:
    """Get color for status."""
    colors = {
        ProjectStatus.ACTIVE: "#4caf50",
        ProjectStatus.PAUSED: "#ffa500",
        ProjectStatus.PLANNING: "#2196f3",
        ProjectStatus.RELEASED: "#9c27b0",
    }
    return colors.get(status, "#808080")


# ============================================================
# REGION 600: UI WIDGETS - PROJECT CARDS, TODO, NOTES
# ============================================================

class ProjectCard(QFrame):
    """Project card widget displaying project information."""
    clicked = pyqtSignal(str)  # project_id
    delete_requested = pyqtSignal(str)  # project_id
    edit_requested = pyqtSignal(str)  # project_id

    def __init__(self, project: Project, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.project = project
        self.git_status: Optional[GitStatusInfo] = None
        self.is_selected = False

        self.setup_ui()
        self.load_git_status()

    def setup_ui(self) -> None:
        """Setup the card UI."""
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header row: name + status/priority badges
        header_layout = QHBoxLayout()

        self.name_label = QLabel(f"<b>{self.project.name}</b>")
        self.name_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(self.name_label)

        header_layout.addStretch()

        # Status badge
        status = self.project.get_status_enum()
        status_color = get_status_color(status)
        self.status_label = QLabel(status.value)
        self.status_label.setStyleSheet(f"""
            background-color: {status_color};
            color: white;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
        """)
        header_layout.addWidget(self.status_label)

        # Priority badge
        priority = self.project.get_priority_enum()
        priority_color = get_priority_color(priority)
        self.priority_label = QLabel(priority.value)
        self.priority_label.setStyleSheet(f"""
            background-color: {priority_color};
            color: white;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
        """)
        header_layout.addWidget(self.priority_label)

        layout.addLayout(header_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(self.project.progress)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat(f"{self.project.progress}%")
        layout.addWidget(self.progress_bar)

        # Last updated
        try:
            dt = datetime.fromisoformat(self.project.last_updated)
            updated_text = dt.strftime('%Y-%m-%d %H:%M')
        except:
            updated_text = self.project.last_updated

        self.updated_label = QLabel(f"Updated: {updated_text}")
        self.updated_label.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(self.updated_label)

        # Git info
        self.git_label = QLabel("Loading git info...")
        self.git_label.setStyleSheet("color: #888888; font-size: 11px;")
        self.git_label.setWordWrap(True)
        layout.addWidget(self.git_label)

        # Path info
        path_exists = Path(self.project.project_path).exists()
        path_style = "color: #888888;" if path_exists else "color: #ff6b6b;"
        path_text = self.project.project_path if path_exists else f"{self.project.project_path} (MISSING)"
        self.path_label = QLabel(f"Path: {path_text}")
        self.path_label.setStyleSheet(f"{path_style} font-size: 11px;")
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)

        # Buttons row
        button_layout = QHBoxLayout()

        self.explorer_btn = QPushButton("Explorer")
        self.explorer_btn.clicked.connect(self.open_in_explorer)
        button_layout.addWidget(self.explorer_btn)

        self.ide_btn = QPushButton("IDE")
        self.ide_btn.clicked.connect(self.open_in_ide)
        button_layout.addWidget(self.ide_btn)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.project.id))
        button_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.project.id))
        button_layout.addWidget(self.delete_btn)

        layout.addLayout(button_layout)

        self.update_selection_style()

    def load_git_status(self) -> None:
        """Load git status in background."""
        if not GIT_AVAILABLE or not self.project.git_repo_path:
            self.git_label.setText("Git: Not available")
            return

        repo_path = Path(self.project.git_repo_path)
        self.worker = GitStatusWorker(self.project.id, repo_path)
        self.worker.status_ready.connect(self.on_git_status_ready)
        self.worker.start()

    def on_git_status_ready(self, project_id: str, status: GitStatusInfo) -> None:
        """Handle git status result."""
        if project_id != self.project.id:
            return

        self.git_status = status

        if status.branch:
            dirty = " ● dirty" if status.is_dirty else " clean"
            commit = status.last_commit_summary or "No commits"
            self.git_label.setText(
                f"Git: {status.branch}{dirty} | {commit[:50]}"
            )
        else:
            self.git_label.setText("Git: No repository")

    def open_in_explorer(self) -> None:
        """Open project path in Windows Explorer."""
        path = Path(self.project.project_path)
        if not path.exists():
            QMessageBox.warning(self, "Path Not Found", f"Path does not exist:\n{path}")
            return

        try:
            if os.name == 'nt':
                subprocess.Popen(['explorer', str(path)])
            else:
                subprocess.Popen(['xdg-open', str(path)])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Explorer:\n{e}")

    def open_in_ide(self) -> None:
        """Open project path in IDE."""
        path = Path(self.project.project_path)
        if not path.exists():
            QMessageBox.warning(self, "Path Not Found", f"Path does not exist:\n{path}")
            return

        try:
            subprocess.Popen(DEFAULT_IDE_COMMAND + [str(path)])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open IDE:\n{e}")

    def set_selected(self, selected: bool) -> None:
        """Set selection state."""
        self.is_selected = selected
        self.update_selection_style()

    def update_selection_style(self) -> None:
        """Update visual style based on selection."""
        if self.is_selected:
            self.setStyleSheet("""
                ProjectCard {
                    background-color: #2a2a2a;
                    border: 2px solid #2a82da;
                    border-radius: 6px;
                }
            """)
        else:
            self.setStyleSheet("""
                ProjectCard {
                    background-color: #252525;
                    border: 1px solid #3c3c3c;
                    border-radius: 6px;
                }
                ProjectCard:hover {
                    border: 1px solid #555555;
                }
            """)

    def mousePressEvent(self, event) -> None:
        """Handle mouse click."""
        self.clicked.emit(self.project.id)
        super().mousePressEvent(event)


class DailyTodoWidget(QWidget):
    """Widget for managing daily TODOs."""
    todos_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.project: Optional[Project] = None
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup the TODO widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header_layout = QHBoxLayout()
        today_str = date.today().strftime('%Y-%m-%d')
        self.title_label = QLabel(f"<b>Daily TODOs – {today_str}</b>")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        self.add_btn = QPushButton("+ Add TODO")
        self.add_btn.clicked.connect(self.add_todo)
        header_layout.addWidget(self.add_btn)

        layout.addLayout(header_layout)

        # TODO list
        self.todo_list = QListWidget()
        self.todo_list.setMaximumHeight(300)
        layout.addWidget(self.todo_list)

    def set_project(self, project: Optional[Project]) -> None:
        """Set the current project."""
        self.project = project
        self.refresh_todos()

    def refresh_todos(self) -> None:
        """Refresh the TODO list."""
        self.todo_list.clear()

        if not self.project:
            self.add_btn.setEnabled(False)
            return

        self.add_btn.setEnabled(True)

        today_str = date.today().isoformat()
        todos = self.project.get_todos()
        today_todos = [t for t in todos if t.date == today_str]

        for todo in today_todos:
            item = QListWidgetItem()
            self.todo_list.addItem(item)

            checkbox = QCheckBox(todo.title)
            checkbox.setChecked(todo.is_done)
            checkbox.stateChanged.connect(
                lambda state, t=todo: self.toggle_todo(t, state)
            )

            self.todo_list.setItemWidget(item, checkbox)

    def add_todo(self) -> None:
        """Add a new TODO."""
        if not self.project:
            return

        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(
            self, "Add TODO", "TODO title:"
        )

        if ok and text.strip():
            todo = DailyTodo.create(self.project.id, text.strip())
            todos = self.project.get_todos()
            todos.append(todo)
            self.project.set_todos(todos)
            self.project.update_timestamp()

            self.refresh_todos()
            self.todos_changed.emit()

    def toggle_todo(self, todo: DailyTodo, state: int) -> None:
        """Toggle TODO done state."""
        if not self.project:
            return

        todo.is_done = (state == Qt.CheckState.Checked.value)

        todos = self.project.get_todos()
        for t in todos:
            if t.id == todo.id:
                t.is_done = todo.is_done
                break

        self.project.set_todos(todos)
        self.project.update_timestamp()
        self.todos_changed.emit()


class QuickNotesWidget(QWidget):
    """Widget for editing quick notes."""
    notes_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.project: Optional[Project] = None
        self.save_timer = QTimer()
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self.save_notes)

        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup the notes widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header_layout = QHBoxLayout()
        self.title_label = QLabel("<b>Quick Notes</b>")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        self.save_btn = QPushButton("Save Notes")
        self.save_btn.clicked.connect(self.save_notes)
        header_layout.addWidget(self.save_btn)

        layout.addLayout(header_layout)

        # Notes editor
        self.notes_editor = QPlainTextEdit()
        self.notes_editor.setPlaceholderText("Enter project notes here...")
        self.notes_editor.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.notes_editor)

    def set_project(self, project: Optional[Project]) -> None:
        """Set the current project."""
        self.project = project

        if project:
            self.notes_editor.setPlainText(project.notes)
            self.notes_editor.setEnabled(True)
            self.save_btn.setEnabled(True)
        else:
            self.notes_editor.clear()
            self.notes_editor.setEnabled(False)
            self.save_btn.setEnabled(False)

    def on_text_changed(self) -> None:
        """Handle text change with debounce."""
        self.save_timer.stop()
        self.save_timer.start(1000)  # Auto-save after 1 second of inactivity

    def save_notes(self) -> None:
        """Save notes to project."""
        if not self.project:
            return

        self.project.notes = self.notes_editor.toPlainText()
        self.project.update_timestamp()
        self.notes_changed.emit()


# ============================================================
# REGION 700: MAIN WINDOW, TOOLBAR, FILTERING, ACTIONS
# ============================================================

class AddEditProjectDialog(QDialog):
    """Dialog for adding or editing a project."""

    def __init__(self, project: Optional[Project] = None, max_order: int = 0, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.project = project
        self.max_order = max_order
        self.is_edit = project is not None

        self.setWindowTitle("Edit Project" if self.is_edit else "Add Project")
        self.setModal(True)
        self.setup_ui()

        if self.is_edit:
            self.load_project_data()

    def setup_ui(self) -> None:
        """Setup dialog UI."""
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        # Name
        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)

        # Status
        self.status_combo = QComboBox()
        for status in ProjectStatus:
            self.status_combo.addItem(status.value, status)
        form_layout.addRow("Status:", self.status_combo)

        # Priority
        self.priority_combo = QComboBox()
        for priority in ProjectPriority:
            self.priority_combo.addItem(priority.value, priority)
        form_layout.addRow("Priority:", self.priority_combo)

        # Progress
        self.progress_spin = QProgressBar()
        progress_layout = QHBoxLayout()
        self.progress_slider = QLineEdit("0")
        self.progress_slider.setMaximumWidth(50)
        progress_layout.addWidget(self.progress_slider)
        progress_layout.addWidget(QLabel("%"))
        form_layout.addRow("Progress:", progress_layout)

        # Project Path
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        path_layout.addWidget(self.path_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)

        form_layout.addRow("Project Path:", path_layout)

        # Git Repo Path
        git_layout = QHBoxLayout()
        self.git_path_edit = QLineEdit()
        git_layout.addWidget(self.git_path_edit)

        git_browse_btn = QPushButton("Browse...")
        git_browse_btn.clicked.connect(self.browse_git_path)
        git_layout.addWidget(git_browse_btn)

        auto_detect_btn = QPushButton("Auto-detect")
        auto_detect_btn.clicked.connect(self.auto_detect_git)
        git_layout.addWidget(auto_detect_btn)

        form_layout.addRow("Git Repo Path:", git_layout)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_project_data(self) -> None:
        """Load existing project data into form."""
        if not self.project:
            return

        self.name_edit.setText(self.project.name)

        # Set status
        status = self.project.get_status_enum()
        index = self.status_combo.findData(status)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)

        # Set priority
        priority = self.project.get_priority_enum()
        index = self.priority_combo.findData(priority)
        if index >= 0:
            self.priority_combo.setCurrentIndex(index)

        self.progress_slider.setText(str(self.project.progress))
        self.path_edit.setText(self.project.project_path)

        if self.project.git_repo_path:
            self.git_path_edit.setText(self.project.git_repo_path)

    def browse_path(self) -> None:
        """Browse for project path."""
        path = QFileDialog.getExistingDirectory(
            self, "Select Project Directory"
        )
        if path:
            self.path_edit.setText(path)
            self.auto_detect_git()

    def browse_git_path(self) -> None:
        """Browse for git repo path."""
        path = QFileDialog.getExistingDirectory(
            self, "Select Git Repository Directory"
        )
        if path:
            self.git_path_edit.setText(path)

    def auto_detect_git(self) -> None:
        """Auto-detect git repository in project path."""
        project_path = self.path_edit.text()
        if not project_path:
            return

        path = Path(project_path)
        if not path.exists():
            return

        # Check if project path itself is a git repo
        if (path / '.git').exists():
            self.git_path_edit.setText(project_path)
            return

    def get_project(self) -> Project:
        """Get the project from form data."""
        name = self.name_edit.text().strip()
        status = self.status_combo.currentData()
        priority = self.priority_combo.currentData()
        progress = int(self.progress_slider.text() or "0")
        project_path = Path(self.path_edit.text())
        git_path_text = self.git_path_edit.text().strip()
        git_repo_path = Path(git_path_text) if git_path_text else None

        if self.is_edit:
            # Update existing project
            self.project.name = name
            self.project.status = status.value
            self.project.priority = priority.value
            self.project.progress = progress
            self.project.project_path = str(project_path)
            self.project.git_repo_path = str(git_repo_path) if git_repo_path else None
            self.project.update_timestamp()
            return self.project
        else:
            # Create new project
            return Project.create(
                name=name,
                status=status,
                priority=priority,
                project_path=project_path,
                git_repo_path=git_repo_path,
                order_index=self.max_order + 1
            )


class BuddyDashMainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.projects: List[Project] = []
        self.project_cards: dict[str, ProjectCard] = {}
        self.current_project: Optional[Project] = None

        self.setWindowTitle("BuddyDash - Project Dashboard")
        self.setMinimumSize(1200, 800)

        self.setup_ui()
        self.load_projects()
        self.apply_filters()

    def setup_ui(self) -> None:
        """Setup the main window UI."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Add Project button
        add_action = QAction("+ Add Project", self)
        add_action.triggered.connect(self.add_project)
        add_action.setShortcut("Ctrl+N")
        toolbar.addAction(add_action)

        toolbar.addSeparator()

        # Export button
        export_action = QAction("Export to Markdown", self)
        export_action.triggered.connect(self.export_to_markdown)
        export_action.setShortcut("Ctrl+E")
        toolbar.addAction(export_action)

        toolbar.addSeparator()

        # Filters
        toolbar.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("All", None)
        for status in ProjectStatus:
            self.status_filter.addItem(status.value, status)
        self.status_filter.currentIndexChanged.connect(self.apply_filters)
        toolbar.addWidget(self.status_filter)

        toolbar.addWidget(QLabel("Priority:"))
        self.priority_filter = QComboBox()
        self.priority_filter.addItem("All", None)
        for priority in ProjectPriority:
            self.priority_filter.addItem(priority.value, priority)
        self.priority_filter.currentIndexChanged.connect(self.apply_filters)
        toolbar.addWidget(self.priority_filter)

        toolbar.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter by name...")
        self.search_box.setMaximumWidth(200)
        self.search_box.textChanged.connect(self.apply_filters)
        self.search_box.setShortcut("Ctrl+F")
        toolbar.addWidget(self.search_box)

        toolbar.addSeparator()

        # Git availability indicator
        if not GIT_AVAILABLE:
            git_label = QLabel("Git: Disabled (GitPython not installed)")
            git_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
            toolbar.addWidget(git_label)

        # Split layout: left = projects, right = details
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Project list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(10, 10, 10, 10)

        projects_label = QLabel("<b>Projects</b>")
        projects_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        left_layout.addWidget(projects_label)

        # Scrollable project list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.projects_container = QWidget()
        self.projects_layout = QVBoxLayout(self.projects_container)
        self.projects_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.projects_layout.setSpacing(10)

        scroll.setWidget(self.projects_container)
        left_layout.addWidget(scroll)

        splitter.addWidget(left_widget)

        # Right: Details panel
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)

        details_label = QLabel("<b>Project Details</b>")
        details_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        right_layout.addWidget(details_label)

        # Daily TODOs
        self.todo_widget = DailyTodoWidget()
        self.todo_widget.todos_changed.connect(self.on_project_changed)
        right_layout.addWidget(self.todo_widget)

        # Quick Notes
        self.notes_widget = QuickNotesWidget()
        self.notes_widget.notes_changed.connect(self.on_project_changed)
        right_layout.addWidget(self.notes_widget)

        splitter.addWidget(right_widget)

        # Set initial splitter sizes
        splitter.setSizes([700, 500])

        main_layout.addWidget(splitter)

    def load_projects(self) -> None:
        """Load projects from storage."""
        self.projects = load_projects()

        # Sort by order_index
        self.projects.sort(key=lambda p: p.order_index)

        # Create project cards
        for project in self.projects:
            self.add_project_card(project)

    def add_project_card(self, project: Project) -> None:
        """Add a project card to the UI."""
        card = ProjectCard(project)
        card.clicked.connect(self.on_project_clicked)
        card.delete_requested.connect(self.delete_project)
        card.edit_requested.connect(self.edit_project)

        self.project_cards[project.id] = card
        self.projects_layout.addWidget(card)

    def apply_filters(self) -> None:
        """Apply current filters to project list."""
        status_filter = self.status_filter.currentData()
        priority_filter = self.priority_filter.currentData()
        search_text = self.search_box.text().lower()

        for project_id, card in self.project_cards.items():
            project = card.project

            # Status filter
            if status_filter and project.get_status_enum() != status_filter:
                card.hide()
                continue

            # Priority filter
            if priority_filter and project.get_priority_enum() != priority_filter:
                card.hide()
                continue

            # Search filter
            if search_text and search_text not in project.name.lower():
                card.hide()
                continue

            card.show()

    def on_project_clicked(self, project_id: str) -> None:
        """Handle project card click."""
        # Deselect all cards
        for card in self.project_cards.values():
            card.set_selected(False)

        # Select clicked card
        if project_id in self.project_cards:
            card = self.project_cards[project_id]
            card.set_selected(True)
            self.current_project = card.project

            # Update detail panels
            self.todo_widget.set_project(self.current_project)
            self.notes_widget.set_project(self.current_project)

    def add_project(self) -> None:
        """Add a new project."""
        max_order = max((p.order_index for p in self.projects), default=0)

        dialog = AddEditProjectDialog(max_order=max_order, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            project = dialog.get_project()
            self.projects.append(project)
            self.add_project_card(project)
            self.save_projects()
            self.apply_filters()

            logging.info(f"Added project: {project.name}")

    def edit_project(self, project_id: str) -> None:
        """Edit an existing project."""
        project = next((p for p in self.projects if p.id == project_id), None)
        if not project:
            return

        max_order = max((p.order_index for p in self.projects), default=0)

        dialog = AddEditProjectDialog(project=project, max_order=max_order, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update card
            if project_id in self.project_cards:
                old_card = self.project_cards[project_id]
                index = self.projects_layout.indexOf(old_card)
                self.projects_layout.removeWidget(old_card)
                old_card.deleteLater()

                new_card = ProjectCard(project)
                new_card.clicked.connect(self.on_project_clicked)
                new_card.delete_requested.connect(self.delete_project)
                new_card.edit_requested.connect(self.edit_project)

                self.project_cards[project_id] = new_card
                self.projects_layout.insertWidget(index, new_card)

                # Re-select if it was selected
                if self.current_project and self.current_project.id == project_id:
                    new_card.set_selected(True)

            self.save_projects()
            self.apply_filters()

            logging.info(f"Edited project: {project.name}")

    def delete_project(self, project_id: str) -> None:
        """Delete a project."""
        project = next((p for p in self.projects if p.id == project_id), None)
        if not project:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete project '{project.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Remove from list
            self.projects = [p for p in self.projects if p.id != project_id]

            # Remove card
            if project_id in self.project_cards:
                card = self.project_cards[project_id]
                self.projects_layout.removeWidget(card)
                card.deleteLater()
                del self.project_cards[project_id]

            # Clear selection if this was selected
            if self.current_project and self.current_project.id == project_id:
                self.current_project = None
                self.todo_widget.set_project(None)
                self.notes_widget.set_project(None)

            self.save_projects()
            logging.info(f"Deleted project: {project.name}")

    def export_to_markdown(self) -> None:
        """Export projects to Markdown file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to Markdown",
            str(Path.home() / "BuddyDash_Projects.md"),
            "Markdown Files (*.md)"
        )

        if file_path:
            try:
                export_projects_to_markdown(self.projects, Path(file_path))
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Projects exported to:\n{file_path}"
                )
                logging.info(f"Exported projects to {file_path}")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Failed to export projects:\n{e}"
                )

    def on_project_changed(self) -> None:
        """Handle project data change."""
        self.save_projects()

    def save_projects(self) -> None:
        """Save projects to storage."""
        save_projects(self.projects)


# ============================================================
# REGION 800: APPLICATION BOOTSTRAP
# ============================================================

def main() -> int:
    """Main application entry point."""
    # Setup logging first
    setup_logging()
    logging.info("Starting BuddyDash...")

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    # Apply dark theme
    palette = setup_dark_palette()
    app.setPalette(palette)
    app.setStyleSheet(DARK_QSS)

    # Create and show main window
    window = BuddyDashMainWindow()
    window.show()

    logging.info("BuddyDash started successfully")

    # Run application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
