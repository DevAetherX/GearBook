import json
import os


CARPETA_MEMORIA = "memoria"

ARCHIVO_RECUERDOS = os.path.join(CARPETA_MEMORIA, "recuerdos.json")
ARCHIVO_HISTORIAL = os.path.join(CARPETA_MEMORIA, "historial.json")


# =========================
# CREAR ARCHIVOS SI NO EXISTEN
# =========================

def inicializar_memoria():
    os.makedirs(CARPETA_MEMORIA, exist_ok=True)

    if not os.path.exists(ARCHIVO_RECUERDOS):
        with open(ARCHIVO_RECUERDOS, "w", encoding="utf-8") as f:
            json.dump({}, f)

    if not os.path.exists(ARCHIVO_HISTORIAL):
        with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
            json.dump([], f)


# =========================
# HISTORIAL SIMPLE
# =========================

def guardar_historial(usuario, maria):
    historial = cargar_historial()

    historial.append({
        "usuario": usuario,
        "maria": maria
    })

    # Limite
    historial = historial[-500:]

    with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=4)


def cargar_historial():
    try:
        with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def obtener_ultimo_mensaje():
    historial = cargar_historial()

    if historial:
        return historial[-1]["usuario"]

    return None


# =========================
# RECUERDOS IMPORTANTES
# =========================

def cargar_recuerdos():
    try:
        with open(ARCHIVO_RECUERDOS, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def guardar_recuerdo(clave, valor):
    recuerdos = cargar_recuerdos()

    recuerdos[clave] = valor

    with open(ARCHIVO_RECUERDOS, "w", encoding="utf-8") as f:
        json.dump(recuerdos, f, ensure_ascii=False, indent=4)


def obtener_recuerdo(clave):
    recuerdos = cargar_recuerdos()

    return recuerdos.get(clave)


def borrar_recuerdo(clave):
    recuerdos = cargar_recuerdos()

    if clave in recuerdos:
        del recuerdos[clave]

    with open(ARCHIVO_RECUERDOS, "w", encoding="utf-8") as f:
        json.dump(recuerdos, f, ensure_ascii=False, indent=4)


def obtener_recuerdos_relevantes(query, max_resultados=5):
    """Devuelve recuerdos cuya clave comparte tokens con la `query`.
    Búsqueda simple por coincidencia de palabras para obtener contexto relevante.
    """
    try:
        recuerdos = cargar_recuerdos()
        q = (query or "").lower()
        tokens = set([t for t in q.split() if len(t) > 2])
        relevantes = []

        for clave, valor in recuerdos.items():
            clave_tokens = set([t for t in clave.lower().split() if len(t) > 2])
            if tokens & clave_tokens:
                relevantes.append({"clave": clave, "valor": valor})

        # Si no hay coincidencias por tokens, intentar coincidencia por substring
        if not relevantes and q:
            for clave, valor in recuerdos.items():
                if q in clave.lower() or q in str(valor).lower():
                    relevantes.append({"clave": clave, "valor": valor})

        return relevantes[:max_resultados]
    except Exception:
        return []

def construir_contexto(self, texto_usuario, max_ultimos=6):
        """Construye un bloque de contexto combinando recuerdos relevantes y últimos mensajes."""
        try:
            ultimos = self.historial[-max_ultimos:]
            recuerdos = obtener_recuerdos_relevantes(texto_usuario, max_resultados=5)

            partes = []
            if recuerdos:
                partes.append("Recuerdos relevantes:")
                for r in recuerdos:
                    partes.append(f"- {r['clave']}: {r['valor']}")

            if ultimos:
                partes.append("Últimos intercambios:")
                for m in ultimos:
                    partes.append(f"Usuario: {m.get('usuario','')}")
                    partes.append(f"Maria: {m.get('maria','')}")

            return "\n".join(partes)
        except Exception as e:
            return ""
