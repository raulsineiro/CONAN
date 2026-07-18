#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# CONAN - Módulo 3: Documentos
# Busca documentos públicos de un dominio mediante DuckDuckGo
# (consultas site:dominio filetype:X), los descarga y extrae
# sus metadatos con Exiftool.

import subprocess
import json
import sys
import os
import time
import shutil
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime

DIR_RESULTADOS = "/opt/conan/resultados"
TIPOS_FICHERO = ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"]
MAX_DOCUMENTOS_POR_TIPO = 5
CABECERAS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

def extraer_url_real(href):
    if "uddg=" in href:
        parsed = urlparse(href)
        qs = parse_qs(parsed.query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
    return href

def buscar_documentos(dominio):
    print(f"[*] Buscando documentos públicos de {dominio} en DuckDuckGo...")
    urls_encontradas = []
    for tipo in TIPOS_FICHERO:
        consulta = f"site:{dominio} filetype:{tipo}"
        try:
            respuesta = requests.post(
                "https://html.duckduckgo.com/html/",
                data={"q": consulta},
                headers=CABECERAS,
                timeout=20
            )
            sopa = BeautifulSoup(respuesta.text, "html.parser")
            enlaces = sopa.find_all("a", class_="result__a")
            encontrados_tipo = 0
            for enlace in enlaces:
                href = enlace.get("href", "")
                url_real = extraer_url_real(href)
                if url_real.lower().endswith(f".{tipo}") and url_real not in urls_encontradas:
                    urls_encontradas.append(url_real)
                    encontrados_tipo += 1
                if encontrados_tipo >= MAX_DOCUMENTOS_POR_TIPO:
                    break
            print(f"    .{tipo}: {encontrados_tipo} encontrados")
        except Exception as e:
            print(f"[-] Error buscando .{tipo}: {e}")
        time.sleep(2)
    return urls_encontradas

def descargar_documentos(urls, dir_destino):
    os.makedirs(dir_destino, exist_ok=True)
    ficheros_descargados = []
    for indice, url in enumerate(urls, start=1):
        try:
            nombre_original = os.path.basename(urlparse(url).path)
            if not nombre_original:
                continue
            nombre_fichero = f"doc_{indice:03d}_{nombre_original}"
            ruta_destino = os.path.join(dir_destino, nombre_fichero)
            respuesta = requests.get(url, headers=CABECERAS, timeout=20)
            if respuesta.status_code == 200:
                with open(ruta_destino, "wb") as f:
                    f.write(respuesta.content)
                ficheros_descargados.append(ruta_destino)
        except Exception as e:
            print(f"[-] Error descargando {url}: {e}")
    return ficheros_descargados

def ejecutar_exiftool(ruta_fichero):
    try:
        resultado = subprocess.run(
            ["exiftool", "-j", ruta_fichero],
            capture_output=True, text=True, timeout=30
        )
        datos = json.loads(resultado.stdout)
        return datos[0] if datos else {}
    except Exception as e:
        print(f"[-] Error extrayendo metadatos de {ruta_fichero}: {e}")
        return {}

def extraer_campos_relevantes(metadatos):
    campos_interes = ["Author", "Creator", "LastModifiedBy", "Producer",
                       "Software", "Company", "CreateDate", "ModifyDate"]
    return {campo: metadatos[campo] for campo in campos_interes if campo in metadatos}

def consolidar_resultados(dominio, ficheros):
    documentos = []
    usuarios_encontrados = set()
    software_encontrado = set()

    for ruta in ficheros:
        print(f"[*] Analizando metadatos de {os.path.basename(ruta)}...")
        metadatos = ejecutar_exiftool(ruta)
        relevantes = extraer_campos_relevantes(metadatos)
        documentos.append({
            "fichero": os.path.basename(ruta),
            "metadatos": relevantes
        })
        for campo in ["Author", "Creator", "LastModifiedBy"]:
            if campo in relevantes:
                usuarios_encontrados.add(relevantes[campo])
        for campo in ["Producer", "Software"]:
            if campo in relevantes:
                software_encontrado.add(relevantes[campo])

    return {
        "modulo": "documentos",
        "dominio": dominio,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "documentos": documentos,
        "usuarios_encontrados": list(usuarios_encontrados),
        "software_encontrado": list(software_encontrado),
        "total_documentos": len(documentos)
    }

def guardar_resultados(dominio, resultado):
    nombre_fichero = f"modulo3_{dominio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    ruta = os.path.join(DIR_RESULTADOS, nombre_fichero)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=4, ensure_ascii=False)
    print(f"\n[+] Resultados guardados en: {ruta}")
    return ruta

def limpiar_temporales(dir_temp):
    if os.path.exists(dir_temp):
        shutil.rmtree(dir_temp)

def main():
    if len(sys.argv) != 2:
        print("Uso: python3 modulo3_documentos.py <dominio>")
        print("Ejemplo: python3 modulo3_documentos.py empresa.com")
        sys.exit(1)

    dominio = sys.argv[1]

    print(f"\n{'='*50}")
    print(f"  CONAN - Módulo 3: Documentos")
    print(f"  Objetivo: {dominio}")
    print(f"{'='*50}\n")

    dir_temp = os.path.join(DIR_RESULTADOS, f"docs_tmp_{dominio}")

    urls = buscar_documentos(dominio)
    print(f"\n[+] Total documentos localizados: {len(urls)}")

    ficheros = descargar_documentos(urls, dir_temp)
    print(f"[+] Total documentos descargados: {len(ficheros)}")

    resultado = consolidar_resultados(dominio, ficheros)
    guardar_resultados(dominio, resultado)
    limpiar_temporales(dir_temp)

    print(f"\n[+] Resumen:")
    print(f"    Documentos analizados: {resultado['total_documentos']}")
    print(f"    Usuarios encontrados:  {len(resultado['usuarios_encontrados'])}")
    print(f"    Software encontrado:   {len(resultado['software_encontrado'])}")

if __name__ == "__main__":
    main()
