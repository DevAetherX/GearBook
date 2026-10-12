from buscador.interfaz_buscador import VentanaBuscador
from buscador import logica_buscador as logica

try:
    import sip
except ImportError:
    sip = None

_instancia_ventana = None


def _reset_ventana_instance(obj=None):
    global _instancia_ventana
    _instancia_ventana = None


def _ventana_valida():
    global _instancia_ventana
    if _instancia_ventana is None:
        return None
    if sip is not None:
        try:
            if sip.isdeleted(_instancia_ventana):
                return None
        except Exception:
            return None
    return _instancia_ventana


def abrir_buscador(parent=None, consulta_inicial=""):
    """Inicializa y muestra la ventana flotante del Buscador Universal.
    Si todavía no existe índice, lanza automáticamente el primer escaneo.
    Devuelve (ok: bool, mensaje: str) para que el llamador pueda avisar
    al usuario si algo salió mal."""
    global _instancia_ventana

    ventana = _ventana_valida()

    if ventana is None or not ventana.isVisible():
        try:
            _instancia_ventana = VentanaBuscador()
        except Exception as e:
            _instancia_ventana = None
            return False, f"⚠️ No se pudo abrir el Buscador Universal: {e}"

        _instancia_ventana.destroyed.connect(_reset_ventana_instance)

        if consulta_inicial:
            _instancia_ventana.txt_buscar.setText(consulta_inicial)

        try:
            if not logica.obtener_ultimo_escaneo():
                _instancia_ventana.iniciar_reindexado()
        except Exception:
            # Si el índice está corrupto o inaccesible, dejamos que el
            # usuario lo arregle a mano con el botón "Reindexar" en vez
            # de impedir que la ventana se abra.
            pass

        _instancia_ventana.show()
    else:
        ventana.raise_()
        ventana.activateWindow()
        if consulta_inicial:
            ventana.txt_buscar.setText(consulta_inicial)

    return True, ""


def reindexar_todo():
    """Fuerza un reindexado completo en segundo plano, abriendo la
    ventana si hiciera falta. Pensado para usarse desde atajos externos
    (Stream Deck, comandos por voz, etc.)."""
    ok, mensaje = abrir_buscador()
    if not ok:
        return mensaje
    _instancia_ventana.iniciar_reindexado()
    return "🔁 Reindexado completo iniciado."


def ejecutar_comando_buscador(subcomando=""):
    """
    Función puente para procesar instrucciones textuales desde el chat de
    María (ej: 'buscar/informe final', 'busca/factura_marzo').
    """
    consulta = (subcomando or "").strip()
    ok, mensaje = abrir_buscador(consulta_inicial=consulta)
    if not ok:
        return mensaje
    if consulta:
        return f"🔎 Buscando «{consulta}» en todo el sistema, Administrador."
    return "Buscador Universal desplegado exitosamente."