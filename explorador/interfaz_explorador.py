import os
import math
from functools import partial
from ctypes import wintypes

import json
from PyQt5.QtCore import QDir, Qt, QPointF, QSize, QEvent, QRectF
from PyQt5.QtGui import (
    QPixmap, QColor, QKeySequence, QIcon, QPainter, QPen, QPolygonF, QFont, QCursor
)
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QFileSystemModel,
    QPushButton, QLineEdit, QLabel, QListWidget, QListWidgetItem,
    QMenu, QSplitter, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QHeaderView, QTabWidget, QTabBar, QShortcut, QInputDialog, QApplication,
    QFrame,
)

from . import logica_explorador as logica
from .logica_explorador import VisorArchivos

# ─────────────────────────────────────────────────────────────
# 🎨 PALETA — cálida, idéntica al cuaderno de notas
# ─────────────────────────────────────────────────────────────
BG_APP         = "#242730"
BG_PANEL       = "#2b2e38"
BG_INPUT       = "#1d2028"
BG_INPUT_HOVER = "#20232c"
BORDE          = "#3c3f4a"
BORDE_SUAVE    = "#33363f"
TEXTO          = "#ded8ca"
TEXTO_SEC      = "#8f8b83"
TEXTO_TER      = "#6b6860"
ACENTO         = "#c17a56"   # terracota
ACENTO_HOVER   = "#d38f6c"
ACENTO_SUAVE   = "rgba(193, 122, 86, 0.16)"
DORADO         = "#c9a24b"   # favoritos
DORADO_SUAVE   = "rgba(201, 162, 75, 0.18)"
PELIGRO        = "#a15c52"
PELIGRO_HOVER  = "#b76f64"
FUENTE_SERIF   = "'Georgia', 'Cambria', serif"
FUENTE_UI      = "'Segoe UI', Arial, sans-serif"
FUENTE_META    = "'Consolas', 'Courier New', monospace"

# ─────────────────────────────────────────────────────────────
# 🖌️ ICONOS VECTORIALES — siempre visibles, sin depender de glifos
# ─────────────────────────────────────────────────────────────
def _dibujar_atras(p, s):
    p.drawLine(QPointF(s * 0.72, s * 0.5), QPointF(s * 0.30, s * 0.5))
    p.drawPolyline(QPolygonF([QPointF(s * 0.50, s * 0.28),
                              QPointF(s * 0.30, s * 0.5),
                              QPointF(s * 0.50, s * 0.72)]))

def _dibujar_adelante(p, s):
    p.drawLine(QPointF(s * 0.28, s * 0.5), QPointF(s * 0.70, s * 0.5))
    p.drawPolyline(QPolygonF([QPointF(s * 0.50, s * 0.28),
                              QPointF(s * 0.70, s * 0.5),
                              QPointF(s * 0.50, s * 0.72)]))

def _dibujar_subir(p, s):
    p.drawLine(QPointF(s * 0.5, s * 0.72), QPointF(s * 0.5, s * 0.30))
    p.drawPolyline(QPolygonF([QPointF(s * 0.28, s * 0.50),
                              QPointF(s * 0.50, s * 0.28),
                              QPointF(s * 0.72, s * 0.50)]))

def _dibujar_recargar(p, s):
    c, r = s / 2, s * 0.30
    inicio, fin = math.radians(-60), math.radians(200)
    pasos = 24
    puntos = []
    for i in range(pasos + 1):
        t = inicio + (fin - inicio) * i / pasos
        puntos.append(QPointF(c + r * math.cos(t), c + r * math.sin(t)))
    p.drawPolyline(QPolygonF(puntos))
    # Punta de flecha en el extremo final del arco
    tx, ty = c + r * math.cos(fin), c + r * math.sin(fin)
    dx, dy = -math.sin(fin), math.cos(fin)          # tangente de avance
    largo = s * 0.17
    for da in (math.radians(28), math.radians(-28)):
        rx = dx * math.cos(da) - dy * math.sin(da)
        ry = dx * math.sin(da) + dy * math.cos(da)
        p.drawLine(QPointF(tx, ty), QPointF(tx - largo * rx, ty - largo * ry))

def _estrella(p, s, relleno):
    c, R = s / 2, s * 0.36
    r = R * 0.45
    pts = []
    for i in range(10):
        ang = math.radians(-90 + i * 36)
        rad = R if i % 2 == 0 else r
        pts.append(QPointF(c + rad * math.cos(ang), c + rad * math.sin(ang)))
    if relleno:
        p.setBrush(p.pen().color())
    p.drawPolygon(QPolygonF(pts))
    p.setBrush(Qt.NoBrush)

def _dibujar_favorito_off(p, s): _estrella(p, s, False)
def _dibujar_favorito_on(p, s):  _estrella(p, s, True)

def _dibujar_mas(p, s):
    p.drawLine(QPointF(s * 0.5, s * 0.26), QPointF(s * 0.5, s * 0.74))
    p.drawLine(QPointF(s * 0.26, s * 0.5), QPointF(s * 0.74, s * 0.5))

def _dibujar_cerrar(p, s):
    p.drawLine(QPointF(s * 0.30, s * 0.30), QPointF(s * 0.70, s * 0.70))
    p.drawLine(QPointF(s * 0.70, s * 0.30), QPointF(s * 0.30, s * 0.70))

def _dibujar_minimizar(p, s):
    p.drawLine(QPointF(s * 0.28, s * 0.5), QPointF(s * 0.72, s * 0.5))

def _dibujar_maximizar(p, s):
    p.drawRect(QRectF(s * 0.30, s * 0.30, s * 0.40, s * 0.40))

def _dibujar_restaurar(p, s):
    p.drawRect(QRectF(s * 0.36, s * 0.36, s * 0.36, s * 0.36))
    p.drawPolyline(QPolygonF([QPointF(s * 0.28, s * 0.64),
                              QPointF(s * 0.28, s * 0.28),
                              QPointF(s * 0.64, s * 0.28)]))

_DIBUJANTES = {
    "atras": _dibujar_atras, "adelante": _dibujar_adelante,
    "subir": _dibujar_subir, "recargar": _dibujar_recargar,
    "favorito_off": _dibujar_favorito_off, "favorito_on": _dibujar_favorito_on,
    "mas": _dibujar_mas, "cerrar": _dibujar_cerrar,
    "minimizar": _dibujar_minimizar, "maximizar": _dibujar_maximizar,
    "restaurar": _dibujar_restaurar,
}

_CACHE_ICONOS = {}

def _pixmap_icono(nombre, color, tam=16):
    pix = QPixmap(tam, tam)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing, True)
    pen = QPen(QColor(color))
    pen.setWidthF(1.5)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    _DIBUJANTES[nombre](p, float(tam))
    p.end()
    return pix

def icono_personalizado(nombre, color=TEXTO_SEC, color_hover=ACENTO, color_off=TEXTO_TER):
    """QIcon con estados normal / hover / deshabilitado en la paleta cálida."""
    clave = (nombre, color, color_hover, color_off)
    if clave not in _CACHE_ICONOS:
        icono = QIcon()
        icono.addPixmap(_pixmap_icono(nombre, color), QIcon.Normal)
        icono.addPixmap(_pixmap_icono(nombre, color_hover), QIcon.Active)
        icono.addPixmap(_pixmap_icono(nombre, color_off), QIcon.Disabled)
        _CACHE_ICONOS[clave] = icono
    return _CACHE_ICONOS[clave]

# ─────────────────────────────────────────────────────────────
# 💾 FAVORITOS — persistencia en ~/.gearbook/favoritos.json
# ─────────────────────────────────────────────────────────────
def _ruta_favoritos():
    carpeta = os.path.join(os.path.expanduser("~"), ".gearbook")
    os.makedirs(carpeta, exist_ok=True)
    return os.path.join(carpeta, "favoritos.json")

def cargar_favoritos():
    ruta = _ruta_favoritos()
    if not os.path.exists(ruta):
        return []
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return [r for r in datos if isinstance(r, str) and os.path.isdir(r)]
    except Exception:
        return []

def guardar_favoritos(lista):
    try:
        with open(_ruta_favoritos(), "w", encoding="utf-8") as f:
            json.dump(lista, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

# ─────────────────────────────────────────────────────────────
# 🧩 Pestaña del explorador
# ─────────────────────────────────────────────────────────────
class PestanaExplorador(QWidget):
    def __init__(self, dialogo, model):
        super().__init__(dialogo)
        self.dialogo = dialogo
        self.model = model
        self.historial = logica.HistorialNavegacion()
        self.ruta_actual = os.path.expanduser("~")
        self.modo_actual = "NORMAL"  # NORMAL | PAPELERA | ESTE_EQUIPO
        self.bloqueada = False
        self.grupo = None
        self.ruta_seleccionada = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.vista_archivos = QTreeView()
        self.vista_archivos.setModel(model)
        self.vista_archivos.setContextMenuPolicy(Qt.CustomContextMenu)
        self.vista_archivos.customContextMenuRequested.connect(
            lambda pos: dialogo._mostrar_menu_contextual_normal(pos, self))
        self.vista_archivos.doubleClicked.connect(
            lambda idx: dialogo._doble_click_archivo(idx, self))
        self.vista_archivos.clicked.connect(
            lambda idx: dialogo._click_simple_archivo(idx, self))
        self.vista_archivos.setColumnWidth(0, 380)
        self.vista_archivos.setSortingEnabled(True)
        self.vista_archivos.setAlternatingRowColors(True)
        layout.addWidget(self.vista_archivos)

        self.tabla_virtual = QTableWidget()
        self.tabla_virtual.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_virtual.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_virtual.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabla_virtual.customContextMenuRequested.connect(
            lambda pos: dialogo._mostrar_menu_contextual_virtual(pos, self))
        self.tabla_virtual.clicked.connect(
            lambda idx: dialogo._click_simple_virtual(idx, self))
        self.tabla_virtual.doubleClicked.connect(
            lambda idx: dialogo._doble_click_virtual(idx, self))
        self.tabla_virtual.horizontalHeader().setStretchLastSection(True)
        self.tabla_virtual.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_virtual.verticalHeader().setVisible(False)
        self.tabla_virtual.setCornerButtonEnabled(False)
        self.tabla_virtual.setAlternatingRowColors(True)
        self.tabla_virtual.hide()
        layout.addWidget(self.tabla_virtual)

# ─────────────────────────────────────────────────────────────
# 🧭 Ventana principal del explorador (frameless, estilo Cuaderno)
# ─────────────────────────────────────────────────────────────
class SelectorDestino(QDialog):
    # Constantes Win32 para redimensionar sin marco
    _WM_NCHITTEST = 0x0084
    _HT_CAPTION, _HT_LEFT, _HT_RIGHT, _HT_TOP, _HT_BOTTOM = 2, 10, 11, 12, 15
    _HT_TOPLEFT, _HT_TOPRIGHT = 13, 14
    _HT_BOTTOMLEFT, _HT_BOTTOMRIGHT = 16, 17
    _BORDE_REDIM = 6

    def __init__(self, parent=None, solo_carpetas=False):
        super().__init__(parent)
        self.parent_app = parent
        self.solo_carpetas = solo_carpetas
        self.ruta_seleccionada = ""

        self.grupos = {}
        self._paleta_grupos = [
            DORADO, ACENTO, "#7a9bb5", "#b083c0",
            "#8fb88a", "#c97a8f", "#6bb5a8", "#c9a26b",
        ]
        self.pestanas_cerradas = []
        self.favoritos = cargar_favoritos()

        # Sin barra de Windows: marco propio como el Cuaderno
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setWindowTitle("Explorador de archivos")
        self.resize(1060, 620)

        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        if solo_carpetas:
            self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        else:
            self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)

        self._inicializar_ui()
        self._cargar_accesos_directos()
        self._configurar_atajos()
        self._aplicar_estilos()
        self._aplicar_radio()
        self._nueva_pestana(os.path.expanduser("~"), activar=True)

    # ─────────────── UI ───────────────
    def _inicializar_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.contenedor = QFrame()
        self.contenedor.setObjectName("contenedorExplorador")
        root.addWidget(self.contenedor)

        layout = QVBoxLayout(self.contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Cabecera (igual que el Cuaderno) ──────────────
        self.header = QFrame()
        self.header.setFixedHeight(52)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(16, 0, 10, 0)
        header_layout.setSpacing(10)

        self.lbl_titulo = QLabel("Explorador")
        self.lbl_titulo.setStyleSheet(f"""
            color: {TEXTO}; font-family: {FUENTE_SERIF};
            font-size: 18px; font-weight: 700; letter-spacing: 0.3px;
            border: none; background: transparent;
        """)
        header_layout.addWidget(self.lbl_titulo)

        self.lbl_subtitulo = QLabel("")
        self.lbl_subtitulo.setStyleSheet(f"""
            color: {TEXTO_TER}; font-family: {FUENTE_UI}; font-size: 11px;
            border: none; background: transparent; padding-top: 4px;
        """)
        header_layout.addWidget(self.lbl_subtitulo)
        header_layout.addSpacing(6)

        # Botones de navegación con iconos vectoriales
        self._botones_nav = []
        for nombre_icono, tooltip, fn in [
            ("atras",    "Atrás (Alt+Izq)",   self._click_atras),
            ("adelante", "Adelante (Alt+Der)", self._click_adelante),
            ("subir",    "Subir un nivel",    self._click_subir),
            ("recargar", "Recargar (F5)",     self._click_recargar),
        ]:
            b = QPushButton()
            b.setIcon(icono_personalizado(nombre_icono))
            b.setIconSize(QSize(16, 16))
            b.setToolTip(tooltip)
            b.setFixedSize(30, 30)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(fn)
            b.setProperty("nav", True)
            header_layout.addWidget(b)
            self._botones_nav.append(b)
        self.btn_atras, self.btn_adelante, self.btn_subir, self.btn_recargar = self._botones_nav

        # Breadcrumb navegable
        self.breadcrumb = QHBoxLayout()
        self.breadcrumb.setContentsMargins(6, 0, 6, 0)
        self.breadcrumb.setSpacing(2)
        self.breadcrumb_frame = QFrame()
        self.breadcrumb_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_INPUT};
                border: 1px solid {BORDE};
                border-radius: 7px;
            }}
        """)
        self.breadcrumb_frame.setLayout(self.breadcrumb)
        header_layout.addWidget(self.breadcrumb_frame, 1)

        # Favorito (estrella)
        self.btn_favorito = QPushButton()
        self.btn_favorito.setIcon(icono_personalizado("favorito_off", TEXTO_SEC, DORADO))
        self.btn_favorito.setIconSize(QSize(16, 16))
        self.btn_favorito.setToolTip("Añadir o quitar de favoritos (Ctrl+D)")
        self.btn_favorito.setFixedSize(30, 30)
        self.btn_favorito.setCursor(Qt.PointingHandCursor)
        self.btn_favorito.clicked.connect(self._alternar_favorito)
        header_layout.addWidget(self.btn_favorito)

        header_layout.addSpacing(4)

        # Controles de ventana (fantasma, como el cierre del Cuaderno)
        self.btn_minimizar = QPushButton()
        self.btn_minimizar.setIcon(icono_personalizado("minimizar", TEXTO_SEC, TEXTO))
        self.btn_minimizar.setIconSize(QSize(16, 16))
        self.btn_minimizar.setToolTip("Minimizar")
        self.btn_minimizar.setFixedSize(30, 30)
        self.btn_minimizar.setCursor(Qt.PointingHandCursor)
        self.btn_minimizar.setProperty("winctrl", True)
        self.btn_minimizar.clicked.connect(self.showMinimized)
        header_layout.addWidget(self.btn_minimizar)

        self.btn_maximizar = QPushButton()
        self.btn_maximizar.setIcon(icono_personalizado("maximizar", TEXTO_SEC, TEXTO))
        self.btn_maximizar.setIconSize(QSize(16, 16))
        self.btn_maximizar.setToolTip("Maximizar / restaurar")
        self.btn_maximizar.setFixedSize(30, 30)
        self.btn_maximizar.setCursor(Qt.PointingHandCursor)
        self.btn_maximizar.setProperty("winctrl", True)
        self.btn_maximizar.clicked.connect(self._alternar_maximizado)
        header_layout.addWidget(self.btn_maximizar)

        self.btn_cerrar = QPushButton()
        self.btn_cerrar.setIcon(icono_personalizado("cerrar", TEXTO_SEC, TEXTO))
        self.btn_cerrar.setIconSize(QSize(16, 16))
        self.btn_cerrar.setToolTip("Cerrar")
        self.btn_cerrar.setFixedSize(30, 30)
        self.btn_cerrar.setCursor(Qt.PointingHandCursor)
        self.btn_cerrar.setProperty("winctrl", True)
        self.btn_cerrar.setProperty("cerrar", True)
        self.btn_cerrar.clicked.connect(self.close)
        header_layout.addWidget(self.btn_cerrar)

        layout.addWidget(self.header)

        # Zonas donde se puede arrastrar la ventana (cabecera vacía + títulos)
        self._zonas_arrastre = (self.header, self.lbl_titulo, self.lbl_subtitulo)

        # ── Cuerpo: splitter ──────────────────────────────
        self.splitter = QSplitter(Qt.Horizontal)

        self.lista_lateral = QListWidget()
        self.lista_lateral.setFixedWidth(230)
        self.lista_lateral.itemClicked.connect(self._click_acceso_directo)
        self.lista_lateral.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lista_lateral.customContextMenuRequested.connect(self._menu_lateral)
        self.splitter.addWidget(self.lista_lateral)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(False)   # usamos botón de cierre propio
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.currentChanged.connect(self._pestana_actual_cambiada)
        self.tabs.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabs.tabBar().customContextMenuRequested.connect(self._menu_contextual_pestanas)

        esquina = QWidget()
        lay_esq = QHBoxLayout(esquina)
        lay_esq.setContentsMargins(0, 0, 0, 0)
        lay_esq.setSpacing(4)
        self.btn_nueva_pestana = QPushButton()
        self.btn_nueva_pestana.setIcon(icono_personalizado("mas", TEXTO_SEC, ACENTO))
        self.btn_nueva_pestana.setIconSize(QSize(14, 14))
        self.btn_nueva_pestana.setToolTip("Nueva pestaña (Ctrl+T)")
        self.btn_nueva_pestana.setFixedSize(30, 26)
        self.btn_nueva_pestana.setCursor(Qt.PointingHandCursor)
        self.btn_nueva_pestana.clicked.connect(lambda: self._nueva_pestana(activar=True))
        self.btn_sesiones = QPushButton("Sesiones")
        self.btn_sesiones.setToolTip("Guardar, cargar o eliminar sesiones de pestañas")
        self.btn_sesiones.setCursor(Qt.PointingHandCursor)
        self.btn_sesiones.setFixedHeight(26)
        self.btn_sesiones.clicked.connect(self._menu_sesiones_boton)
        lay_esq.addWidget(self.btn_nueva_pestana)
        lay_esq.addWidget(self.btn_sesiones)
        self.tabs.setCornerWidget(esquina, Qt.TopRightCorner)
        self.splitter.addWidget(self.tabs)
        layout.addWidget(self.splitter, 1)

        # ── Pie ──────────────────────────────────────────
        self.footer = QFrame()
        self.footer.setFixedHeight(42)
        footer_layout = QHBoxLayout(self.footer)
        footer_layout.setContentsMargins(14, 0, 10, 0)
        self.txt_seleccionado = QLineEdit()
        self.txt_seleccionado.setPlaceholderText("Ningún elemento seleccionado")
        self.txt_seleccionado.setReadOnly(True)
        self.lbl_contador = QLabel("")
        self.lbl_contador.setStyleSheet(f"""
            color: {TEXTO_TER}; font-family: {FUENTE_META}; font-size: 10px;
            border: none; background: transparent; padding-right: 8px;
        """)
        self.btn_aceptar = QPushButton("Seleccionar")
        self.btn_aceptar.setCursor(Qt.PointingHandCursor)
        self.btn_aceptar.clicked.connect(self.accept)
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setCursor(Qt.PointingHandCursor)
        self.btn_cancelar.clicked.connect(self.reject)
        footer_layout.addWidget(self.txt_seleccionado, 1)
        footer_layout.addWidget(self.lbl_contador, 0)
        footer_layout.addWidget(self.btn_aceptar, 0)
        footer_layout.addWidget(self.btn_cancelar, 0)
        layout.addWidget(self.footer)

    # ─────────────── Marco propio (frameless) ───────────────
    def _aplicar_radio(self):
        r = 0 if self.isMaximized() else 10
        self.contenedor.setStyleSheet(f"""
            QFrame#contenedorExplorador {{
                background-color: {BG_APP};
                border: 1px solid {BORDE};
                border-radius: {r}px;
            }}
        """)
        self.header.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_PANEL};
                border-bottom: 1px solid {BORDE_SUAVE};
                border-top-left-radius: {r}px;
                border-top-right-radius: {r}px;
            }}
        """)
        self.footer.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_PANEL};
                border-top: 1px solid {BORDE_SUAVE};
                border-bottom-left-radius: {r}px;
                border-bottom-right-radius: {r}px;
            }}
        """)

    def _alternar_maximizado(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            self._aplicar_radio()
            nombre = "restaurar" if self.isMaximized() else "maximizar"
            self.btn_maximizar.setIcon(icono_personalizado(nombre, TEXTO_SEC, TEXTO))
        super().changeEvent(event)

    def nativeEvent(self, eventType, message):
        """Redimensionado por bordes + arrastre desde la cabecera (sin marco)."""
        if eventType == "windows_generic_MSG":
            try:
                msg = wintypes.MSG.from_address(int(message))
            except Exception:
                return super().nativeEvent(eventType, message)
            if msg.message == self._WM_NCHITTEST and not self.isMaximized():
                pos = self.mapFromGlobal(QCursor.pos())
                m = self._BORDE_REDIM
                izq  = pos.x() <= m
                der  = pos.x() >= self.width() - m
                arr  = pos.y() <= m
                abj  = pos.y() >= self.height() - m
                if arr and izq: return True, self._HT_TOPLEFT
                if arr and der: return True, self._HT_TOPRIGHT
                if abj and izq: return True, self._HT_BOTTOMLEFT
                if abj and der: return True, self._HT_BOTTOMRIGHT
                if izq:         return True, self._HT_LEFT
                if der:         return True, self._HT_RIGHT
                if arr:         return True, self._HT_TOP
                if abj:         return True, self._HT_BOTTOM
                hijo = self.childAt(pos)
                if hijo is None or hijo in self._zonas_arrastre:
                    if self.header.frameGeometry().contains(pos):
                        return True, self._HT_CAPTION
        return super().nativeEvent(eventType, message)

    # ─────────────── Accesos directos laterales ───────────────
    def _cargar_accesos_directos(self):
        self.lista_lateral.clear()
        ruta_home = os.path.expanduser("~")
        ruta_descargas = os.path.join(ruta_home, "Downloads")
        ruta_documentos = os.path.join(ruta_home, "Documents")
        ruta_imagenes = os.path.join(ruta_home, "Pictures")

        self._agregar_seccion_lateral("Ubicaciones")
        for nombre, clave_o_ruta in [
            ("Este equipo", "VIRTUAL_ESTE_EQUIPO"),
            ("Perfil",      ruta_home),
            ("Documentos",  ruta_documentos),
            ("Descargas",   ruta_descargas),
            ("Imágenes",    ruta_imagenes),
            ("Papelera",    "VIRTUAL_PAPELERA"),
        ]:
            self._agregar_item_lateral(nombre, clave_o_ruta, es_favorito=False)

        self._agregar_seccion_lateral("Favoritos")
        if not self.favoritos:
            item_vacio = QListWidgetItem("  — sin favoritos aún —")
            item_vacio.setFlags(Qt.NoItemFlags)
            item_vacio.setData(Qt.UserRole, "__VACIO__")
            item_vacio.setData(Qt.UserRole + 1, False)
            self.lista_lateral.addItem(item_vacio)
        else:
            for ruta in self.favoritos:
                nombre = os.path.basename(os.path.normpath(ruta)) or ruta
                self._agregar_item_lateral(f"★  {nombre}", ruta, es_favorito=True)

    def _agregar_seccion_lateral(self, titulo):
        item = QListWidgetItem(titulo.upper())
        item.setFlags(Qt.NoItemFlags)
        item.setData(Qt.UserRole, "__SECCION__")
        item.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.lista_lateral.addItem(item)

    def _agregar_item_lateral(self, nombre, clave_o_ruta, es_favorito):
        item = QListWidgetItem(nombre)
        item.setData(Qt.UserRole, clave_o_ruta)
        item.setData(Qt.UserRole + 1, es_favorito)
        self.lista_lateral.addItem(item)

    # ─────────────── Atajos ───────────────
    def _configurar_atajos(self):
        QShortcut(QKeySequence("Ctrl+T"),       self, activated=lambda: self._nueva_pestana(activar=True))
        QShortcut(QKeySequence("Ctrl+W"),       self, activated=self._cerrar_pestana_actual)
        QShortcut(QKeySequence("Ctrl+Shift+T"), self, activated=self._reabrir_pestana_cerrada)
        QShortcut(QKeySequence("Ctrl+Shift+D"), self, activated=self._duplicar_pestana_actual)
        QShortcut(QKeySequence("Ctrl+L"),       self, activated=self._alternar_bloqueo_pestana_actual)
        QShortcut(QKeySequence("Ctrl+D"),       self, activated=self._alternar_favorito)
        QShortcut(QKeySequence("Alt+Left"),     self, activated=self._click_atras)
        QShortcut(QKeySequence("Alt+Right"),    self, activated=self._click_adelante)
        QShortcut(QKeySequence("F5"),           self, activated=self._click_recargar)
        for n in range(1, 10):
            QShortcut(QKeySequence(f"Ctrl+{n}"),     self, activated=partial(self._ir_a_pestana_indice, n - 1))
            QShortcut(QKeySequence(f"Ctrl+Alt+{n}"), self, activated=partial(self._abrir_seleccion_en_pestana, n - 1))

    # ─────────────── Favoritos ───────────────
    def _alternar_favorito(self):
        pestana = self.tabs.currentWidget()
        if not pestana or pestana.modo_actual != "NORMAL":
            return
        ruta = pestana.ruta_actual
        if ruta in self.favoritos:
            self.favoritos.remove(ruta)
        else:
            self.favoritos.append(ruta)
        guardar_favoritos(self.favoritos)
        self._cargar_accesos_directos()
        self._actualizar_estado_favorito()

    def _actualizar_estado_favorito(self):
        pestana = self.tabs.currentWidget()
        if not pestana or pestana.modo_actual != "NORMAL":
            self.btn_favorito.setIcon(icono_personalizado("favorito_off", TEXTO_TER, TEXTO_TER))
            self.btn_favorito.setEnabled(False)
            return
        self.btn_favorito.setEnabled(True)
        if pestana.ruta_actual in self.favoritos:
            self.btn_favorito.setIcon(icono_personalizado("favorito_on", DORADO, DORADO))
        else:
            self.btn_favorito.setIcon(icono_personalizado("favorito_off", TEXTO_SEC, DORADO))

    # ─────────────── Breadcrumb ───────────────
    def _construir_breadcrumb(self, ruta):
        while self.breadcrumb.count():
            item = self.breadcrumb.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        if not ruta or not os.path.exists(ruta):
            lbl = QLabel(ruta or "")
            lbl.setStyleSheet(f"color:{TEXTO_SEC}; font-family:{FUENTE_UI}; font-size:12px; border:none; background:transparent;")
            self.breadcrumb.addWidget(lbl)
            return
        partes = []
        actual = os.path.normpath(ruta)
        while True:
            partes.insert(0, actual)
            padre = os.path.dirname(actual)
            if padre == actual:
                break
            actual = padre
        for i, parte in enumerate(partes):
            nombre = os.path.basename(parte) or parte
            if len(nombre) <= 1 and parte.endswith(":\\"):
                nombre = parte.rstrip("\\")
            btn = QPushButton(nombre)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("breadcrumb", True)
            es_ultimo = (i == len(partes) - 1)
            if es_ultimo:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent; color: {TEXTO};
                        font-family: {FUENTE_UI}; font-size: 12px; font-weight: 600;
                        border: none; padding: 2px 6px;
                    }}
                """)
                btn.setEnabled(False)
            else:
                btn.clicked.connect(lambda _, r=parte: self._navegar_a(r))
            self.breadcrumb.addWidget(btn)
            if not es_ultimo:
                sep = QLabel("›")
                sep.setStyleSheet(f"color:{TEXTO_TER}; font-size:13px; border:none; background:transparent; padding:0 2px;")
                self.breadcrumb.addWidget(sep)
        self.breadcrumb.addStretch()

    # ─────────────── Pestañas ───────────────
    def _nueva_pestana(self, destino=None, bloqueada=False, grupo=None, activar=True):
        destino = destino or os.path.expanduser("~")
        pestana = PestanaExplorador(self, self.model)
        self.tabs.addTab(pestana, "…")

        # Botón de cierre propio (coherente con la paleta)
        idx = self.tabs.indexOf(pestana)
        btn_cierre = QPushButton()
        btn_cierre.setIcon(icono_personalizado("cerrar", TEXTO_TER, TEXTO))
        btn_cierre.setIconSize(QSize(12, 12))
        btn_cierre.setFixedSize(18, 18)
        btn_cierre.setCursor(Qt.PointingHandCursor)
        btn_cierre.setToolTip("Cerrar pestaña (Ctrl+W)")
        btn_cierre.setProperty("tabclose", True)
        btn_cierre.clicked.connect(lambda _, p=pestana: self._cerrar_pestana(self.tabs.indexOf(p)))
        self.tabs.tabBar().setTabButton(idx, QTabBar.RightSide, btn_cierre)

        if grupo:
            self._aplicar_grupo(pestana, grupo)
        self._navegar_a(destino, pestana, registrar_historial=True)
        pestana.bloqueada = bloqueada
        self._actualizar_titulo_pestana(pestana)
        if activar:
            self.tabs.setCurrentWidget(pestana)
        self._actualizar_subtitulo()
        return pestana

    def _cerrar_pestana(self, index):
        if self.tabs.count() <= 1:
            return
        pestana = self.tabs.widget(index)
        if pestana is None:
            return
        self.pestanas_cerradas.append(self._exportar_estado_pestana(pestana))
        self.tabs.removeTab(index)
        pestana.deleteLater()
        self._actualizar_subtitulo()

    def _cerrar_pestana_actual(self):
        idx = self.tabs.currentIndex()
        if idx >= 0:
            self._cerrar_pestana(idx)

    def _reabrir_pestana_cerrada(self):
        if not self.pestanas_cerradas:
            return
        estado = self.pestanas_cerradas.pop()
        self._nueva_pestana(estado.get("ruta"), estado.get("bloqueada", False), estado.get("grupo"), activar=True)

    def _duplicar_pestana_actual(self):
        pestana = self.tabs.currentWidget()
        if not pestana:
            return
        estado = self._exportar_estado_pestana(pestana)
        self._nueva_pestana(estado["ruta"], estado["bloqueada"], estado["grupo"], activar=True)

    def _alternar_bloqueo_pestana_actual(self):
        pestana = self.tabs.currentWidget()
        if not pestana:
            return
        pestana.bloqueada = not pestana.bloqueada
        self._actualizar_titulo_pestana(pestana)
        self._actualizar_estado_navegacion(pestana)

    def _ir_a_pestana_indice(self, indice):
        if 0 <= indice < self.tabs.count():
            self.tabs.setCurrentIndex(indice)

    def _abrir_seleccion_en_pestana(self, indice_destino):
        pestana_actual = self.tabs.currentWidget()
        ruta = pestana_actual.ruta_seleccionada if pestana_actual else ""
        if not ruta or not os.path.isdir(ruta):
            return
        while self.tabs.count() <= indice_destino:
            self._nueva_pestana(activar=False)
        pestana_destino = self.tabs.widget(indice_destino)
        self._navegar_a(ruta, pestana_destino, registrar_historial=True)
        self.tabs.setCurrentIndex(indice_destino)

    def _aplicar_grupo(self, pestana, nombre_grupo):
        pestana.grupo = nombre_grupo
        if nombre_grupo and nombre_grupo not in self.grupos:
            color = self._paleta_grupos[len(self.grupos) % len(self._paleta_grupos)]
            self.grupos[nombre_grupo] = color
        self._actualizar_titulo_pestana(pestana)

    def _nombre_visible(self, pestana):
        if pestana.modo_actual == "ESTE_EQUIPO":
            return "Este equipo"
        if pestana.modo_actual == "PAPELERA":
            return "Papelera"
        nombre = os.path.basename(os.path.normpath(pestana.ruta_actual))
        return nombre or pestana.ruta_actual

    def _actualizar_titulo_pestana(self, pestana):
        idx = self.tabs.indexOf(pestana)
        if idx == -1:
            return
        prefijo = "🔒 " if pestana.bloqueada else ""
        if pestana.grupo:
            prefijo += "● "
        self.tabs.setTabText(idx, f"{prefijo}{self._nombre_visible(pestana)}")
        tooltip = pestana.ruta_actual if pestana.modo_actual == "NORMAL" else self._nombre_visible(pestana)
        if pestana.grupo:
            tooltip += f"  [grupo: {pestana.grupo}]"
        self.tabs.setTabToolTip(idx, tooltip)
        color = self.grupos.get(pestana.grupo, TEXTO) if pestana.grupo else TEXTO
        self.tabs.tabBar().setTabTextColor(idx, QColor(color))

    def _actualizar_subtitulo(self):
        n = self.tabs.count()
        self.lbl_subtitulo.setText(f"{n} pestaña{'s' if n != 1 else ''}")

    def _exportar_estado_pestana(self, pestana):
        if pestana.modo_actual == "ESTE_EQUIPO":
            ruta = "VIRTUAL_ESTE_EQUIPO"
        elif pestana.modo_actual == "PAPELERA":
            ruta = "VIRTUAL_PAPELERA"
        else:
            ruta = pestana.ruta_actual
        return {"ruta": ruta, "bloqueada": pestana.bloqueada, "grupo": pestana.grupo}

    def _pestana_actual_cambiada(self, index):
        pestana = self.tabs.widget(index)
        if not pestana:
            return
        self._actualizar_estado_navegacion(pestana)
        self._sincronizar_barra_direccion(pestana)
        self._actualizar_estado_favorito()

    # ─────────────── Sesiones ───────────────
    def _menu_sesiones_boton(self):
        menu = QMenu(self)
        accion_guardar = menu.addAction("Guardar sesión actual")
        submenu_cargar = menu.addMenu("Cargar sesión")
        sesiones = logica.listar_sesiones()
        acciones_cargar = {}
        acciones_eliminar = {}
        if sesiones:
            for s in sesiones:
                a = submenu_cargar.addAction(s)
                acciones_cargar[a] = s
            submenu_eliminar = menu.addMenu("Eliminar sesión")
            for s in sesiones:
                a = submenu_eliminar.addAction(s)
                acciones_eliminar[a] = s
        else:
            a_vacio = submenu_cargar.addAction("(sin sesiones guardadas)")
            a_vacio.setEnabled(False)
        elegida = menu.exec_(self.btn_sesiones.mapToGlobal(self.btn_sesiones.rect().bottomLeft()))
        if elegida is None:
            return
        if elegida == accion_guardar:
            self._guardar_sesion_actual()
        elif elegida in acciones_cargar:
            self._cargar_sesion(acciones_cargar[elegida])
        elif elegida in acciones_eliminar:
            logica.eliminar_sesion(acciones_eliminar[elegida])

    def _guardar_sesion_actual(self):
        if self.tabs.count() == 0:
            return
        nombre, ok = QInputDialog.getText(self, "Guardar sesión", "Nombre de la sesión:")
        if not ok or not nombre.strip():
            return
        pestanas_info = [self._exportar_estado_pestana(self.tabs.widget(i)) for i in range(self.tabs.count())]
        logica.guardar_sesion(nombre.strip(), pestanas_info)

    def _cargar_sesion(self, nombre_sesion):
        pestanas_info, error = logica.cargar_sesion(nombre_sesion)
        if error:
            return
        for i in reversed(range(self.tabs.count())):
            pestana = self.tabs.widget(i)
            self.tabs.removeTab(i)
            pestana.deleteLater()
        for info in pestanas_info:
            self._nueva_pestana(info.get("ruta"), info.get("bloqueada", False), info.get("grupo"), activar=False)
        if self.tabs.count() > 0:
            self.tabs.setCurrentIndex(0)
        else:
            self._nueva_pestana(activar=True)
        self._actualizar_subtitulo()

    # ─────────────── Navegación ───────────────
    def _click_acceso_directo(self, item):
        destino = item.data(Qt.UserRole)
        if destino in ("__SECCION__", "__VACIO__", None):
            return
        self._navegar_a(destino)

    def _menu_lateral(self, pos):
        item = self.lista_lateral.itemAt(pos)
        if not item:
            return
        es_fav = item.data(Qt.UserRole + 1)
        ruta = item.data(Qt.UserRole)
        if not es_fav or not isinstance(ruta, str):
            return
        menu = QMenu(self)
        accion_quitar = menu.addAction("Quitar de favoritos")
        elegida = menu.exec_(self.lista_lateral.mapToGlobal(pos))
        if elegida == accion_quitar:
            if ruta in self.favoritos:
                self.favoritos.remove(ruta)
                guardar_favoritos(self.favoritos)
                self._cargar_accesos_directos()
                self._actualizar_estado_favorito()

    def _navegar_a(self, destino, pestana=None, registrar_historial=True):
        pestana = pestana or self.tabs.currentWidget()
        if pestana is None:
            return
        if pestana.bloqueada:
            return
        if destino == "VIRTUAL_PAPELERA":
            self._cargar_vista_papelera_virtual(pestana)
        elif destino == "VIRTUAL_ESTE_EQUIPO":
            self._cargar_vista_este_equipo(pestana)
        else:
            if not os.path.exists(destino):
                return
            self._ir_a_ruta(destino, pestana)
        if registrar_historial:
            pestana.historial.visitar(destino)
        self._actualizar_estado_navegacion(pestana)
        self._actualizar_titulo_pestana(pestana)
        if pestana is self.tabs.currentWidget():
            self._sincronizar_barra_direccion(pestana)
            self._actualizar_estado_favorito()

    def _ir_a_ruta(self, ruta, pestana):
        pestana.modo_actual = "NORMAL"
        pestana.tabla_virtual.hide()
        pestana.vista_archivos.show()
        if os.path.exists(ruta):
            pestana.ruta_actual = ruta
            idx = self.model.index(ruta)
            pestana.vista_archivos.setRootIndex(idx)
            if pestana.vista_archivos.selectionModel():
                pestana.vista_archivos.selectionModel().clearSelection()
            pestana.ruta_seleccionada = ""
            self._actualizar_contador(pestana)
            if pestana is self.tabs.currentWidget():
                self.txt_seleccionado.setText("")

    def _cargar_vista_este_equipo(self, pestana):
        pestana.modo_actual = "ESTE_EQUIPO"
        pestana.vista_archivos.hide()
        pestana.tabla_virtual.show()
        tabla = pestana.tabla_virtual
        tabla.setRowCount(0)
        tabla.setColumnCount(3)
        tabla.setHorizontalHeaderLabels(["Unidad", "Tipo", "Espacio disponible"])
        pestana.ruta_seleccionada = ""
        if pestana is self.tabs.currentWidget():
            self.txt_seleccionado.setText("")
            self.lbl_contador.setText("")
        for disco in logica.listar_discos_locales():
            row = tabla.rowCount()
            tabla.insertRow(row)
            item_nombre = QTableWidgetItem(disco["nombre"])
            item_tipo = QTableWidgetItem(disco["tipo"])
            item_espacio = QTableWidgetItem(disco["espacio"])
            item_nombre.setData(Qt.UserRole, disco["ruta"])
            tabla.setItem(row, 0, item_nombre)
            tabla.setItem(row, 1, item_tipo)
            tabla.setItem(row, 2, item_espacio)

    def _cargar_vista_papelera_virtual(self, pestana):
        pestana.modo_actual = "PAPELERA"
        pestana.vista_archivos.hide()
        pestana.tabla_virtual.show()
        tabla = pestana.tabla_virtual
        tabla.setRowCount(0)
        tabla.setColumnCount(3)
        tabla.setHorizontalHeaderLabels(["Nombre", "Ubicación original", "Tamaño / Tipo"])
        pestana.ruta_seleccionada = ""
        if pestana is self.tabs.currentWidget():
            self.txt_seleccionado.setText("")
            self.lbl_contador.setText("")
        items, error = logica.listar_items_papelera()
        for item in items:
            row = tabla.rowCount()
            tabla.insertRow(row)
            item_nombre = QTableWidgetItem(item["nombre"])
            item_origen = QTableWidgetItem(item["origen"])
            item_extra = QTableWidgetItem(item["detalles"])
            item_nombre.setData(Qt.UserRole, item["com_item"])
            tabla.setItem(row, 0, item_nombre)
            tabla.setItem(row, 1, item_origen)
            tabla.setItem(row, 2, item_extra)

    def _actualizar_estado_navegacion(self, pestana=None):
        pestana = pestana or self.tabs.currentWidget()
        if not pestana or pestana is not self.tabs.currentWidget():
            return
        self.btn_atras.setEnabled(pestana.historial.puede_retroceder())
        self.btn_adelante.setEnabled(pestana.historial.puede_avanzar())
        self.btn_subir.setEnabled(pestana.modo_actual == "NORMAL" and not pestana.bloqueada)

    def _actualizar_contador(self, pestana):
        if pestana.modo_actual != "NORMAL":
            self.lbl_contador.setText("")
            return
        try:
            idx = self.model.index(pestana.ruta_actual)
            filas = self.model.rowCount(idx)
            self.lbl_contador.setText(f"{filas} elemento{'s' if filas != 1 else ''}")
        except Exception:
            self.lbl_contador.setText("")

    def _sincronizar_barra_direccion(self, pestana):
        if pestana.modo_actual == "PAPELERA":
            self._construir_breadcrumb_texto("Papelera de reciclaje")
        elif pestana.modo_actual == "ESTE_EQUIPO":
            self._construir_breadcrumb_texto("Este equipo")
        else:
            self._construir_breadcrumb(pestana.ruta_actual)
        self.txt_seleccionado.setText(pestana.ruta_seleccionada)

    def _construir_breadcrumb_texto(self, texto):
        while self.breadcrumb.count():
            item = self.breadcrumb.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        lbl = QLabel(texto)
        lbl.setStyleSheet(f"color:{TEXTO}; font-family:{FUENTE_UI}; font-size:12px; font-weight:600; border:none; background:transparent; padding:2px 8px;")
        self.breadcrumb.addWidget(lbl)
        self.breadcrumb.addStretch()

    def _click_atras(self):
        pestana = self.tabs.currentWidget()
        if not pestana:
            return
        destino = pestana.historial.retroceder()
        if destino is not None:
            self._navegar_a(destino, pestana, registrar_historial=False)

    def _click_adelante(self):
        pestana = self.tabs.currentWidget()
        if not pestana:
            return
        destino = pestana.historial.avanzar()
        if destino is not None:
            self._navegar_a(destino, pestana, registrar_historial=False)

    def _click_subir(self):
        pestana = self.tabs.currentWidget()
        if not pestana or pestana.modo_actual != "NORMAL" or pestana.bloqueada:
            return
        padre = logica.obtener_carpeta_padre(pestana.ruta_actual)
        if padre and padre != pestana.ruta_actual:
            self._navegar_a(padre, pestana)

    def _click_recargar(self):
        pestana = self.tabs.currentWidget()
        if not pestana:
            return
        if pestana.modo_actual == "NORMAL":
            self._navegar_a(pestana.ruta_actual, pestana, registrar_historial=False)
        elif pestana.modo_actual == "ESTE_EQUIPO":
            self._navegar_a("VIRTUAL_ESTE_EQUIPO", pestana, registrar_historial=False)
        elif pestana.modo_actual == "PAPELERA":
            self._navegar_a("VIRTUAL_PAPELERA", pestana, registrar_historial=False)

    # ─────────────── Interacción ───────────────
    def _click_simple_archivo(self, index, pestana):
        ruta = self.model.filePath(index)
        if self.solo_carpetas and not self.model.isDir(index):
            return
        pestana.ruta_seleccionada = ruta
        self.ruta_seleccionada = ruta
        if pestana is self.tabs.currentWidget():
            self.txt_seleccionado.setText(ruta)

    def _click_simple_virtual(self, index, pestana):
        row = index.row()
        item_nombre = pestana.tabla_virtual.item(row, 0)
        if not item_nombre:
            return
        if pestana.modo_actual == "PAPELERA":
            pestana.ruta_seleccionada = ""
            if pestana is self.tabs.currentWidget():
                self.txt_seleccionado.setText(item_nombre.text())
        elif pestana.modo_actual == "ESTE_EQUIPO":
            ruta_disco = item_nombre.data(Qt.UserRole)
            pestana.ruta_seleccionada = ruta_disco
            self.ruta_seleccionada = ruta_disco
            if pestana is self.tabs.currentWidget():
                self.txt_seleccionado.setText(ruta_disco)

    def _doble_click_virtual(self, index, pestana):
        row = index.row()
        item_nombre = pestana.tabla_virtual.item(row, 0)
        if item_nombre and pestana.modo_actual == "ESTE_EQUIPO":
            ruta_disco = item_nombre.data(Qt.UserRole)
            if ruta_disco and os.path.exists(ruta_disco):
                if QApplication.keyboardModifiers() & Qt.ControlModifier:
                    self._nueva_pestana(ruta_disco, activar=True)
                else:
                    self._navegar_a(ruta_disco, pestana)

    def _doble_click_archivo(self, index, pestana):
        ruta = self.model.filePath(index)
        if self.model.isDir(index):
            if QApplication.keyboardModifiers() & Qt.ControlModifier:
                self._nueva_pestana(ruta, activar=True)
            else:
                self._navegar_a(ruta, pestana)
        else:
            if not self.solo_carpetas:
                pestana.ruta_seleccionada = ruta
                self.ruta_seleccionada = ruta
                self.accept()

    def directory(self):
        class MockDirectory:
            def __init__(self, path): self.path = path
            def absolutePath(self): return self.path
        pestana = self.tabs.currentWidget()
        if not pestana:
            return MockDirectory(os.path.expanduser("~"))
        if pestana.modo_actual == "PAPELERA":
            return MockDirectory("virtual://papelera")
        elif pestana.modo_actual == "ESTE_EQUIPO":
            return MockDirectory("virtual://este_equipo")
        return MockDirectory(pestana.ruta_actual)

    def selectedFiles(self):
        return [self.ruta_seleccionada] if self.ruta_seleccionada else []

    def setLabelText(self, tipo_boton, texto):
        if self.btn_aceptar:
            self.btn_aceptar.setText(texto)

    # ─────────────── Menús contextuales ───────────────
    def _mostrar_menu_contextual_normal(self, pos, pestana):
        index = pestana.vista_archivos.indexAt(pos)
        menu = QMenu(self)
        acciones_pestana = {}
        ruta_objetivo = None
        accion_nueva = menu.addAction("Nueva carpeta")
        accion_nueva.triggered.connect(lambda: logica.crear_carpeta_nueva(pestana.ruta_actual))
        menu.addSeparator()
        if index.isValid():
            ruta_objetivo = self.model.filePath(index)
            visualizable, tipo, _ = logica.obtener_tipo_visor(ruta_objetivo)
            if visualizable:
                accion_visor = menu.addAction("Previsualizar")
                accion_visor.triggered.connect(lambda: VisorArchivos(ruta_objetivo, tipo, self).exec_())
                menu.addSeparator()
            if os.path.isdir(ruta_objetivo):
                accion_pestana_nueva = menu.addAction("Abrir en nueva pestaña")
                accion_pestana_nueva.triggered.connect(lambda: self._nueva_pestana(ruta_objetivo, activar=True))
                if self.tabs.count() > 1:
                    submenu_abrir_en = menu.addMenu("Abrir en pestaña…")
                    for i in range(self.tabs.count()):
                        if self.tabs.widget(i) is pestana:
                            continue
                        etiqueta = self.tabs.tabText(i).strip() or f"Pestaña {i + 1}"
                        a = submenu_abrir_en.addAction(f"{i + 1}. {etiqueta}")
                        acciones_pestana[a] = i
                menu.addSeparator()
            if os.path.isfile(ruta_objetivo) and ruta_objetivo.lower().endswith((".mp4", ".mp3")):
                accion_reproducir = menu.addAction("Reproducir")
                accion_reproducir.triggered.connect(lambda: logica.reproducir_archivo(ruta_objetivo))
                menu.addSeparator()
            accion_copiar = menu.addAction("Copiar")
            accion_copiar.triggered.connect(lambda: logica.copiar_al_portapapeles(ruta_objetivo))
            accion_cortar = menu.addAction("Cortar")
            accion_cortar.triggered.connect(lambda: logica.cortar_al_portapapeles(ruta_objetivo))
            menu.addSeparator()
            accion_eliminar = menu.addAction("Eliminar")
            accion_eliminar.triggered.connect(lambda: logica.borrar_elemento_nativo(ruta_objetivo))
            menu.addSeparator()
        accion_pegar = menu.addAction("Pegar aquí")
        accion_pegar.setEnabled(logica.hay_elemento_en_portapapeles() and not pestana.bloqueada)
        accion_pegar.triggered.connect(lambda: logica.pegar_desde_portapapeles(pestana.ruta_actual))
        menu.addSeparator()
        accion_ordenar = menu.addAction("Ordenar carpeta")
        accion_ordenar.triggered.connect(lambda: self._ejecutar_ordenar_directo(pestana))
        accion_elegida = menu.exec_(pestana.vista_archivos.viewport().mapToGlobal(pos))
        if accion_elegida is not None and accion_elegida in acciones_pestana and ruta_objetivo is not None:
            self._navegar_a(ruta_objetivo, self.tabs.widget(acciones_pestana[accion_elegida]))

    def _mostrar_menu_contextual_virtual(self, pos, pestana):
        index = pestana.tabla_virtual.indexAt(pos)
        if not index.isValid() or pestana.modo_actual != "PAPELERA":
            return
        menu = QMenu(self)
        row = index.row()
        item_nombre = pestana.tabla_virtual.item(row, 0)
        win_item = item_nombre.data(Qt.UserRole)
        accion_restaurar = menu.addAction("Restaurar")
        accion_destruir = menu.addAction("Eliminar definitivamente")
        accion_restaurar.triggered.connect(lambda: (logica.restaurar_item_papelera(win_item), self._cargar_vista_papelera_virtual(pestana)))
        accion_destruir.triggered.connect(lambda: (logica.destruir_item_papelera(win_item), self._cargar_vista_papelera_virtual(pestana)))
        menu.exec_(pestana.tabla_virtual.viewport().mapToGlobal(pos))

    def _menu_contextual_pestanas(self, pos):
        index = self.tabs.tabBar().tabAt(pos)
        if index == -1:
            return
        pestana = self.tabs.widget(index)
        if not pestana:
            return
        menu = QMenu(self)
        menu.addAction("Nueva pestaña").triggered.connect(lambda: self._nueva_pestana(activar=True))
        menu.addAction("Duplicar pestaña").triggered.connect(lambda: (self.tabs.setCurrentWidget(pestana), self._duplicar_pestana_actual()))
        texto_bloqueo = "Desbloquear pestaña" if pestana.bloqueada else "Bloquear pestaña"
        menu.addAction(texto_bloqueo).triggered.connect(self._toggle_bloqueo_pestana(pestana))
        menu.addSeparator()
        submenu_grupo = menu.addMenu("Agrupar pestaña")
        if pestana.grupo:
            submenu_grupo.addAction("Quitar de grupo").triggered.connect(lambda: self._quitar_grupo(pestana))
            submenu_grupo.addSeparator()
        for nombre_g in self.grupos:
            submenu_grupo.addAction(f"● {nombre_g}").triggered.connect(lambda _, n=nombre_g: self._aplicar_grupo(pestana, n))
        submenu_grupo.addAction("＋ Nuevo grupo…").triggered.connect(lambda: self._nuevo_grupo_dialog(pestana))
        menu.addSeparator()
        menu.addAction("Cerrar pestaña").triggered.connect(lambda: self._cerrar_pestana(index))
        menu.addAction("Cerrar las demás").triggered.connect(lambda: [self._cerrar_pestana(i) for i in reversed(range(self.tabs.count())) if i != index])
        menu.addSeparator()
        menu.addAction("Guardar sesión de pestañas").triggered.connect(self._guardar_sesion_actual)
        submenu_cargar = menu.addMenu("Cargar sesión")
        sesiones = logica.listar_sesiones()
        if sesiones:
            for s in sesiones:
                submenu_cargar.addAction(s).triggered.connect(lambda _, n=s: self._cargar_sesion(n))
        else:
            a = submenu_cargar.addAction("(sin sesiones guardadas)")
            a.setEnabled(False)
        menu.exec_(self.tabs.tabBar().mapToGlobal(pos))

    def _toggle_bloqueo_pestana(self, pestana):
        def _do():
            pestana.bloqueada = not pestana.bloqueada
            self._actualizar_titulo_pestana(pestana)
            if pestana is self.tabs.currentWidget():
                self._actualizar_estado_navegacion(pestana)
        return _do

    def _quitar_grupo(self, pestana):
        pestana.grupo = None
        self._actualizar_titulo_pestana(pestana)

    def _nuevo_grupo_dialog(self, pestana):
        nombre_g, ok = QInputDialog.getText(self, "Nuevo grupo", "Nombre del grupo:")
        if ok and nombre_g.strip():
            self._aplicar_grupo(pestana, nombre_g.strip())

    def _ejecutar_ordenar_directo(self, pestana):
        if os.path.exists(pestana.ruta_actual) and self.parent_app:
            logica.ejecutar_ordenar(self.parent_app, pestana.ruta_actual)

    # ─────────────── Estilos ───────────────
    def _aplicar_estilos(self):
        self.setStyleSheet(f"""
            QDialog {{ background: transparent; }}
            QWidget {{ background-color: {BG_APP}; color: {TEXTO}; font-family: {FUENTE_UI}; font-size: 12px; }}

            /* Botones de navegación de la cabecera */
            QPushButton[nav="true"] {{
                background-color: {BG_INPUT};
                border: 1px solid {BORDE};
                border-radius: 6px;
            }}
            QPushButton[nav="true"]:hover {{ background-color: {BG_INPUT_HOVER}; border-color: {ACENTO}; }}
            QPushButton[nav="true"]:disabled {{ background-color: {BG_APP}; border-color: {BORDE_SUAVE}; }}

            /* Controles de ventana (fantasma) */
            QPushButton[winctrl="true"] {{
                background: transparent; border: none; border-radius: 6px;
            }}
            QPushButton[winctrl="true"]:hover {{ background-color: {BG_INPUT_HOVER}; }}
            QPushButton[winctrl="true"][cerrar="true"]:hover {{ background-color: {PELIGRO}; }}

            /* Cierre de pestaña */
            QPushButton[tabclose="true"] {{
                background: transparent; border: none; border-radius: 4px;
            }}
            QPushButton[tabclose="true"]:hover {{ background-color: {PELIGRO}; }}

            /* Botones genéricos */
            QPushButton {{
                background-color: {BG_INPUT};
                color: {TEXTO_SEC};
                border: 1px solid {BORDE};
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                padding: 0 10px;
            }}
            QPushButton:hover {{ background-color: {BG_INPUT_HOVER}; color: {ACENTO}; border-color: {ACENTO}; }}
            QPushButton:pressed {{ background-color: {ACENTO_SUAVE}; }}
            QPushButton:disabled {{ background-color: {BG_APP}; color: {TEXTO_TER}; border-color: {BORDE_SUAVE}; }}

            /* Breadcrumb interno */
            QPushButton[breadcrumb="true"] {{
                background: transparent; color: {TEXTO_SEC}; border: none;
                font-family: {FUENTE_UI}; font-size: 12px; padding: 2px 6px; border-radius: 4px;
            }}
            QPushButton[breadcrumb="true"]:hover {{ background: {BG_INPUT_HOVER}; color: {ACENTO}; }}

            /* Barra lateral */
            QListWidget {{
                background-color: {BG_PANEL};
                border: none; outline: none;
                color: {TEXTO}; font-size: 12px;
            }}
            QListWidget::item {{
                padding: 6px 12px; border-radius: 6px; margin: 1px 6px;
            }}
            QListWidget::item:hover {{ background-color: {BG_INPUT_HOVER}; }}
            QListWidget::item:selected {{ background-color: {ACENTO_SUAVE}; color: {ACENTO}; border: 1px solid {ACENTO}; }}
            QListWidget::item:disabled {{ color: {TEXTO_TER}; background: transparent; }}

            /* Vista de archivos */
            QTreeView, QTableWidget {{
                background-color: {BG_APP};
                color: {TEXTO};
                border: none; outline: none;
                alternate-background-color: {BG_PANEL};
            }}
            QTreeView::item, QTableWidget::item {{ padding: 4px 6px; border-radius: 4px; }}
            QTreeView::item:hover, QTableWidget::item:hover {{ background-color: {BG_INPUT_HOVER}; }}
            QTreeView::item:selected, QTableWidget::item:selected {{
                background-color: {ACENTO_SUAVE}; color: {ACENTO};
            }}
            QHeaderView::section {{
                background-color: {BG_PANEL}; color: {TEXTO_SEC};
                border: none; border-bottom: 1px solid {BORDE_SUAVE};
                padding: 6px; font-weight: 600; font-size: 11px;
            }}

            /* Inputs */
            QLineEdit {{
                background-color: {BG_INPUT};
                color: {TEXTO};
                border: 1px solid {BORDE};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 12px;
            }}
            QLineEdit:focus {{ border-color: {ACENTO}; }}

            /* Splitter */
            QSplitter::handle {{ background-color: {BORDE_SUAVE}; width: 1px; }}
            QSplitter::handle:hover {{ background-color: {ACENTO}; }}

            /* Menús */
            QMenu {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDE};
                color: {TEXTO};
                padding: 4px;
                border-radius: 6px;
            }}
            QMenu::item {{ padding: 6px 24px 6px 12px; border-radius: 4px; }}
            QMenu::item:selected {{ background-color: {ACENTO_SUAVE}; color: {ACENTO}; }}
            QMenu::separator {{ height: 1px; background: {BORDE_SUAVE}; margin: 4px 8px; }}

            /* Pestañas */
            QTabWidget::pane {{ border: none; background-color: {BG_APP}; }}
            QTabBar::tab {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDE_SUAVE};
                border-bottom: none;
                padding: 6px 12px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-size: 12px;
            }}
            QTabBar::tab:selected {{ background-color: {BG_APP}; border-color: {ACENTO}; }}
            QTabBar::tab:hover:!selected {{ background-color: {BG_INPUT_HOVER}; }}

            /* Scrollbars */
            QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; }}
            QScrollBar::handle:vertical {{ background: {BORDE}; border-radius: 4px; min-height: 24px; }}
            QScrollBar::handle:vertical:hover {{ background: {TEXTO_TER}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
        self.btn_aceptar.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACENTO}; color: {BG_APP};
                border: none; border-radius: 6px;
                padding: 6px 18px; font-weight: 700;
            }}
            QPushButton:hover {{ background-color: {ACENTO_HOVER}; color: {BG_APP}; }}
        """)
        self.btn_cancelar.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: {TEXTO_SEC};
                border: 1px solid {BORDE}; border-radius: 6px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{ border-color: {PELIGRO}; color: {PELIGRO}; }}
        """)