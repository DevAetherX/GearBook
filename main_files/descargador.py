import os
import re
import yt_dlp
from PyQt5.QtCore import QThread, pyqtSignal

class HiloFormatos(QThread):
    """Hilo para extraer resoluciones disponibles sin congelar la UI"""
    resultado = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            # Desactivamos advertencias para evitar el spam en consola
            opciones = {'quiet': True, 'no_warnings': True, 'logger': None}
            with yt_dlp.YoutubeDL(opciones) as ydl:
                info = ydl.extract_info(self.url, download=False)
                formats = info.get('formats', [])
                resoluciones = set()
                for f in formats:
                    height = f.get('height')
                    width = f.get('width')
                    if height and width and height >= 360:
                        resoluciones.add(f"{width}x{height}")
                
                lista_res = sorted(list(resoluciones), key=lambda x: int(x.split('x')[1]), reverse=True)
                self.resultado.emit(lista_res)
        except Exception as e:
            self.error.emit(str(e))


class HiloDescarga(QThread):
    progreso = pyqtSignal(int, str) # Emitiremos porcentaje (int) y texto descriptivo (str)
    completado = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, url, formato, resolucion=None):
        super().__init__()
        self.url = url
        self.formato = formato
        self.resolucion = resolucion

    def progress_hook(self, d):
        """Atrapa el estado interno de yt_dlp y emite las señales para la UI"""
        if d['status'] == 'downloading':
            try:
                # yt_dlp a veces usa 'total_bytes' o 'total_bytes_estimate'
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                if total > 0:
                    descargado = d.get('downloaded_bytes', 0)
                    porcentaje = int((descargado / total) * 100)
                    vel = d.get('_speed_str', 'N/A')
                    eta = d.get('_eta_str', 'N/A')
                    # Removemos códigos ANSI de color que yt_dlp inserta a veces
                    vel = re.sub(r'\x1b\[[0-9;]*m', '', vel)
                    eta = re.sub(r'\x1b\[[0-9;]*m', '', eta)
                    
                    self.progreso.emit(porcentaje, f"DOWNLOADING... Vel: {vel} | ETA: {eta}")
            except Exception:
                pass
        
    def run(self):
        try:
            if self.formato == 'mp3':
                self.descargar_mp3()
            else:
                self.descargar_mp4()
        except Exception as e:
            self.error.emit(f"Error en la descarga: {str(e)}")
    
    def descargar_mp4(self):
     # Crear la carpeta si no existe
     download_dir = os.path.expanduser('~/Downloads/Asistente-Descargas/')
     os.makedirs(download_dir, exist_ok=True)
    
     # 🌟 CORRECCIÓN AQUÍ: Definimos un formato robusto para cuando no hay resolución seleccionada
     if self.resolucion:
        alto = self.resolucion.split("x")[1]
        formato_seleccionado = f'bestvideo[height<={alto}]+bestaudio/best[height<={alto}]'
     else:
        # Esto busca el mejor video absoluto y el mejor audio, y le dice que prefiera MP4/m4a si es posible
        formato_seleccionado = 'bestvideo+bestaudio/best'

     opciones = {
        'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
        'format': formato_seleccionado,
        'merge_output_format': 'mp4',  # Esto une el video y el audio en un archivo .mp4
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [self.progress_hook],
    }
     with yt_dlp.YoutubeDL(opciones) as ydl:
        info = ydl.extract_info(self.url, download=True)
        titulo = info.get('title', 'Desconocido')
        # Obtenemos la extensión real guardada por yt_dlp o forzamos mp4 ya que está en merge_output_format
        ext = info.get('ext', 'mp4')
        ruta_final_archivo = os.path.join(download_dir, f"{titulo}.{ext}")
        self.completado.emit(f"VIDEO_OK|{ruta_final_archivo}")
    
    

    def descargar_mp3(self):
     download_dir = os.path.expanduser('~/Downloads/Asistente-Descargas/')
     os.makedirs(download_dir, exist_ok=True)
    
     opciones = {
        'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',  # <--- Cambiado de '192' a '320'
        }],
        'progress_hooks': [self.progress_hook],
        'quiet': True,
        'no_warnings': True,
    }
     with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(self.url, download=True)
            titulo = info.get('title', 'Desconocido')
            ruta_final_archivo = os.path.join(download_dir, f"{titulo}.mp3")
            self.completado.emit(f"AUDIO_OK|{ruta_final_archivo}")

    def obtener_resoluciones_disponibles(self, url):
            try:
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    formats = info.get('formats', [])
                    resoluciones = set()
                    for f in formats:
                        height = f.get('height')
                        width = f.get('width')
                        if height and width and height >= 360:
                            resoluciones.add(f"{width}x{height}")
                    return sorted(list(resoluciones), key=lambda x: int(x.split('x')[1]), reverse=True)
            except Exception as e:
                print(f"Error al obtener resoluciones: {e}")
                return None
    
def descargar_video_interactivo(self, url):
            if not url.startswith(('http://', 'https://')):
                return "La URL no es válida, cielo."
    
            
            if 'youtube.com' in url or 'youtu.be' in url:
                plataforma = "YouTube"
            elif 'twitter.com' in url or 'x.com' in url:
                plataforma = "X/Twitter"
            else:
                return "Por ahora solo puedo descargar de YouTube y X/Twitter, bombón. 🎬"
            
            self.descarga_pendiente = {
                'url': url,
                'plataforma': plataforma,
                'paso': 1,
                'formato': None,
                'resolucion': None
            }
            return f"📥 Voy a descargar desde {plataforma}.\n\n¿Qué formato prefieres?\n• MP4 (video)\n• MP3 (solo audio)"
    
        
    
def procesar_descarga_respuesta(self, texto):
            # Si hay un mensaje pendiente de la descarga, mostrarlo primero
            if self.respuesta_descarga:
                mensaje = self.respuesta_descarga
                self.respuesta_descarga = None
                return mensaje
            
            if not self.descarga_pendiente:
                return None
            
            estado = self.descarga_pendiente
            texto = texto.lower().strip()
            
            if estado['paso'] == 1:
                if 'mp4' in texto or 'video' in texto:
                    estado['formato'] = 'mp4'
                    self.hilo_descarga = HiloDescarga(estado['url'], 'mp4')
                    self.hilo_descarga.completado.connect(lambda msg: self.set_respuesta_descarga(msg))
                    self.hilo_descarga.error.connect(lambda msg: self.set_respuesta_descarga(msg))
                    self.hilo_descarga.progreso.connect(lambda p, t: self.descarga_progreso_signal.emit(p, t))
                    self.hilo_descarga.start()
                    self.descarga_pendiente = None
                    return "📥 Descargando video MP4... Dame un momento."
                elif 'mp3' in texto or 'audio' in texto:
                    estado['formato'] = 'mp3'
                    self.hilo_descarga = HiloDescarga(estado['url'], 'mp3')
                    self.hilo_descarga.completado.connect(lambda msg: self.set_respuesta_descarga(msg))
                    self.hilo_descarga.error.connect(lambda msg: self.set_respuesta_descarga(msg))
                    self.hilo_descarga.progreso.connect(lambda p, t: self.descarga_progreso_signal.emit(p, t))
                    self.hilo_descarga.start()
                    self.descarga_pendiente = None
                    return f"🎵 Descargando audio MP3... Dame un momento."
                else:
                    return "¿MP4 o MP3?"
    
            elif estado['paso'] == 2:
                if 'mejor' in texto:
                    resoluciones = self.obtener_resoluciones_disponibles(estado['url'])
                    resolucion_seleccionada = resoluciones[0] if resoluciones else '1920x1080'
                else:
                    match = re.search(r'(\d{3,4})x(\d{3,4})', texto)
                    if not match:
                        return "Escribe la resolución como '1920x1080' o 'mejor'"
                    resolucion_seleccionada = f"{match.group(1)}x{match.group(2)}"
                
                self.hilo_descarga = HiloDescarga(estado['url'], 'mp4', resolucion_seleccionada)
                self.hilo_descarga.completado.connect(lambda msg: self.set_respuesta_descarga(msg))
                self.hilo_descarga.error.connect(lambda msg: self.set_respuesta_descarga(msg))
                self.hilo_descarga.start()
                self.descarga_pendiente = None
                return f"📥 Descargando video en {resolucion_seleccionada}..."
            
            return None
    
        # NUEVO MÉTODO AUXILIAR PARA LA INTERFAZ
def notificar_resoluciones_ui(self, resoluciones):
            """Muestra las resoluciones en el chat cuando el hilo termina"""
            if resoluciones:
                lista_res = "\n".join([f"• {res}" for res in resoluciones[:5]])
                msg = f"¡Listo, corazón! Aquí tienes las resoluciones disponibles:\n{lista_res}\n\n¿Cuál prefieres? (Ej: 1920x1080) o escribe 'mejor'"
            else:
                msg = "¿Qué resolución prefieres? (Ej: 1920x1080) o escribe 'mejor'"
            
            self.set_respuesta_descarga(msg)
      
def set_respuesta_descarga(self, mensaje):
            self.respuesta_descarga = mensaje
            self.hablar(mensaje)
            self.descarga_finalizada_signal.emit(mensaje)