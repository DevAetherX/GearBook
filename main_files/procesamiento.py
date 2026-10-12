import re
import os
import random
from internet import detectar_consulta_wikipedia, buscar_wikipedia, procesar_respuesta_url_pendiente, buscar_en_internet 
from memoria.memoria import guardar_historial, obtener_ultimo_mensaje
from organizador import organizar_carpeta
from boveda_musica import reproducir_musica_por_ruta_comando
from buscador import main_buscador
from clima import obtener_clima, detectar_consulta_clima
from finanzas.logica_finanzas import gestor as finanzas_gestor
from datetime import datetime

def procesar(self, texto):
        texto_original = texto.strip()
        texto_lower = texto_original.lower()

        # ── 1. CONTEXTO / MEMORIA ──────────────────────────────────────────
        if "que te dije antes" in texto_lower or "cual fue mi ultimo mensaje" in texto_lower:
            ultimo = obtener_ultimo_mensaje()
            respuesta = f"Me comunicó la siguiente instrucción: '{ultimo}'." if ultimo else "Consola limpia. No se registran mensajes previos en la sesión actual."
            self.guardar_en_historial(texto_original, respuesta)
            return respuesta

        # ── 2. COMANDOS CON BARRA / (necesitan el texto original intacto) ──
        if texto_lower.startswith("ordenar/") or texto_lower.startswith("ordena/") or texto_lower.startswith("organizar/"):
            patron_ruta = re.compile(r'(?:ordenar|ordena|organizar)/+(.*)', re.IGNORECASE)
            match_ruta = patron_ruta.search(texto_original)
            if match_ruta:
                ruta_solicitada = match_ruta.group(1).strip('"\' ')
                resultado = organizar_carpeta(ruta_solicitada)

                # 🌟 Notificación emergente igual que en descargas: éxito o error
                if isinstance(resultado, str) and resultado.startswith("✨"):
                    self.gestor_notificaciones.notificar_organizacion(ruta_solicitada)
                else:
                    self.gestor_notificaciones.notificar_error("Organización de carpeta", resultado)

                return resultado

        if texto_lower.startswith("music/"):
          ruta_comando = texto_original[6:].strip()
          return reproducir_musica_por_ruta_comando(ruta_comando, parent=self)

        if texto_lower.startswith("descargar/"):
            url = texto_original[10:].strip()
            self.descarga_pendiente = None
            return self.descargar_video_interactivo(url)

        if texto_lower.startswith("busca en internet/"):
            busqueda = texto_original[18:].strip()
            return buscar_en_internet(busqueda)

        if texto_lower.startswith("buscar/") or texto_lower.startswith("busca/"):
           consulta = texto_original.split("/", 1)[1].strip() if "/" in texto_original else ""
           return main_buscador.ejecutar_comando_buscador(consulta)

        # ── 3. DESCARGA EN CURSO (respuestas como "mp3", "sí", resolución) ─
        respuesta_descarga = self.procesar_descarga_respuesta(texto_lower)
        if respuesta_descarga:
            return respuesta_descarga

        # ── 4. CONFIRMACIONES PENDIENTES (apagar/reiniciar) ───────────────
        if self.esperando_confirmacion:
            if "si" in texto_lower:
                accion = self.esperando_confirmacion
                self.esperando_confirmacion = None
                if accion == "apagar": os.system("shutdown /s /t 1")
                if accion == "reiniciar": os.system("shutdown /r /t 1")
                return "Entendido. Hasta pronto... ✨"
            else:
                self.esperando_confirmacion = None
                return "Vale, me alegra que te quedes. 😊"

        # ── 5. RESPUESTA A WIKIPEDIA PREVIA ───────────────────────────────
        respuesta_url, self.ultima_url = procesar_respuesta_url_pendiente(texto_lower, self.ultima_url)
        if respuesta_url:
            return respuesta_url

        # ── 6. VOLUMEN ────────────────────────────────────────────────────
        match_volumen = re.search(r'(volumen|audio)\s+(?:al|en)\s+(\d+)', texto_lower)
        if match_volumen:
            nuevo_porcentaje = int(match_volumen.group(2))
            exito = self.fijar_volumen_exacto(nuevo_porcentaje)
            return f"Volumen al {nuevo_porcentaje}%. 🔊" if exito else "No pude ajustar el volumen. 🥺"

        # ── 7. MONITORES ──────────────────────────────────────────────────
        patron_monitores = re.compile(
            r'(?:pon|abre)\s+(youtube|musica|spotify|netflix)\s+en\s+la?\s*pantalla\s*([1-2])|'
            r'(?:pon|abre)\s+(youtube|musica|spotify|netflix)\s+en\s+el?\s*monitor\s*([1-2])',
            re.IGNORECASE
        )
        match_mon = patron_monitores.search(texto_lower)
        if match_mon:
            grupo = match_mon.groups()
            plataforma = grupo[0] or grupo[2]
            monitor_num = int(grupo[1] or grupo[3])
            urls = {"youtube": "https://www.youtube.com", "musica": "https://www.youtube.com/watch?v=jfKfPfyJRdk",
                    "spotify": "http://spotify.com", "netflix": "https://www.netflix.com"}
            return self.abrir_en_monitor(urls.get(plataforma.lower(), "https://www.google.com"), monitor_num, es_url=True)

        # ── 8. COMANDOS DEL DICCIONARIO ───────────────────────────────────
        for cmd in self.comandos:
            if any(key in texto_lower for key in cmd["keys"]):
                if cmd["act"]:
                    cmd["act"]()
                return cmd["resp"]

        # ── NUEVO: CLIMA ──────────────────────────────────────────────────
        ciudad_clima = detectar_consulta_clima(texto_lower)
        if ciudad_clima is not None:
           return obtener_clima(ciudad_clima)

        # ── 9. WIKIPEDIA ──────────────────────────────────────────────────
        algo = detectar_consulta_wikipedia(texto_lower)
        if algo:
            respuesta, url = buscar_wikipedia(algo)
            if url:
                self.ultima_url = url
            return respuesta

        # ── 11. FINANZAS ──────────────────────────────────────────────
        
        # Abrir ventana
        if texto_lower in ("finanzas","FINANZAS", "abrir finanzas", "mis finanzas", "dinero"):
            self.abrir_gestor_finanzas()
            return "Abriendo panel de finanzas... 💰"

        # Registrar gasto: "gasté 20 en comida" / "gasto 15 transporte"
        m_gasto = re.search(
            r'(?:gaste|gasto|gast[ée]|pag[ue]e?)\s+(\d+(?:[.,]\d+)?)\s*(?:€|euros?)?\s+(?:en\s+)?(.+)',
            texto_lower
        )
        if m_gasto:
            monto = float(m_gasto.group(1).replace(",", "."))
            cat = m_gasto.group(2).strip().capitalize()
            ok, msg = finanzas_gestor.agregar_transaccion("gasto", monto, cat)
            return f"💰 {msg}" if ok else f"⚠️ {msg}"

        # Registrar ingreso: "ingreso 1000 nomina"
        m_ingreso = re.search(
            r'(?:ingres[oe]|cobr[ée]|recibi)\s+(\d+(?:[.,]\d+)?)\s*(?:€|euros?)?\s+(?:de\s+|por\s+)?(.+)',
            texto_lower
        )
        if m_ingreso:
            monto = float(m_ingreso.group(1).replace(",", "."))
            cat = m_ingreso.group(2).strip().capitalize()
            ok, msg = finanzas_gestor.agregar_transaccion("ingreso", monto, cat)
            return f"💰 {msg}" if ok else f"⚠️ {msg}"

        # Balance / resumen
        if any(p in texto_lower for p in ("balance", "cuanto tengo", "cuánto tengo", "resumen financiero")):
            b = finanzas_gestor.balance()
            return (
                f"💰 **Resumen global**\n"
                f"• Ingresos: {b['ingresos']:.2f} €\n"
                f"• Gastos: {b['gastos']:.2f} €\n"
                f"• Balance: **{b['balance']:.2f} €**"
            )

        if any(p in texto_lower for p in ("gastos del mes", "gastos de este mes", "gastos del mes actual")):
            ahora = datetime.now()
            b = finanzas_gestor.balance(mes=ahora.month, anio=ahora.year)
            return (
                f"💰 **Mes actual**\n"
                f"• Ingresos: {b['ingresos']:.2f} €\n"
                f"• Gastos: {b['gastos']:.2f} €\n"
                f"• Balance: **{b['balance']:.2f} €**"
            )

        # Gastos por categoría
        if "gastos por categoria" in texto_lower or "desglose de gastos" in texto_lower:
            ahora = datetime.now()
            desglose = finanzas_gestor.gastos_por_categoria(mes=ahora.month, anio=ahora.year)
            if not desglose:
                return "No hay gastos registrados este mes."
            lineas = [f"• **{g['categoria']}**: {g['total']:.2f} €" for g in desglose]
            return "💰 **Desglose de gastos del mes:**\n" + "\n".join(lineas)

        # ── 10. DIÁLOGOS (último recurso, texto limpiado para puntuación) ─
        texto_norm = re.sub(r'[^\w\s]', ' ', texto_lower)

        mejor_categoria = None
        mejor_score = 0
        for categoria, datos in self.dialogos.items():
            if not isinstance(datos, dict) or "palabras_clave" not in datos:
                continue
            score = sum(len(p) for p in datos["palabras_clave"] if p in texto_norm)
            if score > mejor_score:
                mejor_score = score
                mejor_categoria = categoria

        if mejor_categoria:
            datos = self.dialogos[mejor_categoria]
            if mejor_categoria == "despedidas" and not self.muteado:
                self.muteado = True
            respuesta = self.construir_respuesta_dinamica(mejor_categoria)
            if not respuesta:
                respuesta = random.choice(datos["respuestas"]) if "respuestas" in datos else "Error de ejecución."
            guardar_historial(texto_original, respuesta)
            return respuesta

        contexto = self.construir_contexto(texto_original)
        return self.cerebro_dialogo(texto_norm, contexto=contexto)