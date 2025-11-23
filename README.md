# BuddyJump - Premium Folder Launcher

**Version 1.2.2** | **Author:** Adrian (BuddyIT)

A lightning-fast, feature-rich folder launcher for Windows that helps you navigate your filesystem with ease. Launch folders in Explorer or Terminal, organize with tags, and access everything with a global hotkey.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.0%2B-green)

---

## Features

### Core Functionality
- **Global Hotkey** - Access BuddyJump from anywhere with `Ctrl+Alt+Q` (customizable)
- **Smart Search** - Instant folder search with optional fuzzy matching
- **Quick Actions**
  - `Enter` - Open in Explorer
  - `Ctrl+Enter` - Open in Terminal
  - `Ctrl+C` - Copy path to clipboard
  - `Delete` - Remove folder shortcut

### Organization & Discovery
- **Tag-Based Groups** - Organize folders with tags, filter with `@tag`
- **Frecency Ranking** - Smart sorting based on frequency + recency
- **Recent Tab** - Quick access to recently used folders
- **Pin Folders** - Keep important folders at the top
- **Drag & Drop** - Add folders by dragging from Explorer
- **Aliases** - Create shortcuts like `proj` → `D:\Projects`

### Customization
- **Theme System** - Multiple themes with QSS support (VS Code Dark included)
- **Display Options** - Show/hide paths, tags, compact mode
- **Window Opacity** - Adjust transparency (50-100%)
- **Configurable Size** - Resize launcher window (400-1600px width)
- **Auto-Hide** - Optionally hide after opening folder

### Advanced Features
- **Fuzzy Search** - Typo-tolerant search (requires `rapidfuzz`)
- **Usage Tracking** - SQLite-based frecency database
- **Tasks & Reminders** - Folder-linked task management
- **Backup/Restore** - Export/import full configuration
- **Memory Monitoring** - Optional tracking with `psutil`
- **Windows Startup** - Launch on system boot
- **Single Instance** - Only one instance runs at a time

---

## Installation

### Requirements
- **Windows 10/11** (primary platform)
- **Python 3.8+**
- **PyQt6**

### Required Dependencies
```bash
pip install PyQt6
```

### Optional Dependencies
```bash
# For fuzzy search (highly recommended)
pip install rapidfuzz

# For memory monitoring
pip install psutil
```

### Quick Start
1. Clone the repository:
```bash
git clone https://github.com/yourusername/buddyjump.git
cd buddyjump
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python buddyjump.py
```

---

## Usage

### First Launch
1. BuddyJump automatically detects common folders (Documents, Downloads, Desktop)
2. Welcome screen explains key features
3. Access launcher with `Ctrl+Alt+Q` or tray icon

### Adding Folders
- **Quick Add**: Right-click → "⚡ Quick Add Folder"
- **Drag & Drop**: Drag folders from Explorer into launcher
- **Settings**: Settings → Folders → Manage Folders → "+ Add Folder"

### Searching
- **Basic**: Type folder name
- **Fuzzy**: Type partial/misspelled names (e.g., "dcmnts" finds "Documents")
- **Tag Filter**: Type `@dev` to show only folders tagged "dev"
- **Alias**: Type `proj` (if alias configured) to jump directly

### Keyboard Shortcuts

#### Launcher Window
| Shortcut | Action |
|----------|--------|
| `Ctrl+Alt+Q` | Toggle launcher visibility |
| `Ctrl+F` | Focus search box |
| `Enter` | Open folder in Explorer |
| `Ctrl+Enter` | Open folder in Terminal |
| `Ctrl+C` | Copy folder path |
| `Delete` | Remove folder shortcut |
| `Esc` | Hide launcher |

#### Settings Window
| Shortcut | Action |
|----------|--------|
| `Ctrl+F` | Search settings |
| `Delete` | Remove selected folder |
| `Esc` | Close settings |

### Context Menu (Right-Click)
- Sort by: Name / Frequency / Recent
- Quick Add / Edit / Remove folders
- Pin/Unpin folders
- Export/Import configuration
- Access Settings

---

## Configuration

### Configuration Files
BuddyJump stores data in different locations based on environment:

**Production (EXE)**:
```
%LOCALAPPDATA%\BuddyIT\BuddyJump\
├── config.json          # Main configuration
├── frecency.db          # Usage tracking database
├── themes/              # Theme files (JSON + QSS)
└── logs/                # Application logs
```

**Development**:
```
<project_directory>/
├── config.json
├── frecency.db
├── themes/
└── logs/
```

### Configuration Options

#### Display
- Show folder paths
- Show tags in names
- Compact mode (smaller items)
- Window size (400-1600px width, 300-1200px height)
- Opacity (50-100%)

#### Behavior
- Auto-hide after opening folder
- Case-sensitive search
- Search delay (0-1000ms)
- Confirm before deleting shortcuts
- Show notifications on folder changes
- Hide launcher after closing Settings
- Start minimized to tray (Silent Start)

#### Performance
- Enable fuzzy search (requires `rapidfuzz`)
- Enable frecency ranking
- Max search results (10-100)

#### Advanced
- Debug mode (verbose logging)
- Default tag for new folders
- Alias shortcuts
- Startup with Windows

---

## Themes

### Bundled Themes
- **VS Code Dark** (default) - Dark theme inspired by Visual Studio Code

### Custom Themes
Create themes with two files:

1. **Theme Definition** (`mytheme.json`):
```json
{
  "name": "My Theme",
  "author": "Your Name",
  "palette": {
    "launcher.bg": "#1e1e1e",
    "launcher.title": "#007acc",
    "launcher.search.bg": "#2d2d2d",
    "launcher.item.text": "#cccccc",
    ...
  }
}
```

2. **Optional Styling** (`mytheme.qss`):
```css
#container {
    background: qlineargradient(...);
    border-radius: 12px;
}
```

Place files in `themes/` directory and select in Settings → Appearance.

---

## Building

### PyInstaller (Recommended)
```bash
# Install PyInstaller
pip install pyinstaller

# Build one-folder distribution
pyinstaller --onedir --windowed --name BuddyJump \
    --icon=icon.ico \
    --add-data "themes;themes" \
    buddyjump.py

# Build single executable
pyinstaller --onefile --windowed --name BuddyJump \
    --icon=icon.ico \
    --add-data "themes;themes" \
    buddyjump.py
```

### Distribution
The built executable will be in `dist/` directory:
- **One-folder**: `dist/BuddyJump/BuddyJump.exe`
- **One-file**: `dist/BuddyJump.exe`

---

## Architecture

### Key Components

#### Core (`buddyjump.py`)
- **AppConfig** - Configuration management
- **FolderModel** - Folder entry filtering/sorting
- **LauncherWindow** - Main UI (PyQt6)
- **SettingsWindow** - Settings dialog with tabbed interface
- **ThemeManager** - Theme loading and validation

#### Features
- **HotkeyThread** - Global hotkey listener (Windows API)
- **FrecencyTracker** - SQLite-based usage tracking
- **ActionExecutor** - Folder actions (Explorer, Terminal, Copy)
- **SingleInstanceManager** - Mutex-based single instance
- **StartupManager** - Windows registry integration

#### Utilities
- **ErrorRecovery** - Fallback mechanisms for common failures
- **MemoryMonitor** - Optional memory leak detection (psutil)
- **SystemTray** - Tray icon and menu

### Data Flow
```
User Input → LauncherWindow → FolderModel → Filter/Sort → Display
                          ↓
                     ActionExecutor → Open/Copy/Terminal
                          ↓
                   FrecencyTracker → Record usage
```

---

## Troubleshooting

### Hotkey Not Working
1. Check if another app uses the same combination
2. Test hotkey in Settings → Hotkey → "Test Current Hotkey"
3. Try a different combination
4. Restart BuddyJump after changing hotkey

### Folders Not Showing
1. Check if path still exists
2. Verify tags/groups filter (click "All" tab)
3. Clear search box
4. Reload config (Right-click → "🔄 Reload Config")

### Performance Issues
1. Reduce max search results (Settings → Performance)
2. Disable fuzzy search if not needed
3. Clear usage history (Settings → Advanced → "Clear Usage History")
4. Check memory usage in logs

### Theme Not Applying
1. Verify theme files in `themes/` directory
2. Check logs for validation errors
3. Reset to default theme
4. Restart application

---

## Development

### Project Structure
```
buddyjump/
├── buddyjump.py         # Main application
├── icon.ico             # Application icon
├── themes/              # Theme files
│   ├── default_dark.json
│   └── default_dark.qss
├── logs/                # Log files (auto-generated)
├── config.json          # User config (auto-generated)
└── frecency.db          # Usage database (auto-generated)
```

### Logging
BuddyJump uses NASA-grade logging with:
- **File**: `logs/buddyjump.log` (10MB max, 5 backups)
- **Console**: Colored output for development
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

Enable debug mode in Settings → Advanced for verbose logging.

### Adding Features
1. Core logic → `buddyjump.py`
2. UI components → `LauncherWindow` or `SettingsWindow`
3. Configuration → `AppConfig` class
4. Themes → Extend `ThemeManager` and palette keys

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## Changelog

### v1.2.2
- **NEW**: Sorting options (Name, Frequency, Recent)
- **NEW**: Silent Start mode (start minimized to tray)
- **NEW**: Recent tab for quick access to used folders
- **NEW**: Pin folders to keep at top
- **NEW**: Drag & drop reordering
- **NEW**: Bulk tag removal
- **FIX**: Theme contrast validation
- **FIX**: Improved hotkey management (no restart needed)
- **FIX**: QSpinBox styling (seamless dark mode)

### v1.2.0
- Week 1-2 features (production ready)
- Week 3 features (fuzzy, frecency, tags)
- Extensive settings & customization
- Hotkey recorder
- Display options

---

## Known Limitations

- **Platform**: Global hotkeys only work on Windows
- **Terminal**: Requires Windows Terminal, PowerShell, or CMD
- **Single Instance**: Only one BuddyJump instance can run
- **Themes**: Some QSS features may not work in all Qt versions

---

## License

This project is licensed under the MIT License - see LICENSE file for details.

---

## Credits

**Author**: Adrian (BuddyIT)
**Framework**: PyQt6
**Inspiration**: Alfred (macOS), Launchy, Keypirinha

### Third-Party Libraries
- **PyQt6** - GUI framework
- **rapidfuzz** - Fuzzy string matching (optional)
- **psutil** - Memory monitoring (optional)

---

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/buddyjump/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/buddyjump/discussions)
- **Email**: adrian@buddyit.example.com

---

## FAQ

**Q: Can I use BuddyJump on macOS/Linux?**
A: The UI works, but global hotkeys are Windows-only. Contributions for other platforms welcome!

**Q: How do I backup my configuration?**
A: Right-click in launcher → "📤 Export Config" or Settings → Advanced → "Export Config..."

**Q: Can I sync folders between computers?**
A: Export config on computer A, import on computer B. Paths must exist on both machines.

**Q: Why does fuzzy search require rapidfuzz?**
A: Fuzzy matching is CPU-intensive. `rapidfuzz` provides fast, optimized algorithms.

**Q: How do I report a bug?**
A: Enable debug mode (Settings → Advanced), reproduce the issue, and attach `logs/buddyjump.log` to your GitHub issue.

---

**Made with ❤️ by BuddyIT**
