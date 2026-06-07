#!/usr/bin/env python3

import os
import sys
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
VENV_PYTHON = APP_DIR / ".venv" / "bin" / "python"


try:
    from PySide6.QtCore import QProcess, Qt, QTimer
    from PySide6.QtGui import QIcon, QTextCursor
    from PySide6.QtWidgets import (
        QApplication,
        QFileDialog,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QPlainTextEdit,
        QSplitter,
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
        self.script_path = Path(__file__).resolve().with_name("mvsm.sh")
        self.process = None
        self.compare_output = ""

        self.setWindowTitle("mvsm")
        if APP_ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PATH)))
        self.resize(1180, 760)
        self.setAcceptDrops(True)

        self.video1_edit = DropLineEdit("Ruta del primer video", self.handle_dropped_files)
        self.video2_edit = DropLineEdit("Ruta del segundo video", self.handle_dropped_files)

        self.file1_widgets = self.create_file_panel("Video 1")
        self.file2_widgets = self.create_file_panel("Video 2")
        self.current_winner = 0
        self.winner_pulse = False
        self.winner_timer = QTimer(self)
        self.winner_timer.setInterval(550)
        self.winner_timer.timeout.connect(self.pulse_winner_badge)

        self.result_label = QLabel("Resultado pendiente")
        self.result_label.setWordWrap(True)
        self.result_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.result_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #111;")

        self.reasons_label = QLabel("Ejecuta una comparacion para ver el resultado.")
        self.reasons_label.setWordWrap(True)
        self.reasons_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.reasons_label.setStyleSheet("font-size: 13px; color: #333;")

        result_box = QGroupBox("Resultado")
        result_layout = QVBoxLayout(result_box)
        result_layout.setContentsMargins(10, 8, 10, 8)
        result_layout.setSpacing(4)
        result_layout.addWidget(self.result_label)
        result_layout.addWidget(self.reasons_label)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(180)
        self.output.setPlaceholderText("Salida de debug completa del script")

        self.compare_button = QPushButton("Comparar")
        self.compare_button.clicked.connect(self.run_compare)

        self.clear_button = QPushButton("Limpiar")
        self.clear_button.clicked.connect(self.clear_all)

        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.close)

        central = QWidget()
        central.setStyleSheet("background: #eef1f4;")
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 10)
        main_layout.setSpacing(0)

        body_widget = QWidget()
        body_widget.setStyleSheet("background: #f8f9fb; border-top: 1px solid #c8d0da;")
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(10, 12, 10, 0)
        body_layout.setSpacing(6)

        help_label = QLabel(
            "Puedes arrastrar uno o dos ficheros de video sobre la ventana. "
            "Soportados: avi, mkv, mp4, mov, webm, mpeg, mpg, m4v."
        )
        help_label.setStyleSheet("color: #4a5561; background: transparent;")
        body_layout.addWidget(help_label)

        path_layout = QGridLayout()
        path_layout.setHorizontalSpacing(8)
        path_layout.setVerticalSpacing(4)
        path_layout.addLayout(self.path_row("Video 1", self.video1_edit), 0, 0)
        path_layout.addLayout(self.path_row("Video 2", self.video2_edit), 1, 0)
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
        debug_title = QLabel("Debug / salida completa")
        debug_title.setStyleSheet("font-size: 15px; font-weight: 700;")
        debug_layout.addWidget(debug_title)
        debug_layout.addWidget(self.output)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(content_widget)
        splitter.addWidget(debug_widget)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([520, 220])
        body_layout.addWidget(splitter, stretch=1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(close_button)
        body_layout.addLayout(buttons)

        main_layout.addWidget(body_widget, stretch=1)

        self.setCentralWidget(central)

    def create_file_panel(self, title: str) -> dict:
        box = QFrame()
        box.setFrameShape(QFrame.Shape.StyledPanel)
        box.setStyleSheet("QFrame { border: 1px solid #cfd6df; border-radius: 4px; background: #fff; }")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)
        header = QLabel(title.upper())
        header.setStyleSheet("font-size: 24px; font-weight: 900; color: #111; border: 0; background: transparent;")
        winner_badge = QLabel("")
        winner_badge.setFixedWidth(96)
        winner_badge.setFixedHeight(24)
        winner_badge.setVisible(False)
        winner_badge.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        winner_badge.setStyleSheet("font-size: 16px; font-weight: 800; color: #b77900; border: 0; background: transparent;")
        header_layout.addWidget(header)
        header_layout.addWidget(winner_badge)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        highlights = QGridLayout()
        highlights.setHorizontalSpacing(12)
        highlights.setVerticalSpacing(4)
        highlight_labels = {}
        for index, field in enumerate((*IMPORTANT_FIELDS, "Puntuación")):
            name = QLabel(field)
            name.setStyleSheet("font-size: 11px; font-weight: 600; color: #555; border: 0; background: transparent;")
            value = QLabel("-")
            value.setWordWrap(True)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            if field == "Puntuación":
                value.setStyleSheet("font-size: 32px; font-weight: 800; color: #111; border: 0; background: transparent;")
            else:
                value.setStyleSheet("font-size: 16px; font-weight: 700; color: #111; border: 0; background: transparent;")

            row = index // 3
            column = (index % 3) * 2
            highlights.addWidget(name, row * 2, column)
            highlights.addWidget(value, row * 2 + 1, column)
            highlights.setColumnStretch(column, 1)
            highlight_labels[field] = value

        layout.addLayout(highlights)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #d8dde5; background: transparent;")
        layout.addWidget(separator)

        details = QGridLayout()
        details.setHorizontalSpacing(10)
        details.setVerticalSpacing(3)
        detail_labels = {}
        for index, field in enumerate(DETAIL_FIELDS):
            row = index // 2
            column = (index % 2) * 2
            name = QLabel(f"{field}:")
            name.setStyleSheet("font-weight: 600; color: #333; border: 0; background: transparent;")
            value = QLabel("-")
            value.setWordWrap(True)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value.setStyleSheet("border: 0; background: transparent;")
            details.addWidget(name, row, column)
            details.addWidget(value, row, column + 1)
            details.setColumnStretch(column + 1, 1)
            detail_labels[field] = value

        layout.addLayout(details)
        layout.addStretch(1)

        return {
            "box": box,
            "highlight_labels": highlight_labels,
            "detail_labels": detail_labels,
            "winner_badge": winner_badge,
        }

    def path_row(self, label_text: str, edit: QLineEdit) -> QHBoxLayout:
        layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(70)
        browse = QPushButton("Buscar...")
        browse.clicked.connect(lambda: self.browse_file(edit))

        layout.addWidget(label)
        layout.addWidget(edit, stretch=1)
        layout.addWidget(browse)
        return layout

    def browse_file(self, edit: QLineEdit) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar video",
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

        if not video1 or not video2:
            QMessageBox.warning(self, "Faltan archivos", "Indica los dos ficheros de video.")
            return

        for path in (video1, video2):
            if not Path(path).is_file():
                QMessageBox.warning(self, "Archivo no valido", f"No existe el fichero:\n{path}")
                return

        if not self.script_path.is_file():
            QMessageBox.critical(self, "Script no encontrado", f"No existe:\n{self.script_path}")
            return

        self.reset_results()
        self.output.clear()
        self.compare_output = ""
        self.append_output(f"$ {self.script_path} {video1} {video2}\n\n")

        self.process = QProcess(self)
        self.process.setProgram("bash")
        self.process.setArguments([str(self.script_path), video1, video2])
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
        self.append_output(f"\nProceso finalizado con codigo {exit_code}.\n")

    def process_error(self, error) -> None:
        self.compare_button.setEnabled(True)
        self.append_output(f"\nError al ejecutar el proceso: {error}.\n")

    def clear_all(self) -> None:
        self.output.clear()
        self.compare_output = ""
        self.reset_results()

    def reset_results(self) -> None:
        self.stop_winner_animation()
        for widgets in (self.file1_widgets, self.file2_widgets):
            for label in widgets["detail_labels"].values():
                label.setText("-")
            for label in widgets["highlight_labels"].values():
                label.setText("-")

        self.result_label.setText("Resultado pendiente")
        self.reasons_label.setText("Ejecuta una comparacion para ver el resultado.")

    def update_structured_results(self, output: str) -> None:
        parsed = self.parse_compare_output(output)
        self.populate_file_panel(self.file1_widgets, parsed["files"][1])
        self.populate_file_panel(self.file2_widgets, parsed["files"][2])

        enhanced_result, comparison_notes = self.build_enhanced_result(parsed)
        self.set_winner_animation(self.winning_video(parsed))
        fallback_result = parsed["result"].replace("Archivo", "Video") if parsed["result"] else ""
        self.result_label.setText(enhanced_result or fallback_result or "Resultado no encontrado")
        details = []
        if comparison_notes:
            details.append("Lectura rápida:\n" + "\n".join(comparison_notes))
        if parsed["reasons"]:
            details.append("Motivos del script:\n" + "\n".join(parsed["reasons"]))
        if parsed["efficiency"]:
            details.append(parsed["efficiency"].replace("Archivo", "Video"))
        self.reasons_label.setText("\n\n".join(details) if details else "Sin motivos adicionales.")

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
            badge.setStyleSheet("font-size: 16px; font-weight: 800; color: #b77900; border: 0; background: transparent;")
        else:
            badge.setText("🏆")
            badge.setStyleSheet("font-size: 16px; font-weight: 800; color: #b77900; border: 0; background: transparent;")

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
