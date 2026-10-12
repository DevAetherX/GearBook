import argparse
import base64
import os
import re
import sys
import faulthandler
#faulthandler.enable()                     # imprime el trace en stderr
#faulthandler.dump_traceback_later(30)    

# ═══ PRE-CARGA DE ONNXRUNTIME ANTES DE CUALQUIER OTRA COSA ═══
try:
    import onnxruntime as _ort
    print(f"✅ onnxruntime pre-cargado: {_ort.__version__} | providers: {_ort.get_available_providers()}")
except Exception as e:
    print(f"⚠️ No se pudo pre-cargar onnxruntime: {e}")
# ═══════════════════════════════════════════════════════════════

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAIN_DIR = os.path.dirname(os.path.abspath(__file__))

for path in (ROOT, MAIN_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from componentes import Bubble, MenuComandosCyberpunk, VentanaManualComandosCyberpunk, BubbleDescarga, OverlayKawaii

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


import keyboard
import time
import threading
import speech_recognition as sr
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QPushButton, QLabel, 
                             QScrollArea, QSizePolicy, QMenu, QSystemTrayIcon,
                             QShortcut, QListWidgetItem)
from PyQt5.QtWidgets import QFileDialog
import shutil
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint, QRect, QEvent
from PyQt5.QtGui import QKeySequence, QIcon, QImage, QPixmap

from interfaz_principal import InterfazPrincipal
from explorador import main_explorador as explorador
from explorador.interfaz_explorador import SelectorDestino
from stream_deck import stream_deck
from notas import main_notas
from notificaciones import GestorNotificaciones
from indicador import IndicadorFlotante
from finanzas import main_finanzas
import ctypes


from organizador import organizar_carpeta
from comandos import obtener_comandos
from boveda_musica import reproducir_musica_por_ruta_comando
from monitores import abrir_en_monitor as _abrir_en_monitor

from voz_asistente import HiloVozNeuronal
from descargador import (
    HiloDescarga,
    HiloFormatos,
    descargar_video_interactivo as _descargar_video_interactivo,
    procesar_descarga_respuesta as _procesar_descarga_respuesta,
    set_respuesta_descarga as _set_respuesta_descarga,
)
from memoria.memoria import (
    inicializar_memoria,
    guardar_historial,
    obtener_ultimo_mensaje,
    cargar_historial,
    construir_contexto as _construir_contexto,
)
from procesamiento import procesar
from dialogos_motor import (
    cerebro_dialogo as _cerebro_dialogo,
    construir_respuesta_dinamica as _construir_respuesta_dinamica,
    obtener_respuestas_por_defecto as _obtener_respuestas_por_defecto,
)
from dialogos import DIALOGOS
from recursos import ICON_B64


inicializar_memoria()


def get_icon():
    data = base64.b64decode(ICON_B64)
    img = QImage.fromData(data)
    return QIcon(QPixmap.fromImage(img))

def parsear_argumentos(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--comando", dest="comando", default=None)
    return parser.parse_known_args(argv)[0]


ARGUMENTOS_INICIO = parsear_argumentos(sys.argv[1:])


class MariaChat(QMainWindow):
    trigger_mostrar_ocultar = pyqtSignal()
    # 🌟 Señales que antes vivían en LogicaMaria. María es ahora su propio
    # conector, así que las declara ella misma (QMainWindow ya es QObject).
    descarga_finalizada_signal = pyqtSignal(str)
    descarga_progreso_signal = pyqtSignal(int, str)

    # 🎙️ Señales thread-safe para el micrófono (Hilo secundario → GUI)
    voz_recibida_signal = pyqtSignal(str)
    voz_error_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.ultima_url = None
        self.esperando_confirmacion = None  # Para el apagado/reinicio
        self.dialogos = DIALOGOS 
        self.muteado = True
        self.historial = cargar_historial()
        self.comando_inicial = getattr(ARGUMENTOS_INICIO, "comando", None)
        self.gestor_notificaciones = GestorNotificaciones(self)

        # ── Estado que antes gestionaba LogicaMaria ────────────────────
        self.descarga_pendiente = None
        self.respuesta_descarga = None
        self.hilo_descarga = None
        self.hilo_voz = None
        self.comandos = obtener_comandos(self)

        # 🎙️ Conectar señales de voz (thread-safe: hilo secundario → GUI)
        self.voz_recibida_signal.connect(self._voz_recibida)
        self.voz_error_signal.connect(self._voz_error)

        # 🌟 NUEVA POSICIÓN: Creamos el menú independiente de la ventana principal
        self.menu_comandos = MenuComandosCyberpunk()
        self.menu_comandos.hide() # Ahora sí puedes ocultarlo sin errores porque ya existe
        self.ventana_manual_comandos = None
        self.alt_q_pressed = False
        self.ultimo_cambio_estado = 0  
        self.descarga_progreso_signal.connect(self.actualizar_progreso_descarga)
        self.burbuja_descarga_activa = None  # Guardará la referencia a la barra actual
        self.archivo_descargado_pendiente = None
        self.esperando_confirmacion_movimiento = False
        self._msg_count = 0
   
    
        # Guardar geometría original para poder restaurar desde pantalla completa
        self.geometria_normal = QRect(0, 0, 460, 660)
        self.es_pantalla_completa = False
        
        # --- CONFIGURACIÓN DE VENTANA ---
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        
        self.init_ui()
        
        self.drag_position = QPoint()

        # 🌟 Escuchar la señal cuando termine una descarga en segundo plano
        self.descarga_finalizada_signal.connect(self.mostrar_mensaje_descarga_automatica)

        # --- ANIMACIONES ---
        self.anim_geometry = QPropertyAnimation(self, b"geometry")
        self.anim_geometry.setDuration(300)
        self.anim_geometry.setEasingCurve(QEasingCurve.OutBack)

        self.trigger_mostrar_ocultar.connect(self.aparecer_desaparecer)
        
        try:
            keyboard.add_hotkey('alt+q', self.trigger_mostrar_ocultar.emit, suppress=False)
        except Exception as e:
            print(f"No se pudo registrar el hotkey: {e}")
            
        self.hotkey_timer = QTimer(self)
        self.hotkey_timer.timeout.connect(self.check_hotkey)
        self.hotkey_timer.start(50)
        
        QTimer.singleShot(100, self.input_field.setFocus)
        self.inicializar_tray_icon()

        # Conectar el cambio de texto del input para revisar si hay una "/"
        self.input_field.textChanged.connect(self.evaluar_autocompletado)
        
        # Conectar el clic en un elemento del menú para que se escriba en el input
        self.menu_comandos.itemClicked.connect(self.seleccionar_comando_menu)
        
        # Lista de comandos disponibles sacados de la lógica de María
        self.lista_comandos_sugeridos = [
         "explorador/",
         "ordenar/",
         "music/",
         "descargar/",
         "busca en internet/",
         "youtube",
         "whatsapp",
         "pausar",
         "reanudar",
         "telegram",
         "notas/",
         "finanzas",
        ]

    # ── INDICADOR FLOTANTE ──────────────────────────────────────
        self.indicador = IndicadorFlotante()
        self.indicador.clic_restaurar.connect(self._restaurar_desde_indicador)
        self.indicador.clic_ocultar.connect(self.aparecer_desaparecer)

    # --- SISTEMA DE SUSPENSIÓN KAWAII ---
        self.overlay_kawaii = OverlayKawaii(self)
        self.overlay_kawaii.hide()

        # Configurar Timer de inactividad (Ejemplo: 60 segundos)
        self.timer_inactividad = QTimer(self)
        self.timer_inactividad.setInterval(60000) # 60000 ms = 1 min
        self.timer_inactividad.timeout.connect(self._activar_suspension)
        self.timer_inactividad.start()

        # Instalar filtro de eventos en la aplicación para detectar actividad
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        # Reiniciar temporizador ante cualquier interacción del usuario
        if event.type() in (event.MouseButtonPress, event.MouseMove, event.KeyPress, event.Wheel):
            if hasattr(self, 'timer_inactividad'):
                self.timer_inactividad.start()
            if hasattr(self, 'overlay_kawaii') and self.overlay_kawaii.isVisible():
                self.overlay_kawaii.hide()
        return super().eventFilter(obj, event)

    def _activar_suspension(self):
        if self.isVisible() and not self.overlay_kawaii.isVisible():
            self.overlay_kawaii.setGeometry(self.rect())
            self.overlay_kawaii.raise_()
            self.overlay_kawaii.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Mantener el overlay adaptado al tamaño de la ventana
        if hasattr(self, 'overlay_kawaii'):
            self.overlay_kawaii.setGeometry(self.rect())

    def moveEvent(self, event):
        """Si la ventana principal se mueve, reposicionamos oponemos el menú en su sitio"""
        super().moveEvent(event)
        if hasattr(self, 'menu_comandos') and self.menu_comandos.isVisible():
            # Volvemos a calcular la posición para que siga al entry de texto
            punto_global = self.input_field.mapToGlobal(QPoint(0, 0))
            pos_x = punto_global.x()
            pos_y = punto_global.y() - self.menu_comandos.height() - 5
            self.menu_comandos.move(pos_x, pos_y)


    def mostrar_mensaje_descarga_automatica(self, mensaje):
        # 1. Comprobar si el mensaje reporta éxito
        if "|" in mensaje and ("VIDEO_OK" in mensaje or "AUDIO_OK" in mensaje):
            tipo, ruta = mensaje.split("|", 1)
            self.archivo_descargado_pendiente = ruta
            self.esperando_confirmacion_movimiento = True
            
            # Notificación emergente de éxito
            nombre_archivo = os.path.basename(ruta or "Archivo")
            self.gestor_notificaciones.notificar_descarga(nombre_archivo)
            
            # Actualizar burbuja visual
            if hasattr(self, 'burbuja_descarga_activa') and self.burbuja_descarga_activa:
                self.burbuja_descarga_activa.completar("✓ SECUENCIA COMPLETADA")
                self.burbuja_descarga_activa = None  

            txt_consola = (
                f"🛰️ **OPERACIÓN COMPLETADA EXITOSAMENTE**\n\n"
                f"📂 Archivo: `{nombre_archivo}`\n"
                f"📍 Ubicación: `{os.path.dirname(ruta)}`\n\n"
                f"¿Desea redirigir o mover este elemento a un nuevo directorio del sistema? (SÍ / NO)"
            )
            self.agregar_b(txt_consola, False)
            self.hablar("Secuencia de descarga completada, Administrador. ¿Deseas mover el archivo a otra ubicación?")

        # 2. Manejo cuando ocurre un error o fallo en la descarga
        else:
            # Notificación emergente de error
            self.gestor_notificaciones.notificar_error("Descarga fallida", mensaje)
            
            # Marcar burbuja como fallida si existe el método en BubbleDescarga
            if hasattr(self, 'burbuja_descarga_activa') and self.burbuja_descarga_activa:
                if hasattr(self.burbuja_descarga_activa, 'completar'):
                    self.burbuja_descarga_activa.completar("❌ ERROR EN DESCARGA")
                self.burbuja_descarga_activa = None

            self.agregar_b(mensaje, False)
            self.hablar(mensaje)
        

    def check_hotkey(self):
        try:
            if keyboard.is_pressed('alt+q'):
                if not self.alt_q_pressed:
                    self.alt_q_pressed = True
                    self.trigger_mostrar_ocultar.emit()
            else:
                self.alt_q_pressed = False
        except:
            pass

    def init_ui(self):
        self.interfaz_principal = InterfazPrincipal(self)
        self.setCentralWidget(self.interfaz_principal)
        self.resize(1050, 720)
        self.setWindowIcon(get_icon())
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.mostrar_menu)

        self._dot_visible = True
        self._dot_timer = QTimer(self)
        self._dot_timer.timeout.connect(self._parpadear_dot)
        self._dot_timer.start(900)

        self._reloj_timer = QTimer(self)
        self._reloj_timer.timeout.connect(self._actualizar_reloj)
        self._reloj_timer.start(1000)

        self._mic_escuchando = False

        self.btn_maximize.clicked.connect(self.toggle_fullscreen)
        self.btn_minimize.clicked.connect(self.showMinimized)   
        self.btn_mic.clicked.connect(self.toggle_escuchar_voz)
        self.btn_panel.clicked.connect(self.toggle_panel)
         
        self.interfaz_principal.btn_send.clicked.connect(self.enviar)
        self.input_field.textChanged.connect(self.evaluar_autocompletado)
        self.menu_comandos.itemClicked.connect(self.seleccionar_comando_menu)

        self._actualizar_reloj()
        self._actualizar_fecha()

        self.shortcut_foco = QShortcut(QKeySequence("Ctrl+F"), self)
        self.shortcut_foco.activated.connect(self.recuperar_foco_input)

        self.servidor_deck = stream_deck.ServidorStreamDeck()
        self.servidor_deck.comando_recibido.connect(
            lambda cmd: stream_deck.manejar_comando(self, cmd)
        )
        self.servidor_deck.start()
        QTimer.singleShot(300, self._aplicar_comando_inicial)
        QTimer.singleShot(800, self._aplicar_comando_inicial)

    # ═══════════════════════════════════════════
    # MÉTODOS AUXILIARES DE LA HUD
    # ═══════════════════════════════════════════
    def _aplicar_comando_inicial(self):
        if not self.comando_inicial:
            return

        comando = self.comando_inicial.strip()
        if comando:
            self.comando_inicial = None
            _asegurar_visible = lambda: stream_deck._asegurar_visible(self)
            _asegurar_visible()
            stream_deck.manejar_comando(self, comando)

            # Garantizar visibilidad de la ventana
            self.show()
            self.showNormal()
            self.raise_()
            self.activateWindow()

            if comando.startswith("PREFILL:"):
                texto_prefill = comando[len("PREFILL:"):]
                self.input_field.setText(texto_prefill)
                self.input_field.setFocus()
                self.input_field.setCursorPosition(len(self.input_field.text()))
            else:
                # Comandos normales de ejecución directa
                QTimer.singleShot(200, lambda: stream_deck.manejar_comando(self, comando))

    def _actualizar_reloj(self):
        from datetime import datetime
        self.lbl_reloj.setText(datetime.now().strftime("[%H:%M:%S]"))

    def _actualizar_fecha(self):
        from datetime import datetime
        self.lbl_fecha.setText(datetime.now().strftime("DATE:%Y.%m.%d"))

    def _parpadear_dot(self):
        self._dot_visible = not self._dot_visible
        color = "#f0c37b" if self._dot_visible else "#7c6a4f"
        self.lbl_status_dot.setStyleSheet(f"color: {color}; font-size: 10px;")

    def _set_maria_procesando(self, procesando: bool):
        """Cambia el indicador de estado mientras María genera respuesta."""
        if procesando:
            self.lbl_status_dot.setStyleSheet("color: #ff7700; font-size: 10px;")
            self.lbl_status_text.setText("PROC...")
            self.lbl_status_text.setStyleSheet("color: #ff7700; font-family: 'Segoe UI', sans-serif; font-size: 9px;")
            self.lbl_status_bar.setText("▸ Generando respuesta... por favor espere")
            self.lbl_status_bar.setStyleSheet("color: #ff7700; font-family: 'Segoe UI', sans-serif; font-size: 8px; background-color: #eef2f8;")
            self._sync_estado_indicador("procesando" if procesando else "idle")
            self._dot_timer.stop()
        else:
            self.lbl_status_dot.setStyleSheet("color: #f0c37b; font-size: 10px;")
            self.lbl_status_text.setText("ONLINE")
            self.lbl_status_text.setStyleSheet("color: #f0c37b; font-family: 'Segoe UI', sans-serif; font-size: 9px;")
            self.lbl_status_bar.setText("▸ SISTEMA LISTO — Esperando entrada del Administrador...")
            self.lbl_status_bar.setStyleSheet("color: #4f5f78; font-family: 'Segoe UI', sans-serif; font-size: 8px; background-color: #eef2f8;")
            self._dot_timer.start(900)

    def _incrementar_msg_count(self):
        self._msg_count += 1
        self.lbl_mensajes.setText(f"MSG_COUNT: {self._msg_count}")

    def _sync_estado_indicador(self, estado: str):
         if hasattr(self, "indicador") and self.indicador:
            self.indicador.set_estado(estado)

    def _restaurar_desde_indicador(self):
        """Restaura la ventana principal al hacer clic en el punto flotante."""
        if not self.isVisible():
            self.aparecer_desaparecer()
        else:
            self.raise_()
            self.activateWindow()

    def _mostrar_indicador(self):
     if hasattr(self, 'indicador') and self.indicador:
        self.indicador.show()
        self.indicador.raise_()

    def _ocultar_indicador(self):
     if hasattr(self, 'indicador') and self.indicador:
        self.indicador.hide()

    def showEvent(self, event):
     super().showEvent(event)
     self._ocultar_indicador()

    def hideEvent(self, event):
     super().hideEvent(event)
     self._mostrar_indicador()

    def changeEvent(self, event):
     if event.type() == QEvent.WindowStateChange:
        if self.isMinimized():
            self._mostrar_indicador()
        else:
            self._ocultar_indicador()
     super().changeEvent(event)

    # ═══════════════════════════════════════════
    # MÉTODOS DE LÓGICA (antes vivían en logica.py)
    # Cada uno delega directamente al módulo correspondiente; main.py es
    # ahora el único punto que conecta la UI con los módulos de negocio.
    # ═══════════════════════════════════════════
    def set_espera(self, accion):
        self.esperando_confirmacion = accion

    def guardar_en_historial(self, mensaje_usuario, respuesta_maria):
        guardar_historial(mensaje_usuario, respuesta_maria)

    def construir_contexto(self, texto_usuario, max_ultimos=6):
        return _construir_contexto(self, texto_usuario, max_ultimos=max_ultimos)

    def fijar_volumen_exacto(self, porcentaje):
        try:
            import ctypes
            porcentaje = max(0, min(100, porcentaje))
            WM_APPCOMMAND = 0x0319
            APPCOMMAND_VOLUME_DOWN = 0x09
            APPCOMMAND_VOLUME_UP = 0x0A
            hwnd = ctypes.windll.user32.GetForegroundWindow()

            for _ in range(50):
                ctypes.windll.user32.SendMessageW(hwnd, WM_APPCOMMAND, 0, APPCOMMAND_VOLUME_DOWN << 16)

            pasos = int(porcentaje / 2)
            for _ in range(pasos):
                ctypes.windll.user32.SendMessageW(hwnd, WM_APPCOMMAND, 0, APPCOMMAND_VOLUME_UP << 16)

            return True
        except Exception:
            return False

    def cerebro_dialogo(self, texto_norm, contexto=None):
        """Delegado al módulo dialogos_motor (motor de diálogos de María)."""
        return _cerebro_dialogo(self, texto_norm, contexto=contexto)

    def construir_respuesta_dinamica(self, categoria):
        """Delegado al módulo dialogos_motor."""
        return _construir_respuesta_dinamica(self, categoria)

    def obtener_respuestas_por_defecto(self, humor_actual):
        """Delegado al módulo dialogos_motor."""
        return _obtener_respuestas_por_defecto(self, humor_actual)

    def hablar(self, texto):
        if self.muteado:
            return

        texto_limpio = self._limpiar_texto_para_voz(texto)
        if not texto_limpio.strip():
            return  # Si después de limpiar queda vacío, no hablamos
        
        self.hilo_voz = HiloVozNeuronal(texto_limpio)
        self.hilo_voz.start()

    
    def _limpiar_texto_para_voz(self, texto):
        if not texto:
            return ""

        t = texto

        # 1. Eliminar URLs completas (http://... o https://...)
        t = re.sub(r'https?://\S+', '', t)
        t = re.sub(r'www\.\S+', '', t)

        # 2. Eliminar markdown: **, __, `, ~, #, etc.
        t = re.sub(r'[*_`~#|]', '', t)

        # 3. Eliminar TODO tipo de emojis y símbolos por rangos Unicode
        #    (esto cubre los miles de emojis que existen, no solo 20)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticonos
            "\U0001F300-\U0001F5FF"  # símbolos y pictogramas
            "\U0001F680-\U0001F6FF"  # transporte y mapas
            "\U0001F1E0-\U0001F1FF"  # banderas
            "\U00002702-\U000027B0"  # dingbats
            "\U000024C2-\U0001F251"  # caracteres enclosed
            "\U0001f926-\U0001f937"  # caras gestuales
            "\U00010000-\U0010ffff"  # caracteres suplementarios
            "\u2640-\u2642"          # símbolos de género
            "\u2600-\u2B55"          # miscelánea de símbolos
            "\u200d"                 # zero width joiner
            "\u23cf"                 # símbolos de reproducción
            "\u23e9"                 # más símbolos
            "\u231a"                 # reloj
            "\ufe0f"                 # variation selector
            "\u3030"                 # guión ondulado
            "]+", flags=re.UNICODE
        )
        t = emoji_pattern.sub('', t)

        # 4. Eliminar caracteres NO latinos (japoneses, chinos, árabes, etc.)
        #    que el TTS lee como "símbolo japonés símbolo japonés..."
        t = re.sub(r'[^\w\s.,;:!?¿¡()\'"áéíóúüñÁÉÍÓÚÜÑ\-]', ' ', t, flags=re.UNICODE)

        # 5. Eliminar paréntesis con contenido raro dentro (tipo "(R>)E>7-ty")
        #    Si dentro del paréntesis hay más símbolos que letras, se elimina
        def limpiar_parentesis(match):
            contenido = match.group(1)
            letras = sum(1 for c in contenido if c.isalpha())
            otros = sum(1 for c in contenido if not c.isalpha() and not c.isspace())
            if otros > letras:  # más símbolos que letras → basura
                return ''
            return match.group(0)
        t = re.sub(r'\(([^)]*)\)', limpiar_parentesis, t)

        # 6. Normalizar espacios múltiples
        t = re.sub(r'\s+', ' ', t).strip()

        # 7. Truncar a 400 caracteres para no eternizar la locución
        if len(t) > 400:
            # Cortar en el último punto o espacio antes del límite
            corte = t[:400].rfind('.')
            if corte == -1:
                corte = t[:400].rfind(' ')
            if corte == -1:
                corte = 400
            t = t[:corte] + "."

        return t


    def abrir_gestor_finanzas(self):
        main_finanzas.abrir_gestor_finanzas(maria=self)

    def abrir_en_monitor(self, url_o_comando, num_monitor, es_url=True):
        """Delegado al módulo monitores (gestión de apertura por pantalla)."""
        return _abrir_en_monitor(url_o_comando, num_monitor, es_url=es_url)

    def reanudar_multimedia_sistema(self):
        """Simula la tecla física de Play/Pause de Windows para reanudar."""
        try:
            import ctypes
            # Enviamos el mismo código virtual VK_MEDIA_PLAY_PAUSE (0xB3)
            ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0)  # Presionar
            ctypes.windll.user32.keybd_event(0xB3, 0, 2, 0)  # Soltar
            return True
        except Exception as e:
            print(f"Error al reanudar multimedia: {e}")
            return False

    def descargar_video_interactivo(self, url):
        return _descargar_video_interactivo(self, url)

    def procesar_descarga_respuesta(self, texto):
        return _procesar_descarga_respuesta(self, texto)

    def set_respuesta_descarga(self, mensaje):
        return _set_respuesta_descarga(self, mensaje)

    def obtener_resoluciones_disponibles(self, url):
        try:
            return HiloDescarga(url, 'mp4').obtener_resoluciones_disponibles(url)
        except Exception:
            return None

    # --- INTERCEPTOR DE TECLAS FÍSICAS (FUSIONADO) ---
    def keyPressEvent(self, event):
        # F11: Pantalla completa (Activa y desactiva)
        if event.key() == Qt.Key_F11:
            self.toggle_fullscreen()
            event.accept()
            return
            
        # Ctrl + F: Re-enfocar el cuadro de texto
        if event.key() == Qt.Key_F and (event.modifiers() & Qt.ControlModifier):
            self.input_field.setFocus()
            self.input_field.selectAll()
            event.accept()
            return

        # Escape: Ocultar la ventana con animación
        if event.key() == Qt.Key_Escape:
            if self.isVisible():
                self.aparecer_desaparecer()
            event.accept()
            return
            
        super().keyPressEvent(event)

    def recuperar_foco_input(self):
        """Fuerza el foco al campo de texto del chat borrando cualquier selección previa."""
        self.input_field.setFocus()          # <--- CORREGIDO: input_field
        self.input_field.activateWindow()
    

    def toggle_fullscreen(self):
        desktop = QApplication.desktop().availableGeometry(self)
        if not self.es_pantalla_completa:
            self.geometria_normal = self.geometry()
            self.setGeometry(desktop)
            self.es_pantalla_completa = True
            self.btn_maximize.setText("❐")
        else:
            self.setGeometry(self.geometria_normal)
            self.es_pantalla_completa = False
            self.btn_maximize.setText("⛶")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.es_pantalla_completa:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self.es_pantalla_completa:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def toggle_panel(self):
        panel = self.interfaz_principal.panel_imagen
        if panel.isVisible():
            panel.setVisible(False)
            panel.setMaximumWidth(0)
            panel.setMinimumWidth(0)
            panel.panel_abierto = False
        else:
            panel.setVisible(True)
            panel.setMaximumWidth(320)
            panel.setMinimumWidth(320)
            panel.panel_abierto = True
            panel.mostrar_manual()

        # Reajustar distribución respetando si la búsqueda está activa
        ancho_busqueda = 300 if self.interfaz_principal.panel_busqueda.isVisible() else 0
        ancho_sidebar = 230 if self.interfaz_principal.sidebar_frame.isVisible() else 0
        ancho_manual = 320 if panel.panel_abierto else 0

        self.interfaz_principal.splitter.setSizes([ancho_sidebar, ancho_manual, 600, ancho_busqueda])
        self._update_arrow()

    def _update_arrow(self):
        panel = self.interfaz_principal.panel_imagen
        self.btn_panel.setText("▶" if panel and getattr(panel, 'panel_abierto', False) else "◀")

    def mostrar_manual_desde_menu(self):
        """Abre la ventana independiente del manual de comandos."""
        self.abrir_manual_comandos()

    def abrir_manual_comandos(self):
        if self.ventana_manual_comandos is None or not self.ventana_manual_comandos.isVisible():
            # 1. Instanciamos primero el objeto
            self.ventana_manual_comandos = VentanaManualComandosCyberpunk()
            # 2. Ahora sí podemos conectar la señal destroyed
            self.ventana_manual_comandos.destroyed.connect(lambda _: setattr(self, 'ventana_manual_comandos', None))
            self.ventana_manual_comandos.show()
        else:
            self.ventana_manual_comandos.raise_()
            self.ventana_manual_comandos.activateWindow()

    def aparecer_desaparecer(self):
        tiempo_actual = time.time()
        if tiempo_actual - self.ultimo_cambio_estado < 0.5:
            return
        self.ultimo_cambio_estado = tiempo_actual

        desktop = QApplication.desktop().availableGeometry(self)
        target_x = desktop.width() - self.width() - 40
        target_y_visible = desktop.height() - self.height() - 40
        target_y_oculto = desktop.height() + 50

        # === 1. CAPA DE SEGURIDAD: Si está minimizada de forma nativa por Windows, asegurar que el programa sepa que debe MOSTRARLA
        if self.isMinimized():
            self.showNormal()

        # === 2. CASO: LA VENTANA ES VISIBLE (Toca ocultarla) ===
        if self.isVisible():
            if self.es_pantalla_completa:
                self.hide()
            else:
                self.anim_geometry.setStartValue(self.geometry())
                self.anim_geometry.setEndValue(QRect(self.x(), target_y_oculto, self.width(), self.height()))
                self.anim_geometry.start()
                QTimer.singleShot(300, self.hide)

            QTimer.singleShot(50, self.input_field.clear)
        
        # === 3. CASO: LA VENTANA ESTÁ OCULTA (Toca mostrarla) ===
        else:
            # Si el usuario la tenía en pantalla completa antes de ocultarla
            if self.es_pantalla_completa:
                self.showFullScreen()  # Re-activamos el fullscreen nativo de Windows
                self.raise_()
                self.activateWindow()
            else:
                self.setGeometry(target_x, target_y_oculto, self.width(), self.height())
                self.show()
                self.raise_()
                self.activateWindow()
                self.anim_geometry.setStartValue(self.geometry())
                self.anim_geometry.setEndValue(QRect(target_x, target_y_visible, self.width(), self.height()))
                self.anim_geometry.start()

            self.input_field.clear()
            QTimer.singleShot(320, self.input_field.setFocus)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.agregar_b("Me quedaré esperando en las sombras, cielo... ✨", False)
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.showMessage(
                "María sigue activa",
                "Sigo aquí abajo, bombón. Usa Alt + Q para llamarme.",
                QSystemTrayIcon.Information,
                2000
            )

    def actualizar_progreso_descarga(self, porcentaje, texto):
        # Si no hay burbuja activa, la creamos con su contenedor de alineación.
        if not self.burbuja_descarga_activa:
            self.contenedor_descarga = QWidget()
            layout_envoltura = QHBoxLayout(self.contenedor_descarga)
            layout_envoltura.setContentsMargins(5, 5, 5, 5)  # Mismo margen que Bubble

            self.burbuja_descarga_activa = BubbleDescarga()
            layout_envoltura.addWidget(self.burbuja_descarga_activa)
            layout_envoltura.addStretch()

            self.chat_layout.insertWidget(self.chat_layout.count() - 1, self.contenedor_descarga)
            QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum()))

        self.burbuja_descarga_activa.actualizar(porcentaje, texto)
 
    # ═══════════════════════════════════════════
    # VOZ — Reconocimiento de voz por micrófono
    # ═══════════════════════════════════════════
    def toggle_escuchar_voz(self):
        """Alterna el estado de escucha: Inicia si está apagado, Cancela si está escuchando."""
        if self._mic_escuchando:
            # Si ya está escuchando, cancelamos la grabación
            self._cancelar_escucha_voz()
        else:
            self._iniciar_escucha_voz()

    def _iniciar_escucha_voz(self):
        self._mic_escuchando = True
        self.btn_mic.setText("⏹")
        self._sync_estado_indicador("escuchando")
        self.btn_mic.setStyleSheet("""
            QPushButton { 
                background: #3a0000; 
                border-radius: 4px; 
                font-size: 18px; 
                color: #ff0055; 
                border: 1px solid #ff0055;
            }
        """)
        self.input_field.setPlaceholderText("🎙 Escuchando... habla ahora (clic en ⏹ para cancelar)")
        
        # Guardamos la referencia al hilo para poder consultar el estado de cancelación
        self.hilo_mic = threading.Thread(target=self._reconocer_voz, daemon=True)
        self.hilo_mic.start()

    def _cancelar_escucha_voz(self):
        """Cancela la escucha activa e informa al usuario."""
        self._mic_escuchando = False
        self._restaurar_btn_mic()
        self.input_field.setPlaceholderText("❌ Escucha cancelada.")
        self._sync_estado_indicador("idle")
        QTimer.singleShot(1500, lambda: self.input_field.setPlaceholderText(
            "Escribe un mensaje o presiona el micro..."
        ))

    def _reconocer_voz(self):
        """Se ejecuta en un hilo secundario. Usa señales para comunicar con la GUI."""
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                print("[MIC] Ajustando ruido ambiente...")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("[MIC] Escuchando...")
                # Timeout más generoso: 15s para empezar a hablar, 30s máx de frase
                audio = recognizer.listen(source, timeout=15, phrase_time_limit=30)
            
            print("[MIC] Audio capturado, reconociendo...")

            # Verificación: si el usuario presionó detener mientras grababa
            if not self._mic_escuchando:
                print("[MIC] Cancelado por el usuario durante la grabación.")
                return

            texto = recognizer.recognize_google(audio, language="es-ES")
            print(f"[MIC] Reconocido: {texto}")

            # Verificar de nuevo antes de emitir la señal (Thread-safe)
            if self._mic_escuchando:
                self.voz_recibida_signal.emit(texto)

        except sr.WaitTimeoutError:
            print("[MIC] Timeout: no se detectó voz.")
            if self._mic_escuchando:
                self.voz_error_signal.emit("Sin señal de voz detectada. Intenta hablar más cerca.")
        except sr.UnknownValueError:
            print("[MIC] No se pudo entender el audio.")
            if self._mic_escuchando:
                self.voz_error_signal.emit("No entendí nada, ¿puedes repetir?")
        except sr.RequestError as e:
            print(f"[MIC] Error de conexión con Google: {e}")
            if self._mic_escuchando:
                self.voz_error_signal.emit(f"Error de conexión con el servicio de voz: {e}")
        except OSError as e:
            print(f"[MIC] Error de dispositivo de audio: {e}")
            if self._mic_escuchando:
                self.voz_error_signal.emit("No se detectó micrófono. Verifica que PyAudio esté instalado.")
        except Exception as e:
            print(f"[MIC] Error inesperado: {e}")
            if self._mic_escuchando:
                self.voz_error_signal.emit(f"Error inesperado: {e}")
                
    def _voz_recibida(self, texto):
        """Callback en hilo principal: pone el texto en el input y restaura el botón."""
        self.input_field.setText(texto)
        self.input_field.setFocus()
        self._restaurar_btn_mic()

    def _voz_error(self, msg):
        """Muestra el error brevemente en el placeholder y restaura el botón."""
        self.input_field.setPlaceholderText(f"⚠ {msg}")
        QTimer.singleShot(2500, lambda: self.input_field.setPlaceholderText(
            "Establecer conexión... (Ctrl + F para enfocar o escribe '/' para comandos)"
        ))
        self._restaurar_btn_mic()

    def _restaurar_btn_mic(self):
        """Vuelve el botón mic a su estado normal."""
        self._mic_escuchando = False
        self.btn_mic.setText("🎙")
        self._sync_estado_indicador("idle")
        self.btn_mic.setStyleSheet("""
            QPushButton { 
                background: #0d0d1a; 
                border-radius: 4px; 
                font-size: 18px; 
                color: #ff7700; 
                border: 1px solid #2a1a0a;
            }
            QPushButton:hover { 
                background: #1a1008; 
                border: 1px solid #ff7700;
            }
        """)


    def enviar(self):
        txt = self.input_field.text().strip()
        if not txt: return
        self.agregar_b(txt, True)
        self.input_field.clear()

        # 📂 INTERCEPCIÓN LIMPIA: Abrir terminal táctica de archivos
        if txt.lower().strip() == "explorador/":
            self.agregar_b("📂 **ABRIENDO TERMINAL DE AUDITORÍA INTEGRADA...**", False)
            QTimer.singleShot(400, self.abrir_explorador_auditoria)
            return  # 👈 CRÍTICO: Ponemos el return para evitar que el mensaje llegue a la IA y se duplique todo

        # Lógica existente de confirmación de movimiento de descargas
        if self.esperando_confirmacion_movimiento:
            self.esperando_confirmacion_movimiento = False
            texto_normalizado = txt.lower().replace("í", "i").strip()
            
            if texto_normalizado in ["si", "afirmativo", "aceptar", "mover"]:
                self.agregar_b("⚡ Inicializando interfaz cyberpunk de transferencia...", False)
                QTimer.singleShot(500, self.abrir_interfaz_movimiento_cyberpunk)
            else:
                self.archivo_descargado_pendiente = None
                self.agregar_b("❌ Archivo preservado en el directorio raíz de descargas.", False)
            return  # 👈 CRÍTICO

        # 🧠 Procesamiento normal de la IA (María) si no es un comando interceptado
        self._incrementar_msg_count()
        self._set_maria_procesando(True)
        self.agregar_b("SYSTEM:// Generando respuesta... ⚡", False)

        # Buscamos la burbuja de carga para eliminarla luego
        burbuja_sistema = self.chat_layout.itemAt(self.chat_layout.count() - 2).widget()
        
        def respuesta_maria():
            if burbuja_sistema:
                burbuja_sistema.deleteLater()

            # 🌟 procesar() vive en procesamiento.py y recibe `self` (esta
            # misma ventana) como el objeto de estado: ultima_url, dialogos,
            # comandos, muteado, etc. ya están todos aquí.
            respuesta = procesar(self, txt)

            self.agregar_b(respuesta, False)
            self.hablar(respuesta)
            self._set_maria_procesando(False)

            guardar_historial(txt, respuesta)

        QTimer.singleShot(400, respuesta_maria)

    def agregar_b(self, t, u):
        nueva_burbuja = Bubble(t, u)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, nueva_burbuja)
        
        # Forzar un scroll inmediato al crearse
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum()))
        
        # Si es María quien responde, conectamos su timer para que desplace el scroll automáticamente
        if not u and hasattr(nueva_burbuja, 'timer_typing'):
            # Cada vez que el timer de la burbuja sume una letra, bajamos el scroll de la ventana
            nueva_burbuja.timer_typing.timeout.connect(
                lambda: self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
            )

    def mostrar_menu(self, posicion):
         menu = QMenu(self)
         menu.setStyleSheet("""
            QMenu { 
                background-color: #2b2e38;       /* BG_PANEL */
                color: #ded8ca;                  /* TEXTO_PRINCIPAL */
                border: 1px solid #3c3f4a;       /* BORDE */
                font-family: 'Segoe UI', sans-serif; 
                font-size: 12px; 
                padding: 6px;
                border-radius: 8px;
            }
            QMenu::item { 
                padding: 6px 28px 6px 14px; 
                border-radius: 4px;
            }
            QMenu::item:selected { 
                background-color: rgba(193, 122, 86, 0.16); /* ACENTO_SUAVE */
                color: #ded8ca; 
            }
            QMenu::separator {
                height: 1px;
                background-color: #33363f;      /* BORDE_SUAVE */
                margin: 4px 0px;
            }
         """)
        
         texto_fs = "🗖 Salir de Pantalla Completa" if self.es_pantalla_completa else "⛶ Pantalla Completa"
         accion_fs = menu.addAction(texto_fs)
         accion_fs.triggered.connect(self.toggle_fullscreen)
        
         texto_mute = "🔊 Desmutear a María" if self.muteado else "🔇 Mutear a María"
         accion_mute = menu.addAction(texto_mute)
         accion_mute.triggered.connect(lambda: self._toggle_mute())
        
         accion_manual = menu.addAction("📖 Ver Manual de Comandos")
         accion_manual.triggered.connect(self.mostrar_manual_desde_menu)
        
         accion_notas = menu.addAction("📝 Abrir Notas")
         accion_notas.triggered.connect(self.abrir_gestor_notas)
        
         accion_explorador = menu.addAction("📁 Abrir Explorador")
         accion_explorador.triggered.connect(self.abrir_explorador_independiente)
        
         menu.addSeparator()
        
         accion_vaciar = menu.addAction("🧹 Vaciar Chat")
         accion_vaciar.triggered.connect(self.vaciar_chat)
        
         accion_cerrar = menu.addAction("❌ Salir")
         accion_cerrar.triggered.connect(self.cerrar_definitivo)
        
         menu.exec_(self.mapToGlobal(posicion))
    
    
    def _toggle_mute(self):
        self.muteado = not self.muteado
        if self.muteado:
            self.agregar_b("María ha sido silenciada. 🤫", False)
        else:
            self.agregar_b("Ya puedo hablar, Administrador.", False)
            self.hablar("Ya puedo hablar, Administrador.")

    def vaciar_chat(self):
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

                # 🌟 NUEVA LÍNEA: Borramos también la memoria interna de María
        self.historial.clear()
        

    def inicializar_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(get_icon())
        self.tray_icon.setToolTip("MARIA // NÚCLEO_DE_SISTEMA")
        
        tray_menu = QMenu()
        accion_mostrar = tray_menu.addAction("👁️ Desplegar Interfaz")
        accion_mostrar.triggered.connect(self.aparecer_desaparecer)

        accion_salir = tray_menu.addAction("🔌 Finalizar Proceso (Terminar)")
        accion_salir.triggered.connect(self.cerrar_definitivo)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.aparecer_desaparecer()

    def cerrar_definitivo(self):
        self.tray_icon.hide()
        QApplication.quit()

    def evaluar_autocompletado(self, texto):
        # Si el texto empieza con "/" mostramos el menú, si no, lo ocultamos
        if texto.startswith("/"):
            texto_busqueda = texto[1:].lower()  # Quita la barra para filtrar

            self.menu_comandos.clear()

            # Filtrar comandos que coincidan con lo que escribe el usuario
            comandos_filtrados = [cmd for cmd in self.lista_comandos_sugeridos if texto_busqueda in cmd.lower()]

            if comandos_filtrados:
                for cmd in comandos_filtrados:
                    item = QListWidgetItem(cmd)
                    self.menu_comandos.addItem(item)

                # Redimensionar el menú según la cantidad de comandos
                alto_item = 35  # Alto aproximado por cada fila
                total_items = len(comandos_filtrados)
                self.menu_comandos.setFixedHeight(min(total_items * alto_item + 6, 180))
                self.menu_comandos.setFixedWidth(self.input_field.width())

                # Posicionar el menú cerca del QLineEdit
                punto_global = self.input_field.mapToGlobal(QPoint(0, 0))
                pos_x = punto_global.x()
                pos_y = punto_global.y() - self.menu_comandos.height() - 5
                if pos_y < 0:
                    pos_y = punto_global.y() + self.input_field.height() + 5

                self.menu_comandos.move(pos_x, pos_y)
                self.menu_comandos.show()
                self.menu_comandos.activateWindow()
            else:
                self.menu_comandos.hide()
        else:
            self.menu_comandos.hide()

    def seleccionar_comando_menu(self, item):
        # Al hacer clic, insertamos el comando en el entry pero NO lo enviamos
        self.input_field.setText(item.text() + " ") # Añade espacio final por si quiere añadir más parámetros
        self.menu_comandos.hide()
        self.input_field.setFocus() # Devuelve el foco al entry

    def on_sidebar_item_clicked(self, item):
        texto = item.text().lower()
        if "notas" in texto:
            self.abrir_gestor_notas()
        elif "explorador" in texto:
            self.abrir_explorador_independiente()
        elif "finanzas" in texto:
            self.abrir_gestor_finanzas()
        else:
            # General: mostrar el manual de comandos o abrir el panel si existe
            try:
                self.mostrar_manual_desde_menu()
            except AttributeError:
                pass
        

    def abrir_gestor_notas(self):
        main_notas.abrir_gestor_notas()

    def abrir_interfaz_movimiento_cyberpunk(self):
        if not self.archivo_descargado_pendiente or not os.path.exists(self.archivo_descargado_pendiente):
            self.agregar_b("⚠️ Error en la matriz de transferencia: El archivo de origen ya no existe.", False)
            return
            
        dialogo = SelectorDestino(self)
        if dialogo.exec_():
            directorios = dialogo.selectedFiles()
            if directorios:
                destino_dir = directorios[0]
                nombre_fichero = os.path.basename(self.archivo_descargado_pendiente)
                ruta_final_destino = os.path.join(destino_dir, nombre_fichero)
                
                try:
                    shutil.move(self.archivo_descargado_pendiente, ruta_final_destino)
                    self.agregar_b(f"💾 **TRANSFERENCIA CONCLUIDA EN NODO:**\n`{ruta_final_destino}`", False)
                    self.hablar("Archivo transferido correctamente.")
                except Exception as e:
                    self.agregar_b(f"⚠️ **FALLO EN LA REUBICACIÓN:** {str(e)}", False)
        
        self.archivo_descargado_pendiente = None

    def abrir_explorador_independiente(self):
        """Delega en el módulo explorador: abre el selector en modo 'auditar carpeta'."""
        explorador.abrir_explorador_independiente(self)

    def abrir_explorador_auditoria(self):
        """Delega en el módulo explorador: abre la terminal de archivos en modo libre."""
        explorador.abrir_explorador_auditoria(self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) 

    from PyQt5.QtCore import QTranslator, QLibraryInfo
    traductor = QTranslator()
    if traductor.load("qtbase_es", QLibraryInfo.location(QLibraryInfo.TranslationsPath)):
        app.installTranslator(traductor)

    window = MariaChat()

    from splash import SplashCyberpunk
    splash = SplashCyberpunk()
    splash.show()

    def lanzar_ventana():
        window.show()
        # Se ejecuta el comando inicial de forma limpia SOLO cuando la interfaz y el Splash ya concluyeron
        if getattr(window, "comando_inicial", None):
            QTimer.singleShot(300, window._aplicar_comando_inicial)
        elif ARGUMENTOS_INICIO and getattr(ARGUMENTOS_INICIO, "comando", None):
            window.comando_inicial = ARGUMENTOS_INICIO.comando
            ARGUMENTOS_INICIO.comando = None
            QTimer.singleShot(300, window._aplicar_comando_inicial)

    splash.iniciar(callback=lanzar_ventana)

    app.aboutToQuit.connect(window.servidor_deck.detener)

    sys.exit(app.exec_())