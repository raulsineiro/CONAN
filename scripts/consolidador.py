#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# CONAN - Consolidador
# Lee los JSONs de los módulos ejecutados, cruza datos entre ellos,
# llama a Ollama para generar un resumen ejecutivo y crea el informe HTML.

import json
import os
import glob
import sys
import requests
from datetime import datetime

DIR_RESULTADOS = "/opt/conan/resultados"
DIR_INFORMES = "/opt/conan/informes"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODELO_OLLAMA = "mistral"

def cargar_resultados_modulo(dominio, numero_modulo):
    patron = os.path.join(DIR_RESULTADOS, f"modulo{numero_modulo}_{dominio}_*.json")
    ficheros = sorted(glob.glob(patron))
    if not ficheros:
        return None
    with open(ficheros[-1], "r", encoding="utf-8") as f:
        return json.load(f)

def cruzar_datos(mod1, mod2, mod3, mod4):
    correlaciones = []

    # Usuarios en metadatos que también aparecen como emails
    if mod2 and mod3:
        emails = [e.get("email", "") for e in mod2.get("empleados", [])]
        usuarios_docs = mod3.get("usuarios_encontrados", [])
        for usuario in usuarios_docs:
            for email in emails:
                if usuario.lower() in email.lower():
                    correlaciones.append(
                        f"Usuario '{usuario}' encontrado en metadatos de documentos "
                        f"coincide con email corporativo '{email}'"
                    )

    # IPs del módulo 1 que aparecen en URLScan del módulo 4
    if mod1 and mod4:
        hosts_mod1 = mod1.get("hosts", [])
        escaneos_urlscan = mod4.get("urlscan", {}).get("escaneos", [])
        for escaneo in escaneos_urlscan:
            if escaneo.get("veredicto"):
                correlaciones.append(
                    f"URL maliciosa detectada por URLScan: {escaneo.get('url')}"
                )

    # Software encontrado en documentos
    if mod3:
        software = mod3.get("software_encontrado", [])
        if software:
            correlaciones.append(
                f"Software corporativo identificado en metadatos: {', '.join(software)}"
            )

    # Emails encontrados en filtraciones
    if mod2 and mod4:
        nivel_riesgo = mod4.get("evaluacion_riesgo", {}).get("nivel", "BAJO")
        if nivel_riesgo in ["MEDIO", "ALTO"]:
            correlaciones.append(
                f"Dominio con nivel de riesgo {nivel_riesgo} según análisis de reputación"
            )

    return correlaciones

def construir_contexto(dominio, mod1, mod2, mod3, mod4, correlaciones):
    lineas = [f"Dominio analizado: {dominio}\n"]

    if mod1:
        lineas.append("INFRAESTRUCTURA:")
        lineas.append(f"  - {mod1.get('total_hosts', 0)} hosts encontrados")
        lineas.append(f"  - {mod1.get('total_subdominios', 0)} subdominios encontrados")

    if mod2:
        lineas.append("\nEMPLEADOS:")
        lineas.append(f"  - {mod2.get('total_emails', 0)} emails corporativos encontrados")
        empleados = mod2.get('empleados', [])
        for emp in empleados[:3]:
            servicios = ', '.join(emp.get('servicios_registrados', [])) or 'ninguno'
            lineas.append(f"  - {emp.get('email')} registrado en: {servicios}")
        lineas.append(f"  - {mod2.get('total_perfiles', 0)} perfiles sociales encontrados")

    if mod3:
        lineas.append("\nDOCUMENTOS:")
        lineas.append(f"  - {mod3.get('total_documentos', 0)} documentos analizados")
        usuarios = mod3.get('usuarios_encontrados', [])
        if usuarios:
            lineas.append(f"  - Usuarios en metadatos: {', '.join(usuarios)}")
        software = mod3.get('software_encontrado', [])
        if software:
            lineas.append(f"  - Software identificado: {', '.join(software)}")

    if mod4:
        lineas.append("\nREPUTACIÓN:")
        lineas.append(f"  - IP principal: {mod4.get('ip', 'N/A')}")
        vt = mod4.get('virustotal', {})
        if 'error' not in vt:
            lineas.append(f"  - VirusTotal: {vt.get('malicioso', 0)} motores lo marcan como malicioso")
        abuse = mod4.get('abuseipdb', {})
        if 'error' not in abuse:
            lineas.append(f"  - AbuseIPDB: puntuación {abuse.get('puntuacion_abuso', 0)}/100, ISP: {abuse.get('isp', 'N/A')}")
        nivel = mod4.get('evaluacion_riesgo', {}).get('nivel', 'BAJO')
        lineas.append(f"  - Nivel de riesgo: {nivel}")

    if correlaciones:
        lineas.append("\nCORRELACIONES DETECTADAS:")
        for c in correlaciones:
            lineas.append(f"  - {c}")
    else:
        lineas.append("\nCORRELACIONES: Ninguna detectada")

    return '\n'.join(lineas)


def generar_resumen_ollama(dominio, mod1, mod2, mod3, mod4, correlaciones):
    print("[*] Generando resumen ejecutivo con Ollama...")

    resumen_datos = {
        "dominio": dominio,
        "infraestructura": {
            "total_hosts": mod1.get("total_hosts", 0) if mod1 else 0,
            "total_subdominios": mod1.get("total_subdominios", 0) if mod1 else 0,
            "total_emails": mod1.get("total_emails", 0) if mod1 else 0
        } if mod1 else "No ejecutado",
        "empleados": {
            "total_emails": mod2.get("total_emails", 0) if mod2 else 0,
            "total_perfiles": mod2.get("total_perfiles", 0) if mod2 else 0
        } if mod2 else "No ejecutado",
        "documentos": {
            "total_documentos": mod3.get("total_documentos", 0) if mod3 else 0,
            "usuarios_encontrados": mod3.get("usuarios_encontrados", []) if mod3 else [],
            "software_encontrado": mod3.get("software_encontrado", []) if mod3 else []
        } if mod3 else "No ejecutado",
        "reputacion": {
            "nivel_riesgo": mod4.get("evaluacion_riesgo", {}).get("nivel", "N/A") if mod4 else "N/A",
            "motivos": mod4.get("evaluacion_riesgo", {}).get("motivos", []) if mod4 else []
        } if mod4 else "No ejecutado",
        "correlaciones": correlaciones
    }

    contexto = construir_contexto(dominio, mod1, mod2, mod3, mod4, correlaciones)

    prompt = f"""Eres un analista de ciberinteligencia. IMPORTANTE: Responde ÚNICAMENTE con el informe ejecutivo en español, sin introducción ni explicaciones previas.

Genera un informe ejecutivo detallado sobre el dominio '{dominio}' con estos 5 apartados:
1. Superficie de exposición
2. Hallazgos relevantes por área
3. Correlaciones y patrones detectados
4. Evaluación del riesgo
5. Recomendaciones específicas para este dominio

Datos del reconocimiento:
{contexto}

Menciona datos concretos como emails, usuarios y software cuando estén disponibles."""

    try:
        respuesta = requests.post(
            OLLAMA_URL,
            json={"model": MODELO_OLLAMA, "prompt": prompt, "stream": False},
            timeout=600
        )
        if respuesta.status_code == 200:
            return respuesta.json().get("response", "No se pudo generar el resumen.")
        else:
            return f"Error al conectar con Ollama: {respuesta.status_code}"
    except Exception as e:
        return f"Error al conectar con Ollama: {e}"

def markdown_a_html(texto):
    import re
    texto = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', texto)
    texto = re.sub(r'\*(.*?)\*', r'<em>\1</em>', texto)
    return texto

def generar_informe_html(dominio, mod1, mod2, mod3, mod4, correlaciones, resumen):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nombre_fichero = f"informe_{dominio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    ruta = os.path.join(DIR_INFORMES, nombre_fichero)

    def seccion_modulo(titulo, datos, campos):
        if not datos:
            return f"<div class='modulo'><h2>{titulo}</h2><p class='no-data'>Módulo no ejecutado.</p></div>"
        filas = ""
        for campo, etiqueta in campos:
            valor = datos.get(campo, "N/A")
            if isinstance(valor, list):
                valor = "<br>".join(str(v) for v in valor) if valor else "Ninguno"
            filas += f"<tr><td class='label'>{etiqueta}</td><td>{valor}</td></tr>"
        return f"<div class='modulo'><h2>{titulo}</h2><table>{filas}</table></div>"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CONAN — Informe {dominio}</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #0d0d0d; color: #e0e0e0; margin: 0; padding: 20px; }}
        h1 {{ color: #00bfff; border-bottom: 2px solid #00bfff; padding-bottom: 10px; }}
        h2 {{ color: #00bfff; margin-top: 0; }}
        .header {{ background: #1a1a2e; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .header p {{ margin: 4px 0; color: #aaa; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
        .modulo {{ background: #1a1a2e; padding: 20px; border-radius: 8px; border-left: 4px solid #00bfff; }}
        .no-data {{ color: #888; font-style: italic; }}
        table {{ width: 100%; border-collapse: collapse; }}
        td {{ padding: 8px; border-bottom: 1px solid #333; }}
        .label {{ color: #00bfff; font-weight: bold; width: 40%; }}
        .correlaciones {{ background: #1a1a2e; padding: 20px; border-radius: 8px; border-left: 4px solid #ffa500; margin-bottom: 20px; }}
        .correlaciones h2 {{ color: #ffa500; }}
        .correlaciones ul {{ margin: 0; padding-left: 20px; }}
        .correlaciones li {{ margin-bottom: 8px; }}
        .resumen {{ background: #1a1a2e; padding: 20px; border-radius: 8px; border-left: 4px solid #00ff88; margin-bottom: 20px; }}
        .resumen h2 {{ color: #00ff88; }}
        .resumen p {{ line-height: 1.8; white-space: pre-wrap; }}
        .riesgo-BAJO {{ color: #00ff88; font-weight: bold; }}
        .riesgo-MEDIO {{ color: #ffa500; font-weight: bold; }}
        .riesgo-ALTO {{ color: #ff4444; font-weight: bold; }}
        .footer {{ text-align: center; color: #555; margin-top: 20px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 CONAN — Informe de Reconocimiento</h1>
        <p><strong>Dominio objetivo:</strong> {dominio}</p>
        <p><strong>Fecha del análisis:</strong> {fecha}</p>
        <p><strong>Nivel de riesgo:</strong> <span class="riesgo-{mod4.get('evaluacion_riesgo', {}).get('nivel', 'BAJO') if mod4 else 'BAJO'}">{mod4.get('evaluacion_riesgo', {}).get('nivel', 'N/A') if mod4 else 'N/A'}</span></p>
    </div>

    <div class="grid">
        {seccion_modulo("🏗️ Módulo 1 — Infraestructura", mod1, [
            ("total_hosts", "Hosts encontrados"),
            ("total_subdominios", "Subdominios encontrados"),
        ])}
        {seccion_modulo("👥 Módulo 2 — Empleados", mod2, [
            ("total_emails", "Emails corporativos"),
            ("total_perfiles", "Perfiles sociales")
        ])}
        {seccion_modulo("📄 Módulo 3 — Documentos", mod3, [
            ("total_documentos", "Documentos analizados"),
            ("usuarios_encontrados", "Usuarios encontrados"),
            ("software_encontrado", "Software identificado")
        ])}
        {seccion_modulo("🛡️ Módulo 4 — Reputación", mod4, [
            ("ip", "IP principal"),
        ])}
    </div>

    <div class="correlaciones">
        <h2>🔗 Correlaciones detectadas</h2>
        {"<ul>" + "".join(f"<li>{c}</li>" for c in correlaciones) + "</ul>" if correlaciones else "<p class='no-data'>No se detectaron correlaciones entre módulos.</p>"}
    </div>

    <div class="resumen">
        <h2>🤖 Resumen ejecutivo (Ollama)</h2>
        <p>{markdown_a_html(resumen)}</p>
    </div>

    <div class="footer">
        <p>Generado por CONAN — Corporate Open-source Network ANalysis</p>
    </div>
</body>
</html>"""

    with open(ruta, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[+] Informe generado en: {ruta}")
    return ruta

def main(dominio):
    print(f"\n{'='*50}")
    print(f"  CONAN - Consolidador")
    print(f"  Dominio: {dominio}")
    print(f"{'='*50}\n")

    print("[*] Cargando resultados de los módulos...")
    mod1 = cargar_resultados_modulo(dominio, 1)
    mod2 = cargar_resultados_modulo(dominio, 2)
    mod3 = cargar_resultados_modulo(dominio, 3)
    mod4 = cargar_resultados_modulo(dominio, 4)

    modulos_encontrados = sum(1 for m in [mod1, mod2, mod3, mod4] if m)
    print(f"[+] {modulos_encontrados} módulos encontrados para {dominio}")

    if modulos_encontrados == 0:
        print("[-] No hay resultados para este dominio. Ejecuta al menos un módulo primero.")
        return

    print("[*] Cruzando datos entre módulos...")
    correlaciones = cruzar_datos(mod1, mod2, mod3, mod4)
    print(f"[+] {len(correlaciones)} correlaciones detectadas.")

    resumen = generar_resumen_ollama(dominio, mod1, mod2, mod3, mod4, correlaciones)
    ruta_informe = generar_informe_html(dominio, mod1, mod2, mod3, mod4, correlaciones, resumen)

    print(f"\n[+] Proceso completado.")
    print(f"[+] Informe disponible en: {ruta_informe}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 consolidador.py <dominio>")
        print("Ejemplo: python3 consolidador.py empresa.com")
        sys.exit(1)
    main(sys.argv[1])
