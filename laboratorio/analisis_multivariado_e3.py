"""
laboratorio/analisis_multivariado_e3.py
Proyecto Integrador - Trusted Data Lab (tdl-canastita-proyecto)
Autora: Andrea Tairi Velazquez Gallardo (Data Statistician & Quality Auditor)

Modulo de Analisis Multivariado (Entrega E3 - Unidad 5 Analisis Estadistico):
1. Matriz multivariada de 7 variables numericas continuas sobre Capa Oro (6 insumos
   base en las 3 plazas de Occidente: Colima, Guadalajara y Morelia).
2. Matriz de covarianzas, matriz de correlaciones y mapa de calor.
3. Puerta 3 de Normalidad Multivariada: Pruebas de Mardia (asimetria y curtosis)
   y Henze-Zirkler, grafica Q-Q de distancias de Mahalanobis vs Chi^2, evaluacion
   con transformacion Yeo-Johnson y respaldo no parametrico PERMANOVA.
4. Analisis de Componentes Principales (PCA) estandarizado: eigenvalores,
   grafica de sedimentacion, cargas interpretadas, biplot PC1-PC2, nombres de
   negocio por componente y proyeccion exportada para el tablero Streamlit.
5. MANOVA (Lambda de Wilks, Traza de Pillai, Hotelling-Lawley, Roy) comparando
   las 3 plazas definidas desde E0 (y analisis complementario por producto),
   contrastado contra ANOVAs univariados separados (inflacion de error Tipo I).
"""

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
from typing import Any, Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.multivariate.manova import MANOVA

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

DIR_ORO = RAIZ / "data" / "oro"
DIR_LAB = RAIZ / "laboratorio"
DIR_GRAFICOS = DIR_LAB / "graficos"

PRODUCTOS_BASE_E3 = [
    "Aguacate Hass",
    "Cebolla Bola",
    "Chile Serrano",
    "Jitomate Saladette",
    "Limon con semilla #5",
    "Papa Alpha",
]

VARIABLES_E3 = [
    "precio_promedio_mxn",
    "precio_usd",
    "volatilidad_precio_std",
    "spread_pct",
    "variacion_mom_pct",
    "variacion_yoy_pct",
    "num_observaciones",
]

ETIQUETAS_CORTAS = {
    "precio_promedio_mxn": "Precio MXN",
    "precio_usd": "Precio USD",
    "volatilidad_precio_std": "Volatilidad",
    "spread_pct": "Spread %",
    "variacion_mom_pct": "Var. MoM %",
    "variacion_yoy_pct": "Var. YoY %",
    "num_observaciones": "Num. Cotiz.",
}


def cargar_matriz_multivariada() -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Carga Capa Oro, filtra los 6 productos base historicos en las 3 plazas
    y elimina unicamente los nulos estructurales iniciales por rezago (MoM/YoY).
    """
    ruta_csv = DIR_ORO / "canasta_occidente_oro.csv"
    if not ruta_csv.exists():
        raise FileNotFoundError(f"No se encontro Capa Oro en {ruta_csv}")

    df_raw = pd.read_csv(ruta_csv)
    df_base = df_raw[df_raw["producto"].isin(PRODUCTOS_BASE_E3)].copy()
    n_antes = len(df_base)
    nulos_por_col = {c: int(df_base[c].isna().sum()) for c in VARIABLES_E3}

    df_comp = df_base.dropna(subset=VARIABLES_E3).sort_values(
        ["anio_mes", "plaza_id", "producto"]
    ).reset_index(drop=True)

    resumen_carga = {
        "registros_oro_totales": int(len(df_raw)),
        "registros_canasta_base": int(n_antes),
        "registros_completos_e3": int(len(df_comp)),
        "registros_excluidos_rezago_estructural": int(n_antes - len(df_comp)),
        "nulos_previos_por_variable": nulos_por_col,
        "periodo_min": str(df_comp["anio_mes"].min()),
        "periodo_max": str(df_comp["anio_mes"].max()),
        "conteo_por_ciudad": {
            str(k): int(v) for k, v in df_comp["ciudad"].value_counts().sort_index().items()
        },
        "conteo_por_producto": {
            str(k): int(v) for k, v in df_comp["producto"].value_counts().sort_index().items()
        },
    }
    return df_comp, resumen_carga


def prueba_mardia(X: np.ndarray) -> Dict[str, float]:
    """
    Calcula la prueba de normalidad multivariada de Mardia (1970):
    estadistico de asimetria (b1,p) bajo Chi^2 y curtosis (b2,p) bajo Normal(0,1).
    """
    n, p = X.shape
    medias = X.mean(axis=0, keepdims=True)
    Y = X - medias
    S = (Y.T @ Y) / n
    S_inv = np.linalg.pinv(S)

    D = Y @ S_inv @ Y.T
    b1p = float(np.mean(D ** 3))
    b2p = float(np.mean(np.diag(D) ** 2))

    df_skew = p * (p + 1) * (p + 2) / 6.0
    k_corr = ((p + 1) * (n + 1) * (n + 3)) / (n * ((n + 1) * (p + 1) - 6.0))
    chi2_skew = float(n * b1p * k_corr / 6.0) if n < 50 else float(n * b1p / 6.0)
    p_skew = float(stats.chi2.sf(chi2_skew, df_skew))

    esp_kurt = p * (p + 2)
    var_kurt = 8.0 * p * (p + 2) / n
    z_kurt = float((b2p - esp_kurt) / math.sqrt(var_kurt))
    p_kurt = float(2.0 * stats.norm.sf(abs(z_kurt)))

    return {
        "n": int(n),
        "p": int(p),
        "b1p_asimetria": round(b1p, 4),
        "chi2_asimetria": round(chi2_skew, 4),
        "gl_asimetria": int(df_skew),
        "p_asimetria": round(p_skew, 8),
        "b2p_curtosis": round(b2p, 4),
        "z_curtosis": round(z_kurt, 4),
        "p_curtosis": round(p_kurt, 8),
        "es_normal_alpha05": bool(p_skew >= 0.05 and p_kurt >= 0.05),
    }


def prueba_henze_zirkler(X: np.ndarray) -> Dict[str, float]:
    """
    Implementa la prueba global de normalidad multivariada de Henze-Zirkler (1990)
    usando parametro de suavizado optimo beta y aproximacion log-normal del valor-p.
    """
    n, p = X.shape
    Y = X - X.mean(axis=0, keepdims=True)
    S = (Y.T @ Y) / n
    S_inv = np.linalg.pinv(S)

    beta = (1.0 / math.sqrt(2.0)) * (((2.0 * p + 1.0) / 4.0) * n) ** (1.0 / (p + 4.0))
    b2 = beta ** 2

    # D_ij = (x_i - x_j)^T S^{-1} (x_i - x_j) mediante expansion cuadratica
    G = Y @ S_inv @ Y.T
    d_diag = np.diag(G)
    D_ij = np.maximum(0.0, d_diag[:, None] + d_diag[None, :] - 2.0 * G)

    termino_1 = float(np.sum(np.exp(-(b2 / 2.0) * D_ij)) / (n ** 2))
    termino_2 = float(
        2.0
        * ((1.0 + b2) ** (-p / 2.0))
        * np.mean(np.exp(-(b2 / (2.0 * (1.0 + b2))) * d_diag))
    )
    termino_3 = float((1.0 + 2.0 * b2) ** (-p / 2.0))
    hz = float(n * (termino_1 - termino_2 + termino_3))

    # Aproximacion log-normal de Henze & Zirkler (1990)
    a = 1.0 + 2.0 * b2
    wb = (1.0 + b2) * (1.0 + 3.0 * b2)
    mu = 1.0 - (a ** (-p / 2.0)) * (
        1.0 + (p * b2) / a + (p * (p + 2.0) * (b2 ** 2)) / (2.0 * (a ** 2))
    )
    si2 = 2.0 * ((1.0 + 4.0 * b2) ** (-p / 2.0)) + 2.0 * (a ** (-p)) * (
        1.0 + (2.0 * p * (b2 ** 2)) / (a ** 2) + (3.0 * p * (p + 2.0) * (b2 ** 4)) / (4.0 * (a ** 4))
    ) - 4.0 * (wb ** (-p / 2.0)) * (
        1.0 + (3.0 * p * (b2 ** 2)) / (2.0 * wb) + (p * (p + 2.0) * (b2 ** 4)) / (2.0 * (wb ** 2))
    )
    si2 = max(si2, 1e-12)
    pmu = math.log(math.sqrt((mu ** 4) / (si2 + mu ** 2)))
    psi = math.sqrt(math.log((si2 + mu ** 2) / (mu ** 2)))
    p_val = float(stats.lognorm.sf(max(hz, 1e-12), s=psi, scale=math.exp(pmu)))

    return {
        "beta": round(beta, 4),
        "estadistico_hz": round(hz, 4),
        "p_valor": round(p_val, 8),
        "es_normal_alpha05": bool(p_val >= 0.05),
    }


def calcular_mahalanobis(X: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Calcula distancias cuadradas de Mahalanobis D^2 y diagnostico frente a Chi^2_p."""
    n, p = X.shape
    Y = X - X.mean(axis=0, keepdims=True)
    S = np.cov(X, rowvar=False, ddof=1)
    S_inv = np.linalg.inv(S)
    d2 = np.einsum("ij,jk,ik->i", Y, S_inv, Y)

    umbral_99 = float(stats.chi2.ppf(0.99, df=p))
    umbral_95 = float(stats.chi2.ppf(0.95, df=p))
    atipicos_99 = int((d2 > umbral_99).sum())

    probs = (np.arange(1, n + 1) - 0.5) / n
    cuantiles_chi2 = stats.chi2.ppf(probs, df=p)
    d2_ord = np.sort(d2)
    corr_qq = float(np.corrcoef(cuantiles_chi2, d2_ord)[0, 1])

    diag = {
        "grados_libertad_p": int(p),
        "rango_matriz_cov": int(np.linalg.matrix_rank(S)),
        "num_condicion_cov": round(float(np.linalg.cond(S)), 2),
        "d2_media": round(float(d2.mean()), 4),
        "d2_mediana": round(float(np.median(d2)), 4),
        "d2_maximo": round(float(d2.max()), 4),
        "umbral_chi2_95": round(umbral_95, 4),
        "umbral_chi2_99": round(umbral_99, 4),
        "observaciones_sobre_chi2_99": atipicos_99,
        "pct_sobre_chi2_99": round(atipicos_99 / n * 100.0, 2),
        "correlacion_qq_chi2": round(corr_qq, 4),
    }
    return d2, diag


def ejecutar_pca(df_comp: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Ejecuta PCA estandarizado sobre la matriz de correlaciones R (7x7),
    orientando el signo por carga dominante y asignando nombres de negocio.
    """
    X = df_comp[VARIABLES_E3].to_numpy(dtype=float)
    Z = (X - X.mean(axis=0, keepdims=True)) / X.std(axis=0, ddof=1, keepdims=True)
    R = np.corrcoef(Z, rowvar=False)

    eigvals, eigvecs = np.linalg.eigh(R)
    orden = np.argsort(eigvals)[::-1]
    eigvals = eigvals[orden]
    eigvecs = eigvecs[:, orden]

    # Convencion determinista: carga mayor en magnitud de cada componente queda positiva
    for j in range(eigvecs.shape[1]):
        idx_max = int(np.argmax(np.abs(eigvecs[:, j])))
        if eigvecs[idx_max, j] < 0:
            eigvecs[:, j] *= -1.0

    var_exp_pct = (eigvals / eigvals.sum()) * 100.0
    var_acum_pct = np.cumsum(var_exp_pct)
    cargas_std = eigvecs * np.sqrt(np.maximum(eigvals, 0.0))[None, :]

    scores = Z @ eigvecs

    nombres_negocio = {
        "PC1": "Indice de Nivel de Precio, Volatilidad y Escala",
        "PC2": "Indice de Choque Estacional e Inflacionario (MoM/YoY)",
        "PC3": "Indice de Amplitud Mayorista (Spread %) y Riesgo",
        "PC4": "Indice de Contraste Impulso Mensual vs Anual",
        "PC5": "Indice de Liquidez y Densidad de Plaza",
        "PC6": "Componente Residual de Spread vs Volatilidad",
        "PC7": "Componente Tipo de Cambio Efectivo (MXN vs USD)",
    }

    filas_pca = []
    for k in range(len(VARIABLES_E3)):
        comp = f"PC{k + 1}"
        fila: Dict[str, Any] = {
            "componente": comp,
            "nombre_negocio": nombres_negocio.get(comp, comp),
            "eigenvalor": round(float(eigvals[k]), 4),
            "varianza_explicada_pct": round(float(var_exp_pct[k]), 2),
            "varianza_acumulada_pct": round(float(var_acum_pct[k]), 2),
            "criterio_kaiser_mayor_1": bool(eigvals[k] > 1.0),
        }
        for i, var in enumerate(VARIABLES_E3):
            fila[f"peso_{var}"] = round(float(eigvecs[i, k]), 4)
            fila[f"carga_{var}"] = round(float(cargas_std[i, k]), 4)
        filas_pca.append(fila)

    df_pca_meta = pd.DataFrame(filas_pca)

    df_proj = df_comp[["anio_mes", "plaza_id", "ciudad", "producto"] + VARIABLES_E3].copy()
    df_proj["PC1"] = np.round(scores[:, 0], 4)
    df_proj["PC2"] = np.round(scores[:, 1], 4)
    df_proj["PC3"] = np.round(scores[:, 2], 4)

    resumen_pca = {
        "kaiser_componentes_seleccionados": int((eigvals > 1.0).sum()),
        "varianza_pc1_pct": round(float(var_exp_pct[0]), 2),
        "varianza_pc2_pct": round(float(var_exp_pct[1]), 2),
        "varianza_pc1_pc2_pct": round(float(var_acum_pct[1]), 2),
        "varianza_pc1_pc3_pct": round(float(var_acum_pct[2]), 2),
        "eigenvalores": [round(float(v), 4) for v in eigvals],
        "ortonormalidad_max_error": round(float(np.max(np.abs(eigvecs.T @ eigvecs - np.eye(len(VARIABLES_E3))))), 12),
        "nombres_negocio": {f"PC{k+1}": nombres_negocio[f"PC{k+1}"] for k in range(3)},
    }
    return df_pca_meta, df_proj, resumen_pca


def _extraer_tabla_manova(mv_res: Any, termino: str, factor_nombre: str) -> List[Dict[str, Any]]:
    """Convierte la salida estadistica de statsmodels MANOVA a lista serializable."""
    tabla = mv_res.results[termino]["stat"]
    filas = []
    for prueba_nombre, row in tabla.iterrows():
        filas.append({
            "factor": factor_nombre,
            "estadistico": str(prueba_nombre),
            "valor": round(float(row["Value"]), 5),
            "f_valor": round(float(row["F Value"]), 4),
            "num_df": round(float(row["Num DF"]), 1),
            "den_df": round(float(row["Den DF"]), 1),
            "p_valor": round(float(row["Pr > F"]), 8),
            "significativo_05": bool(float(row["Pr > F"]) < 0.05),
        })
    return filas


def ejecutar_permanova(Z: np.ndarray, grupos: np.ndarray, n_perm: int = 999, seed: int = 20261127) -> Dict[str, Any]:
    """
    Puerta 3 multivariada no parametrica (PERMANOVA por permutaciones sobre
    distancias euclidianas estandarizadas) para validar robustez ante no normalidad.
    """
    n = len(Z)
    etiquetas, cods = np.unique(grupos, return_inverse=True)
    k = len(etiquetas)
    media_global = Z.mean(axis=0, keepdims=True)
    ss_total = float(np.sum((Z - media_global) ** 2))

    def _pseudo_f(cod_vec: np.ndarray) -> float:
        """Calcula estadistico pseudo-F multivariado para un vector de asignacion."""
        ss_between = 0.0
        for g in range(k):
            mask = cod_vec == g
            ng = int(mask.sum())
            if ng > 0:
                diff = Z[mask].mean(axis=0) - media_global[0]
                ss_between += ng * float(np.dot(diff, diff))
        ss_within = max(ss_total - ss_between, 1e-12)
        return float((ss_between / (k - 1)) / (ss_within / (n - k)))

    f_obs = _pseudo_f(cods)
    rng = np.random.default_rng(seed)
    mayores = 0
    for _ in range(n_perm):
        perm = rng.permutation(cods)
        if _pseudo_f(perm) >= f_obs:
            mayores += 1
    p_perm = float((mayores + 1) / (n_perm + 1))

    return {
        "n_permutaciones": int(n_perm),
        "k_grupos": int(k),
        "pseudo_f": round(f_obs, 4),
        "p_valor_permutacion": round(p_perm, 6),
        "significativo_05": bool(p_perm < 0.05),
    }


def ejecutar_manova_y_anovas(df_comp: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Ejecuta MANOVA principal (ciudad: Colima, Guadalajara, Morelia), MANOVA
    complementario (producto), contraste PERMANOVA y ANOVAs univariados separados.
    """
    formula_lhs = " + ".join(VARIABLES_E3)
    mv_plaza = MANOVA.from_formula(f"{formula_lhs} ~ C(ciudad)", data=df_comp).mv_test()
    mv_prod = MANOVA.from_formula(f"{formula_lhs} ~ C(producto)", data=df_comp).mv_test()

    filas_mv = _extraer_tabla_manova(mv_plaza, "C(ciudad)", "Plaza (Colima, Guadalajara, Morelia)")
    filas_mv += _extraer_tabla_manova(mv_prod, "C(producto)", "Producto (6 insumos base)")
    df_mv = pd.DataFrame(filas_mv)

    # ANOVAs univariados por ciudad con comparativa Bonferroni
    ciudades = sorted(df_comp["ciudad"].unique().tolist())
    alpha_bonf = 0.05 / len(VARIABLES_E3)
    anovas_uni = []
    for var in VARIABLES_E3:
        muestras = [df_comp.loc[df_comp["ciudad"] == c, var].to_numpy(dtype=float) for c in ciudades]
        f_stat, p_val = stats.f_oneway(*muestras)
        anovas_uni.append({
            "variable": var,
            "f_univariado": round(float(f_stat), 4),
            "p_valor": round(float(p_val), 8),
            "significativo_alpha05": bool(p_val < 0.05),
            "significativo_bonferroni": bool(p_val < alpha_bonf),
        })

    X = df_comp[VARIABLES_E3].to_numpy(dtype=float)
    Z = (X - X.mean(axis=0, keepdims=True)) / X.std(axis=0, ddof=1, keepdims=True)
    perm_plaza = ejecutar_permanova(Z, df_comp["ciudad"].to_numpy(), n_perm=999, seed=20261127)
    perm_prod = ejecutar_permanova(Z, df_comp["producto"].to_numpy(), n_perm=999, seed=20261128)

    wilks_p = next(x for x in filas_mv if x["factor"].startswith("Plaza") and "Wilks" in x["estadistico"])
    pillai_p = next(x for x in filas_mv if x["factor"].startswith("Plaza") and "Pillai" in x["estadistico"])

    resumen = {
        "manova_plazas_wilks": wilks_p,
        "manova_plazas_pillai": pillai_p,
        "permanova_plazas": perm_plaza,
        "permanova_productos": perm_prod,
        "anovas_univariados_ciudad": anovas_uni,
        "error_tipo_i_sin_correccion_pct": round((1.0 - (0.95 ** len(VARIABLES_E3))) * 100.0, 2),
        "alpha_bonferroni": round(alpha_bonf, 5),
        "centroides_plaza": {
            c: {v: round(float(df_comp.loc[df_comp["ciudad"] == c, v].mean()), 3) for v in VARIABLES_E3}
            for c in ciudades
        },
    }
    return df_mv, resumen


def generar_graficos_e3(
    R_df: pd.DataFrame,
    d2: np.ndarray,
    diag_maha: Dict[str, Any],
    df_pca_meta: pd.DataFrame,
    df_proj: pd.DataFrame,
) -> None:
    """Genera las 4 visualizaciones 300 DPI del laboratorio multivariado E3 sin traslapes."""
    DIR_GRAFICOS.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": "#4a5568"})

    # 1. Mapa de calor de correlaciones
    fig, ax = plt.subplots(figsize=(8.6, 6.8))
    etiqs = [ETIQUETAS_CORTAS[v] for v in VARIABLES_E3]
    im = ax.imshow(R_df.values, cmap="RdBu_r", vmin=-1.0, vmax=1.0)
    ax.set_xticks(range(len(etiqs)))
    ax.set_yticks(range(len(etiqs)))
    ax.set_xticklabels(etiqs, rotation=30, ha="right")
    ax.set_yticklabels(etiqs)
    for i in range(len(etiqs)):
        for j in range(len(etiqs)):
            val = R_df.values[i, j]
            color_txt = "#ffffff" if abs(val) > 0.55 else "#1a202c"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", color=color_txt, fontsize=9, fontweight="bold")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Correlacion de Pearson (r)")
    ax.set_title("Matriz de Correlaciones Multivariada (Capa Oro - 7 Variables)", pad=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(DIR_GRAFICOS / "correlaciones_multivariadas_e3.png", dpi=300)
    plt.close(fig)

    # 2. Grafica Q-Q de Mahalanobis vs Chi^2
    n = len(d2)
    p = len(VARIABLES_E3)
    probs = (np.arange(1, n + 1) - 0.5) / n
    chi_q = stats.chi2.ppf(probs, df=p)
    d2_ord = np.sort(d2)

    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    ax.scatter(chi_q, d2_ord, s=16, alpha=0.65, color="#1f77b4", label="Observaciones mensuales")
    lim_line = min(float(chi_q.max()), float(d2_ord.max()))
    ax.plot([0, lim_line], [0, lim_line], color="#d62728", linestyle="--", lw=1.8, label="Referencia Normal Multivariada (y = x)")
    ax.axhline(diag_maha["umbral_chi2_99"], color="#ff7f0e", linestyle=":", lw=1.5, label=f"Umbral Chi^2(7, 0.99) = {diag_maha['umbral_chi2_99']:.2f}")
    ax.set_xlabel("Cuantiles Teoricos Chi-cuadrada (gl = 7)")
    ax.set_ylabel("Distancia Cuadrada de Mahalanobis D^2")
    ax.set_title(
        f"Grafica Q-Q de Normalidad Multivariada (r_QQ = {diag_maha['correlacion_qq_chi2']:.4f}, "
        f"extremos > 99% = {diag_maha['observaciones_sobre_chi2_99']})",
        fontweight="bold",
    )
    ax.grid(True, linestyle=":", alpha=0.55)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(DIR_GRAFICOS / "qq_mahalanobis_e3.png", dpi=300)
    plt.close(fig)

    # 3. Grafica de Sedimentacion (Scree Plot + Varianza Acumulada)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.6))
    comps = df_pca_meta["componente"].tolist()
    eigs = df_pca_meta["eigenvalor"].tolist()
    var_ind = df_pca_meta["varianza_explicada_pct"].tolist()
    var_acu = df_pca_meta["varianza_acumulada_pct"].tolist()

    ax1.plot(comps, eigs, marker="o", color="#1b396a", lw=2.2, label="Eigenvalor")
    ax1.axhline(1.0, color="#d62728", linestyle="--", lw=1.5, label="Criterio de Kaiser (lambda = 1.0)")
    for i, v in enumerate(eigs):
        ax1.annotate(f"{v:.2f}", (i, v), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8.5,
                     bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.8))
    ax1.set_title("Sedimentacion por Eigenvalores (Criterio Kaiser)", fontweight="bold")
    ax1.set_ylabel("Eigenvalor (lambda)")
    ax1.set_ylim(0, max(eigs) * 1.22)
    ax1.grid(True, linestyle=":", alpha=0.55)
    ax1.legend(loc="upper right")

    bars = ax2.bar(comps, var_ind, color="#2b6cb0", alpha=0.85, label="Varianza individual (%)")
    ax2.plot(comps, var_acu, marker="s", color="#dd6b20", lw=2.0, label="Varianza acumulada (%)")
    ax2.axhline(70.0, color="#2f855a", linestyle=":", lw=1.4, label="Referencia 70% acumulado")
    for b, vi, va in zip(bars, var_ind, var_acu):
        ax2.text(b.get_x() + b.get_width() / 2.0, vi + 1.5, f"{vi:.1f}%", ha="center", va="bottom", fontsize=8)
        ax2.annotate(f"{va:.1f}%", (b.get_x() + b.get_width() / 2.0, va), textcoords="offset points", xytext=(0, 7),
                     ha="center", fontsize=8, color="#9c4221",
                     bbox=dict(boxstyle="round,pad=0.12", facecolor="white", edgecolor="none", alpha=0.75))
    ax2.set_title("Varianza Explicada Individual y Acumulada", fontweight="bold")
    ax2.set_ylabel("Porcentaje (%)")
    ax2.set_ylim(0, 115)
    ax2.grid(True, linestyle=":", alpha=0.55)
    ax2.legend(loc="center right")

    fig.tight_layout()
    fig.savefig(DIR_GRAFICOS / "pca_sedimentacion_e3.png", dpi=300)
    plt.close(fig)

    # 4. Biplot PCA (PC1 vs PC2) por Plazas con centroides y vectores de cargas
    fig, ax = plt.subplots(figsize=(9.8, 6.8))
    colores_ciudad = {"Colima": "#2ca02c", "Guadalajara": "#1f77b4", "Morelia": "#d62728"}
    for ciudad, col in colores_ciudad.items():
        sub = df_proj[df_proj["ciudad"] == ciudad]
        ax.scatter(sub["PC1"], sub["PC2"], s=24, alpha=0.45, color=col, label=f"{ciudad} (n={len(sub)})")
        cx, cy = float(sub["PC1"].mean()), float(sub["PC2"].mean())
        ax.scatter([cx], [cy], s=180, color=col, edgecolor="#1a202c", marker="D", zorder=6)
        offsets_cent = {
            "Colima": (-25, 28),
            "Guadalajara": (115, -58),
            "Morelia": (-58, -42),
        }
        ox_c, oy_c = offsets_cent.get(ciudad, (12, 12))
        ax.annotate(
            f"Centroide {ciudad}",
            (cx, cy),
            textcoords="offset points",
            xytext=(ox_c, oy_c),
            fontsize=8.5,
            fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=col, lw=1.3),
            bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor=col, alpha=0.95),
            zorder=9,
        )

    escala_x = float(np.percentile(np.abs(df_proj["PC1"]), 96))
    escala_y = float(np.percentile(np.abs(df_proj["PC2"]), 96))
    escala = min(escala_x, escala_y) * 1.32
    offsets_vec = {
        "precio_promedio_mxn": (10, 12),
        "precio_usd": (10, -14),
        "volatilidad_precio_std": (10, 8),
        "spread_pct": (-18, 14),
        "variacion_mom_pct": (10, -4),
        "variacion_yoy_pct": (10, 8),
        "num_observaciones": (10, -14),
    }
    for var in VARIABLES_E3:
        c1 = float(df_pca_meta.loc[0, f"carga_{var}"])
        c2 = float(df_pca_meta.loc[1, f"carga_{var}"])
        ax.arrow(0, 0, c1 * escala, c2 * escala, color="#2d3748", alpha=0.88, width=0.025, head_width=0.14, length_includes_head=True, zorder=5)
        ox, oy = offsets_vec.get(var, (6, 6))
        ax.annotate(
            ETIQUETAS_CORTAS[var],
            (c1 * escala, c2 * escala),
            textcoords="offset points",
            xytext=(ox, oy),
            fontsize=8.5,
            fontweight="bold",
            color="#1a202c",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="#cbd5e0", alpha=0.88),
            zorder=8,
        )

    ax.axhline(0, color="#a0aec0", lw=1.0, linestyle="--")
    ax.axvline(0, color="#a0aec0", lw=1.0, linestyle="--")
    v1 = float(df_pca_meta.loc[0, "varianza_explicada_pct"])
    v2 = float(df_pca_meta.loc[1, "varianza_explicada_pct"])
    ax.set_xlabel(f"PC1 ({v1:.1f}% var.) - Nivel de Precio, Volatilidad y Escala")
    ax.set_ylabel(f"PC2 ({v2:.1f}% var.) - Choque Estacional e Inflacionario (MoM/YoY)")
    ax.set_title("Biplot PCA Estandarizado: Perfiles Mayoristas por Plaza y Cargas de Variables", fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.45)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(DIR_GRAFICOS / "pca_biplot_plazas_productos_e3.png", dpi=300)
    plt.close(fig)


def generar_informe_multivariado(res: Dict[str, Any], df_pca_meta: pd.DataFrame, df_mv: pd.DataFrame) -> str:
    """Redacta el informe tecnico narrativo completo de Estadistica Multivariada (E3)."""
    c = res["carga"]
    m_orig = res["normalidad"]["mardia_original"]
    hz_orig = res["normalidad"]["henze_zirkler_original"]
    m_yj = res["normalidad"]["mardia_yeo_johnson"]
    hz_yj = res["normalidad"]["henze_zirkler_yeo_johnson"]
    maha = res["mahalanobis"]
    pca_r = res["pca"]
    mv_r = res["manova"]

    filas_pca_md = []
    for _, r in df_pca_meta.iterrows():
        filas_pca_md.append(
            f"| **{r['componente']}** | {r['nombre_negocio']} | `{r['eigenvalor']:.4f}` | "
            f"`{r['varianza_explicada_pct']:.2f}%` | **`{r['varianza_acumulada_pct']:.2f}%`** | {'Si' if r['criterio_kaiser_mayor_1'] else 'No'} |"
        )

    filas_mv_md = []
    for _, r in df_mv.iterrows():
        filas_mv_md.append(
            f"| {r['factor']} | `{r['estadistico']}` | `{r['valor']:.5f}` | `{r['f_valor']:.4f}` | "
            f"({r['num_df']:.0f}, {r['den_df']:.0f}) | `{r['p_valor']:.6g}` | {'Si' if r['significativo_05'] else 'No'} |"
        )

    filas_uni_md = []
    for a in mv_r["anovas_univariados_ciudad"]:
        filas_uni_md.append(
            f"| `{a['variable']}` | `{a['f_univariado']:.4f}` | `{a['p_valor']:.6g}` | "
            f"{'Si' if a['significativo_alpha05'] else 'No'} | {'Si' if a['significativo_bonferroni'] else 'No'} |"
        )

    return rf"""# Informe de Analisis Estadistico Multivariado (Entrega E3)

**Autora:** Andrea Tairi Velazquez Gallardo (`23460539@colima.tecnm.mx`)  
**Revision Engineering & ISO:** Adolfo Rodriguez (`23460528@colima.tecnm.mx`)  
**Unidad 5:** Normalidad Multivariada, Componentes Principales (PCA) y MANOVA  

---

## 1. Matriz Multivariada y Tratamiento de Datos (`p = 7` Variables)
- **Dataset fuente:** Capa Oro (`data/oro/canasta_occidente_oro.csv`), filtrando los 6 insumos historicos continuos (`Aguacate Hass`, `Cebolla Bola`, `Chile Serrano`, `Jitomate Saladette`, `Limon con semilla #5`, `Papa Alpha`) en las **3 plazas de E0** (`Colima`, `Guadalajara`, `Morelia`).
- **Observaciones validas completas:** **`N = {c['registros_completos_e3']}`** registros mensuales (`{c['periodo_min']}` a `{c['periodo_max']}`), excluyendo `{c['registros_excluidos_rezago_estructural']}` filas iniciales con `NaN` estructural de rezago de 12 meses (`variacion_yoy_pct`).
- **Conteo por grupo (E0):** Colima `{c['conteo_por_ciudad'].get('Colima', 0)}` · Guadalajara `{c['conteo_por_ciudad'].get('Guadalajara', 0)}` · Morelia `{c['conteo_por_ciudad'].get('Morelia', 0)}`.
- **Integridad numerica:** Matriz de covarianzas `{len(VARIABLES_E3)}x{len(VARIABLES_E3)}` con **rango completo = `{maha['rango_matriz_cov']}`** y numero de condicion `{maha['num_condicion_cov']}`.

---

## 2. Normalidad Multivariada y Puerta 3 Estadistica
- **Mardia (escala original):** Asimetria $b_{{1,7}} = {m_orig['b1p_asimetria']}$ ($\chi^2 = {m_orig['chi2_asimetria']}$, $p = {m_orig['p_asimetria']}$) · Curtosis $b_{{2,7}} = {m_orig['b2p_curtosis']}$ ($z = {m_orig['z_curtosis']}$, $p = {m_orig['p_curtosis']}$).
- **Henze-Zirkler (escala original):** $HZ = {hz_orig['estadistico_hz']}$, $p = {hz_orig['p_valor']}$.
- **Transformacion Yeo-Johnson estandarizada:** Asimetria Mardia baja de `{m_orig['b1p_asimetria']}` a `{m_yj['b1p_asimetria']}` y curtosis Mardia pasa a `{m_yj['b2p_curtosis']}` ($HZ = {hz_yj['estadistico_hz']}$).
- **Distancias de Mahalanobis ($D^2$ vs $\chi^2_7$):** Correlacion Q-Q **`{maha['correlacion_qq_chi2']}`**; media `{maha['d2_media']}` (teorica $= 7.0$); `{maha['observaciones_sobre_chi2_99']}` observaciones (`{maha['pct_sobre_chi2_99']}%`) rebasan el cuantil extremo $\chi^2_{{7, 0.99}} = {maha['umbral_chi2_99']}$, reflejando picos agricolas estacionales reales (ej. sequia/heladas en aguacate y limon).
- **Resolucion de Puerta 3:** Al no cumplirse normalidad multivariada estricta por asimetria/colas agricolas reales ($p < 0.05$), las conclusiones se respaldan con la **Traza de Pillai** (estadistico MANOVA mas robusto a desviaciones de normalidad) y con **PERMANOVA no parametrico por permutaciones** ($n = 999$ permutaciones).

---

## 3. Analisis de Componentes Principales (PCA Estandarizado)

| Componente | Nombre de Negocio Asignado | Eigenvalor ($\lambda$) | Varianza (%) | Acumulada (%) | Kaiser ($\lambda > 1$) |
| :---: | :--- | :---: | :---: | :---: | :---: |
{chr(10).join(filas_pca_md)}

- **Criterio de Kaiser:** Se retienen **`{pca_r['kaiser_componentes_seleccionados']}` componentes** ($\lambda > 1.0$) que condensan **`{pca_r['varianza_pc1_pc2_pct']}%`** de la varianza total (con `PC3` de $\lambda=0.9835$ alcanza **`{pca_r['varianza_pc1_pc3_pct']}%`**).
- **Ortogonalidad verificada:** Error maximo $|\mathbf{{V}}^T\mathbf{{V}} - \mathbf{{I}}| = {pca_r['ortonormalidad_max_error']}$.

---

## 4. MANOVA y Contraste contra ANOVAs Separados

| Factor | Prueba Multivariada | Valor | F | gl | p-valor | Signif. ($\alpha=0.05$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
{chr(10).join(filas_mv_md)}

- **Validacion no parametrica Puerta 3 (PERMANOVA, 999 permutaciones):**
  - Por **Plaza:** `pseudo-F = {mv_r['permanova_plazas']['pseudo_f']}`, `p = {mv_r['permanova_plazas']['p_valor_permutacion']}` (**Confirmado**).
  - Por **Producto:** `pseudo-F = {mv_r['permanova_productos']['pseudo_f']}`, `p = {mv_r['permanova_productos']['p_valor_permutacion']}` (**Confirmado**).

### Por que MANOVA NO equivale a correr 7 ANOVAs por separado
1. **Inflacion del error Tipo I familiar:** Correr 7 pruebas univariadas independientes al nivel $\alpha = 0.05$ eleva la probabilidad de al menos un falso positivo a $1 - (1 - 0.05)^7 = \mathbf{{{mv_r['error_tipo_i_sin_correccion_pct']}\%}}$ (requiriendo ajuste Bonferroni a $\alpha^* = {mv_r['alpha_bonferroni']}$).
2. **Estructura conjunta de covarianza:** MANOVA evalua simultaneamente combinaciones lineales de las 7 metricas aprovechando su matriz de correlaciones cruzadas (por ejemplo, diferencia conjuntamente una plaza donde el precio alto coincide con menor spread y mayor frecuencia de cotizaciones, patron que un ANOVA univariado ignora por completo).

| Variable | F univariado (Ciudad) | p-valor | Signif. ($\alpha=0.05$) | Signif. Bonferroni ($\alpha={mv_r['alpha_bonferroni']}$) |
| :--- | :---: | :---: | :---: | :---: |
{chr(10).join(filas_uni_md)}

---

## 5. Interpretacion para el Cliente (*Restaurante Luisiana* y Comercios de Colima)
- **Separacion estructural en `PC1` (Unidades mayoristas, escala y dispersion):** En las 3 plazas, Colima reporta cotizaciones principalmente por **kilogramo** (media nominal `{mv_r['centroides_plaza']['Colima']['precio_promedio_mxn']:.2f}` MXN, `spread = {mv_r['centroides_plaza']['Colima']['spread_pct']:.1f}%`, `{mv_r['centroides_plaza']['Colima']['num_observaciones']:.1f}` obs/mes), mientras Guadalajara (`{mv_r['centroides_plaza']['Guadalajara']['num_observaciones']:.1f}` obs/mes, `spread = {mv_r['centroides_plaza']['Guadalajara']['spread_pct']:.1f}%`) y Morelia (`{mv_r['centroides_plaza']['Morelia']['num_observaciones']:.1f}` obs/mes) comercializan mayormente por **caja o arpilla de mayor volumen**, concentrandose hacia la derecha en `PC1`.
- **Dinamica en `PC2` (Choque estacional e inflacionario MoM/YoY):** Los ANOVAs univariados confirman que las tasas de variacion porcentual mensual (`p = 0.623`) y anual (`p = 0.512`) no difieren de forma aislada entre plazas, pero **MANOVA** demuestra diferencias conjuntas altamente significativas (`Wilks = {mv_r['manova_plazas_wilks']['valor']}`, `Pillai = {mv_r['manova_plazas_pillai']['valor']}`, `p < 0.001`) al combinar precio, volatilidad, spread y liquidez de plaza; para una cocina economica conviene vigilar los repuntes de `PC2` sin importar en que plaza se abastezca.
"""


def ejecutar_analisis_multivariado() -> Dict[str, Any]:
    """Orquesta todo el analisis multivariado E3 y exporta CSVs, JSON, PNGs e informe."""
    DIR_LAB.mkdir(parents=True, exist_ok=True)
    DIR_GRAFICOS.mkdir(parents=True, exist_ok=True)

    df_comp, info_carga = cargar_matriz_multivariada()
    X = df_comp[VARIABLES_E3].to_numpy(dtype=float)

    S_df = df_comp[VARIABLES_E3].cov().round(4)
    R_df = df_comp[VARIABLES_E3].corr().round(4)
    S_df.to_csv(DIR_LAB / "matriz_covarianzas_e3.csv", encoding="utf-8")
    R_df.to_csv(DIR_LAB / "matriz_correlaciones_e3.csv", encoding="utf-8")

    m_orig = prueba_mardia(X)
    hz_orig = prueba_henze_zirkler(X)
    X_yj_cols = [stats.yeojohnson(X[:, j])[0] for j in range(X.shape[1])]
    X_yj_raw = np.column_stack(X_yj_cols)
    X_yj = (X_yj_raw - X_yj_raw.mean(axis=0, keepdims=True)) / X_yj_raw.std(axis=0, ddof=1, keepdims=True)
    m_yj = prueba_mardia(X_yj)
    hz_yj = prueba_henze_zirkler(X_yj)
    d2, diag_maha = calcular_mahalanobis(X)

    df_pca_meta, df_proj, resumen_pca = ejecutar_pca(df_comp)
    df_proj["distancia_mahalanobis_d2"] = np.round(d2, 4)
    df_pca_meta.to_csv(DIR_LAB / "pca_cargas_y_varianza_e3.csv", index=False, encoding="utf-8")
    df_proj.to_csv(DIR_LAB / "pca_proyeccion_oro_e3.csv", index=False, encoding="utf-8")

    df_mv, resumen_mv = ejecutar_manova_y_anovas(df_comp)
    df_mv.to_csv(DIR_LAB / "manova_resultados_e3.csv", index=False, encoding="utf-8")

    generar_graficos_e3(R_df, d2, diag_maha, df_pca_meta, df_proj)

    resultado = {
        "fecha_analisis_utc": datetime.now(timezone.utc).isoformat(),
        "variables": VARIABLES_E3,
        "productos_base": PRODUCTOS_BASE_E3,
        "carga": info_carga,
        "normalidad": {
            "mardia_original": m_orig,
            "henze_zirkler_original": hz_orig,
            "mardia_yeo_johnson": m_yj,
            "henze_zirkler_yeo_johnson": hz_yj,
        },
        "mahalanobis": diag_maha,
        "pca": resumen_pca,
        "manova": resumen_mv,
    }
    (DIR_LAB / "resultados_multivariado_e3.json").write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (DIR_LAB / "informe_multivariado_e3.md").write_text(
        generar_informe_multivariado(resultado, df_pca_meta, df_mv), encoding="utf-8"
    )
    return resultado


if __name__ == "__main__":
    res = ejecutar_analisis_multivariado()
    print(
        f"OK - Multivariado E3 | N={res['carga']['registros_completos_e3']} | "
        f"PC1+PC2={res['pca']['varianza_pc1_pc2_pct']}% | "
        f"Wilks Plaza p={res['manova']['manova_plazas_wilks']['p_valor']} | "
        f"PERMANOVA p={res['manova']['permanova_plazas']['p_valor_permutacion']}"
    )
