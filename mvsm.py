#!/usr/bin/env python3

import os
import sys
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
VENV_PYTHON = APP_DIR / ".venv" / "bin" / "python"


try:
    from PySide6.QtCore import QProcess, QSettings, Qt, QTimer
    from PySide6.QtGui import QIcon, QTextCursor
    from PySide6.QtWidgets import (
        QApplication,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFileDialog,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QPlainTextEdit,
        QSplitter,
        QTextBrowser,
        QVBoxLayout,
        QWidget,
    )
except ImportError as exc:
    if VENV_PYTHON.exists() and Path(sys.executable) != VENV_PYTHON:
        os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]])

    print(
        "Error: no se encontro PySide6.\n"
        "Instalalo con: sudo apt install python3.12-venv && python3 -m venv .venv && . .venv/bin/activate && python -m pip install PySide6",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc


APP_ICON_PATH = APP_DIR / "assets" / "icons" / "mvsm-512.png"
DESKTOP_FILE_ID = "mvsm"

THEME_MODES = ("system", "light", "dark")


def theme_styles(theme: str) -> str:
    if theme == "dark":
        colors = {
            "window": "#171a1f",
            "surface": "#20252c",
            "surface_alt": "#282e36",
            "input": "#15191e",
            "text": "#f3f4f6",
            "muted": "#b8c0cc",
            "border": "#46515f",
            "border_focus": "#8aa3bd",
            "button": "#2d3540",
            "button_hover": "#394452",
            "button_pressed": "#222a33",
            "disabled": "#737d8a",
            "selection": "#38536e",
            "accent": "#e0aa4f",
        }
    else:
        colors = {
            "window": "#eef1f4",
            "surface": "#f8f9fb",
            "surface_alt": "#ffffff",
            "input": "#ffffff",
            "text": "#111111",
            "muted": "#4a5568",
            "border": "#c9d1db",
            "border_focus": "#8aa3bd",
            "button": "#f4f6f8",
            "button_hover": "#e8edf3",
            "button_pressed": "#dfe6ee",
            "disabled": "#8a94a3",
            "selection": "#c9dced",
            "accent": "#b77900",
        }

    return f"""
QWidget {{ color: {colors['text']}; }}
QWidget#centralWidget {{ background: {colors['window']}; }}
QWidget#bodyWidget {{ background: {colors['surface']}; }}
QLabel {{ color: {colors['text']}; }}
QLabel#hintLabel, QLabel#mutedText, QLabel#fieldName, QLabel#resultTitle {{ color: {colors['muted']}; }}
QLabel#winnerBadge {{ color: {colors['accent']}; }}
QLineEdit, QPlainTextEdit {{
    background: {colors['input']}; color: {colors['text']};
    border: 1px solid {colors['border']}; border-radius: 4px;
    selection-background-color: {colors['selection']}; selection-color: {colors['text']};
}}
QLineEdit {{ padding: 4px 8px; }}
QPlainTextEdit {{ padding: 6px 8px; }}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{ border: 1px solid {colors['border_focus']}; }}
QLineEdit:disabled, QPlainTextEdit:disabled, QComboBox:disabled, QPushButton:disabled {{
    background: {colors['surface_alt']}; color: {colors['disabled']};
}}
QPushButton {{
    background: {colors['button']}; color: {colors['text']};
    border: 1px solid {colors['border']}; border-radius: 6px;
    padding: 6px 12px; min-height: 18px;
}}
QPushButton:hover {{ background: {colors['button_hover']}; border-color: {colors['border_focus']}; }}
QPushButton:pressed {{ background: {colors['button_pressed']}; border-color: {colors['border_focus']}; }}
QComboBox {{
    background: {colors['input']}; color: {colors['text']};
    border: 1px solid {colors['border']}; border-radius: 4px; padding: 2px 8px;
}}
QComboBox QAbstractItemView {{
    background: {colors['input']}; color: {colors['text']};
    selection-background-color: {colors['selection']}; selection-color: {colors['text']};
}}
QFrame#resultPanel, QFrame#filePanel {{
    background: {colors['surface_alt']}; border: 1px solid {colors['border']}; border-radius: 6px;
}}
QDialog#richDialog {{ background: {colors['surface']}; }}
QTextBrowser#richBrowser {{
    background: {colors['input']}; color: {colors['text']};
    border: 1px solid {colors['border']}; border-radius: 6px; padding: 10px;
}}
QToolTip {{ background: {colors['input']}; color: {colors['text']}; border: 1px solid {colors['border']}; }}
"""


DETAIL_FIELDS = (
    "Fichero",
    "Codec vídeo",
    "Formato de píxel",
    "FPS",
    "Codec audio",
    "Bitrate audio",
    "Canales audio",
    "Frecuencia audio",
)

IMPORTANT_FIELDS = (
    "Duración",
    "Tamaño",
    "Resolución",
    "Bitrate total",
    "Bitrate vídeo",
)

VIDEO_CODEC_RANKS = {
    "av1": 100,
    "vp9": 93,
    "hevc": 86,
    "h265": 79,
    "h264": 72,
    "x264": 65,
    "mpeg4": 58,
    "xvid": 51,
    "divx": 44,
    "vp8": 37,
    "mpeg2video": 30,
}

TRANSLATIONS = {
    "es": {
        "language_name": "Espa\u00f1ol",
        "help": "Ayuda",
        "about": "Acerca de",
        "language": "Idioma",
        "theme": "Tema",
        "theme_system": "Sistema",
        "theme_light": "Claro",
        "theme_dark": "Oscuro",
        "browse": "Buscar...",
        "file": "Archivo",
        "file2": "Archivo 2",
        "label_video_codec": "Codec vídeo",
        "label_pix_fmt": "Formato de píxel",
        "label_fps": "FPS",
        "label_audio_codec": "Codec audio",
        "label_audio_bitrate": "Bitrate audio",
        "label_audio_channels": "Canales audio",
        "label_audio_sample_rate": "Frecuencia audio",
        "label_duration": "Duración",
        "label_size": "Tamaño",
        "label_resolution": "Resolución",
        "label_total_bitrate": "Bitrate total",
        "label_video_bitrate": "Bitrate vídeo",
        "label_score": "Puntuación",
        "analyze": "Analizar",
        "clear": "Limpiar",
        "close": "Cerrar",
        "summary": "Resumen",
        "debug_title": "Debug / salida completa",
        "hint": "Arrastra un fichero sobre el campo o usa Buscar. El segundo es opcional para comparar.",
        "video_placeholder": "Arrastra un video o usa Buscar",
        "video2_placeholder": "Opcional: arrastra otro video para comparar",
        "browse_tooltip": "Seleccionar un archivo de video",
        "select_video": "Seleccionar video",
        "no_files_title": "Faltan archivos",
        "no_files": "Indica al menos un fichero de video.",
        "invalid_title": "Archivo no valido",
        "file_not_found": "No existe el fichero:\n{path}",
        "script_not_found_title": "Script no encontrado",
        "script_not_found": "No existe:\n{path}",
        "pending_result": "Resultado pendiente",
        "pending_reason": "Analiza un archivo para ver sus caracteristicas, o dos para compararlos.",
        "single_result": "Archivo analizado.",
        "single_reason": "Se muestran las caracteristicas tecnicas del archivo cargado.",
        "compare_ready": "Comparacion lista.",
        "no_more_details": "Sin motivos adicionales.",
        "process_done": "\nProceso finalizado con codigo {code}.\n",
        "process_error": "\nError al ejecutar el proceso: {error}.\n",
        "help_title": "Ayuda de mvsm",
        "help_html": (
            "<h3>Uso rapido</h3>"
            "<ol>"
            "<li>Arrastra un fichero al primer campo o usa <b>Buscar</b>.</li>"
            "<li>El segundo fichero es opcional y solo sirve para comparar.</li>"
            "<li>Pulsa <b>Analizar</b> para ver la ficha tecnica o la comparacion.</li>"
            "</ol>"
            "<h3>Que muestra</h3>"
            "<ul>"
            "<li><b>Resumen</b>: resultado legible y motivos principales.</li>"
            "<li><b>Tarjeta de archivo</b>: duracion, tamano, resolucion, bitrate y codecs.</li>"
            "<li><b>Debug</b>: salida completa del script por si quieres revisar detalles.</li>"
            "</ul>"
            "<p>Los cambios de idioma afectan a las etiquetas de la interfaz. El analisis siempre se ejecuta localmente con <code>mvsm.sh</code>.</p>"
        ),
        "about_title": "Acerca de mvsm",
        "about_html": (
            "<h3>mvsm</h3>"
            "<p>Herramienta local para inspeccionar videos y comparar su calidad tecnica de forma rapida.</p>"
            "<ul>"
            "<li>Analisis de un fichero o comparacion de dos.</li>"
            "<li>Interfaz Qt6 con arrastre de archivos y selector de idioma.</li>"
            "<li>Resultado resumido y salida detallada del script.</li>"
            "</ul>"
            "<p><b>Licencia:</b> GPL-3.0-or-later.</p>"
            "<p>El proyecto no necesita enviar archivos a ningun servicio externo.</p>"
        ),
    },
    "en": {
        "language_name": "English",
        "help": "Help",
        "about": "About",
        "language": "Language",
        "theme": "Theme",
        "theme_system": "System",
        "theme_light": "Light",
        "theme_dark": "Dark",
        "browse": "Browse...",
        "file": "File",
        "file2": "File 2",
        "label_video_codec": "Video codec",
        "label_pix_fmt": "Pixel format",
        "label_fps": "FPS",
        "label_audio_codec": "Audio codec",
        "label_audio_bitrate": "Audio bitrate",
        "label_audio_channels": "Audio channels",
        "label_audio_sample_rate": "Audio sample rate",
        "label_duration": "Duration",
        "label_size": "Size",
        "label_resolution": "Resolution",
        "label_total_bitrate": "Total bitrate",
        "label_video_bitrate": "Video bitrate",
        "label_score": "Score",
        "analyze": "Analyze",
        "clear": "Clear",
        "close": "Close",
        "summary": "Summary",
        "debug_title": "Debug / full output",
        "hint": "Drag a file onto the field or use Browse. The second one is optional for comparison.",
        "video_placeholder": "Drag a video or use Browse",
        "video2_placeholder": "Optional: drag another video to compare",
        "browse_tooltip": "Select a video file",
        "select_video": "Select video",
        "no_files_title": "Missing files",
        "no_files": "Provide at least one video file.",
        "invalid_title": "Invalid file",
        "file_not_found": "File does not exist:\n{path}",
        "script_not_found_title": "Script not found",
        "script_not_found": "Does not exist:\n{path}",
        "pending_result": "Result pending",
        "pending_reason": "Analyze one file to see its characteristics, or two to compare them.",
        "single_result": "File analyzed.",
        "single_reason": "The technical characteristics of the loaded file are shown.",
        "compare_ready": "Comparison ready.",
        "no_more_details": "No additional reasons.",
        "process_done": "\nProcess finished with code {code}.\n",
        "process_error": "\nError while executing the process: {error}.\n",
        "help_title": "mvsm help",
        "help_html": (
            "<h3>Quick use</h3>"
            "<ol>"
            "<li>Drag a file into the first field or use <b>Browse</b>.</li>"
            "<li>The second file is optional and only used for comparison.</li>"
            "<li>Press <b>Analyze</b> to show the file sheet or the comparison.</li>"
            "</ol>"
            "<h3>What you get</h3>"
            "<ul>"
            "<li><b>Summary</b>: readable result and main reasons.</li>"
            "<li><b>File card</b>: duration, size, resolution, bitrate and codecs.</li>"
            "<li><b>Debug</b>: full script output if you need the raw details.</li>"
            "</ul>"
            "<p>Language changes affect interface labels. Analysis always runs locally through <code>mvsm.sh</code>.</p>"
        ),
        "about_title": "About mvsm",
        "about_html": (
            "<h3>mvsm</h3>"
            "<p>Local tool for inspecting videos and comparing their technical quality quickly.</p>"
            "<ul>"
            "<li>Analyze one file or compare two.</li>"
            "<li>Qt6 interface with drag and drop and language selection.</li>"
            "<li>Concise result summary and detailed script output.</li>"
            "</ul>"
            "<p><b>License:</b> GPL-3.0-or-later.</p>"
            "<p>The project does not send files to any external service.</p>"
        ),
    },
}


class DropLineEdit(QLineEdit):
    def __init__(self, placeholder: str, file_dropped):
        super().__init__()
        self.file_dropped = file_dropped
        self.setPlaceholderText(placeholder)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        files = [url.toLocalFile() for url in urls if url.isLocalFile()]
        if files:
            self.file_dropped(files)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class VideoCompareWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.language = "es"
        self.script_path = Path(__file__).resolve().with_name("mvsm.sh")
        self.process = None
        self.compare_output = ""
        self.analysis_mode = "idle"
        self.settings = QSettings("mvsm", "mvsm")
        self.theme_mode = self.settings.value("theme", "system")
        if self.theme_mode not in THEME_MODES:
            self.theme_mode = "system"
        self.style_hints = QApplication.instance().styleHints()
        self.style_hints.colorSchemeChanged.connect(self.on_system_color_scheme_changed)

        self.setWindowTitle("mvsm")
        if APP_ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PATH)))
        self.resize(1180, 760)
        self.setAcceptDrops(True)

        self.video1_edit = DropLineEdit("Ruta del video", self.handle_dropped_files)
        self.video2_edit = DropLineEdit("Ruta opcional para comparar", self.handle_dropped_files)
        self.video1_edit.textChanged.connect(self.on_input_changed)
        self.video2_edit.textChanged.connect(self.on_input_changed)
        self.path_row_labels = {}

        self.file1_widgets = self.create_file_panel("Archivo")
        self.file2_widgets = self.create_file_panel("Archivo 2")
        self.current_winner = 0
        self.winner_pulse = False
        self.winner_timer = QTimer(self)
        self.winner_timer.setInterval(550)
        self.winner_timer.timeout.connect(self.pulse_winner_badge)

        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        self.result_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.result_label.setStyleSheet("font-size: 18px; font-weight: 700;")

        self.reasons_label = QLabel()
        self.reasons_label.setWordWrap(True)
        self.reasons_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.reasons_label.setObjectName("mutedText")
        self.reasons_label.setStyleSheet("font-size: 13px;")

        result_box = QFrame()
        result_box.setObjectName("resultPanel")
        result_layout = QVBoxLayout(result_box)
        result_layout.setContentsMargins(12, 10, 12, 10)
        result_layout.setSpacing(6)
        self.result_title = QLabel()
        self.result_title.setObjectName("resultTitle")
        self.result_title.setStyleSheet("font-size: 12px; font-weight: 700; letter-spacing: 0;")
        result_layout.addWidget(self.result_title)
        result_layout.addWidget(self.result_label)
        result_layout.addWidget(self.reasons_label)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(180)
        self.output.setPlaceholderText("")

        utility_row = QHBoxLayout()
        utility_row.setSpacing(8)

        self.language_label = QLabel()
        self.language_combo = QComboBox()
        self.language_combo.addItem("")
        self.language_combo.addItem("")
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        self.language_combo.setFixedWidth(140)
        self.theme_label = QLabel()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["", "", ""])
        self.theme_combo.setFixedWidth(140)
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        utility_row.addWidget(self.language_label)
        utility_row.addWidget(self.language_combo)
        utility_row.addWidget(self.theme_label)
        utility_row.addWidget(self.theme_combo)

        utility_row.addStretch(1)

        self.help_button = QPushButton()
        self.help_button.clicked.connect(self.show_help)
        utility_row.addWidget(self.help_button)

        self.about_button = QPushButton()
        self.about_button.clicked.connect(self.show_about)
        utility_row.addWidget(self.about_button)

        self.compare_button = QPushButton()
        self.compare_button.clicked.connect(self.run_compare)

        self.clear_button = QPushButton()
        self.clear_button.clicked.connect(self.clear_all)

        self.close_button = QPushButton()
        self.close_button.clicked.connect(self.close)

        central = QWidget()
        central.setObjectName("centralWidget")
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 10)
        main_layout.setSpacing(0)

        body_widget = QWidget()
        body_widget.setObjectName("bodyWidget")
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(10, 10, 10, 0)
        body_layout.setSpacing(5)

        body_layout.addLayout(utility_row)

        self.hint_label = QLabel()
        self.hint_label.setObjectName("hintLabel")
        self.hint_label.setWordWrap(True)
        self.hint_label.setStyleSheet("font-size: 12px; background: transparent;")
        body_layout.addWidget(self.hint_label)

        path_layout = QGridLayout()
        path_layout.setHorizontalSpacing(8)
        path_layout.setVerticalSpacing(5)
        path_layout.addLayout(self.path_row("Archivo", self.video1_edit), 0, 0)
        path_layout.addLayout(self.path_row("Archivo 2", self.video2_edit), 1, 0)
        body_layout.addLayout(path_layout)

        top_buttons = QHBoxLayout()
        top_buttons.addWidget(self.compare_button)
        top_buttons.addWidget(self.clear_button)
        top_buttons.addStretch(1)
        body_layout.addLayout(top_buttons)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(6)

        comparison_layout = QHBoxLayout()
        comparison_layout.setSpacing(8)
        comparison_layout.addWidget(self.file1_widgets["box"], stretch=1)
        comparison_layout.addWidget(self.file2_widgets["box"], stretch=1)
        content_layout.addLayout(comparison_layout, stretch=1)
        content_layout.addWidget(result_box)

        debug_widget = QWidget()
        debug_layout = QVBoxLayout(debug_widget)
        debug_layout.setContentsMargins(0, 0, 0, 0)
        debug_layout.setSpacing(4)
        self.debug_title = QLabel()
        self.debug_title.setStyleSheet("font-size: 15px; font-weight: 700;")
        debug_layout.addWidget(self.debug_title)
        debug_layout.addWidget(self.output)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(content_widget)
        splitter.addWidget(debug_widget)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([520, 220])
        body_layout.addWidget(splitter, stretch=1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self.close_button)
        body_layout.addLayout(buttons)

        main_layout.addWidget(body_widget, stretch=1)

        self.setCentralWidget(central)
        self.retranslate_ui()
        self.update_compare_visibility()

    def create_file_panel(self, title: str) -> dict:
        box = QFrame()
        box.setObjectName("filePanel")
        box.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(4)
        header = QLabel(title.upper())
        header.setStyleSheet("font-size: 18px; font-weight: 800; border: 0; background: transparent;")
        winner_badge = QLabel("")
        winner_badge.setFixedWidth(42)
        winner_badge.setFixedHeight(22)
        winner_badge.setVisible(False)
        winner_badge.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        winner_badge.setObjectName("winnerBadge")
        winner_badge.setStyleSheet("font-size: 16px; font-weight: 800; border: 0; background: transparent;")
        header_layout.addWidget(header)
        header_layout.addWidget(winner_badge)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        highlights = QGridLayout()
        highlights.setHorizontalSpacing(12)
        highlights.setVerticalSpacing(4)
        highlight_labels = {}
        highlight_name_labels = {}
        for index, field in enumerate((*IMPORTANT_FIELDS, "Puntuación")):
            name = QLabel(field)
            name.setObjectName("fieldName")
            name.setStyleSheet("font-size: 11px; font-weight: 600; border: 0; background: transparent;")
            value = QLabel("-")
            value.setWordWrap(True)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            if field == "Puntuación":
                value.setStyleSheet("font-size: 32px; font-weight: 800; border: 0; background: transparent;")
            else:
                value.setStyleSheet("font-size: 16px; font-weight: 700; border: 0; background: transparent;")

            row = index // 3
            column = (index % 3) * 2
            highlights.addWidget(name, row * 2, column)
            highlights.addWidget(value, row * 2 + 1, column)
            highlights.setColumnStretch(column, 1)
            highlight_labels[field] = value
            highlight_name_labels[field] = name

        layout.addLayout(highlights)

        details = QGridLayout()
        details.setHorizontalSpacing(10)
        details.setVerticalSpacing(3)
        detail_labels = {}
        detail_name_labels = {}
        for index, field in enumerate(DETAIL_FIELDS):
            row = index // 2
            column = (index % 2) * 2
            name = QLabel(f"{field}:")
            name.setObjectName("fieldName")
            name.setStyleSheet("font-weight: 600; border: 0; background: transparent;")
            value = QLabel("-")
            value.setWordWrap(True)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value.setStyleSheet("border: 0; background: transparent;")
            details.addWidget(name, row, column)
            details.addWidget(value, row, column + 1)
            details.setColumnStretch(column + 1, 1)
            detail_labels[field] = value
            detail_name_labels[field] = name

        layout.addLayout(details)
        layout.addStretch(1)

        return {
            "box": box,
            "header": header,
            "highlight_labels": highlight_labels,
            "highlight_name_labels": highlight_name_labels,
            "detail_labels": detail_labels,
            "detail_name_labels": detail_name_labels,
            "winner_badge": winner_badge,
        }

    def t(self, key: str, **kwargs) -> str:
        text = TRANSLATIONS[self.language][key]
        return text.format(**kwargs) if kwargs else text

    def retranslate_ui(self) -> None:
        self.help_button.setText(self.t("help"))
        self.about_button.setText(self.t("about"))
        self.language_label.setText(self.t("language"))
        self.theme_label.setText(self.t("theme"))

        self.language_combo.blockSignals(True)
        self.language_combo.setItemText(0, TRANSLATIONS["es"]["language_name"])
        self.language_combo.setItemText(1, TRANSLATIONS["en"]["language_name"])
        self.language_combo.setCurrentIndex(0 if self.language == "es" else 1)
        self.language_combo.blockSignals(False)

        self.theme_combo.blockSignals(True)
        self.theme_combo.setItemText(0, self.t("theme_system"))
        self.theme_combo.setItemText(1, self.t("theme_light"))
        self.theme_combo.setItemText(2, self.t("theme_dark"))
        self.theme_combo.setCurrentIndex(THEME_MODES.index(self.theme_mode))
        self.theme_combo.blockSignals(False)

        self.compare_button.setText(self.t("analyze"))
        self.clear_button.setText(self.t("clear"))
        self.close_button.setText(self.t("close"))
        self.hint_label.setText(self.t("hint"))
        self.result_title.setText(self.t("summary"))
        self.debug_title.setText(self.t("debug_title"))
        self.output.setPlaceholderText(self.t("debug_title"))
        self.video1_edit.setPlaceholderText(self.t("video_placeholder"))
        self.video2_edit.setPlaceholderText(self.t("video2_placeholder"))
        self.video1_edit.setToolTip(self.t("video_placeholder"))
        self.video2_edit.setToolTip(self.t("video2_placeholder"))

        self.path_row_labels["Archivo"].setText(self.t("file"))
        self.path_row_labels["Archivo 2"].setText(self.t("file2"))
        self.path_row_labels["Archivo__browse"].setText(self.t("browse"))
        self.path_row_labels["Archivo 2__browse"].setText(self.t("browse"))

        self.file1_widgets["header"].setText(self.t("file").upper())
        self.file2_widgets["header"].setText(self.t("file2").upper())
        for field in DETAIL_FIELDS:
            self.file1_widgets["detail_name_labels"][field].setText(f"{self.t(self.detail_field_key(field))}:")
            self.file2_widgets["detail_name_labels"][field].setText(f"{self.t(self.detail_field_key(field))}:")
        for field in IMPORTANT_FIELDS:
            self.file1_widgets["highlight_name_labels"][field].setText(self.t(self.highlight_field_key(field)))
            self.file2_widgets["highlight_name_labels"][field].setText(self.t(self.highlight_field_key(field)))

        if self.language == "es":
            self.setWindowTitle("mvsm")
        else:
            self.setWindowTitle("mvsm")

        if self.analysis_mode in ("idle", "single"):
            self.apply_state_texts()
        self.apply_theme()

    def effective_theme(self) -> str:
        if self.theme_mode != "system":
            return self.theme_mode
        return "dark" if self.style_hints.colorScheme() == Qt.ColorScheme.Dark else "light"

    def apply_theme(self) -> None:
        QApplication.instance().setStyleSheet(theme_styles(self.effective_theme()))

    def on_theme_changed(self, index: int) -> None:
        self.theme_mode = THEME_MODES[index]
        self.settings.setValue("theme", self.theme_mode)
        self.apply_theme()

    def on_system_color_scheme_changed(self, *_args) -> None:
        if self.theme_mode == "system":
            self.apply_theme()

    def apply_state_texts(self) -> None:
        if self.analysis_mode == "single":
            self.result_label.setText(self.t("single_result"))
            self.reasons_label.setText(self.t("single_reason"))
        elif self.analysis_mode == "compare":
            self.result_label.setText(self.t("compare_ready"))
        else:
            self.result_label.setText(self.t("pending_result"))
            self.reasons_label.setText(self.t("pending_reason"))

    def on_language_changed(self, index: int) -> None:
        language = "es" if index == 0 else "en"
        if language == self.language:
            return
        self.language = language
        self.retranslate_ui()

    def on_input_changed(self, *_args) -> None:
        self.update_compare_visibility()

    def show_help(self) -> None:
        self.show_rich_dialog(self.t("help_title"), self.t("help_html"))

    def show_about(self) -> None:
        self.show_rich_dialog(self.t("about_title"), self.t("about_html"))

    def show_rich_dialog(self, title: str, html: str) -> None:
        dialog = QDialog(self)
        dialog.setObjectName("richDialog")
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.resize(620, 460)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        browser = QTextBrowser()
        browser.setObjectName("richBrowser")
        browser.setOpenExternalLinks(True)
        browser.setReadOnly(True)
        browser.setHtml(html)
        browser.setStyleSheet("QTextBrowser h3 { margin-top: 0; }")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)

        layout.addWidget(browser, stretch=1)
        layout.addWidget(buttons)
        dialog.exec()

    def detail_field_key(self, field: str) -> str:
        mapping = {
            "Fichero": "file",
            "Codec vídeo": "label_video_codec",
            "Formato de píxel": "label_pix_fmt",
            "FPS": "label_fps",
            "Codec audio": "label_audio_codec",
            "Bitrate audio": "label_audio_bitrate",
            "Canales audio": "label_audio_channels",
            "Frecuencia audio": "label_audio_sample_rate",
        }
        return mapping[field]

    def highlight_field_key(self, field: str) -> str:
        mapping = {
            "Duración": "label_duration",
            "Tamaño": "label_size",
            "Resolución": "label_resolution",
            "Bitrate total": "label_total_bitrate",
            "Bitrate vídeo": "label_video_bitrate",
            "Puntuación": "label_score",
        }
        return mapping[field]

    def path_row(self, label_text: str, edit: QLineEdit) -> QHBoxLayout:
        layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(90)
        label.setStyleSheet("background: transparent;")
        self.path_row_labels[label_text] = label
        browse = QPushButton("Buscar...")
        self.path_row_labels[f"{label_text}__browse"] = browse
        browse.clicked.connect(lambda: self.browse_file(edit))
        browse.setToolTip(self.t("browse_tooltip"))

        if label_text == "Archivo":
            edit.setPlaceholderText(self.t("video_placeholder"))
        else:
            edit.setPlaceholderText(self.t("video2_placeholder"))

        layout.addWidget(label)
        layout.addWidget(edit, stretch=1)
        layout.addWidget(browse)
        return layout

    def browse_file(self, edit: QLineEdit) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.t("select_video"),
            str(Path.home()),
            "Videos (*.avi *.mkv *.mp4 *.mov *.webm *.mpeg *.mpg *.m4v);;Todos los archivos (*)",
        )
        if path:
            edit.setText(path)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        files = [url.toLocalFile() for url in urls if url.isLocalFile()]
        if files:
            self.handle_dropped_files(files)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def handle_dropped_files(self, files: list[str]) -> None:
        if len(files) >= 2:
            self.video1_edit.setText(files[0])
            self.video2_edit.setText(files[1])
            return

        if not self.video1_edit.text().strip():
            self.video1_edit.setText(files[0])
        else:
            self.video2_edit.setText(files[0])

    def run_compare(self) -> None:
        video1 = self.video1_edit.text().strip()
        video2 = self.video2_edit.text().strip()

        if not video1 and not video2:
            QMessageBox.warning(self, self.t("no_files_title"), self.t("no_files"))
            return

        paths = [video1] + ([video2] if video2 else [])
        for path in paths:
            if not Path(path).is_file():
                QMessageBox.warning(self, self.t("invalid_title"), self.t("file_not_found", path=path))
                return

        if not self.script_path.is_file():
            QMessageBox.critical(self, self.t("script_not_found_title"), self.t("script_not_found", path=self.script_path))
            return

        self.reset_results()
        self.output.clear()
        self.compare_output = ""
        command_line = f"$ {self.script_path} {video1}"
        if video2:
            command_line += f" {video2}"
        self.append_output(f"{command_line}\n\n")

        self.process = QProcess(self)
        self.process.setProgram("bash")
        arguments = [str(self.script_path), video1]
        if video2:
            arguments.append(video2)
        self.process.setArguments(arguments)
        self.process.setWorkingDirectory(str(self.script_path.parent))
        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.readyReadStandardError.connect(self.read_stderr)
        self.process.finished.connect(self.process_finished)
        self.process.errorOccurred.connect(self.process_error)

        self.compare_button.setEnabled(False)
        self.process.start()

    def read_stdout(self) -> None:
        data = self.process.readAllStandardOutput().data().decode(errors="replace")
        self.compare_output += data
        self.append_output(data)

    def read_stderr(self) -> None:
        data = self.process.readAllStandardError().data().decode(errors="replace")
        self.append_output(data)

    def process_finished(self, exit_code: int, _exit_status) -> None:
        self.compare_button.setEnabled(True)
        self.update_structured_results(self.compare_output)
        self.append_output(self.t("process_done", code=exit_code))

    def process_error(self, error) -> None:
        self.compare_button.setEnabled(True)
        self.append_output(self.t("process_error", error=error))

    def clear_all(self) -> None:
        self.output.clear()
        self.compare_output = ""
        self.video1_edit.clear()
        self.video2_edit.clear()
        self.reset_results()
        self.update_compare_visibility()

    def reset_results(self) -> None:
        self.stop_winner_animation()
        for widgets in (self.file1_widgets, self.file2_widgets):
            for label in widgets["detail_labels"].values():
                label.setText("-")
            for label in widgets["highlight_labels"].values():
                label.setText("-")

        self.analysis_mode = "idle"
        self.apply_state_texts()
        self.update_compare_visibility()

    def update_structured_results(self, output: str) -> None:
        parsed = self.parse_compare_output(output)
        self.populate_file_panel(self.file1_widgets, parsed["files"][1])
        self.populate_file_panel(self.file2_widgets, parsed["files"][2])

        single_mode = not parsed["files"][2]["fields"]
        if single_mode:
            self.stop_winner_animation()
            self.analysis_mode = "single"
            self.apply_state_texts()
            self.update_compare_visibility()
            return

        enhanced_result, comparison_notes = self.build_enhanced_result(parsed)
        self.analysis_mode = "compare"
        self.set_winner_animation(self.winning_video(parsed))
        fallback_result = self.clean_result_text(parsed["result"])
        self.result_label.setText(enhanced_result or fallback_result or self.t("compare_ready"))
        details = []
        if comparison_notes:
            details.append("Lectura rápida:\n" + "\n".join(comparison_notes))
        if parsed["reasons"]:
            details.append("Motivos del script:\n" + "\n".join(parsed["reasons"]))
        if parsed["efficiency"]:
            details.append(self.clean_result_text(parsed["efficiency"]))
        self.reasons_label.setText("\n\n".join(details) if details else self.t("no_more_details"))
        self.update_compare_visibility()

    def populate_file_panel(self, widgets: dict, data: dict) -> None:
        for field in DETAIL_FIELDS:
            if field == "Fichero":
                value = self.display_filename(data["fields"].get("Ruta", "-"))
            else:
                value = data["fields"].get(field, "-")
            widgets["detail_labels"][field].setText(value)

        for field in IMPORTANT_FIELDS:
            widgets["highlight_labels"][field].setText(data["fields"].get(field, "-"))

        widgets["highlight_labels"]["Puntuación"].setText(data.get("score") or "-")

    def display_filename(self, value: str) -> str:
        if not value or value == "-":
            return "-"
        return Path(value).name

    def winning_video(self, parsed: dict) -> int:
        score1 = self.float_value(parsed["files"][1].get("score"))
        score2 = self.float_value(parsed["files"][2].get("score"))
        if score1 > score2:
            return 1
        if score2 > score1:
            return 2
        return 0

    def set_winner_animation(self, winner: int) -> None:
        self.stop_winner_animation()
        if winner not in (1, 2):
            return
        self.current_winner = winner
        self.winner_pulse = False
        badge = self.winner_widgets()["winner_badge"]
        badge.setVisible(True)
        badge.setText("🏆")
        self.winner_timer.start()

    def stop_winner_animation(self) -> None:
        self.winner_timer.stop()
        self.current_winner = 0
        for widgets in (self.file1_widgets, self.file2_widgets):
            widgets["winner_badge"].setVisible(False)
            widgets["winner_badge"].setText("")

    def pulse_winner_badge(self) -> None:
        if self.current_winner not in (1, 2):
            self.winner_timer.stop()
            return
        self.winner_pulse = not self.winner_pulse
        badge = self.winner_widgets()["winner_badge"]
        if self.winner_pulse:
            badge.setText("🥇")
            badge.setStyleSheet("font-size: 16px; font-weight: 800; border: 0; background: transparent;")
        else:
            badge.setText("🏆")
            badge.setStyleSheet("font-size: 16px; font-weight: 800; border: 0; background: transparent;")

    def winner_widgets(self) -> dict:
        return self.file1_widgets if self.current_winner == 1 else self.file2_widgets

    def build_enhanced_result(self, parsed: dict) -> tuple[str, list[str]]:
        file1 = parsed["files"][1]
        file2 = parsed["files"][2]
        score1 = self.float_value(file1.get("score"))
        score2 = self.float_value(file2.get("score"))

        if score1 <= 0 or score2 <= 0:
            return parsed["result"], []

        winner = 1 if score1 > score2 else 2 if score2 > score1 else 0
        if not winner:
            return "Resultado: empate técnico aproximado.", ["Las puntuaciones finales son iguales o prácticamente equivalentes."]

        loser = 2 if winner == 1 else 1
        winner_data = parsed["files"][winner]
        loser_data = parsed["files"][loser]
        winner_score = score1 if winner == 1 else score2
        loser_score = score2 if winner == 1 else score1

        metrics = self.metric_comparison(winner_data, loser_data, winner_score, loser_score)
        strong_metrics = [metric for metric in metrics if metric["ratio"] >= 1.5]
        double_metrics = [metric for metric in metrics if metric["ratio"] >= 2.0]
        triple_metrics = [metric for metric in metrics if metric["ratio"] >= 3.0]

        score_ratio = winner_score / loser_score if loser_score > 0 else 0
        if score_ratio >= 3.0:
            strength = "muy superior: triplica o más la puntuación final"
        elif score_ratio >= 2.0:
            strength = "muy superior: dobla o más la puntuación final"
        elif triple_metrics:
            strength = "muy superior: alguna métrica importante triplica a la otra"
        elif double_metrics:
            strength = "muy superior: alguna métrica importante dobla a la otra"
        elif len(strong_metrics) >= 2 or score_ratio >= 1.5:
            strength = "claramente mejor"
        elif score_ratio >= 1.2:
            strength = "mejor de forma notable"
        else:
            strength = "ligeramente mejor"

        result = f"Resultado: Video {winner} es {strength} técnicamente."
        notes = [
            f"Puntuación: Video {winner} {self.ratio_text(score_ratio)} a Video {loser} ({winner_score:.2f} frente a {loser_score:.2f})."
        ]
        notes.extend(metric["text"] for metric in metrics if metric["text"])

        if len(strong_metrics) >= 3:
            notes.append(
                f"La ventaja no es pequeña: varias métricas importantes favorecen claramente al Video {winner}."
            )
        elif strength == "ligeramente mejor":
            notes.append(
                "La diferencia global parece ajustada; conviene revisar visualmente si ambos videos son candidatos reales."
            )

        return result, notes

    def metric_comparison(self, winner_data: dict, loser_data: dict, winner_score: float, loser_score: float) -> list[dict]:
        winner_fields = winner_data["fields"]
        loser_fields = loser_data["fields"]
        metrics = []

        winner_pixels = self.resolution_pixels(winner_fields.get("Resolución", ""))
        loser_pixels = self.resolution_pixels(loser_fields.get("Resolución", ""))
        if winner_pixels > 0 and loser_pixels > 0:
            ratio = winner_pixels / loser_pixels
            if ratio > 1.05:
                metrics.append({
                    "ratio": ratio,
                    "text": f"Resolución: Video ganador {self.ratio_text(ratio)} en píxeles.",
                })

        winner_video_bitrate = self.first_number(winner_fields.get("Bitrate vídeo", ""))
        loser_video_bitrate = self.first_number(loser_fields.get("Bitrate vídeo", ""))
        if winner_video_bitrate > 0 and loser_video_bitrate > 0:
            ratio = winner_video_bitrate / loser_video_bitrate
            if ratio > 1.05:
                metrics.append({
                    "ratio": ratio,
                    "text": f"Bitrate de vídeo: Video ganador {self.ratio_text(ratio)}.",
                })

        winner_codec = winner_fields.get("Codec vídeo", "").lower()
        loser_codec = loser_fields.get("Codec vídeo", "").lower()
        winner_codec_rank = VIDEO_CODEC_RANKS.get(winner_codec, 0)
        loser_codec_rank = VIDEO_CODEC_RANKS.get(loser_codec, 0)
        if winner_codec_rank > 0 and loser_codec_rank > 0 and winner_codec_rank > loser_codec_rank:
            ratio = winner_codec_rank / loser_codec_rank
            metrics.append({
                "ratio": max(ratio, 1.2),
                "text": f"Codec: {winner_codec} está por encima de {loser_codec} en el ranking técnico usado por el comparador.",
            })

        if loser_score > 0:
            metrics.append({"ratio": winner_score / loser_score, "text": ""})

        return metrics

    def ratio_text(self, ratio: float) -> str:
        if ratio >= 3.0:
            return f"triplica o más ({ratio:.2f}x)"
        if ratio >= 2.0:
            return f"dobla o más ({ratio:.2f}x)"
        if ratio >= 1.5:
            return f"es mucho mayor ({ratio:.2f}x)"
        if ratio >= 1.2:
            return f"es claramente mayor ({ratio:.2f}x)"
        return f"es algo mayor ({ratio:.2f}x)"

    def resolution_pixels(self, value: str) -> int:
        clean = value.lower().replace(" ", "")
        if "x" not in clean:
            return 0
        left, right = clean.split("x", 1)
        width = self.first_number(left)
        height = self.first_number(right)
        return int(width * height) if width > 0 and height > 0 else 0

    def first_number(self, value: str) -> float:
        number = []
        started = False
        for char in str(value):
            if char.isdigit() or char == ".":
                number.append(char)
                started = True
            elif started:
                break
        return self.float_value("".join(number))

    def float_value(self, value) -> float:
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            return 0.0

    def parse_compare_output(self, output: str) -> dict:
        parsed = {
            "files": {
                1: {"fields": {}, "score": "", "score_details": []},
                2: {"fields": {}, "score": "", "score_details": []},
            },
            "result": "",
            "reasons": [],
            "efficiency": "",
        }

        current_file = None
        current_score = None
        collecting_reasons = False
        single_mode = "=== Archivo 1 ===" not in output and "=== Archivo 2 ===" not in output

        for raw_line in output.splitlines():
            line = raw_line.strip()
            if not line:
                collecting_reasons = False
                current_score = None
                continue

            if line == "=== Archivo 1 ===":
                current_file = 1
                current_score = None
                collecting_reasons = False
                continue
            if line == "=== Archivo 2 ===":
                current_file = 2
                current_score = None
                collecting_reasons = False
                continue

            if line.startswith("Puntuación archivo 1:"):
                parsed["files"][1]["score"] = line.split(":", 1)[1].strip()
                current_score = 1
                current_file = None
                collecting_reasons = False
                continue
            if line.startswith("Puntuación archivo 2:"):
                parsed["files"][2]["score"] = line.split(":", 1)[1].strip()
                current_score = 2
                current_file = None
                collecting_reasons = False
                continue
            if single_mode and current_file is None and current_score is None and ":" in line:
                current_file = 1
            if line == "Resumen puntuacion:":
                collecting_reasons = False
                continue
            if current_score and line.startswith("-"):
                parsed["files"][current_score]["score_details"].append(line)
                continue

            if line.startswith("Resultado:"):
                parsed["result"] = line
                collecting_reasons = False
                current_score = None
                current_file = None
                continue
            if line == "Motivos:":
                collecting_reasons = True
                current_score = None
                continue
            if collecting_reasons and line.startswith("-"):
                parsed["reasons"].append(line)
                continue
            if line.startswith("Eficiencia:"):
                parsed["efficiency"] = line
                collecting_reasons = False
                continue

            if current_file and ":" in line:
                key, value = line.split(":", 1)
                parsed["files"][current_file]["fields"][key.strip()] = value.strip()

        return parsed

    def append_output(self, text: str) -> None:
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output.setTextCursor(cursor)
        self.output.insertPlainText(text)
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output.setTextCursor(cursor)

    def update_compare_visibility(self) -> None:
        has_second = bool(self.video2_edit.text().strip())
        self.file2_widgets["box"].setVisible(has_second)

    def clean_result_text(self, text: str) -> str:
        cleaned = (text or "").strip()
        if cleaned.startswith("Resultado:"):
            cleaned = cleaned.split(":", 1)[1].strip()
        return cleaned.replace("Archivo", "Video")


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("mvsm")
    app.setApplicationDisplayName("mvsm")
    app.setDesktopFileName(DESKTOP_FILE_ID)
    if APP_ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_PATH)))
    window = VideoCompareWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
