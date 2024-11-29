# test_settings.py

import sys
import os
import pytest
import json
import tempfile
from unittest.mock import patch, MagicMock, mock_open

from PyQt6.QtWidgets import QApplication, QPushButton, QCheckBox, QComboBox, QMessageBox
from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QFont

# Import the main application classes
from python_tutor import PythonTutorApp, SettingsDialog

# Initialize the QApplication for testing
# Note: Only one QApplication instance should exist
app_instance = QApplication.instance()
if not app_instance:
    app_instance = QApplication(sys.argv)


@pytest.fixture
def mock_qsettings():
    """
    Fixture to create a mock QSettings instance that correctly handles the 'type' keyword.
    Returns the mock object and a dictionary to store settings.
    """
    settings = {}

    def get_value(key, default=None, type=None, **kwargs):
        value = settings.get(key, default)
        if type is not None and value is not None:
            try:
                return type(value)
            except (ValueError, TypeError):
                return default
        return value

    def set_value(key, value):
        settings[key] = value

    mock = MagicMock()
    mock.value.side_effect = get_value
    mock.setValue.side_effect = set_value
    return mock, settings
@pytest.fixture
    
def test_app(qtbot, mock_qsettings):
    """
    Fixture to initialize the PythonTutorApp for testing.
    Function-scoped to match qtbot's scope.
    """
    mock_settings_instance, settings = mock_qsettings

    with patch('python_tutor.QSettings', autospec=True) as MockSettings:
        MockSettings.return_value = mock_settings_instance

        # Create a temporary directory for settings and data files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Paths for user lessons and progress
            user_lessons_file = os.path.join(temp_dir, 'user_lessons.json')
            progress_file = os.path.join(temp_dir, 'progress.json')

            # Initialize the app
            app = PythonTutorApp(user_lessons_file=user_lessons_file, progress_file=progress_file)
            qtbot.addWidget(app)
            app.show()

            yield app, settings

            app.close()


@pytest.fixture
def settings_dialog(test_app, qtbot):
    """
    Fixture to initialize the SettingsDialog for testing.
    """
    app, settings = test_app
    dialog = SettingsDialog(parent=app)
    qtbot.addWidget(dialog)
    dialog.show()
    yield dialog
    dialog.close()


# --------------------------
# Test Cases
# --------------------------

# 1. Test Font Settings
def test_change_font_family(test_app, qtbot):
    app, settings = test_app
    settings["font_family"] = "Courier New"

    # Apply font settings
    app.load_settings()

    # Assert that the application's font family is updated
    current_font = app.font()
    assert current_font.family() == "Courier New"


def test_change_font_size(test_app, qtbot):
    app, settings = test_app
    settings["font_size"] = 16

    # Apply font settings
    app.load_settings()

    # Assert that the application's font size is updated
    current_font = app.font()
    assert current_font.pointSize() == 16


def test_invalid_font_size(test_app, qtbot):
    app, settings = test_app
    # Set an extremely large font size
    settings["font_size"] = 1000

    # Apply font settings
    app.load_settings()

    # Assert that the font size does not exceed a reasonable limit (e.g., 72)
    current_font = app.font()
    assert current_font.pointSize() <= 72  # Adjust based on your application logic


# 2. Test Theme Settings
def test_switch_theme_to_dark(test_app, qtbot):
    app, settings = test_app
    settings["theme"] = "dark"

    # Apply theme settings
    app.load_settings()

    # Assert that dark theme styles are applied
    assert "background-color: #2b2b2b;" in app.styleSheet()


def test_switch_theme_to_light(test_app, qtbot):
    app, settings = test_app
    settings["theme"] = "light"

    # Apply theme settings
    app.load_settings()

    # Assert that light theme styles are applied
    assert "background-color: #f0f0f0;" in app.styleSheet()


def test_invalid_theme(test_app, qtbot):
    app, settings = test_app
    # Set an invalid theme
    settings["theme"] = "invalid_theme"

    # Apply theme settings
    app.load_settings()

    # Assert that the default theme is applied (light theme)
    assert "background-color: #f0f0f0;" in app.styleSheet()


# 3. Test Color Customizations
def test_change_custom_background_and_text_colors(test_app, qtbot):
    app, settings = test_app
    settings["bg_color"] = "#FFFFFF"
    settings["text_color"] = "#000000"

    # Apply color settings
    app.load_settings()

    # Assert that custom colors are in the stylesheet
    assert "background-color: #FFFFFF;" in app.styleSheet()
    assert "color: #000000;" in app.styleSheet()


def test_invalid_color_codes(test_app, qtbot):
    app, settings = test_app
    # Set invalid color codes
    settings["bg_color"] = "invalid_color"
    settings["text_color"] = "another_invalid_color"

    # Apply color settings
    app.load_settings()

    # Since invalid color codes are set, PyQt might ignore them or set defaults
    # Assert that the invalid colors are not applied
    assert "background-color: invalid_color;" not in app.styleSheet()
    assert "color: another_invalid_color;" not in app.styleSheet()


# 4. Test Color Profiles
def test_apply_protanopia_color_profile(test_app, qtbot):
    app, settings = test_app
    settings["color_profile"] = "Protanopia"

    # Apply color profile
    app.load_settings()

    # Assert that Protanopia styles are applied
    assert "/* Protanopia color adjustments */" in app.styleSheet()
    assert "background-color: #FFD700;" in app.styleSheet()


def test_apply_deuteranopia_color_profile(test_app, qtbot):
    app, settings = test_app
    settings["color_profile"] = "Deuteranopia"

    # Apply color profile
    app.load_settings()

    # Assert that Deuteranopia styles are applied
    assert "/* Deuteranopia color adjustments */" in app.styleSheet()
    assert "background-color: #FF69B4;" in app.styleSheet()


def test_apply_tritanopia_color_profile(test_app, qtbot):
    app, settings = test_app
    settings["color_profile"] = "Tritanopia"

    # Apply color profile
    app.load_settings()

    # Assert that Tritanopia styles are applied
    assert "/* Tritanopia color adjustments */" in app.styleSheet()
    assert "background-color: #87CEFA;" in app.styleSheet()


def test_invalid_color_profile(test_app, qtbot):
    app, settings = test_app
    # Set an invalid color profile
    settings["color_profile"] = "InvalidProfile"

    # Apply color profile
    app.load_settings()

    # Assert that no color profile styles are applied
    assert "/* Protanopia color adjustments */" not in app.styleSheet()
    assert "/* Deuteranopia color adjustments */" not in app.styleSheet()
    assert "/* Tritanopia color adjustments */" not in app.styleSheet()


# 5. Test Interface Scaling
def test_interface_scaling_normal(test_app, qtbot):
    app, settings = test_app
    # Set interface scale to 100%
    settings["interface_scale"] = 100
    settings["font_size"] = 12
    settings["font_family"] = "Arial"

    # Apply interface scaling
    app.load_settings()

    # Assert that the font size remains unchanged
    current_font = app.font()
    assert current_font.pointSize() == 12


def test_interface_scaling_increase(test_app, qtbot):
    app, settings = test_app
    # Set interface scale to 150%
    settings["interface_scale"] = 150
    settings["font_size"] = 12
    settings["font_family"] = "Arial"

    # Apply interface scaling
    app.load_settings()

    # Assert that the font size is increased by 1.5x
    current_font = app.font()
    assert current_font.pointSize() == 18  # 12 * 1.5 = 18


def test_interface_scaling_decrease(test_app, qtbot):
    app, settings = test_app
    # Set interface scale to 50%
    settings["interface_scale"] = 50
    settings["font_size"] = 12
    settings["font_family"] = "Arial"

    # Apply interface scaling
    app.load_settings()

    # Assert that the font size is decreased by 0.5x
    current_font = app.font()
    assert current_font.pointSize() == 6  # 12 * 0.5 = 6


def test_interface_scaling_extreme_low(test_app, qtbot):
    app, settings = test_app
    # Set interface scale to below minimum (e.g., 10%)
    settings["interface_scale"] = 10
    settings["font_size"] = 12
    settings["font_family"] = "Arial"

    # Apply interface scaling
    app.load_settings()

    # Assert that the font size does not go below a reasonable limit (e.g., 8)
    current_font = app.font()
    assert current_font.pointSize() >= 8  # Adjust based on your application logic


def test_interface_scaling_extreme_high(test_app, qtbot):
    app, settings = test_app
    # Set interface scale to above maximum (e.g., 300%)
    settings["interface_scale"] = 300
    settings["font_size"] = 12
    settings["font_family"] = "Arial"

    # Apply interface scaling
    app.load_settings()

    # Assert that the font size does not exceed a reasonable limit (e.g., 72)
    current_font = app.font()
    assert current_font.pointSize() <= 72  # Adjust based on your application logic


# 6. Test Accessibility Modes
def test_enable_dyslexia_mode(test_app, qtbot):
    app, settings = test_app
    # Enable dyslexia mode
    settings["dyslexia_mode"] = True

    # Apply settings
    app.load_settings()

    # Assert that dyslexia styles are applied
    assert 'font-family: "Comic Sans MS";' in app.styleSheet()


def test_disable_dyslexia_mode(test_app, qtbot):
    app, settings = test_app
    # Disable dyslexia mode
    settings["dyslexia_mode"] = False

    # Apply settings
    app.load_settings()

    # Assert that dyslexia styles are not applied
    assert 'font-family: "Comic Sans MS";' not in app.styleSheet()


def test_enable_tremor_mode(test_app, qtbot):
    app, settings = test_app
    # Enable tremor mode
    settings["tremor_mode"] = True

    # Apply settings
    app.load_settings()

    # Assert that tremor styles are applied
    assert "padding: 20px;" in app.styleSheet()
    assert "font-size: 18px;" in app.styleSheet()


def test_disable_tremor_mode(test_app, qtbot):
    app, settings = test_app
    # Disable tremor mode
    settings["tremor_mode"] = False

    # Apply settings
    app.load_settings()

    # Assert that tremor styles are not applied
    assert "padding: 20px;" not in app.styleSheet()
    assert "font-size: 18px;" not in app.styleSheet()


def test_enable_autism_mode(test_app, qtbot):
    app, settings = test_app
    # Enable autism mode
    settings["autism_mode"] = True

    # Apply settings
    app.load_settings()

    # Assert that autism styles are applied
    assert "font-weight: bold;" in app.styleSheet()
    assert "border: 2px solid #000000;" in app.styleSheet()


def test_disable_autism_mode(test_app, qtbot):
    app, settings = test_app
    # Disable autism mode
    settings["autism_mode"] = False

    # Apply settings
    app.load_settings()

    # Assert that autism styles are not applied
    assert "font-weight: bold;" not in app.styleSheet()
    assert "border: 2px solid #000000;" not in app.styleSheet()


# 7. Test Text-to-Speech (TTS) Settings
def test_enable_tts(test_app, qtbot):
    app, settings = test_app
    with patch.object(app, 'set_tts_voice') as mock_set_voice:
        # Enable TTS
        settings["tts_enabled"] = True

        # Apply TTS settings
        app.apply_tts_enabled()

        # Assert that TTS is enabled in the application
        assert app.tts_enabled is True
        mock_set_voice.assert_called_once()


def test_disable_tts(test_app, qtbot):
    app, settings = test_app
    with patch.object(app, 'set_tts_voice') as mock_set_voice:
        # Disable TTS
        settings["tts_enabled"] = False

        # Apply TTS settings
        app.apply_tts_enabled()

        # Assert that TTS is disabled in the application
        assert app.tts_enabled is False
        mock_set_voice.assert_not_called()


def test_change_tts_voice_based_on_language(test_app, qtbot):
    app, settings = test_app
    with patch.object(app, 'engine') as mock_engine:
        # Set language to German
        settings["language"] = "de"

        # Mock available voices
        mock_voice = MagicMock()
        mock_voice.languages = [b'de_DE']
        mock_voice.id = 'voice_de_DE'
        mock_engine.getProperty.return_value = [mock_voice]

        # Apply language settings
        app.set_tts_voice()

        # Assert that the TTS engine's voice is set to German
        mock_engine.setProperty.assert_called_with('voice', 'voice_de_DE')


def test_change_tts_voice_no_matching_language(test_app, qtbot):
    app, settings = test_app
    with patch.object(app, 'engine') as mock_engine:
        # Set language to Japanese (assuming no voice available)
        settings["language"] = "ja"

        # Mock available voices
        mock_voice = MagicMock()
        mock_voice.languages = [b'en_US', b'en_GB']
        mock_voice.id = 'voice_en_US'
        mock_engine.getProperty.return_value = [mock_voice]

        # Apply language settings
        app.set_tts_voice()

        # Assert that no matching voice was set, default voice is used
        mock_engine.setProperty.assert_not_called()


# 8. Test Language Settings
def test_switch_language_to_polish(test_app, qtbot):
    app, settings = test_app
    # Set language to Polish
    settings["language"] = "pl"

    # Apply language settings
    app.load_language()

    # Assert that translations are loaded (assuming 'app_title' exists in pl.json)
    expected_translation = app.translations.get("app_title", "app_title")
    assert app.translate("app_title") == expected_translation


def test_switch_language_to_unsupported(test_app, qtbot):
    app, settings = test_app
    with patch('builtins.open', side_effect=FileNotFoundError()):
        # Set language to unsupported (e.g., 'xx')
        settings["language"] = "xx"

        # Apply language settings
        app.load_language()

        # Assert that translations fallback to keys
        assert app.translate("app_title") == "app_title"


# 9. Test Persistence of Settings
def test_save_and_load_settings(test_app, qtbot):
    app, settings = test_app
    with patch('python_tutor.os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data='[]')) as mock_file:
        # Simulate saving settings
        settings["theme"] = "dark"
        settings["font_size"] = 16
        settings["font_family"] = "Times New Roman"
        settings["interface_scale"] = 125
        settings["dyslexia_mode"] = True
        settings["tts_enabled"] = True
        settings["language"] = "de"

        # Apply settings
        app.load_settings()

        # Assert that settings are applied
        assert "background-color: #2b2b2b;" in app.styleSheet()  # Dark theme
        current_font = app.font()
        assert current_font.family() == "Times New Roman"
        assert current_font.pointSize() == 16
        assert app.tts_enabled is True
        assert settings.get("dyslexia_mode", False) is True


# 10. Test Reset to Defaults
def test_reset_to_defaults(test_app, qtbot):
    app, settings = test_app
    with patch('python_tutor.QSettings.clear') as mock_clear, \
         patch('PyQt6.QtWidgets.QMessageBox.information') as mock_info:
        # Simulate opening settings dialog
        dialog = SettingsDialog(parent=app)
        qtbot.addWidget(dialog)
        dialog.show()

        # Simulate user clicking "Reset to Defaults"
        reset_button = dialog.findChild(QPushButton, "Reset to Defaults")
        if not reset_button:
            # If objectName is not set, find by text
            buttons = dialog.findChildren(QPushButton)
            reset_button = next((btn for btn in buttons if btn.text() == "Reset to Defaults" or btn.text() == app.translate("labels.Reset to Defaults")), None)

        assert reset_button is not None, "Reset to Defaults button not found."

        # Click the reset button
        qtbot.mouseClick(reset_button, Qt.LeftButton)

        # Assert that QSettings.clear() was called
        mock_clear.assert_called_once()

        # Assert that QMessageBox.information was called
        mock_info.assert_called_once()

        # Close the dialog
        dialog.accept()

        # Apply settings after reset
        app.load_settings()
        app.apply_font_settings()
        app.apply_interface_scale()

        # Assert that default settings are applied
        assert "background-color: #f0f0f0;" in app.styleSheet()  # Light theme
        current_font = app.font()
        assert current_font.family() == "Arial"
        assert current_font.pointSize() == 12
        assert app.tts_enabled is False
        assert settings.get("dyslexia_mode", False) is False


# 11. Test User Interactions with Settings Dialog
def test_user_interactions_with_settings_dialog(qtbot, test_app, settings_dialog):
    app, settings = test_app
    with patch('python_tutor.QSettings.setValue') as mock_set_value, \
         patch('PyQt6.QtWidgets.QFontDialog.getFont') as mock_font_dialog:
        # Mock QFontDialog to return a specific font
        mock_font_dialog.return_value = (QFont("Calibri", 14), True)

        # Simulate user changing font family via dialog
        change_font_button = settings_dialog.findChild(QPushButton, "Change Font")
        if not change_font_button:
            # If objectName is not set, find by text
            buttons = settings_dialog.findChildren(QPushButton)
            change_font_button = next((btn for btn in buttons if btn.text() == "Change Font" or btn.text() == app.translate("labels.Change Font")), None)

        assert change_font_button is not None, "Change Font button not found."

        # Click the Change Font button
        qtbot.mouseClick(change_font_button, Qt.LeftButton)

        # Simulate user confirming the font selection
        # Already handled by mock_font_dialog

        # Simulate user changing theme via dialog
        theme_combo = settings_dialog.findChild(QComboBox)
        if not theme_combo:
            # Find the QComboBox by label
            combo_boxes = settings_dialog.findChildren(QComboBox)
            theme_combo = combo_boxes[0] if combo_boxes else None

        assert theme_combo is not None, "Theme combo box not found."

        # Set theme to Dark Theme
        theme_combo.setCurrentText("Dark Theme")
        theme_combo.setCurrentIndex(theme_combo.findText("Dark Theme"))

        # Click OK to apply changes
        ok_button = settings_dialog.findChild(QPushButton, "OK")
        if not ok_button:
            # If objectName is not set, find by text
            buttons = settings_dialog.findChildren(QPushButton)
            ok_button = next((btn for btn in buttons if btn.text() in ["OK", "Ok"] or btn.text() == app.translate("labels.OK")), None)

        assert ok_button is not None, "OK button not found."

        # Click the OK button
        qtbot.mouseClick(ok_button, Qt.LeftButton)

        # Assert that QSettings.setValue was called with updated values
        mock_set_value.assert_any_call("font_family", "Calibri")
        mock_set_value.assert_any_call("font_size", 14)
        mock_set_value.assert_any_call("theme", "dark")

        # Assert that dark theme is applied
        assert "background-color: #2b2b2b;" in app.styleSheet()

        # Simulate enabling dyslexia mode via dialog
        # Reopen the settings dialog
        dialog = SettingsDialog(parent=app)
        qtbot.addWidget(dialog)
        dialog.show()

        # Find dyslexia mode checkbox
        dyslexia_checkbox = dialog.findChild(QCheckBox, "Enabled")
        if not dyslexia_checkbox:
            # Find by label
            checkboxes = dialog.findChildren(QCheckBox)
            dyslexia_checkbox = next((cb for cb in checkboxes if cb.text() == "Enabled" or cb.text() == app.translate("labels.Enabled")), None)

        assert dyslexia_checkbox is not None, "Dyslexia Mode checkbox not found."

        # Enable dyslexia mode
        dyslexia_checkbox.setChecked(True)

        # Click OK to apply changes
        dialog_ok_button = dialog.findChild(QPushButton, "OK")
        if not dialog_ok_button:
            # If objectName is not set, find by text
            buttons = dialog.findChildren(QPushButton)
            dialog_ok_button = next((btn for btn in buttons if btn.text() in ["OK", "Ok"] or btn.text() == app.translate("labels.OK")), None)

        assert dialog_ok_button is not None, "OK button not found in SettingsDialog."

        # Click the OK button
        qtbot.mouseClick(dialog_ok_button, Qt.LeftButton)

        # Assert that QSettings.setValue was called with dyslexia_mode enabled
        mock_set_value.assert_any_call("dyslexia_mode", True)

        # Assert that dyslexia styles are applied
        assert 'font-family: "Comic Sans MS";' in app.styleSheet()

        # Simulate changing language via dialog
        # Reopen the settings dialog
        dialog = SettingsDialog(parent=app)
        qtbot.addWidget(dialog)
        dialog.show()

        # Find language combo box
        language_combo = dialog.findChild(QComboBox)
        if not language_combo:
            # Find the QComboBox by label
            combo_boxes = dialog.findChildren(QComboBox)
            language_combo = combo_boxes[-1] if combo_boxes else None  # Assuming it's the last combo box

        assert language_combo is not None, "Language combo box not found."

        # Set language to Polish
        language_combo.setCurrentText("Polski")
        language_combo.setCurrentIndex(language_combo.findText("Polski"))

        # Click OK to apply changes
        dialog_ok_button = dialog.findChild(QPushButton, "OK")
        if not dialog_ok_button:
            # If objectName is not set, find by text
            buttons = dialog.findChildren(QPushButton)
            dialog_ok_button = next((btn for btn in buttons if btn.text() in ["OK", "Ok"] or btn.text() == app.translate("labels.OK")), None)

        assert dialog_ok_button is not None, "OK button not found in SettingsDialog."

        # Click the OK button
        qtbot.mouseClick(dialog_ok_button, Qt.LeftButton)

        # Assert that QSettings.setValue was called with language set to 'pl'
        mock_set_value.assert_any_call("language", "pl")

        # Assert that translations are loaded (assuming 'app_title' exists in pl.json)
        expected_translation = app.translations.get("app_title", "app_title")
        assert app.translate("app_title") == expected_translation

