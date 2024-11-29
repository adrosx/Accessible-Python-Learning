import logging
from PyQt6.QtWidgets import QApplication
from editor_window import MegasolidEditor
import sys
import os
def exception_handler(type, value, traceback):
    import logging
    logging.error("Uncaught exception", exc_info=(type, value, traceback))
    sys.__excepthook__(type, value, traceback)

sys.excepthook = exception_handler
# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)

logging.debug("Start aplikacji")

if __name__ == "__main__":
    logging.info("Tworzenie aplikacji...")
    app = QApplication(sys.argv)
    app.setApplicationName("MordeczkoEditor")
    logging.info("Aplikacja utworzona.")

    logging.info("Tworzenie okna...")
    window = MegasolidEditor()
    logging.info("Okno utworzone.")

    logging.info("Resetowanie okna...")
    window.reset()
    logging.info("Okno zresetowane.")

    logging.info("Wyświetlanie okna...")
    window.show()
    logging.info("Okno wyświetlone.")

    logging.info("Uruchamianie aplikacji...")
    app.exec()
    logging.info("Aplikacja zakończyła działanie.")
