#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# CONAN - Script principal
# Corporate Open-source Network ANalysis

import os
import sys
import time

# Añadir el directorio de módulos al path
sys.path.insert(0, "/opt/conan/modulos")
sys.path.insert(0, "/opt/conan")

BANNER = """
\033[1;36m
   ██████╗ ██████╗ ███╗   ██╗ █████╗ ███╗   ██╗
  ██╔════╝██╔═══██╗████╗  ██║██╔══██╗████╗  ██║
  ██║     ██║   ██║██╔██╗ ██║███████║██╔██╗ ██║
  ██║     ██║   ██║██║╚██╗██║██╔══██║██║╚██╗██║
  ╚██████╗╚██████╔╝██║ ╚████║██║  ██║██║ ╚████║
   ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═══╝
\033[0m
\033[1;37m       Corporate Open-source Network ANalysis\033[0m
\033[0;36m          TFM — Máster en Ciberseguridad\033[0m
"""

MENU = """
\033[1;37m  ┌─────────────────────────────────────────┐
  │          MÓDULOS DISPONIBLES            │
  ├─────────────────────────────────────────┤
  │  [1]  Infraestructura                   │
  │  [2]  Empleados                         │
  │  [3]  Documentos                        │
  │  [4]  Reputación e Inteligencia         │
  │  [5]  Todos los módulos                 │
  ├─────────────────────────────────────────┤
  │  [0]  Salir                             │
  └─────────────────────────────────────────┘\033[0m
"""

def limpiar_pantalla():
    os.system("clear")

def imprimir_banner():
    limpiar_pantalla()
    print(BANNER)

def pedir_dominio():
    print("\033[1;37m  Introduce el dominio objetivo:\033[0m ", end="")
    dominio = input().strip()
    if not dominio:
        print("\033[1;31m  [-] El dominio no puede estar vacío.\033[0m")
        return None
    return dominio

def pedir_modulos():
    print(MENU)
    print("\033[1;37m  Selección:\033[0m ", end="")
    seleccion = input().strip()
    return seleccion

def ejecutar_modulo(numero, dominio):
    modulos = {
        "1": ("/opt/conan/modulos/modulo1_infraestructura.py", "Infraestructura"),
        "2": ("/opt/conan/modulos/modulo2_empleados.py", "Empleados"),
        "3": ("/opt/conan/modulos/modulo3_documentos.py", "Documentos"),
        "4": ("/opt/conan/modulos/modulo4_reputacion.py", "Reputación e Inteligencia"),
    }
    if numero not in modulos:
        return
    ruta, nombre = modulos[numero]
    print(f"\n\033[1;36m  [*] Ejecutando Módulo {numero}: {nombre}...\033[0m\n")
    python = "/opt/conan/venv/bin/python3"
    os.system(f"{python} {ruta} {dominio}")

def ejecutar_consolidador(dominio):
    print(f"\n\033[1;36m  [*] Generando informe consolidado...\033[0m\n")
    python = "/opt/conan/venv/bin/python3"
    os.system(f"{python} /opt/conan/consolidador.py {dominio}")

def main():
    imprimir_banner()

    dominio = pedir_dominio()
    if not dominio:
        sys.exit(1)

    print(f"\n\033[1;32m  [+] Objetivo: {dominio}\033[0m")

    seleccion = pedir_modulos()

    if seleccion == "0":
        print("\n\033[1;36m  Hasta pronto.\033[0m\n")
        sys.exit(0)

    elif seleccion == "5":
        for num in ["1", "2", "3", "4"]:
            ejecutar_modulo(num, dominio)
        ejecutar_consolidador(dominio)

    elif seleccion in ["1", "2", "3", "4"]:
        ejecutar_modulo(seleccion, dominio)
        print(f"\n\033[1;37m  ¿Generar informe con los datos disponibles? [s/n]:\033[0m ", end="")
        respuesta = input().strip().lower()
        if respuesta == "s":
            ejecutar_consolidador(dominio)

    else:
        print("\033[1;31m  [-] Opción no válida.\033[0m")
        sys.exit(1)

    print(f"\n\033[1;32m  [+] Proceso completado para {dominio}.\033[0m\n")

if __name__ == "__main__":
    main()
