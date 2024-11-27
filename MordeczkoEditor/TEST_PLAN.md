# Manual Testing Plan

## Table of Contents
- [Objective](#objective)
- [Test Scenarios](#test-scenarios)
  - [Application Launch](#application-launch)
  - [Editing Code](#editing-code)
  - [Change History](#change-history)
  - [Learning Mode](#learning-mode)
  - [Linter](#linter)
  - [Debugging](#debugging)
  - [Unit Testing](#unit-testing)
  - [Git Integration](#git-integration)
  - [Export](#export)
  - [Theme Switching](#theme-switching)
  - [Language Switching](#language-switching)
- [Notes](#notes)

## Objective
Ensure that all application functions work correctly and are aligned with the latest code changes.

## Test Scenarios

### Application Launch
**Steps:**
- Run `python main.py`.

**Expected Result:**
- The application launches without errors and displays the main window.

---

### Editing Code
**Steps:**
- Type code in the editor.
- Check syntax highlighting for the selected programming language.
- Save the file (`Ctrl + S`).

**Expected Result:**
- The code is highlighted correctly according to the language syntax.
- The file saves without errors.

---

### Change History
**Steps:**
- Make several changes to the code.
- Check the Change History panel.
- Restore a previous version of the code.

**Expected Result:**
- History updates after each change, displaying timestamps.
- Code is restored to the selected version.

---

### Learning Mode
**Steps:**
- Enable Learning Mode via `Configuration > Learning Mode`.
- Observe contextual suggestions while typing code.

**Expected Result:**
- Contextual suggestions appear while typing.
- Disabling Learning Mode stops the suggestions.

---

### Linter
**Steps:**
- Introduce intentional errors in the code.
- Ensure that Automatic Linting is enabled (`Configuration > Automatic Linting`).
- Observe linter feedback in the output panel.
- Disable Automatic Linting and manually run the linter (`Ctrl + L`).

**Expected Result:**
- The linter automatically detects errors and highlights them in the editor.
- Linter messages appear in the output panel.
- Manual linting works when Automatic Linting is disabled.

---

### Debugging
**Steps:**
- Set breakpoints by clicking on line numbers.
- Run the debugger (`F6`).
- Connect an external debugger (e.g., VSCode) on port 5678.

**Expected Result:**
- Breakpoints are set and visible.
- The debugger starts and waits for a client connection.
- The external debugger connects and allows step-by-step execution of the code.

---

### Unit Testing
**Steps:**
- Open a Python file containing unit tests.
- Run the tests via `Tests > Run Tests` or press `Ctrl + T`.

**Expected Result:**
- Tests execute successfully.
- Test results are displayed in the output panel.

---

### Git Integration
**Steps:**
- Select a Git repository via `Git > Select Git Repository`.
- Perform Git operations (Commit, Push, Pull, Create Branch, Merge Branch, Show Log).

**Expected Result:**
- Git operations execute correctly without errors.
- Appropriate messages and dialogs appear for each operation.

---

### Export
**Steps:**
- Export code to HTML via `File > Export to HTML`.
- Export code to PDF via `File > Export to PDF`.

**Expected Result:**
- HTML and PDF files are generated correctly.
- Exported files contain code with proper syntax highlighting.

---

### Theme Switching
**Steps:**
- Switch between Dark Mode and Light Mode via the `View` menu.

**Expected Result:**
- The application theme changes according to the selection.
- All interface elements are displayed correctly in both themes.

---

### Language Switching
**Steps:**
- Change the application language via `Configuration > Language`.
- Select between English and Polish.

**Expected Result:**
- The application updates all menus and labels to the selected language.
- The change is reflected immediately.

---

## Notes
- **Reporting Bugs:** Document any encountered issues, including steps to reproduce them.
- **UI Consistency:** Ensure that the user interface is intuitive and labels are correctly translated.
- **Performance:** Verify that the application runs smoothly without delays or freezes.
- **Dependency Checks:** Ensure all required external dependencies (e.g., `debugpy`, `pylint`, `pdfkit`) are installed and properly configured.
