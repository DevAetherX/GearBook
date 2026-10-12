import os
import socket
import subprocess
import sys
import time
from PyQt5.QtCore import QThread, pyqtSignal

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DEL "PUERTO" DE COMUNICACIÓN
# ═══════════════════════════════════════════════════════════════
HOST = "127.0.0.1"           # Solo escucha conexiones locales
PUERTO = 57432                # Puerto de comunicación local
TIMEOUT_CLIENTE = 1.5         # Segundos de espera para el socket


def construir_argumentos_lanzamiento(comando):
    """Prepara los argumentos para abrir María con un comando inicial."""
    carpeta_proyecto = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    ruta_main = os.path.join(carpeta_proyecto, "main.py")
    
    python_exe = sys.executable if sys.executable else "python"
    # Intentar usar pythonw.exe si existe para evitar consolas flotantes descolgadas
    if python_exe.endswith("python.exe"):
        pythonw = python_exe[:-10] + "pythonw.exe"
        if os.path.exists(pythonw):
            python_exe = pythonw

    return [python_exe, ruta_main, "--comando", comando]


def lanzar_maria(comando):
    """Arranca María en un nuevo proceso si no estaba abierta."""
    carpeta_proyecto = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    try:
        creationflags = 0
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | getattr(subprocess, 'DETACHED_PROCESS', 0x00000008)
        
        subprocess.Popen(
            construir_argumentos_lanzamiento(comando),
            cwd=carpeta_proyecto,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
            close_fds=True
        )
        print(f"🚀 Proceso de María iniciado con el comando: {comando}")
        return True
    except Exception as e:
        print(f"⚠️ [StreamDeck] No se pudo lanzar María automáticamente: {e}")
        return False


# ═══════════════════════════════════════════════════════════════
# 1) SERVIDOR (vive dentro de María, corre en segundo plano)
# ═══════════════════════════════════════════════════════════════
class ServidorStreamDeck(QThread):
    comando_recibido = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._activo = True
        self._socket_servidor = None

    def run(self):
        try:
            self._socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket_servidor.bind((HOST, PUERTO))
            self._socket_servidor.listen(5)
            print(f"🎛️ [StreamDeck] Servidor escuchando en {HOST}:{PUERTO}")

            while self._activo:
                try:
                    cliente, _ = self._socket_servidor.accept()
                except OSError:
                    break

                with cliente:
                    datos = cliente.recv(1024)
                    if datos:
                        comando = datos.decode("utf-8", errors="ignore").strip()
                        if comando:
                            self.comando_recibido.emit(comando)
                    try:
                        cliente.sendall(b"OK")
                    except OSError:
                        pass

        except Exception as e:
            print(f"⚠️ [StreamDeck] Error en el servidor: {e}")

    def detener(self):
        self._activo = False
        try:
            if self._socket_servidor:
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((HOST, PUERTO))
        except Exception:
            pass
        self.wait(1000)


# ═══════════════════════════════════════════════════════════════
# 2) DESPACHADOR DE COMANDOS
# ═══════════════════════════════════════════════════════════════
def manejar_comando(ventana, comando):
    comando = comando.strip()

    if comando == "TOGGLE":
        ventana.trigger_mostrar_ocultar.emit()

    elif comando == "EXPLORADOR":
        _asegurar_visible(ventana)
        ventana.abrir_explorador_auditoria()

    elif comando == "MUTE_TOGGLE":
        ventana._toggle_mute()

    elif comando == "PANEL_TOGGLE":
        ventana.toggle_panel()

    elif comando in ("NOTAS", "NOTAS_TOGGLE"):
        _asegurar_visible(ventana)
        ventana.abrir_gestor_notas()

    elif comando in ("FINANZAS", "FINANZAS_TOGGLE"):
        _asegurar_visible(ventana)
        ventana.abrir_gestor_finanzas()

    elif comando.startswith("PREFILL:"):
        texto = comando[len("PREFILL:"):]
        _asegurar_visible(ventana)
        ventana.input_field.setText(texto)
        ventana.input_field.setFocus()
        ventana.input_field.setCursorPosition(len(texto))

    elif comando.startswith("SEND:"):
        texto = comando[len("SEND:"):]
        _asegurar_visible(ventana)
        ventana.input_field.setText(texto)
        ventana.enviar()

    else:
        print(f"⚠️ [StreamDeck] Comando desconocido: {comando}")


def _asegurar_visible(ventana):
    if not ventana.isVisible() or ventana.windowOpacity() < 0.1:
        ventana.trigger_mostrar_ocultar.emit()


# ═══════════════════════════════════════════════════════════════
# 3) CLIENTE (lo que ejecuta cada tecla del Stream Deck)
# ═══════════════════════════════════════════════════════════════
def enviar_comando(comando, host=HOST, puerto=PUERTO, timeout=TIMEOUT_CLIENTE):
    comando = comando.strip()
    if not comando:
        return False

    # 1. Si María ya está abierta, responderá inmediatamente por el socket
    try:
        with socket.create_connection((host, puerto), timeout=timeout) as s:
            s.sendall(comando.encode("utf-8"))
            s.recv(64)
        return True
    except (ConnectionRefusedError, OSError):
        pass

    # 2. Si María está cerrada, la arrancamos pasándole el comando inicial vía CLI
    print("⚠️ María no está iniciada. Arrancando sistema...")
    return lanzar_maria(comando)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python stream_deck.py <COMANDO>")
        sys.exit(1)

    comando_cli = " ".join(sys.argv[1:])
    enviar_comando(comando_cli)