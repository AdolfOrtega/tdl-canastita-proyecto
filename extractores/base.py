"""
extractores/base.py
Proyecto Integrador - Trusted Data Lab (tdl-canastita-proyecto)
Alumnos: Adolfo Rodriguez y Andrea Tairi Velazquez Gallardo

Modulo base del extractor etico (partiendo del codigo base del Kit de arranque
del documento del proyecto): revisa robots.txt, manda nuestro correo en el
User-Agent y espera entre peticiones para no saturar el servidor.
"""

import os
import time
import urllib.robotparser
from urllib.parse import urlparse
import requests

# Correo institucional del equipo para identificar el scraper
UA = "TDL-Observatorio/1.0 (proyecto academico; contacto: 23460528@colima.tecnm.mx)"


def cargar_env():
    """Carga las variables del archivo .env local si existe."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta_env = os.path.join(base_dir, ".env")
    if not os.path.exists(ruta_env):
        return

    with open(ruta_env, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, valor = linea.split("=", 1)
            clave = clave.strip()
            valor = valor.strip().strip('"').strip("'")
            if clave and valor and not os.getenv(clave):
                os.environ[clave] = valor


cargar_env()


class ExtractorEtico:
    def __init__(self, pausa=1.5):
        self.pausa = pausa  # segundos minimos entre peticiones al mismo dominio
        self.robots = {}
        self.ultimo = {}
        self.sesion = requests.Session()
        self.sesion.headers["User-Agent"] = UA

    def _reglas(self, url):
        p = urlparse(url)
        base = f"{p.scheme}://{p.netloc}"
        if base not in self.robots:
            rp = urllib.robotparser.RobotFileParser(base + "/robots.txt")
            try:
                resp = self.sesion.get(base + "/robots.txt", timeout=10)
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                else:
                    rp.allow_all = True
            except Exception:
                rp.allow_all = True
            self.robots[base] = rp
        return self.robots[base]

    def get(self, url, params=None, headers=None, intentos=3):
        reglas = self._reglas(url)
        if not reglas.can_fetch(UA, url):
            raise PermissionError(f"robots.txt no permite {url}")

        dominio = urlparse(url).netloc
        pausa = max(self.pausa, reglas.crawl_delay(UA) or 0)
        espera = pausa - (time.time() - self.ultimo.get(dominio, 0))
        if espera > 0:
            time.sleep(espera)

        for i in range(intentos):
            try:
                r = self.sesion.get(url, params=params, headers=headers, timeout=25)
                self.ultimo[dominio] = time.time()
                if r.status_code == 429 or r.status_code >= 500:
                    time.sleep(pausa * 2 ** i)  # espera exponencial ante saturacion
                    continue
                r.raise_for_status()
                return r
            except requests.RequestException as e:
                self.ultimo[dominio] = time.time()
                if i == intentos - 1:
                    raise RuntimeError(f"Sin respuesta valida de {url} tras {intentos} intentos: {e}")
                time.sleep(pausa * 2 ** i)

        raise RuntimeError(f"Sin respuesta valida de {url} tras {intentos} intentos")
