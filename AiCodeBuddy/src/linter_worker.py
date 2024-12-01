from PyQt6.QtCore import QObject, pyqtSignal
import subprocess
import re
import os
import uuid

class LinterWorker(QObject):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, code, flake8_config, repo_path):
        super().__init__()
        self.code = code
        self.flake8_config = flake8_config
        self.repo_path = repo_path

    def run(self):
        """
        Metoda uruchamiana w osobnym wątku, która wykonuje linting kodu.
        """
        temp_file = os.path.abspath(f"temp_script_{uuid.uuid4().hex}.py")

        try:
            # Tworzenie tymczasowego pliku z kodem
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

        finally:
            # Usunięcie pliku tymczasowego dopiero po uruchomieniu lintera
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as cleanup_error:
                    self.error.emit(f"Failed to remove temp file: {cleanup_error}")
