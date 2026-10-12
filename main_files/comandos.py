import os
import random
import webbrowser
from datetime import datetime
import screen_brightness_control as sbc
from notas import main_notas  # Asegúrate de ajustar la importación según tu estructura
from buscador import main_buscador
from clima import obtener_clima, detectar_consulta_clima

def obtener_comandos(instancia):
    return [
        {"id": "buscar/", "keys": [], "resp": "", "act": lambda: None},

        {
            "id": "brave", 
            "keys": ["brave", "navegador"], 
            "resp": "Inicializando el navegador Brave.", 
            "act": lambda: os.startfile(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe")
        },
        {
            "id": "youtube", 
            "keys": ["youtube", "video"], 
            "resp": "Accediendo a la plataforma de YouTube.", 
            "act": lambda: webbrowser.open("https://www.youtube.com")
        },
        {
            "id": "google", 
            "keys": ["google", "buscar"], 
            "resp": "Abriendo el motor de búsqueda Google.", 
            "act": lambda: webbrowser.open("https://www.google.com")
        },
        {
            "id": "whatsapp", 
            "keys": ["whatsapp", "wasap"], 
            "resp": "Abriendo la interfaz de mensajería externa.", 
            "act": lambda: webbrowser.open("whatsapp://")
        },
        {
            "id": "telegram", 
            "keys": ["telegram", "mensajeria"], 
            "resp": "Iniciando la aplicación de mensajería Telegram.", 
            "act": lambda: os.startfile(r"C:\Users\Nitropc\AppData\Roaming\Telegram Desktop\Telegram.exe")
        },
        {
            "id": "calculadora", 
            "keys": ["calc", "calculadora"], 
            "resp": "Desplegando la herramienta de calculadora del sistema.", 
            "act": lambda: os.system("calc")
        },
        {
            "id": "v_subir", 
            "keys": ["subir volumen", "mas volumen", "sube el volumen"], 
            "resp": "Incrementando el volumen de salida de audio.", 
            "act": lambda: [os.system('powershell -Command "(new-object -com wscript.shell).SendKeys([char]175)"') for _ in range(5)]
        },
        {
            "id": "v_bajar", 
            "keys": ["bajar volumen", "menos volumen", "baja el volumen"], 
            "resp": "Disminuyendo el volumen de salida de audio.", 
            "act": lambda: [os.system('powershell -Command "(new-object -com wscript.shell).SendKeys([char]174)"') for _ in range(5)]
        },
        {
            "id": "v_mute", 
            "keys": ["silencio", "mutear"], 
            "resp": "Salida de audio silenciada correctamente.", 
            "act": lambda: os.system('powershell -Command "(new-object -com wscript.shell).SendKeys([char]173)"')
        },
        {
            "id": "bloquear", 
            "keys": ["bloquea", "bloquear", "lock", "suspende el pc", "bloquea el pc"], 
            "resp": "Estación de trabajo bloqueada de forma segura.", 
            "act": lambda: os.system("rundll32.exe user32.dll,LockWorkStation")
        },
        {
            "id": "apagar", 
            "keys": ["apaga el pc", "apagar computadora"], 
            "resp": "Se ha solicitado el apagado del equipo. ¿Confirma la operación, Administrador? (Escriba: sí / no)", 
            "act": lambda: instancia.set_espera("apagar")
        },
        {
            "id": "reiniciar", 
            "keys": ["reinicia", "reiniciar pc"], 
            "resp": "Se ha solicitado el reinicio del sistema. ¿Confirma la operación, Administrador? (Escriba: sí / no)", 
            "act": lambda: instancia.set_espera("reiniciar")
        },
        {
            "id": "minimizar", 
            "keys": ["limpia la pantalla", "minimiza todo", "escritorio"], 
            "resp": "Minimizando todas las ventanas para liberar el entorno visual.", 
            "act": lambda: os.system('powershell -Command "(New-Object -ComObject shell.application).MinimizeAll()"')
        },
        {
            "id": "brillo_max", 
            "keys": ["brillo maximo", "subir todo el brillo"], 
            "resp": "Ajustando el brillo de la pantalla al 100%.", 
            "act": lambda: sbc.set_brightness(100)
        },
        {
            "id": "brillo_min", 
            "keys": ["bajar todo el brillo", "brillo minimo"], 
            "resp": "Ajustando el brillo de la pantalla al 20% para optimización visual.", 
            "act": lambda: sbc.set_brightness(20)
        },
        {
            "id": "ordenar/", 
            "keys": [], 
            "resp": "Procesando directorio...", 
            "act": lambda: None
        },
        {
            "id": "pausar_todo", 
            "keys": ["pausa", "pausar", "detener musica", "para la musica"], 
            "resp": "Deteniendo la reproducción multimedia global.", 
            "act": lambda: os.system('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]179)"')
        },
        {
            "id": "reanudar_todo", 
            "keys": ["reanuda", "reanudar", "reproducir", "sigue con la musica", "continua"], 
            "resp": "Reanudando la secuencia multimedia previa.", 
            "act": lambda: instancia.reanudar_multimedia_sistema()
        },
        {
            "id": "notas/", 
            "keys": ["notas", "apuntes", "recordatorio"], 
            "resp": "Desplegando la interfaz de gestión de notas.", 
            "act": lambda: main_notas.abrir_gestor_notas()
        },
        {
            "id": "info_commands",
            "keys": ["info commands", "info comands", "ayuda", "comandos", "que puedes hacer", "manual"],
            "resp": (
                "🖥️ **MANUAL DE OPERACIONES DEL SISTEMA:**\n\n"
                "🎛️ **CONTROLES DEL ENTORNO:**\n"
                "• `brillo al X` ➔ Modifica el nivel de brillo del monitor (Ej: *brillo al 80*).\n"
                "• `volumen al X` ➔ Ajusta el volumen maestro del sistema (Ej: *volumen al 50*).\n"
                "• `ordenar/[Ruta]` ➔ Clasifica y organiza archivos por extensión en la ruta indicada (Ej: *ordenar/D:\\Descargas*).\n"
                "• `limpia la pantalla` / `minimiza todo` ➔ Minimiza todas las ventanas activas para despejar el escritorio.\n"
                "• `como esta el clima` ➔ Consulta y despliega el reporte climatológico en el navegador Brave.\n"
                "• `pon [App] en la pantalla [1-2]` ➔ Ejecuta la aplicación y la posiciona en el monitor especificado (Ej: *pon youtube en la pantalla 2*).\n"
                "• `apaga el pc` / `reinicia el pc` ➔ Comandos críticos del sistema con confirmación de seguridad.\n"
                "• `pausa` / `pausar` ➔ Detiene de forma global la reproducción multimedia activa. ⏸️\n"
                "• `reanuda` / `continua` ➔ Reanuda la reproducción del medio pausado previamente. ▶️\n\n"
                "🔍 **BUSCADOR UNIVERSAL:**\n"
                "• `buscar/` ➔ Abre la ventana flotante del Buscador Universal.\n"
                "• `buscar/[Término]` ➔ Indexa y localiza de forma instantánea archivos, carpetas o contenidos de texto (Ej: *buscar/factura_marzo*).\n\n"
                "🗄️ **BÓVEDA DE MEDIOS (Disco D):**\n"
                "• `music/` ➔ Reproduce un archivo multimedia de forma aleatoria desde el directorio raíz.\n"
                "• `music/Género` ➔ Inicia reproducción dentro del directorio del género especificado (Ej: *music/rap*).\n"
                "• `music/Artista` ➔ Accede directamente al directorio del artista (Ej: *music/canserbero*).\n"
                "• `music/Canción` ➔ Localiza y ejecuta un archivo MP4 específico por su nombre (Ej: *music/jeremias 17-5*).\n\n"
                "📥 **GESTIÓN DE DESCARGAS:**\n"
                "• `descargar/[Link]` ➔ Inicializa el módulo interactivo de descarga para fuentes de YouTube o X/Twitter (Ej: *descargar/https://...*).\n\n"
                "🔍 **MÓDULO DE INVESTIGACIÓN:**\n"
                "• `¿Qué es X?` / `Busca X` ➔ Consulta y sintetiza información en Wikipedia, ofreciendo la apertura del enlace completo.\n\n"
                "Sistema en espera. Indique la acción o comando que desea ejecutar, Administrador."
            ),
            "act": lambda: None  
        }
    ]