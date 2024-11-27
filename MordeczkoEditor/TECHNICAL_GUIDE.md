# Technical Guide

## Table of Contents

1. [Code Structure](#code-structure)
   - [MainWindow](#mainwindow)
   - [CodeEditor](#codeeditor)
   - [GenericHighlighter](#generichighlighter)
   - [LineNumberArea](#linenumberarea)
   - [FunctionPanel](#functionpanel)
   - [HistoryPanel](#historypanel)
   - [LinterWorker](#linterworker)
   - [Translator](#translator)
2. [Adding a New Feature](#adding-a-new-feature)
3. [Debugging Tips](#debugging-tips)

## Code Structure

### MainWindow

- **Description**: The main window of the application, managing layout and interactions.
- **Key Attributes**:
  - `tab_widget`: Manages multiple code editor tabs.
  - `output`: Panel for displaying output and messages.
  - `functions_panel`: Displays a list of functions in the current code.
  - `history_panel`: Shows the history of code changes.
  - `automatic_linting_enabled`: Stores the state of automatic linting.
  - `git_repo_path`: Stores the path to the selected Git repository.
- **Key Methods**:
  - `create_menu()`: Creates the application menu with all actions and settings.
  - `add_new_tab(code, filename)`: Adds a new tab with a code editor.
  - `get_current_editor()`: Returns the currently active CodeEditor instance.
  - `change_language(lang_code)`: Changes the application language.
  - `toggle_automatic_linting(checked)`: Enables or disables automatic linting across all editors.
  - Handles actions related to files, running code, debugging, Git integration, and more.

### CodeEditor

- **Description**: Extends QPlainTextEdit, providing advanced code editing functionalities.
- **Features**:
  - Syntax Highlighting: Uses `GenericHighlighter` for multiple languages.
  - Line Numbering: Displays line numbers and handles breakpoints via `LineNumberArea`.
  - Automatic Indentation: Smart indentation while coding.
  - Code Change History: Tracks changes and integrates with `HistoryPanel`.
  - Learning Mode: Provides contextual suggestions.
- **Key Methods**:
  - `run_linter()`: Runs the linter in a separate thread.
  - `on_text_changed()`: Handles actions after text changes.
  - `toggle_learning_mode(enabled)`: Enables or disables learning mode.

### GenericHighlighter

- **Description**: Responsible for syntax highlighting in the code editor.
- **Methods**:
  - `set_language(language)`: Sets the language for syntax highlighting.
  - `highlightBlock(text)`: Highlights a block of text based on syntax rules.

### LineNumberArea

- **Description**: Widget displaying line numbers and handling breakpoint interactions.
- **Features**:
  - Drawing line numbers alongside the code editor.
  - Handling mouse clicks to set or remove breakpoints.

### FunctionPanel

- **Description**: Displays a list of functions detected in the current code.
- **Features**:
  - Dynamically updates with code changes.
  - Allows navigation to function definitions upon selection.

### HistoryPanel

- **Description**: Shows the history of code changes with timestamps.
- **Features**:
  - Tracks changes and allows restoring previous code versions.
  - Integrates with `CodeEditor` to receive change events.

### LinterWorker

- **Description**: Runs linting in a separate thread to prevent blocking the UI.
- **Features**:
  - Uses Pylint to analyze Python code.
  - Emits signals with linting results or errors.

### Translator

- **Description**: Manages translations and localization of the application.
- **Features**:
  - Stores translations for supported languages.
  - Provides a `translate(text)` method to translate interface text.
  - Dynamically updates language based on user selection.

## Adding a New Feature

1. **Design the Feature**: Define the functionality and how it integrates with existing components.
2. **Create or Modify Classes**:
   - Create new classes if new UI components are needed.
   - Modify existing classes to add methods or attributes for the new feature.
3. **Update the Interface**:
   - Add new actions in the menu, buttons, or panels as necessary.
   - Connect signals and slots for event handling.
4. **Implement Logic**: Write the logic for the feature, ensuring it interacts correctly with current code.
5. **Update Translations**:
   - Add new text strings to the `Translator` class for localization.
6. **Test the Feature**:
   - Ensure the feature works as expected.
   - Verify it doesn't introduce bugs or performance issues.

## Debugging Tips

- **Thread Issues**:
  - Ensure correct signal-slot connections.
  - Verify threads are properly started and terminated.
- **Interface Updates**:
  - Remember that UI updates should occur in the main thread.
- **Error Handling**:
  - Catch exceptions and provide user-friendly error messages.
  - Use the output panel to display errors and logs.
- **Logging**:
  - Utilize the logging module or `print()` statements for debugging purposes.
- **Dependency Checks**:
  - Ensure all required external libraries and tools are installed.
