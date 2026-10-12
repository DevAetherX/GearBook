import sys
from PyQt5.QtCore import Qt, QSize, QPoint, QTimer, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QStackedWidget,
    QSizeGrip,
    QMenu,
)

# ═══════════════════════════════════════════════════════════════════
# CATÁLOGO DE ACCIONES
# (icono, título, descripción, tipo, valor)
#   tipo "metodo"       → llama a ventana.<valor>()
#   tipo "metodo_chat"  → llama a ventana.<valor>() y salta al chat
#   tipo "prefill"      → salta al chat y escribe el texto (sin enviar)
#   tipo "comando"      → salta al chat y envía el texto directamente
# ═══════════════════════════════════════════════════════════════════
ACCIONES = [
    ("Productividad", [
        ("📝", "Notas", "Crea y consulta tus notas rápidas.", "metodo", "abrir_gestor_notas"),
        ("📁", "Explorador", "Audita y navega tus carpetas.", "metodo", "abrir_explorador_independiente"),
        ("💰", "Finanzas", "Controla tus ingresos y gastos.", "metodo", "abrir_gestor_finanzas"),
        ("🗂️", "Ordenar", "Organiza una carpeta por tipo de archivo.", "prefill", "ordenar/ "),
        ("🔍", "Buscar local", "Busca archivos y carpetas. Con o sin término.", "prefill", "buscar/ ","Escribe  buscar/  y pulsa Enter para abrir el buscador vacío.\n" "O escribe  buscar/ término  (ej: buscar/ De la Vida Como Pelicula, Tragedia, Comedia y Ficcion ) para abrirlo ya con la búsqueda hecha."),
    ]),
    ("Multimedia", [
        ("🎵", "Música", "Reproduce tu música por canción, artista, género o idioma.", "prefill", "music/ ",
         "Escribe  music/  y pulsa Enter para reproducir TODA tu bóveda en modo aleatorio.\n"
         "O escribe  music/ nombre  y María detecta qué es:\n"
         "• Canción  →  music/ Lose Yourself  (suena esa canción y sigue con el resto de su carpeta)\n"
         "• Artista  →  music/ Eminem  (todas sus canciones)\n"
         "• Género  →  music/ Rap  (todos los artistas y canciones de ese género)\n"
         "• Idioma  →  music/ Español  (todos los géneros, artistas y canciones de ese idioma)\n"
         "Las carpetas se reproducen mezcladas. No importan mayúsculas, tildes ni guiones."),
        ("⬇️", "Descargar", "Baja vídeo o audio desde una URL.", "prefill", "descargar/ "),
        ("⏸️", "Pausar", "Pausa la reproducción actual.", "comando", "pausar"),
        ("▶️", "Reanudar", "Reanuda la reproducción pausada.", "comando", "reanudar"),
    ]),
    ("Web y mensajería", [
        ("🔎", "Buscar", "Busca en internet por ti.", "prefill", "busca en internet/ "),
        ("📺", "YouTube", "Abre YouTube en tu navegador.", "comando", "youtube"),
        ("💬", "WhatsApp", "Abre WhatsApp.", "comando", "whatsapp"),
        ("✈️", "Telegram", "Abre Telegram.", "comando", "telegram"),
    ]),
    ("Sistema", [
        ("📖", "Manual", "Consulta todos los comandos disponibles.", "metodo", "mostrar_manual_desde_menu"),
        ("🔇", "Silenciar", "Activa o desactiva la voz de María.", "metodo_chat", "_toggle_mute"),
        ("🧹", "Vaciar chat", "Borra la conversación actual.", "metodo_chat", "vaciar_chat"),
    ]),
]

# Atajos fijos de la barra lateral (se mantienen los iconos originales)
ATAJOS = [
    ("📝", "Notas", "abrir_gestor_notas"),
    ("📁", "Explorador", "abrir_explorador_independiente"),
    ("💰", "Finanzas", "abrir_gestor_finanzas"),
]

CARD_W, CARD_H, CARD_GAP = 176, 150, 14
PAD_ACCIONES = 28

# ═══════════════════════════════════════════════════════════════════
# ESTILO — paleta cálida (grafito + terracota)
# BG_APP #242730 | BG_PANEL #2b2e38 | BG_INPUT #1d2028 | BG_INPUT_HOVER #20232c
# BORDE #3c3f4a | BORDE_SUAVE #33363f | TEXTO_PRINCIPAL #ded8ca
# TEXTO_SECUNDARIO #8f8b83 | TEXTO_TERCIARIO #6b6860 | ACENTO #c17a56
# ACENTO_HOVER #d38f6c | ACENTO_SUAVE rgba(193,122,86,0.16) | PELIGRO #a15c52
# DORADO #c9a24b
# ═══════════════════════════════════════════════════════════════════
QSS_STYLE = """
QWidget#InterfazPrincipal { background-color: #242730; }

/* ---------- Menús contextuales ---------- */
QMenu {
    background-color: #2b2e38 !important;
    border: 1px solid #3c3f4a !important;
    border-radius: 8px;
    padding: 6px;
}
QMenu::item {
    background-color: transparent;
    color: #ded8ca;
    padding: 6px 20px 6px 10px;
    border-radius: 4px;
    font-size: 13px;
}
QMenu::item:selected { background-color: rgba(193, 122, 86, 0.16) !important; color: #ded8ca !important; }
QMenu::item:disabled { color: #6b6860; }
QMenu::separator { height: 1px; background-color: #33363f; margin: 4px 0px; }

QToolTip {
    background-color: #2b2e38;
    color: #ded8ca;
    border: 1px solid #3c3f4a;
    padding: 4px 8px;
}

/* ---------- Scrollbars ---------- */
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollBar:vertical { border: none; background: transparent; width: 6px; margin: 0; }
QScrollBar::handle:vertical { background: #3c3f4a; border-radius: 3px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #4a4e5b; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background: none; height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

/* ---------- Barra de título ---------- */
QFrame#title_bar { background-color: #242730; border-bottom: 1px solid #33363f; }
QLabel#app_title { color: #8f8b83; font-size: 13px; font-weight: 500; }
QPushButton#win_btn, QPushButton#close_btn {
    background-color: transparent; color: #8f8b83; border: none; font-size: 12px; border-radius: 4px;
}
QPushButton#win_btn:hover { background-color: #2b2e38; color: #ded8ca; }
QPushButton#close_btn:hover { background-color: #a15c52; color: #ded8ca; }

/* ---------- Sidebar ---------- */
QFrame#sidebar { background-color: #2b2e38; border-right: 1px solid #33363f; }
QLabel#section_label {
    color: #6b6860; font-size: 10px; font-weight: 700; letter-spacing: 1px; padding: 6px 8px 2px 8px;
}
QLabel#sidebar_footer { color: #6b6860; font-size: 10px; padding: 4px 8px; }
QListWidget#nav_list, QListWidget#atajos_list {
    background-color: transparent; border: none; color: #8f8b83; font-size: 13px; outline: 0;
}
QListWidget#nav_list::item, QListWidget#atajos_list::item {
    padding: 10px 14px; border-radius: 8px; margin-bottom: 3px; border-left: 3px solid transparent;
}
QListWidget#nav_list::item:hover, QListWidget#atajos_list::item:hover {
    background-color: #20232c; color: #ded8ca;
}
QListWidget#nav_list::item:selected {
    background-color: rgba(193, 122, 86, 0.16); color: #ded8ca;
    border-left: 3px solid #c17a56; font-weight: 600;
}

/* ---------- Cabeceras de página ---------- */
QLabel#page_title { color: #ded8ca; font-size: 20px; font-weight: 700; }
QLabel#page_subtitle { color: #8f8b83; font-size: 12px; }

/* ---------- Chat ---------- */
QFrame#chat_container { background-color: #242730; }
QFrame#input_container { background-color: #1d2028; border: 1px solid #3c3f4a; border-radius: 20px; }
QFrame#input_container:focus-within { border: 1px solid #c17a56; }
QLineEdit#input_field {
    background: transparent; border: none; color: #ded8ca; font-size: 14px; padding: 6px 10px;
    selection-background-color: rgba(193, 122, 86, 0.35); selection-color: #ded8ca;
}
QPushButton#send_button {
    background-color: #c17a56; color: #242730; border: none; border-radius: 18px; font-weight: 700; font-size: 15px;
}
QPushButton#send_button:hover { background-color: #d38f6c; }
QPushButton#icon_button { background-color: transparent; color: #8f8b83; border: none; border-radius: 6px; }
QPushButton#icon_button:hover { background-color: #33363f; color: #ded8ca; }

/* ---------- Acciones ---------- */
QLineEdit#search_field {
    background-color: #1d2028; border: 1px solid #3c3f4a; border-radius: 10px;
    color: #ded8ca; font-size: 13px; padding: 8px 12px; max-width: 360px;
    selection-background-color: rgba(193, 122, 86, 0.35);
}
QLineEdit#search_field:focus { border: 1px solid #c17a56; background-color: #20232c; }
QLabel#section_title { color: #8f8b83; font-size: 11px; font-weight: 700; letter-spacing: 1px; padding-top: 10px; }
QLabel#empty_label { color: #6b6860; font-size: 13px; padding: 24px 0; }

QFrame#action_card { background-color: #2b2e38; border: 1px solid #33363f; border-radius: 12px; }
QFrame#action_card:hover { background-color: #2f323d; border: 1px solid #c17a56; }
QLabel#card_icon { background-color: rgba(193, 122, 86, 0.16); border-radius: 12px; font-size: 26px; }
QLabel#card_title { color: #ded8ca; font-size: 13px; font-weight: 600; }
QLabel#card_desc { color: #8f8b83; font-size: 11px; }
QLabel#card_info { color: #c17a56; font-size: 14px; background: transparent; }


/* ---------- Barra de estado ---------- */
QFrame#status_bar { background-color: #1d2028; border-top: 1px solid #33363f; }
QLabel#status_dot { color: #c9a24b; font-size: 10px; }
QLabel#status_text { color: #c9a24b; font-size: 10px; font-weight: 700; letter-spacing: 1px; }
QLabel#status_msg, QLabel#status_info { color: #6b6860; font-size: 10px; }
"""


class TarjetaAccion(QFrame):
    """Tarjeta cuadrada: icono arriba, título y descripción breve debajo."""
    clicked = pyqtSignal()

    def __init__(self, icono, titulo, descripcion, parent=None, ayuda=None):
        super().__init__(parent)
        self.setObjectName("action_card")
        self.setFixedSize(CARD_W, CARD_H)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(ayuda or descripcion)
        self._texto_busqueda = f"{titulo} {descripcion} {ayuda or ''}".lower()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 12)
        lay.setSpacing(6)

        lbl_icono = QLabel(icono)
        lbl_icono.setObjectName("card_icon")
        lbl_icono.setFixedSize(52, 52)
        lbl_icono.setAlignment(Qt.AlignCenter)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setObjectName("card_title")

        lbl_desc = QLabel(descripcion)
        lbl_desc.setObjectName("card_desc")
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        lay.addWidget(lbl_icono)
        lay.addWidget(lbl_titulo)
        lay.addWidget(lbl_desc, 1)

        # Que el clic siempre llegue a la tarjeta (y el :hover se mantenga)
        for w in (lbl_icono, lbl_titulo, lbl_desc):
            w.setAttribute(Qt.WA_TransparentForMouseEvents)
         # ⓘ solo en las tarjetas que tienen texto de ayuda
        if ayuda:
            lbl_info = QLabel("ⓘ", self)
            lbl_info.setObjectName("card_info")
            lbl_info.setAttribute(Qt.WA_TransparentForMouseEvents)
            lbl_info.adjustSize()
            lbl_info.move(CARD_W - lbl_info.width() - 10, 10)
            lbl_info.raise_()

    def coincide(self, texto):
        return texto in self._texto_busqueda

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.pos()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class InterfazPrincipal(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("InterfazPrincipal")

        # Estilo a nivel de aplicación (así los menús contextuales también lo heredan)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(QSS_STYLE)
        else:
            self.setStyleSheet(QSS_STYLE)

        self.resize(1050, 720)
        self.setMinimumSize(850, 580)

        self.drag_position = QPoint()
        self._secciones = []
        self.setup_ui()

        if parent is not None:
            parent.resize(1050, 720)
            parent.setMinimumSize(850, 580)
            self._exponer_widgets_al_parent(parent)

    # ═══════════════════════════════════════════
    # CONSTRUCCIÓN
    # ═══════════════════════════════════════════
    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._crear_title_bar())

        body = QWidget()
        body_l = QHBoxLayout(body)
        body_l.setContentsMargins(0, 0, 0, 0)
        body_l.setSpacing(0)

        self.sidebar_frame = self._crear_sidebar()
        body_l.addWidget(self.sidebar_frame)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._crear_pagina_chat())      # 0
        self.stack.addWidget(self._crear_pagina_acciones())  # 1
        body_l.addWidget(self.stack, 1)

        root.addWidget(body, 1)
        root.addWidget(self._crear_status_bar())

        self.nav_list.currentRowChanged.connect(self._cambiar_pagina)
        self._crear_elementos_compatibilidad()

    # ---------- Barra de título ----------
    def _crear_title_bar(self):
        self.title_bar = QFrame()
        self.title_bar.setObjectName("title_bar")
        self.title_bar.setFixedHeight(40)
        self.title_bar.mousePressEvent = self.title_bar_mousePressEvent
        self.title_bar.mouseMoveEvent = self.title_bar_mouseMoveEvent
        self.title_bar.mouseDoubleClickEvent = self.title_bar_mouseDoubleClickEvent

        lay = QHBoxLayout(self.title_bar)
        lay.setContentsMargins(10, 0, 8, 0)
        lay.setSpacing(8)

        self.toggle_button = QPushButton("☰")
        self.toggle_button.setObjectName("icon_button")
        self.toggle_button.setFixedSize(QSize(30, 30))
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        lay.addWidget(self.toggle_button)

        app_title = QLabel("✦ GearBook")
        app_title.setObjectName("app_title")
        lay.addWidget(app_title)
        lay.addStretch()

        self.btn_minimize = QPushButton("—")
        self.btn_minimize.setObjectName("win_btn")
        self.btn_maximize = QPushButton("▢")
        self.btn_maximize.setObjectName("win_btn")
        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("close_btn")
        for b in (self.btn_minimize, self.btn_maximize, self.btn_close):
            b.setFixedSize(30, 30)
            b.setCursor(Qt.PointingHandCursor)
            lay.addWidget(b)

        # El botón cerrar no estaba conectado: closeEvent de María lo oculta a la bandeja
        self.btn_close.clicked.connect(lambda: self.window().close())
        return self.title_bar

    # ---------- Sidebar ----------
    def _crear_sidebar(self):
        frame = QFrame()
        frame.setObjectName("sidebar")
        frame.setFixedWidth(220)

        lay = QVBoxLayout(frame)
        lay.setContentsMargins(10, 14, 10, 10)
        lay.setSpacing(2)

        lay.addWidget(self._crear_label_seccion("ESPACIO"))

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("nav_list")
        self.nav_list.setFocusPolicy(Qt.NoFocus)
        self.nav_list.addItem("🤖   Chat")
        self.nav_list.addItem("⚡   Acciones")
        self.nav_list.setCurrentRow(0)
        self.nav_list.setFixedHeight(2 * 46 + 4)
        lay.addWidget(self.nav_list)

        lay.addSpacing(10)
        lay.addWidget(self._crear_label_seccion("ATAJOS"))

        self.atajos_list = QListWidget()
        self.atajos_list.setObjectName("atajos_list")
        self.atajos_list.setFocusPolicy(Qt.NoFocus)
        self.atajos_list.setSelectionMode(QListWidget.NoSelection)
        for icono, texto, metodo in ATAJOS:
            item = QListWidgetItem(f"{icono}   {texto}")
            item.setData(Qt.UserRole, metodo)
            self.atajos_list.addItem(item)
        self.atajos_list.setFixedHeight(len(ATAJOS) * 46 + 4)
        self.atajos_list.itemClicked.connect(
            lambda it: self._ejecutar_accion("metodo", it.data(Qt.UserRole))
        )
        lay.addWidget(self.atajos_list)

        lay.addStretch()
        footer = QLabel("Alt + Q  ·  mostrar / ocultar")
        footer.setObjectName("sidebar_footer")
        lay.addWidget(footer)
        return frame

    def _crear_label_seccion(self, texto):
        lbl = QLabel(texto)
        lbl.setObjectName("section_label")
        return lbl

    # ---------- Cabecera de página ----------
    def _crear_header(self, titulo, subtitulo):
        frame = QFrame()
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(PAD_ACCIONES, 20, PAD_ACCIONES, 12)
        lay.setSpacing(2)
        lbl_t = QLabel(titulo)
        lbl_t.setObjectName("page_title")
        lbl_s = QLabel(subtitulo)
        lbl_s.setObjectName("page_subtitle")
        lay.addWidget(lbl_t)
        lay.addWidget(lbl_s)
        return frame, lbl_s

    # ---------- Página: CHAT ----------
    def _crear_pagina_chat(self):
        pagina = QFrame()
        pagina.setObjectName("chat_container")
        lay = QVBoxLayout(pagina)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        header, self.lbl_subtitulo = self._crear_header("Chat", "Conversa con María o escribe '/' para ver comandos")
        lay.addWidget(header)

        cuerpo = QVBoxLayout()
        cuerpo.setContentsMargins(PAD_ACCIONES, 0, PAD_ACCIONES, 18)
        cuerpo.setSpacing(12)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_layout.setSpacing(14)
        self.chat_layout.addStretch()
        self.scroll.setWidget(self.chat_container)
        cuerpo.addWidget(self.scroll, 1)

        self.lbl_typing = QLabel("Escribiendo respuesta...")
        self.lbl_typing.setStyleSheet("color: #8f8b83; font-size: 11px; padding: 0 8px;")
        self.lbl_typing.setFixedHeight(18)
        self.lbl_typing.hide()
        cuerpo.addWidget(self.lbl_typing)

        input_frame = QFrame()
        input_frame.setObjectName("input_container")
        input_l = QHBoxLayout(input_frame)
        input_l.setContentsMargins(12, 8, 10, 8)

        self.btn_mic = QPushButton("🎙️")
        self.btn_mic.setObjectName("icon_button")
        self.btn_mic.setFixedSize(QSize(32, 32))
        self.btn_mic.setCursor(Qt.PointingHandCursor)

        self.input_field = QLineEdit()
        self.input_field.setObjectName("input_field")
        self.input_field.setPlaceholderText("Escribe un mensaje o presiona el micro...")
        self.input_field.returnPressed.connect(self._emitir_enviar)
        self.input_field.setContextMenuPolicy(Qt.CustomContextMenu)
        self.input_field.customContextMenuRequested.connect(self._mostrar_menu_custom_input)

        self.btn_send = QPushButton("↑")
        self.btn_send.setObjectName("send_button")
        self.btn_send.setFixedSize(QSize(36, 36))
        self.btn_send.setCursor(Qt.PointingHandCursor)
        self.btn_send.setToolTip("Enviar mensaje (Enter)")

        input_l.addWidget(self.btn_mic)
        input_l.addWidget(self.input_field, 1)
        input_l.addWidget(self.btn_send)
        cuerpo.addWidget(input_frame)

        lay.addLayout(cuerpo, 1)
        return pagina

    # ---------- Página: ACCIONES ----------
    def _crear_pagina_acciones(self):
        pagina = QFrame()
        pagina.setObjectName("chat_container")
        lay = QVBoxLayout(pagina)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        header, _ = self._crear_header(
            "Acciones",
            "Todo lo que María puede hacer, a un clic  ·  Deja el cursor unos segundos sobre una tarjeta para ver cómo usarla"
            )
        lay.addWidget(header)

        fila_busqueda = QHBoxLayout()
        fila_busqueda.setContentsMargins(PAD_ACCIONES, 0, PAD_ACCIONES, 4)
        self.search_acciones = QLineEdit()
        self.search_acciones.setObjectName("search_field")
        self.search_acciones.setPlaceholderText("🔍  Filtrar acciones...")
        self.search_acciones.setClearButtonEnabled(True)
        self.search_acciones.textChanged.connect(self._filtrar_acciones)
        fila_busqueda.addWidget(self.search_acciones)
        fila_busqueda.addStretch()
        lay.addLayout(fila_busqueda)

        self.acciones_scroll = QScrollArea()
        self.acciones_scroll.setWidgetResizable(True)
        self.acciones_scroll.setFrameShape(QFrame.NoFrame)
        self.acciones_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        inner = QWidget()
        inner_l = QVBoxLayout(inner)
        inner_l.setContentsMargins(PAD_ACCIONES, 0, PAD_ACCIONES, 24)
        inner_l.setSpacing(10)

        for nombre_seccion, items in ACCIONES:
            lbl = QLabel(nombre_seccion.upper())
            lbl.setObjectName("section_title")
            inner_l.addWidget(lbl)

            cont = QWidget()
            grid = QGridLayout(cont)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setSpacing(CARD_GAP)

            tarjetas = []
            for icono, titulo, desc, tipo, valor, *extra in items:
                ayuda = extra[0] if extra else None
                t = TarjetaAccion(icono, titulo, desc, cont, ayuda=ayuda)
                t.clicked.connect(lambda tp=tipo, v=valor: self._ejecutar_accion(tp, v))
                tarjetas.append(t)
            inner_l.addWidget(cont, 0, Qt.AlignLeft)
            self._secciones.append((lbl, cont, grid, tarjetas))

        self.lbl_sin_resultados = QLabel("Ninguna acción coincide con tu búsqueda.")
        self.lbl_sin_resultados.setObjectName("empty_label")
        self.lbl_sin_resultados.hide()
        inner_l.addWidget(self.lbl_sin_resultados)
        inner_l.addStretch()

        self.acciones_scroll.setWidget(inner)
        lay.addWidget(self.acciones_scroll, 1)

        self._reflow_acciones()
        return pagina
    

    # ---------- Barra de estado ----------
    def _crear_status_bar(self):
        bar = QFrame()
        bar.setObjectName("status_bar")
        bar.setFixedHeight(28)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 0, 2, 0)
        lay.setSpacing(8)

        self.lbl_status_dot = QLabel("●")
        self.lbl_status_dot.setObjectName("status_dot")
        self.lbl_status_text = QLabel("ONLINE")
        self.lbl_status_text.setObjectName("status_text")
        self.lbl_status_bar = QLabel("Sistema listo — esperando entrada del Administrador")
        self.lbl_status_bar.setObjectName("status_msg")

        self.lbl_mensajes = QLabel("MSG_COUNT: 0")
        self.lbl_mensajes.setObjectName("status_info")
        self.lbl_fecha = QLabel("")
        self.lbl_fecha.setObjectName("status_info")
        self.lbl_reloj = QLabel("")
        self.lbl_reloj.setObjectName("status_info")

        lay.addWidget(self.lbl_status_dot)
        lay.addWidget(self.lbl_status_text)
        lay.addWidget(self.lbl_status_bar)
        lay.addStretch()
        lay.addWidget(self.lbl_mensajes)
        lay.addWidget(self.lbl_fecha)
        lay.addWidget(self.lbl_reloj)
        lay.addWidget(QSizeGrip(bar), 0, Qt.AlignBottom | Qt.AlignRight)  # ventana sin marco → redimensionar
        return bar

    # ═══════════════════════════════════════════
    # LÓGICA DE LA INTERFAZ
    # ═══════════════════════════════════════════
    def ir_a_chat(self):
        self.nav_list.setCurrentRow(0)

    def _cambiar_pagina(self, indice):
        if indice < 0:
            return
        self.stack.setCurrentIndex(indice)
        if indice == 1:
            QTimer.singleShot(0, self._reflow_acciones)
        else:
            self.input_field.setFocus()

    def _ejecutar_accion(self, tipo, valor):
        ventana = self.window()
        if tipo in ("metodo", "metodo_chat"):
            fn = getattr(ventana, valor, None)
            if callable(fn):
                fn()
            if tipo == "metodo_chat":
                self.ir_a_chat()
        elif tipo == "prefill":
            self.ir_a_chat()
            self.input_field.setText(valor)
            self.input_field.setFocus()
            self.input_field.setCursorPosition(len(valor))
        elif tipo == "comando":
            self.ir_a_chat()
            self.input_field.setText(valor)
            self._emitir_enviar()

    def _filtrar_acciones(self, texto):
        texto = texto.strip().lower()
        for _, _, _, tarjetas in self._secciones:
            for t in tarjetas:
                t.setVisible(t.coincide(texto))
        self._reflow_acciones()

    def _reflow_acciones(self):
        """Recoloca las tarjetas según el ancho disponible (rejilla responsive)."""
        if not self._secciones:
            return
        ancho = self.acciones_scroll.viewport().width() - 2 * PAD_ACCIONES
        cols = max(1, (ancho + CARD_GAP) // (CARD_W + CARD_GAP))
        hay_resultados = False
        for lbl, cont, grid, tarjetas in self._secciones:
            for t in tarjetas:
                grid.removeWidget(t)
            visibles = [t for t in tarjetas if not t.isHidden()]
            for i, t in enumerate(visibles):
                grid.addWidget(t, i // cols, i % cols)
            if visibles:
                filas = (len(visibles) + cols - 1) // cols
                columnas = min(cols, len(visibles))
                cont.setFixedSize(columnas * CARD_W + (columnas - 1) * CARD_GAP,
                                  filas * CARD_H + (filas - 1) * CARD_GAP)
            lbl.setVisible(bool(visibles))
            cont.setVisible(bool(visibles))
            hay_resultados = hay_resultados or bool(visibles)
        self.lbl_sin_resultados.setVisible(not hay_resultados)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.stack.currentIndex() == 1:
            QTimer.singleShot(0, self._reflow_acciones)

    def _emitir_enviar(self):
        """Llama al método enviar() de la ventana principal"""
        parent = self.window()
        if hasattr(parent, 'enviar'):
            parent.enviar()

    def _mostrar_menu_custom_input(self, pos):
        """Menú contextual del input garantizando el tema oscuro"""
        menu = self.input_field.createStandardContextMenu()
        menu.setStyleSheet("""
            QMenu { background-color: #2b2e38; color: #ded8ca; border: 1px solid #3c3f4a;
                    font-family: 'Segoe UI', sans-serif; font-size: 12px; padding: 6px; border-radius: 8px; }
            QMenu::item { padding: 6px 28px 6px 14px; }
            QMenu::item:selected { background-color: rgba(193, 122, 86, 0.16); color: #ded8ca; border-radius: 4px; }
        """)
        menu.exec_(self.input_field.mapToGlobal(pos))

    def toggle_sidebar(self):
        self.sidebar_frame.setVisible(not self.sidebar_frame.isVisible())
        if self.stack.currentIndex() == 1:
            QTimer.singleShot(0, self._reflow_acciones)

    # ---------- Arrastre de ventana ----------
    def title_bar_mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            parent = self.window()
            self.drag_position = event.globalPos() - parent.frameGeometry().topLeft()
            event.accept()

    def title_bar_mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            parent = self.window()
            if getattr(parent, "es_pantalla_completa", False):
                return
            parent.move(event.globalPos() - self.drag_position)
            event.accept()

    def title_bar_mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            parent = self.window()
            if hasattr(parent, "toggle_fullscreen"):
                parent.toggle_fullscreen()
            event.accept()

    # ═══════════════════════════════════════════
    # COMPATIBILIDAD CON main.py
    # ═══════════════════════════════════════════
    def _crear_elementos_compatibilidad(self):
        """Crea los widgets 'fantasma' que main.py espera pero que ya no se muestran."""
        for nombre in ("btn_exportar", "btn_buscar", "btn_ajustes_header", "btn_panel",
                       "btn_adjuntar", "btn_scroll_bottom", "btn_limpiar"):
            if not hasattr(self, nombre):
                setattr(self, nombre, QPushButton())
        for nombre in ("lbl_avatar", "lbl_node", "lbl_contador", "lbl_latencia"):
            if not hasattr(self, nombre):
                setattr(self, nombre, QLabel())
        for nombre in ("welcome_widget", "info_bar", "barra_acciones"):
            if not hasattr(self, nombre):
                setattr(self, nombre, QWidget())

    def _exponer_widgets_al_parent(self, parent):
        atributos = [
            "input_field", "btn_mic", "btn_send", "btn_panel",
            "chat_layout", "chat_container", "scroll", "lbl_status_bar",
            "lbl_status_dot", "lbl_status_text", "lbl_reloj", "lbl_mensajes",
            "lbl_fecha", "lbl_node", "info_bar", "btn_maximize", "btn_minimize",
            "lbl_avatar", "lbl_subtitulo", "btn_ajustes_header", "btn_close",
            "barra_acciones", "btn_limpiar", "btn_exportar", "btn_buscar",
            "welcome_widget", "btn_scroll_bottom", "lbl_typing",
            "btn_adjuntar", "lbl_contador", "lbl_latencia",
        ]
        for nombre in atributos:
            if hasattr(self, nombre):
                setattr(parent, nombre, getattr(self, nombre))