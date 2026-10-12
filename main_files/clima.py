import re
import requests

# ─────────────────────────────────────────────────────────────
# 🌦️ MÓDULO DE CLIMA — usa Open-Meteo (gratuito, sin API key)
# ─────────────────────────────────────────────────────────────

_URL_GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
_URL_FORECAST = "https://api.open-meteo.com/v1/forecast"

CIUDAD_POR_DEFECTO = "Sevilla"  # 👈 Cambia esto por tu ciudad habitual

# Tabla oficial de códigos WMO (weathercode) → (descripción, emoji)
_CODIGOS_CLIMA = {
    0: ("Cielo despejado", "☀️"),
    1: ("Mayormente despejado", "🌤️"),
    2: ("Parcialmente nublado", "⛅"),
    3: ("Nublado", "☁️"),
    45: ("Niebla", "🌫️"),
    48: ("Niebla con escarcha", "🌫️"),
    51: ("Llovizna ligera", "🌦️"),
    53: ("Llovizna moderada", "🌦️"),
    55: ("Llovizna intensa", "🌧️"),
    56: ("Llovizna helada", "🌧️"),
    57: ("Llovizna helada intensa", "🌧️"),
    61: ("Lluvia ligera", "🌧️"),
    63: ("Lluvia moderada", "🌧️"),
    65: ("Lluvia intensa", "🌧️"),
    66: ("Lluvia helada", "🌧️"),
    67: ("Lluvia helada intensa", "🌧️"),
    71: ("Nevada ligera", "🌨️"),
    73: ("Nevada moderada", "🌨️"),
    75: ("Nevada intensa", "❄️"),
    77: ("Granos de nieve", "❄️"),
    80: ("Chubascos ligeros", "🌦️"),
    81: ("Chubascos moderados", "🌧️"),
    82: ("Chubascos violentos", "⛈️"),
    85: ("Chubascos de nieve ligeros", "🌨️"),
    86: ("Chubascos de nieve intensos", "❄️"),
    95: ("Tormenta eléctrica", "⛈️"),
    96: ("Tormenta con granizo ligero", "⛈️"),
    99: ("Tormenta con granizo intenso", "⛈️"),
}

# Palabras que disparan la intención de clima, sin importar qué haya entre
# medio (p.ej. "hace" en "que tiempo hace en Lima").
_PATRON_DISPARADOR = re.compile(r'\b(clima|tiempo|llover|lluvia)\b', re.IGNORECASE)
# Extrae la ciudad si el usuario la especificó con en/de/para.
_PATRON_CIUDAD = re.compile(r'\b(?:en|de|para)\s+(.+)', re.IGNORECASE)


def detectar_consulta_clima(texto_lower):
    """Devuelve la ciudad detectada (o '' si no especificó ninguna), o None
    si el texto no es una consulta de clima."""
    if not _PATRON_DISPARADOR.search(texto_lower):
        return None
    match_ciudad = _PATRON_CIUDAD.search(texto_lower)
    ciudad = match_ciudad.group(1).strip("?¿!¡. ") if match_ciudad else ""
    return ciudad


def obtener_clima(ciudad=None):
    """Consulta el clima actual para 'ciudad' (o CIUDAD_POR_DEFECTO si no
    se especifica). Devuelve un texto ya formateado, listo para el chat."""
    ciudad = (ciudad or "").strip() or CIUDAD_POR_DEFECTO

    try:
        # 1. Geocodificación: convertir el nombre de la ciudad en coordenadas
        resp_geo = requests.get(
            _URL_GEOCODING,
            params={"name": ciudad, "count": 1, "language": "es", "format": "json"},
            timeout=6,
        )
        resp_geo.raise_for_status()
        resultados = resp_geo.json().get("results")

        if not resultados:
            return f"⚠️ **SISTEMA:** No localicé la ciudad '{ciudad}' en la base geográfica. ¿Revisas la ortografía, Administrador?"

        lugar = resultados[0]
        lat, lon = lugar["latitude"], lugar["longitude"]
        nombre_mostrar = lugar.get("name", ciudad)
        pais = lugar.get("country", "")

        # 2. Clima actual en esas coordenadas
        resp_clima = requests.get(
            _URL_FORECAST,
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": "true",
                "timezone": "auto",
            },
            timeout=6,
        )
        resp_clima.raise_for_status()
        actual = resp_clima.json().get("current_weather", {})

        temperatura = actual.get("temperature")
        viento = actual.get("windspeed")
        codigo = actual.get("weathercode")
        descripcion, emoji = _CODIGOS_CLIMA.get(codigo, ("Condición no catalogada", "🌡️"))

        return (
            f"{emoji} **REPORTE CLIMATOLÓGICO — {nombre_mostrar}, {pais}**\n\n"
            f"🌡️ Temperatura: {temperatura}°C\n"
            f"📋 Condición: {descripcion}\n"
            f"💨 Viento: {viento} km/h\n\n"
            f"Datos sincronizados en tiempo real, Administrador."
        )

    except requests.exceptions.RequestException:
        return "⚠️ **SISTEMA:** No pude conectar con el servicio climatológico. Verifica tu conexión a internet, Administrador."
    except Exception as e:
        return f"⚠️ **SISTEMA:** Fallo inesperado al procesar el clima: {e}"
