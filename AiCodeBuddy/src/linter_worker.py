# src/linter_worker.py

from PyQt6.QtCore import QObject, pyqtSignal
import subprocess
import re

class LinterWorker(QObject):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, code, flake8_config, repo_path):
        super().__init__()
    def __init__(self, code, flake8_config, repo_path):
        super().__init__()
        self.code = code
        self.flake8_config = flake8_config
        self.repo_path = repo_path

    def run(self):
        """
        Metoda uruchamiana w osobnym wątku, która wykonuje linting kodu.
        """
        try:
            # Tworzenie tymczasowego pliku z kodem
            temp_file = "temp_script.py"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(self.code)

            # Przygotowanie argumentów dla flake8
            args = ['flake8', temp_file]
            if self.flake8_config:
                args += ['--config', self.flake8_config]
            # Uruchomienie lintera
            result = subprocess.run(args, capture_output=True, text=True, cwd=self.repo_path)
            output = result.stdout
            errors = []

            # Parsowanie wyników lintera
            for line in output.strip().split('\n'):
                if line:
                    match = re.match(rf"{re.escape(temp_file)}:(\d+):\d+:\s+(.*)", line)
                    if match:
                        line_num = int(match.group(1)) - 1
                        message = match.group(2)
                        errors.append((line_num, message))

            # Emisja sygnału z błędami
            self.finished.emit(errors)
        except Exception as e:
            # Emisja sygnału błędu w razie niepowodzenia
            self.error.emit(str(e))