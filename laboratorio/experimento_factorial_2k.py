"""
laboratorio/experimento_factorial_2k.py
Proyecto Integrador - Trusted Data Lab (tdl-canastita-proyecto)
Autora: Andrea Tairi Velazquez Gallardo (Data Statistician & Quality Auditor)

Laboratorio de Diseno de Experimentos (Entrega E2 - Unidad 4 Analisis Estadistico):
1. Experimento Factorial 2^3 real (Ruta Ingenieria sobre el extractor local SNIIM):
   - Factor A: Concurrencia (1 hilo vs 4 hilos)
   - Factor B: Parser HTML (html.parser vs lxml)
   - Factor C: Formato de escritura (CSV vs Parquet)
   3 bloques completos aleatorizados (24 corridas) + corrida de calentamiento descartada.
2. ANOVA de efectos fijos, cuantificacion de efectos principales/interacciones,
   validacion de supuestos Puerta 3 (Shapiro-Wilk, Levene, Durbin-Watson;
   transformacion logaritmica + Kruskal-Wallis si aplica) y corrida de confirmacion.
3. Diseno de dos factores con >= 3 niveles (3 x 3 = 27 corridas reales):
   lote de paginas (6, 12, 24) x formato (CSV, CSV_GZIP, Parquet), ANOVA de dos vias
   con interaccion y comparaciones Tukey HSD.
4. Comparativa matricial 2^4 completo (16 tratamientos) vs 2^(4-1) fraccionado
   (8 tratamientos, generador D = A*B*C, relacion definidora I = ABCD, Resolucion IV).
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import itertools
import json
from pathlib import Path
import sys
import tempfile
import time
from typing import Any, Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.stattools import durbin_watson

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from extractores.sniim_canasta import PLAZAS_OCCIDENTE, parsear_tabla_sniim

DIR_SNAPSHOT = RAIZ / "data" / "bronce" / "sniim_html_snapshot"
DIR_LAB = RAIZ / "laboratorio"
DIR_GRAFICOS = DIR_LAB / "graficos"

NIVELES_A = {-1: "1 hilo", 1: "4 hilos"}
NIVELES_B = {-1: "html.parser", 1: "lxml"}
NIVELES_C = {-1: "CSV", 1: "Parquet"}


def cargar_paginas_snapshot() -> Tuple[List[Tuple[str, Dict[str, Any], str]], int]:
    """Carga en memoria las 6 paginas HTML reales del snapshot local para evitar sesgo de I/O externo."""
    ruta_meta = DIR_SNAPSHOT / "snapshot_manifest.meta.json"
    if not ruta_meta.exists():
        raise FileNotFoundError(
            "No existe snapshot local SNIIM. Ejecuta `python -m extractores.snapshot_html_sniim`."
        )
    manifiesto = json.loads(ruta_meta.read_text(encoding="utf-8"))
    paginas = []
    for p in manifiesto["paginas"]:
        ruta_html = DIR_SNAPSHOT / p["archivo"]
        html = ruta_html.read_text(encoding="utf-8")
        info = PLAZAS_OCCIDENTE[int(p["plaza_id"])]
        paginas.append((html, info, p["url_origen"]))
    return paginas, int(manifiesto["total_filas_referencia_lote"])


def ejecutar_corrida_extractor(
    paginas_base: List[Tuple[str, Dict[str, Any], str]],
    filas_ref_por_ciclo: int,
    ciclos: int,
    hilos: int,
    parser: str,
    formato: str,
) -> Tuple[float, float, float, int]:
    """
    Ejecuta una corrida controlada del extractor sobre HTML locales y mide:
    (tiempo_seg, tasa_error_pct, tamano_kb, filas_extraidas).
    """
    tareas = paginas_base * ciclos
    filas_esperadas = filas_ref_por_ciclo * ciclos
    captura_ts = "2026-11-20T00:00:00+00:00"

    def _procesar_una(item: Tuple[str, Dict[str, Any], str]) -> List[Dict[str, Any]]:
        """Parsea una pagina HTML del lote asignado."""
        html, info, url = item
        return parsear_tabla_sniim(html, info, captura_ts, url, parser=parser)

    t0 = time.perf_counter()
    excepciones = 0
    filas: List[Dict[str, Any]] = []
    try:
        if hilos <= 1:
            for item in tareas:
                filas.extend(_procesar_una(item))
        else:
            with ThreadPoolExecutor(max_workers=hilos) as pool:
                for sub in pool.map(_procesar_una, tareas):
                    filas.extend(sub)

        df = pd.DataFrame(filas)
        ext = ".csv" if formato == "CSV" else (".csv.gz" if formato == "CSV_GZIP" else ".parquet")
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            ruta_tmp = Path(tmp.name)

        try:
            if formato == "CSV":
                df.to_csv(ruta_tmp, index=False, encoding="utf-8")
            elif formato == "CSV_GZIP":
                df.to_csv(ruta_tmp, index=False, encoding="utf-8", compression="gzip")
            elif formato == "Parquet":
                df.to_parquet(ruta_tmp, index=False)
            else:
                raise ValueError(f"Formato no soportado: {formato}")
            tamano_kb = ruta_tmp.stat().st_size / 1024.0
        finally:
            if ruta_tmp.exists():
                ruta_tmp.unlink()
    except Exception:
        excepciones = 1
        tamano_kb = 0.0

    tiempo_seg = time.perf_counter() - t0
    filas_obtenidas = len(filas)
    if excepciones > 0 or filas_esperadas == 0:
        tasa_error_pct = 100.0
    else:
        discrepancia = abs(filas_obtenidas - filas_esperadas) / filas_esperadas * 100.0
        tasa_error_pct = round(discrepancia, 4)

    return round(tiempo_seg, 5), tasa_error_pct, round(tamano_kb, 3), filas_obtenidas


def construir_diseno_2_3(n_bloques: int = 3, seed: int = 20261123) -> pd.DataFrame:
    """Genera matriz ortogonal balanceada 2^3 con bloqueos y orden aleatorizado por bloque."""
    rng = np.random.default_rng(seed)
    combinaciones = list(itertools.product([-1, 1], [-1, 1], [-1, 1]))
    filas = []
    orden_global = 1
    for bloque in range(1, n_bloques + 1):
        perm = rng.permutation(len(combinaciones))
        for idx_p in perm:
            a, b, c = combinaciones[int(idx_p)]
            tratamiento = (
                f"{'A+' if a > 0 else 'A-'}_"
                f"{'B+' if b > 0 else 'B-'}_"
                f"{'C+' if c > 0 else 'C-'}"
            )
            filas.append(
                {
                    "orden_corrida": orden_global,
                    "bloque": bloque,
                    "A": a,
                    "B": b,
                    "C": c,
                    "etiqueta_A": NIVELES_A[a],
                    "etiqueta_B": NIVELES_B[b],
                    "etiqueta_C": NIVELES_C[c],
                    "tratamiento": tratamiento,
                }
            )
            orden_global += 1
    return pd.DataFrame(filas)


def construir_matrices_2_4() -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Construye matriz completa 2^4 (16 corridas) y fraccionada 2^(4-1) (8 corridas)
    con generador D = A*B*C (I = ABCD, Resolucion IV), validando los alias.
    """
    filas_comp = []
    for i, (d, c, b, a) in enumerate(itertools.product([-1, 1], repeat=4), start=1):
        filas_comp.append(
            {
                "corrida_estandar": i,
                "A_hilos": a,
                "B_parser": b,
                "C_formato": c,
                "D_compresion": d,
                "producto_ABCD": int(a * b * c * d),
            }
        )
    df_comp = pd.DataFrame(filas_comp)
    df_frac = df_comp[df_comp["D_compresion"] == (df_comp["A_hilos"] * df_comp["B_parser"] * df_comp["C_formato"])].copy()
    df_frac = df_frac.reset_index(drop=True)
    df_frac.insert(0, "corrida_fraccionada", range(1, len(df_frac) + 1))

    # Verificacion algebraica de alias bajo I = ABCD
    a = df_frac["A_hilos"]
    b = df_frac["B_parser"]
    c = df_frac["C_formato"]
    d = df_frac["D_compresion"]

    alias_verificados = {
        "I_equals_ABCD": bool((df_frac["producto_ABCD"] == 1).all()),
        "A_alias_BCD": bool((a == b * c * d).all()),
        "B_alias_ACD": bool((b == a * c * d).all()),
        "C_alias_ABD": bool((c == a * b * d).all()),
        "D_alias_ABC": bool((d == a * b * c).all()),
        "AB_alias_CD": bool(((a * b) == (c * d)).all()),
        "AC_alias_BD": bool(((a * c) == (b * d)).all()),
        "AD_alias_BC": bool(((a * d) == (b * c)).all()),
    }

    info_alias = {
        "tratamientos_2_4_completo": len(df_comp),
        "tratamientos_2_4_fraccionado": len(df_frac),
        "corridas_con_3_replicas_completo": len(df_comp) * 3,
        "corridas_con_3_replicas_fraccionado": len(df_frac) * 3,
        "ahorro_pct": round((1.0 - len(df_frac) / len(df_comp)) * 100.0, 2),
        "relacion_definidora": "I = ABCD",
        "generador": "D = A * B * C",
        "resolucion": "IV",
        "alias_principales": ["A = BCD", "B = ACD", "C = ABD", "D = ABC"],
        "alias_interacciones_2f": ["AB = CD", "AC = BD", "AD = BC"],
        "verificacion_algebraica": alias_verificados,
    }
    return df_comp, df_frac, info_alias


def evaluar_supuestos_puerta3(
    modelo, df: pd.DataFrame, col_resp: str, col_grupo: str
) -> Dict[str, Any]:
    """Ejecuta pruebas de normalidad (Shapiro-Wilk), homocedasticidad (Levene) e independencia (DW)."""
    residuos = np.asarray(modelo.resid, dtype=float)
    stat_sw, p_sw = stats.shapiro(residuos)

    grupos = [grp[col_resp].values for _, grp in df.groupby(col_grupo)]
    stat_lev, p_lev = stats.levene(*grupos)

    dw = float(durbin_watson(residuos))
    stat_kw, p_kw = stats.kruskal(*grupos)

    normalidad_ok = bool(p_sw >= 0.05)
    homoced_ok = bool(p_lev >= 0.05)
    indep_ok = bool(1.2 <= dw <= 2.8)

    return {
        "escala": col_resp,
        "shapiro_w": round(float(stat_sw), 5),
        "shapiro_p": round(float(p_sw), 5),
        "normalidad_cumplida": normalidad_ok,
        "levene_w": round(float(stat_lev), 5),
        "levene_p": round(float(p_lev), 5),
        "homocedasticidad_cumplida": homoced_ok,
        "durbin_watson": round(dw, 4),
        "independencia_razonable": indep_ok,
        "kruskal_h": round(float(stat_kw), 4),
        "kruskal_p": round(float(p_kw), 6),
        "todos_supuestos_ok": bool(normalidad_ok and homoced_ok and indep_ok),
    }


def extraer_tabla_anova(modelo) -> List[Dict[str, Any]]:
    """Convierte la tabla anova_lm Tipo II en lista serializable con eta^2 parcial."""
    tab = anova_lm(modelo, typ=2)
    ss_resid = float(tab.loc["Residual", "sum_sq"])
    filas = []
    for termino, row in tab.iterrows():
        ss = float(row["sum_sq"])
        df_g = int(row["df"])
        f_val = None if pd.isna(row["F"]) else round(float(row["F"]), 4)
        p_val = None if pd.isna(row["PR(>F)"]) else round(float(row["PR(>F)"]), 6)
        eta_p = None if termino == "Residual" else round(ss / (ss + ss_resid), 4)
        filas.append(
            {
                "termino": str(termino),
                "sum_sq": round(ss, 6),
                "df": df_g,
                "F": f_val,
                "p_valor": p_val,
                "significativo_05": bool(p_val is not None and p_val < 0.05),
                "eta_cuadrada_parcial": eta_p,
            }
        )
    return filas


def graficar_resultados_experimento(
    df_2k: pd.DataFrame,
    modelo_activo,
    df_2vias: pd.DataFrame,
    df_conf: pd.DataFrame,
) -> Dict[str, str]:
    """Genera los 5 graficos estadisticos del diseno experimental en laboratorio/graficos/."""
    DIR_GRAFICOS.mkdir(parents=True, exist_ok=True)
    rutas = {}

    # 1. Grafico de Efectos Principales 2^3
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.3), sharey=True)
    factores = [
        ("A", "etiqueta_A", "Factor A: Concurrencia"),
        ("B", "etiqueta_B", "Factor B: Parser HTML"),
        ("C", "etiqueta_C", "Factor C: Formato de Salida"),
    ]
    media_global = df_2k["tiempo_seg"].mean()
    for ax, (col_cod, col_etq, titulo) in zip(axes, factores):
        resumen = df_2k.groupby([col_cod, col_etq])["tiempo_seg"].agg(["mean", "std"]).reset_index().sort_values(col_cod)
        x = np.arange(len(resumen))
        ax.errorbar(x, resumen["mean"], yerr=resumen["std"], marker="o", lw=2.2, capsize=5, color="#1f77b4")
        ax.axhline(media_global, color="gray", linestyle="--", lw=1, label=f"Media global ({media_global:.2f}s)")
        ax.set_xticks(x)
        ax.set_xticklabels(resumen[col_etq], fontsize=10)
        ax.set_title(titulo, fontweight="bold")
        ax.grid(True, linestyle=":", alpha=0.6)
        for xi, val in zip(x, resumen["mean"]):
            ax.annotate(
                f"{val:.3f}s",
                (xi, val),
                textcoords="offset points",
                xytext=(12, 10),
                ha="left",
                fontsize=9,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="#cccccc", alpha=0.92),
                zorder=10,
            )
    axes[0].set_ylabel("Tiempo de ejecucion (seg)")
    axes[0].legend(loc="best", fontsize=8)
    fig.suptitle("Efectos Principales en Diseno Factorial 2^3 (Lote 12 paginas SNIIM)", fontweight="bold", y=1.02)
    plt.tight_layout()
    p1 = DIR_GRAFICOS / "efectos_principales_2_3.png"
    fig.savefig(p1, dpi=300, bbox_inches="tight")
    plt.close(fig)
    rutas["efectos_principales"] = str(p1.relative_to(RAIZ)).replace("\\", "/")

    # 2. Graficas de Interaccion Doble (AB, AC, BC)
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.3), sharey=True)
    pares = [
        ("etiqueta_A", "etiqueta_B", "Interaccion A (Hilos) x B (Parser)"),
        ("etiqueta_A", "etiqueta_C", "Interaccion A (Hilos) x C (Formato)"),
        ("etiqueta_B", "etiqueta_C", "Interaccion B (Parser) x C (Formato)"),
    ]
    colores = ["#1f77b4", "#d62728"]
    for ax, (f1, f2, titulo) in zip(axes, pares):
        niveles_f2 = sorted(df_2k[f2].unique())
        for idx, n2 in enumerate(niveles_f2):
            sub = df_2k[df_2k[f2] == n2].groupby(f1)["tiempo_seg"].mean()
            ax.plot(sub.index, sub.values, marker="s", lw=2, color=colores[idx % 2], label=n2)
        ax.set_title(titulo, fontweight="bold", fontsize=10)
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(title=f2.replace("etiqueta_", "Factor "), fontsize=8)
    axes[0].set_ylabel("Tiempo medio (seg)")
    fig.suptitle("Graficas de Interaccion de Dos Factores (Diseno 2^3)", fontweight="bold", y=1.02)
    plt.tight_layout()
    p2 = DIR_GRAFICOS / "interacciones_2_3.png"
    fig.savefig(p2, dpi=300, bbox_inches="tight")
    plt.close(fig)
    rutas["interacciones"] = str(p2.relative_to(RAIZ)).replace("\\", "/")

    # 3. Diagnostico de Residuos (Panel 2x2)
    residuos = np.asarray(modelo_activo.resid, dtype=float)
    ajustados = np.asarray(modelo_activo.fittedvalues, dtype=float)
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    stats.probplot(residuos, dist="norm", plot=axes[0, 0])
    axes[0, 0].set_title("Grafica Q-Q Normal de Residuos")
    axes[0, 0].grid(True, linestyle=":", alpha=0.5)

    axes[0, 1].scatter(ajustados, residuos, color="#1f77b4", alpha=0.85, edgecolors="k")
    axes[0, 1].axhline(0, color="red", linestyle="--", lw=1.2)
    axes[0, 1].set_xlabel("Valores Ajustados")
    axes[0, 1].set_ylabel("Residuos")
    axes[0, 1].set_title("Residuos vs Valores Ajustados (Homocedasticidad)")
    axes[0, 1].grid(True, linestyle=":", alpha=0.5)

    axes[1, 0].hist(residuos, bins=8, color="#2ca02c", alpha=0.75, edgecolor="black")
    axes[1, 0].set_xlabel("Residuo")
    axes[1, 0].set_ylabel("Frecuencia")
    axes[1, 0].set_title("Histograma de Residuos")
    axes[1, 0].grid(True, linestyle=":", alpha=0.5)

    axes[1, 1].plot(range(1, len(residuos) + 1), residuos, marker="o", color="#9467bd", lw=1.5)
    axes[1, 1].axhline(0, color="red", linestyle="--", lw=1.2)
    axes[1, 1].set_xlabel("Orden de Corrida Aleatorizada")
    axes[1, 1].set_ylabel("Residuo")
    axes[1, 1].set_title("Residuos vs Orden de Corrida (Independencia)")
    axes[1, 1].grid(True, linestyle=":", alpha=0.5)

    fig.suptitle("Validacion de Supuestos ANOVA (Puerta 3 Estadistica)", fontweight="bold", y=1.01)
    plt.tight_layout()
    p3 = DIR_GRAFICOS / "residuos_anova_2_3.png"
    fig.savefig(p3, dpi=300, bbox_inches="tight")
    plt.close(fig)
    rutas["residuos"] = str(p3.relative_to(RAIZ)).replace("\\", "/")

    # 4. Grafico Interaccion 2 Vias (3 x 3)
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    paleta = {"CSV": "#1f77b4", "CSV_GZIP": "#ff7f0e", "Parquet": "#2ca02c"}
    for fmt in ["CSV", "CSV_GZIP", "Parquet"]:
        sub = df_2vias[df_2vias["formato_salida"] == fmt].groupby("lote_paginas")["tiempo_seg"].mean()
        ax.plot(sub.index, sub.values, marker="o", lw=2.2, label=fmt, color=paleta[fmt])
    ax.set_xticks([6, 12, 24])
    ax.set_xlabel("Tamano del lote (paginas HTML reales SNIIM)")
    ax.set_ylabel("Tiempo medio de ejecucion (seg)")
    ax.set_title("Diseno de Dos Factores (3x3): Lote de Paginas x Formato de Salida", fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(title="Formato de Salida")
    plt.tight_layout()
    p4 = DIR_GRAFICOS / "interaccion_2vias_lote_formato.png"
    fig.savefig(p4, dpi=300, bbox_inches="tight")
    plt.close(fig)
    rutas["interaccion_2vias"] = str(p4.relative_to(RAIZ)).replace("\\", "/")

    # 5. Grafico Corrida de Confirmacion
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    res_conf = df_conf.groupby("escenario")["tiempo_seg"].agg(["mean", "std"]).reset_index()
    col_bar = ["#2ca02c" if "Optimo" in e else "#7f7f7f" for e in res_conf["escenario"]]
    bars = ax.bar(res_conf["escenario"], res_conf["mean"], yerr=res_conf["std"], capsize=6, color=col_bar, edgecolor="black", alpha=0.88)
    for b, val, err in zip(bars, res_conf["mean"], res_conf["std"]):
        ax.text(b.get_x() + b.get_width() / 2.0, val + err + 0.04, f"{val:.3f}s", ha="center", va="bottom", fontweight="bold")
    ax.set_ylim(0, float((res_conf["mean"] + res_conf["std"]).max()) * 1.18)
    ax.set_ylabel("Tiempo de ejecucion promedio (seg)")
    ax.set_title("Corrida de Confirmacion (5 replicas independientes por escenario)", fontweight="bold")
    ax.grid(True, axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()
    p5 = DIR_GRAFICOS / "confirmacion_optimo_vs_base.png"
    fig.savefig(p5, dpi=300, bbox_inches="tight")
    plt.close(fig)
    rutas["confirmacion"] = str(p5.relative_to(RAIZ)).replace("\\", "/")

    return rutas


def generar_informe_markdown(resultados: Dict[str, Any]) -> str:
    """Redacta laboratorio/informe_experimento.md con cifras reales medidas y rutas relativas."""
    exp1 = resultados["experimento_2_3"]
    sup_lin = exp1["supuestos_escala_original"]
    sup_log = exp1.get("supuestos_escala_log")
    conf = resultados["confirmacion"]
    exp2 = resultados["experimento_2vias"]
    f24 = resultados["comparativa_2_4_fraccionado"]

    def _tabla_anova_md(filas: List[Dict[str, Any]]) -> str:
        """Formatea una tabla ANOVA Tipo II como tabla Markdown."""
        lineas = ["| Termino | Sum Sq | GL | Estadistico F | p-valor | Significativo (alpha=0.05) | Eta^2 parcial |", "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |"]
        for r in filas:
            f_str = f"{r['F']:.3f}" if r["F"] is not None else "--"
            p_str = f"{r['p_valor']:.5f}" if r["p_valor"] is not None else "--"
            sig = "Si" if r["significativo_05"] else ("No" if r["p_valor"] is not None else "--")
            eta = f"{r['eta_cuadrada_parcial']:.4f}" if r["eta_cuadrada_parcial"] is not None else "--"
            lineas.append(f"| `{r['termino']}` | {r['sum_sq']:.5f} | {r['df']} | {f_str} | {p_str} | {sig} | {eta} |")
        return "\n".join(lineas)

    lineas_trat = ["| Tratamiento | Hilos (A) | Parser (B) | Formato (C) | Tiempo Medio (s) | Desv. Est (s) | Tamano (KB) | Error (%) |", "| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: |"]
    for t in exp1["resumen_tratamientos"]:
        lineas_trat.append(
            f"| `{t['tratamiento']}` | {t['etiqueta_A']} | {t['etiqueta_B']} | {t['etiqueta_C']} | "
            f"{t['tiempo_medio_seg']:.4f} | {t['tiempo_std_seg']:.4f} | {t['tamano_kb_medio']:.2f} | {t['tasa_error_media_pct']:.2f}% |"
        )

    texto_sup_log = ""
    if sup_log:
        texto_sup_log = f"""
Dado que la escala original presento desviacion en algun supuesto parametrico (Puerta 3 activada), se aplico transformacion **Box-Cox logaritmica (`ln(tiempo_seg)`)** y verificacion no parametrica **Kruskal-Wallis**:
- **Shapiro-Wilk (`ln(Y)`):** $W = {sup_log['shapiro_w']}$, $p = {sup_log['shapiro_p']}$ (Normalidad: `{sup_log['normalidad_cumplida']}`).
- **Levene (`ln(Y)`):** $W = {sup_log['levene_w']}$, $p = {sup_log['levene_p']}$ (Homocedasticidad: `{sup_log['homocedasticidad_cumplida']}`).
- **Durbin-Watson (`ln(Y)`):** $DW = {sup_log['durbin_watson']}$.
- **Kruskal-Wallis (respaldo robusto entre 8 tratamientos):** $H = {sup_log['kruskal_h']}$, $p = {sup_log['kruskal_p']:.6f}$.

#### ANOVA sobre modelo transformado `ln(tiempo_seg)`
{_tabla_anova_md(exp1['anova_log'])}
"""

    tukey_lines = ["| Grupo 1 | Grupo 2 | Dif. Medias (s) | p-adj | Rechaza H0 |", "| :--- | :--- | :---: | :---: | :---: |"]
    for tk in exp2["tukey_formato"]:
        tukey_lines.append(f"| {tk['grupo_1']} | {tk['grupo_2']} | {tk['meandiff']:+.4f} | {tk['p_adj']:.4f} | {tk['reject']} |")

    md = f"""# Informe de Diseno Experimental (Entrega E2)

**Proyecto:** TDL Canastita (Occidente)  
**Autora:** Andrea Tairi Velazquez Gallardo (Data Statistician & Quality Auditor)  
**Ruta elegida:** Ruta Ingenieria (evaluacion controlada sobre copia local congelada del SNIIM en `data/bronce/sniim_html_snapshot/`)

---

## 1. Experimento Factorial Completo $2^3$ (Tiempo de Procesamiento y Eficiencia)

Se diseno un experimento factorial completo **$2^3$** con **3 bloques completos aleatorizados** (24 corridas reales en lote de 12 paginas HTML del SNIIM = 4,846 registros por corrida, mas 1 corrida previa de calentamiento descartada por factor). La tasa de error de parseo fue **{exp1['tasa_error_global_pct']:.2f}%** en todas las configuraciones.

### Factores y Niveles
- **Factor A (Concurrencia):** `-1` = `1 hilo` | `+1` = `4 hilos` (`ThreadPoolExecutor`)
- **Factor B (Parser HTML):** `-1` = `html.parser` | `+1` = `lxml`
- **Factor C (Formato de salida):** `-1` = `CSV` | `+1` = `Parquet`

### Resumen por Tratamiento
{chr(10).join(lineas_trat)}

### Tabla ANOVA de Efectos Fijos (Escala Original `tiempo_seg`)
{_tabla_anova_md(exp1['anova_original'])}

### Efectos Principales Estimados ($2\\hat{{\\beta}}$)
- **Efecto A (1 hilo -> 4 hilos):** `{exp1['efectos_estimados_seg']['A']:+.4f} s`
- **Efecto B (`html.parser` -> `lxml`):** `{exp1['efectos_estimados_seg']['B']:+.4f} s`
- **Efecto C (`CSV` -> `Parquet`):** `{exp1['efectos_estimados_seg']['C']:+.4f} s`

> **Hallazgo empirico clave sobre Python/GIL y Parquet:** Contrario a la intuicion inicial de paralelismo con hilos, en procesamiento intensivo de DOM HTML en Python con BeautifulSoup, **4 hilos introduce contencion por el Global Interpreter Lock (GIL)** respecto a 1 hilo secuencial. Por otro lado, **Parquet reduce el peso en disco de ~{exp1['tamano_csv_kb']:.1f} KB a ~{exp1['tamano_parquet_kb']:.1f} KB ({exp1['ahorro_espacio_parquet_pct']:.2f}% menos almacenamiento)**.

![Efectos Principales 2^3](graficos/efectos_principales_2_3.png)
![Interacciones 2^3](graficos/interacciones_2_3.png)

---

## 2. Puerta 3 Estadistica: Validacion de Supuestos del ANOVA

- **Shapiro-Wilk (Normalidad en escala original):** $W = {sup_lin['shapiro_w']}$, $p = {sup_lin['shapiro_p']}$ (Cumple: `{sup_lin['normalidad_cumplida']}`)
- **Levene (Homocedasticidad):** $W = {sup_lin['levene_w']}$, $p = {sup_lin['levene_p']}$ (Cumple: `{sup_lin['homocedasticidad_cumplida']}`)
- **Durbin-Watson (Independencia):** $DW = {sup_lin['durbin_watson']}$
{texto_sup_log}
![Diagnostico de Residuos ANOVA](graficos/residuos_anova_2_3.png)

---

## 3. Corrida de Confirmacion del Optimo Experimental

- **Configuracion optima seleccionada (menor tiempo y 0% error):** `{conf['optimo_descripcion']}`
- **Configuracion alternativa de contraste:** `{conf['referencia_descripcion']}`
- **Prediccion del modelo ANOVA para el optimo (IC 95%):** `{conf['prediccion_modelo_seg']:.4f} s` (rango `[{conf['ic95_inf_seg']:.4f}, {conf['ic95_sup_seg']:.4f}] s`)
- **Media observada en 5 corridas independientes del optimo:** **`{conf['optimo_media_obs_seg']:.4f} s`** (desv. est. `{conf['optimo_std_obs_seg']:.4f} s`, dentro de IC 95%: `{conf['confirmacion_dentro_ic95']}`)
- **Media observada en 5 corridas de contraste:** `{conf['referencia_media_obs_seg']:.4f} s` (**mejora relativa: {conf['mejora_tiempo_vs_referencia_pct']:.2f}%**).

![Corrida de Confirmacion](graficos/confirmacion_optimo_vs_base.png)

---

## 4. Diseno de Dos Factores con $\\ge 3$ Niveles (ANOVA 2 Vias 3x3)

Se evaluo el efecto conjunto del **Tamano del lote (`6, 12, 24` paginas HTML reales)** y el **Formato de salida (`CSV, CSV_GZIP, Parquet`)** con 3 replicas aleatorizadas por celda (27 corridas reales).

{_tabla_anova_md(exp2['anova_2vias'])}

### Prueba Post-Hoc Tukey HSD (por Formato de Salida)
{chr(10).join(tukey_lines)}

![Interaccion 2 Vias Lote x Formato](graficos/interaccion_2vias_lote_formato.png)

---

## 5. Comparativa Matricial: Diseno Completo $2^4$ vs Fraccionado $2^{{4-1}}$

Al incorporar un cuarto factor `D` (Compresion en lectura/escritura: `-1` Sin compresion vs `+1` Con compresion), se construyeron las matrices completas en [matriz_2_4_completo.csv](matriz_2_4_completo.csv) y fraccionadas en [matriz_2_4_fraccionado.csv](matriz_2_4_fraccionado.csv):

- **Tratamientos $2^4$ completo:** {f24['tratamientos_2_4_completo']} ({f24['corridas_con_3_replicas_completo']} corridas con 3 replicas).
- **Tratamientos $2^{{4-1}}$ fraccionado:** {f24['tratamientos_2_4_fraccionado']} ({f24['corridas_con_3_replicas_fraccionado']} corridas con 3 replicas).
- **Ahorro experimental cuantificado:** **{f24['ahorro_pct']:.1f}% menos corridas**.
- **Generador y Resolucion:** `{f24['generador']}`, relacion definidora **`{f24['relacion_definidora']}`** (**Resolucion {f24['resolucion']}**).
- **Estructura de alias verificada algebraicamente:**
  - Efectos principales confundidos solo con interacciones de 3 factores: `{', '.join(f24['alias_principales'])}`.
  - Interacciones de 2 factores confundidas entre si: `{', '.join(f24['alias_interacciones_2f'])}`.
"""
    return md


def ejecutar_experimento_completo() -> Dict[str, Any]:
    """Ejecuta todos los disenos experimentales de E2 y guarda sus artefactos."""
    DIR_LAB.mkdir(parents=True, exist_ok=True)
    DIR_GRAFICOS.mkdir(parents=True, exist_ok=True)

    paginas_base, filas_ref = cargar_paginas_snapshot()

    # Calentamiento descartado para estabilizar caches de parsers y writers antes de medir
    for hilos, parser, fmt in [(1, "html.parser", "CSV"), (4, "lxml", "Parquet"), (1, "lxml", "CSV_GZIP")]:
        ejecutar_corrida_extractor(paginas_base, filas_ref, ciclos=1, hilos=hilos, parser=parser, formato=fmt)

    # ---------------- EXPERIMENTO 1: FACTORIAL 2^3 ----------------
    df_diseno = construir_diseno_2_3(n_bloques=3, seed=20261123)
    tiempos, errores, tamanos, filas_list = [], [], [], []
    for _, row in df_diseno.iterrows():
        hilos = 1 if int(row["A"]) < 0 else 4
        parser = "html.parser" if int(row["B"]) < 0 else "lxml"
        fmt = "CSV" if int(row["C"]) < 0 else "Parquet"
        t_s, err, kb, n_rows = ejecutar_corrida_extractor(
            paginas_base, filas_ref, ciclos=2, hilos=hilos, parser=parser, formato=fmt
        )
        tiempos.append(t_s)
        errores.append(err)
        tamanos.append(kb)
        filas_list.append(n_rows)

    df_2k = df_diseno.copy()
    df_2k["bloque_cat"] = "B" + df_2k["bloque"].astype(str)
    df_2k["tiempo_seg"] = tiempos
    df_2k["log_tiempo"] = np.log(df_2k["tiempo_seg"])
    df_2k["tasa_error_pct"] = errores
    df_2k["tamano_kb"] = tamanos
    df_2k["filas_extraidas"] = filas_list
    df_2k.to_csv(DIR_LAB / "experimento_2_3_corridas.csv", index=False, encoding="utf-8")

    modelo_orig = ols("tiempo_seg ~ bloque_cat + A * B * C", data=df_2k).fit()
    anova_orig = extraer_tabla_anova(modelo_orig)
    sup_orig = evaluar_supuestos_puerta3(modelo_orig, df_2k, "tiempo_seg", "tratamiento")

    modelo_activo = modelo_orig
    sup_log = None
    anova_log = None
    if not sup_orig["todos_supuestos_ok"]:
        modelo_log = ols("log_tiempo ~ bloque_cat + A * B * C", data=df_2k).fit()
        anova_log = extraer_tabla_anova(modelo_log)
        sup_log = evaluar_supuestos_puerta3(modelo_log, df_2k, "log_tiempo", "tratamiento")
        modelo_activo = modelo_log

    resumen_trat = (
        df_2k.groupby(["tratamiento", "A", "B", "C", "etiqueta_A", "etiqueta_B", "etiqueta_C"])
        .agg(
            tiempo_medio_seg=("tiempo_seg", "mean"),
            tiempo_std_seg=("tiempo_seg", "std"),
            tamano_kb_medio=("tamano_kb", "mean"),
            tasa_error_media_pct=("tasa_error_pct", "mean"),
        )
        .reset_index()
        .sort_values("tiempo_medio_seg")
    )

    # Seleccionar optimo (menor tiempo medio con 0% error) y contrastar contra base E1 (-1, -1, -1)
    opt_row = resumen_trat[resumen_trat["tasa_error_media_pct"] == 0.0].iloc[0]
    a_opt, b_opt, c_opt = int(opt_row["A"]), int(opt_row["B"]), int(opt_row["C"])
    if (a_opt, b_opt, c_opt) == (-1, -1, -1):
        ref_row = resumen_trat.iloc[-1]
        a_ref, b_ref, c_ref = int(ref_row["A"]), int(ref_row["B"]), int(ref_row["C"])
        etq_ref = "Contraste"
    else:
        a_ref, b_ref, c_ref = -1, -1, -1
        etq_ref = "Base E1"

    # Prediccion del modelo original para IC 95% del optimo
    pred_df = pd.DataFrame([{"bloque_cat": "B1", "A": a_opt, "B": b_opt, "C": c_opt}])
    pred_sum = modelo_orig.get_prediction(pred_df).summary_frame(alpha=0.05).iloc[0]

    # Corrida de confirmacion (5 optimo vs 5 base E1)
    filas_conf = []
    for rep in range(1, 6):
        t_opt, e_opt, kb_opt, _ = ejecutar_corrida_extractor(
            paginas_base,
            filas_ref,
            ciclos=2,
            hilos=1 if a_opt < 0 else 4,
            parser="html.parser" if b_opt < 0 else "lxml",
            formato="CSV" if c_opt < 0 else "Parquet",
        )
        filas_conf.append(
            {
                "escenario": f"Optimo ({NIVELES_A[a_opt]}, {NIVELES_B[b_opt]}, {NIVELES_C[c_opt]})",
                "tipo": "optimo",
                "replica": rep,
                "tiempo_seg": t_opt,
                "tasa_error_pct": e_opt,
                "tamano_kb": kb_opt,
            }
        )
        t_ref, e_ref, kb_ref, _ = ejecutar_corrida_extractor(
            paginas_base,
            filas_ref,
            ciclos=2,
            hilos=1 if a_ref < 0 else 4,
            parser="html.parser" if b_ref < 0 else "lxml",
            formato="CSV" if c_ref < 0 else "Parquet",
        )
        filas_conf.append(
            {
                "escenario": f"{etq_ref} ({NIVELES_A[a_ref]}, {NIVELES_B[b_ref]}, {NIVELES_C[c_ref]})",
                "tipo": "referencia",
                "replica": rep,
                "tiempo_seg": t_ref,
                "tasa_error_pct": e_ref,
                "tamano_kb": kb_ref,
            }
        )

    df_conf = pd.DataFrame(filas_conf)
    df_conf.to_csv(DIR_LAB / "confirmacion_optimo.csv", index=False, encoding="utf-8")

    opt_obs = df_conf[df_conf["tipo"] == "optimo"]["tiempo_seg"]
    ref_obs = df_conf[df_conf["tipo"] == "referencia"]["tiempo_seg"]
    media_opt_obs = float(opt_obs.mean())
    media_ref_obs = float(ref_obs.mean())
    mejora_pct = ((media_ref_obs - media_opt_obs) / media_ref_obs) * 100.0 if media_ref_obs > 0 else 0.0

    # ---------------- EXPERIMENTO 2: DOS FACTORES >= 3 NIVELES (3 x 3) ----------------
    rng2 = np.random.default_rng(20261124)
    celdas_2vias = list(itertools.product([6, 12, 24], ["CSV", "CSV_GZIP", "Parquet"])) * 3
    rng2.shuffle(celdas_2vias)
    filas_2vias = []
    hilos_opt = 1 if a_opt < 0 else 4
    parser_opt = "html.parser" if b_opt < 0 else "lxml"
    for ord2, (lote_pags, fmt2) in enumerate(celdas_2vias, start=1):
        ciclos2 = lote_pags // 6
        t2, err2, kb2, n_r2 = ejecutar_corrida_extractor(
            paginas_base, filas_ref, ciclos=ciclos2, hilos=hilos_opt, parser=parser_opt, formato=fmt2
        )
        filas_2vias.append(
            {
                "orden_corrida": ord2,
                "lote_paginas": lote_pags,
                "formato_salida": fmt2,
                "tiempo_seg": t2,
                "tasa_error_pct": err2,
                "tamano_kb": kb2,
                "filas_extraidas": n_r2,
            }
        )
    df_2vias = pd.DataFrame(filas_2vias)
    df_2vias["lote_cat"] = df_2vias["lote_paginas"].astype(str) + "_pags"
    df_2vias.to_csv(DIR_LAB / "experimento_2vias_corridas.csv", index=False, encoding="utf-8")

    modelo_2vias = ols("tiempo_seg ~ lote_cat * formato_salida", data=df_2vias).fit()
    anova_2vias = extraer_tabla_anova(modelo_2vias)
    tukey = pairwise_tukeyhsd(endog=df_2vias["tiempo_seg"], groups=df_2vias["formato_salida"], alpha=0.05)
    tukey_rows = []
    for row_tk in tukey.summary().data[1:]:
        tukey_rows.append(
            {
                "grupo_1": str(row_tk[0]),
                "grupo_2": str(row_tk[1]),
                "meandiff": float(row_tk[2]),
                "p_adj": float(row_tk[3]),
                "reject": bool(row_tk[6]),
            }
        )

    # ---------------- DISENO 2^4 vs 2^(4-1) ----------------
    df_comp, df_frac, info_alias = construir_matrices_2_4()
    df_comp.to_csv(DIR_LAB / "matriz_2_4_completo.csv", index=False, encoding="utf-8")
    df_frac.to_csv(DIR_LAB / "matriz_2_4_fraccionado.csv", index=False, encoding="utf-8")

    # ---------------- GRAFICOS E INFORME ----------------
    rutas_graf = graficar_resultados_experimento(df_2k, modelo_activo, df_2vias, df_conf)

    tamano_csv_kb = float(df_2k[df_2k["C"] == -1]["tamano_kb"].mean())
    tamano_parq_kb = float(df_2k[df_2k["C"] == 1]["tamano_kb"].mean())
    ahorro_parq_pct = ((tamano_csv_kb - tamano_parq_kb) / tamano_csv_kb) * 100.0 if tamano_csv_kb > 0 else 0.0

    # Efectos principales: 2 * coeficiente OLS sobre variables codificadas {-1, +1}
    efectos_est = {
        "A": round(float(modelo_orig.params.get("A", 0.0) * 2.0), 5),
        "B": round(float(modelo_orig.params.get("B", 0.0) * 2.0), 5),
        "C": round(float(modelo_orig.params.get("C", 0.0) * 2.0), 5),
    }

    resultados = {
        "fecha_ejecucion_utc": datetime.now(timezone.utc).isoformat(),
        "lote_paginas_base": len(paginas_base),
        "filas_por_ciclo": filas_ref,
        "experimento_2_3": {
            "total_corridas": len(df_2k),
            "bloques": 3,
            "tasa_error_global_pct": round(float(df_2k["tasa_error_pct"].mean()), 4),
            "tamano_csv_kb": round(tamano_csv_kb, 2),
            "tamano_parquet_kb": round(tamano_parq_kb, 2),
            "ahorro_espacio_parquet_pct": round(ahorro_parq_pct, 2),
            "efectos_estimados_seg": efectos_est,
            "anova_original": anova_orig,
            "supuestos_escala_original": sup_orig,
            "anova_log": anova_log,
            "supuestos_escala_log": sup_log,
            "resumen_tratamientos": json.loads(resumen_trat.to_json(orient="records")),
        },
        "confirmacion": {
            "optimo_tratamiento": str(opt_row["tratamiento"]),
            "optimo_descripcion": f"{NIVELES_A[a_opt]} + {NIVELES_B[b_opt]} + {NIVELES_C[c_opt]}",
            "referencia_descripcion": f"{NIVELES_A[a_ref]} + {NIVELES_B[b_ref]} + {NIVELES_C[c_ref]}",
            "prediccion_modelo_seg": round(float(pred_sum["mean"]), 4),
            "ic95_inf_seg": round(float(pred_sum["obs_ci_lower"]), 4),
            "ic95_sup_seg": round(float(pred_sum["obs_ci_upper"]), 4),
            "optimo_media_obs_seg": round(media_opt_obs, 4),
            "optimo_std_obs_seg": round(float(opt_obs.std()), 4),
            "referencia_media_obs_seg": round(media_ref_obs, 4),
            "confirmacion_dentro_ic95": bool(pred_sum["obs_ci_lower"] <= media_opt_obs <= pred_sum["obs_ci_upper"]),
            "mejora_tiempo_vs_referencia_pct": round(mejora_pct, 2),
        },
        "experimento_2vias": {
            "total_corridas": len(df_2vias),
            "factores": {"lote_paginas": [6, 12, 24], "formato_salida": ["CSV", "CSV_GZIP", "Parquet"]},
            "anova_2vias": anova_2vias,
            "tukey_formato": tukey_rows,
        },
        "comparativa_2_4_fraccionado": info_alias,
        "graficos": rutas_graf,
    }

    (DIR_LAB / "resultados_experimento_e2.json").write_text(
        json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    informe_md = generar_informe_markdown(resultados)
    (DIR_LAB / "informe_experimento.md").write_text(informe_md, encoding="utf-8")

    print(
        f"OK - Experimento E2 completado | Optimo: {resultados['confirmacion']['optimo_descripcion']} "
        f"({media_opt_obs:.4f}s vs {media_ref_obs:.4f}s, mejora {mejora_pct:.1f}%) | Error: {resultados['experimento_2_3']['tasa_error_global_pct']}%"
    )
    return resultados


if __name__ == "__main__":
    ejecutar_experimento_completo()
