#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# CONAN - Herramientas auxiliares
# Menú interactivo con 20 herramientas OSINT organizadas por categorías.

import os
import sys

BANNER = """\033[1;36m
  ██╗  ██╗███████╗██████╗ ██████╗  █████╗ ███╗   ███╗██╗███████╗███╗   ██╗████████╗ █████╗ ███████╗
  ██║  ██║██╔════╝██╔══██╗██╔══██╗██╔══██╗████╗ ████║██║██╔════╝████╗  ██║╚══██╔══╝██╔══██╗██╔════╝
  ███████║█████╗  ██████╔╝██████╔╝███████║██╔████╔██║██║█████╗  ██╔██╗ ██║   ██║   ███████║███████╗
  ██╔══██║██╔══╝  ██╔══██╗██╔══██╗██╔══██║██║╚██╔╝██║██║██╔══╝  ██║╚██╗██║   ██║   ██╔══██║╚════██║
  ██║  ██║███████╗██║  ██║██║  ██║██║  ██║██║ ╚═╝ ██║██║███████╗██║ ╚████║   ██║   ██║  ██║███████║
  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚══════╝
\033[0m
"""

# Cada herramienta: (nombre, descripción, comando_a_ejecutar)
HERRAMIENTAS = {
    "Reconocimiento web y DNS": [
        ("whois", "Consulta información de registro de un dominio", "whois {input}"),
        ("dig", "Consultas DNS manuales sobre un dominio", "dig {input}"),
        ("dnsrecon", "Reconocimiento DNS avanzado (registros, transferencias de zona)", "dnsrecon -d {input}"),
        ("wafw00f", "Detecta si un sitio web está protegido por un WAF", "wafw00f {input}"),
        ("whatweb", "Identifica tecnologías y frameworks usados en un sitio web", "whatweb {input}"),
        ("sublist3r", "Enumeración pasiva de subdominios de un dominio", "python3 /opt/Sublist3r/sublist3r.py -d {input}"),
        ("gobuster", "Fuerza bruta de directorios y subdominios (requiere URL con http://)", "gobuster -m dir -u {input} -w /usr/share/dirb/wordlists/common.txt"),
    ],
    "Análisis de red": [
        ("traceroute", "Traza la ruta de red hasta un destino", "traceroute {input}"),
        ("nmap", "Escaneo de puertos y descubrimiento de servicios", "nmap {input}"),
        ("masscan", "Escáner de puertos ultra-rápido sobre una IP (no dominio)", "sudo masscan {input} -p1-1000 --rate=1000"),
    ],
    "OSINT sobre personas y usuarios": [
        ("sherlock", "Busca un nombre de usuario en cientos de redes sociales", "sherlock {input}"),
        ("blackbird", "Búsqueda de usuarios usando la base de datos WhatsMyName", "python3 /opt/blackbird/blackbird.py -u {input}"),
    ],
    "Análisis de ficheros": [
        ("exiftool", "Extrae metadatos de ficheros (imágenes, PDFs, documentos)", "exiftool {input}"),
        ("binwalk", "Analiza ficheros binarios y firmware buscando contenido embebido", "binwalk {input}"),
        ("foremost", "Recuperación de ficheros a partir de imágenes de disco", "foremost -T -i {input} -o /tmp/foremost_output"),
        ("strings", "Extrae cadenas de texto legibles de ficheros binarios", "strings {input}"),
    ],
    "Web y análisis offline": [
        ("httrack", "Descarga completa de un sitio web para análisis offline", "httrack {input} -O /tmp/httrack_output"),
    ],
    "Análisis de tráfico": [
        ("wireshark", "Análisis interactivo de tráfico de red en tiempo real", "wireshark"),
    ],
    "OSINT integrado": [
        ("maltego", "Visualización gráfica de relaciones entre entidades OSINT", "maltego"),
        ("spiderfoot", "Automatización OSINT con módulos propios (interfaz web en :5001)", "bash -c 'source /opt/spiderfoot-venv/bin/activate && python3 /opt/spiderfoot/sf.py -l 127.0.0.1:5001'"),
    ],
}

def limpiar_pantalla():
    os.system("clear")

def imprimir_banner():
    limpiar_pantalla()
    print(BANNER)

def mostrar_menu():
    print("\033[1;37m  ┌─────────────────────────────────────────────────────────────┐")
    print("  │                  HERRAMIENTAS DISPONIBLES                   │")
    print("  └─────────────────────────────────────────────────────────────┘\033[0m\n")

    numero = 1
    indice = {}
    for categoria, herramientas in HERRAMIENTAS.items():
        print(f"\033[1;36m  {categoria}\033[0m")
        for nombre, descripcion, comando in herramientas:
            print(f"\033[1;33m    [{numero:2d}]\033[0m \033[1;37m{nombre:12s}\033[0m — {descripcion}")
            indice[str(numero)] = (nombre, comando)
            numero += 1
        print()

    print(f"\033[1;31m    [ 0] Salir\033[0m\n")
    return indice

def ejecutar_herramienta(nombre, comando):
    if "{input}" in comando:
        print(f"\n\033[1;37m  Introduce el parámetro para {nombre} (dominio, IP, fichero, usuario...):\033[0m ", end="")
        parametro = input().strip()
        if not parametro:
            print("\033[1;31m  [-] Parámetro vacío. Cancelado.\033[0m")
            return
        comando_final = comando.replace("{input}", parametro)
    else:
        comando_final = comando

    print(f"\n\033[1;36m  [*] Ejecutando: {comando_final}\033[0m\n")
    os.system(comando_final)
    print(f"\n\033[1;32m  [+] Ejecución de {nombre} finalizada.\033[0m")
    input("\n\033[1;37m  Pulsa Enter para volver al menú...\033[0m")

def main():
    while True:
        imprimir_banner()
        indice = mostrar_menu()

        print("\033[1;37m  Selección:\033[0m ", end="")
        seleccion = input().strip()

        if seleccion == "0":
            print("\n\033[1;36m  Hasta pronto.\033[0m\n")
            sys.exit(0)

        if seleccion in indice:
            nombre, comando = indice[seleccion]
            ejecutar_herramienta(nombre, comando)
        else:
            print("\033[1;31m  [-] Opción no válida.\033[0m")
            input("\n\033[1;37m  Pulsa Enter para continuar...\033[0m")

if __name__ == "__main__":
    main()
