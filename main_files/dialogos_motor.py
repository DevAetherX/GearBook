import random
import dialogos


def obtener_respuestas_por_defecto(logica, humor_actual):
    """Devuelve la lista de respuestas por defecto para el humor actual, con respaldo global."""
    defaults = logica.dialogos.get("respuesta_por_defecto", {})
    if humor_actual in defaults:
        respuestas = defaults[humor_actual]
    else:
        respuestas = [respuesta for lista in defaults.values() for respuesta in lista]

    if not respuestas:
        return ["Hmm... no sé qué decir ahora mismo."]

    return respuestas


def construir_respuesta_dinamica(logica, categoria):
    """
    Selecciona un inicio, un apodo, un intermedio (si existe) y un cierre al azar
    de la categoría indicada y los une usando un formato corporativo y serio.
    """
    # 1. Comprobamos que la categoría exista en los diálogos
    if categoria not in logica.dialogos:
        return None

    bloques = logica.dialogos[categoria]

    # Validamos que existan las listas obligatorias de la estructura
    if "inicio" not in bloques or "apodo" not in bloques or "cierre" not in bloques:
        return None

    # 2. Extraemos un elemento aleatorio de cada bloque plano
    inicio = random.choice(bloques["inicio"])
    apodo = random.choice(bloques["apodo"])
    cierre = random.choice(bloques["cierre"])

    # 3. Si la categoría tiene el bloque intermedio (como en saludos), lo añadimos
    if "intermedio" in bloques and bloques["intermedio"]:
        intermedio = random.choice(bloques["intermedio"])
        return f"{inicio} {apodo}. {intermedio} {cierre}"
    else:
        # Estructura básica si no tiene bloque intermedio (como en piropos)
        return f"{inicio} {apodo}. {cierre}"


def cerebro_dialogo(logica, texto_norm, contexto=None):
    respuesta_base = ""
    reaccion_extra = ""
    
    # 1. Elegir la categoría con mayor score ponderado por longitud de palabra clave
    # Las frases largas ("te quiero") valen más que palabras cortas ("hola")
    mejor_categoria = None
    mejor_score = 0
    for categoria, contenido in logica.dialogos.items():
        if categoria in ["respuesta_por_defecto", "insultos_reaccion"]:
            continue
        if isinstance(contenido, dict) and "palabras_clave" in contenido:
            score = sum(
                len(p)  # peso = longitud de la palabra clave
                for p in contenido["palabras_clave"]
                if p in texto_norm
            )
            if score > mejor_score:
                mejor_score = score
                mejor_categoria = categoria
            elif score == mejor_score and score > 0:
                # Empate: 50% de probabilidad de cambiar (evita sesgo por orden)
                if random.random() < 0.5:
                    mejor_categoria = categoria
    
    if mejor_categoria:
        contenido = logica.dialogos[mejor_categoria]
        if "respuestas" in contenido:
            respuesta_base = random.choice(contenido["respuestas"])
        else:
            respuesta_base = construir_respuesta_dinamica(logica, mejor_categoria)
    
    # 2. Capa de insultos
    if "insultos_reaccion" in logica.dialogos:
        datos_insultos = logica.dialogos["insultos_reaccion"]
        if any(insulto in texto_norm for insulto in datos_insultos["palabras_clave"]):
            reaccion_extra = random.choice(datos_insultos["respuestas"])
    
    # 3. Combinar
    if respuesta_base and reaccion_extra:
        return f"{respuesta_base}{reaccion_extra}"
    elif respuesta_base:
        return respuesta_base
    elif reaccion_extra:
        return reaccion_extra
    
    humor_actual = getattr(dialogos, "estado_animo_actual", "tsundere")
    respuesta_defecto = obtener_respuestas_por_defecto(logica, humor_actual)
    return random.choice(respuesta_defecto)