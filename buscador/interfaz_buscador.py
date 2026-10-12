import os
import re
import sys
import time
import html
import subprocess
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
                             QListWidget, QListWidgetItem, QPushButton, QFrame,
                             QApplication, QMenu, QMessageBox, QShortcut, QCheckBox,
                             QComboBox, QGridLayout, QScrollArea, QFileDialog,
                             QSizeGrip, QTextEdit)
from PyQt5.QtCore import (Qt, QTimer, QPoint, QThread, pyqtSignal, QSize, QEvent,
                          QMimeData, QUrl)
from PyQt5.QtGui import QKeySequence, QPixmap, QImageReader
from buscador import logica_buscador as logica


# ─────────────────────────────────────────────────────────────
# 🎨 PALETA — la misma que el módulo de Notas
# (cálida, de bajo contraste, sin verdes ni blanco/negro puros)
# ─────────────────────────────────────────────────────────────
BG_APP = "#242730"
BG_PANEL = "#2b2e38"
BG_INPUT = "#1d2028"
BG_INPUT_HOVER = "#20232c"
BORDE = "#3c3f4a"
BORDE_SUAVE = "#33363f"
TEXTO_PRINCIPAL = "#ded8ca"
TEXTO_SECUNDARIO = "#8f8b83"
TEXTO_TERCIARIO = "#6b6860"
ACENTO = "#c17a56"
ACENTO_HOVER = "#d38f6c"
ACENTO_SUAVE = "rgba(193, 122, 86, 0.16)"
ACENTO_MEDIO = "rgba(193, 122, 86, 0.32)"
DORADO = "#c9a24b"
DORADO_SUAVE = "rgba(201, 162, 75, 0.18)"
PELIGRO = "#a15c52"
PELIGRO_HOVER = "#b76f64"

FUENTE_SERIF = "'Georgia', 'Cambria', 'Constantia', serif"
FUENTE_UI = "'Segoe UI', Arial, sans-serif"
FUENTE_META = "'Consolas', 'Courier New', monospace"


# ═══════════════════════════════════════════════════════════
# 🏷️ CATEGORÍAS, ORDEN Y AYUDA
# ═══════════════════════════════════════════════════════════
CATEGORIAS_FILTRO = [
    ("Todo",        "🌐"),
    ("Documentos",  "📄"),
    ("Imágenes",    "🖼️"),
    ("Videos",      "🎬"),
    ("Música",      "🎵"),
    ("Código",      "💻"),
    ("Comprimidos", "📦"),
    ("Carpetas",    "📁"),
    ("Otros",       "📎"),
]
ICONOS_CATEGORIA = {cat: icon for cat, icon in CATEGORIAS_FILTRO}

OPCIONES_ORDEN = [
    ("Relevancia",            "relevancia"),
    ("Nombre (A-Z)",          "nombre"),
    ("Nombre (Z-A)",          "nombre_desc"),
    ("Más recientes",         "fecha"),
    ("Más antiguos",          "fecha_asc"),
    ("Tamaño: mayor primero", "tamano"),
    ("Tamaño: menor primero", "tamano_asc"),
]

TAMANO_PAGINA = 80

# Alias reconocidos por cada tipo de modificador (para sustituirlos desde el menú)
_ALIAS_MODIFICADOR = {
    "fecha": "fecha|modificado|date",
    "size": "size|tamano|tamaño",
    "ext": "ext|extension",
}

AYUDA_SINTAXIS = (
    "Puedes combinar texto y filtros en la misma búsqueda:\n\n"
    "  informe final        → ambas palabras, en cualquier orden\n"
    "  \"informe final\"      → frase exacta\n"
    "  factura -borrador    → excluye lo que contenga «borrador»\n"
    "  ext:pdf  ·  ext:doc,docx   → por extensión\n"
    "  carpeta:descargas    → dentro de rutas que contengan eso\n"
    "  size:>10mb  ·  size:<500kb → por tamaño\n"
    "  fecha:hoy  ·  fecha:semana  ·  fecha:mes  ·  fecha:7d  ·  fecha:2025-01-31\n\n"
    "Ejemplo:  presupuesto ext:xlsx fecha:mes -antiguo\n\n"
    "Atajos: ↓ baja a los resultados · Enter abre · Ctrl+Enter abre la ubicación · "
    "Ctrl+D fija · Ctrl+P vista previa · Ctrl+G cambia lista/cuadrícula · "
    "Ctrl+Shift+C copia la ruta · Ctrl+E exporta a CSV · Ctrl+R reindexa."
)


# ═══════════════════════════════════════════════════════════
# 🛠️ UTILIDADES
# ═══════════════════════════════════════════════════════════
def _formatear_fecha(timestamp):
    try:
        return datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return "—"


def _recortar_medio(texto, maximo):
    texto = texto or ""
    if len(texto) <= maximo:
        return texto
    mitad = (maximo - 1) // 2
    return texto[:mitad] + "…" + texto[-(maximo - mitad - 1):]


def _resaltar_texto(nombre, terminos):
    """HTML seguro con las coincidencias resaltadas en terracota."""
    terminos = sorted({t for t in (terminos or []) if len(t) >= 2}, key=len, reverse=True)
    if not terminos:
        return html.escape(nombre)
    try:
        patron = re.compile("|".join(re.escape(t) for t in terminos), re.IGNORECASE)
    except re.error:
        return html.escape(nombre)
    partes, ultimo = [], 0
    for m in patron.finditer(nombre):
        partes.append(html.escape(nombre[ultimo:m.start()]))
        partes.append(f'<span style="color:{ACENTO_HOVER};font-weight:700;">{html.escape(m.group(0))}</span>')
        ultimo = m.end()
    partes.append(html.escape(nombre[ultimo:]))
    return "".join(partes)


def _cargar_miniatura(ruta, ancho, alto):
    """Miniatura recortada al centro, decodificando la imagen ya reducida
    (mucho más ligero que cargar la imagen entera)."""
    try:
        lector = QImageReader(ruta)
        lector.setAutoTransform(True)
        tam = lector.size()
        if not tam.isValid() or tam.isEmpty():
            return None
        lector.setScaledSize(tam.scaled(ancho, alto, Qt.KeepAspectRatioByExpanding))
        img = lector.read()
        if img.isNull():
            return None
        pix = QPixmap.fromImage(img)
        x = max(0, (pix.width() - ancho) // 2)
        y = max(0, (pix.height() - alto) // 2)
        return pix.copy(x, y, ancho, alto)
    except Exception:
        return None


def _crear_placeholder(html_texto):
    lbl = QLabel(html_texto)
    lbl.setTextFormat(Qt.RichText)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(f"""
        color: {TEXTO_TERCIARIO}; font-family: {FUENTE_UI}; font-size: 12px;
        padding: 36px 20px; border: none; background: transparent;
    """)
    return lbl


def _estilo_boton_secundario():
    return f"""
        QPushButton {{
            background-color: {BG_INPUT}; color: {TEXTO_SECUNDARIO};
            border: 1px solid {BORDE}; border-radius: 6px;
            padding: 0 12px; font-family: {FUENTE_UI}; font-size: 11px; font-weight: 600;
        }}
        QPushButton:hover {{ border-color: {ACENTO}; color: {ACENTO}; }}
        QPushButton:checked {{ background-color: {ACENTO_SUAVE}; border-color: {ACENTO}; color: {ACENTO}; }}
        QPushButton:disabled {{ color: {TEXTO_TERCIARIO}; border-color: {BORDE_SUAVE}; }}
        QPushButton::menu-indicator {{ image: none; width: 0px; }}
    """


def _estilo_boton_primario():
    return f"""
        QPushButton {{
            background-color: {ACENTO}; color: {BG_APP}; border: none;
            border-radius: 6px; padding: 0 16px;
            font-family: {FUENTE_UI}; font-size: 12px; font-weight: 700;
        }}
        QPushButton:hover {{ background-color: {ACENTO_HOVER}; }}
        QPushButton:disabled {{ background-color: {BORDE}; color: {TEXTO_TERCIARIO}; }}
    """


def _estilo_menu():
    return f"""
        QMenu {{
            background-color: {BG_PANEL}; border: 1px solid {BORDE};
            color: {TEXTO_PRINCIPAL}; padding: 6px; border-radius: 8px;
        }}
        QMenu::item {{
            padding: 7px 24px 7px 14px; border-radius: 6px;
            font-family: {FUENTE_UI}; font-size: 12px;
        }}
        QMenu::item:selected {{ background-color: {ACENTO_SUAVE}; color: {ACENTO_HOVER}; }}
        QMenu::separator {{ height: 1px; background: {BORDE_SUAVE}; margin: 4px 8px; }}
    """


# ═══════════════════════════════════════════════════════════
# 🧵 HILOS DE TRABAJO
# ═══════════════════════════════════════════════════════════
class HiloEscaneo(QThread):
    progreso = pyqtSignal(str, int)
    terminado = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.cancelado = False

    def run(self):
        try:
            total = logica.escanear_sistema(
                callback_progreso=lambda c, n: self.progreso.emit(c, n),
                cancelar_flag=self,
            )
            self.terminado.emit(total)
        except Exception as e:
            self.error.emit(str(e))


class HiloCarpeta(QThread):
    terminado = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, carpeta):
        super().__init__()
        self.carpeta = carpeta
        self.cancelado = False

    def run(self):
        try:
            self.terminado.emit(logica.reindexar_carpeta(self.carpeta, cancelar_flag=self))
        except Exception as e:
            self.error.emit(str(e))


class HiloBusqueda(QThread):
    resultados_listos = pyqtSignal(list, int, bool)
    error = pyqtSignal(str)

    def __init__(self, texto, categoria, orden, incluir_contenido,
                 offset, limite, generacion, reemplazar):
        super().__init__()
        self.texto = texto
        self.categoria = categoria
        self.orden = orden
        self.incluir_contenido = incluir_contenido
        self.offset = offset
        self.limite = limite
        self.generacion = generacion
        self.reemplazar = reemplazar

    def run(self):
        try:
            resultados = logica.buscar(
                self.texto, categoria=self.categoria,
                limite=self.limite, offset=self.offset, orden=self.orden
            )
            if self.incluir_contenido:
                rutas_existentes = {r["ruta"] for r in resultados}
                for extra in logica.buscar_contenido(self.texto):
                    if extra["ruta"] not in rutas_existentes:
                        resultados.append(extra)
                        rutas_existentes.add(extra["ruta"])
            self.resultados_listos.emit(resultados, self.generacion, self.reemplazar)
        except Exception as e:
            self.error.emit(str(e))


class HiloDuplicados(QThread):
    listo = pyqtSignal(list, object)
    error = pyqtSignal(str)

    def run(self):
        try:
            grupos, recuperable = logica.buscar_duplicados()
            self.listo.emit(grupos, recuperable)
        except Exception as e:
            self.error.emit(str(e))


class HiloLimpieza(QThread):
    terminado = pyqtSignal(int)
    error = pyqtSignal(str)

    def run(self):
        try:
            self.terminado.emit(logica.verificar_y_limpiar_indice())
        except Exception as e:
            self.error.emit(str(e))


# ═══════════════════════════════════════════════════════════
# 📇 FILA DE RESULTADO
# ═══════════════════════════════════════════════════════════
class FilaResultado(QWidget):
    def __init__(self, resultado, terminos=None):
        super().__init__()
        self.resultado = resultado
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        fijado = resultado.get("fijado", False)

        cont_icono = QFrame()
        cont_icono.setFixedSize(36, 36)
        cont_icono.setStyleSheet(f"""
            QFrame {{
                background-color: {DORADO_SUAVE if fijado else ACENTO_SUAVE};
                border-radius: 8px; border: none;
            }}
        """)
        lbl_icono = QLabel(ICONOS_CATEGORIA.get(resultado["categoria"], "📎"), cont_icono)
        lbl_icono.setGeometry(0, 0, 36, 36)
        lbl_icono.setAlignment(Qt.AlignCenter)
        lbl_icono.setStyleSheet("font-size: 17px; background: transparent; border: none;")

        col_texto = QVBoxLayout()
        col_texto.setSpacing(2)

        marca = f'<span style="color:{DORADO};">★ </span>' if fijado else ""
        lbl_nombre = QLabel()
        lbl_nombre.setTextFormat(Qt.RichText)
        lbl_nombre.setText(marca + _resaltar_texto(_recortar_medio(resultado["nombre"], 64), terminos))
        lbl_nombre.setStyleSheet(f"""
            color: {TEXTO_PRINCIPAL}; font-family: {FUENTE_SERIF};
            font-size: 13px; font-weight: 600; background: transparent; border: none;
        """)

        lbl_ruta = QLabel(_recortar_medio(resultado["carpeta"], 72))
        lbl_ruta.setStyleSheet(f"""
            color: {TEXTO_TERCIARIO}; font-family: {FUENTE_META};
            font-size: 10px; background: transparent; border: none;
        """)

        col_texto.addWidget(lbl_nombre)
        col_texto.addWidget(lbl_ruta)

        fragmento = resultado.get("fragmento")
        if fragmento:
            lbl_frag = QLabel(f"“{html.escape(_recortar_medio(fragmento, 110))}”")
            lbl_frag.setTextFormat(Qt.RichText)
            lbl_frag.setStyleSheet(f"""
                color: {TEXTO_SECUNDARIO}; font-family: {FUENTE_SERIF}; font-style: italic;
                font-size: 11px; background: transparent; border: none;
            """)
            col_texto.addWidget(lbl_frag)

        lbl_meta = QLabel(
            f"{logica.formatear_tamano(resultado['tamano'])}<br>"
            f"<span style='color:{TEXTO_TERCIARIO};'>{_formatear_fecha(resultado['modificado'])}</span>"
        )
        lbl_meta.setTextFormat(Qt.RichText)
        lbl_meta.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_meta.setStyleSheet(f"""
            color: {TEXTO_SECUNDARIO}; font-family: {FUENTE_META};
            font-size: 10px; background: transparent; border: none;
        """)

        layout.addWidget(cont_icono)
        layout.addLayout(col_texto, 1)
        layout.addWidget(lbl_meta)

        self.setToolTip(
            f"{resultado['nombre']}\n{resultado['carpeta']}\n"
            f"{logica.formatear_tamano(resultado['tamano'])}  ·  {_formatear_fecha(resultado['modificado'])}\n"
            f"{resultado['categoria']}"
        )


# ═══════════════════════════════════════════════════════════
# 🖼️ TARJETA DE LA VISTA CUADRÍCULA
# ═══════════════════════════════════════════════════════════
class TarjetaGrid(QWidget):
    clic = pyqtSignal(dict)
    doble = pyqtSignal(dict)

    def __init__(self, resultado, terminos=None):
        super().__init__()
        self.resultado = resultado
        self.setFixedSize(150, 160)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            TarjetaGrid {{
                background-color: {BG_PANEL}; border: 1px solid {BORDE_SUAVE}; border-radius: 10px;
            }}
            TarjetaGrid:hover {{
                background-color: {BG_INPUT_HOVER}; border: 1px solid {ACENTO};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        fijado = resultado.get("fijado", False)
        preview = QLabel(ICONOS_CATEGORIA.get(resultado["categoria"], "📎"))
        preview.setAlignment(Qt.AlignCenter)
        preview.setFixedSize(132, 80)
        preview.setStyleSheet(f"""
            background-color: {DORADO_SUAVE if fijado else ACENTO_SUAVE};
            border-radius: 6px; font-size: 30px; border: none;
        """)
        if resultado["categoria"] == "Imágenes":
            pix = _cargar_miniatura(resultado["ruta"], 132, 80)
            if pix:
                preview.setPixmap(pix)

        marca = f'<span style="color:{DORADO};">★ </span>' if fijado else ""
        lbl_nombre = QLabel()
        lbl_nombre.setTextFormat(Qt.RichText)
        lbl_nombre.setText(marca + _resaltar_texto(_recortar_medio(resultado["nombre"], 40), terminos))
        lbl_nombre.setAlignment(Qt.AlignCenter)
        lbl_nombre.setWordWrap(True)
        lbl_nombre.setMaximumHeight(40)
        lbl_nombre.setStyleSheet(f"""
            color: {TEXTO_PRINCIPAL}; font-family: {FUENTE_SERIF};
            font-size: 11px; font-weight: 600; background: transparent; border: none;
        """)

        lbl_meta = QLabel(logica.formatear_tamano(resultado["tamano"]))
        lbl_meta.setAlignment(Qt.AlignCenter)
        lbl_meta.setStyleSheet(f"""
            color: {TEXTO_TERCIARIO}; font-family: {FUENTE_META};
            font-size: 9px; background: transparent; border: none;
        """)

        layout.addWidget(preview)
        layout.addWidget(lbl_nombre)
        layout.addWidget(lbl_meta)
        self.setToolTip(f"{resultado['nombre']}\n{resultado['carpeta']}")

    def mousePressEvent(self, event):
        if event.button() in (Qt.LeftButton, Qt.RightButton):
            self.clic.emit(self.resultado)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.doble.emit(self.resultado)


# ═══════════════════════════════════════════════════════════
# 🪟 VENTANA PRINCIPAL
# ═══════════════════════════════════════════════════════════
class VentanaBuscador(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hilo_escaneo = None
        self.hilo_busqueda = None
        self.hilo_limpieza = None
        self.hilo_duplicados = None
        self.hilo_carpeta = None
        self._hilos_vivos = set()

        self.categoria_activa = "Todo"
        self.orden_activo = "relevancia"
        self.resultados_actuales = []
        self._generacion_busqueda = 0
        self._offset_actual = 0
        self._tiempo_inicio_busqueda = 0.0
        self._modo_vista = "lista"        # "lista" | "grid"
        self._modo = "inicio"             # "inicio" | "busqueda" | "duplicados"
        self._grid_sucio = True
        self._mensaje_vacio = ""
        self._resultado_sel = None
        self._tiene_historial = False

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.NonModal)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(1000, 650)
        self.setMinimumSize(720, 480)
        self.drag_position = QPoint()

        self.setStyleSheet(f"""
            QToolTip {{
                background-color: {BG_PANEL}; color: {TEXTO_PRINCIPAL};
                border: 1px solid {BORDE}; padding: 4px 6px;
                font-family: {FUENTE_UI}; font-size: 11px;
            }}
            QMessageBox {{ background-color: {BG_PANEL}; }}
            QMessageBox QLabel {{ color: {TEXTO_PRINCIPAL}; font-family: {FUENTE_UI}; font-size: 12px; }}
            QMessageBox QPushButton {{
                background-color: {BG_INPUT}; color: {TEXTO_PRINCIPAL};
                border: 1px solid {BORDE}; border-radius: 6px; padding: 6px 14px;
                font-family: {FUENTE_UI}; font-size: 12px;
            }}
            QMessageBox QPushButton:hover {{ border-color: {ACENTO}; color: {ACENTO}; }}
        """)

        self.timer_busqueda = QTimer(self)
        self.timer_busqueda.setSingleShot(True)
        self.timer_busqueda.timeout.connect(self._ejecutar_busqueda)

        self._construir_ui()
        self._configurar_atajos()
        self._actualizar_estado_indice()
        self._refrescar_historial()
        self._limpiar_vista_previa()
        try:
            self._mostrar_inicio()
        except Exception:
            pass
        self.txt_buscar.setFocus()

    # ─────────────────────────────────────────────
    # HILOS
    # ─────────────────────────────────────────────
    def _retener(self, hilo):
        """Evita que Python destruya un QThread que sigue ejecutándose."""
        self._hilos_vivos.add(hilo)
        hilo.finished.connect(lambda h=hilo: self._hilos_vivos.discard(h))

    # ─────────────────────────────────────────────
    # ARRASTRE
    # ─────────────────────────────────────────────
    def _header_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def _header_mouse_move(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    # ─────────────────────────────────────────────
    # ATAJOS
    # ─────────────────────────────────────────────
    def _configurar_atajos(self):
        QShortcut(QKeySequence("Escape"), self, activated=self._on_escape)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.iniciar_reindexado)
        QShortcut(QKeySequence("Ctrl+L"), self, activated=self._enfocar_busqueda)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self._enfocar_busqueda)
        QShortcut(QKeySequence("Ctrl+G"), self, activated=self._toggle_vista)
        QShortcut(QKeySequence("Ctrl+P"), self, activated=lambda: self.btn_preview.click())
        QShortcut(QKeySequence("Ctrl+D"), self, activated=self._fijar_seleccionado)
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self._exportar_csv)
        QShortcut(QKeySequence("Ctrl+Shift+D"), self, activated=lambda: self.btn_duplicados.click())
        QShortcut(QKeySequence("Ctrl+Shift+C"), self, activated=self._copiar_ruta_seleccionado)
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self._abrir_ubicacion_seleccionado)
        for tecla in (Qt.Key_Return, Qt.Key_Enter):
            sc = QShortcut(QKeySequence(tecla), self.lista_resultados)
            sc.setContext(Qt.WidgetShortcut)
            sc.activated.connect(self._abrir_seleccionado)

        self.txt_buscar.installEventFilter(self)

    def eventFilter(self, obj, ev):
        if obj is self.txt_buscar and ev.type() == QEvent.KeyPress and ev.key() == Qt.Key_Down:
            self._enfocar_lista()
            return True
        return super().eventFilter(obj, ev)

    def _on_escape(self):
        if self.txt_buscar.text():
            self.txt_buscar.clear()
        else:
            self.close()

    def _enfocar_busqueda(self):
        self.txt_buscar.setFocus()
        self.txt_buscar.selectAll()

    def _enfocar_lista(self):
        if self._modo_vista != "lista":
            return
        for i in range(self.lista_resultados.count()):
            item = self.lista_resultados.item(i)
            if item.flags() & Qt.ItemIsSelectable:
                self.lista_resultados.setCurrentItem(item)
                self.lista_resultados.setFocus()
                return

    def _toggle_vista(self):
        self._modo_vista = "grid" if self._modo_vista == "lista" else "lista"
        self.btn_toggle_vista.setText("▦" if self._modo_vista == "grid" else "☰")
        self.btn_toggle_vista.setToolTip(f"Vista: {self._modo_vista} (Ctrl+G)")
        self._redibujar_resultados()

    def _toggle_preview(self, visible):
        self.panel_preview.setVisible(visible)
        if visible and self._resultado_sel:
            self._mostrar_vista_previa(self._resultado_sel)
        if self._modo_vista == "grid":
            self._grid_sucio = True
            self._redibujar_resultados()

    # ─────────────────────────────────────────────
    # CONSTRUCCIÓN DE UI
    # ─────────────────────────────────────────────
    def _construir_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        contenedor = QFrame()
        contenedor.setObjectName("contenedorBuscador")
        contenedor.setStyleSheet(f"""
            QFrame#contenedorBuscador {{
                background-color: {BG_APP}; border: 1px solid {BORDE}; border-radius: 10px;
            }}
        """)
        root.addWidget(contenedor)

        layout_main = QVBoxLayout(contenedor)
        layout_main.setContentsMargins(0, 0, 0, 0)
        layout_main.setSpacing(0)

        # ── CABECERA ──────────────────────────────────
        header = QFrame()
        header.setFixedHeight(46)
        header.setStyleSheet(f"""
            background-color: {BG_PANEL};
            border-top-left-radius: 10px; border-top-right-radius: 10px;
            border-bottom: 1px solid {BORDE_SUAVE};
        """)
        header.mousePressEvent = self._header_mouse_press
        header.mouseMoveEvent = self._header_mouse_move

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 10, 0)

        lbl_titulo = QLabel("Buscador")
        lbl_titulo.setStyleSheet(f"""
            color: {TEXTO_PRINCIPAL}; font-family: {FUENTE_SERIF}; font-size: 15px;
            font-weight: 700; letter-spacing: 0.5px; border: none; background: transparent;
        """)
        self.lbl_estado_indice = QLabel("")
        self.lbl_estado_indice.setStyleSheet(f"""
            color: {TEXTO_TERCIARIO}; font-family: {FUENTE_META}; font-size: 10px;
            border: none; background: transparent; padding-left: 8px;
        """)

        btn_ayuda = QPushButton("?")
        btn_ayuda.setFixedSize(28, 28)
        btn_ayuda.setCursor(Qt.PointingHandCursor)
        btn_ayuda.setToolTip("Sintaxis de búsqueda y atajos")
        btn_ayuda.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {TEXTO_SECUNDARIO}; border: none;
                           font-family: {FUENTE_SERIF}; font-size: 14px; font-weight: 700; border-radius: 5px; }}
            QPushButton:hover {{ background: {ACENTO_SUAVE}; color: {ACENTO}; }}
        """)
        btn_ayuda.clicked.connect(self._mostrar_ayuda)

        btn_cerrar = QPushButton("✕")
        btn_cerrar.setFixedSize(28, 28)
        btn_cerrar.setCursor(Qt.PointingHandCursor)
        btn_cerrar.setToolTip("Cerrar (Esc)")
        btn_cerrar.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {TEXTO_SECUNDARIO}; border: none;
                           font-size: 13px; border-radius: 5px; }}
            QPushButton:hover {{ background: {PELIGRO}; color: {TEXTO_PRINCIPAL}; }}
        """)
        btn_cerrar.clicked.connect(self.close)

        header_layout.addWidget(lbl_titulo)
        header_layout.addWidget(self.lbl_estado_indice)
        header_layout.addStretch()
        header_layout.addWidget(btn_ayuda)
        header_layout.addWidget(btn_cerrar)
        layout_main.addWidget(header)

        # ── BARRA DE PROGRESO ─────────────────────────
        self.barra_progreso = QFrame()
        self.barra_progreso.setFixedHeight(3)
        self.barra_progreso.setStyleSheet(f"background: {BG_PANEL};")
        self.barra_progreso.hide()
        self.barra_interior = QFrame(self.barra_progreso)
        self.barra_interior.setFixedHeight(3)
        self.barra_interior.setStyleSheet(f"background: {ACENTO}; border-radius: 1px;")
        self.barra_interior.setFixedWidth(0)
        layout_main.addWidget(self.barra_progreso)

        # ── CUERPO: columna principal + panel de vista previa ──
        cuerpo = QHBoxLayout()
        cuerpo.setContentsMargins(0, 0, 0, 0)
        cuerpo.setSpacing(0)

        columna = QVBoxLayout()
        columna.setContentsMargins(18, 14, 18, 8)
        columna.setSpacing(10)
        self._construir_columna_principal(columna)
        cuerpo.addLayout(columna, 1)

        self.panel_preview = self._construir_panel_preview()
        cuerpo.addWidget(self.panel_preview, 0)

        layout_main.addLayout(cuerpo, 1)
        layout_main.addWidget(self._construir_pie())

    def _construir_columna_principal(self, columna):
        # ── Fila de búsqueda ──
        fila_busqueda = QHBoxLayout()
        fila_busqueda.setSpacing(8)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍  Buscar archivos…   (ej: informe ext:pdf fecha:mes)")
        self.txt_buscar.setFixedHeight(38)
        self.txt_buscar.setClearButtonEnabled(True)
        self.txt_buscar.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BG_INPUT}; color: {TEXTO_PRINCIPAL};
                border: 1px solid {BORDE}; border-radius: 7px; padding: 0 12px;
                font-family: {FUENTE_UI}; font-size: 13px;
                selection-background-color: {ACENTO_MEDIO};
            }}
            QLineEdit:focus {{ border: 1px solid {ACENTO}; }}
        """)
        self.txt_buscar.textChanged.connect(self._on_texto_cambiado)
        self.txt_buscar.returnPressed.connect(self._on_enter_pressed)

        self.btn_filtros = QPushButton("⚙  Filtros")
        self.btn_filtros.setFixedHeight(38)
        self.btn_filtros.setCursor(Qt.PointingHandCursor)
        self.btn_filtros.setStyleSheet(_estilo_boton_secundario())
        self.btn_filtros.setMenu(self._construir_menu_filtros())

        self.combo_orden = QComboBox()
        for etiqueta, clave in OPCIONES_ORDEN:
            self.combo_orden.addItem(etiqueta, clave)
        self.combo_orden.setFixedHeight(38)
        self.combo_orden.setToolTip("Ordenar resultados")
        self.combo_orden.setStyleSheet(f"""
            QComboBox {{
                background-color: {BG_INPUT}; color: {TEXTO_PRINCIPAL};
                border: 1px solid {BORDE}; border-radius: 7px; padding: 0 12px;
                font-family: {FUENTE_UI}; font-size: 12px; min-width: 130px;
            }}
            QComboBox:hover {{ border-color: {ACENTO}; }}
            QComboBox::drop-down {{ border: none; width: 22px; }}
            QComboBox QAbstractItemView {{
                background-color: {BG_PANEL}; color: {TEXTO_PRINCIPAL};
                selection-background-color: {ACENTO_SUAVE}; selection-color: {ACENTO_HOVER};
                border: 1px solid {BORDE}; outline: none;
            }}
        """)
        self.combo_orden.currentIndexChanged.connect(self._cambiar_orden)

        estilo_icono = _estilo_boton_secundario().replace("padding: 0 12px;", "padding: 0; font-size: 15px;")

        self.btn_toggle_vista = QPushButton("☰")
        self.btn_toggle_vista.setFixedSize(38, 38)
        self.btn_toggle_vista.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_vista.setToolTip("Vista: lista (Ctrl+G)")
        self.btn_toggle_vista.setStyleSheet(estilo_icono)
        self.btn_toggle_vista.clicked.connect(self._toggle_vista)

        self.btn_preview = QPushButton("◧")
        self.btn_preview.setFixedSize(38, 38)
        self.btn_preview.setCheckable(True)
        self.btn_preview.setChecked(True)
        self.btn_preview.setCursor(Qt.PointingHandCursor)
        self.btn_preview.setToolTip("Panel de vista previa (Ctrl+P)")
        self.btn_preview.setStyleSheet(estilo_icono)
        self.btn_preview.toggled.connect(self._toggle_preview)

        fila_busqueda.addWidget(self.txt_buscar, 1)
        fila_busqueda.addWidget(self.btn_filtros)
        fila_busqueda.addWidget(self.combo_orden)
        fila_busqueda.addWidget(self.btn_toggle_vista)
        fila_busqueda.addWidget(self.btn_preview)
        columna.addLayout(fila_busqueda)

        # ── Chips de categoría (compactos: sólo el activo muestra su nombre) ──
        fila_chips = QHBoxLayout()
        fila_chips.setSpacing(6)
        self.botones_categoria = {}
        for categoria, _icono in CATEGORIAS_FILTRO:
            btn = QPushButton()
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _c, cat=categoria: self._filtrar_por_categoria(cat))
            self.botones_categoria[categoria] = btn
            fila_chips.addWidget(btn)
        fila_chips.addStretch()

        self.chk_contenido = QCheckBox("Buscar también dentro de archivos de texto")
        self.chk_contenido.setCursor(Qt.PointingHandCursor)
        self.chk_contenido.setStyleSheet(f"""
            QCheckBox {{
                color: {TEXTO_SECUNDARIO}; font-family: {FUENTE_UI}; font-size: 11px;
                background: transparent; border: none; spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 14px; height: 14px; border-radius: 4px;
                border: 1px solid {BORDE}; background: {BG_INPUT};
            }}
            QCheckBox::indicator:checked {{ background: {ACENTO}; border-color: {ACENTO}; }}
            QCheckBox:hover {{ color: {ACENTO}; }}
        """)
        self.chk_contenido.toggled.connect(self._ejecutar_busqueda)
        fila_chips.addWidget(self.chk_contenido)
        columna.addLayout(fila_chips)
        self._refrescar_estilos_chips()

        # ── Historial de búsquedas ──
        self.frame_historial = QFrame()
        self.frame_historial.setStyleSheet("background: transparent; border: none;")
        self.historial_layout = QHBoxLayout(self.frame_historial)
        self.historial_layout.setContentsMargins(0, 0, 0, 0)
        self.historial_layout.setSpacing(6)
        columna.addWidget(self.frame_historial)

        # ── Resultados (lista o cuadrícula) con el "margen de cuaderno" de Notas ──
        fila_resultados = QHBoxLayout()
        fila_resultados.setContentsMargins(0, 0, 0, 0)
        fila_resultados.setSpacing(0)

        margen = QFrame()
        margen.setFixedWidth(3)
        margen.setStyleSheet(f"background-color: {ACENTO}; border: none; border-radius: 1px;")
        fila_resultados.addWidget(margen)

        self.stack_vista = QFrame()
        self.stack_vista.setStyleSheet("background: transparent; border: none;")
        self.stack_layout = QVBoxLayout(self.stack_vista)
        self.stack_layout.setContentsMargins(8, 0, 0, 0)

        estilo_scroll = f"""
            QScrollBar:vertical {{ background: transparent; width: 7px; margin: 2px; }}
            QScrollBar::handle:vertical {{ background: {BORDE}; border-radius: 3px; min-height: 24px; }}
            QScrollBar::handle:vertical:hover {{ background: {TEXTO_TERCIARIO}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """

        self.lista_resultados = QListWidget()
        self.lista_resultados.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.lista_resultados.setStyleSheet(f"""
            QListWidget {{ background-color: transparent; border: none; outline: none; }}
            QListWidget::item {{ border-radius: 8px; margin-bottom: 3px; }}
            QListWidget::item:hover {{ background-color: {BG_INPUT_HOVER}; }}
            QListWidget::item:selected {{
                background-color: {ACENTO_SUAVE}; border: 1px solid {ACENTO};
            }}
            {estilo_scroll}
        """)
        self.lista_resultados.setSpacing(0)
        self.lista_resultados.itemDoubleClicked.connect(self._abrir_item)
        self.lista_resultados.currentItemChanged.connect(self._on_item_actual)
        self.lista_resultados.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lista_resultados.customContextMenuRequested.connect(self._menu_contextual)

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.scroll_grid = QScrollArea()
        self.scroll_grid.setWidgetResizable(True)
        self.scroll_grid.setWidget(self.grid_container)
        self.scroll_grid.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_grid.setContextMenuPolicy(Qt.CustomContextMenu)
        self.scroll_grid.customContextMenuRequested.connect(self._menu_contextual_grid)
        self.scroll_grid.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }} {estilo_scroll}")

        self.stack_layout.addWidget(self.lista_resultados)
        self.stack_layout.addWidget(self.scroll_grid)
        self.scroll_grid.hide()

        fila_resultados.addWidget(self.stack_vista, 1)
        columna.addLayout(fila_resultados, 1)

        self.btn_cargar_mas = QPushButton("↓  Cargar más resultados")
        self.btn_cargar_mas.setCursor(Qt.PointingHandCursor)
        self.btn_cargar_mas.setFixedHeight(32)
        self.btn_cargar_mas.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_INPUT}; color: {ACENTO};
                border: 1px dashed {BORDE}; border-radius: 7px;
                font-family: {FUENTE_UI}; font-size: 11px; font-weight: 600;
            }}
            QPushButton:hover {{ border-color: {ACENTO}; background-color: {BG_INPUT_HOVER}; }}
        """)
        self.btn_cargar_mas.clicked.connect(self._cargar_mas_resultados)
        self.btn_cargar_mas.hide()
        columna.addWidget(self.btn_cargar_mas)

    def _construir_pie(self):
        pie = QFrame()
        pie.setFixedHeight(44)
        pie.setStyleSheet(f"""
            background-color: {BG_PANEL};
            border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;
            border-top: 1px solid {BORDE_SUAVE};
        """)
        fila = QHBoxLayout(pie)
        fila.setContentsMargins(18, 0, 6, 0)
        fila.setSpacing(8)

        self.lbl_contador = QLabel("")
        self.lbl_contador.setStyleSheet(f"""
            color: {TEXTO_TERCIARIO}; font-family: {FUENTE_META}; font-size: 10px;
            border: none; background: transparent;
        """)
        fila.addWidget(self.lbl_contador, 1)

        def _boton(texto, tip, slot, checkable=False):
            b = QPushButton(texto)
            b.setFixedHeight(28)
            b.setToolTip(tip)
            b.setCursor(Qt.PointingHandCursor)
            b.setCheckable(checkable)
            b.setStyleSheet(_estilo_boton_secundario())
            b.clicked.connect(slot)
            return b

        self.btn_duplicados = _boton("Duplicados", "Buscar archivos duplicados (Ctrl+Shift+D)",
                                     self._alternar_duplicados, checkable=True)
        self.btn_exportar = _boton("Exportar CSV", "Guardar los resultados en un CSV (Ctrl+E)", self._exportar_csv)
        self.btn_indexar_carpeta = _boton("＋ Carpeta", "Añadir o actualizar una carpeta en el índice",
                                          self._indexar_carpeta_nueva)
        self.btn_limpiar_indice = _boton("Limpiar", "Quitar del índice las rutas que ya no existen",
                                         self.iniciar_limpieza_indice)

        self.btn_reindexar = QPushButton("⟳  Reindexar")
        self.btn_reindexar.setFixedHeight(28)
        self.btn_reindexar.setCursor(Qt.PointingHandCursor)
        self.btn_reindexar.setToolTip("Escaneo completo del sistema (Ctrl+R)")
        self.btn_reindexar.setStyleSheet(_estilo_boton_primario())
        self.btn_reindexar.clicked.connect(self.iniciar_reindexado)

        for w in (self.btn_duplicados, self.btn_exportar, self.btn_indexar_carpeta,
                  self.btn_limpiar_indice, self.btn_reindexar):
            fila.addWidget(w)

        grip = QSizeGrip(self)
        grip.setStyleSheet("background: transparent;")
        grip.setFixedSize(16, 16)
        fila.addWidget(grip, 0, Qt.AlignBottom | Qt.AlignRight)
        return pie

    def _construir_panel_preview(self):
        panel = QFrame()
        panel.setObjectName("panelPreview")
        panel.setFixedWidth(272)
        panel.setStyleSheet(f"""
            QFrame#panelPreview {{
                background-color: {BG_PANEL}; border: none; border-left: 1px solid {BORDE_SUAVE};
            }}
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 12)
        layout.setSpacing(10)

        self.lbl_prev_img = QLabel()
        self.lbl_prev_img.setFixedHeight(150)
        self.lbl_prev_img.setAlignment(Qt.AlignCenter)
        self.lbl_prev_img.setStyleSheet(f"""
            background-color: {BG_INPUT}; border: 1px solid {BORDE_SUAVE};
            border-radius: 8px; font-size: 46px;
        """)
        layout.addWidget(self.lbl_prev_img)

        self.lbl_prev_nombre = QLabel("")
        self.lbl_prev_nombre.setWordWrap(True)
        self.lbl_prev_nombre.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_prev_nombre.setStyleSheet(f"""
            color: {TEXTO_PRINCIPAL}; font-family: {FUENTE_SERIF}; font-size: 14px;
            font-weight: 700; background: transparent; border: none;
        """)
        layout.addWidget(self.lbl_prev_nombre)

        self.lbl_prev_meta = QLabel("")
        self.lbl_prev_meta.setTextFormat(Qt.RichText)
        self.lbl_prev_meta.setWordWrap(True)
        self.lbl_prev_meta.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_prev_meta.setStyleSheet(f"""
            color: {TEXTO_SECUNDARIO}; font-family: {FUENTE_META}; font-size: 10px;
            background: transparent; border: none;
        """)
        layout.addWidget(self.lbl_prev_meta)

        layout.addStretch(1)

        self.txt_prev_texto = QTextEdit()
        self.txt_prev_texto.setReadOnly(True)
        self.txt_prev_texto.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_INPUT}; color: {TEXTO_SECUNDARIO};
                border: 1px solid {BORDE_SUAVE}; border-radius: 8px; padding: 8px 10px;
                font-family: {FUENTE_META}; font-size: 10px;
            }}
        """)
        self.txt_prev_texto.hide()
        layout.addWidget(self.txt_prev_texto, 4)

        fila_botones = QHBoxLayout()
        fila_botones.setSpacing(6)
        self.btn_prev_abrir = QPushButton("Abrir")
        self.btn_prev_abrir.setFixedHeight(30)
        self.btn_prev_abrir.setCursor(Qt.PointingHandCursor)
        self.btn_prev_abrir.setStyleSheet(_estilo_boton_primario())
        self.btn_prev_abrir.clicked.connect(self._abrir_seleccionado)

        self.btn_prev_ubic = QPushButton("Ubicación")
        self.btn_prev_ubic.setFixedHeight(30)
        self.btn_prev_ubic.setCursor(Qt.PointingHandCursor)
        self.btn_prev_ubic.setStyleSheet(_estilo_boton_secundario())
        self.btn_prev_ubic.clicked.connect(self._abrir_ubicacion_seleccionado)

        self.btn_prev_fijar = QPushButton("☆")
        self.btn_prev_fijar.setFixedSize(30, 30)
        self.btn_prev_fijar.setCursor(Qt.PointingHandCursor)
        self.btn_prev_fijar.setToolTip("Fijar arriba (Ctrl+D)")
        self.btn_prev_fijar.setStyleSheet(_estilo_boton_secundario().replace("padding: 0 12px;", "padding: 0;"))
        self.btn_prev_fijar.clicked.connect(self._fijar_seleccionado)

        fila_botones.addWidget(self.btn_prev_abrir, 1)
        fila_botones.addWidget(self.btn_prev_ubic, 1)
        fila_botones.addWidget(self.btn_prev_fijar)
        layout.addLayout(fila_botones)
        return panel

    def _construir_menu_filtros(self):
        menu = QMenu(self)
        menu.setStyleSheet(_estilo_menu())
        grupos = [
            ("📅  Modificado", "fecha", [("Hoy", "hoy"), ("Últimos 7 días", "semana"),
                                         ("Último mes", "mes"), ("Último año", "año")]),
            ("📏  Tamaño", "size", [("Mayor de 10 MB", ">10mb"), ("Mayor de 100 MB", ">100mb"),
                                    ("Mayor de 1 GB", ">1gb"), ("Menor de 1 MB", "<1mb")]),
            ("🏷  Tipo", "ext", [("PDF", "pdf"), ("Word", "doc,docx"), ("Excel", "xls,xlsx"),
                                  ("Imágenes", "jpg,jpeg,png,webp"), ("Python", "py")]),
        ]
        for titulo, clave, opciones in grupos:
            sub = menu.addMenu(titulo)
            for etiqueta, valor in opciones:
                accion = sub.addAction(etiqueta)
                accion.triggered.connect(lambda _c=False, k=clave, v=valor: self._aplicar_modificador(k, v))
        menu.addSeparator()
        menu.addAction("Quitar todos los filtros").triggered.connect(self._quitar_modificadores)
        menu.addAction("Ayuda de sintaxis…").triggered.connect(self._mostrar_ayuda)
        return menu

    # ─────────────────────────────────────────────
    # MODIFICADORES / AYUDA
    # ─────────────────────────────────────────────
    def _aplicar_modificador(self, clave, valor):
        patron = rf'(?<!\S)(?:{_ALIAS_MODIFICADOR[clave]}):\S+'
        texto = re.sub(patron, " ", self.txt_buscar.text(), flags=re.IGNORECASE)
        texto = " ".join(texto.split())
        self.txt_buscar.setText(f"{texto} {clave}:{valor}".strip())
        self.txt_buscar.setFocus()

    def _quitar_modificadores(self):
        texto, _ = logica.parsear_consulta(self.txt_buscar.text())
        self.txt_buscar.setText(texto)

    def _mostrar_ayuda(self):
        QMessageBox.information(self, "Sintaxis de búsqueda", AYUDA_SINTAXIS)

    # ─────────────────────────────────────────────
    # CHIPS E HISTORIAL
    # ─────────────────────────────────────────────
    def _refrescar_estilos_chips(self):
        for categoria, btn in self.botones_categoria.items():
            activo = (categoria == self.categoria_activa)
            icono = ICONOS_CATEGORIA[categoria]
            btn.setText(f"{icono}  {categoria}" if activo else icono)
            btn.setToolTip(categoria)
            btn.setChecked(activo)
            btn.setFixedHeight(26)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ACENTO_SUAVE if activo else 'transparent'};
                    color: {ACENTO if activo else TEXTO_SECUNDARIO};
                    border: 1px solid {ACENTO if activo else BORDE};
                    border-radius: 12px; padding: 0 10px;
                    font-family: {FUENTE_UI}; font-size: 11px; font-weight: 600;
                }}
                QPushButton:hover {{ border-color: {ACENTO}; color: {ACENTO}; }}
            """)

    def _filtrar_por_categoria(self, categoria):
        self.categoria_activa = categoria
        self._refrescar_estilos_chips()
        if self._modo != "duplicados":
            self._refrescar_vista()

    def _cambiar_orden(self, index):
        self.orden_activo = self.combo_orden.itemData(index)
        if self._modo == "busqueda":
            self._ejecutar_busqueda()

    def _refrescar_historial(self):
        while self.historial_layout.count():
            item = self.historial_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        try:
            consultas = logica.obtener_historial(6)
        except Exception:
            consultas = []
        self._tiene_historial = bool(consultas)

        if consultas:
            lbl = QLabel("Recientes")
            lbl.setStyleSheet(f"""
                color: {TEXTO_TERCIARIO}; font-family: {FUENTE_META}; font-size: 10px;
                background: transparent; border: none;
            """)
            self.historial_layout.addWidget(lbl)
            for consulta in consultas:
                chip = QPushButton(_recortar_medio(consulta, 22))
                chip.setToolTip(consulta)
                chip.setCursor(Qt.PointingHandCursor)
                chip.setFixedHeight(24)
                chip.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {BG_INPUT}; color: {TEXTO_SECUNDARIO};
                        border: 1px solid {BORDE_SUAVE}; border-radius: 12px; padding: 0 10px;
                        font-family: {FUENTE_UI}; font-size: 11px;
                    }}
                    QPushButton:hover {{ border-color: {ACENTO}; color: {ACENTO}; }}
                """)
                chip.clicked.connect(lambda _c, q=consulta: self.txt_buscar.setText(q))
                self.historial_layout.addWidget(chip)
            self.historial_layout.addStretch()
            borrar = QPushButton("Borrar")
            borrar.setCursor(Qt.PointingHandCursor)
            borrar.setFixedHeight(24)
            borrar.setStyleSheet(f"""
                QPushButton {{ background: transparent; color: {TEXTO_TERCIARIO}; border: none;
                               font-family: {FUENTE_UI}; font-size: 10px; }}
                QPushButton:hover {{ color: {PELIGRO_HOVER}; }}
            """)
            borrar.clicked.connect(self._borrar_historial)
            self.historial_layout.addWidget(borrar)
        self._actualizar_historial_visible()

    def _actualizar_historial_visible(self):
        self.frame_historial.setVisible(self._tiene_historial and not self.txt_buscar.text().strip())

    def _borrar_historial(self):
        logica.borrar_historial()
        self._refrescar_historial()

    def _registrar_consulta_actual(self):
        texto = self.txt_buscar.text().strip()
        if len(texto) >= 2:
            try:
                logica.registrar_busqueda(texto)
                self._refrescar_historial()
            except Exception:
                pass

    # ─────────────────────────────────────────────
    # ÍNDICE / ESCANEO
    # ─────────────────────────────────────────────
    def _actualizar_estado_indice(self):
        ultimo = logica.obtener_ultimo_escaneo()
        if ultimo:
            total = logica.obtener_total_indexado()
            self.lbl_estado_indice.setText(f"{total:,} elementos · {ultimo}".replace(",", " "))
            try:
                stats = logica.obtener_estadisticas_indice()
                resumen = "\n".join(
                    f"{ICONOS_CATEGORIA.get(cat, '📎')} {cat}: {cant:,}".replace(",", " ")
                    for cat, cant in stats.items() if cat != "__total__"
                )
                self.lbl_estado_indice.setToolTip(resumen)
            except Exception:
                pass
        else:
            self.lbl_estado_indice.setText("índice vacío — pulsa Reindexar")
            self.lbl_estado_indice.setToolTip("")

    def iniciar_reindexado(self):
        if self.hilo_escaneo and self.hilo_escaneo.isRunning():
            return
        self.btn_reindexar.setEnabled(False)
        self.btn_reindexar.setText("⟳  Escaneando…")
        self.barra_progreso.show()
        self.hilo_escaneo = HiloEscaneo()
        self.hilo_escaneo.progreso.connect(self._on_progreso_escaneo)
        self.hilo_escaneo.terminado.connect(self._on_escaneo_terminado)
        self.hilo_escaneo.error.connect(self._on_error_escaneo)
        self._retener(self.hilo_escaneo)
        self.hilo_escaneo.start()

    def _on_progreso_escaneo(self, carpeta, total):
        self.lbl_estado_indice.setText(f"indexando… {total:,} elementos".replace(",", " "))
        self.barra_interior.setFixedWidth(min(max(self.barra_progreso.width(), 60), 40 + (total % 400)))

    def _on_escaneo_terminado(self, total):
        self.btn_reindexar.setEnabled(True)
        self.btn_reindexar.setText("⟳  Reindexar")
        self.barra_progreso.hide()
        self._actualizar_estado_indice()
        self._refrescar_vista()

    def _on_error_escaneo(self, mensaje):
        self.btn_reindexar.setEnabled(True)
        self.btn_reindexar.setText("⟳  Reindexar")
        self.barra_progreso.hide()
        QMessageBox.warning(self, "Error al reindexar", mensaje)

    def iniciar_limpieza_indice(self):
        if self.hilo_limpieza and self.hilo_limpieza.isRunning():
            return
        self.btn_limpiar_indice.setEnabled(False)
        self.hilo_limpieza = HiloLimpieza()
        self.hilo_limpieza.terminado.connect(self._on_limpieza_terminada)
        self.hilo_limpieza.error.connect(self._on_limpieza_error)
        self._retener(self.hilo_limpieza)
        self.hilo_limpieza.start()

    def _on_limpieza_terminada(self, eliminadas):
        self.btn_limpiar_indice.setEnabled(True)
        self._actualizar_estado_indice()
        plural = "s" if eliminadas != 1 else ""
        self.lbl_contador.setText(f"{eliminadas} entrada{plural} obsoleta{plural} eliminada{plural}")

    def _on_limpieza_error(self, mensaje):
        self.btn_limpiar_indice.setEnabled(True)
        QMessageBox.warning(self, "Error al limpiar el índice", mensaje)

    def _indexar_carpeta_nueva(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Elige la carpeta a indexar",
                                                   os.path.expanduser("~"))
        if carpeta:
            self._reindexar_carpeta_puntual(carpeta)

    def _reindexar_carpeta_puntual(self, carpeta):
        if not carpeta or not os.path.isdir(carpeta):
            QMessageBox.warning(self, "Ruta no válida", "Esa carpeta ya no existe en disco.")
            return
        if self.hilo_carpeta and self.hilo_carpeta.isRunning():
            return
        self.lbl_contador.setText(f"indexando «{_recortar_medio(carpeta, 40)}»…")
        self.btn_indexar_carpeta.setEnabled(False)
        self.hilo_carpeta = HiloCarpeta(carpeta)
        self.hilo_carpeta.terminado.connect(self._on_carpeta_terminada)
        self.hilo_carpeta.error.connect(self._on_carpeta_error)
        self._retener(self.hilo_carpeta)
        self.hilo_carpeta.start()

    def _on_carpeta_terminada(self, total):
        self.btn_indexar_carpeta.setEnabled(True)
        self._actualizar_estado_indice()
        self._refrescar_vista()
        self.lbl_contador.setText(f"Carpeta indexada: {total} elemento{'s' if total != 1 else ''}")

    def _on_carpeta_error(self, mensaje):
        self.btn_indexar_carpeta.setEnabled(True)
        QMessageBox.warning(self, "Error al indexar", mensaje)

    # ─────────────────────────────────────────────
    # BÚSQUEDA
    # ─────────────────────────────────────────────
    def _refrescar_vista(self):
        if self.txt_buscar.text().strip():
            self._ejecutar_busqueda()
        else:
            self._mostrar_inicio()

    def _on_texto_cambiado(self, texto):
        t = texto.strip()
        self._actualizar_historial_visible()
        if not t:
            self.timer_busqueda.stop()
            if self._modo != "duplicados":
                self._mostrar_inicio()
            return
        if len(t) < 2:
            self.timer_busqueda.stop()
            return
        self.timer_busqueda.start(220)

    def _on_enter_pressed(self):
        self._registrar_consulta_actual()
        if self.timer_busqueda.isActive():
            self.timer_busqueda.stop()
            self._ejecutar_busqueda()
        else:
            self._abrir_primer_resultado()

    def _ejecutar_busqueda(self, *_):
        texto = self.txt_buscar.text().strip()
        if not texto:
            self._mostrar_inicio()
            return
        if self.btn_duplicados.isChecked():
            self.btn_duplicados.blockSignals(True)
            self.btn_duplicados.setChecked(False)
            self.btn_duplicados.blockSignals(False)
        self._modo = "busqueda"
        self.btn_cargar_mas.hide()
        self._generacion_busqueda += 1
        self._lanzar_busqueda(texto, offset=0, reemplazar=True)

    def _cargar_mas_resultados(self):
        texto = self.txt_buscar.text().strip()
        if texto:
            self._lanzar_busqueda(texto, offset=self._offset_actual, reemplazar=False)

    def _lanzar_busqueda(self, texto, offset, reemplazar):
        self._tiempo_inicio_busqueda = time.time()
        hilo = HiloBusqueda(
            texto=texto,
            categoria=self.categoria_activa,
            orden=self.orden_activo,
            incluir_contenido=self.chk_contenido.isChecked() and offset == 0,
            offset=offset,
            limite=TAMANO_PAGINA,
            generacion=self._generacion_busqueda,
            reemplazar=reemplazar,
        )
        hilo.resultados_listos.connect(self._on_resultados_listos)
        hilo.error.connect(self._on_error_busqueda)
        self.hilo_busqueda = hilo
        self._retener(hilo)
        hilo.start()

    def _on_resultados_listos(self, resultados, generacion, reemplazar):
        if generacion != self._generacion_busqueda or self._modo != "busqueda":
            return
        if reemplazar:
            self._limpiar_resultados()

        terminos = logica.terminos_busqueda(self.txt_buscar.text())
        self._agregar_filas(resultados, terminos)

        if not self.resultados_actuales:
            self._mostrar_vacio(
                "Sin resultados<br><br><span style='color:#6b6860;'>Prueba con otra palabra, "
                "quita filtros o activa la búsqueda en contenido.</span>"
            )

        elapsed_ms = int((time.time() - self._tiempo_inicio_busqueda) * 1000)
        total = len(self.resultados_actuales)
        self.lbl_contador.setText(f"{total} resultado{'s' if total != 1 else ''} · {elapsed_ms} ms")
        self.btn_cargar_mas.setVisible(len(resultados) >= TAMANO_PAGINA)
        self._grid_sucio = True
        self._redibujar_resultados()

    def _on_error_busqueda(self, mensaje):
        self.lbl_contador.setText("error en la búsqueda")
        QMessageBox.warning(self, "Error de búsqueda", mensaje)

    # ─────────────────────────────────────────────
    # PANTALLA DE INICIO (fijados + recientes)
    # ─────────────────────────────────────────────
    def _mostrar_inicio(self):
        self._generacion_busqueda += 1  # invalida cualquier búsqueda en vuelo
        self._modo = "inicio"
        self.btn_cargar_mas.hide()
        self._limpiar_resultados()
        try:
            fijados = logica.obtener_fijados()
            recientes = logica.archivos_recientes(15, self.categoria_activa)
        except Exception:
            fijados, recientes = [], []

        if fijados:
            self._agregar_encabezado("★  Fijados", DORADO)
            self._agregar_filas(fijados, [])
        if recientes:
            self._agregar_encabezado("Modificados recientemente", TEXTO_TERCIARIO)
            self._agregar_filas([r for r in recientes if not r["fijado"]], [])

        if not self.resultados_actuales:
            self._mostrar_vacio(
                "Escribe para buscar en todo el sistema.<br><br>"
                "<span style='color:#6b6860;'>Prueba con <b>ext:pdf</b>, <b>size:&gt;10mb</b>, "
                "<b>fecha:semana</b>, <b>\"frase exacta\"</b> o <b>-excluir</b>.<br>"
                "Pulsa ? arriba para ver todos los atajos.</span>"
            )
            self.lbl_contador.setText("")
        else:
            self.lbl_contador.setText("Fija archivos con Ctrl+D para tenerlos siempre a mano")
        self._grid_sucio = True
        self._redibujar_resultados()

    # ─────────────────────────────────────────────
    # DUPLICADOS
    # ─────────────────────────────────────────────
    def _alternar_duplicados(self, activo):
        if activo:
            self.lbl_contador.setText("buscando duplicados…")
            self.hilo_duplicados = HiloDuplicados()
            self.hilo_duplicados.listo.connect(self._on_duplicados_listos)
            self.hilo_duplicados.error.connect(self._on_error_busqueda)
            self._retener(self.hilo_duplicados)
            self.hilo_duplicados.start()
        else:
            self._refrescar_vista()

    def _on_duplicados_listos(self, grupos, recuperable):
        if not self.btn_duplicados.isChecked():
            return
        self._generacion_busqueda += 1
        self._modo = "duplicados"
        self.btn_cargar_mas.hide()
        self._limpiar_resultados()

        total_archivos = 0
        for g in grupos:
            n = len(g["archivos"])
            self._agregar_encabezado(
                f"{_recortar_medio(g['nombre'], 48)}  ·  {logica.formatear_tamano(g['tamano'])}  ·  {n} copias",
                ACENTO_HOVER
            )
            self._agregar_filas(g["archivos"], [])
            total_archivos += n

        if grupos:
            self.lbl_contador.setText(
                f"{len(grupos)} grupos · {total_archivos} archivos · "
                f"{logica.formatear_tamano(recuperable)} recuperables"
            )
        else:
            self._mostrar_vacio(
                "No se encontraron duplicados<br><br><span style='color:#6b6860;'>"
                "Se comparan nombre y tamaño (archivos de 100 KB o más).</span>"
            )
            self.lbl_contador.setText("sin duplicados")
        self._grid_sucio = True
        self._redibujar_resultados()

    # ─────────────────────────────────────────────
    # POBLADO DE RESULTADOS
    # ─────────────────────────────────────────────
    def _limpiar_resultados(self):
        self.lista_resultados.clear()
        self._limpiar_grid()
        self.resultados_actuales = []
        self._offset_actual = 0
        self._grid_sucio = True

    def _agregar_encabezado(self, texto, color):
        lbl = QLabel(texto)
        lbl.setStyleSheet(f"""
            color: {color}; font-family: {FUENTE_SERIF}; font-size: 11px; font-weight: 700;
            font-style: italic; padding: 8px 6px 2px 6px; background: transparent; border: none;
        """)
        item = QListWidgetItem()
        item.setFlags(Qt.NoItemFlags)
        item.setSizeHint(QSize(100, 30))
        self.lista_resultados.addItem(item)
        self.lista_resultados.setItemWidget(item, lbl)

    def _agregar_filas(self, resultados, terminos):
        for resultado in resultados:
            item = QListWidgetItem()
            fila = FilaResultado(resultado, terminos)
            item.setData(Qt.UserRole, resultado)
            item.setSizeHint(QSize(100, fila.sizeHint().height()))
            self.lista_resultados.addItem(item)
            self.lista_resultados.setItemWidget(item, fila)
        self.resultados_actuales.extend(resultados)
        self._offset_actual = len(self.resultados_actuales)
        self._grid_sucio = True

    def _mostrar_vacio(self, html_texto):
        self._mensaje_vacio = html_texto
        item = QListWidgetItem()
        item.setFlags(Qt.NoItemFlags)
        item.setSizeHint(QSize(400, 230))
        self.lista_resultados.addItem(item)
        self.lista_resultados.setItemWidget(item, _crear_placeholder(html_texto))

    def _limpiar_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _reconstruir_grid(self):
        self._limpiar_grid()
        self._grid_sucio = False
        if not self.resultados_actuales:
            self.grid_layout.addWidget(_crear_placeholder(self._mensaje_vacio), 0, 0, 1, 4)
            return
        terminos = logica.terminos_busqueda(self.txt_buscar.text())
        cols = max(3, self.scroll_grid.viewport().width() // 160)
        for i, r in enumerate(self.resultados_actuales):
            tarjeta = TarjetaGrid(r, terminos)
            tarjeta.clic.connect(self._mostrar_vista_previa)
            tarjeta.doble.connect(self._abrir_desde_resultado)
            self.grid_layout.addWidget(tarjeta, i // cols, i % cols)

    def _redibujar_resultados(self):
        if self._modo_vista == "lista":
            self.lista_resultados.show()
            self.scroll_grid.hide()
        else:
            if self._grid_sucio:
                self._reconstruir_grid()
            self.lista_resultados.hide()
            self.scroll_grid.show()

    # ─────────────────────────────────────────────
    # VISTA PREVIA
    # ─────────────────────────────────────────────
    def _limpiar_vista_previa(self):
        self._resultado_sel = None
        self.lbl_prev_img.clear()
        self.lbl_prev_img.setText("🗂️")
        self.lbl_prev_nombre.setText("Sin selección")
        self.lbl_prev_meta.setText("Selecciona un archivo para ver sus detalles y una vista previa.")
        self.txt_prev_texto.hide()
        for b in (self.btn_prev_abrir, self.btn_prev_ubic, self.btn_prev_fijar):
            b.setEnabled(False)

    def _on_item_actual(self, actual, _previo):
        if actual is None:
            return
        resultado = actual.data(Qt.UserRole)
        if resultado:
            self._mostrar_vista_previa(resultado)

    def _mostrar_vista_previa(self, r):
        self._resultado_sel = r
        if not self.panel_preview.isVisible():
            return

        for b in (self.btn_prev_abrir, self.btn_prev_ubic, self.btn_prev_fijar):
            b.setEnabled(True)

        pix = None
        if r["categoria"] == "Imágenes":
            pix = _cargar_miniatura(r["ruta"], 242, 148)
        self.lbl_prev_img.clear()
        if pix:
            self.lbl_prev_img.setPixmap(pix)
        else:
            self.lbl_prev_img.setText(ICONOS_CATEGORIA.get(r["categoria"], "📎"))

        self.lbl_prev_nombre.setText(r["nombre"])

        def linea(etiqueta, valor):
            return (f"<span style='color:{TEXTO_TERCIARIO};'>{etiqueta}</span><br>"
                    f"<span style='color:{TEXTO_PRINCIPAL};'>{html.escape(str(valor))}</span><br>")

        tipo = r["categoria"] + (f"  ({r['extension']})" if r.get("extension") else "")
        meta = linea("Carpeta", r["carpeta"]) + linea("Tamaño", logica.formatear_tamano(r["tamano"])) \
            + linea("Modificado", _formatear_fecha(r["modificado"])) + linea("Tipo", tipo)
        if not os.path.exists(r["ruta"]):
            meta += f"<span style='color:{PELIGRO_HOVER};'>⚠ Ya no existe en disco (usa Limpiar)</span>"
        self.lbl_prev_meta.setText(meta)

        texto = None if r["es_carpeta"] else logica.leer_vista_previa_texto(r["ruta"])
        if texto:
            self.txt_prev_texto.setPlainText(texto)
            self.txt_prev_texto.show()
        else:
            self.txt_prev_texto.hide()

        self.btn_prev_fijar.setText("★" if r.get("fijado") else "☆")
        self.btn_prev_fijar.setToolTip("Quitar de fijados (Ctrl+D)" if r.get("fijado") else "Fijar arriba (Ctrl+D)")

    # ─────────────────────────────────────────────
    # ACCIONES SOBRE ARCHIVOS
    # ─────────────────────────────────────────────
    def _abrir_primer_resultado(self):
        for i in range(self.lista_resultados.count()):
            resultado = self.lista_resultados.item(i).data(Qt.UserRole)
            if resultado:
                self._abrir_desde_resultado(resultado)
                return

    def _abrir_item(self, item):
        resultado = item.data(Qt.UserRole)
        if resultado:
            self._abrir_desde_resultado(resultado)

    def _abrir_desde_resultado(self, resultado):
        self._registrar_consulta_actual()
        self._abrir_ruta(resultado["ruta"])

    def _abrir_seleccionado(self):
        if self._resultado_sel:
            self._abrir_desde_resultado(self._resultado_sel)

    def _abrir_ubicacion_seleccionado(self):
        if self._resultado_sel:
            self._abrir_carpeta_contenedora(self._resultado_sel)

    def _copiar_ruta_seleccionado(self):
        if self._resultado_sel:
            self._copiar_ruta(self._resultado_sel)

    def _fijar_seleccionado(self):
        if self._resultado_sel:
            self._alternar_fijado(self._resultado_sel)

    def _abrir_ruta(self, ruta):
        try:
            if sys.platform.startswith("win"):
                os.startfile(ruta)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", ruta])
            else:
                subprocess.Popen(["xdg-open", ruta])
        except Exception as e:
            QMessageBox.warning(self, "Error al abrir", str(e))

    def _abrir_carpeta_contenedora(self, resultado):
        try:
            if resultado["es_carpeta"]:
                self._abrir_ruta(resultado["ruta"])
            elif sys.platform.startswith("win"):
                subprocess.Popen(["explorer", "/select,", os.path.normpath(resultado["ruta"])])
            else:
                self._abrir_ruta(resultado["carpeta"])
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _copiar_ruta(self, resultado):
        QApplication.clipboard().setText(resultado["ruta"])
        self.lbl_contador.setText("Ruta copiada al portapapeles")

    def _copiar_nombre(self, resultado):
        QApplication.clipboard().setText(resultado["nombre"])
        self.lbl_contador.setText("Nombre copiado al portapapeles")

    def _copiar_archivo(self, resultado):
        """Deja el archivo en el portapapeles para pegarlo en el Explorador."""
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(resultado["ruta"])])
        QApplication.clipboard().setMimeData(mime)
        self.lbl_contador.setText("Archivo copiado: ya puedes pegarlo en otra carpeta")

    def _alternar_fijado(self, resultado):
        try:
            resultado["fijado"] = logica.alternar_fijado(resultado["ruta"])
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return
        self._mostrar_vista_previa(resultado)
        if self._modo == "inicio":
            self._mostrar_inicio()
        elif self._modo == "busqueda":
            self._ejecutar_busqueda()
        else:
            self._grid_sucio = True

    def _exportar_csv(self):
        if not self.resultados_actuales:
            self.lbl_contador.setText("No hay resultados que exportar")
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar resultados",
            os.path.join(os.path.expanduser("~"), "resultados_busqueda.csv"),
            "CSV (*.csv)"
        )
        if not ruta:
            return
        try:
            n = logica.exportar_csv(self.resultados_actuales, ruta)
            self.lbl_contador.setText(f"{n} resultados exportados")
        except Exception as e:
            QMessageBox.warning(self, "Error al exportar", str(e))

    def _eliminar_a_papelera(self, resultado):
        respuesta = QMessageBox.question(
            self, "Eliminar", f"¿Enviar «{resultado['nombre']}» a la papelera?",
            QMessageBox.Yes | QMessageBox.No
        )
        if respuesta != QMessageBox.Yes:
            return
        try:
            try:
                from explorador.logica_explorador import borrar_elemento_nativo
            except ImportError:
                from send2trash import send2trash  # alternativa si no existe el módulo explorador

                def borrar_elemento_nativo(ruta):
                    send2trash(ruta)
                    return True
            if borrar_elemento_nativo(resultado["ruta"]):
                logica.eliminar_ruta_del_indice(resultado["ruta"])
                self._refrescar_vista()
        except Exception as e:
            QMessageBox.warning(self, "Error al eliminar", str(e))

    # ─────────────────────────────────────────────
    # MENÚ CONTEXTUAL
    # ─────────────────────────────────────────────
    def _menu_contextual(self, pos):
        item = self.lista_resultados.itemAt(pos)
        if not item:
            return
        resultado = item.data(Qt.UserRole)
        if resultado:
            self._mostrar_menu_contextual(resultado, self.lista_resultados.viewport().mapToGlobal(pos))

    def _menu_contextual_grid(self, pos):
        pos_contenedor = self.grid_container.mapFrom(self.scroll_grid.viewport(), pos)
        widget = self.grid_container.childAt(pos_contenedor)
        while widget and not isinstance(widget, TarjetaGrid):
            widget = widget.parent()
        if widget:
            self._mostrar_menu_contextual(widget.resultado, self.scroll_grid.viewport().mapToGlobal(pos))

    def _mostrar_menu_contextual(self, resultado, global_pos):
        menu = QMenu(self)
        menu.setStyleSheet(_estilo_menu())
        a_abrir = menu.addAction("Abrir")
        a_ubic = menu.addAction("Abrir ubicación")
        menu.addSeparator()
        a_ruta = menu.addAction("Copiar ruta")
        a_nombre = menu.addAction("Copiar nombre")
        a_archivo = menu.addAction("Copiar archivo (para pegar)")
        menu.addSeparator()
        a_fijar = menu.addAction("Quitar de fijados" if resultado.get("fijado") else "★  Fijar arriba")
        a_reindex = menu.addAction("Reindexar esta carpeta")
        menu.addSeparator()
        a_papelera = menu.addAction("Enviar a la papelera")

        elegida = menu.exec_(global_pos)
        if elegida is None:
            return
        if elegida == a_abrir:
            self._abrir_desde_resultado(resultado)
        elif elegida == a_ubic:
            self._abrir_carpeta_contenedora(resultado)
        elif elegida == a_ruta:
            self._copiar_ruta(resultado)
        elif elegida == a_nombre:
            self._copiar_nombre(resultado)
        elif elegida == a_archivo:
            self._copiar_archivo(resultado)
        elif elegida == a_fijar:
            self._alternar_fijado(resultado)
        elif elegida == a_reindex:
            carpeta = resultado["ruta"] if resultado["es_carpeta"] else resultado["carpeta"]
            self._reindexar_carpeta_puntual(carpeta)
        elif elegida == a_papelera:
            self._eliminar_a_papelera(resultado)

    # ─────────────────────────────────────────────
    # CIERRE
    # ─────────────────────────────────────────────
    def closeEvent(self, event):
        for hilo in (self.hilo_escaneo, self.hilo_carpeta):
            if hilo and hilo.isRunning():
                hilo.cancelado = True
                hilo.wait(500)
        for hilo in (self.hilo_busqueda, self.hilo_limpieza, self.hilo_duplicados):
            if hilo and hilo.isRunning():
                hilo.wait(200)
        super().closeEvent(event)