#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# CONAN - Módulo 4: Reputación e Inteligencia de Amenazas
# Analiza la reputación de un dominio usando VirusTotal y AbuseIPDB.
# Funciona con tiers gratuitos. Si el usuario tiene API keys de pago
# en config.yaml, se usarán automáticamente para obtener más datos.

import requests
import json
import sys
import os
import yaml
import socket
from datetime import datetime

DIR_RESULTADOS = "/opt/conan/resultados"
CONFIG_PATH = "/opt/conan/config.yaml"

def cargar_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[-] No se pudo cargar config.yaml: {e}")
        return {}

def resolver_ip(dominio):
    try:
        ip = socket.gethostbyname(dominio)
        print(f"[+] IP resuelta: {ip}")
        return ip
    except Exception as e:
        print(f"[-] No se pudo resolver la IP de {dominio}: {e}")
        return None

def consultar_virustotal(dominio, api_key):
    print(f"[*] Consultando VirusTotal sobre {dominio}...")
    cabeceras = {"x-apikey": api_key}
    url = f"https://www.virustotal.com/api/v3/domains/{dominio}"
    try:
        respuesta = requests.get(url, headers=cabeceras, timeout=20)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            atributos = datos.get("data", {}).get("attributes", {})
            stats = atributos.get("last_analysis_stats", {})
            votos = atributos.get("total_votes", {})
            categorias = atributos.get("categories", {})
            resultado = {
                "fuente": "VirusTotal",
                "malicioso": stats.get("malicious", 0),
                "sospechoso": stats.get("suspicious", 0),
                "limpio": stats.get("harmless", 0),
                "no_detectado": stats.get("undetected", 0),
                "votos_malicioso": votos.get("malicious", 0),
                "votos_inofensivo": votos.get("harmless", 0),
                "categorias": categorias,
                "reputacion": atributos.get("reputation", 0)
            }
            print(f"[+] VirusTotal: {stats.get('malicious', 0)} motores lo marcan como malicioso.")
            return resultado
        elif respuesta.status_code == 401:
            print("[-] VirusTotal: API key no válida o no configurada.")
            return {"fuente": "VirusTotal", "error": "API key no válida"}
        elif respuesta.status_code == 429:
            print("[-] VirusTotal: límite de peticiones alcanzado.")
            return {"fuente": "VirusTotal", "error": "Límite de peticiones alcanzado"}
        else:
            print(f"[-] VirusTotal: error {respuesta.status_code}")
            return {"fuente": "VirusTotal", "error": f"Error {respuesta.status_code}"}
    except Exception as e:
        print(f"[-] Error consultando VirusTotal: {e}")
        return {"fuente": "VirusTotal", "error": str(e)}

def consultar_abuseipdb(ip, api_key):
    print(f"[*] Consultando AbuseIPDB sobre {ip}...")
    cabeceras = {"Key": api_key, "Accept": "application/json"}
    url = "https://api.abuseipdb.com/api/v2/check"
    params = {"ipAddress": ip, "maxAgeInDays": 90}
    try:
        respuesta = requests.get(url, headers=cabeceras, params=params, timeout=20)
        if respuesta.status_code == 200:
            datos = respuesta.json().get("data", {})
            resultado = {
                "fuente": "AbuseIPDB",
                "ip": ip,
                "puntuacion_abuso": datos.get("abuseConfidenceScore", 0),
                "total_reportes": datos.get("totalReports", 0),
                "ultimo_reporte": datos.get("lastReportedAt", ""),
                "pais": datos.get("countryCode", ""),
                "isp": datos.get("isp", ""),
                "es_proxy": datos.get("isPublic", False),
                "dominio": datos.get("domain", "")
            }
            puntuacion = datos.get("abuseConfidenceScore", 0)
            print(f"[+] AbuseIPDB: puntuación de abuso {puntuacion}/100.")
            return resultado
        elif respuesta.status_code == 401:
            print("[-] AbuseIPDB: API key no válida o no configurada.")
            return {"fuente": "AbuseIPDB", "error": "API key no válida"}
        elif respuesta.status_code == 429:
            print("[-] AbuseIPDB: límite de peticiones alcanzado.")
            return {"fuente": "AbuseIPDB", "error": "Límite de peticiones alcanzado"}
        else:
            print(f"[-] AbuseIPDB: error {respuesta.status_code}")
            return {"fuente": "AbuseIPDB", "error": f"Error {respuesta.status_code}"}
    except Exception as e:
        print(f"[-] Error consultando AbuseIPDB: {e}")
        return {"fuente": "AbuseIPDB", "error": str(e)}

def consultar_urlscan(dominio):
    print(f"[*] Consultando URLScan.io sobre {dominio}...")
    url = f"https://urlscan.io/api/v1/search/?q=domain:{dominio}&size=5"
    try:
        respuesta = requests.get(url, timeout=20)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            resultados = datos.get("results", [])
            escaneos = []
            for r in resultados[:5]:
                escaneos.append({
                    "url": r.get("page", {}).get("url", ""),
                    "fecha": r.get("task", {}).get("time", ""),
                    "veredicto": r.get("verdicts", {}).get("overall", {}).get("malicious", False),
                    "puntuacion": r.get("verdicts", {}).get("overall", {}).get("score", 0)
                })
            print(f"[+] URLScan.io: {len(escaneos)} escaneos encontrados.")
            return {"fuente": "URLScan.io", "escaneos": escaneos, "total": datos.get("total", 0)}
        else:
            print(f"[-] URLScan.io: error {respuesta.status_code}")
            return {"fuente": "URLScan.io", "error": f"Error {respuesta.status_code}"}
    except Exception as e:
        print(f"[-] Error consultando URLScan.io: {e}")
        return {"fuente": "URLScan.io", "error": str(e)}

def evaluar_riesgo(vt, abuseipdb):
    nivel = "BAJO"
    motivos = []

    if "error" not in vt:
        if vt.get("malicioso", 0) > 5:
            nivel = "ALTO"
            motivos.append(f"{vt['malicioso']} motores de VirusTotal lo marcan como malicioso")
        elif vt.get("malicioso", 0) > 0:
            nivel = "MEDIO"
            motivos.append(f"{vt['malicioso']} motores de VirusTotal lo marcan como malicioso")

    if "error" not in abuseipdb:
        puntuacion = abuseipdb.get("puntuacion_abuso", 0)
        if puntuacion > 50:
            nivel = "ALTO"
            motivos.append(f"Puntuación de abuso {puntuacion}/100 en AbuseIPDB")
        elif puntuacion > 10:
            if nivel != "ALTO":
                nivel = "MEDIO"
            motivos.append(f"Puntuación de abuso {puntuacion}/100 en AbuseIPDB")

    return {"nivel": nivel, "motivos": motivos}

def guardar_resultados(dominio, resultado):
    nombre_fichero = f"modulo4_{dominio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    ruta = os.path.join(DIR_RESULTADOS, nombre_fichero)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=4, ensure_ascii=False)
    print(f"\n[+] Resultados guardados en: {ruta}")
    return ruta

def main():
    if len(sys.argv) != 2:
        print("Uso: python3 modulo4_reputacion.py <dominio>")
        print("Ejemplo: python3 modulo4_reputacion.py empresa.com")
        sys.exit(1)

    dominio = sys.argv[1]

    print(f"\n{'='*50}")
    print(f"  CONAN - Módulo 4: Reputación e Inteligencia")
    print(f"  Objetivo: {dominio}")
    print(f"{'='*50}\n")

    config = cargar_config()
    vt_key = config.get("virustotal_api_key", "")
    abuse_key = config.get("abuseipdb_api_key", "")

    if not vt_key:
        print("[!] VirusTotal: no hay API key en config.yaml. Configúrala para obtener resultados.")
    if not abuse_key:
        print("[!] AbuseIPDB: no hay API key en config.yaml. Configúrala para obtener resultados.")

    ip = resolver_ip(dominio)

    vt = consultar_virustotal(dominio, vt_key) if vt_key else {"fuente": "VirusTotal", "error": "API key no configurada"}
    abuseipdb = consultar_abuseipdb(ip, abuse_key) if (abuse_key and ip) else {"fuente": "AbuseIPDB", "error": "API key no configurada"}
    urlscan = consultar_urlscan(dominio)
    riesgo = evaluar_riesgo(vt, abuseipdb)

    resultado = {
        "modulo": "reputacion",
        "dominio": dominio,
        "ip": ip,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "virustotal": vt,
        "abuseipdb": abuseipdb,
        "urlscan": urlscan,
        "evaluacion_riesgo": riesgo
    }

    guardar_resultados(dominio, resultado)

    print(f"\n[+] Evaluación de riesgo: {riesgo['nivel']}")
    if riesgo["motivos"]:
        for motivo in riesgo["motivos"]:
            print(f"    - {motivo}")

if __name__ == "__main__":
    main()
