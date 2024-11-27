
# Simple Python Editor - MiniIDE

## Table of Contents

- [Description](#description)
- [Requirements](#requirements)
- [Installation](#installation)
- [Launching the Application](#launching-the-application)
- [Key Features](#key-features)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Usage Examples](#usage-examples)

## Description

The **Simple Python Editor - MiniIDE** is a lightweight code editor offering essential IDE functionalities, such as:

- Syntax highlighting for multiple programming languages.
- Code change history tracking.
- Learning mode with contextual suggestions.
- Integration with Git version control.
- Running unit tests.
- Debugging Python code.
- Language localization (English and Polish).
- Automatic and manual code linting.
- Code export to HTML and PDF.

## Requirements

- **Python**: Version 3.8 or later.
- **Python Libraries**:
  - PyQt6
  - pygments
  - pdfkit
  - gitpython
  - unittest (built-in Python library)
  - **Optional**:
    - debugpy (for debugging)
    - pylint (for code linting)
- **External Tools**:
  - wkhtmltopdf (required for PDF export)

## Installation

Install the required libraries using pip:

```bash
pip install PyQt6 pygments pdfkit gitpython
```

Install optional libraries if needed:

```bash
pip install debugpy pylint
```

Ensure that `wkhtmltopdf` is installed:

- **Windows**: Download the installer from [wkhtmltopdf.org](https://wkhtmltopdf.org).
- **macOS**: Install via Homebrew:

```bash
brew install wkhtmltopdf
```

- **Linux**: Install via package manager (e.g., for Debian-based systems):

```bash
sudo apt-get install wkhtmltopdf
```

## Launching the Application

1. Clone the repository or download the `main.py` file.
2. Navigate to the folder containing `main.py` in your terminal.
3. Launch the application by running:

```bash
python main.py
```

## Key Features

### Code Editing

- Syntax highlighting for Python, JavaScript, C++, and Go.
- Line numbering and highlighting of the current line.
- Automatic indentation while writing code.

### Code Change History

- Tracks changes in the code through a dedicated history panel.
- Restore previous versions by selecting the desired timestamp from the history.

### Learning Mode

- **Activation**: Navigate to Configuration > Learning Mode in the menu.
- Displays contextual suggestions while writing code.

### Git Integration

- Perform Git operations like Commit, Push, Pull, create and merge branches, and view logs.
- Select a repository via Git > Select Git Repository in the menu.

### Unit Testing

- Run tests via Tests > Run Tests in the menu or use the shortcut `Ctrl + T`.
- Results are displayed in the output panel.

### Debugging

- Debug Python scripts using Run > Debug Script in the menu or press `F6`.
- Connect external debuggers (e.g., VSCode) on port 5678.

## Keyboard Shortcuts

- **New File**: `Ctrl + N`
- **Open File**: `Ctrl + O`
- **Save File**: `Ctrl + S`
- **Run Script**: `F5`
- **Debug Script**: `F6`
- **Run Tests**: `Ctrl + T`
- **Lint Code**: `Ctrl + L`

## Usage Examples

### Adding a Commit in Git

1. Select a repository: Navigate to Git > Select Git Repository.
2. Make changes to the code.
3. Commit changes: Navigate to Git > Commit.
4. Enter a commit message and confirm.

### Restoring a Previous Version of Code

1. Open the **Code Change History** panel on the right.
2. Click on the desired timestamp to restore the code to that version.
