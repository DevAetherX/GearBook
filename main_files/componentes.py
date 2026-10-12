from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QScrollArea, QListWidget, QListWidgetItem, QPushButton, QApplication,
                             QProgressBar, QLineEdit, QTextEdit)
from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath
import math


class CableConector(QWidget):
    """Línea o 'cable' sutil que une visualmente la barra de acciones con el panel desplegado."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Permitimos eventos del ratón para poder arrastrar el cable
        self.setMouseTracking(True)
        self.dragging = False
        self._drag_offset = QPoint()

        # Apariencia por defecto
        self.pen_color = QColor("#3c3f4a")
        self.pen_width = 2

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Estilo del cable: Gris mate sobrio y curvo (flácido)
        pen = QPen(self.pen_color, self.pen_width, Qt.DashLine)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        w = max(1, self.width())
        h = max(1, self.height() // 2)

        # Amplitud de la curvatura, dependiente de la altura disponible
        amplitude = min(48, max(12, self.parent().height() // 12 if self.parent() else 20))

        # Dibujar una curva cuadrática que simula un cable flácido
        path = QPainterPath()
        # moveTo
        path.moveTo(0, h)
        # control point en la mitad con desplazamiento vertical para la curva
        cx = w / 2
        cy = h + amplitude
        path.quadTo(cx, cy, w, h)

        painter.drawPath(path)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self._drag_offset = event.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging and self.parent():
            # Calcular nueva posición vertical relativa al padre
            global_pos = self.mapToParent(event.pos() - self._drag_offset)
            new_x = self.x()
            new_y = max(0, min(self.parent().height() - self.height(), global_pos.y()))
            self.move(new_x, new_y)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class Bubble(QFrame):
    """Burbujas de mensaje estilo redondeado tradicional y mate."""

    def __init__(self, texto, es_usuario):
        super().__init__()
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(6, 4, 6, 4)

        self.lbl = QLabel("")
        self.lbl.setWordWrap(True)
        self.lbl.setContentsMargins(14, 10, 14, 10)
        self.lbl.setMaximumWidth(450)

        self.texto_completo = texto or ""
        self.es_usuario = es_usuario

        if es_usuario:
            self.lbl.setText(texto)
            # Gris neutro ligeramente más claro para el usuario
            self.lbl.setStyleSheet("""
                background-color: rgba(193, 122, 86, 0.16);
                color: #ded8ca;
                border-radius: 14px;
                border-bottom-right-radius: 4px;
                font-size: 13px;
            """)
            self.layout.addStretch()
            self.layout.addWidget(self.lbl)
        else:
            # Gris oscuro neutro para el bot
            self.lbl.setStyleSheet("""
                background-color: #2b2e38;
                color: #ded8ca;
                border: 1px solid #33363f;
                border-radius: 14px;
                border-bottom-left-radius: 4px;
                font-size: 13px;
            """)

            self.contenedor = QWidget()
            self.contenedor.setStyleSheet("background-color: transparent;")
            contenedor_layout = QVBoxLayout(self.contenedor)
            contenedor_layout.setContentsMargins(0, 0, 0, 0)
            contenedor_layout.setSpacing(0)
            contenedor_layout.addWidget(self.lbl)

            self.btn_copiar = QPushButton("Copiar", self.contenedor)
            self.btn_copiar.setCursor(Qt.PointingHandCursor)
            self.btn_copiar.setFixedHeight(22)
            self.btn_copiar.setFixedWidth(50)
            self.btn_copiar.hide()
            self.btn_copiar.setStyleSheet("""
                QPushButton {
                    background-color: #1d2028;
                    color: #8f8b83;
                    border: 1px solid #3c3f4a;
                    border-radius: 4px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #20232c;
                    color: #ded8ca;
                }
            """)
            self.btn_copiar.clicked.connect(self._copiar_texto)

            self._timer_feedback = QTimer(self)
            self._timer_feedback.setSingleShot(True)
            self._timer_feedback.timeout.connect(self._restaurar_boton)

            self.layout.addWidget(self.contenedor)
            self.layout.addStretch()

            self.setMouseTracking(True)
            self.contenedor.setMouseTracking(True)
            self.lbl.setMouseTracking(True)

            self.indice_actual = 0
            self.timer_typing = QTimer(self)
            self.timer_typing.timeout.connect(self.mostrar_siguiente_letra)
            self.timer_typing.start(12)

        self.setLayout(self.layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.es_usuario and hasattr(self, 'btn_copiar'):
            x = self.lbl.x() + self.lbl.width() - self.btn_copiar.width() - 6
            y = self.lbl.y() + 6
            self.btn_copiar.move(x, y)

    def enterEvent(self, event):
        if not self.es_usuario and hasattr(self, 'btn_copiar'):
            self.btn_copiar.show()
            self.btn_copiar.raise_()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.es_usuario and hasattr(self, 'btn_copiar'):
            self.btn_copiar.hide()
        super().leaveEvent(event)

    def _copiar_texto(self):
        QApplication.clipboard().setText(self.texto_completo)
        self.btn_copiar.setText("✓")
        self.btn_copiar.setStyleSheet("""
            QPushButton {
                background-color: rgba(193, 122, 86, 0.16);
                color: #d38f6c;
                border: 1px solid #c17a56;
                border-radius: 4px;
                font-size: 10px;
            }
        """)
        self._timer_feedback.start(1200)

    def _restaurar_boton(self):
        self.btn_copiar.setText("Copiar")
        self.btn_copiar.setStyleSheet("""
            QPushButton {
                background-color: #1d2028;
                color: #8f8b83;
                border: 1px solid #3c3f4a;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #20232c;
                color: #ded8ca;
            }
        """)

    def mostrar_siguiente_letra(self):
        if self.indice_actual < len(self.texto_completo):
            self.indice_actual += 1
            self.lbl.setText(self.texto_completo[:self.indice_actual])
        else:
            self.timer_typing.stop()
            self.lbl.setText(self.texto_completo)


class TarjetaComando(QFrame):
    """Tarjeta de comandos estilo mate."""
    def __init__(self, titulo, descripcion):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #1d2028;
                border: 1px solid #33363f;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        title_label = QLabel(titulo)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: #ded8ca; font-size: 12px; font-weight: 600; border: none; background: transparent;")

        desc_label = QLabel(descripcion)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #8f8b83; font-size: 11px; border: none; background: transparent;")

        layout.addWidget(title_label)
        layout.addWidget(desc_label)


class PanelManualCyberpunk(QWidget):
    """Panel desplegable tipo explorador/comandos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.panel_abierto = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.main_frame = QFrame()
        self.main_frame.setStyleSheet("""
            QFrame {
                background-color: #2b2e38;
                border-right: 1px solid #33363f;
            }
        """)
        frame_layout = QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        self.header = QLabel(" Comandos")
        self.header.setFixedHeight(38)
        self.header.setStyleSheet("""
            background-color: #2b2e38;
            color: #ded8ca;
            font-size: 12px;
            font-weight: 600;
            border-bottom: 1px solid #33363f;
            padding-left: 10px;
        """)
        frame_layout.addWidget(self.header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background-color: #2b2e38; }
            QScrollBar:vertical { border: none; background: transparent; width: 4px; }
            QScrollBar::handle:vertical { background: #3c3f4a; border-radius: 2px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background: none; }
        """)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: #2b2e38;")

        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setContentsMargins(10, 10, 10, 10)
        self.cards_layout.setSpacing(6)

        self.scroll.setWidget(self.scroll_content)
        frame_layout.addWidget(self.scroll)
        layout.addWidget(self.main_frame)

        self.preparar_manual()

    def preparar_manual(self):
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        try:
            from comandos import obtener_comandos
            _comandos = obtener_comandos(None)
            texto = next(c["resp"] for c in _comandos if c["id"] == "info_commands")

            lineas = texto.split('\n')
            for linea in lineas:
                linea_limpia = linea.strip()

                if not linea_limpia or linea_limpia.startswith('**') or '¿Qué te apetece' in linea_limpia:
                    continue

                if linea_limpia.startswith('•'):
                    linea_limpia = linea_limpia[1:].strip()

                if '➔' in linea_limpia:
                    partes = linea_limpia.split('➔', 1)
                    cmd = partes[0].replace('`', '').strip()
                    desc = partes[1].strip()

                    tarjeta = TarjetaComando(cmd, desc)
                    self.cards_layout.addWidget(tarjeta)

            self.cards_layout.addStretch()

        except Exception as e:
            error_label = QLabel(f"Error: {e}")
            error_label.setWordWrap(True)
            error_label.setStyleSheet("color: #8f8b83; font-size: 11px;")
            self.cards_layout.addWidget(error_label)


    def mostrar_manual(self):
        self.preparar_manual()


class VentanaManualComandosCyberpunk(QWidget):
    """Ventana independiente para el manual de comandos."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowModality(Qt.NonModal)
        self.resize(529, 620)

        # Para controlar el arrastre con el ratón
        self.drag_position = QPoint()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        container = QFrame(self)
        container.setStyleSheet("""
            QFrame {
                background-color: #242730;
                border: 1px solid #3c3f4a;
                border-radius: 12px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(8)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        title = QLabel("🧠 Comandos")
        title.setStyleSheet("color: #ded8ca; font-size: 13px; font-weight: 600;")

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8f8b83;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { color: #ded8ca; }
        """)
        close_btn.clicked.connect(self.close)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)

        self.panel = PanelManualCyberpunk(self)
        self.panel.setContentsMargins(0, 0, 0, 0)

        container_layout.addLayout(header_layout)
        container_layout.addWidget(self.panel)
        root_layout.addWidget(container)

    # --- Métodos para permitir arrastrar la ventana flotante ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def show(self):
        super().show()
        self.raise_()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


class MenuComandosCyberpunk(QWidget):
    """Ventana independiente de comandos."""

    itemClicked = pyqtSignal(QListWidgetItem)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowModality(Qt.NonModal)
        self.resize(340, 260) 
  

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        container = QFrame(self)
        container.setStyleSheet("""
            QFrame {
                background-color: #2b2e38;
                border: 1px solid #3c3f4a;
                border-radius: 10px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(8)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        title_label = QLabel("Comandos")
        title_label.setStyleSheet("color: #ded8ca; font-size: 13px; font-weight: 600;")

        close_button = QPushButton("✕")
        close_button.setFixedSize(26, 26)
        close_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8f8b83;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #ded8ca;
            }
        """)
        close_button.clicked.connect(self.hide)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_button)

        self.list_widget = QListWidget(self)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                color: #ded8ca;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-radius: 6px;
            }
            QListWidget::item:hover {
                background-color: rgba(193, 122, 86, 0.16);
            }
        """)

        container_layout.addLayout(header_layout)
        container_layout.addWidget(self.list_widget)
        root_layout.addWidget(container)

        self.list_widget.itemClicked.connect(self.itemClicked.emit)
        self.hide()

    def clear(self):
        self.list_widget.clear()

    def addItem(self, item):
        self.list_widget.addItem(item)

    def setFixedHeight(self, h):
        self.list_widget.setFixedHeight(h)
        super().setFixedHeight(h)

    def setFixedWidth(self, w):
        self.list_widget.setFixedWidth(w)
        super().setFixedWidth(w)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    def show(self):
        super().show()
        self.raise_()

    def hide(self):
        super().hide()


class BubbleDescarga(QFrame):
    def __init__(self):
        super().__init__()
        self.setMaximumWidth(300)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 10, 12, 10)
        self.layout.setSpacing(6)

        self.setStyleSheet("""
            QFrame {
                background-color: #2b2e38;
                border: 1px solid #3c3f4a;
                border-radius: 8px;
            }
        """)

        self.lbl_info = QLabel("Descargando...")
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setStyleSheet("color: #ded8ca; font-size: 12px;")

        self.barra = QProgressBar()
        self.barra.setTextVisible(False)
        self.barra.setFixedHeight(4)
        self.barra.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #1d2028;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #c17a56;
                border-radius: 2px;
            }
        """)

        self.layout.addWidget(self.lbl_info)
        self.layout.addWidget(self.barra)

    def actualizar(self, porcentaje, texto):
        self.barra.setValue(porcentaje)
        self.lbl_info.setText(texto)

    def completar(self, texto_final):
        self.barra.setValue(100)
        self.lbl_info.setStyleSheet("color: #ded8ca; font-size: 12px; font-weight: bold;")
        self.lbl_info.setText(texto_final)

import random
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen

class OverlayKawaii(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setFocusPolicy(Qt.StrongFocus)
        
        # Ángulo de rotación de la galaxia
        self.angulo_rotacion = 0.0
        
        # Generar estrellas fijas en la estructura de los brazos
        self.estrellas = []
        num_brazos = 3
        estrellas_por_brazo = 120
        
        for brazo in range(num_brazos):
            angulo_base = (2 * math.pi / num_brazos) * brazo
            for i in range(estrellas_por_brazo):
                distancia = 10 + (i * 2.2) + (i ** 1.1)
                espira = angulo_base + (distancia * 0.015)
                # Variación leve para dar volumen al brazo galáctico
                offset_r = (i % 7) - 3
                distancia_final = max(5, distancia + offset_r)
                
                # Tamaño y brillo
                tamano = 1.5 if i % 3 == 0 else (2.5 if i % 5 == 0 else 1.0)
                alpha = min(255, int(100 + (155 * (1 - (distancia / 350)))))
                
                # Color (Tonos cian, violeta y rosa neón)
                if i % 4 == 0:
                    color = QColor(138, 43, 226, max(30, alpha))   # Púrpura
                elif i % 4 == 1:
                    color = QColor(0, 240, 255, max(30, alpha))    # Cian
                elif i % 4 == 2:
                    color = QColor(255, 105, 180, max(30, alpha))  # Rosa
                else:
                    color = QColor(255, 255, 255, max(40, alpha))  # Blanco
                    
                self.estrellas.append({
                    'r': distancia_final,
                    'angulo_inicial': espira,
                    'tamano': tamano,
                    'color': color
                })

        # Timer de renderizado continuo (~60 FPS)
        self.timer_animacion = QTimer(self)
        self.timer_animacion.timeout.connect(self._actualizar_rotacion)
        self.timer_animacion.start(16)

    def _actualizar_rotacion(self):
        # Velocidad de rotación
        self.angulo_rotacion += 0.008
        if self.angulo_rotacion >= 2 * math.pi:
            self.angulo_rotacion -= 2 * math.pi
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Fondo semi-transparente oscuro profundo
        painter.fillRect(self.rect(), QColor(8, 10, 15, 235))

        cx = self.width() // 2
        cy = self.height() // 2

        painter.setPen(Qt.NoPen)

        # 2. Resplandor central del núcleo galáctico
        for r, alpha in [(60, 15), (40, 35), (20, 70), (8, 180)]:
            painter.setBrush(QBrush(QColor(180, 220, 255, alpha)))
            painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        # 3. Dibujar estrellas en sus posiciones rotadas
        for estrella in self.estrellas:
            angulo_actual = estrella['angulo_inicial'] + self.angulo_rotacion
            
            # Coordenadas polares a cartesianas
            x = cx + estrella['r'] * math.cos(angulo_actual)
            y = cy + estrella['r'] * math.sin(angulo_actual)

            painter.setBrush(QBrush(estrella['color']))
            r_tam = estrella['tamano']
            painter.drawEllipse(int(x - r_tam), int(y - r_tam), int(r_tam * 2), int(r_tam * 2))

    def mousePressEvent(self, event):
        self.hide()
        event.accept()

    def keyPressEvent(self, event):
        self.hide()
        event.accept()