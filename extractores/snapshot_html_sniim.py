"""
extractores/snapshot_html_sniim.py
Proyecto Integrador - Trusted Data Lab (tdl-canastita-proyecto)
Autora: Andrea Tairi Velazquez Gallardo (Data Statistician & Quality Auditor)

Descarga una unica copia local congelada de 6 paginas HTML reales del portal
SNIIM (2 ventanas temporales por cada una de las 3 plazas: Colima, Guadalajara
y Morelia) para ejecutar el experimento factorial 2^3 de la Entrega E2 de forma
100% reproducible sin saturar el servidor gubernamental.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from extractores.base import ExtractorEtico
from extractores.sniim_canasta import PLAZAS_OCCIDENTE, URL_SNIIM, parsear_tabla_sniim

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
DIR_SNAPSHOT = RAIZ_PROYECTO / "data" / "bronce" / "sniim_html_snapshot"

VENTANAS_SNAPSHOT = [
    ("w1", "01/10/2026", "15/10/2026"),
    ("w2", "16/10/2026", "31/10/2026"),
]


def capturar_snapshot_local() -> Dict[str, Any]:
    """Descarga 6 paginas HTML reales del SNIIM y genera su manifiesto SHA-256."""
    DIR_SNAPSHOT.mkdir(parents=True, exist_ok=True)
    ext = ExtractorEtico(pausa=1.5)
    captura_ts = datetime.now(timezone.utc).isoformat()
    paginas: List[Dict[str, Any]] = []
    idx = 1

    for dest_id, info in PLAZAS_OCCIDENTE.items():
        ciudad_slug = info["ciudad"].lower()
        for etiqueta_w, f_ini, f_fin in VENTANAS_SNAPSHOT:
            params = {
                "fechaInicio": f_ini,
                "fechaFinal": f_fin,
                "ProductoId": "-1",
                "OrigenId": "-1",
                "Origen": "Todos",
                "DestinoId": str(dest_id),
                "Destino": info["ciudad"],
                "PreciosPorId": "1",
                "RegistrosPorPagina": "500",
            }
            resp = ext.get(URL_SNIIM, params=params)
            html_texto = resp.content.decode("latin-1", errors="replace")
            nombre_archivo = f"page_{idx:02d}_{ciudad_slug}_{etiqueta_w}.html"
            ruta_html = DIR_SNAPSHOT / nombre_archivo
            ruta_html.write_text(html_texto, encoding="utf-8")

            filas_ref = parsear_tabla_sniim(html_texto, info, captura_ts, resp.url)
            sha = hashlib.sha256(ruta_html.read_bytes()).hexdigest()

            paginas.append(
                {
                    "indice": idx,
                    "archivo": nombre_archivo,
                    "plaza_id": dest_id,
                    "ciudad": info["ciudad"],
                    "estado": info["estado"],
                    "nombre_plaza": info["nombre_plaza"],
                    "fecha_inicio": f_ini,
                    "fecha_final": f_fin,
                    "tamano_bytes": ruta_html.stat().st_size,
                    "filas_referencia": len(filas_ref),
                    "url_origen": resp.url,
                    "sha256": sha,
                }
            )
            print(
                f"OK - {nombre_archivo}: {ruta_html.stat().st_size / 1024:.1f} KB, "
                f"{len(filas_ref)} filas de referencia"
            )
            idx += 1

    manifiesto = {
        "descripcion": "Copia local congelada de paginas HTML del SNIIM para diseño experimental reproducible (E2)",
        "fecha_captura_utc": captura_ts,
        "total_paginas": len(paginas),
        "total_filas_referencia_lote": sum(p["filas_referencia"] for p in paginas),
        "paginas": paginas,
    }
    ruta_meta = DIR_SNAPSHOT / "snapshot_manifest.meta.json"
    ruta_meta.write_text(
        json.dumps(manifiesto, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return manifiesto


if __name__ == "__main__":
    capturar_snapshot_local()
