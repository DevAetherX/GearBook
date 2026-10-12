import threading
import os

# Ocultar el mensaje de bienvenida de pygame en consola (debe ir ANTES del import)
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import soundfile as sf
# 🌟 kokoro_onnx / onnxruntime se importan de forma perezosa (ver _cargar_kokoro),
# para que un fallo ahí NO impida arrancar el programa completo.

# 📍 Rutas ABSOLUTAS basadas en la ubicación de este archivo, para que
# funcione sin importar desde qué carpeta se lance main.py.
_DIR_MODELOS = os.path.dirname(os.path.abspath(__file__))
RUTA_MODELO_ONNX = os.path.join(_DIR_MODELOS, "kokoro-v1.0.onnx")   # 👈 AJUSTA el nombre exacto de tu archivo
RUTA_VOCES = os.path.join(_DIR_MODELOS, "voices-v1.0.bin")           # 👈 AJUSTA el nombre exacto de tu archivo


class HiloVozNeuronal(threading.Thread):
    _kokoro_instance = None
    _kokoro_error = None

    def __init__(self, texto, parent=None):
        super().__init__(parent)
        self.texto = texto
        self.archivo_temporal = "v_temp.wav"

    @classmethod
    def _cargar_kokoro(cls):
     if cls._kokoro_instance is not None:
        return cls._kokoro_instance
     if cls._kokoro_error is not None:
        return None
     try:
        import faulthandler
        faulthandler.enable()  # por si crasha aquí
        
        if not os.path.exists(RUTA_MODELO_ONNX):
            raise FileNotFoundError(f"No se encuentra el modelo: {RUTA_MODELO_ONNX}")
        if not os.path.exists(RUTA_VOCES):
            raise FileNotFoundError(f"No se encuentra el archivo de voces: {RUTA_VOCES}")
        
        from kokoro_onnx import Kokoro
        cls._kokoro_instance = Kokoro(RUTA_MODELO_ONNX, RUTA_VOCES)
        return cls._kokoro_instance
     except Exception as e:
        cls._kokoro_error = str(e)
        print(f"⚠️ No se pudo cargar el motor de voz Kokoro: {e}")
        import traceback
        traceback.print_exc()
        return None

    def run(self):
        kokoro = self._cargar_kokoro()
        if kokoro is None:
            print("⚠️ Voz local no disponible; se omite la locución.")
            return
        try:
            samples, sample_rate = kokoro.create(
                self.texto,
                voice="af_heart",
                speed=1.0,
                lang="es"
            )
            sf.write(self.archivo_temporal, samples, sample_rate)

            pygame.mixer.init()
            pygame.mixer.music.load(self.archivo_temporal)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            pygame.mixer.music.unload()
            pygame.mixer.quit()

            if os.path.exists(self.archivo_temporal):
                os.remove(self.archivo_temporal)

        except Exception as e:
            print(f"Error en voz local Kokoro: {e}")