import os
import re
import csv
import time
import string
import sqlite3
import unicodedata
from datetime import datetime, timedelta

RUTA_CONFIG = os.path.join(os.path.expanduser("~"), ".gearbook")
RUTA_BD = os.path.join(RUTA_CONFIG, "indice_buscador.db")

# Carpetas que no aportan valor indexar y ralentizan muchísimo el escaneo
CARPETAS_IGNORADAS = {
    "node_modules", ".git", "__pycache__", "$recycle.bin",
    "system volume information", ".venv", "venv", "windows",
    "programdata", ".cache", "site-packages", "dist", "build",
}

EXTENSIONES_CATEGORIA = {
    "Documentos": {".pdf", ".docx", ".doc", ".txt", ".xlsx", ".xls", ".pptx",
                   ".ppt", ".md", ".csv", ".rtf", ".odt"},
    "Imágenes": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico"},
    "Videos": {".mp4", ".avi", ".mkv", ".mov", ".webm", ".wmv", ".flv", ".m4v"},
    "Música": {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".wma", ".aac"},
    "Código": {".py", ".js", ".ts", ".java", ".c", ".cpp", ".html", ".css",
               ".json", ".php", ".go", ".rs", ".sh", ".bat"},
    "Comprimidos": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"},
}

# Extensiones sobre las que tiene sentido buscar dentro del contenido
EXTENSIONES_TEXTO_BUSCABLE = {
    ".txt", ".md", ".py", ".json", ".csv", ".log", ".ini", ".cfg",
    ".yaml", ".yml", ".js", ".html", ".css",
}
TAMANO_MAXIMO_CONTENIDO = 400_000  # bytes (~400 KB) por archivo a inspeccionar

# Categorías que cuentan como "archivos personales" para la lista de recientes
CATEGORIAS_RECIENTES = ("Documentos", "Imágenes", "Videos", "Música", "Comprimidos")

COLUMNAS = "ruta, nombre, extension, categoria, carpeta, tamano, modificado, es_carpeta"

# Claves válidas de ordenación → fragmento SQL ORDER BY.
# "relevancia" no está aquí: se calcula y ordena en Python (ver buscar()).
ORDEN_SQL = {
    "nombre": "nombre_lower ASC",
    "nombre_desc": "nombre_lower DESC",
    "fecha": "modificado DESC",
    "fecha_asc": "modificado ASC",
    "tamano": "tamano DESC",
    "tamano_asc": "tamano ASC",
}

_PATRON_MODIFICADOR = re.compile(
    r'(?<!\S)(ext|extension|carpeta|folder|tamano|tamaño|size|fecha|modificado|date):("[^"]*"|\S+)',
    re.IGNORECASE,
)
_UNIDADES_TAMANO = {
    "b": 1, "k": 1024, "kb": 1024, "m": 1024 ** 2, "mb": 1024 ** 2,
    "g": 1024 ** 3, "gb": 1024 ** 3, "tb": 1024 ** 4,
}


# ─────────────────────────────────────────────
# UTILIDADES DE TEXTO
# ─────────────────────────────────────────────
def _asegurar_directorio():
    os.makedirs(RUTA_CONFIG, exist_ok=True)


def _quitar_acentos(texto):
    if not texto:
        return texto
    nfkd = unicodedata.normalize('NFD', texto)
    return ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')


def _categoria_de(ext):
    for categoria, extensiones in EXTENSIONES_CATEGORIA.items():
        if ext in extensiones:
            return categoria
    return "Otros"


def _escapar_like(texto):
    """Escapa los comodines especiales de SQLite LIKE (%, _ y el propio
    carácter de escape '\\') para que la búsqueda del usuario se trate
    siempre como texto literal, nunca como patrón."""
    return (texto.replace("\\", "\\\\")
                 .replace("%", "\\%")
                 .replace("_", "\\_"))


# ─────────────────────────────────────────────
# PARSEO DE CONSULTAS
# Sintaxis admitida:
#   palabra1 palabra2        → todas deben aparecer en el nombre (en cualquier orden)
#   "frase exacta"           → la frase completa
#   -palabra                 → excluir nombres que la contengan
#   ext:pdf   ext:doc,docx   → una o varias extensiones
#   carpeta:descargas        → parte de la ruta de la carpeta
#   size:>10mb  size:<500kb  → filtro por tamaño (también tamano:)
#   fecha:hoy|semana|mes|año|7d|2025-01-31  → modificado desde…
# ─────────────────────────────────────────────
def _parsear_tamano(valor):
    m = re.match(r'^(>=|<=|>|<)?(\d+(?:[.,]\d+)?)([a-z]*)$', valor)
    if not m:
        return None
    operador, numero, unidad = m.groups()
    unidad = unidad or "mb"
    if unidad not in _UNIDADES_TAMANO:
        return None
    n = int(float(numero.replace(",", ".")) * _UNIDADES_TAMANO[unidad])
    if operador in ("<", "<="):
        return {"tamano_max": n}
    return {"tamano_min": n}


def _parsear_fecha(valor):
    inicio_hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    dias = {"hoy": 0, "today": 0, "ayer": 1, "semana": 7, "week": 7,
            "mes": 30, "month": 30, "año": 365, "ano": 365, "anio": 365, "year": 365}
    if valor in dias:
        return (inicio_hoy - timedelta(days=dias[valor])).timestamp()
    m = re.match(r'^(\d+)d$', valor)
    if m:
        return (inicio_hoy - timedelta(days=int(m.group(1)))).timestamp()
    try:
        return datetime.strptime(valor, "%Y-%m-%d").timestamp()
    except ValueError:
        return None


def parsear_consulta(texto_busqueda):
    """Extrae los modificadores (ext:, carpeta:, size:, fecha:) del texto libre.
    Devuelve (texto_restante, filtros_dict)."""
    filtros = {}
    texto = texto_busqueda or ""

    for match in _PATRON_MODIFICADOR.finditer(texto):
        clave = match.group(1).lower()
        valor = match.group(2).strip('"').lower()
        if not valor:
            continue
        if clave in ("ext", "extension"):
            exts = [v if v.startswith(".") else f".{v}" for v in valor.split(",") if v]
            if exts:
                filtros["extension"] = exts
        elif clave in ("carpeta", "folder"):
            filtros["carpeta"] = valor
        elif clave in ("tamano", "tamaño", "size"):
            rango = _parsear_tamano(valor)
            if rango:
                filtros.update(rango)
        else:  # fecha / modificado / date
            desde = _parsear_fecha(valor)
            if desde is not None:
                filtros["desde"] = desde

    texto_libre = _PATRON_MODIFICADOR.sub(" ", texto)
    return " ".join(texto_libre.split()).strip(), filtros


def _extraer_terminos(texto_libre):
    """Separa el texto libre en (términos a incluir, términos a excluir).
    Respeta "frases entre comillas" y el prefijo - para excluir."""
    incluir, excluir = [], []
    for frase, palabra in re.findall(r'"([^"]+)"|(\S+)', texto_libre or ""):
        if frase:
            incluir.append(frase.strip())
        else:
            palabra = palabra.strip('"')
            if palabra.startswith("-") and len(palabra) > 1:
                excluir.append(palabra[1:])
            elif palabra:
                incluir.append(palabra)
    return incluir, excluir


def terminos_busqueda(texto):
    """Términos positivos de la consulta (para resaltar en la interfaz)."""
    libre, _ = parsear_consulta((texto or "").lower())
    return _extraer_terminos(libre)[0]


# ─────────────────────────────────────────────
# BASE DE DATOS
# ─────────────────────────────────────────────
def obtener_conexion():
    """Abre (y crea si hace falta) la base de datos del índice."""
    _asegurar_directorio()
    conn = sqlite3.connect(RUTA_BD, check_same_thread=False)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except sqlite3.OperationalError:
        pass  # algunos sistemas de archivos en red no soportan WAL; no es crítico

    conn.execute("""
        CREATE TABLE IF NOT EXISTS archivos (
            ruta TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            nombre_lower TEXT NOT NULL,
            extension TEXT,
            categoria TEXT,
            carpeta TEXT,
            tamano INTEGER,
            modificado REAL,
            es_carpeta INTEGER
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nombre_lower ON archivos(nombre_lower)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_categoria ON archivos(categoria)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_carpeta ON archivos(carpeta)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_modificado ON archivos(modificado)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tamano ON archivos(tamano)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS metadatos_indice (
            clave TEXT PRIMARY KEY,
            valor TEXT
        )
    """)
    # Se conservan aunque se reconstruya el índice completo
    conn.execute("""
        CREATE TABLE IF NOT EXISTS historial (
            consulta TEXT PRIMARY KEY,
            ultima REAL,
            veces INTEGER DEFAULT 1
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fijados (
            ruta TEXT PRIMARY KEY,
            anadido REAL
        )
    """)
    conn.commit()

    _migrar_normalizacion(conn)
    return conn


def _migrar_normalizacion(conn):
    """Si el índice se creó antes de añadir la normalización de acentos,
    reescribe nombre_lower sin tildes. Se ejecuta una sola vez gracias a
    la clave 'version_normalizacion' en metadatos_indice."""
    try:
        cur = conn.execute(
            "SELECT valor FROM metadatos_indice WHERE clave='version_normalizacion'"
        )
        fila = cur.fetchone()
        version = int(fila[0]) if fila and fila[0].isdigit() else 1
        if version >= 2:
            return
    except sqlite3.OperationalError:
        return

    cur = conn.execute("SELECT ruta, nombre_lower FROM archivos")
    actualizaciones = [
        (_quitar_acentos(nl), ruta)
        for ruta, nl in cur.fetchall()
        if _quitar_acentos(nl) != nl
    ]
    if actualizaciones:
        conn.executemany(
            "UPDATE archivos SET nombre_lower = ? WHERE ruta = ?",
            actualizaciones,
        )
        conn.commit()

    conn.execute(
        "INSERT OR REPLACE INTO metadatos_indice (clave, valor) "
        "VALUES ('version_normalizacion', '2')"
    )
    conn.commit()


def obtener_ultimo_escaneo():
    """Devuelve la fecha/hora del último reindexado completo, o None si nunca se hizo."""
    conn = obtener_conexion()
    try:
        cur = conn.execute("SELECT valor FROM metadatos_indice WHERE clave='ultimo_escaneo'")
        fila = cur.fetchone()
        return fila[0] if fila else None
    finally:
        conn.close()


def obtener_total_indexado():
    conn = obtener_conexion()
    try:
        cur = conn.execute("SELECT COUNT(*) FROM archivos")
        return cur.fetchone()[0]
    finally:
        conn.close()


def obtener_estadisticas_indice():
    """Devuelve un dict {categoria: cantidad} más una clave especial
    '__total__' con la suma. Útil para mostrar un resumen del índice."""
    conn = obtener_conexion()
    try:
        cur = conn.execute(
            "SELECT categoria, COUNT(*) FROM archivos GROUP BY categoria ORDER BY COUNT(*) DESC"
        )
        stats = {categoria: cantidad for categoria, cantidad in cur.fetchall()}
        stats["__total__"] = sum(stats.values())
        return stats
    finally:
        conn.close()


# ─────────────────────────────────────────────
# ESCANEO
# ─────────────────────────────────────────────
def _listar_raices_escaneo():
    """Detecta discos locales disponibles (C:, D:, etc.). Si no encuentra
    ninguno (p.ej. en Linux/Mac), cae de vuelta a la carpeta personal."""
    raices = []
    for letra in string.ascii_uppercase:
        ruta = f"{letra}:\\"
        if os.path.exists(ruta):
            raices.append(ruta)
    if not raices:
        raices = [os.path.expanduser("~")]
    return raices


def _insertar_lote(conn, lote):
    conn.executemany(
        "INSERT OR REPLACE INTO archivos VALUES (?,?,?,?,?,?,?,?,?)",
        lote
    )
    conn.commit()


def _procesar_arbol(conn, raiz, raices_excluidas, callback_progreso, cancelar_flag, total_inicial=0):
    """Recorre 'raiz' con os.walk e inserta lo encontrado en 'archivos'.
    'raices_excluidas' son rutas que NO deben insertarse como carpeta en sí
    mismas (para no duplicar los puntos de partida del escaneo completo)."""
    total = total_inicial
    lote = []
    TAMANO_LOTE = 500

    for carpeta_actual, subcarpetas, archivos in os.walk(raiz, topdown=True, onerror=lambda e: None):
        if cancelar_flag is not None and getattr(cancelar_flag, "cancelado", False):
            break

        subcarpetas[:] = [
            sc for sc in subcarpetas
            if sc.lower() not in CARPETAS_IGNORADAS and not sc.startswith(".")
        ]

        if carpeta_actual not in raices_excluidas:
            try:
                stat_carpeta = os.stat(carpeta_actual)
                nombre_carpeta = os.path.basename(carpeta_actual)
                lote.append((
                    carpeta_actual, nombre_carpeta, _quitar_acentos(nombre_carpeta.lower()),
                    "", "Carpetas", os.path.dirname(carpeta_actual),
                    0, stat_carpeta.st_mtime, 1
                ))
                total += 1
            except Exception:
                pass

        for nombre_archivo in archivos:
            ruta_completa = os.path.join(carpeta_actual, nombre_archivo)
            try:
                stat_archivo = os.stat(ruta_completa)
            except Exception:
                continue

            ext = os.path.splitext(nombre_archivo)[1].lower()
            lote.append((
                ruta_completa, nombre_archivo, _quitar_acentos(nombre_archivo.lower()),
                ext, _categoria_de(ext), carpeta_actual,
                stat_archivo.st_size, stat_archivo.st_mtime, 0
            ))
            total += 1

            if len(lote) >= TAMANO_LOTE:
                _insertar_lote(conn, lote)
                lote = []
                if callback_progreso:
                    callback_progreso(carpeta_actual, total)

    if lote:
        _insertar_lote(conn, lote)

    return total


def escanear_sistema(callback_progreso=None, raices=None, cancelar_flag=None):
    """Recorre el sistema de archivos y reconstruye el índice completo desde cero.
    Los fijados y el historial se conservan."""
    raices = raices or _listar_raices_escaneo()
    conn = obtener_conexion()
    total = 0

    try:
        conn.execute("DELETE FROM archivos")
        conn.commit()

        for raiz in raices:
            if not os.path.exists(raiz):
                continue
            if cancelar_flag is not None and getattr(cancelar_flag, "cancelado", False):
                break
            total = _procesar_arbol(conn, raiz, raices, callback_progreso, cancelar_flag, total)

        conn.execute(
            "INSERT OR REPLACE INTO metadatos_indice (clave, valor) VALUES ('ultimo_escaneo', ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),)
        )
        conn.commit()
    finally:
        conn.close()

    if callback_progreso:
        callback_progreso("Completado", total)

    return total


def reindexar_carpeta(ruta_objetivo, callback_progreso=None, cancelar_flag=None):
    if not ruta_objetivo or not os.path.isdir(ruta_objetivo):
        raise ValueError(f"La ruta '{ruta_objetivo}' no es una carpeta válida.")

    conn = obtener_conexion()
    try:
        prefijo = os.path.normpath(ruta_objetivo)
        patron_hijos = _escapar_like(prefijo + os.sep) + "%"
        conn.execute(
            "DELETE FROM archivos WHERE ruta = ? OR ruta LIKE ? ESCAPE '\\'",
            (prefijo, patron_hijos)
        )
        conn.commit()

        total = _procesar_arbol(conn, ruta_objetivo, set(), callback_progreso, cancelar_flag)
        conn.commit()
    finally:
        conn.close()

    if callback_progreso:
        callback_progreso("Completado", total)
    return total


def eliminar_ruta_del_indice(ruta):
    if not ruta:
        return
    conn = obtener_conexion()
    try:
        prefijo = os.path.normpath(ruta)
        patron_hijos = _escapar_like(prefijo + os.sep) + "%"
        conn.execute(
            "DELETE FROM archivos WHERE ruta = ? OR ruta LIKE ? ESCAPE '\\'",
            (prefijo, patron_hijos)
        )
        conn.execute("DELETE FROM fijados WHERE ruta = ?", (prefijo,))
        conn.commit()
    finally:
        conn.close()


def verificar_y_limpiar_indice(limite_verificacion=20000):
    conn = obtener_conexion()
    eliminadas = 0
    try:
        cur = conn.execute("SELECT ruta FROM archivos LIMIT ?", (limite_verificacion,))
        rutas = [fila[0] for fila in cur.fetchall()]
        huerfanas = [(ruta,) for ruta in rutas if not os.path.exists(ruta)]
        if huerfanas:
            conn.executemany("DELETE FROM archivos WHERE ruta = ?", huerfanas)
            conn.commit()
            eliminadas = len(huerfanas)
    finally:
        conn.close()
    return eliminadas


# ─────────────────────────────────────────────
# HISTORIAL Y FIJADOS
# ─────────────────────────────────────────────
def registrar_busqueda(consulta):
    consulta = " ".join((consulta or "").split())
    if len(consulta) < 2:
        return
    conn = obtener_conexion()
    try:
        ahora = time.time()
        conn.execute(
            "INSERT OR IGNORE INTO historial (consulta, ultima, veces) VALUES (?, ?, 0)",
            (consulta, ahora)
        )
        conn.execute(
            "UPDATE historial SET ultima = ?, veces = veces + 1 WHERE consulta = ?",
            (ahora, consulta)
        )
        # Mantener sólo las 50 más recientes
        conn.execute(
            "DELETE FROM historial WHERE consulta NOT IN "
            "(SELECT consulta FROM historial ORDER BY ultima DESC LIMIT 50)"
        )
        conn.commit()
    finally:
        conn.close()


def obtener_historial(limite=8):
    conn = obtener_conexion()
    try:
        cur = conn.execute("SELECT consulta FROM historial ORDER BY ultima DESC LIMIT ?", (limite,))
        return [fila[0] for fila in cur.fetchall()]
    finally:
        conn.close()


def borrar_historial():
    conn = obtener_conexion()
    try:
        conn.execute("DELETE FROM historial")
        conn.commit()
    finally:
        conn.close()


def _rutas_fijadas(conn):
    return {fila[0] for fila in conn.execute("SELECT ruta FROM fijados")}


def alternar_fijado(ruta):
    """Fija o desfija un archivo. Devuelve True si queda fijado."""
    conn = obtener_conexion()
    try:
        existe = conn.execute("SELECT 1 FROM fijados WHERE ruta = ?", (ruta,)).fetchone()
        if existe:
            conn.execute("DELETE FROM fijados WHERE ruta = ?", (ruta,))
            fijado = False
        else:
            conn.execute("INSERT INTO fijados (ruta, anadido) VALUES (?, ?)", (ruta, time.time()))
            fijado = True
        conn.commit()
        return fijado
    finally:
        conn.close()


def _fila_a_dict(fila, fijados, score=0):
    ruta, nombre, ext, cat, carpeta, tamano, modificado, es_carpeta = fila
    return {
        "ruta": ruta, "nombre": nombre, "extension": ext, "categoria": cat,
        "carpeta": carpeta, "tamano": tamano, "modificado": modificado or 0,
        "es_carpeta": bool(es_carpeta), "score": score, "fijado": ruta in fijados,
    }


def obtener_fijados():
    conn = obtener_conexion()
    try:
        fijados = _rutas_fijadas(conn)
        cur = conn.execute(
            f"SELECT {', '.join('a.' + c.strip() for c in COLUMNAS.split(','))} "
            "FROM fijados f JOIN archivos a ON a.ruta = f.ruta ORDER BY f.anadido DESC"
        )
        return [_fila_a_dict(f, fijados) for f in cur.fetchall()]
    finally:
        conn.close()


def archivos_recientes(limite=15, categoria=None):
    """Archivos personales modificados más recientemente (para la pantalla de inicio)."""
    conn = obtener_conexion()
    try:
        fijados = _rutas_fijadas(conn)
        if categoria and categoria != "Todo":
            cats = (categoria,)
            es_carpeta_sql = "1=1"
        else:
            cats = CATEGORIAS_RECIENTES
            es_carpeta_sql = "es_carpeta = 0"
        marcadores = ",".join("?" * len(cats))
        cur = conn.execute(
            f"SELECT {COLUMNAS} FROM archivos WHERE categoria IN ({marcadores}) AND {es_carpeta_sql} "
            "ORDER BY modificado DESC LIMIT ?",
            (*cats, limite)
        )
        return [_fila_a_dict(f, fijados) for f in cur.fetchall()]
    finally:
        conn.close()


# ─────────────────────────────────────────────
# BÚSQUEDA
# ─────────────────────────────────────────────
def _puntuar(nombre_lower, texto_busqueda):
    if not texto_busqueda:
        return 10
    if nombre_lower == texto_busqueda:
        return 100
    if nombre_lower.startswith(texto_busqueda):
        return 80
    for separador in (" ", "_", "-", "."):
        if f"{separador}{texto_busqueda}" in nombre_lower:
            return 60
    if texto_busqueda in nombre_lower:
        return 40
    return 0


def _puntuar_terminos(nombre, incluir):
    if not incluir:
        return 10
    nl = _quitar_acentos(nombre.lower())
    if len(incluir) == 1:
        return _puntuar(nl, incluir[0])
    media = sum(_puntuar(nl, t) for t in incluir) // len(incluir)
    return max(_puntuar(nl, " ".join(incluir)), media)


def buscar(texto_busqueda, categoria=None, limite=80, offset=0, orden="relevancia"):
    texto_libre, filtros = parsear_consulta((texto_busqueda or "").strip().lower())
    incluir, excluir = _extraer_terminos(_quitar_acentos(texto_libre))

    if not incluir and not filtros:
        return []

    conn = obtener_conexion()
    try:
        condiciones = []
        parametros = []

        for termino in incluir:
            condiciones.append("nombre_lower LIKE ? ESCAPE '\\'")
            parametros.append(f"%{_escapar_like(termino)}%")
        for termino in excluir:
            condiciones.append("nombre_lower NOT LIKE ? ESCAPE '\\'")
            parametros.append(f"%{_escapar_like(termino)}%")

        if "extension" in filtros:
            exts = filtros["extension"]
            condiciones.append(f"extension IN ({','.join('?' * len(exts))})")
            parametros.extend(exts)

        if "carpeta" in filtros:
            condiciones.append("LOWER(carpeta) LIKE ? ESCAPE '\\'")
            parametros.append(f"%{_escapar_like(filtros['carpeta'])}%")

        if "tamano_min" in filtros:
            condiciones.append("tamano >= ?")
            parametros.append(filtros["tamano_min"])
        if "tamano_max" in filtros:
            condiciones.append("tamano <= ? AND es_carpeta = 0")
            parametros.append(filtros["tamano_max"])

        if "desde" in filtros:
            condiciones.append("modificado >= ?")
            parametros.append(filtros["desde"])

        if categoria and categoria != "Todo":
            condiciones.append("categoria = ?")
            parametros.append(categoria)

        where_sql = " AND ".join(condiciones) if condiciones else "1=1"
        order_sql = ORDEN_SQL.get(orden)

        # Para ordenar por relevancia puntuamos en Python, así que traemos
        # un margen mayor de filas candidatas antes de recortar y paginar.
        limite_sql = 3000 if orden == "relevancia" else (limite + offset)

        query = (
            f"SELECT {COLUMNAS} FROM archivos WHERE {where_sql} "
            + (f"ORDER BY {order_sql} " if order_sql else "")
            + "LIMIT ?"
        )
        parametros.append(limite_sql)

        filas = conn.execute(query, parametros).fetchall()
        fijados = _rutas_fijadas(conn)
    finally:
        conn.close()

    resultados = [
        _fila_a_dict(f, fijados, _puntuar_terminos(f[1], incluir)) for f in filas
    ]

    if orden == "relevancia":
        resultados.sort(key=lambda r: (not r["fijado"], -r["score"], -r["modificado"]))

    return resultados[offset:offset + limite]


def buscar_contenido(texto_busqueda, limite_archivos=400, limite_resultados=40):
    """Busca dentro de archivos de texto. Todos los términos deben aparecer;
    cada resultado incluye 'fragmento' con el contexto de la primera coincidencia."""
    texto_libre, _filtros = parsear_consulta((texto_busqueda or "").strip().lower())
    incluir, excluir = _extraer_terminos(_quitar_acentos(texto_libre))
    if not incluir or max(len(t) for t in incluir) < 3:
        return []

    conn = obtener_conexion()
    try:
        fijados = _rutas_fijadas(conn)
        marcadores = ",".join("?" * len(EXTENSIONES_TEXTO_BUSCABLE))
        cur = conn.execute(
            f"SELECT {COLUMNAS} FROM archivos "
            f"WHERE extension IN ({marcadores}) AND tamano <= ? AND es_carpeta = 0 "
            f"ORDER BY modificado DESC LIMIT ?",
            (*EXTENSIONES_TEXTO_BUSCABLE, TAMANO_MAXIMO_CONTENIDO, limite_archivos)
        )
        candidatos = cur.fetchall()
    finally:
        conn.close()

    resultados = []
    for fila in candidatos:
        ruta = fila[0]
        if not os.path.exists(ruta):
            continue
        try:
            with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
                contenido = f.read()
        except Exception:
            continue

        contenido_norm = _quitar_acentos(contenido.lower())
        if not all(t in contenido_norm for t in incluir):
            continue
        if any(e in contenido_norm for e in excluir):
            continue

        i = contenido_norm.find(incluir[0])
        inicio = max(0, i - 40)
        fragmento = " ".join(contenido[inicio:i + len(incluir[0]) + 80].split())
        if inicio > 0:
            fragmento = "…" + fragmento

        r = _fila_a_dict(fila, fijados, 30)
        r["fragmento"] = fragmento
        resultados.append(r)

        if len(resultados) >= limite_resultados:
            break

    return resultados


# ─────────────────────────────────────────────
# DUPLICADOS
# ─────────────────────────────────────────────
def buscar_duplicados(tamano_minimo=100 * 1024, limite_grupos=150):
    """Agrupa archivos con el mismo nombre y tamaño (heurística rápida, sin
    leer el contenido). Devuelve (grupos, bytes_recuperables), donde cada
    grupo es {'nombre', 'tamano', 'archivos': [resultado, ...]}, ordenados
    por espacio que se liberaría."""
    conn = obtener_conexion()
    try:
        fijados = _rutas_fijadas(conn)
        claves = conn.execute(
            "SELECT nombre_lower, tamano FROM archivos "
            "WHERE es_carpeta = 0 AND tamano >= ? "
            "GROUP BY nombre_lower, tamano HAVING COUNT(*) > 1 "
            "ORDER BY tamano * (COUNT(*) - 1) DESC LIMIT ?",
            (tamano_minimo, limite_grupos)
        ).fetchall()

        grupos = []
        recuperable = 0
        for nombre_lower, tamano in claves:
            filas = conn.execute(
                f"SELECT {COLUMNAS} FROM archivos "
                "WHERE nombre_lower = ? AND tamano = ? AND es_carpeta = 0 "
                "ORDER BY modificado DESC",
                (nombre_lower, tamano)
            ).fetchall()
            archivos = [_fila_a_dict(f, fijados) for f in filas]
            if len(archivos) < 2:
                continue
            grupos.append({"nombre": archivos[0]["nombre"], "tamano": tamano, "archivos": archivos})
            recuperable += tamano * (len(archivos) - 1)
        return grupos, recuperable
    finally:
        conn.close()


# ─────────────────────────────────────────────
# VISTA PREVIA / EXPORTACIÓN / FORMATO
# ─────────────────────────────────────────────
def leer_vista_previa_texto(ruta, max_chars=2500):
    """Primeros caracteres de un archivo de texto, o None si no aplica."""
    ext = os.path.splitext(ruta)[1].lower()
    if ext not in EXTENSIONES_TEXTO_BUSCABLE:
        return None
    try:
        with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(max_chars)
    except Exception:
        return None


def exportar_csv(resultados, ruta_destino):
    """Guarda los resultados en un CSV (UTF-8 con BOM, abre bien en Excel)."""
    with open(ruta_destino, "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow(["Nombre", "Ruta", "Carpeta", "Categoría", "Tamaño (bytes)", "Modificado"])
        for r in resultados:
            try:
                fecha = datetime.fromtimestamp(r["modificado"]).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                fecha = ""
            escritor.writerow([r["nombre"], r["ruta"], r["carpeta"], r["categoria"], r["tamano"], fecha])
    return len(resultados)


def formatear_tamano(num_bytes):
    if not num_bytes:
        return "—"
    valor = float(num_bytes)
    for unidad in ["B", "KB", "MB", "GB", "TB"]:
        if valor < 1024:
            return f"{valor:.0f} {unidad}" if unidad == "B" else f"{valor:.1f} {unidad}"
        valor /= 1024
    return f"{valor:.1f} PB"