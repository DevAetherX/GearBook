import base64
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve
from PyQt5.QtGui import QPixmap, QImage
from recursos import ICON_B64


class ToastCyberpunk(QWidget):
    """Notificación flotante personalizada estilo Cyberpunk."""
    def __init__(self, titulo: str, mensaje: str, icon_b64: str = ICON_B64):
        super().__init__()
        
        # Configuración de ventana flotante sin bordes
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Contenedor principal con estilo visual
        self.contenedor = QWidget(self)
        self.contenedor.setStyleSheet("""
            QWidget {
                background-color: #12151a;
                border: 1px solid #ff7700;
                border-radius: 8px;
            }
        """)

        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        
        layout_interno = QHBoxLayout(self.contenedor)
        layout_interno.setContentsMargins(12, 12, 12, 12)
        layout_interno.setSpacing(12)

        # 1. Icono personalizado desde Base64
        lbl_icon = QLabel()
        data = base64.b64decode(icon_b64)
        img = QImage.fromData(data)
        lbl_icon.setPixmap(QPixmap.fromImage(img).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        lbl_icon.setStyleSheet("border: none; background: transparent;")

        # 2. Bloque de Textos
        vbox_texto = QVBoxLayout()
        vbox_texto.setSpacing(2)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("""
            color: #ff7700; 
            font-size: 13px; 
            font-weight: bold; 
            font-family: 'Segoe UI', sans-serif;
            border: none;
            background: transparent;
        """)

        lbl_mensaje = QLabel(mensaje)
        lbl_mensaje.setStyleSheet("""
            color: #c9d1d9; 
            font-size: 11px; 
            font-family: 'Segoe UI', sans-serif;
            border: none;
            background: transparent;
        """)
        lbl_mensaje.setWordWrap(True)

        vbox_texto.addWidget(lbl_titulo)
        vbox_texto.addWidget(lbl_mensaje)

        layout_interno.addWidget(lbl_icon, 0, Qt.AlignTop)
        layout_interno.addLayout(vbox_texto, 1)
        layout_principal.addWidget(self.contenedor)

        self.setFixedSize(360, 80)

        # Posicionar en la esquina inferior derecha de la pantalla
        desktop = QApplication.desktop().availableGeometry()
        self.pos_x = desktop.width() - self.width() - 20
        self.pos_y_final = desktop.height() - self.height() - 40
        self.pos_y_inicio = desktop.height() + 10

        self.setGeometry(self.pos_x, self.pos_y_inicio, self.width(), self.height())

        # Animación de entrada
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300)
        self.anim.setStartValue(QPoint(self.pos_x, self.pos_y_inicio))
        self.anim.setEndValue(QPoint(self.pos_x, self.pos_y_final))
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()

        # Ocultar automáticamente tras 4 segundos
        QTimer.singleShot(4000, self.cerrar_con_animacion)

    def cerrar_con_animacion(self):
        self.anim_salida = QPropertyAnimation(self, b"pos")
        self.anim_salida.setDuration(300)
        self.anim_salida.setStartValue(QPoint(self.pos_x, self.pos_y_final))
        self.anim_salida.setEndValue(QPoint(self.pos_x, self.pos_y_inicio))
        self.anim_salida.setEasingCurve(QEasingCurve.InCubic)
        self.anim_salida.finished.connect(self.close)
        self.anim_salida.start()


class GestorNotificaciones:
    """Vínculo entre María y el nuevo sistema de Toast."""
    def __init__(self, maria_instance):
        self.maria = maria_instance
        self._notificacion_activa = None

    def notificar_tarea_finalizada(self, tarea: str, detalle: str = ""):
        titulo = f"⚡ Tarea Finalizada: {tarea}"
        mensaje = detalle if detalle else f"La operación '{tarea}' ha concluido con éxito."
        
        # Crear y mostrar el Toast personalizado
        self._notificacion_activa = ToastCyberpunk(titulo, mensaje)
        self._notificacion_activa.show()

    def notificar_descarga(self, nombre_archivo: str):
        self.notificar_tarea_finalizada(
            "Descarga completada",
            f"El archivo '{nombre_archivo}' ya está disponible."
        )
    # 🌟 NUEVO MÉTODO PARA ERRORES
    def notificar_error(self, tarea: str, detalle: str = ""):
        titulo = f"❌ Error en Tarea: {tarea}"
        mensaje = detalle if detalle else f"Ocurrió un fallo en la operación '{tarea}'."
        self._notificacion_activa = ToastCyberpunk(titulo, mensaje)
        self._notificacion_activa.show()

    def notificar_organizacion(self, carpeta: str):
        self.notificar_tarea_finalizada(
            "Organización finalizada",
            f"Se ha terminado de ordenar el directorio: {carpeta}"
        )