import sys
import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRectF, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient, QLinearGradient


# ─────────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────────
class SplashConfig:
    SISTEMA_NOMBRE = "GearBook"
    SUBTITULO = "ASISTENTE PERSONAL"
    TOTAL_DURATION_MS = 3200
    FADE_OUT_MS = 600


# ─────────────────────────────────────────────
#  NÚCLEO ANIMADO — anillos de puntos concéntricos
#  girando a distinto ritmo, con un halo que respira.
#  Sobrio y ámbar, coherente con el resto de la app.
# ─────────────────────────────────────────────
class NucleoCarga(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(190, 190)
        self._angulo = 0.0
        self._respiracion = 0.0
        self._dir = 1

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animar)
        self.timer.start(16)

    def _animar(self):
        self._angulo += 0.4
        if self._angulo >= 360:
            self._angulo -= 360
        self._respiracion += 0.02 * self._dir
        if self._respiracion >= 1.0 or self._respiracion <= 0.0:
            self._dir *= -1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        cx = self.width() / 2.0
        cy = self.height() / 2.0
        painter.setPen(Qt.NoPen)

        # Halo central que respira
        radio_halo = 62 + (self._respiracion * 7)
        grad = QRadialGradient(cx, cy, radio_halo)
        grad.setColorAt(0.0, QColor(224, 164, 92, 55))
        grad.setColorAt(1.0, QColor(224, 164, 92, 0))
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(QRectF(cx - radio_halo, cy - radio_halo, radio_halo * 2, radio_halo * 2))

        # Tres anillos de puntos, cada uno con su propia velocidad y opacidad
        anillos = [
            {"radio": 40, "n": 8, "vel": 1.0, "tam": 3.0, "alpha": 220},
            {"radio": 56, "n": 12, "vel": -0.6, "tam": 2.2, "alpha": 140},
            {"radio": 72, "n": 16, "vel": 0.35, "tam": 1.6, "alpha": 80},
        ]
        for anillo in anillos:
            for i in range(anillo["n"]):
                angulo_base = (360 / anillo["n"]) * i
                angulo_actual = math.radians(angulo_base + self._angulo * anillo["vel"])
                x = cx + anillo["radio"] * math.cos(angulo_actual)
                y = cy + anillo["radio"] * math.sin(angulo_actual)
                painter.setBrush(QBrush(QColor(224, 164, 92, anillo["alpha"])))
                r = anillo["tam"]
                painter.drawEllipse(QRectF(x - r, y - r, r * 2, r * 2))

        # Núcleo central sólido
        radio_nucleo = 9 + (self._respiracion * 1.4)
        painter.setBrush(QBrush(QColor(224, 164, 92, 235)))
        painter.drawEllipse(QRectF(cx - radio_nucleo, cy - radio_nucleo, radio_nucleo * 2, radio_nucleo * 2))


# ─────────────────────────────────────────────
#  BARRA DE PROGRESO — fina, degradado terracota → ámbar
# ─────────────────────────────────────────────
class BarraCarga(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(4)
        self.setFixedWidth(240)
        self.progress = 0.0

    def set_progress(self, val):
        self.progress = max(0.0, min(1.0, val))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Riel de fondo, apenas visible
        pen_riel = QPen(QColor(255, 255, 255, 18), 3, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_riel)
        painter.drawLine(2, 2, self.width() - 2, 2)

        if self.progress > 0:
            fill_width = (self.width() - 4) * self.progress
            grad = QLinearGradient(0, 0, fill_width, 0)
            grad.setColorAt(0.0, QColor(193, 122, 86))   # terracota
            grad.setColorAt(1.0, QColor(224, 164, 92))   # ámbar
            pen_fill = QPen(QBrush(grad), 3, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen_fill)
            painter.drawLine(2, 2, int(2 + fill_width), 2)


# ─────────────────────────────────────────────
#  SPLASH — panel redondeado coherente con el resto de ventanas de la app
# ─────────────────────────────────────────────
class SplashCyberpunk(QWidget):
    def __init__(self, config: SplashConfig = None):
        super().__init__()
        self.cfg = config or SplashConfig()
        self._callback = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SplashScreen)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.resize(360, 400)
        self._centrar()

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(0, 0, 0, 0)

        # Panel: mismo fondo/borde/radio que interfaz_buscador.py e interfaz_notas.py
        self.panel = QWidget(self)
        self.panel.setObjectName("panelSplash")
        self.panel.setStyleSheet("""
            QWidget#panelSplash {
                background-color: #1a1f2b;
                border: 1px solid #4a5570;
                border-radius: 14px;
            }
        """)
        layout_raiz.addWidget(self.panel)

        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(0, 38, 0, 32)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        self.nucleo = NucleoCarga(self.panel)
        layout.addWidget(self.nucleo, alignment=Qt.AlignCenter)

        layout.addSpacing(16)

        self.lbl_title = QLabel(self.cfg.SISTEMA_NOMBRE)
        self.lbl_title.setStyleSheet("""
            QLabel {
                color: #d8dee9;
                font-family: 'Georgia', 'Cambria', 'Constantia', serif;
                font-size: 26px;
                font-weight: 700;
                letter-spacing: 6px;
                background: transparent;
            }
        """)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_title)

        self.lbl_sub = QLabel(self.cfg.SUBTITULO)
        self.lbl_sub.setStyleSheet("""
            QLabel {
                color: #8b93a8;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 2px;
                background: transparent;
                margin-top: 4px;
            }
        """)
        self.lbl_sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_sub)

        layout.addSpacing(24)

        self.lbl_estado = QLabel("Iniciando…")
        self.lbl_estado.setStyleSheet("""
            QLabel {
                color: #5c6478;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10px;
                background: transparent;
            }
        """)
        self.lbl_estado.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_estado)

        layout.addSpacing(10)

        self.progress_bar = BarraCarga(self.panel)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)

        # Fade in / out
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)

        self._fade_in = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_in.setDuration(400)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.OutCubic)

        self._fade_out = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_out.setDuration(self.cfg.FADE_OUT_MS)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.InCubic)
        self._fade_out.finished.connect(self._on_fade_out_done)

    def paintEvent(self, event):
        pass  # el panel interno ya pinta su propio fondo/borde

    def iniciar(self, callback=None):
        self._callback = callback
        self._fade_in.start()

        pasos = [
            (0.25, "Cargando módulos…"),
            (0.55, "Preparando interfaz…"),
            (0.85, "Sincronizando datos…"),
            (1.0, "Listo."),
        ]
        total = self.cfg.TOTAL_DURATION_MS
        for i, (prog, texto) in enumerate(pasos):
            momento = int(total * (i + 1) / (len(pasos) + 0.3))
            QTimer.singleShot(momento, lambda p=prog, t=texto: self._update_step(p, t))

        QTimer.singleShot(total, self._iniciar_cierre)

    def _update_step(self, progress, texto):
        self.progress_bar.set_progress(progress)
        self.lbl_estado.setText(texto)

    def _iniciar_cierre(self):
        self._fade_out.start()

    def _on_fade_out_done(self):
        self.close()
        if self._callback:
            self._callback()

    def _centrar(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = SplashCyberpunk()
    splash.show()
    splash.iniciar(callback=lambda: print("¡Arranque completado con éxito!"))
    sys.exit(app.exec_())