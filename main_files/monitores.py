import time
import subprocess
import webbrowser

from screeninfo import get_monitors
import pygetwindow as gw


def abrir_en_monitor(url_o_comando, num_monitor, es_url=True):
    """Abre un navegador o aplicación y lo arrastra al monitor seleccionado (1 o 2)"""
    try:
        monitores = get_monitors()
        if num_monitor > len(monitores):
            num_monitor = 1

        monitor = monitores[num_monitor - 1]
        x_destino = monitor.x + 100
        y_destino = monitor.y + 100

        if es_url:
            webbrowser.open(url_o_comando)
        else:
            subprocess.Popen(url_o_comando)

        time.sleep(1.5)

        ventana = gw.getActiveWindow()
        if ventana:
            if ventana.isMaximized:
                ventana.restore()
            ventana.moveTo(x_destino, y_destino)
            ventana.maximize()

        return f"¡Listo, mi rey! Ya te puse eso en el Monitor {num_monitor}. ¡A disfrutar! 🎬✨"

    except Exception as e:
        print(f"❌ Error al mover ventana: {e}")
        if es_url:
            webbrowser.open(url_o_comando)
        return f"Te abrí el enlace, corazón, pero no pude arrastrarlo automáticamente al Monitor {num_monitor}. 🥺"