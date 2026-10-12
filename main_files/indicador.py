import os
import json
import math
from PyQt5.QtWidgets import QWidget, QMenu
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QRadialGradient, QCursor, QPen, QBrush
RUTA_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "indicador_config.json")

def _lerp(a, b, t):
    return a + (b - a) * t

def _lerp_color(c1, c2, t):
    """Interpola linealmente entre dos QColor (incluyendo alfa)."""
    return QColor(
        int(_lerp(c1.red(), c2.red(), t)),
        int(_lerp(c1.green(), c2.green(), t)),
        int(_lerp(c1.blue(), c2.blue(), t)),
        int(_lerp(c1.alpha(), c2.alpha(), t)),
    )

class IndicadorFlotante(QWidget):
    """Mini-sistema planetario/estelar flotante. Coherente con la estética
    galáctica centralizada: núcleo brillante, anillos orbitales inclinados,
    partículas giratorias y halo de nebulosa."""
    
    clic_restaurar = pyqtSignal()
    clic_ocultar = pyqtSignal()
    estado_cambiado = pyqtSignal(str)

    # Paleta coherente con el overlay galáctico (cian, violeta, rosa)
    PALETA = {
        "idle": {
            "nucleo": QColor(220, 240, 255, 255),      # Blanco-cian brillante
            "anillo1": QColor(138, 43, 226, 180),       # Púrpura
            "anillo2": QColor(0, 240, 255, 160),        # Cian
            "particula": QColor(255, 255, 255, 220),    # Blanco
            "halo": QColor(100, 150, 255, 60)           # Azul suave
        },
        "escuchando": {
            "nucleo": QColor(255, 200, 220, 255),       # Rosa claro
            "anillo1": QColor(255, 105, 180, 200),      # Rosa intenso
            "anillo2": QColor(255, 180, 100, 180),      # Naranja suave
            "particula": QColor(255, 220, 240, 240),    # Rosa blanco
            "halo": QColor(255, 150, 200, 80)           # Rosa halo
        },
        "procesando": {
            "nucleo": QColor(230, 180, 255, 255),       # Violeta claro
            "anillo1": QColor(180, 100, 255, 220),      # Violeta intenso
            "anillo2": QColor(100, 200, 255, 200),      # Cian claro
            "particula": QColor(255, 255, 255, 255),    # Blanco puro
            "halo": QColor(150, 100, 255, 100)          # Violeta halo
        }
    }

    MARGEN_HALO = 20  # Margen extra para el halo de nebulosa

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tamano = 28
        self._estado = "idle"
        self._tick = 0
        self._drag_pos = None
        self._drag_start = None

        # Estado de transición de color (fundido suave ~350ms)
        self._colores_actuales = {k: QColor(v) for k, v in self.PALETA["idle"].items()}
        self._colores_destino = {k: QColor(v) for k, v in self.PALETA["idle"].items()}
        self._transicion_t = 1.0

        # Ecos de escucha (ondas gravitacionales)
        self._ecos = []

        # Ángulos de rotación para anillos y partículas
        self._angulo_anillo1 = 0.0
        self._angulo_anillo2 = 90.0
        self._angulo_particulas = [0.0, 120.0, 240.0]  # 3 partículas distribuidas

        # Velocidad de rotación base (aumenta en "procesando")
        self._velocidad_rotacion = 0.8

        flags = (
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        self._cargar_config()
        self._aplicar_geometria()

        self._timer_pulso = QTimer(self)
        self._timer_pulso.timeout.connect(self._animar)
        self._timer_pulso.start(16)  # ~60 FPS

    # ── CONFIG PERSISTENTE ──────────────────────────────────
    def _cargar_config(self):
        try:
            with open(RUTA_CONFIG, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self._tamano = max(16, min(100, cfg.get("tamano", 28)))
            self._pos_guardada = QPoint(cfg.get("x", -1), cfg.get("y", -1))
        except Exception:
            self._pos_guardada = QPoint(-1, -1)

    def _guardar_config(self):
        try:
            cfg = {"tamano": self._tamano, "x": self.x(), "y": self.y()}
            with open(RUTA_CONFIG, "w", encoding="utf-8") as f:
                json.dump(cfg, f)
        except Exception:
            pass

    def _aplicar_geometria(self):
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        ancho_total = self._tamano + (self.MARGEN_HALO * 2)
        if self._pos_guardada.x() < 0 or self._pos_guardada.y() < 0:
            x = screen.width() - ancho_total - 60
            y = screen.height() - ancho_total - 100
        else:
            x, y = self._pos_guardada.x(), self._pos_guardada.y()
        self.setGeometry(x, y, ancho_total, ancho_total)

    # ── ESTADO ──────────────────────────────────────────────
    def set_estado(self, estado: str):
        if estado in self.PALETA and estado != self._estado:
            self._estado = estado
            # Iniciar transición suave hacia los nuevos colores
            for k in self.PALETA[estado]:
                self._colores_destino[k] = QColor(self.PALETA[estado][k])
            self._transicion_t = 0.0
            
            # Ajustar velocidad de rotación según estado
            if estado == "procesando":
                self._velocidad_rotacion = 2.5
            elif estado == "escuchando":
                self._velocidad_rotacion = 1.2
            else:
                self._velocidad_rotacion = 0.8
            
            if estado == "escuchando":
                self._ecos = [0.0]  # Lanza el primer eco inmediatamente
            
            self.estado_cambiado.emit(estado)

    # ── ANIMACIÓN ───────────────────────────────────────────
    def _animar(self):
        self._tick += 1

        # 1. Avanzar transición de color (~350ms a 60 FPS ≈ 21 frames)
        if self._transicion_t < 1.0:
            self._transicion_t = min(1.0, self._transicion_t + 0.05)
            for k in self._colores_actuales:
                self._colores_actuales[k] = _lerp_color(
                    self._colores_actuales[k], self._colores_destino[k], 0.18
                )

        # 2. Ecos de escucha (ondas gravitacionales expansivas)
        if self._estado == "escuchando":
            if self._tick % 40 == 0:
                self._ecos.append(0.0)
        self._ecos = [r + 0.015 for r in self._ecos if r < 1.0]

        # 3. Rotación de anillos y partículas
        self._angulo_anillo1 = (self._angulo_anillo1 + self._velocidad_rotacion) % 360
        self._angulo_anillo2 = (self._angulo_anillo2 + self._velocidad_rotacion * 0.7) % 360
        for i in range(len(self._angulo_particulas)):
            self._angulo_particulas[i] = (self._angulo_particulas[i] + self._velocidad_rotacion * 1.5) % 360

        self.update()

        # ── DIBUJO ──────────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        centro = self.rect().center()

        # Pulso orgánico del núcleo (combinación de senos)
        fase = self._tick * 0.04
        factor_pulso = 1.0 + 0.08 * math.sin(fase) + 0.04 * math.sin(fase * 2.1 + 1.0)
        
        # Convertimos todo a enteros desde el principio para evitar errores de tipo en PyQt5
        radio_nucleo = int((self._tamano / 4) * factor_pulso)
        radio_anillo1 = int(self._tamano / 2.2)
        radio_anillo2 = int(self._tamano / 1.8)
        radio_halo = int(self._tamano / 1.4 + self.MARGEN_HALO)

        # ── 0. Ecos expansivos (ondas gravitacionales) ────────
        for r in self._ecos:
            alpha = max(0, int(120 * (1.0 - r)))
            if alpha <= 0:
                continue
            radio_eco = int(radio_nucleo + r * (self.MARGEN_HALO * 1.8))
            pen = QPen(QColor(self._colores_actuales["halo"].red(),
                              self._colores_actuales["halo"].green(),
                              self._colores_actuales["halo"].blue(), alpha), 1.5)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(centro, radio_eco, radio_eco)
        painter.setPen(Qt.NoPen)

        # ── 1. Halo de nebulosa exterior ──────────────────────
        grad_halo = QRadialGradient(centro, radio_halo)
        c_halo = self._colores_actuales["halo"]
        c_halo_fuerte = QColor(c_halo)
        c_halo_fuerte.setAlpha(80)
        c_halo_medio = QColor(c_halo)
        c_halo_medio.setAlpha(40)
        c_transparente = QColor(c_halo)
        c_transparente.setAlpha(0)
        grad_halo.setColorAt(0.0, c_halo_fuerte)
        grad_halo.setColorAt(0.5, c_halo_medio)
        grad_halo.setColorAt(1.0, c_transparente)
        painter.setBrush(grad_halo)
        painter.drawEllipse(centro, radio_halo, radio_halo)

        # ── 2. Anillos orbitales inclinados ───────────────────
        painter.save()
        painter.translate(centro)
        
        # Anillo 1
        painter.save()
        painter.rotate(self._angulo_anillo1)
        pen_anillo1 = QPen(self._colores_actuales["anillo1"], 2)
        painter.setPen(pen_anillo1)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(int(-radio_anillo1), int(-radio_anillo1 // 2), int(radio_anillo1 * 2), int(radio_anillo1))
        painter.restore()

        # Anillo 2
        painter.save()
        painter.rotate(self._angulo_anillo2)
        pen_anillo2 = QPen(self._colores_actuales["anillo2"], 1.5)
        painter.setPen(pen_anillo2)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(int(-radio_anillo2 // 1.5), int(-radio_anillo2), int(radio_anillo2 * 1.33), int(radio_anillo2 * 2))
        painter.restore()

        # ── 3. Partículas orbitales (estrellas/planetas) ──────
        for i, ang in enumerate(self._angulo_particulas):
            ang_rad = math.radians(ang)
            rx = int(radio_anillo1 * 0.9)
            ry = int(radio_anillo1 * 0.45)
            px = int(rx * math.cos(ang_rad))
            py = int(ry * math.sin(ang_rad))
            
            tam_particula = int(2.5 if i % 2 == 0 else 1.8)
            color_part = self._colores_actuales["particula"]
            painter.setBrush(QBrush(color_part))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(px - tam_particula), int(py - tam_particula),
                               int(tam_particula * 2), int(tam_particula * 2))

        painter.restore()
        painter.setPen(Qt.NoPen)

        # ── 4. Núcleo central brillante (estrella) ────────────
        grad_nucleo = QRadialGradient(
            centro.x() - int(radio_nucleo * 0.2),
            centro.y() - int(radio_nucleo * 0.2),
            int(radio_nucleo * 1.8)
        )
        c_nucleo = self._colores_actuales["nucleo"]
        c_nucleo_centro = QColor(min(255, c_nucleo.red() + 50),
                                  min(255, c_nucleo.green() + 50),
                                  min(255, c_nucleo.blue() + 50), 255)
        c_nucleo_borde = QColor(c_nucleo.red(), c_nucleo.green(), c_nucleo.blue(), 180)
        grad_nucleo.setColorAt(0.0, c_nucleo_centro)
        grad_nucleo.setColorAt(0.6, c_nucleo)
        grad_nucleo.setColorAt(1.0, c_nucleo_borde)
        painter.setBrush(grad_nucleo)
        painter.drawEllipse(centro, radio_nucleo, radio_nucleo)

        # ── 5. Reflejo especular (brillo tipo estrella) ───────
        radio_brillo = int(radio_nucleo * 0.4)
        centro_brillo = QPoint(
            int(centro.x() - radio_nucleo * 0.25),
            int(centro.y() - radio_nucleo * 0.3)
        )
        grad_brillo = QRadialGradient(centro_brillo, radio_brillo)
        grad_brillo.setColorAt(0.0, QColor(255, 255, 255, 220))
        grad_brillo.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(grad_brillo)
        painter.drawEllipse(centro_brillo, radio_brillo, radio_brillo)

    # ── ARRASTRAR + CLIC ───────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            self._drag_start = event.globalPos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._drag_start is not None:
                delta = (event.globalPos() - self._drag_start).manhattanLength()
                if delta < 5:
                    self.clic_restaurar.emit()
            self._drag_pos = None
            self._drag_start = None
            self._guardar_config()
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clic_ocultar.emit()
            event.accept()

    # ── SCROLL = TAMAÑO ────────────────────────────────────
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        paso = 4 if delta > 0 else -4
        self._cambiar_tamano(paso)
        event.accept()

    # ── MENÚ DERECHO ───────────────────────────────────────
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #1e1e24; color: #ffffff; border: 1px solid #3a3a44;
                    font-family: 'Segoe UI'; font-size: 12px; padding: 4px; border-radius: 6px; }
            QMenu::item { padding: 6px 20px; border-radius: 4px; }
            QMenu::item:selected { background: #007acc; }
        """)
        act_aumentar = menu.addAction("Aumentar tamaño")
        act_disminuir = menu.addAction("Disminuir tamaño")
        menu.addSeparator()
        act_centro = menu.addAction("Centrar en pantalla")
        menu.addSeparator()
        act_ocultar = menu.addAction("Ocultar indicador")
        accion = menu.exec_(event.globalPos())
        if accion == act_aumentar:
            self._cambiar_tamano(+6)
        elif accion == act_disminuir:
            self._cambiar_tamano(-6)
        elif accion == act_centro:
            from PyQt5.QtWidgets import QApplication
            screen = QApplication.primaryScreen().availableGeometry()
            ancho_total = self._tamano + (self.MARGEN_HALO * 2)
            self.move(screen.width() // 2 - ancho_total // 2,
                      screen.height() // 2 - ancho_total // 2)
            self._guardar_config()
        elif accion == act_ocultar:
            self.hide()

    def _cambiar_tamano(self, delta):
        centro = self.geometry().center()
        nuevo = max(16, min(100, self._tamano + delta))
        if nuevo != self._tamano:
            self._tamano = nuevo
            ancho_total = self._tamano + (self.MARGEN_HALO * 2)
            self.resize(ancho_total, ancho_total)
            self.move(centro.x() - ancho_total // 2, centro.y() - ancho_total // 2)
            self._guardar_config()