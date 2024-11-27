# Quick Troubleshooting Guide

## Table of Contents

1. [Application Doesn't Launch](#application-doesnt-launch)
2. [Syntax Highlighting Not Working](#syntax-highlighting-not-working)
3. [Linter Not Functioning](#linter-not-functioning)
4. [Debugging Issues](#debugging-issues)
5. [Git Operations Fail](#git-operations-fail)
6. [Language Switching Problems](#language-switching-problems)
7. [Export Function Not Working](#export-function-not-working)

## Application Doesn't Launch

- **Possible Causes**:
  - Missing required Python libraries.
  - Code errors due to version incompatibilities.
- **Solutions**:
  - Ensure all required libraries are installed (PyQt6, pygments, etc.).
  - Run the application from the terminal to view error messages:
    ```bash
    python main.py
    ```

## Syntax Highlighting Not Working

- **Possible Causes**:
  - Unsupported programming language selected.
  - Errors in the syntax highlighting module.
- **Solutions**:
  - Ensure the selected language is supported.
  - Check for errors in the terminal and make necessary corrections.

## Linter Not Functioning

- **Possible Causes**:
  - `pylint` is not installed.
  - Incorrect linter configuration.
- **Solutions**:
  - Install `pylint` using:
    ```bash
    pip install pylint
    ```
  - Verify the path to the Pylint configuration file in the application settings.

## Debugging Issues

- **Possible Causes**:
  - `debugpy` is not installed.
  - Incorrect Python interpreter path.
- **Solutions**:
  - Install `debugpy` using:
    ```bash
    pip install debugpy
    ```
  - Ensure the correct Python interpreter is selected in the application settings.

## Git Operations Fail

- **Possible Causes**:
  - Incorrect Git repository path.
  - Network issues during push or pull.
- **Solutions**:
  - Verify the Git repository path via **Git > Select Git Repository**.
  - Check network connectivity and remote repository settings.

## Language Switching Problems

- **Possible Causes**:
  - Missing translations in the `Translator` class.
- **Solutions**:
  - Ensure all interface text strings are included in the translations.
  - Update the `Translator` class with any missing entries.

## Export Function Not Working

- **Possible Causes**:
  - `pdfkit` is not properly configured.
  - `wkhtmltopdf` is not installed.
- **Solutions**:
  - Ensure `pdfkit` is installed and configured correctly.
  - Install `wkhtmltopdf` on your system:
    - **Windows**: Download the installer from [wkhtmltopdf.org](https://wkhtmltopdf.org).
    - **macOS**: Install via Homebrew:
      ```bash
      brew install wkhtmltopdf
      ```
    - **Linux**: Install via package manager (e.g., for Debian-based systems):
      ```bash
      sudo apt-get install wkhtmltopdf
      ```
