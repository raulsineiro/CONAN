#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# CONAN - Módulo 1: Infraestructura
# Ejecuta theHarvester y Amass sobre un dominio objetivo
# y guarda los resultados en un JSON unificado.

import subprocess
import json
import sys
import os
from datetime import datetime

DIR_RESULTADOS = "/opt/conan/resultados"

def ejecutar_theharvester(dominio):
    print(f"[*] Ejecutando theHarvester sobre {dominio}...")
    fichero_salida = os.path.join(DIR_RESULTADOS, "theharvester_tmp")
    try:
        subprocess.run(
            ["theHarvester", "-d", dominio, "-b", "hackertarget", "-f", fichero_salida],
            capture_output=True, text=True, timeout=120
        )
        fichero_json = fichero_salida + ".json"
        if os.path.exists(fichero_json):
            with open(fichero_json, "r") as f:
                datos = json.load(f)
            os.remove(fichero_json)
            fichero_xml = fichero_salida + ".xml"
            if os.path.exists(fichero_xml):
                os.remove(fichero_xml)
            return datos
        else:
            print("[-] theHarvester no generó resultados.")
            return {}
    except subprocess.TimeoutExpired:
        print("[-] theHarvester tardó demasiado y fue interrumpido.")
        return {}
    except Exception as e:
        print(f"[-] Error ejecutando theHarvester: {e}")
        return {}

def ejecutar_amass(dominio):
    print(f"[*] Ejecutando Amass sobre {dominio}...")
    fichero_salida = os.path.join(DIR_RESULTADOS, "amass_tmp.json")
    try:
        subprocess.run(
            ["amass", "enum", "-d", dominio, "-json", fichero_salida, "-timeout", "5"],
            capture_output=True, text=True, timeout=360
        )
        subdominios = []
        if os.path.exists(fichero_salida):
            with open(fichero_salida, "r") as f:
                for linea in f:
                    try:
                        entrada = json.loads(linea)
                        if "name" in entrada:
                            subdominios.append(entrada["name"])
                    except json.JSONDecodeError:
                        continue
            os.remove(fichero_salida)
        else:
            print("[-] Amass no generó resultados.")
        return subdominios
    except subprocess.TimeoutExpired:
        print("[-] Amass tardó demasiado y fue interrumpido.")
        return []
    except Exception as e:
        print(f"[-] Error ejecutando Amass: {e}")
        return []

def consolidar_resultados(dominio, datos_harvester, subdominios_amass):
    hosts = datos_harvester.get("hosts", [])
    todos_subdominios = list(set(
        [h.split(":")[0] for h in hosts] + subdominios_amass
    ))
    return {
        "modulo": "infraestructura",
        "dominio": dominio,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hosts": hosts,
        "subdominios": todos_subdominios,
        "total_hosts": len(hosts),
        "total_subdominios": len(todos_subdominios)
    }

def guardar_resultados(dominio, resultado):
    nombre_fichero = f"modulo1_{dominio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    ruta = os.path.join(DIR_RESULTADOS, nombre_fichero)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=4, ensure_ascii=False)
    print(f"\n[+] Resultados guardados en: {ruta}")
    return ruta

def main():
    if len(sys.argv) != 2:
        print("Uso: python3 modulo1_infraestructura.py <dominio>")
        print("Ejemplo: python3 modulo1_infraestructura.py empresa.com")
        sys.exit(1)

    dominio = sys.argv[1]

    print(f"\n{'='*50}")
    print(f"  CONAN - Módulo 1: Infraestructura")
    print(f"  Objetivo: {dominio}")
    print(f"{'='*50}\n")

    datos_harvester = ejecutar_theharvester(dominio)
    subdominios_amass = ejecutar_amass(dominio)
    resultado = consolidar_resultados(dominio, datos_harvester, subdominios_amass)
    ruta = guardar_resultados(dominio, resultado)

    print(f"\n[+] Resumen:")
    print(f"    Hosts encontrados:       {resultado['total_hosts']}")
    print(f"    Subdominios encontrados: {resultado['total_subdominios']}")

if __name__ == "__main__":
    main()

