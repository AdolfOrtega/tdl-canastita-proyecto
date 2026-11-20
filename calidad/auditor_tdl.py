"""
calidad/auditor_tdl.py
Proyecto Integrador - Trusted Data Lab (tdl-canastita-proyecto)
Autora: Andrea Tairi Velazquez Gallardo (Data Statistician & Quality Auditor)

Herramienta CLI de auditoria tecnica bajo criterios ISO/IEC 25010, ISO/IEC 25012
y directrices ISO 19011 para evaluar repositorios del ecosistema Trusted Data Lab
(propio o de otro equipo en auditoria cruzada).

Uso:
  python calidad/auditor_tdl.py .
  python calidad/auditor_tdl.py /ruta/al/repo-equipo-par
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

import pandas as pd

DIRECTORIOS_REQUERIDOS = [
    "docs",
    "calidad",
    "extractores",
    "pipeline",
    "data/bronce",
    "data/plata",
    "data/oro",
    "data/cuarentena",
    "laboratorio",
    "tablero",
    "tests",
    ".github/workflows",
]


def auditar_repositorio(ruta_repo: Path) -> Dict[str, Any]:
    """Inspecciona un repositorio TDL y clasifica hallazgos en CRITICO, MAYOR o MENOR."""
    raiz = ruta_repo.resolve()
    hallazgos: List[Dict[str, str]] = []

    def _agregar(sev: str, categoria: str, evidencia: str, recomendacion: str) -> None:
        hallazgos.append(
            {
                "severidad": sev,
                "categoria": categoria,
                "evidencia": evidencia,
                "recomendacion": recomendacion,
            }
        )

    # 1. Estructura base del Kit TDL
    faltantes = [d for d in DIRECTORIOS_REQUERIDOS if not (raiz / d).exists()]
    if faltantes:
        _agregar(
            "MAYOR",
            "Estructura del Repositorio",
            f"Faltan directorios del Kit TDL: {faltantes}",
            "Completar la arquitectura de carpetas recomendada para garantizar reproducibilidad.",
        )

    # 2. Seguridad (.env y .gitignore)
    ruta_gi = raiz / ".gitignore"
    if not ruta_gi.exists() or ".env" not in ruta_gi.read_text(encoding="utf-8", errors="ignore"):
        _agregar(
            "CRITICO",
            "Seguridad (ISO 25010)",
            ".gitignore inexistente o sin proteccion para archivos .env",
            "Agregar `.env` y `.env.*` al .gitignore y verificar historial con gitleaks.",
        )

    if (raiz / ".env").exists():
        pass  # Permitido en local si esta en .gitignore

    # 3. Flujos de CI y captura programada
    wf_dir = raiz / ".github" / "workflows"
    workflows = list(wf_dir.glob("*.yml")) + list(wf_dir.glob("*.yaml")) if wf_dir.exists() else []
    tiene_ci_push = False
    for wf in workflows:
        txt = wf.read_text(encoding="utf-8", errors="ignore")
        if "push:" in txt and "pytest" in txt:
            tiene_ci_push = True
            break
    if not tiene_ci_push:
        _agregar(
            "MAYOR",
            "Integracion Continua (Puerta 2)",
            f"Se encontraron {len(workflows)} workflows pero ninguno ejecuta pytest automaticamente ante cada push.",
            "Agregar workflow CI disparado en `push` que ejecute `pytest` y validaciones de seguridad.",
        )

    # 4. Bitacora y Fiabilidad (ISO 25010)
    ruta_bit = raiz / "calidad" / "bitacora_captura.csv"
    disp_pct = 0.0
    if not ruta_bit.exists():
        _agregar(
            "CRITICO",
            "Fiabilidad (ISO 25010)",
            "No existe calidad/bitacora_captura.csv para comprobar disponibilidad real.",
            "Registrar cada ejecucion de captura programada con timestamp, estado y duracion.",
        )
    else:
        df_b = pd.read_csv(ruta_bit)
        sub = df_b[df_b["modo"] == "diario"] if "modo" in df_b.columns else df_b
        if sub.empty:
            sub = df_b
        if not sub.empty and "estado" in sub.columns:
            disp_pct = float((sub["estado"] == "EXITO").mean() * 100.0)
            if disp_pct < 95.0:
                _agregar(
                    "MAYOR",
                    "Fiabilidad (ISO 25010)",
                    f"Disponibilidad medida en {disp_pct:.2f}%, por debajo del umbral TDL (95%).",
                    "Revisar registros de FALLA en bitacora y aplicar retroceso exponencial en extractores.",
                )

    # 5. Calidad de datos Oro (ISO 25012) y Cuarentena
    archivos_oro = [p for p in (raiz / "data" / "oro").glob("*.csv")] if (raiz / "data" / "oro").exists() else []
    if not archivos_oro:
        _agregar(
            "CRITICO",
            "Calidad de Datos (ISO 25012)",
            "No se encontro ningun dataset analitico CSV en data/oro/.",
            "Ejecutar el pipeline de transformacion Medallion hasta poblar Capa Oro.",
        )
    else:
        df_o = pd.read_csv(archivos_oro[0])
        cols_lin = [c for c in df_o.columns if c.startswith("_linaje_")]
        if not cols_lin:
            _agregar(
                "MAYOR",
                "Trazabilidad (ISO 25012)",
                f"{archivos_oro[0].name} no incluye columnas de linaje por registro (_linaje_*).",
                "Incorporar fuente origen y fecha de captura en cada fila de Capa Oro.",
            )

    archivos_test = list((raiz / "tests").glob("test_*.py")) if (raiz / "tests").exists() else []
    if not archivos_test:
        _agregar(
            "CRITICO",
            "Mantenibilidad / Pruebas",
            "No existen pruebas automatizadas test_*.py en tests/.",
            "Implementar suite pytest con cobertura >= 60%.",
        )

    conteos = {
        "CRITICO": sum(1 for h in hallazgos if h["severidad"] == "CRITICO"),
        "MAYOR": sum(1 for h in hallazgos if h["severidad"] == "MAYOR"),
        "MENOR": sum(1 for h in hallazgos if h["severidad"] == "MENOR"),
    }

    return {
        "repositorio_auditado": raiz.name,
        "disponibilidad_medida_pct": round(disp_pct, 2),
        "total_hallazgos": len(hallazgos),
        "conteos_severidad": conteos,
        "hallazgos": hallazgos,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Auditor TDL bajo ISO 25010 / 25012 / 19011")
    parser.add_argument("ruta", nargs="?", default=".", help="Ruta del repositorio a auditar")
    parser.add_argument("--json", action="store_true", help="Imprime salida en JSON")
    args = parser.parse_args()

    res = auditar_repositorio(Path(args.ruta))
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(f"=== Auditoria TDL: {res['repositorio_auditado']} ===")
        print(f"Disponibilidad medida: {res['disponibilidad_medida_pct']}%")
        print(f"Hallazgos: {res['conteos_severidad']}")
        for h in res["hallazgos"]:
            print(f" - [{h['severidad']}] {h['categoria']}: {h['evidencia']} -> {h['recomendacion']}")
        if res["total_hallazgos"] == 0:
            print("OK - Cero hallazgos abiertos en la auditoria automatizada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
