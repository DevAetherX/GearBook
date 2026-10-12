
import re
import random
import webbrowser
import wikipedia

# Configuración de Wikipedia (se hace una sola vez al importar el módulo)
wikipedia.set_lang("es")
wikipedia.set_user_agent("MariaBot/1.0")


# ─────────────────────────────────────────────────────────────
# 🌐 BÚSQUEDA GENERAL EN INTERNET (DuckDuckGo)
# ─────────────────────────────────────────────────────────────

def buscar_en_internet(busqueda):
    """Realiza una búsqueda general en internet y devuelve un resumen formateado."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            resultados = list(ddgs.text(busqueda, max_results=8, region="es-es"))
            if resultados:
                resumen = f"### 🌐 Resultados para '{busqueda}':\n\n"
                cont = 0
                
                # Lista de dominios o palabras irrelevantes a ignorar
                ignorar = ["google.com", "diccionario", "rae.es", "wikipedia.org/wiki/.es"]
                
                for res in resultados:
                    url = res.get('href', '')
                    titulo = res.get('title', 'Sin título')
                    cuerpo = res.get('body', '').strip()
                    
                    # Filtrar snippets vacíos o no informativos
                    if any(bad in url.lower() for bad in ignorar) or len(cuerpo) < 20:
                        continue
                        
                    resumen += f"• **[{titulo}]({url})**\n{cuerpo}\n\n"
                    cont += 1
                    if cont >= 4:  # Mostrar solo los mejores 4 resultados útiles
                        break

                return resumen if cont > 0 else f"No se encontraron resultados relevantes para '{busqueda}'."
            else:
                return f"No encontré información en la red sobre '{busqueda}'."
    except Exception as e:
        return f"Error al conectar con la red de búsqueda: {e}"

# ─────────────────────────────────────────────────────────────
# 📖 WIKIPEDIA
# ─────────────────────────────────────────────────────────────

_PATRON_WIKI = re.compile(
    r'\b(busca|buscame|busques|quien\s+es|quién\s+es|que\s+es|qué\s+es|sabes\s+quien\s+es|'
    r'sabes\s+que\s+es|cuentame\s+sobre|háblame\s+de|quien\s+fue|quién\s+fue)\s+(.*)',
    re.IGNORECASE
)


def detectar_consulta_wikipedia(texto_lower):
    """Analiza el texto (ya en minúsculas) y devuelve el término a buscar
    en Wikipedia si el texto coincide con un patrón de consulta ('qué es...',
    'quién es...', etc.), o None si no coincide."""
    match_wiki = _PATRON_WIKI.search(texto_lower)
    if not match_wiki:
        return None

    algo = match_wiki.group(2).strip("?¿!¡. ")
    algo = re.sub(r'^(el|la|los|las|un|una|sobre|de|del|busca)\s+', '', algo, flags=re.IGNORECASE)
    return algo or None


def buscar_wikipedia(algo):
    """Busca 'algo' en Wikipedia. Devuelve (respuesta_texto, url_o_None).

    Si hay ambigüedad o no se encuentra nada, la url devuelta es None
    (no queda pendiente ninguna confirmación de apertura de página).
    """
    try:
        resumen = wikipedia.summary(algo, sentences=2)
        url = wikipedia.page(algo).url
        resumen = re.sub(r'[^\w\s.,;:!?¿¡()\'"áéíóúüñÁÉÍÓÚÜÑ\-]', ' ', resumen, flags=re.UNICODE)
        resumen = re.sub(r'\s+', ' ', resumen).strip()
        respuesta = (
            f"Esto es lo que encontré sobre **{algo.capitalize()}**:\n\n{resumen}\n\n"
            f"¿Quieres que abra la página completa? Di 'si' o 'no'. 🥰"
        )
        return respuesta, url
    except wikipedia.exceptions.DisambiguationError as e:
        opciones = ", ".join(e.options[:3])
        return f"Hay varias opciones para '{algo}' (ej: {opciones}). ¿Puedes ser más específico? 🌸", None
    except Exception:
        return f"No encontré nada sobre '{algo}'. ¿Está bien escrito? 🧠", None


def procesar_respuesta_url_pendiente(texto_lower, ultima_url):
    """Gestiona la confirmación 'sí'/'no' cuando hay una URL de Wikipedia
    pendiente de abrir.

    Devuelve (respuesta, nueva_ultima_url):
      - Si 'ultima_url' es None (no había nada pendiente): (None, None).
      - Si el texto confirma o rechaza la apertura: (texto_respuesta, None).
      - Si hay una url pendiente pero el texto no es una confirmación
        reconocible: (None, ultima_url) — se mantiene pendiente.
    """
    if not ultima_url:
        return None, ultima_url

    if texto_lower == "si" or "abre" in texto_lower:
        webbrowser.open(ultima_url)
        return "¡Página abierta! 🚀", None

    if texto_lower == "no" or "pasa" in texto_lower or "deja" in texto_lower:
        respuesta = random.choice([
            "Entendido. ¿En qué más puedo ayudarte?",
            "Como quieras. Consola a la espera.",
            "De acuerdo. ¿Siguiente instrucción?"
        ])
        return respuesta, None

    return None, ultima_url
