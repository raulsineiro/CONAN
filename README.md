<div align="center">

<img src="imagenes/banner.png" alt="CONAN" width="600">

# CONAN — Corporate Open-source Network ANalysis

**Distribución Linux especializada en el reconocimiento OSINT corporativo**

</div>

---

## ¿Qué es CONAN?

CONAN es una distribución Linux basada en Ubuntu 22.04 LTS, diseñada específicamente para automatizar la fase de reconocimiento OSINT sobre dominios corporativos. Integra en un mismo sistema un conjunto coherente de herramientas OSINT, scripts propios desarrollados en Python y un modelo de inteligencia artificial ejecutado localmente que unifica los hallazgos en un informe ejecutivo automatizado.

A diferencia de otras distribuciones OSINT existentes (generalmente en inglés y orientadas a la investigación sobre personas o al pentesting general), CONAN se centra específicamente en el reconocimiento de **empresas y organizaciones**, ofreciendo una experiencia completa en castellano y sin necesidad de configuraciones adicionales.

## Características principales

- 🔍 **Cuatro módulos OSINT especializados**: infraestructura, empleados, documentos y reputación.
- 🤖 **Inteligencia artificial local** (Ollama + Mistral 7B): los datos analizados nunca salen del sistema.
- 📊 **Informe HTML automatizado** con detección de correlaciones entre módulos.
- 🛠️ **Menú de 20 herramientas OSINT adicionales** organizadas por categorías.
- 🌐 **Tres navegadores preconfigurados** (Firefox, Chrome, Tor Browser) con marcadores OSINT.
- 💻 **Empaquetado como OVA** listo para importar en VirtualBox.
- 🇪🇸 **Todo en castellano**, desde la interfaz hasta el informe final.


## Uso básico

Una vez importada la OVA en VirtualBox, arranca la máquina virtual. El usuario por defecto es `conan`.

### Lanzar CONAN

Desde el escritorio, haz doble clic en el acceso directo **Iniciar CONAN**, o desde una terminal:

```bash
source /opt/conan/venv/bin/activate
python3 /opt/conan/conan.py
```

Se mostrará el banner y el menú interactivo. Introduce el dominio objetivo y selecciona los módulos que deseas ejecutar.

### Lanzar el menú de herramientas OSINT

Desde el escritorio, haz doble clic en **Herramientas CONAN**, o desde una terminal:

```bash
python3 /opt/conan/herramientas.py
```

Se abrirá un menú con las 20 herramientas OSINT auxiliares organizadas por categorías.

## Módulos disponibles

CONAN se estructura en cuatro módulos independientes. Cada uno recibe como entrada un dominio y genera un fichero JSON con los resultados.

### Módulo 1 — Infraestructura

Descubre hosts, subdominios e IPs expuestas del dominio objetivo.

**Herramientas:** theHarvester, Amass.

### Módulo 2 — Empleados

Busca correos corporativos indexados, verifica en qué servicios están registrados y localiza perfiles públicos asociados.

**Herramientas:** theHarvester, Holehe, Maigret.

### Módulo 3 — Documentos

Localiza documentos públicos del dominio (PDF, DOC, XLS, PPT y variantes) y extrae sus metadatos para identificar usuarios internos y software corporativo.

**Herramientas:** búsqueda propia sobre DuckDuckGo, Exiftool.

### Módulo 4 — Reputación e Inteligencia de Amenazas

Analiza la reputación del dominio y su IP principal en bases de datos de amenazas conocidas, y clasifica el nivel de riesgo global.

**Herramientas / fuentes:** VirusTotal, AbuseIPDB, URLScan.io.

## Consolidador

Cuando se ejecutan varios módulos sobre un mismo dominio, el consolidador reúne los JSONs generados, detecta correlaciones entre ellos y llama al modelo Mistral 7B (a través de Ollama, ejecutándose en local) para generar un resumen ejecutivo en español. El resultado final es un informe HTML almacenado en `/opt/conan/informes/`.
