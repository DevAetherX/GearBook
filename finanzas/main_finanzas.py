from PyQt5.QtWidgets import QApplication

_instancia = None


def abrir_gestor_finanzas(maria=None):
    """Abre (o reenfoca) la ventana de finanzas."""
    global _instancia
    if _instancia is None or not _instancia.isVisible():
        from .interfaz_finanzas import VentanaFinanzas
        _instancia = VentanaFinanzas(maria=maria)
        _instancia.destroyed.connect(lambda: globals().update(_instancia=None))
    _instancia.show()
    _instancia.raise_()
    _instancia.activateWindow()
    return _instancia