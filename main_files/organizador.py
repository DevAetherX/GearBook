import os
import shutil
import time
from datetime import datetime
import screen_brightness_control as sbc

def organizar_carpeta(ruta_objetivo):
        if not os.path.exists(ruta_objetivo):
            return f"Ay, cielo... la ruta '{ruta_objetivo}' no existe. ¿Te has equivocado en alguna letra? 🥺"
           
        
        # Categorías estándar del sistema
        extensiones = {
            "Imágenes": ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.psd', '.ai', '.eps'],
            "Imágenes RAW": ['.raw', '.cr2', '.nef', '.arw', '.dng', '.orf', '.rw2'],
            "Documentos": ['.pdf', '.docx', '.doc', '.txt', '.xlsx', '.xls', '.pptx', '.ppt', '.md', '.rtf', '.odt', '.epub', '.ods', '.odp', '.mobi', '.url', '.log'],
            "Videos": ['.mp4', '.avi', '.mkv', '.mov', '.flv', '.webm', '.wmv', '.mpeg', '.m4v', '.3gp'],
            "Música": ['.mp3', '.wav', '.flac', '.m4a', '.wma', '.aac', '.ogg', '.mid', '.midi', '.aiff', '.alac', '.opus'],
            "Archivos Comprimidos": ['.zip', '.rar', '.7z', '.tar', '.gz', '.xz', '.bz2'],
            "Instaladores y Ejecutables": ['.exe', '.msi', '.jar', '.bat', '.cmd', '.dmg', '.pkg', '.apk', '.deb', '.rpm', '.app', '.run', '.sh', '.bin', '.vbs', '.ps1', '.scr', '.cpl', '.gadget', '.xpi', '.crx', '.xap', '.air'],
            "Archivos de programación": ['.py', '.java', '.c', '.cpp', '.js', '.ts', '.php', '.rb', '.go', '.rs', '.swift', '.html', '.css', '.json', '.xml', '.pl', '.r', '.lua', '.asm'],
            "Web y Frontend": ['.jsx', '.tsx', '.scss', '.less', '.vue', '.svelte'],
            "DevOps": ['.dockerignore', '.tf', '.tfstate'],
            "Notebooks": ['.ipynb'],
            "Bases de datos": ['.db', '.sql', '.mdb', '.accdb', '.sqlite', '.sqlite3', '.dbf', '.csv'],
            "Seguridad y Certificados": ['.pem', '.key', '.crt', '.cer', '.pfx', '.p12'],
            "Backups y Dumps": ['.bak', '.backup', '.dump', '.tar.gz'],
            "Fuentes y Tipografías": ['.ttf', '.otf', '.woff', '.woff2', '.eot', '.fon'],
            "Personalización y Temas": ['.vlt', '.ithmb', '.msstyles', '.theme'],
            "Máquinas Virtuales": ['.vmdk', '.vdi', '.vhdx', '.vhd', '.ova', '.ovf'],
            "Diseño 3D y CAD": ['.stl', '.obj', '.fbx', '.dwg', '.dxf', '.blend', '.gcode'],
            "Imágenes de Sistema y Diagnóstico": ['.img', '.dmp', '.wim', '.iso', '.vhd', '.vhdx', '.bin', '.cue', '.mdf', '.nrg'],
            "Configuración": ['.cfg', '.conf', '.ini', '.toml', '.yaml', '.yml', '.env'],
            "Juegos": ['.sav', '.pak', '.unity', '.uasset', '.godot'],
            "ROMs y Emulación": ['.gba'],
            "Carpetas de Programas y Proyectos": [],  # Destino para las carpetas con autorización ( 19-9 )
            "Acceso Directo y Atajos": ['.lnk', '.desktop', '.url'],
            "Sin clasificar": []  # Para cualquier archivo que no encaje en las categorías anteriores
        }

        # Nombres de las carpetas destino para evitar que se procesen a sí mismas
        carpetas_destino_sistema = set(extensiones.keys())
        carpetas_destino_sistema.add("Sin clasificar")

        archivos_movidos = 0
        carpetas_movidas = 0
        carpetas_ignoradas = 0
        carpetas_eliminadas = 0
        estadisticas = {}
        inicio = time.time()
        
        # Definimos la marca exacta requerida para carpetas
        MARCA_AUTORIZACION = "( 19-9 )"

        try:
            # 1. PASO: Procesar elementos en la raíz de la ruta objetivo
            for elemento in os.listdir(ruta_objetivo):
                ruta_elemento = os.path.join(ruta_objetivo, elemento)
                
                # Evitar tocar las carpetas organizadoras del propio sistema
                if elemento in carpetas_destino_sistema:
                    continue

                # SI ES UN ARCHIVO (Libre movimiento, no requiere autorización)
                if os.path.isfile(ruta_elemento):
                    nombre_ext = os.path.splitext(elemento)[1].lower()
                    clasificado = False
                    
                    for categoria, ext_lista in extensiones.items():
                        if nombre_ext in ext_lista:
                            carpeta_destino = os.path.join(ruta_objetivo, categoria)
                            if not os.path.exists(carpeta_destino):
                                os.makedirs(carpeta_destino)
                            
                            shutil.move(ruta_elemento, os.path.join(carpeta_destino, elemento))
                            archivos_movidos += 1
                            estadisticas[categoria] = estadisticas.get(categoria, 0) + 1
                            clasificado = True
                            break
                    
                    if not clasificado:
                        carpeta_sin_clasificar = os.path.join(ruta_objetivo, "Sin clasificar")
                        if not os.path.exists(carpeta_sin_clasificar):
                            os.makedirs(carpeta_sin_clasificar)
                        shutil.move(ruta_elemento, os.path.join(carpeta_sin_clasificar, elemento))
                        archivos_movidos += 1
                        estadisticas["Sin clasificar"] = estadisticas.get("Sin clasificar", 0) + 1

                # SI ES UNA CARPETA
                elif os.path.isdir(ruta_elemento):
                    # Regla estricta: Si NO tiene la marca exacta, se ignora por completo
                    if MARCA_AUTORIZACION not in elemento:
                        carpetas_ignoradas += 1
                        continue
                    
                    # Si SI tiene la marca, se mueve de forma superficial a la categoría de proyectos
                    categoria = "Carpetas de Programas y Proyectos"
                    carpeta_destino = os.path.join(ruta_objetivo, categoria)
                    if not os.path.exists(carpeta_destino):
                        os.makedirs(carpeta_destino)
                    
                    try:
                        # Se mueve la carpeta entera como un solo bloque. No se lee su interior.
                        shutil.move(ruta_elemento, os.path.join(carpeta_destino, elemento))
                        carpetas_movidas += 1
                        estadisticas[categoria] = estadisticas.get(categoria, 0) + 1
                    except Exception as e:
                        print(f"No se pudo mover la carpeta autorizada {elemento}: {e}")

            # 2. PASO: Limpieza automática de carpetas vacías 
            # (No requiere autorización; si se quedó vacía tras mover sus archivos, se borra)
            for elemento in os.listdir(ruta_objetivo):
                ruta_elemento = os.path.join(ruta_objetivo, elemento)
                if os.path.isdir(ruta_elemento) and elemento not in carpetas_destino_sistema:
                    # Si está completamente vacía, se elimina
                    if not os.listdir(ruta_elemento):
                        os.rmdir(ruta_elemento)
                        carpetas_eliminadas += 1
            
            tiempo_total = round(time.time() - inicio, 2)

            # 3. PASO: Construcción del reporte final
            resumen = "✨ **Organización completada**\n\n"
            resumen += f"📂 **Carpeta:** {os.path.basename(ruta_objetivo)}\n\n"

            iconos = {
                "Imágenes": "🖼️",
                "Imágenes RAW": "📸",
                "Documentos": "📄", 
                "Videos": "🎬",
                "Música": "🎵", 
                "Archivos Comprimidos": "📦", 
                "Instaladores y Ejecutables": "⚙️",
                "Archivos de programación": "💻",
                "Web y Frontend": "🌐", 
                "DevOps": "🚀",
                "Notebooks": "📓",
                "Bases de datos": "🗄️", 
                "Seguridad y Certificados": "🔒",
                "Backups y Dumps": "💾", 
                "Fuentes y Tipografías": "🔤", 
                "Personalización y Temas": "🎨",
                "Máquinas Virtuales": "🧩",
                "Diseño 3D y CAD": "📐", 
                "Imágenes de Sistema y Diagnóstico": "💾",
                "Configuración": "⚙️", 
                "Juegos": "🎮", 
                "ROMs y Emulación": "🕹️",
                "Carpetas de Programas y Proyectos": "📁", 
                "Acceso Directo y Atajos": "🔗",
                "Sin clasificar": "🚫"
            }

            for categoria, cantidad in estadisticas.items():
                if cantidad > 0:
                    icono = iconos.get(categoria, "📁")
                    resumen += f"{icono} {categoria}: {cantidad}\n"

            resumen += f"\n🛡️ Carpetas Ignoradas: {carpetas_ignoradas}\n"
            resumen += f"🧹 Carpetas vacías eliminadas: {carpetas_eliminadas}\n"
            resumen += f"\n📊 Total: {archivos_movidos} archivos y {carpetas_movidas} carpetas autorizadas\n"
            resumen += f"⏱️ Tiempo: {tiempo_total} segundos\n\n"
            resumen += "¡Todo limpito! ✨"
            return resumen
            
        except Exception as e:
            return f"Ay, corazón... no pude organizar la carpeta debido a: {e}"