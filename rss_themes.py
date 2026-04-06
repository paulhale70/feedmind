"""
Theme Manager for RSS Reader V2
Provides light and dark mode color schemes.
"""

class Theme:
    """Base theme class with color definitions."""

    def __init__(self, name: str):
        self.name = name

    # Override these in subclasses
    bg_primary = '#FFFFFF'
    bg_secondary = '#F5F5F5'
    bg_tertiary = '#E0E0E0'
    fg_primary = '#212121'
    fg_secondary = '#757575'
    button_bg = '#2196F3'
    button_fg = '#FFFFFF'
    button_active = '#1976D2'
    entry_bg = '#FFFFFF'
    entry_fg = '#212121'
    listbox_bg = '#FFFFFF'
    listbox_fg = '#212121'
    listbox_select_bg = '#2196F3'
    listbox_select_fg = '#FFFFFF'
    text_bg = '#FFFFFF'
    text_fg = '#212121'
    accent_green = '#4CAF50'
    accent_red = '#F44336'
    accent_orange = '#FF9800'
    accent_purple = '#9C27B0'
    accent_pink = '#E91E63'
    accent_cyan = '#00BCD4'
    accent = '#2196F3'  # Primary accent color
    border = '#BDBDBD'


class LightTheme(Theme):
    """Light color theme."""

    def __init__(self):
        super().__init__("Light")

    bg_primary = '#FFFFFF'
    bg_secondary = '#F5F5F5'
    bg_tertiary = '#E0E0E0'
    fg_primary = '#212121'
    fg_secondary = '#757575'
    button_bg = '#2196F3'
    button_fg = '#FFFFFF'
    button_active = '#1976D2'
    entry_bg = '#FFFFFF'
    entry_fg = '#212121'
    listbox_bg = '#FFFFFF'
    listbox_fg = '#212121'
    listbox_select_bg = '#2196F3'
    listbox_select_fg = '#FFFFFF'
    text_bg = '#FFFFFF'
    text_fg = '#212121'
    accent_green = '#4CAF50'
    accent_red = '#F44336'
    accent_orange = '#FF9800'
    accent_purple = '#9C27B0'
    accent_pink = '#E91E63'
    accent_cyan = '#00BCD4'
    accent = '#2196F3'  # Primary accent color
    border = '#BDBDBD'


class DarkTheme(Theme):
    """Dark color theme."""

    def __init__(self):
        super().__init__("Dark")

    bg_primary = '#1E1E1E'
    bg_secondary = '#252525'
    bg_tertiary = '#2D2D2D'
    fg_primary = '#E0E0E0'
    fg_secondary = '#A0A0A0'
    button_bg = '#0D47A1'
    button_fg = '#FFFFFF'
    button_active = '#1565C0'
    entry_bg = '#2D2D2D'
    entry_fg = '#E0E0E0'
    listbox_bg = '#252525'
    listbox_fg = '#E0E0E0'
    listbox_select_bg = '#0D47A1'
    listbox_select_fg = '#FFFFFF'
    text_bg = '#252525'
    text_fg = '#E0E0E0'
    accent_green = '#66BB6A'
    accent_red = '#EF5350'
    accent_orange = '#FFA726'
    accent_purple = '#AB47BC'
    accent_pink = '#EC407A'
    accent_cyan = '#26C6DA'
    accent = '#0D47A1'  # Primary accent color for dark theme
    border = '#424242'


THEMES = {
    'Light': LightTheme(),
    'Dark': DarkTheme()
}


def get_theme(name: str) -> Theme:
    """Get a theme by name."""
    return THEMES.get(name, LightTheme())
