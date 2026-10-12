from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                             QTextEdit, QLineEdit, QPushButton, QLabel, QWidget, QFrame,
                             QMessageBox, QShortcut, QSizePolicy, QGraphicsOpacityEffect,
                             QScrollArea)
from PyQt5.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QKeySequence, QTextCursor
from notas.logica_notas import LogicaNotas


# ─────────────────────────────────────────────────────────────
# 🎨 PALETA — cálida, de bajo contraste, sin verdes ni blanco/negro puros
# ─────────────────────────────────────────────────────────────
BG_APP = "#242730"          # fondo general (grafito cálido, no negro)
BG_PANEL = "#2b2e38"        # sidebar / paneles
BG_INPUT = "#1d2028"        # campos de texto
BG_INPUT_HOVER = "#20232c"
BORDE = "#3c3f4a"
BORDE_SUAVE = "#33363f"
TEXTO_PRINCIPAL = "#ded8ca"   # hueso cálido, nunca blanco puro
TEXTO_SECUNDARIO = "#8f8b83"  # gris cálido para metadatos
TEXTO_TERCIARIO = "#6b6860"
ACENTO = "#c17a56"           # terracota — color de marca de este panel
ACENTO_HOVER = "#d38f6c"
ACENTO_SUAVE = "rgba(193, 122, 86, 0.16)"
DORADO = "#c9a24b"           # para notas fijadas
DORADO_SUAVE = "rgba(201, 162, 75, 0.18)"
PELIGRO = "#a15c52"
PELIGRO_HOVER = "#b76f64"

FUENTE_SERIF = "'Georgia', 'Cambria', 'Constantia', serif"
FUENTE_UI = "'Segoe UI', Arial, sans-serif"
FUENTE_META = "'Consolas', 'Courier New', monospace"


class TarjetaNota(QWidget):
    """Fila enriquecida para cada nota en la lista: título, vista previa y fecha."""

    def __init__(self, titulo, vista_previa, fecha, fijada):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 9, 10, 9)
        layout.setSpacing(3)

        fila_superior = QHBoxLayout()
        fila_superior.setSpacing(6)

        marca = "●  " if fijada else ""
        color_titulo = DORADO if fijada else TEXTO_PRINCIPAL

        self.lbl_titulo = QLabel(self._recortar(marca + (titulo or "Sin título"), 30))
        self.lbl_titulo.setStyleSheet(f"""
            color: {color_titulo};
            font-family: {FUENTE_SERIF};
            font-size: 13px;
            font-weight: 600;
            background: transparent;
            border: none;
        """)

        self.lbl_fecha = QLabel(fecha)
        self.lbl_fecha.setStyleSheet(f"""
            color: {TEXTO_TERCIARIO};
            font-family: {FUENTE_META};
            font-size: 10px;
            background: transparent;
            border: none;
        """)
        self.lbl_fecha.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        fila_superior.addWidget(self.lbl_titulo, 1)
        fila_superior.addWidget(self.lbl_fecha, 0)

        self.lbl_preview = QLabel(self._recortar(vista_previa, 44))
        self.lbl_preview.setStyleSheet(f"""
            color: {TEXTO_SECUNDARIO};
            font-family: {FUENTE_UI};
            font-size: 11px;
            background: transparent;
            border: none;
        """)

        layout.addLayout(fila_superior)
        layout.addWidget(self.lbl_preview)

    @staticmethod
    def _recortar(texto, longitud):
        texto = texto or ""
        return texto if len(texto) <= longitud else texto[:longitud - 1].rstrip() + "…"


class DialogoPapelera(QDialog):
    """Ventana modal cálida para revisar, restaurar o borrar para siempre
    las notas eliminadas. Se conservan 30 días antes de purgarse solas."""

    def __init__(self, parent, logica):
        super().__init__(parent)
        self.logica = logica
        self.setWindowTitle("Papelera")
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.resize(460, 420)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDE};
                border-radius: 12px;
            }}
            QLabel {{ color: {TEXTO_PRINCIPAL}; font-family: {FUENTE_UI}; }}
            QScrollArea {{ border: none; background: transparent; }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 16)
        root.setSpacing(10)

        top = QHBoxLayout()
        titulo = QLabel("🗑  Papelera")
        titulo.setStyleSheet(f"color:{TEXTO_PRINCIPAL}; font-family:{FUENTE_SERIF}; font-size:16px; font-weight:700;")
        top.addWidget(titulo)
        top.addStretch()
        btn_x = QPushButton("✕")
        btn_x.setFixedSize(26, 26)
        btn_x.setCursor(Qt.PointingHandCursor)
        btn_x.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {TEXTO_SECUNDARIO}; border: none; font-size: 13px; border-radius: 5px; }}
            QPushButton:hover {{ background: {PELIGRO}; color: {TEXTO_PRINCIPAL}; }}
        """)
        btn_x.clicked.connect(self.close)
        top.addWidget(btn_x)
        root.addLayout(top)

        info = QLabel("Las notas eliminadas se guardan aquí 30 días antes de borrarse para siempre.")
        info.setWordWrap(True)
        info.setStyleSheet(f"color:{TEXTO_TERCIARIO}; font-size:11px; font-style:italic;")
        root.addWidget(info)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        contenido = QWidget()
        self.lista_layout = QVBoxLayout(contenido)
        self.lista_layout.setSpacing(6)
        self.lista_layout.addStretch()
        scroll.setWidget(contenido)
        root.addWidget(scroll, 1)

        fila_pie = QHBoxLayout()
        fila_pie.addStretch()
        btn_vaciar = QPushButton("Vaciar papelera")
        btn_vaciar.setCursor(Qt.PointingHandCursor)
        btn_vaciar.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: {PELIGRO}; border: 1px solid {PELIGRO};
                border-radius: 6px; padding: 6px 14px; font-family: {FUENTE_UI}; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {PELIGRO}; color: {TEXTO_PRINCIPAL}; }}
        """)
        btn_vaciar.clicked.connect(self._vaciar_papelera)
        fila_pie.addWidget(btn_vaciar)
        root.addLayout(fila_pie)

        self._cargar_lista()

    def _cargar_lista(self):
        while self.lista_layout.count() > 1:
            item = self.lista_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        elementos = self.logica.listar_papelera()
        if not elementos:
            vacio = QLabel("La papelera está vacía.")
            vacio.setAlignment(Qt.AlignCenter)
            vacio.setStyleSheet(f"color:{TEXTO_TERCIARIO}; font-size:12px; padding: 24px 10px;")
            self.lista_layout.insertWidget(0, vacio)
            return

        for meta in elementos:
            fila = QFrame()
            fila.setStyleSheet(f"""
                QFrame {{ background-color: {BG_INPUT}; border: 1px solid {BORDE_SUAVE}; border-radius: 8px; }}
            """)
            fl = QHBoxLayout(fila)
            fl.setContentsMargins(10, 8, 10, 8)
            fl.setSpacing(8)

            info_v = QVBoxLayout()
            lbl_titulo = QLabel(meta["titulo"] or "Sin título")
            lbl_titulo.setStyleSheet(f"color:{TEXTO_PRINCIPAL}; font-family:{FUENTE_SERIF}; font-size:12px; font-weight:700;")
            lbl_meta = QLabel(f"Eliminada {meta['eliminada_en']} · se borra en {meta['dias_restantes']} día(s)")
            lbl_meta.setStyleSheet(f"color:{TEXTO_TERCIARIO}; font-family:{FUENTE_META}; font-size:9px;")
            info_v.addWidget(lbl_titulo)
            info_v.addWidget(lbl_meta)
            fl.addLayout(info_v, 1)

            btn_restaurar = QPushButton("↺  Restaurar")
            btn_restaurar.setCursor(Qt.PointingHandCursor)
            btn_restaurar.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ACENTO}; color: {BG_APP}; border: none;
                    border-radius: 6px; padding: 5px 10px; font-family: {FUENTE_UI}; font-size: 11px; font-weight: 700;
                }}
                QPushButton:hover {{ background-color: {ACENTO_HOVER}; }}
            """)
            btn_restaurar.clicked.connect(lambda _, c=meta["clave"]: self._restaurar(c))
            fl.addWidget(btn_restaurar)

            btn_borrar = QPushButton("✕")
            btn_borrar.setCursor(Qt.PointingHandCursor)
            btn_borrar.setFixedSize(28, 28)
            btn_borrar.setToolTip("Eliminar para siempre")
            btn_borrar.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent; color: {TEXTO_SECUNDARIO}; border: 1px solid {BORDE};
                    border-radius: 6px; font-size: 12px;
                }}
                QPushButton:hover {{ background-color: {PELIGRO}; color: {TEXTO_PRINCIPAL}; border-color: {PELIGRO}; }}
            """)
            btn_borrar.clicked.connect(lambda _, c=meta["clave"], t=meta["titulo"]: self._borrar_definitivo(c, t))
            fl.addWidget(btn_borrar)

            self.lista_layout.insertWidget(self.lista_layout.count() - 1, fila)

    def _restaurar(self, clave):
        self.logica.restaurar_nota(clave)
        self._cargar_lista()
        if self.parent():
            self.parent().cargar_lista_notas()

    def _borrar_definitivo(self, clave, titulo):
        caja = QMessageBox(self)
        caja.setWindowTitle("Eliminar para siempre")
        caja.setText(f"«{titulo}» se borrará permanentemente y no podrá recuperarse. ¿Continuar?")
        caja.setIcon(QMessageBox.NoIcon)
        btn_si = caja.addButton("Eliminar para siempre", QMessageBox.DestructiveRole)
        caja.addButton("Cancelar", QMessageBox.RejectRole)
        caja.setStyleSheet(f"""
            QMessageBox {{ background-color: {BG_PANEL}; }}
            QLabel {{ color: {TEXTO_PRINCIPAL}; font-family: {FUENTE_UI}; font-size: 12px; }}
            QPushButton {{
                background-color: {BG_INPUT}; color: {TEXTO_PRINCIPAL};
                border: 1px solid {BORDE}; border-radius: 6px; padding: 6px 14px;
                font-family: {FUENTE_UI}; font-size: 12px;
            }}
            QPushButton:hover {{ border-color: {PELIGRO}; color: {PELIGRO}; }}
        """)
        caja.exec_()
        if caja.clickedButton() == btn_si:
            self.logica.eliminar_definitivamente(clave)
            self._cargar_lista()

    def _vaciar_papelera(self):
        caja = QMessageBox(self)
        caja.setWindowTitle("Vaciar papelera")
        caja.setText("Se eliminarán permanentemente todas las notas de la papelera. ¿Continuar?")
        caja.setIcon(QMessageBox.NoIcon)
        btn_si = caja.addButton("Vaciar", QMessageBox.DestructiveRole)
        caja.addButton("Cancelar", QMessageBox.RejectRole)
        caja.setStyleSheet(f"""
            QMessageBox {{ background-color: {BG_PANEL}; }}
            QLabel {{ color: {TEXTO_PRINCIPAL}; font-family: {FUENTE_UI}; font-size: 12px; }}
            QPushButton {{
                background-color: {BG_INPUT}; color: {TEXTO_PRINCIPAL};
                border: 1px solid {BORDE}; border-radius: 6px; padding: 6px 14px;
                font-family: {FUENTE_UI}; font-size: 12px;
            }}
            QPushButton:hover {{ border-color: {PELIGRO}; color: {PELIGRO}; }}
        """)
        caja.exec_()
        if caja.clickedButton() == btn_si:
            self.logica.vaciar_papelera()
            self._cargar_lista()


class VentanaNotas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logica = LogicaNotas()
        self.nota_actual = None
        self._suprimir_autoguardado = False

        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.NonModal)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(880, 560)
        self.setMinimumSize(680, 440)
        self.drag_position = QPoint()

        # Temporizador de autoguardado (debounce): guarda 900ms después de dejar de escribir
        self.timer_autoguardado = QTimer(self)
        self.timer_autoguardado.setSingleShot(True)
        self.timer_autoguardado.timeout.connect(self._autoguardar)

        self.init_ui()
        self.cargar_lista_notas()
        self._configurar_atajos()

    # ─────────────────────────────────────────────
    # ARRASTRE (solo desde la cabecera)
    # ─────────────────────────────────────────────
    def _header_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def _header_mouse_move(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def _configurar_atajos(self):
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.nueva_nota)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=lambda: self.guardar_nota(manual=True))
        QShortcut(QKeySequence("Ctrl+F"), self, activated=lambda: (self.txt_buscar.setFocus(), self.txt_buscar.selectAll()))

    # ─────────────────────────────────────────────
    # CONSTRUCCIÓN DE INTERFAZ
    # ─────────────────────────────────────────────
    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        contenedor = QFrame()
        contenedor.setStyleSheet(f"""
            QFrame#contenedorNotas {{
                background-color: {BG_APP};
                border: 1px solid {BORDE};
                border-radius: 10px;
            }}
        """)
        contenedor.setObjectName("contenedorNotas")
        root.addWidget(contenedor)

        layout_main = QVBoxLayout(contenedor)
        layout_main.setContentsMargins(0, 0, 0, 0)
        layout_main.setSpacing(0)

        # ── CABECERA ──────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(46)
        header.setStyleSheet(f"""
            background-color: {BG_PANEL};
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            border-bottom: 1px solid {BORDE_SUAVE};
        """)
        header.mousePressEvent = self._header_mouse_press
        header.mouseMoveEvent = self._header_mouse_move

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 10, 0)

        lbl_titulo_app = QLabel("Cuaderno")
        lbl_titulo_app.setStyleSheet(f"""
            color: {TEXTO_PRINCIPAL};
            font-family: {FUENTE_SERIF};
            font-size: 15px;
            font-weight: 700;
            letter-spacing: 0.5px;
            border: none; background: transparent;
        """)

        self.lbl_contador_notas = QLabel("")
        self.lbl_contador_notas.setStyleSheet(f"""
            color: {TEXTO_TERCIARIO}; font-family: {FUENTE_META}; font-size: 10px;
            border: none; background: transparent; padding-left: 8px;
        """)

        btn_cerrar = QPushButton("✕")
        btn_cerrar.setFixedSize(28, 28)
        btn_cerrar.setCursor(Qt.PointingHandCursor)
        btn_cerrar.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {TEXTO_SECUNDARIO}; border: none;
                           font-size: 13px; border-radius: 5px; }}
            QPushButton:hover {{ background: {PELIGRO}; color: {TEXTO_PRINCIPAL}; }}
        """)
        btn_cerrar.clicked.connect(self.close)

        header_layout.addWidget(lbl_titulo_app)
        header_layout.addWidget(self.lbl_contador_notas)
        header_layout.addStretch()
        header_layout.addWidget(btn_cerrar)
        layout_main.addWidget(header)

        # ── CUERPO ────────────────────────────────────────────
        cuerpo = QHBoxLayout()
        cuerpo.setContentsMargins(0, 0, 0, 0)
        cuerpo.setSpacing(0)

        cuerpo.addWidget(self._construir_panel_izquierdo(), 0)
        cuerpo.addWidget(self._separador_vertical(), 0)
        cuerpo.addWidget(self._construir_panel_derecho(), 1)

        layout_main.addLayout(cuerpo, 1)

    def _separador_vertical(self):
        linea = QFrame()
        linea.setFixedWidth(1)
        linea.setStyleSheet(f"background-color: {BORDE_SUAVE}; border: none;")
        return linea

    # ---- panel izquierdo: buscador + lista + nueva nota ----
    def _construir_panel_izquierdo(self):
        panel = QFrame()
        panel.setFixedWidth(250)
        panel.setStyleSheet(f"background-color: {BG_PANEL}; border: none;")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        btn_nueva = QPushButton("＋   Nueva nota")
        btn_nueva.setCursor(Qt.PointingHandCursor)
        btn_nueva.setFixedHeight(36)
        btn_nueva.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACENTO};
                color: {BG_APP};
                border: none;
                border-radius: 7px;
                font-family: {FUENTE_UI};
                font-weight: 600;
                font-size: 12px;
                text-align: left;
                padding-left: 12px;
            }}
            QPushButton:hover {{ background-color: {ACENTO_HOVER}; }}
            QPushButton:pressed {{ background-color: {ACENTO}; }}
        """)
        btn_nueva.clicked.connect(self.nueva_nota)

        fila_nueva = QHBoxLayout()
        fila_nueva.setSpacing(6)
        fila_nueva.addWidget(btn_nueva, 1)

        self.btn_papelera = QPushButton("🗑")
        self.btn_papelera.setToolTip("Papelera")
        self.btn_papelera.setCursor(Qt.PointingHandCursor)
        self.btn_papelera.setFixedSize(36, 36)
        self.btn_papelera.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_INPUT};
                color: {TEXTO_SECUNDARIO};
                border: 1px solid {BORDE};
                border-radius: 7px;
                font-size: 13px;
            }}
            QPushButton:hover {{ border-color: {PELIGRO}; color: {PELIGRO}; }}
        """)
        self.btn_papelera.clicked.connect(self.abrir_papelera)
        fila_nueva.addWidget(self.btn_papelera)
        layout.addLayout(fila_nueva)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍  Buscar en el cuaderno…")
        self.txt_buscar.setFixedHeight(32)
        self.txt_buscar.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BG_INPUT};
                color: {TEXTO_PRINCIPAL};
                border: 1px solid {BORDE};
                border-radius: 7px;
                padding: 0 10px;
                font-family: {FUENTE_UI};
                font-size: 12px;
            }}
            QLineEdit:focus {{ border: 1px solid {ACENTO}; }}
        """)
        self.txt_buscar.textChanged.connect(self.filtrar_notas)
        layout.addWidget(self.txt_buscar)

        self.lista_widget = QListWidget()
        self.lista_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                border-radius: 8px;
                margin-bottom: 3px;
            }}
            QListWidget::item:hover {{
                background-color: {BG_INPUT_HOVER};
            }}
            QListWidget::item:selected {{
                background-color: {ACENTO_SUAVE};
                border: 1px solid {ACENTO};
            }}
            QScrollBar:vertical {{ background: transparent; width: 7px; margin: 2px; }}
            QScrollBar::handle:vertical {{ background: {BORDE}; border-radius: 3px; min-height: 24px; }}
            QScrollBar::handle:vertical:hover {{ background: {TEXTO_TERCIARIO}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
        self.lista_widget.setSpacing(0)
        self.lista_widget.itemClicked.connect(self.seleccionar_nota)
        layout.addWidget(self.lista_widget, 1)

        return panel

    # ---- panel derecho: editor ----
    def _construir_panel_derecho(self):
        panel = QFrame()
        panel.setStyleSheet(f"background-color: {BG_APP}; border: none;")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 18, 22, 14)
        layout.setSpacing(10)

        # Título de la nota
        self.txt_titulo = QLineEdit()
        self.txt_titulo.setPlaceholderText("Título de la nota…")
        self.txt_titulo.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                color: {TEXTO_PRINCIPAL};
                border: none;
                font-family: {FUENTE_SERIF};
                font-weight: 700;
                font-size: 20px;
                padding: 2px 0;
            }}
        """)
        self.txt_titulo.textChanged.connect(self._on_texto_modificado)
        layout.addWidget(self.txt_titulo)

        # Barra de metadatos: fecha · fijar · estado de guardado
        fila_meta = QHBoxLayout()
        fila_meta.setSpacing(10)

        self.lbl_fecha_nota = QLabel("Nota nueva")
        self.lbl_fecha_nota.setStyleSheet(f"""
            color: {TEXTO_TERCIARIO}; font-family: {FUENTE_META}; font-size: 10px;
            border: none; background: transparent;
        """)

        self.btn_fijar = QPushButton("☆  Fijar")
        self.btn_fijar.setCursor(Qt.PointingHandCursor)
        self.btn_fijar.setCheckable(True)
        self.btn_fijar.setFixedHeight(24)
        self._actualizar_estilo_boton_fijar()
        self.btn_fijar.clicked.connect(self.alternar_fijar_nota)

        self.lbl_estado_guardado = QLabel("")
        self.lbl_estado_guardado.setStyleSheet(f"""
            color: {ACENTO}; font-family: {FUENTE_META}; font-size: 10px;
            border: none; background: transparent;
        """)
        self._efecto_estado = QGraphicsOpacityEffect(self.lbl_estado_guardado)
        self.lbl_estado_guardado.setGraphicsEffect(self._efecto_estado)
        self._efecto_estado.setOpacity(0.0)

        fila_meta.addWidget(self.lbl_fecha_nota)
        fila_meta.addWidget(self.btn_fijar)
        fila_meta.addStretch()
        fila_meta.addWidget(self.lbl_estado_guardado)
        layout.addLayout(fila_meta)

        # Barra de formato ligero (estilo cuaderno de campo, markdown simple)
        fila_formato = QHBoxLayout()
        fila_formato.setSpacing(4)
        for etiqueta, tip, funcion in [
            ("N", "Negrita (**texto**)", lambda: self._envolver_seleccion("**")),
            ("I", "Cursiva (_texto_)", lambda: self._envolver_seleccion("_")),
            ("≡", "Lista con guiones", self._insertar_lista),
            ("❝", "Cita", self._insertar_cita),
        ]:
            btn = QPushButton(etiqueta)
            btn.setToolTip(tip)
            btn.setFixedSize(28, 26)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BG_INPUT};
                    color: {TEXTO_SECUNDARIO};
                    border: 1px solid {BORDE};
                    border-radius: 6px;
                    font-family: {FUENTE_SERIF};
                    font-weight: 700;
                    font-size: 12px;
                }}
                QPushButton:hover {{ border-color: {ACENTO}; color: {ACENTO}; }}
            """)
            btn.clicked.connect(funcion)
            fila_formato.addWidget(btn)
        fila_formato.addStretch()
        layout.addLayout(fila_formato)

        # Editor de contenido con "margen" de cuaderno a la izquierda (elemento distintivo)
        fila_editor = QHBoxLayout()
        fila_editor.setContentsMargins(0, 0, 0, 0)
        fila_editor.setSpacing(0)

        margen = QFrame()
        margen.setFixedWidth(3)
        margen.setStyleSheet(f"background-color: {ACENTO}; border: none; border-radius: 1px;")
        fila_editor.addWidget(margen)

        self.txt_contenido = QTextEdit()
        self.txt_contenido.setPlaceholderText("Escribe aquí tus observaciones o apuntes…")
        self.txt_contenido.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_INPUT};
                color: {TEXTO_PRINCIPAL};
                border: 1px solid {BORDE};
                border-left: none;
                border-radius: 0 8px 8px 0;
                padding: 14px 16px;
                font-family: {FUENTE_SERIF};
                font-size: 14px;
                line-height: 1.5;
                selection-background-color: {ACENTO_SUAVE};
            }}
        """)
        self.txt_contenido.textChanged.connect(self._on_texto_modificado)
        fila_editor.addWidget(self.txt_contenido, 1)
        layout.addLayout(fila_editor, 1)

        # Pie: contador de palabras + acciones
        fila_pie = QHBoxLayout()
        fila_pie.setSpacing(10)

        self.lbl_contador_palabras = QLabel("0 palabras")
        self.lbl_contador_palabras.setStyleSheet(f"""
            color: {TEXTO_TERCIARIO}; font-family: {FUENTE_META}; font-size: 10px;
            border: none; background: transparent;
        """)
        fila_pie.addWidget(self.lbl_contador_palabras)
        fila_pie.addStretch()

        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.setCursor(Qt.PointingHandCursor)
        btn_eliminar.setFixedHeight(30)
        btn_eliminar.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {PELIGRO};
                border: 1px solid {PELIGRO};
                border-radius: 6px;
                padding: 0 14px;
                font-family: {FUENTE_UI};
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {PELIGRO}; color: {TEXTO_PRINCIPAL}; }}
        """)
        btn_eliminar.clicked.connect(self.eliminar_nota)

        btn_guardar = QPushButton("Guardar ahora")
        btn_guardar.setCursor(Qt.PointingHandCursor)
        btn_guardar.setFixedHeight(30)
        btn_guardar.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACENTO};
                color: {BG_APP};
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                font-family: {FUENTE_UI};
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background-color: {ACENTO_HOVER}; }}
        """)
        btn_guardar.clicked.connect(lambda: self.guardar_nota(manual=True))

        fila_pie.addWidget(btn_eliminar)
        fila_pie.addWidget(btn_guardar)
        layout.addLayout(fila_pie)

        return panel

    def _actualizar_estilo_boton_fijar(self):
        if self.btn_fijar.isChecked():
            self.btn_fijar.setText("★  Fijada")
            color, borde = DORADO, DORADO
            fondo = DORADO_SUAVE
        else:
            self.btn_fijar.setText("☆  Fijar")
            color, borde = TEXTO_SECUNDARIO, BORDE
            fondo = "transparent"
        self.btn_fijar.setStyleSheet(f"""
            QPushButton {{
                background-color: {fondo};
                color: {color};
                border: 1px solid {borde};
                border-radius: 12px;
                padding: 0 10px;
                font-family: {FUENTE_UI};
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{ border-color: {DORADO}; color: {DORADO}; }}
        """)

    # ─────────────────────────────────────────────
    # HERRAMIENTAS DE FORMATO (markdown ligero, no destructivo)
    # ─────────────────────────────────────────────
    def _envolver_seleccion(self, marcador):
        cursor = self.txt_contenido.textCursor()
        if cursor.hasSelection():
            texto = cursor.selectedText()
            cursor.insertText(f"{marcador}{texto}{marcador}")
        else:
            cursor.insertText(f"{marcador}{marcador}")
            cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.MoveAnchor, len(marcador))
            self.txt_contenido.setTextCursor(cursor)
        self.txt_contenido.setFocus()

    def _insertar_lista(self):
        cursor = self.txt_contenido.textCursor()
        if cursor.hasSelection():
            texto = cursor.selectedText().replace("\u2029", "\n")
            lineas = texto.split("\n")
            nuevo = "\n".join(f"- {linea}" if linea.strip() else linea for linea in lineas)
            cursor.insertText(nuevo)
        else:
            cursor.insertText("- ")
        self.txt_contenido.setFocus()

    def _insertar_cita(self):
        cursor = self.txt_contenido.textCursor()
        cursor.insertText("> ")
        self.txt_contenido.setFocus()

    # ─────────────────────────────────────────────
    # LISTA DE NOTAS
    # ─────────────────────────────────────────────
    def cargar_lista_notas(self):
        metadatos = self.logica.obtener_lista_notas()
        self._pintar_lista(metadatos)

    def _pintar_lista(self, metadatos):
        self.lista_widget.clear()
        for meta in metadatos:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, meta["titulo"])
            tarjeta = TarjetaNota(meta["titulo"], meta["vista_previa"], meta["fecha"], meta["fijada"])
            item.setSizeHint(tarjeta.sizeHint())
            self.lista_widget.addItem(item)
            self.lista_widget.setItemWidget(item, tarjeta)
            if self.nota_actual and meta["titulo"] == self.nota_actual:
                item.setSelected(True)

        total = len(metadatos)
        self.lbl_contador_notas.setText(f"{total} nota{'s' if total != 1 else ''}" if total else "vacío")

        if not metadatos:
            self._mostrar_lista_vacia()

    def _mostrar_lista_vacia(self):
        item = QListWidgetItem()
        placeholder = QLabel("Tu cuaderno está vacío.\nPulsa “＋ Nueva nota” para empezar.")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setWordWrap(True)
        placeholder.setStyleSheet(f"""
            color: {TEXTO_TERCIARIO}; font-family: {FUENTE_UI}; font-size: 11px;
            padding: 24px 10px; border: none; background: transparent;
        """)
        item.setFlags(Qt.NoItemFlags)
        item.setSizeHint(placeholder.sizeHint())
        self.lista_widget.addItem(item)
        self.lista_widget.setItemWidget(item, placeholder)

    def seleccionar_nota(self, item):
        titulo = item.data(Qt.UserRole)
        if not titulo:
            return
        self._cargar_en_editor(titulo)

    def _cargar_en_editor(self, titulo):
        datos = self.logica.cargar_nota(titulo)
        self.nota_actual = titulo

        self._suprimir_autoguardado = True
        self.txt_titulo.setText(datos.get("titulo", ""))
        self.txt_contenido.setPlainText(datos.get("contenido", ""))
        self._suprimir_autoguardado = False

        self.btn_fijar.setChecked(bool(datos.get("fijada", False)))
        self._actualizar_estilo_boton_fijar()

        fecha = datos.get("ultima_modificacion", "")
        self.lbl_fecha_nota.setText(f"Editado: {fecha}" if fecha else "Nota nueva")
        self._actualizar_contador_palabras()
        self._mostrar_estado_guardado("", instantaneo=True)

    def nueva_nota(self):
        self.nota_actual = None
        self.lista_widget.clearSelection()

        self._suprimir_autoguardado = True
        self.txt_titulo.clear()
        self.txt_contenido.clear()
        self._suprimir_autoguardado = False

        self.btn_fijar.setChecked(False)
        self._actualizar_estilo_boton_fijar()
        self.lbl_fecha_nota.setText("Nota nueva")
        self._actualizar_contador_palabras()
        self._mostrar_estado_guardado("", instantaneo=True)
        self.txt_titulo.setFocus()

    def filtrar_notas(self, texto):
        resultados = self.logica.buscar_notas(texto)
        self._pintar_lista(resultados)

    # ─────────────────────────────────────────────
    # GUARDADO / AUTOGUARDADO
    # ─────────────────────────────────────────────
    def _on_texto_modificado(self):
        if self._suprimir_autoguardado:
            return
        self._actualizar_contador_palabras()
        self._mostrar_estado_guardado("Escribiendo…", instantaneo=True)
        self.timer_autoguardado.start(900)

    def _autoguardar(self):
        self.guardar_nota(manual=False)

    def guardar_nota(self, manual=False):
        titulo = self.txt_titulo.text().strip()
        contenido = self.txt_contenido.toPlainText()

        if not titulo and not contenido:
            if manual:
                self._mostrar_estado_guardado("Nada que guardar", instantaneo=True)
            return

        guardado = self.logica.guardar_nota(
            titulo, contenido,
            titulo_anterior=self.nota_actual,
            fijada=self.btn_fijar.isChecked(),
        )
        self.nota_actual = guardado

        if self.txt_titulo.text().strip() != guardado:
            self._suprimir_autoguardado = True
            self.txt_titulo.setText(guardado)
            self._suprimir_autoguardado = False

        from datetime import datetime as _dt
        self.lbl_fecha_nota.setText(f"Editado: {_dt.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Refresca la lista preservando la búsqueda activa y la selección
        if self.txt_buscar.text():
            self.filtrar_notas(self.txt_buscar.text())
        else:
            self.cargar_lista_notas()

        self._mostrar_estado_guardado("Guardado ✓" if manual else "Guardado automáticamente")

    def alternar_fijar_nota(self):
        self._actualizar_estilo_boton_fijar()
        # Si la nota ya existe en disco, persistimos el cambio al instante;
        # si es nueva y aún no tiene contenido, se guardará cuando el usuario escriba.
        if self.nota_actual:
            self.guardar_nota(manual=False)

    def eliminar_nota(self):
        if not self.nota_actual:
            self._mostrar_estado_guardado("No hay nota que eliminar", instantaneo=True)
            return

        respuesta = self._confirmar(
            "Eliminar nota",
            f"«{self.nota_actual}» se moverá a la papelera.\nPodrás recuperarla durante 30 días."
        )
        if not respuesta:
            return

        self.logica.eliminar_nota(self.nota_actual)
        self.nueva_nota()
        if self.txt_buscar.text():
            self.filtrar_notas(self.txt_buscar.text())
        else:
            self.cargar_lista_notas()
        self._mostrar_estado_guardado("Movida a la papelera 🗑", instantaneo=True)

    def abrir_papelera(self):
        dialogo = DialogoPapelera(self, self.logica)
        dialogo.exec_()

    def _confirmar(self, titulo, mensaje):
        caja = QMessageBox(self)
        caja.setWindowTitle(titulo)
        caja.setText(mensaje)
        caja.setIcon(QMessageBox.NoIcon)
        btn_si = caja.addButton("Mover a papelera", QMessageBox.DestructiveRole)
        caja.addButton("Cancelar", QMessageBox.RejectRole)
        caja.setStyleSheet(f"""
            QMessageBox {{ background-color: {BG_PANEL}; }}
            QLabel {{ color: {TEXTO_PRINCIPAL}; font-family: {FUENTE_UI}; font-size: 12px; }}
            QPushButton {{
                background-color: {BG_INPUT}; color: {TEXTO_PRINCIPAL};
                border: 1px solid {BORDE}; border-radius: 6px; padding: 6px 14px;
                font-family: {FUENTE_UI}; font-size: 12px;
            }}
            QPushButton:hover {{ border-color: {PELIGRO}; color: {PELIGRO}; }}
        """)
        caja.exec_()
        return caja.clickedButton() == btn_si

    # ─────────────────────────────────────────────
    # UTILIDADES DE ESTADO
    # ─────────────────────────────────────────────
    def _actualizar_contador_palabras(self):
        texto = self.txt_contenido.toPlainText().strip()
        palabras = len(texto.split()) if texto else 0
        caracteres = len(texto)
        self.lbl_contador_palabras.setText(f"{palabras} palabra{'s' if palabras != 1 else ''} · {caracteres} caracteres")

    def _mostrar_estado_guardado(self, texto, instantaneo=False):
        self.lbl_estado_guardado.setText(texto)
        if not texto:
            self._efecto_estado.setOpacity(0.0)
            return

        self._efecto_estado.setOpacity(1.0)
        if not instantaneo:
            self._anim_estado = QPropertyAnimation(self._efecto_estado, b"opacity")
            self._anim_estado.setDuration(1600)
            self._anim_estado.setStartValue(1.0)
            self._anim_estado.setEndValue(0.0)
            self._anim_estado.setEasingCurve(QEasingCurve.InCubic)
            QTimer.singleShot(1200, self._anim_estado.start)

    # ─────────────────────────────────────────────
    # CIERRE: asegurar que no se pierde nada sin guardar
    # ─────────────────────────────────────────────
    def closeEvent(self, event):
        if self.timer_autoguardado.isActive() or self.txt_titulo.text().strip() or self.txt_contenido.toPlainText().strip():
            self.guardar_nota(manual=False)
        super().closeEvent(event)