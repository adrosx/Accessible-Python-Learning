# src/main.py
import sys
import os
import logging
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow

# Konfiguracja logowania
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    filemode='w'
)

# Dodaj ścieżkę do katalogu src, jeśli to konieczne
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
