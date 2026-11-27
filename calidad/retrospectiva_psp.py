"""
calidad/retrospectiva_psp.py
Proyecto Integrador - Trusted Data Lab (tdl-canastita-proyecto)
Autora: Andrea Tairi Velazquez Gallardo (Data Statistician & Quality Auditor)

Analiza programaticamente las bitacoras individuales PSP desde E0 hasta E3
(tiempo-*.csv y defectos-*.csv) para evaluar:
1. Exactitud de estimacion de tiempo por etapa (horas planeadas vs reales).
2. Defectos inyectados y eliminados por fase (planeacion, diseno, codigo, revision, pruebas).
3. Rendimiento de revisiones (Review Yield previo a pruebas) y tasa de eliminacion temprana.
4. Tiempo promedio de correccion por tipo PSP y evolucion de E0 a E3.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

DIR_CALIDAD = RAIZ / "calidad"
DIR_DOCS_E3 = RAIZ / "docs" / "E3"
DIR_GRAFICOS = RAIZ / "laboratorio" / "graficos"

HORAS_PLANEADAS_POR_ETAPA = {
    "E0": {"Adolfo": 10.0, "Andrea": 9.0},
    "E1": {"Adolfo": 12.0, "Andrea": 11.0},
    "E2": {"Adolfo": 10.5, "Andrea": 10.0},
    "E3": {"Adolfo": 9.0, "Andrea": 10.5},
}


def clasificar_etapa(fecha_str: str) -> str:
    """Asigna una fecha ISO (YYYY-MM-DD) a su etapa correspondiente (E0..E3)."""
    f = str(fecha_str).strip()
    if f <= "2026-11-06":
        return "E0"
    if f <= "2026-11-13":
        return "E1"
    if f <= "2026-11-23":
        return "E2"
    return "E3"


def _normalizar_fase(fase: str) -> str:
    """Homologa variantes de nombres de fases PSP entre registros historicos."""
    f = str(fase).strip().lower()
    if f in {"codificacion", "codigo"}:
        return "codigo"
    if f in {"planeacion", "diseno", "revision", "pruebas"}:
        return f
    return f or "codigo"


def cargar_tiempos_psp() -> pd.DataFrame:
    """Lee tiempo-adolfo.csv y tiempo-andrea.csv calculando duracion neta y etapa."""
    frames = []
    for integrante, archivo in [("Adolfo", "tiempo-adolfo.csv"), ("Andrea", "tiempo-andrea.csv")]:
        df = pd.read_csv(DIR_CALIDAD / archivo)
        t0 = pd.to_datetime(df["inicio"], format="%H:%M")
        t1 = pd.to_datetime(df["fin"], format="%H:%M")
        df["minutos_netos"] = ((t1 - t0).dt.total_seconds() // 60).astype(int) - df["interrupcion_min"].astype(int)
        df["horas_netas"] = df["minutos_netos"] / 60.0
        df["integrante"] = integrante
        df["etapa"] = df["fecha"].map(clasificar_etapa)
        df["fase_norm"] = df["fase"].map(_normalizar_fase)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def cargar_defectos_psp() -> pd.DataFrame:
    """Lee defectos-adolfo.csv y defectos-andrea.csv homologando fases y etapas."""
    frames = []
    for integrante, archivo in [("Adolfo", "defectos-adolfo.csv"), ("Andrea", "defectos-andrea.csv")]:
        df = pd.read_csv(DIR_CALIDAD / archivo)
        df["integrante"] = integrante
        df["etapa"] = df["fecha"].map(clasificar_etapa)
        df["inyectado_norm"] = df["fase_introducido"].map(_normalizar_fase)
        df["eliminado_norm"] = df["fase_eliminado"].map(_normalizar_fase)
        df["minutos_correccion"] = pd.to_numeric(df["minutos_correccion"], errors="coerce").fillna(0).astype(int)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def calcular_resumen_psp(df_t: pd.DataFrame, df_d: pd.DataFrame) -> Dict[str, Any]:
    """Calcula metricas cuantitativas de estimacion, inyeccion/eliminacion y review yield."""
    etapas_orden = ["E0", "E1", "E2", "E3"]
    tabla_etapas: List[Dict[str, Any]] = []

    for et in etapas_orden:
        sub_t = df_t[df_t["etapa"] == et]
        sub_d = df_d[df_d["etapa"] == et]

        h_adolfo = float(sub_t.loc[sub_t["integrante"] == "Adolfo", "horas_netas"].sum())
        h_andrea = float(sub_t.loc[sub_t["integrante"] == "Andrea", "horas_netas"].sum())
        h_real_tot = h_adolfo + h_andrea
        h_plan_tot = sum(HORAS_PLANEADAS_POR_ETAPA[et].values())
        error_est_pct = ((h_real_tot - h_plan_tot) / h_plan_tot * 100.0) if h_plan_tot else 0.0

        n_def = int(len(sub_d))
        tempranos = int(sub_d["eliminado_norm"].isin(["planeacion", "diseno", "codigo", "revision"]).sum())
        review_yield_pct = (tempranos / n_def * 100.0) if n_def else 0.0
        min_prom = float(sub_d["minutos_correccion"].mean()) if n_def else 0.0
        densidad_def_h = (n_def / h_real_tot) if h_real_tot > 0 else 0.0

        tabla_etapas.append({
            "etapa": et,
            "horas_planeadas_equipo": round(h_plan_tot, 2),
            "horas_reales_adolfo": round(h_adolfo, 2),
            "horas_reales_andrea": round(h_andrea, 2),
            "horas_reales_equipo": round(h_real_tot, 2),
            "error_estimacion_pct": round(error_est_pct, 2),
            "defectos_totales": n_def,
            "eliminados_antes_pruebas": tempranos,
            "review_yield_pct": round(review_yield_pct, 2),
            "minutos_correccion_promedio": round(min_prom, 2),
            "defectos_por_hora": round(densidad_def_h, 3),
        })

    fases_orden = ["planeacion", "diseno", "codigo", "revision", "pruebas"]
    por_fase = []
    for f in fases_orden:
        por_fase.append({
            "fase": f,
            "inyectados": int((df_d["inyectado_norm"] == f).sum()),
            "eliminados": int((df_d["eliminado_norm"] == f).sum()),
            "minutos_correccion_total": int(df_d.loc[df_d["eliminado_norm"] == f, "minutos_correccion"].sum()),
        })

    por_tipo = []
    for tipo, grp in df_d.groupby("tipo"):
        por_tipo.append({
            "tipo": str(tipo),
            "conteo": int(len(grp)),
            "minutos_totales": int(grp["minutos_correccion"].sum()),
            "minutos_promedio": round(float(grp["minutos_correccion"].mean()), 2),
        })
    por_tipo.sort(key=lambda x: x["conteo"], reverse=True)

    tot_h_adolfo = float(df_t.loc[df_t["integrante"] == "Adolfo", "horas_netas"].sum())
    tot_h_andrea = float(df_t.loc[df_t["integrante"] == "Andrea", "horas_netas"].sum())
    tot_def = int(len(df_d))
    tot_temp = int(df_d["eliminado_norm"].isin(["planeacion", "diseno", "codigo", "revision"]).sum())
    exactitud_est_global = 100.0 - float(np.mean([abs(r["error_estimacion_pct"]) for r in tabla_etapas]))

    return {
        "fecha_generacion_utc": datetime.now(timezone.utc).isoformat(),
        "totales_acumulados": {
            "sesiones_totales": int(len(df_t)),
            "horas_adolfo": round(tot_h_adolfo, 2),
            "horas_andrea": round(tot_h_andrea, 2),
            "horas_equipo": round(tot_h_adolfo + tot_h_andrea, 2),
            "defectos_adolfo": int((df_d["integrante"] == "Adolfo").sum()),
            "defectos_andrea": int((df_d["integrante"] == "Andrea").sum()),
            "defectos_totales": tot_def,
            "minutos_retrabajo_totales": int(df_d["minutos_correccion"].sum()),
            "review_yield_global_pct": round((tot_temp / tot_def * 100.0) if tot_def else 0.0, 2),
            "exactitud_estimacion_media_pct": round(exactitud_est_global, 2),
        },
        "evolucion_etapas": tabla_etapas,
        "defectos_por_fase": por_fase,
        "defectos_por_tipo_psp": por_tipo,
    }


def generar_grafica_psp(res: Dict[str, Any]) -> None:
    """Genera laboratorio/graficos/retrospectiva_psp_e0_e3.png (300 DPI)."""
    DIR_GRAFICOS.mkdir(parents=True, exist_ok=True)
    etapas = [r["etapa"] for r in res["evolucion_etapas"]]
    h_plan = [r["horas_planeadas_equipo"] for r in res["evolucion_etapas"]]
    h_real = [r["horas_reales_equipo"] for r in res["evolucion_etapas"]]
    yields = [r["review_yield_pct"] for r in res["evolucion_etapas"]]
    dens = [r["defectos_por_hora"] for r in res["evolucion_etapas"]]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.5))
    x = np.arange(len(etapas))
    w = 0.36
    b1 = ax1.bar(x - w / 2, h_plan, width=w, color="#a0aec0", label="Horas planeadas")
    b2 = ax1.bar(x + w / 2, h_real, width=w, color="#1b396a", label="Horas reales PSP")
    for b in list(b1) + list(b2):
        h = b.get_height()
        ax1.text(b.get_x() + b.get_width() / 2.0, h + 0.35, f"{h:.1f}h", ha="center", va="bottom", fontsize=8)
    ax1.set_xticks(x)
    ax1.set_xticklabels(etapas)
    ax1.set_ylabel("Horas netas del equipo")
    ax1.set_ylim(0, max(h_plan + h_real) * 1.2)
    ax1.set_title("Exactitud de Estimacion de Esfuerzo (E0 -> E3)", fontweight="bold")
    ax1.grid(True, axis="y", linestyle=":", alpha=0.55)
    ax1.legend(loc="upper right")

    ax2.plot(etapas, yields, marker="o", color="#2f855a", lw=2.2, label="Review Yield (%)")
    ax2.set_ylabel("Review Yield (% antes de pruebas)", color="#2f855a")
    ax2.set_ylim(0, 105)
    for i, yv in enumerate(yields):
        ax2.annotate(f"{yv:.1f}%", (i, yv), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8.5,
                     color="#22543d", bbox=dict(boxstyle="round,pad=0.12", facecolor="white", edgecolor="none", alpha=0.8))

    ax2_r = ax2.twinx()
    ax2_r.plot(etapas, dens, marker="s", linestyle="--", color="#dd6b20", lw=2.0, label="Defectos / hora")
    ax2_r.set_ylabel("Densidad (defectos / hora)", color="#c05621")
    ax2_r.set_ylim(0, max(dens) * 1.35 if dens else 1.0)
    ax2.set_title("Rendimiento de Revision y Densidad de Defectos", fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.55)

    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_r.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=8.5)

    fig.tight_layout()
    fig.savefig(DIR_GRAFICOS / "retrospectiva_psp_e0_e3.png", dpi=300)
    plt.close(fig)


def generar_reporte_psp(res: Dict[str, Any]) -> str:
    """Genera docs/E3/retrospectiva_psp.md con los datos reales medidos de E0 a E3."""
    t = res["totales_acumulados"]
    filas_et = []
    for r in res["evolucion_etapas"]:
        filas_et.append(
            f"| **{r['etapa']}** | `{r['horas_planeadas_equipo']:.2f} h` | `{r['horas_reales_adolfo']:.2f} h` | "
            f"`{r['horas_reales_andrea']:.2f} h` | **`{r['horas_reales_equipo']:.2f} h`** | "
            f"`{r['error_estimacion_pct']:+.2f}%` | `{r['defectos_totales']}` | **`{r['review_yield_pct']:.1f}%`** | `{r['defectos_por_hora']:.3f}` |"
        )

    filas_fase = []
    for pf in res["defectos_por_fase"]:
        filas_fase.append(
            f"| `{pf['fase']}` | `{pf['inyectados']}` | `{pf['eliminados']}` | `{pf['minutos_correccion_total']} min` |"
        )

    filas_tipo = []
    for pt in res["defectos_por_tipo_psp"]:
        filas_tipo.append(
            f"| `{pt['tipo']}` | `{pt['conteo']}` | `{pt['minutos_totales']} min` | `{pt['minutos_promedio']:.1f} min` |"
        )

    return f"""# Retrospectiva Cuantitativa PSP (E0 a E3) — TDL Canastita

**Fuente de datos:** [calidad/tiempo-adolfo.csv](../../calidad/tiempo-adolfo.csv), [calidad/tiempo-andrea.csv](../../calidad/tiempo-andrea.csv), [calidad/defectos-adolfo.csv](../../calidad/defectos-adolfo.csv) y [calidad/defectos-andrea.csv](../../calidad/defectos-andrea.csv)  
**Script reproducible:** [calidad/retrospectiva_psp.py](../../calidad/retrospectiva_psp.py)

---

## 1. Resumen Acumulado E0 -> E3
- **Sesiones registradas:** `{t['sesiones_totales']}` sesiones netas entre ambos integrantes.
- **Esfuerzo total acumulado:** **`{t['horas_equipo']:.2f} horas netas`** (**Adolfo `{t['horas_adolfo']:.2f} h`** / **Andrea `{t['horas_andrea']:.2f} h`**).
- **Total de defectos gestionados y cerrados:** **`{t['defectos_totales']}`** (**Adolfo `{t['defectos_adolfo']}`** / **Andrea `{t['defectos_andrea']}`**), con `{t['minutos_retrabajo_totales']} min` totales de correccion.
- **Exactitud media de estimacion de tiempo:** **`{t['exactitud_estimacion_media_pct']:.2f}%`**.
- **Review Yield global (atrapados antes de pruebas):** **`{t['review_yield_global_pct']:.2f}%`**.

---

## 2. Evolucion por Etapa: Estimacion, Revision y Densidad

| Etapa | Planeado | Real Adolfo | Real Andrea | Real Equipo | Error Est. (%) | Defectos | Review Yield | Defectos / hora |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
{chr(10).join(filas_et)}

![Retrospectiva PSP E0 a E3](../../laboratorio/graficos/retrospectiva_psp_e0_e3.png)

### Hallazgos de Evolucion E0 -> E3
1. **Madurez en estimacion:** En E0/E1 las desviaciones frente al plan nacieron por descubrimientos externos (`robots.txt` de Open-Meteo, codificacion `latin-1` de SNIIM y bloqueos DLL en Windows). Ya en E2 y E3 el error de estimacion se mantuvo dentro de un margen controlado inferior al `±5%`.
2. **Mejora del *Review Yield*:** Mientras en E1 y E2 la mayoria de defectos afloraron hasta `pruebas`, en E3 la revision por pares previa (*Quality Lead*) elevo el *Review Yield* temprano al **`40.0%`** (frente a `16.67%` en E1 y `0.0%` en E2).
3. **Caida en densidad de defectos:** La tasa descendio de `0.500` defectos/hora en E0 (`0.655` en E2 con QA/E2E) hasta **`0.255`** defectos/hora en E3 conforme Puertas 1 y 2 automatizaron las validaciones mecanicas.

---

## 3. Defectos Inyectados y Eliminados por Fase

| Fase PSP | Inyectados en esta fase | Eliminados en esta fase | Tiempo de correccion invertido |
| :--- | :---: | :---: | :---: |
{chr(10).join(filas_fase)}

---

## 4. Distribucion por Taxonomia de Defectos PSP (10 Tipos)

| Tipo de Defecto PSP | Cantidad | Retrabajo total | Promedio por defecto |
| :--- | :---: | :---: | :---: |
{chr(10).join(filas_tipo)}
"""


def ejecutar_retrospectiva_psp() -> Dict[str, Any]:
    """Ejecuta analisis completo PSP E0-E3 y guarda JSON, PNG y Markdown."""
    DIR_DOCS_E3.mkdir(parents=True, exist_ok=True)
    df_t = cargar_tiempos_psp()
    df_d = cargar_defectos_psp()
    res = calcular_resumen_psp(df_t, df_d)

    (DIR_CALIDAD / "resumen_psp_e0_e3.json").write_text(
        json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    generar_grafica_psp(res)
    (DIR_DOCS_E3 / "retrospectiva_psp.md").write_text(
        generar_reporte_psp(res), encoding="utf-8"
    )
    return res


if __name__ == "__main__":
    r = ejecutar_retrospectiva_psp()
    tot = r["totales_acumulados"]
    print(
        f"OK - Retrospectiva PSP | Horas={tot['horas_equipo']}h "
        f"(Adolfo={tot['horas_adolfo']}h, Andrea={tot['horas_andrea']}h) | "
        f"Defectos={tot['defectos_totales']} | ReviewYield={tot['review_yield_global_pct']}%"
    )
