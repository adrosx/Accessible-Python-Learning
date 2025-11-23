# 🎯 BuddyDash - Project Dashboard

A comprehensive PyQt6-based project management dashboard for tracking multiple development projects with Git integration.

![Dark Theme](https://img.shields.io/badge/Theme-Dark-black)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-green)

## Features

### 📊 Project Management
- **Project Cards** with visual status indicators
- Track: Name, Status, Priority, Progress %, Last Updated
- Quick notes per project
- Status categories: Active, Paused, Planning, Released
- Priority levels: 1 (High) to 5 (Low)

### 🔧 Git Integration
- Automatic Git repository detection
- Display current branch
- Show uncommitted changes count
- Display last commit message
- Real-time repository status

### 📝 Daily TODO Lists
- Per-project TODO tracking
- Mark tasks as complete
- Add/remove tasks easily
- Visual progress indicators

### 🎨 User Interface
- Beautiful dark theme
- Intuitive card-based layout
- Filter by status and priority
- Search across project names and notes
- Reorderable project list (manual reordering via data persistence)

### 🚀 Quick Actions
- **Open in Explorer** - Open project folder
- **Open in IDE** - Launch VS Code (or default)
- **Edit Project** - Full project details editor
- **Delete Project** - Remove projects with confirmation

### 📤 Export
- Export all projects to Markdown
- Organized by status
- Includes all project details, Git info, and TODOs

## Installation

### Prerequisites
- Python 3.8 or higher
- Windows (optimized), but works on Linux/Mac

### Setup

1. **Clone or download** this repository

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install PyQt6 GitPython
```

## Usage

### Running BuddyDash

```bash
python BuddyDash.py
```

### Creating Your First Project

1. Click **"➕ New Project"**
2. Fill in project details:
   - **Name**: Your project name
   - **Path**: Browse to project folder (optional, for Git integration)
   - **Status**: Active, Paused, Planning, or Released
   - **Priority**: 1 (highest) to 5 (lowest)
   - **Progress**: 0-100%
   - **Notes**: Any notes about the project
3. Add TODO items for daily tracking
4. Click **OK** to save

### Managing Projects

**Editing**: Click the **"Edit"** button on any project card

**Deleting**: Click the **"Delete"** button (with confirmation)

**Opening Folder**: Click **"Open Folder"** to open in file explorer

**Opening in IDE**: Click **"Open in IDE"** to launch in VS Code

### Filtering & Searching

- **Filter by Status**: Select from dropdown (All, Active, Paused, Planning, Released)
- **Filter by Priority**: Select priority level
- **Search**: Type in search box to filter by name or notes content

### Git Integration

If a project path points to a Git repository, BuddyDash automatically shows:
- Current branch name
- Number of uncommitted changes
- Latest commit message (abbreviated)

### Exporting Data

Click **"📄 Export to Markdown"** to create a formatted markdown file with:
- All projects organized by status
- Complete project details
- Git information
- TODO lists with completion status

## Data Storage

Projects are automatically saved to:
```
%USERPROFILE%/buddydash_projects.json  (Windows)
~/buddydash_projects.json              (Linux/Mac)
```

Data is saved automatically when:
- Creating new projects
- Editing existing projects
- Deleting projects
- Reordering projects

## Architecture

### Single-File Design
BuddyDash uses a monolithic single-file architecture with region markers for easy navigation:

- `#region Imports` - All dependencies
- `#region Data Models` - Project class and data structures
- `#region Project Storage` - JSON persistence layer
- `#region Project Card Widget` - Individual project card UI
- `#region Project Edit Dialog` - Project creation/editing dialog
- `#region Draggable Project List` - Main project list container
- `#region Main Window` - Application main window and logic
- `#region Main Entry Point` - Application startup

### Technologies Used
- **PyQt6**: Modern Qt6 bindings for Python
- **GitPython**: Git repository interaction
- **JSON**: Lightweight data persistence
- **subprocess**: System integration (open folders, IDE)

## Customization

### Changing IDE Integration
Edit the `open_in_ide()` method in `BuddyDashWindow` class:

```python
def open_in_ide(self, path: str):
    # Change 'code' to your preferred IDE command
    subprocess.run(['your-ide-command', path], check=True)
```

### Modifying Theme
Adjust colors in the `apply_dark_theme()` method:

```python
palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
# Change RGB values to customize colors
```

### Adding Status Categories
Modify the status list in `ProjectEditDialog`:

```python
self.status_combo.addItems(["Active", "Paused", "Planning", "Released", "Your-Status"])
```

## Troubleshooting

### GitPython Not Working
If Git integration fails:
```bash
pip install --upgrade GitPython
```

### VS Code Not Opening
Ensure VS Code is in your PATH:
- Windows: `code` should work from command prompt
- Linux: Usually installed to `/usr/bin/code`
- Mac: Install Shell Command from VS Code Command Palette

### Application Won't Start
Check Python version:
```bash
python --version  # Should be 3.8+
```

Verify PyQt6 installation:
```bash
python -c "import PyQt6; print('PyQt6 OK')"
```

## Keyboard Shortcuts

- **Ctrl+N**: New Project (can be added)
- **Ctrl+R**: Refresh (can be added)
- **Ctrl+E**: Export (can be added)
- **Ctrl+F**: Focus Search (can be added)

*Note: Keyboard shortcuts can be implemented by adding them to the respective button definitions*

## Tips & Best Practices

1. **Use Git Integration**: Point projects to their repository folders for automatic Git status
2. **Regular Updates**: Update progress percentages and status regularly
3. **Prioritize Effectively**: Use priority 1 for urgent items, 5 for low priority
4. **Daily TODOs**: Keep TODO lists focused on daily/short-term tasks
5. **Export Regularly**: Export to markdown for backups and sharing
6. **Search Feature**: Use search to quickly find projects by keywords

## Future Enhancements

Potential features for future versions:
- Full drag-and-drop reordering with visual feedback
- Project templates
- Time tracking integration
- Custom tags/labels
- Statistics and charts
- Multiple dashboard views
- Cloud sync support
- Integration with GitHub/GitLab APIs
- Notification system for deadlines

## License

This project is provided as-is for personal and educational use.

## Contributing

Feel free to fork and modify for your needs. Suggestions and improvements welcome!

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Verify all dependencies are installed
3. Ensure Python 3.8+ is being used

---

**Created with ❤️ using PyQt6**

*Happy project tracking!* 🚀
