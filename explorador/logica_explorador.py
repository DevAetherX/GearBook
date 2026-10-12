import os
import string
import shutil
import threading
import ctypes
import sys
import json
from ctypes import wintypes

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QLabel, QScrollArea, QPushButton
from PyQt5.QtGui import QFont, QColor, QPixmap
from PyQt5.QtCore import Qt

from main_files.organizador import organizar_carpeta
import win32com.client

# ─────────────────────────────────────────────────────────────
# 🎨 Paleta cálida (misma que el cuaderno y el explorador)
# ─────────────────────────────────────────────────────────────
BG_APP       = "#242730"
BG_INPUT     = "#1d2028"
BORDE        = "#3c3f4a"
TEXTO        = "#ded8ca"
TEXTO_SEC    = "#8f8b83"
ACENTO       = "#c17a56"
ACENTO_HOVER = "#d38f6c"
FUENTE_UI    = "'Segoe UI', Arial, sans-serif"
FUENTE_META  = "'Consolas', 'Courier New', monospace"


# ─────────────────────────────────────────────────────────────
# 🛠️ Conexión nativa con el Shell de Windows
# ─────────────────────────────────────────────────────────────
class SHFILEOPSTRUCT(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("wFunc", wintypes.UINT),
        ("pFrom", wintypes.LPCWSTR),
        ("pTo", wintypes.LPCWSTR),
        ("fFlags", wintypes.WORD),
        ("fAnyOperationsAborted", wintypes.BOOL),
        ("hNameMappings", wintypes.LPVOID),
        ("lpszProgressTitle", wintypes.LPCWSTR),
    ]

FO_DELETE = 3
FOF_ALLOWUNDO = 0x0040       # Mover a la papelera nativa
FOF_NOCONFIRMATION = 0x0010  # Sin confirmación de Windows


def borrar_elemento_nativo(ruta):
    """Mueve un archivo o carpeta a la Papelera de Reciclaje de Windows."""
    ruta_normalizada = os.path.abspath(ruta)
    ruta_doble_nulo = ruta_normalizada + "\0"
    fileop = SHFILEOPSTRUCT()
    fileop.hwnd = None
    fileop.wFunc = FO_DELETE
    fileop.pFrom = ruta_doble_nulo
    fileop.pTo = None
    fileop.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION
    resultado = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(fileop))
    return resultado == 0


def crear_carpeta_nueva(ruta_base):
    """Crea 'Nueva_Carpeta' (o 'Nueva_Carpeta_N') dentro de ruta_base."""
    nueva_ruta = os.path.join(ruta_base, "Nueva_Carpeta")
    count = 1
    while os.path.exists(nueva_ruta):
        nueva_ruta = os.path.join(ruta_base, f"Nueva_Carpeta_{count}")
        count += 1
    os.makedirs(nueva_ruta, exist_ok=True)
    return nueva_ruta


def reproducir_archivo(ruta):
    """Reproduce un archivo con el reproductor predeterminado del sistema."""
    try:
        if os.path.exists(ruta):
            os.startfile(ruta)
            return True, f"Reproduciendo: {ruta}"
        return False, None
    except Exception as e:
        return False, f"Error al reproducir: {e}"


def listar_discos_locales():
    """Devuelve los discos duros locales detectados (C:, D:, etc.)."""
    unidades_validas = []
    for letra in string.ascii_uppercase:
        ruta_disco = f"{letra}:\\"
        if os.path.exists(ruta_disco):
            unidades_validas.append(ruta_disco)
    discos = []
    for disco in unidades_validas:
        espacio_str = "Protegido o desconocido"
        try:
            total, usado, libre = shutil.disk_usage(disco)
            gb_libres = libre // (1024 ** 3)
            espacio_str = f"{gb_libres} GB libres"
        except Exception:
            pass
        discos.append({
            "ruta": disco,
            "nombre": f"Disco local ({disco.strip(chr(92))})",
            "tipo": "Disco duro",
            "espacio": espacio_str,
        })
    return discos


def listar_items_papelera():
    """Vuelca la papelera real con la API Shell de Windows.
    Devuelve (items, error)."""
    items = []
    error = None
    try:
        shell = win32com.client.Dispatch("Shell.Application")
        folder_papelera = shell.Namespace(10)  # 10 = Papelera de reciclaje
        if folder_papelera is not None:
            for item in folder_papelera.Items():
                nombre = item.Name
                ruta_origen = folder_papelera.GetDetailsOf(item, 1) or "Desconocida"
                detalles_extra = folder_papelera.GetDetailsOf(item, 2) or "Desconocido"
                items.append({
                    "nombre": nombre,
                    "origen": ruta_origen,
                    "detalles": detalles_extra,
                    "com_item": item,
                })
    except Exception as e:
        error = f"Error al leer la papelera: {e}"
    return items, error


def restaurar_item_papelera(win_item):
    """Restaura un elemento de la papelera a su ubicación original."""
    try:
        win_item.InvokeVerb("undelete")
        return True, "Elemento restaurado en su ubicación original."
    except Exception as e:
        return False, f"Error al restaurar: {e}"


def destruir_item_papelera(win_item):
    """Elimina definitivamente un elemento de la papelera."""
    try:
        win_item.InvokeVerb("delete")
        return True, "Elemento eliminado definitivamente."
    except Exception as e:
        return False, f"Error al eliminar: {e}"


def ejecutar_ordenar(parent_app, ruta):
    """Lanza en segundo plano la organización automática de una carpeta."""
    if os.path.exists(ruta) and parent_app:
        threading.Thread(target=organizar_carpeta, args=(ruta,), daemon=True).start()
        parent_app.hablar("Organizando carpeta…")
        return True
    return False


# ─────────────────────────────────────────────────────────────
# 📋 Portapapeles interno (Copiar / Cortar / Pegar)
# ─────────────────────────────────────────────────────────────
_portapapeles = {"ruta": None, "modo": None}  # modo: "COPIAR" | "CORTAR"


def copiar_al_portapapeles(ruta):
    if not ruta or not os.path.exists(ruta):
        return False, "El elemento seleccionado ya no existe."
    _portapapeles["ruta"] = ruta
    _portapapeles["modo"] = "COPIAR"
    return True, f"Copiado al portapapeles: {ruta}"


def cortar_al_portapapeles(ruta):
    if not ruta or not os.path.exists(ruta):
        return False, "El elemento seleccionado ya no existe."
    _portapapeles["ruta"] = ruta
    _portapapeles["modo"] = "CORTAR"
    return True, f"Cortado al portapapeles: {ruta}"


def hay_elemento_en_portapapeles():
    ruta = _portapapeles["ruta"]
    return bool(ruta) and os.path.exists(ruta)


def pegar_desde_portapapeles(carpeta_destino):
    """Ejecuta la operación pendiente (copiar o cortar) sobre carpeta_destino."""
    origen = _portapapeles["ruta"]
    modo = _portapapeles["modo"]
    if not origen or not os.path.exists(origen):
        return False, "No hay ningún elemento en el portapapeles o ya no existe."
    if not carpeta_destino or not os.path.isdir(carpeta_destino):
        return False, "El destino no es una carpeta válida."
    nombre = os.path.basename(os.path.normpath(origen))
    destino = os.path.join(carpeta_destino, nombre)
    if os.path.abspath(destino) == os.path.abspath(origen):
        return False, "El origen y el destino son la misma carpeta."
    if os.path.exists(destino):
        es_carpeta = os.path.isdir(origen)
        base, ext = os.path.splitext(nombre)
        if es_carpeta:
            base, ext = nombre, ""
        count = 1
        while os.path.exists(destino):
            destino = os.path.join(carpeta_destino, f"{base}_copia_{count}{ext}")
            count += 1
    try:
        if modo == "COPIAR":
            if os.path.isdir(origen):
                shutil.copytree(origen, destino)
            else:
                shutil.copy2(origen, destino)
            return True, f"Copiado en: {destino}"
        elif modo == "CORTAR":
            shutil.move(origen, destino)
            _portapapeles["ruta"] = None
            _portapapeles["modo"] = None
            return True, f"Movido a: {destino}"
        return False, "Operación de portapapeles desconocida."
    except Exception as e:
        return False, f"Error al pegar: {e}"


# ─────────────────────────────────────────────────────────────
# 🧭 Navegación (Subir / Historial Atrás-Adelante)
# ─────────────────────────────────────────────────────────────
def obtener_carpeta_padre(ruta):
    if not ruta:
        return ruta
    padre = os.path.dirname(os.path.normpath(ruta))
    return padre if padre else ruta


class HistorialNavegacion:
    """Historial de navegación al estilo navegador (pilas atrás/adelante)."""
    def __init__(self, ruta_inicial=None):
        self._pila_atras = []
        self._pila_adelante = []
        self._actual = ruta_inicial

    def visitar(self, destino):
        if self._actual is not None and self._actual != destino:
            self._pila_atras.append(self._actual)
        self._actual = destino
        self._pila_adelante.clear()

    def retroceder(self):
        if not self._pila_atras:
            return None
        self._pila_adelante.append(self._actual)
        self._actual = self._pila_atras.pop()
        return self._actual

    def avanzar(self):
        if not self._pila_adelante:
            return None
        self._pila_atras.append(self._actual)
        self._actual = self._pila_adelante.pop()
        return self._actual

    def puede_retroceder(self):
        return len(self._pila_atras) > 0

    def puede_avanzar(self):
        return len(self._pila_adelante) > 0

    def actual(self):
        return self._actual


# ─────────────────────────────────────────────────────────────
# 🗂️ Sesiones de pestañas
# ─────────────────────────────────────────────────────────────
def _ruta_archivo_sesiones():
    carpeta_config = os.path.join(os.path.expanduser("~"), ".gearbook")
    os.makedirs(carpeta_config, exist_ok=True)
    return os.path.join(carpeta_config, "sesiones_pestanas.json")


def guardar_sesion(nombre_sesion, pestanas):
    if not nombre_sesion or not nombre_sesion.strip():
        return False, "La sesión necesita un nombre válido."
    if not pestanas:
        return False, "No hay pestañas que guardar."
    nombre_sesion = nombre_sesion.strip()
    ruta_archivo = _ruta_archivo_sesiones()
    datos = {}
    if os.path.exists(ruta_archivo):
        try:
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except Exception:
            datos = {}
    try:
        datos[nombre_sesion] = pestanas
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        return True, f"Sesión guardada: {nombre_sesion} ({len(pestanas)} pestañas)."
    except Exception as e:
        return False, f"Error al guardar la sesión: {e}"


def cargar_sesion(nombre_sesion):
    """Devuelve (pestanas, error)."""
    ruta_archivo = _ruta_archivo_sesiones()
    if not os.path.exists(ruta_archivo):
        return None, "No existe ninguna sesión guardada todavía."
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except Exception as e:
        return None, f"Error al leer las sesiones: {e}"
    if nombre_sesion not in datos:
        return None, f"La sesión '{nombre_sesion}' no existe."
    return datos[nombre_sesion], None


def listar_sesiones():
    ruta_archivo = _ruta_archivo_sesiones()
    if not os.path.exists(ruta_archivo):
        return []
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return sorted(datos.keys())
    except Exception:
        return []


def eliminar_sesion(nombre_sesion):
    ruta_archivo = _ruta_archivo_sesiones()
    if not os.path.exists(ruta_archivo):
        return False, "No hay sesiones guardadas."
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            datos = json.load(f)
        if nombre_sesion not in datos:
            return False, f"La sesión '{nombre_sesion}' no existe."
        del datos[nombre_sesion]
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        return True, f"Sesión eliminada: {nombre_sesion}"
    except Exception as e:
        return False, f"Error al eliminar la sesión: {e}"


# ─────────────────────────────────────────────────────────────
# 👁️ Visor de archivos (paleta cálida, sin estética cyberpunk)
# ─────────────────────────────────────────────────────────────
def obtener_tipo_visor(ruta):
    if not os.path.exists(ruta) or os.path.isdir(ruta):
        return False, None, None
    ext = os.path.splitext(ruta)[1].lower()
    extensiones_texto = {'.txt', '.py', '.json', '.log', '.ini', '.cfg', '.md', '.bat', '.sh', '.html', '.css'}
    extensiones_imagen = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    if ext in extensiones_texto:
        return True, "TEXTO", None
    elif ext in extensiones_imagen:
        return True, "IMAGEN", None
    return False, None, None


def leer_archivo_texto_seguro(ruta):
    """Abre un archivo de texto e intenta decodificarlo de forma segura."""
    try:
        with open(ruta, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        return f"No se pudo leer el archivo.\nMotivo: {e}"


class VisorArchivos(QDialog):
    def __init__(self, ruta, tipo_visualizacion, parent=None):
        super().__init__(parent)
        self.ruta = ruta
        self.tipo_visualizacion = tipo_visualizacion

        nombre_archivo = os.path.basename(ruta)
        self.setWindowTitle(f"Visor — {nombre_archivo}")
        self.resize(800, 600)
        self._inicializar_ui()
        self._aplicar_estilos()
        self._cargar_contenido()

    def _inicializar_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.lbl_info = QLabel(f"Archivo: {self.ruta}")
        layout.addWidget(self.lbl_info)

        if self.tipo_visualizacion == "TEXTO":
            self.visor_texto = QTextEdit()
            self.visor_texto.setReadOnly(True)
            layout.addWidget(self.visor_texto)
        elif self.tipo_visualizacion == "IMAGEN":
            self.contenedor_scroll = QScrollArea()
            self.contenedor_scroll.setWidgetResizable(True)
            self.lbl_imagen = QLabel()
            self.lbl_imagen.setAlignment(Qt.AlignCenter)
            self.contenedor_scroll.setWidget(self.lbl_imagen)
            layout.addWidget(self.contenedor_scroll)

        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.setCursor(Qt.PointingHandCursor)
        self.btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(self.btn_cerrar, 0, Qt.AlignRight)

    def _cargar_contenido(self):
        if self.tipo_visualizacion == "TEXTO":
            contenido = leer_archivo_texto_seguro(self.ruta)
            self.visor_texto.setPlainText(contenido)
        elif self.tipo_visualizacion == "IMAGEN":
            pixmap = QPixmap(self.ruta)
            if not pixmap.isNull():
                self.lbl_imagen.setPixmap(
                    pixmap.scaled(750, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                self.lbl_imagen.setText("No se pudo cargar la imagen: está corrupta o no es legible.")

    def _aplicar_estilos(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG_APP};
                border: 1px solid {BORDE};
                border-radius: 10px;
            }}
            QWidget {{
                background-color: {BG_APP}; color: {TEXTO};
                font-family: {FUENTE_UI}; font-size: 12px;
            }}
            QLabel {{
                color: {TEXTO_SEC}; font-family: {FUENTE_META}; font-size: 11px;
                background: transparent; border: none;
            }}
            QTextEdit {{
                background-color: {BG_INPUT};
                border: 1px solid {BORDE};
                border-radius: 6px;
                color: {TEXTO};
                font-family: {FUENTE_META};
                font-size: 12px;
                padding: 6px;
                selection-background-color: {ACENTO};
            }}
            QScrollArea {{
                background-color: {BG_INPUT};
                border: 1px solid {BORDE};
                border-radius: 6px;
            }}
            QPushButton {{
                background-color: {ACENTO};
                color: {BG_APP};
                border: none;
                border-radius: 6px;
                padding: 6px 18px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background-color: {ACENTO_HOVER}; }}
        """)