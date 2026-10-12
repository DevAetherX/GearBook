# main_explorador.py
from .interfaz_explorador import SelectorDestino

def abrir_explorador_independiente(parent_app):
    dialogo = SelectorDestino(parent_app, solo_carpetas=False)
    dialogo.setWindowTitle("Explorador — Seleccionar carpeta de destino")
    dialogo.btn_aceptar.setText("Seleccionar aquí")
    return dialogo.exec_() 
"Este es para SELECCIONAR DESTINO (ej. mover un archivo descargado). Debe mostrar SOLO CARPETAS para no confundirse con archivos."

def abrir_explorador_auditoria(parent_app):
    dialogo = SelectorDestino(parent_app, solo_carpetas=True) 
    dialogo.setWindowTitle("Explorador de Archivos")
    dialogo.btn_aceptar.setText("Seleccionar archivo")
    dialogo.show() 
"Este es el explorador NORMAL (para ver fotos, videos, música, etc.). Debe mostrar ARCHIVOS Y CARPETAS."