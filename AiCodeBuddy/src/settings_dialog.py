# src/settings_dialog.py

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QLabel, QComboBox, QSpinBox, QPushButton

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ustawienia IDE")
        layout = QVBoxLayout()

        # Opcja automatycznego czyszczenia wklejania
        self.clean_paste_checkbox = QCheckBox("Automatycznie czyść wklejany tekst")
        self.clean_paste_checkbox.setChecked(True)
        layout.addWidget(self.clean_paste_checkbox)

        # Opcja inteligentnego wcięcia
        self.smart_indent_checkbox = QCheckBox("Inteligentne wcięcie")
        self.smart_indent_checkbox.setChecked(True)
        layout.addWidget(self.smart_indent_checkbox)

        # Opcja potwierdzenia usunięcia
        self.confirm_delete_checkbox = QCheckBox("Potwierdzenie przed usunięciem")
        self.confirm_delete_checkbox.setChecked(True)
        layout.addWidget(self.confirm_delete_checkbox)

        # Wybór motywu
        self.theme_label = QLabel("Wybierz motyw:")
        layout.addWidget(self.theme_label)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Jasny", "Ciemny", "Monokai", "Solarized Light", "Solarized Dark"])
        layout.addWidget(self.theme_combo)

        # Wybór czcionki
        self.font_label = QLabel("Wybierz czcionkę:")
        layout.addWidget(self.font_label)
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Consolas", "Courier New", "DejaVu Sans Mono", "Segoe UI", "Monospace"])
        layout.addWidget(self.font_combo)

        # Regulacja rozmiaru czcionki
        self.font_size_label = QLabel("Rozmiar czcionki:")
        layout.addWidget(self.font_size_label)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(12)
        layout.addWidget(self.font_size_spin)

        # Opcja auto-save
        self.auto_save_checkbox = QCheckBox("Włącz auto-save (co 5 minut)")
        self.auto_save_checkbox.setChecked(True)
        layout.addWidget(self.auto_save_checkbox)

        # Tryb skupienia
        self.focus_mode_checkbox = QCheckBox("Tryb skupienia (ukryj panele boczne)")
        self.focus_mode_checkbox.setChecked(False)
        layout.addWidget(self.focus_mode_checkbox)

        # Autouzupełnianie na żądanie
        self.autocomplete_on_demand_checkbox = QCheckBox("Autouzupełnianie na żądanie (Ctrl+Spacja)")
        self.autocomplete_on_demand_checkbox.setChecked(False)
        layout.addWidget(self.autocomplete_on_demand_checkbox)

        # Przycisk Zapisz
        save_button = QPushButton("Zapisz")
        save_button.clicked.connect(self.accept)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def get_settings(self):
        """
        Zwraca aktualne ustawienia z dialogu.
        """
        return {
            'clean_paste': self.clean_paste_checkbox.isChecked(),
            'smart_indent': self.smart_indent_checkbox.isChecked(),
            'confirm_delete': self.confirm_delete_checkbox.isChecked(),
            'theme': self.theme_combo.currentText(),
            'font_size': self.font_size_spin.value(),
            'auto_save': self.auto_save_checkbox.isChecked(),
            'focus_mode': self.focus_mode_checkbox.isChecked(),
            'autocomplete_on_demand': self.autocomplete_on_demand_checkbox.isChecked(),
            'font_family': self.font_combo.currentText(),

        }
