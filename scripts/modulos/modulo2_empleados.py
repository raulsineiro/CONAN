#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# CONAN - Módulo 2: Empleados
# Busca emails corporativos, verifica registros
# y busca perfiles en redes sociales.

import re
import subprocess
import json
import sys
import os
from datetime import datetime

DIR_RESULTADOS = "/opt/conan/resultados"

def ejecutar_theharvester(dominio):
    print(f"[*] Buscando emails corporativos de {dominio}...")
    fichero_salida = os.path.join(DIR_RESULTADOS, "theharvester_mod2_tmp")
    try:
        subprocess.run(
            ["theHarvester", "-d", dominio, "-b", "baidu,yahoo,duckduckgo,brave", "-f", fichero_salida],
            capture_output=True, text=True, timeout=300
        )
        fichero_json = fichero_salida + ".json"
        emails = []
        if os.path.exists(fichero_json):
            with open(fichero_json, "r") as f:
                datos = json.load(f)
            emails = datos.get("emails", [])
            os.remove(fichero_json)
        fichero_xml = fichero_salida + ".xml"
        if os.path.exists(fichero_xml):
            os.remove(fichero_xml)
        if emails:
            print(f"[+] {len(emails)} emails encontrados.")
        else:
            print("[-] No se encontraron emails.")
        return emails
    except subprocess.TimeoutExpired:
        print("[-] theHarvester tardó demasiado y fue interrumpido.")
        return []
    except Exception as e:
        print(f"[-] Error ejecutando theHarvester: {e}")
        return []

def ejecutar_holehe(email):
    print(f"[*] Verificando registros de {email}...")
    try:
        resultado = subprocess.run(
            ["holehe", "--no-color", email],
            capture_output=True, text=True, timeout=60
        )
        servicios = []
        for linea in resultado.stdout.splitlines():
            linea = linea.strip()
            if "Email" in linea and ("used" in linea or "not used" in linea):
                continue
            coincidencia = re.match(r"^\[\+\]\s+(\S+)$", linea)
            if coincidencia and coincidencia.group(1) != "Email":
                servicios.append(coincidencia.group(1))
        return servicios
    except subprocess.TimeoutExpired:
        print(f"[-] Holehe tardó demasiado para {email}.")
        return []
    except Exception as e:
        print(f"[-] Error ejecutando Holehe: {e}")
        return []

def ejecutar_maigret(usuario):
    print(f"[*] Buscando perfiles de {usuario}...")
    try:
        resultado = subprocess.run(
            ["maigret", usuario, "--no-color"],
            capture_output=True, text=True, timeout=120
        )
        perfiles = []
        for linea in resultado.stdout.splitlines():
            if "[+]" in linea and "http" in linea:
                partes = linea.strip().split()
                for parte in partes:
                    if parte.startswith("http"):
                        perfiles.append(parte)
        return perfiles
    except subprocess.TimeoutExpired:
        print(f"[-] Maigret tardó demasiado para {usuario}.")
        return []
    except Exception as e:
        print(f"[-] Error ejecutando Maigret: {e}")
        return []

def consolidar_resultados(dominio, emails, resultados_holehe, resultados_maigret):
    empleados = []
    for email in emails:
        usuario = email.split("@")[0]
        empleado = {
            "email": email,
            "usuario": usuario,
            "servicios_registrados": resultados_holehe.get(email, []),
            "perfiles_sociales": resultados_maigret.get(usuario, [])
        }
        empleados.append(empleado)
    return {
        "modulo": "empleados",
        "dominio": dominio,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "empleados": empleados,
        "total_emails": len(emails),
        "total_perfiles": sum(len(e["perfiles_sociales"]) for e in empleados)
    }

def guardar_resultados(dominio, resultado):
    nombre_fichero = f"modulo2_{dominio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    ruta = os.path.join(DIR_RESULTADOS, nombre_fichero)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=4, ensure_ascii=False)
    print(f"\n[+] Resultados guardados en: {ruta}")
    return ruta

def main():
    if len(sys.argv) != 2:
        print("Uso: python3 modulo2_empleados.py <dominio>")
        print("Ejemplo: python3 modulo2_empleados.py empresa.com")
        sys.exit(1)

    dominio = sys.argv[1]

    print(f"\n{'='*50}")
    print(f"  CONAN - Módulo 2: Empleados")
    print(f"  Objetivo: {dominio}")
    print(f"{'='*50}\n")

    # Paso 1: Buscar emails con theHarvester
    emails = ejecutar_theharvester(dominio)

    # Paso 2: Verificar emails con Holehe (máximo 3)
    resultados_holehe = {}
    for email in emails[:3]:
        servicios = ejecutar_holehe(email)
        resultados_holehe[email] = servicios

    # Paso 3: Buscar perfiles con Maigret (máximo 3)
    resultados_maigret = {}
    for email in emails[:3]:
        usuario = email.split("@")[0]
        if usuario not in resultados_maigret:
            perfiles = ejecutar_maigret(usuario)
            resultados_maigret[usuario] = perfiles

    # Consolidar y guardar
    resultado = consolidar_resultados(dominio, emails, resultados_holehe, resultados_maigret)
    guardar_resultados(dominio, resultado)

    print(f"\n[+] Resumen:")
    print(f"    Emails encontrados:   {resultado['total_emails']}")
    print(f"    Perfiles encontrados: {resultado['total_perfiles']}")

if __name__ == "__main__":
    main()
