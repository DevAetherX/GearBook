from PyQt5.QtWidgets import QApplication
from notas.interfaz_notas import VentanaNotas

try:
    import sip
except ImportError:
    sip = None

_instancia_ventana = None

def _reset_ventana_instance(obj=None):
    global _instancia_ventana
    _instancia_ventana = None


def abrir_gestor_notas(parent=None):
    """Inicializa y muestra la ventana flotante del gestor de notas."""
    global _instancia_ventana

    if _instancia_ventana is not None:
        if sip is not None:
            try:
                if sip.isdeleted(_instancia_ventana):
                    _instancia_ventana = None
            except Exception:
                _instancia_ventana = None

    if _instancia_ventana is None or not _instancia_ventana.isVisible():
        _instancia_ventana = VentanaNotas()
        _instancia_ventana.destroyed.connect(_reset_ventana_instance)
        _instancia_ventana.show()
    else:
        _instancia_ventana.raise_()
        _instancia_ventana.activateWindow()

def ejecutar_comando_notas(subcomando=""):
    """
    Función puente para procesar instrucciones textuales desde el chat de GearBook (ej: 'notas/').
    """
    abrir_gestor_notas()
    return "Módulo de Notas desplegado exitosamente."