import os
import random
import tempfile
import unicodedata
import re
import json
from PyQt5.QtWidgets import QFileDialog, QMessageBox

# Ruta del archivo de configuración
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config_usuario.json")

# Formatos de audio soportados
EXTENSIONES_AUDIO = ('.mp3', '.mp4', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.wma')


def _obtener_ruta_musica(parent=None):
    """Lee la ruta de la música desde el JSON. Si no existe, pide al usuario que la seleccione."""
    ruta = None
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                ruta = config.get("ruta_musica")
                if ruta and os.path.exists(ruta):
                    return ruta
        except Exception as e:
            print(f"⚠️ Error leyendo config de música: {e}")

    if parent:
        QMessageBox.information(
            parent, "Configuración Inicial",
            "No se ha encontrado la carpeta de música.\nPor favor, selecciona la carpeta principal donde guardas tu música."
        )
        ruta_seleccionada = QFileDialog.getExistingDirectory(parent, "Selecciona tu carpeta de Música", os.path.expanduser("~"))
        if ruta_seleccionada:
            config = {"ruta_musica": ruta_seleccionada}
            try:
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"❌ Error guardando config de música: {e}")
            return ruta_seleccionada
    return None


def _quitar_acentos(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return texto.replace('’', "'").replace('‘', "'").replace('´', "'")


def _normalizar_texto(texto):
    """Normalización compacta: sin acentos, espacios, guiones ni apóstrofes."""
    texto = _quitar_acentos(texto)
    texto = re.sub(r'[\s\-_]+', '', texto)
    return texto.replace("'", "")


def _tokens(texto):
    """Palabras sueltas normalizadas (para comparar 'Rap' con 'Rap Español')."""
    return set(re.findall(r'[a-z0-9]+', _quitar_acentos(texto)))


def _audios_recursivos(carpeta):
    """Todos los audios de una carpeta, incluyendo TODAS sus subcarpetas."""
    audios = []
    for raiz, _dirs, archivos in os.walk(carpeta):
        for a in archivos:
            if a.lower().endswith(EXTENSIONES_AUDIO):
                audios.append(os.path.join(raiz, a))
    return audios


def _crear_playlist_m3u(ruta_archivo, lista_canciones):
    with open(ruta_archivo, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for cancion in lista_canciones:
            ruta_abs = os.path.abspath(cancion)
            f.write(f"#EXTINF:-1,{os.path.basename(ruta_abs)}\n")
            f.write(f"{ruta_abs}\n")


def _buscar_carpetas(ruta_madre, objetivo_raw, objetivo_norm):
    """
    Devuelve (carpetas_coincidentes, audios).
    1) Coincidencia EXACTA de nombre (en todas las ubicaciones, no solo la primera).
    2) Si no hay, coincidencia por palabras: 'rap' encaja con 'Rap Español'.
    """
    todas = []
    for raiz, dirs, _ in os.walk(ruta_madre):
        for d in dirs:
            todas.append(os.path.join(raiz, d))

    exactas = [c for c in todas if _normalizar_texto(os.path.basename(c)) == objetivo_norm]

    # Solo nos quedamos con las que realmente contienen audio
    def con_audio(lista):
        res, audios = [], []
        for c in lista:
            a = _audios_recursivos(c)
            if a:
                res.append(c)
                audios.extend(a)
        return res, audios

    carpetas, audios = con_audio(exactas)
    if carpetas:
        return carpetas, list(set(audios))

    tokens_obj = _tokens(objetivo_raw)
    if tokens_obj:
        parciales = [c for c in todas if tokens_obj.issubset(_tokens(os.path.basename(c)))]
        carpetas, audios = con_audio(parciales)
        if carpetas:
            return carpetas, list(set(audios))

    return [], []


def reproducir_musica_por_ruta_comando(ruta_comando, parent=None):
    try:
        ruta_madre = _obtener_ruta_musica(parent)
        if not ruta_madre:
            return "No se ha seleccionado ninguna carpeta de música. Operación cancelada."

        partes = [p.strip() for p in ruta_comando.split('/') if p.strip()]

        # Caso: bóveda completa
        if not partes or (len(partes) == 1 and partes[0].lower() in ["gran boveda musical 2", "boveda", "todo"]):
            todos = _audios_recursivos(ruta_madre)
            if todos:
                random.shuffle(todos)
                ruta_m3u = os.path.join(tempfile.gettempdir(), "maria_boveda_playlist.m3u")
                _crear_playlist_m3u(ruta_m3u, todos)
                os.startfile(ruta_m3u)
                return f"Accediendo a la bóveda principal. Reproducción aleatoria de toda tu música ({len(todos)} archivos)."
            return "Error: El directorio de la bóveda de medios se encuentra vacío."

        objetivo_raw = partes[-1]
        objetivo_norm = _normalizar_texto(objetivo_raw)
        print(f"🎵 Buscando: '{objetivo_raw}' → normalizado: '{objetivo_norm}'")

        # PASO 1: ¿Es una CARPETA? (idioma / género / artista) → se carga ENTERA, con todas sus subcarpetas
        carpetas, audios_carpeta = _buscar_carpetas(ruta_madre, objetivo_raw, objetivo_norm)
        if audios_carpeta:
            print(f"📂 Carpeta(s) encontrada(s): {carpetas} → {len(audios_carpeta)} archivos")
            random.shuffle(audios_carpeta)
            ruta_m3u = os.path.join(tempfile.gettempdir(), "maria_carpeta_playlist.m3u")
            _crear_playlist_m3u(ruta_m3u, audios_carpeta)
            os.startfile(ruta_m3u)
            return f"Directorio **{objetivo_raw}** identificado con éxito. Archivos multimedia sincronizados en el reproductor maestro."

        # PASO 2: Canción suelta. Primero coincidencias exactas; solo si no hay, las aproximadas.
        exactas, aproximadas = [], []
        for raiz, _dirs, archivos in os.walk(ruta_madre):
            for audio in archivos:
                if not audio.lower().endswith(EXTENSIONES_AUDIO):
                    continue
                nombre_norm = _normalizar_texto(os.path.splitext(audio)[0])
                ruta_audio = os.path.join(raiz, audio)
                if objetivo_norm == nombre_norm:
                    exactas.append(ruta_audio)
                elif len(objetivo_norm) >= 4 and objetivo_norm in nombre_norm:
                    aproximadas.append(ruta_audio)
                elif len(objetivo_raw.split()) > 1 and all(p in nombre_norm for p in _quitar_acentos(objetivo_raw).split()):
                    aproximadas.append(ruta_audio)

        coincidencias = list(set(exactas)) or list(set(aproximadas))

        if coincidencias:
            elegida = random.choice(coincidencias)
            print(f"✅ Reproduciendo canción: {elegida}")
            carpeta_padre = os.path.dirname(elegida)
            resto = [
                os.path.join(carpeta_padre, f) for f in os.listdir(carpeta_padre)
                if f.lower().endswith(EXTENSIONES_AUDIO) and os.path.join(carpeta_padre, f) != elegida
            ]
            ruta_m3u = os.path.join(tempfile.gettempdir(), "maria_cancion_playlist.m3u")
            _crear_playlist_m3u(ruta_m3u, [elegida] + resto)
            os.startfile(ruta_m3u)
            return f"¡Encontré tu canción! Reproduciendo **{objetivo_raw}** y cargando el resto del álbum. "

        return f"No encontré '{objetivo_raw}' en tu bóveda musical. ¿Seguro que está en la carpeta configurada? "

    except Exception as e:
        print(f"❌ Error en música: {e}")
        return "Tuve un problema técnico al buscar la música. "