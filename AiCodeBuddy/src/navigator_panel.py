# src/navigator_panel.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QTabWidget
from PyQt6.QtCore import Qt

class CodeNavigatorPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        self.functions_list_widget = QListWidget()
        self.classes_list_widget = QListWidget()

        self.tab_widget.addTab(self.functions_list_widget, "Funkcje")
        self.tab_widget.addTab(self.classes_list_widget, "Klasy")

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
        self.setMaximumWidth(200)

        # Po kliknięciu na funkcję lub klasę, przenieś kursor do jej definicji
        self.functions_list_widget.itemClicked.connect(self.go_to_function)
        self.classes_list_widget.itemClicked.connect(self.go_to_class)

    def update_symbols(self, symbols):
        """
        Aktualizuje listy funkcji i klas w panelu nawigacji.
        """
        self.functions_list_widget.clear()
        self.classes_list_widget.clear()

        for func_name, line_number in symbols.get('functions', []):
            item = QListWidgetItem(f"{func_name} (linia {line_number + 1})")
            item.setData(Qt.ItemDataRole.UserRole, line_number)
            self.functions_list_widget.addItem(item)

        for class_name, line_number in symbols.get('classes', []):
            item = QListWidgetItem(f"{class_name} (linia {line_number + 1})")
            item.setData(Qt.ItemDataRole.UserRole, line_number)
            self.classes_list_widget.addItem(item)

    def go_to_function(self, item):
        """
        Przenosi kursor w edytorze do wybranej funkcji.
        """
        line_number = item.data(Qt.ItemDataRole.UserRole)
        self.go_to_line(line_number)

    def go_to_class(self, item):
        """
        Przenosi kursor w edytorze do wybranej klasy.
        """
        line_number = item.data(Qt.ItemDataRole.UserRole)
        self.go_to_line(line_number)

    def go_to_line(self, line_number):
        """
        Przenosi kursor w edytorze do określonej linii.
        """
        editor = self.main_window.get_current_editor()
        if editor:
            cursor = editor.textCursor()
            # Ustawiamy pozycję kursora na początek wybranej linii
            block = editor.document().findBlockByNumber(line_number)
            if block.isValid():
                cursor.setPosition(block.position())
                editor.setTextCursor(cursor)
                editor.setFocus()
    def apply_theme(self, theme):
        if theme == 'Ciemny':
            self.setStyleSheet("background-color: #2b2b2b; color: #f8f8f2;")
            self.functions_list_widget.setStyleSheet("background-color: #2b2b2b; color: #f8f8f2;")
            self.classes_list_widget.setStyleSheet("background-color: #2b2b2b; color: #f8f8f2;")
        else:
            self.setStyleSheet("")
            self.functions_list_widget.setStyleSheet("")
            self.classes_list_widget.setStyleSheet("")
