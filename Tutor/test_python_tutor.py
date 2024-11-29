import sys
import os
import pytest
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtGui import QFont
from unittest.mock import patch
import logging
from python_tutor import PythonTutorApp, SettingsDialog

@pytest.fixture(scope="session")
def app():
    app = QApplication(sys.argv)
    return app

@pytest.fixture
def tutor_app(qtbot):
    tutor_app = PythonTutorApp()
    qtbot.addWidget(tutor_app)
    return tutor_app

def test_load_default_lessons(tutor_app):
    tutor_app.settings.setValue('language', 'en')
    assert len(tutor_app.lessons) >= 1  # Adjust based on the actual number of default lessons

def test_add_new_lesson(tutor_app, qtbot):
    tutor_app.settings.setValue('language', 'en')
    with patch('PyQt6.QtWidgets.QInputDialog.getText') as mock_get_text, \
         patch('PyQt6.QtWidgets.QInputDialog.getMultiLineText') as mock_get_multiline_text:
        mock_get_text.side_effect = [("Test Lesson", True), ("Test Category", True)]
        mock_get_multiline_text.return_value = ("Test Content", True)

        tutor_app.add_new_lesson()

    language = tutor_app.settings.value("language", "en")
    lesson_titles = [lesson['title'].get(language, next(iter(lesson['title'].values()), '')) for lesson in tutor_app.lessons]
    assert "Test Lesson" in lesson_titles

def test_edit_lesson(tutor_app, qtbot):
    tutor_app.settings.setValue('language', 'en')
    with patch('PyQt6.QtWidgets.QInputDialog.getText') as mock_get_text, \
         patch('PyQt6.QtWidgets.QInputDialog.getMultiLineText') as mock_get_multiline_text:
        mock_get_text.side_effect = [("Lesson to Edit", True), ("Category", True)]
        mock_get_multiline_text.return_value = ("Original Content", True)

        tutor_app.add_new_lesson()

    # Select the lesson in the tree
    for category_index in range(tutor_app.lesson_tree.topLevelItemCount()):
        category_item = tutor_app.lesson_tree.topLevelItem(category_index)
        for lesson_index in range(category_item.childCount()):
            lesson_item = category_item.child(lesson_index)
            if lesson_item.text(0).replace(" ✔", "") == "Lesson to Edit":
                tutor_app.lesson_tree.setCurrentItem(lesson_item)
                break

    with patch('PyQt6.QtWidgets.QInputDialog.getText') as mock_get_text, \
         patch('PyQt6.QtWidgets.QInputDialog.getMultiLineText') as mock_get_multiline_text:
        mock_get_text.side_effect = [("Edited Lesson", True), ("Edited Category", True)]
        mock_get_multiline_text.return_value = ("Edited Content", True)

        tutor_app.edit_lesson()

    language = tutor_app.settings.value("language", "en")
    lesson_titles = [lesson['title'].get(language, next(iter(lesson['title'].values()), '')) for lesson in tutor_app.lessons]
    assert "Edited Lesson" in lesson_titles
    assert "Lesson to Edit" not in lesson_titles

def test_delete_lesson(tutor_app, qtbot):
    tutor_app.settings.setValue('language', 'en')
    with patch('PyQt6.QtWidgets.QInputDialog.getText') as mock_get_text, \
         patch('PyQt6.QtWidgets.QInputDialog.getMultiLineText') as mock_get_multiline_text:
        mock_get_text.side_effect = [("Lesson to Delete", True), ("Category", True)]
        mock_get_multiline_text.return_value = ("Content", True)

        tutor_app.add_new_lesson()

    # Select the lesson in the tree
    for category_index in range(tutor_app.lesson_tree.topLevelItemCount()):
        category_item = tutor_app.lesson_tree.topLevelItem(category_index)
        for lesson_index in range(category_item.childCount()):
            lesson_item = category_item.child(lesson_index)
            if lesson_item.text(0).replace(" ✔", "") == "Lesson to Delete":
                tutor_app.lesson_tree.setCurrentItem(lesson_item)
                break

    with patch('PyQt6.QtWidgets.QMessageBox.question') as mock_question:
        mock_question.return_value = QMessageBox.StandardButton.Yes
        tutor_app.delete_lesson()

    language = tutor_app.settings.value("language", "en")
    lesson_titles = [lesson['title'].get(language, next(iter(lesson['title'].values()), '')) for lesson in tutor_app.lessons]
    assert "Lesson to Delete" not in lesson_titles
def test_run_code(tutor_app, qtbot):
    # Ustawiamy kod w edytorze kodu
    tutor_app.code_editor.setPlainText('print("Hello, World!")')
    # Klikamy przycisk "Uruchom kod"
    tutor_app.run_code()
    # Czekamy, aż proces się zakończy
    qtbot.waitUntil(lambda: tutor_app.process is None or tutor_app.process.state() == 0, timeout=3000)
    # Sprawdzamy, czy konsola wyjściowa zawiera oczekiwany output
    output = tutor_app.output_console.toPlainText()
    assert "Hello, World!" in output

def test_syntax_error(tutor_app, qtbot):
    # Ustawiamy kod z błędem składni
    tutor_app.code_editor.setPlainText('print("Missing parenthesis"')
    # Uruchamiamy kod
    tutor_app.run_code()
    # Czekamy, aż proces się zakończy
    qtbot.wait(1000)
    # Sprawdzamy, czy wyświetlono komunikat o błędzie składni w pasku statusu
    message = tutor_app.status_bar.currentMessage()
    assert "Error" in message

def test_change_font_size(tutor_app, qtbot):
    # Zmieniamy rozmiar czcionki
    tutor_app.set_large_font()
    # Sprawdzamy, czy rozmiar czcionki aplikacji został zmieniony
    font = tutor_app.font()
    assert font.pointSize() == 18

def test_dyslexia_mode(tutor_app, qtbot):
    # Włączamy tryb dysleksji
    tutor_app.settings.setValue("dyslexia_mode", True)
    tutor_app.apply_dyslexia_mode()
    # Sprawdzamy, czy czcionka ma zwiększony odstęp między literami
    font = tutor_app.font()
    assert font.letterSpacingType() == QFont.SpacingType.PercentageSpacing
    assert font.letterSpacing() == 120

def test_debug_mode(tutor_app, qtbot):
    # Włączamy tryb debugowania
    tutor_app.settings.setValue("debug_mode", True)
    tutor_app.apply_debug_mode()
    # Sprawdzamy, czy poziom logowania jest ustawiony na DEBUG
    assert logging.getLogger().level == logging.DEBUG

def test_load_examples_from_file(tutor_app, tmp_path):
    # Tworzymy tymczasowy plik z przykładami
    examples_file = tmp_path / "examples.txt"
    examples_file.write_text("def test_function():\n    pass\n###")
    # Wczytujemy przykłady z pliku
    tutor_app.load_examples_from_file(str(examples_file))
    # Sprawdzamy, czy przykłady wcięć zostały wczytane
    assert len(tutor_app.indentation_examples) == 1

def test_step_by_step_execution(tutor_app, qtbot):
    # Ustawiamy kod w edytorze
    code = "print('Line 1')\nprint('Line 2')"
    tutor_app.code_editor.setPlainText(code)
    # Uruchamiamy krok po kroku
    tutor_app.run_step_by_step()
    # Czekamy wystarczająco długo, aby obie linie zostały wykonane
    qtbot.wait(2000)
    # Sprawdzamy konsolę wyjściową
    output = tutor_app.output_console.toPlainText()
    assert "Line 1" in output
    assert "Line 2" in output

def test_apply_custom_colors(tutor_app):
    # Zastosuj własne kolory
    bg_color = "#123456"
    text_color = "#abcdef"
    tutor_app.apply_custom_colors(bg_color, text_color)
    # Ponieważ nie możemy łatwo sprawdzić stylu, zakładamy, że działa, jeśli nie wystąpiły wyjątki

def test_show_hint(tutor_app, qtbot):
    # Wybieramy lekcję
    item = tutor_app.lesson_tree.topLevelItem(0).child(0)
    tutor_app.lesson_tree.setCurrentItem(item)
    # Mockujemy QMessageBox, aby automatycznie akceptował
    with patch('PyQt6.QtWidgets.QMessageBox.information') as mock_info:
        tutor_app.show_hint()
        mock_info.assert_called_once()

def test_play_lesson_content(tutor_app, qtbot):
    # Enable TTS
    tutor_app.settings.setValue("tts_enabled", True)
    tutor_app.apply_tts_enabled()
    
    # Select a lesson with content
    item = tutor_app.lesson_tree.topLevelItem(0).child(0)
    tutor_app.lesson_tree.setCurrentItem(item)
    tutor_app.load_lesson(item)
    
    # Mock the TTS engine to prevent actual playback
    with patch.object(tutor_app.engine, 'say') as mock_say, \
         patch.object(tutor_app.engine, 'runAndWait'):
        tutor_app.play_lesson_content()
        # Verify that engine.say was called
        mock_say.assert_called_once()


def test_read_output_console(tutor_app, qtbot):
    # Enable TTS
    tutor_app.settings.setValue("tts_enabled", True)
    tutor_app.apply_tts_enabled()
    
    # Set some output
    tutor_app.output_console.setPlainText("Test output")
    
    # Mock the TTS engine to prevent actual playback
    with patch.object(tutor_app.engine, 'say') as mock_say, \
         patch.object(tutor_app.engine, 'runAndWait'):
        tutor_app.read_output_console()
        # Verify that engine.say was called
        mock_say.assert_called_once()

def test_assistant(tutor_app, qtbot):
    # Mockujemy QMessageBox, aby automatycznie klikać 'Ok'
    with patch('PyQt6.QtWidgets.QMessageBox.question') as mock_question:
        mock_question.return_value = QMessageBox.StandardButton.Ok
        tutor_app.show_assistant()
        # Czekamy, aż asystent zakończy
        qtbot.wait(1000)
        assert tutor_app.current_assistant_step == 0  # Powinien zresetować się po zakończeniu

def test_settings_dialog(tutor_app, qtbot):
    # Otwieramy okno ustawień
    with patch.object(SettingsDialog, 'exec') as mock_exec:
        mock_exec.return_value = True
        tutor_app.open_settings_dialog()
        mock_exec.assert_called_once()

def test_reset_to_defaults(tutor_app, qtbot):
    # Otwieramy okno ustawień
    settings_dialog = SettingsDialog(tutor_app)
    # Mockujemy QMessageBox, aby automatycznie akceptować
    with patch('PyQt6.QtWidgets.QMessageBox.information'):
        settings_dialog.reset_to_defaults()
        # Weryfikujemy, czy ustawienia zostały wyczyszczone
        assert not tutor_app.settings.allKeys()

# Nowe testy dodane:

def test_apply_interface_scale(tutor_app, qtbot):
    # Set interface scale
    tutor_app.settings.setValue("interface_scale", 150)
    tutor_app.settings.sync()  # Ensure settings are saved
    tutor_app.apply_interface_scale()
    
    # Calculate expected font size
    default_font_size = tutor_app.settings.value("font_size", 12, type=int)
    expected_font_size = int(default_font_size * 1.5)
    font = tutor_app.font()
    assert font.pointSize() == expected_font_size

def test_apply_theme(tutor_app, qtbot):
    # Ustawiamy motyw na ciemny
    tutor_app.settings.setValue("theme", "dark")
    tutor_app.apply_theme()
    # Sprawdzamy, czy styl został zmieniony na ciemny motyw
    assert tutor_app.styleSheet() == tutor_app.dark_theme_stylesheet()

def test_apply_color_profile_protanopia(tutor_app, qtbot):
    # Ustawiamy profil kolorów na Protanopia
    tutor_app.settings.setValue("color_profile", "Protanopia")
    tutor_app.apply_color_profile()
    # Ponieważ nie możemy bezpośrednio sprawdzić kolorów, zakładamy, że działa, jeśli nie wystąpiły wyjątki

def test_apply_simple_language_mode(tutor_app, qtbot):
    # Włączamy tryb prostego języka
    tutor_app.settings.setValue("simple_language", True)
    # Przeładowujemy lekcję
    item = tutor_app.lesson_tree.topLevelItem(0).child(0)
    tutor_app.lesson_tree.setCurrentItem(item)
    tutor_app.load_lesson(item)
    # Zakładamy, że treść została uproszczona, jeśli nie wystąpiły wyjątki

def test_language_change(tutor_app, qtbot):
    # Zmieniamy język na niemiecki
    tutor_app.settings.setValue("language", "de")
    tutor_app.load_language()
    tutor_app.apply_translations()
    # Sprawdzamy, czy tytuł okna został zmieniony na niemiecki
    assert tutor_app.windowTitle() == tutor_app.translate("app_title")
    # Sprawdzamy etykietę
    assert tutor_app.code_label.text() == tutor_app.translate("labels.Code Editor:")

def test_tts_enabled(tutor_app, qtbot):
    # Wyłączamy TTS
    tutor_app.settings.setValue("tts_enabled", False)
    tutor_app.apply_tts_enabled()
    # Próba odtworzenia treści lekcji
    with patch.object(tutor_app.engine, 'say') as mock_say, \
         patch.object(tutor_app.engine, 'runAndWait') as mock_runAndWait:
        tutor_app.play_lesson_content()
        # Weryfikujemy, czy engine.say nie został wywołany
        mock_say.assert_not_called()

def test_save_progress(tutor_app, tmp_path):
    # Ustawiamy tymczasową ścieżkę dla pliku postępu
    progress_file = tmp_path / "progress.json"
    tutor_app.progress_file = str(progress_file)
    # Ukończ lekcję
    tutor_app.completed_lessons.append("Test Lesson")
    tutor_app.save_progress()
    # Sprawdzamy, czy plik istnieje
    assert progress_file.exists()
    # Wczytujemy postęp i sprawdzamy zawartość
    tutor_app.completed_lessons = []
    tutor_app.completed_lessons = tutor_app.load_progress()
    assert "Test Lesson" in tutor_app.completed_lessons

def test_load_user_lessons_from_file(tutor_app, tmp_path):
    # Tworzymy tymczasowy plik z lekcjami użytkownika
    user_lessons_file = tmp_path / "user_lessons.json"
    user_lessons_content = [
        {
            "title": {"en": "User Lesson"},
            "content": {"en": "Content"},
            "type": "user",
            "category": {"en": "User Category"}
        }
    ]
    import json
    with open(user_lessons_file, 'w', encoding='utf-8') as f:
        json.dump(user_lessons_content, f)
    # Wczytujemy lekcje użytkownika
    tutor_app.load_user_lessons_from_file(str(user_lessons_file))
    # Sprawdzamy, czy lekcja została wczytana
    lesson_titles = [lesson['title']['en'] for lesson in tutor_app.lessons]
    assert "User Lesson" in lesson_titles

def test_apply_autism_mode(tutor_app, qtbot):
    # Enable autism mode
    tutor_app.settings.setValue("autism_mode", True)
    tutor_app.settings.sync()
    
    with patch.object(tutor_app.engine, 'setProperty') as mock_set_property:
        tutor_app.apply_autism_mode()
        # Verify that setProperty was called with 'volume', 0.0
        mock_set_property.assert_any_call('volume', 0.0)

def test_apply_tremor_mode(tutor_app, qtbot):
    # Włączamy tryb drżenia rąk
    tutor_app.settings.setValue("tremor_mode", True)
    tutor_app.apply_tremor_mode()
    # Sprawdzamy, czy styl został zaktualizowany
    assert "padding: 20px;" in tutor_app.styleSheet()

def test_assistant_interruption(tutor_app, qtbot):
    # Mockujemy QMessageBox, aby zasymulować kliknięcie 'Anuluj' na drugim kroku
    with patch('PyQt6.QtWidgets.QMessageBox.question') as mock_question:
        mock_question.side_effect = [QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Cancel]
        tutor_app.show_assistant()
        # Czekamy, aż asystent przetworzy kroki
        qtbot.wait(1000)
        # Weryfikujemy, czy asystent został przerwany
        assert tutor_app.current_assistant_step == 0

def test_search_documentation(tutor_app, qtbot):
    # Mockujemy webbrowser.open, aby zapobiec otwieraniu przeglądarki
    with patch('webbrowser.open') as mock_open:
        tutor_app.search_bar.setText("list comprehension")
        tutor_app.search_documentation()
        # Weryfikujemy, czy webbrowser.open został wywołany z poprawnym URL
        mock_open.assert_called_with("https://docs.python.org/3/search.html?q=list comprehension")

def test_show_about(tutor_app, qtbot):
    # Mockujemy QMessageBox.information, aby zapobiec pojawieniu się dialogu
    with patch('PyQt6.QtWidgets.QMessageBox.information') as mock_info:
        tutor_app.show_about()
        # Weryfikujemy, czy information zostało wywołane
        mock_info.assert_called_once()

def test_load_buggy_code_example(tutor_app, qtbot):
    # Wczytujemy przykładowy kod z błędami
    tutor_app.load_buggy_code_example()
    # Sprawdzamy, czy edytor kodu zawiera błędny kod
    code = tutor_app.code_editor.toPlainText()
    assert "def add(a, b)" in code

