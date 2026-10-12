import os
import json
from datetime import datetime, date, timedelta

RUTA_ARCHIVOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archivos")
RUTA_PAPELERA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "papelera")
DIAS_RETENCION_PAPELERA = 30


def asegurar_directorio():
    """Garantiza que las carpetas de almacenamiento de notas y papelera existan."""
    if not os.path.exists(RUTA_ARCHIVOS):
        os.makedirs(RUTA_ARCHIVOS, exist_ok=True)
    if not os.path.exists(RUTA_PAPELERA):
        os.makedirs(RUTA_PAPELERA, exist_ok=True)


def _formatear_fecha_relativa(fecha_str):
    """Convierte 'YYYY-MM-DD HH:MM:SS' en algo legible: Hoy 14:32, Ayer 09:10, o 12 ene."""
    if not fecha_str:
        return ""
    try:
        dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return fecha_str

    hoy = date.today()
    if dt.date() == hoy:
        return f"Hoy · {dt.strftime('%H:%M')}"

    diferencia = (hoy - dt.date()).days
    if diferencia == 1:
        return f"Ayer · {dt.strftime('%H:%M')}"
    if diferencia < 7:
        dias = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
        return f"{dias[dt.weekday()]} · {dt.strftime('%H:%M')}"

    meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    return f"{dt.day} {meses[dt.month - 1]}"


def _generar_vista_previa(contenido, longitud=90):
    """Genera una vista previa de una línea a partir del contenido de la nota."""
    if not contenido:
        return "Sin contenido todavía…"
    plano = " ".join(contenido.split())
    if len(plano) <= longitud:
        return plano
    return plano[:longitud].rstrip() + "…"


class LogicaNotas:
    def __init__(self):
        asegurar_directorio()

    # ─────────────────────────────────────────────
    # LECTURA
    # ─────────────────────────────────────────────

    def _cargar_json_bruto(self, titulo):
        ruta = os.path.join(RUTA_ARCHIVOS, f"{titulo}.json")
        if not os.path.exists(ruta):
            return None
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except Exception:
            return None
        # Compatibilidad con notas creadas antes de añadir "fijada"
        datos.setdefault("fijada", False)
        datos.setdefault("titulo", titulo)
        datos.setdefault("contenido", "")
        datos.setdefault("ultima_modificacion", "")
        return datos

    def obtener_lista_notas(self):
        """Devuelve metadatos de todas las notas (para pintar la lista),
        ordenadas: fijadas primero, luego por fecha de modificación descendente."""
        asegurar_directorio()
        archivos = [f[:-5] for f in os.listdir(RUTA_ARCHIVOS) if f.endswith(".json")]

        notas = []
        for titulo in archivos:
            datos = self._cargar_json_bruto(titulo)
            if datos is None:
                continue
            ruta = os.path.join(RUTA_ARCHIVOS, f"{titulo}.json")
            mtime = os.path.getmtime(ruta)
            notas.append({
                "titulo": datos["titulo"],
                "vista_previa": _generar_vista_previa(datos.get("contenido", "")),
                "fijada": bool(datos.get("fijada", False)),
                "fecha": _formatear_fecha_relativa(datos.get("ultima_modificacion", "")),
                "_mtime": mtime,
            })

        notas.sort(key=lambda n: (not n["fijada"], -n["_mtime"]))
        for n in notas:
            n.pop("_mtime", None)
        return notas

    def cargar_nota(self, titulo):
        """Carga el contenido completo de una nota según su título."""
        datos = self._cargar_json_bruto(titulo)
        if datos is None:
            return {"titulo": titulo, "contenido": "", "ultima_modificacion": "", "fijada": False}
        return datos

    # ─────────────────────────────────────────────
    # ESCRITURA
    # ─────────────────────────────────────────────

    def guardar_nota(self, titulo, contenido, titulo_anterior=None, fijada=None):
        """Guarda o actualiza una nota en formato JSON, manejando renombres
        y preservando el estado de 'fijada' si no se indica lo contrario."""
        asegurar_directorio()

        titulo_limpio = "".join([c for c in titulo if c.isalnum() or c in (" ", "_", "-")]).strip()
        if not titulo_limpio:
            titulo_limpio = f"Nota_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if fijada is None:
            referencia = titulo_anterior or titulo_limpio
            previa = self._cargar_json_bruto(referencia)
            fijada = bool(previa.get("fijada", False)) if previa else False

        ruta_nueva = os.path.join(RUTA_ARCHIVOS, f"{titulo_limpio}.json")

        if titulo_anterior and titulo_anterior != titulo_limpio:
            ruta_anterior = os.path.join(RUTA_ARCHIVOS, f"{titulo_anterior}.json")
            if os.path.exists(ruta_anterior):
                os.remove(ruta_anterior)

        datos = {
            "titulo": titulo_limpio,
            "contenido": contenido,
            "fijada": fijada,
            "ultima_modificacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        with open(ruta_nueva, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)

        return titulo_limpio

    def alternar_fijada(self, titulo):
        """Invierte el estado 'fijada' de una nota existente. Devuelve el nuevo
        estado (bool) o None si la nota no existe."""
        datos = self._cargar_json_bruto(titulo)
        if datos is None:
            return None
        datos["fijada"] = not datos.get("fijada", False)
        ruta = os.path.join(RUTA_ARCHIVOS, f"{titulo}.json")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
        return datos["fijada"]

    def eliminar_nota(self, titulo):
        """Envía una nota a la papelera en lugar de borrarla para siempre.
        Se conserva ahí 30 días por si se eliminó por error."""
        asegurar_directorio()
        ruta = os.path.join(RUTA_ARCHIVOS, f"{titulo}.json")
        if not os.path.exists(ruta):
            return False

        datos = self._cargar_json_bruto(titulo) or {"titulo": titulo, "contenido": "", "fijada": False}
        datos["eliminada_en"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        ruta_papelera = os.path.join(RUTA_PAPELERA, f"{titulo}.json")
        # Evita colisiones si ya había una nota con el mismo nombre en la papelera
        if os.path.exists(ruta_papelera):
            sufijo = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta_papelera = os.path.join(RUTA_PAPELERA, f"{titulo}_{sufijo}.json")

        with open(ruta_papelera, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
        os.remove(ruta)
        return True

    # ─────────────────────────────────────────────
    # PAPELERA
    # ─────────────────────────────────────────────

    def _purgar_papelera_vencida(self):
        """Borra definitivamente las notas de la papelera con más de
        DIAS_RETENCION_PAPELERA días. Se ejecuta cada vez que se consulta la papelera."""
        asegurar_directorio()
        limite = datetime.now() - timedelta(days=DIAS_RETENCION_PAPELERA)
        for nombre_archivo in os.listdir(RUTA_PAPELERA):
            if not nombre_archivo.endswith(".json"):
                continue
            ruta = os.path.join(RUTA_PAPELERA, nombre_archivo)
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                eliminada_en = datetime.strptime(datos.get("eliminada_en", ""), "%Y-%m-%d %H:%M:%S")
                if eliminada_en < limite:
                    os.remove(ruta)
            except Exception:
                continue

    def listar_papelera(self):
        """Devuelve metadatos de las notas en la papelera, con los días
        restantes antes de que se borren para siempre."""
        asegurar_directorio()
        self._purgar_papelera_vencida()

        notas = []
        for nombre_archivo in os.listdir(RUTA_PAPELERA):
            if not nombre_archivo.endswith(".json"):
                continue
            ruta = os.path.join(RUTA_PAPELERA, nombre_archivo)
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    datos = json.load(f)
            except Exception:
                continue

            clave = nombre_archivo[:-5]
            eliminada_en_str = datos.get("eliminada_en", "")
            dias_restantes = DIAS_RETENCION_PAPELERA
            try:
                eliminada_en = datetime.strptime(eliminada_en_str, "%Y-%m-%d %H:%M:%S")
                transcurridos = (datetime.now() - eliminada_en).days
                dias_restantes = max(0, DIAS_RETENCION_PAPELERA - transcurridos)
            except Exception:
                pass

            notas.append({
                "clave": clave,
                "titulo": datos.get("titulo", clave),
                "vista_previa": _generar_vista_previa(datos.get("contenido", "")),
                "eliminada_en": _formatear_fecha_relativa(eliminada_en_str),
                "dias_restantes": dias_restantes,
            })

        notas.sort(key=lambda n: n["dias_restantes"])
        return notas

    def restaurar_nota(self, clave):
        """Recupera una nota de la papelera y la devuelve al cuaderno activo.
        Si ya existe una nota con ese título, se le añade un sufijo para no pisarla."""
        asegurar_directorio()
        ruta_papelera = os.path.join(RUTA_PAPELERA, f"{clave}.json")
        if not os.path.exists(ruta_papelera):
            return None

        with open(ruta_papelera, "r", encoding="utf-8") as f:
            datos = json.load(f)

        titulo = datos.get("titulo", clave)
        titulo_final = titulo
        ruta_destino = os.path.join(RUTA_ARCHIVOS, f"{titulo_final}.json")
        contador = 1
        while os.path.exists(ruta_destino):
            contador += 1
            titulo_final = f"{titulo} ({contador})"
            ruta_destino = os.path.join(RUTA_ARCHIVOS, f"{titulo_final}.json")

        datos["titulo"] = titulo_final
        datos.pop("eliminada_en", None)
        datos["ultima_modificacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(ruta_destino, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
        os.remove(ruta_papelera)
        return titulo_final

    def eliminar_definitivamente(self, clave):
        """Borra una nota de la papelera para siempre, sin posibilidad de recuperarla."""
        ruta = os.path.join(RUTA_PAPELERA, f"{clave}.json")
        if os.path.exists(ruta):
            os.remove(ruta)
            return True
        return False

    def vaciar_papelera(self):
        """Elimina definitivamente todas las notas de la papelera."""
        asegurar_directorio()
        contador = 0
        for nombre_archivo in os.listdir(RUTA_PAPELERA):
            if nombre_archivo.endswith(".json"):
                os.remove(os.path.join(RUTA_PAPELERA, nombre_archivo))
                contador += 1
        return contador

    def buscar_notas(self, texto_busqueda):
        """Devuelve metadatos de las notas que coincidan con la búsqueda,
        respetando el mismo orden (fijadas primero) que obtener_lista_notas."""
        texto_busqueda = (texto_busqueda or "").lower().strip()
        todas = self.obtener_lista_notas()
        if not texto_busqueda:
            return todas

        resultados = []
        for meta in todas:
            datos = self._cargar_json_bruto(meta["titulo"]) or {}
            if (texto_busqueda in meta["titulo"].lower()
                    or texto_busqueda in datos.get("contenido", "").lower()):
                resultados.append(meta)
        return resultados