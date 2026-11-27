# Informe de Analisis Estadistico Multivariado (Entrega E3)

**Autora:** Andrea Tairi Velazquez Gallardo (`23460539@colima.tecnm.mx`)  
**Revision Engineering & ISO:** Adolfo Rodriguez (`23460528@colima.tecnm.mx`)  
**Unidad 5:** Normalidad Multivariada, Componentes Principales (PCA) y MANOVA  

---

## 1. Matriz Multivariada y Tratamiento de Datos (`p = 7` Variables)
- **Dataset fuente:** Capa Oro (`data/oro/canasta_occidente_oro.csv`), filtrando los 6 insumos historicos continuos (`Aguacate Hass`, `Cebolla Bola`, `Chile Serrano`, `Jitomate Saladette`, `Limon con semilla #5`, `Papa Alpha`) en las **3 plazas de E0** (`Colima`, `Guadalajara`, `Morelia`).
- **Observaciones validas completas:** **`N = 619`** registros mensuales (`2023-01` a `2026-11`), excluyendo `204` filas iniciales con `NaN` estructural de rezago de 12 meses (`variacion_yoy_pct`).
- **Conteo por grupo (E0):** Colima `274` · Guadalajara `160` · Morelia `185`.
- **Integridad numerica:** Matriz de covarianzas `7x7` con **rango completo = `7`** y numero de condicion `55963.92`.

---

## 2. Normalidad Multivariada y Puerta 3 Estadistica
- **Mardia (escala original):** Asimetria $b_{1,7} = 68.8254$ ($\chi^2 = 7100.4854$, $p = 0.0$) · Curtosis $b_{2,7} = 168.9883$ ($z = 117.4594$, $p = 0.0$).
- **Henze-Zirkler (escala original):** $HZ = 24.4096$, $p = 0.0$.
- **Transformacion Yeo-Johnson estandarizada:** Asimetria Mardia baja de `68.8254` a `14.6406` y curtosis Mardia pasa a `75.5093` ($HZ = 5.9951$).
- **Distancias de Mahalanobis ($D^2$ vs $\chi^2_7$):** Correlacion Q-Q **`0.7755`**; media `6.9887` (teorica $= 7.0$); `47` observaciones (`7.59%`) rebasan el cuantil extremo $\chi^2_{7, 0.99} = 18.4753$, reflejando picos agricolas estacionales reales (ej. sequia/heladas en aguacate y limon).
- **Resolucion de Puerta 3:** Al no cumplirse normalidad multivariada estricta por asimetria/colas agricolas reales ($p < 0.05$), las conclusiones se respaldan con la **Traza de Pillai** (estadistico MANOVA mas robusto a desviaciones de normalidad) y con **PERMANOVA no parametrico por permutaciones** ($n = 999$ permutaciones).

---

## 3. Analisis de Componentes Principales (PCA Estandarizado)

| Componente | Nombre de Negocio Asignado | Eigenvalor ($\lambda$) | Varianza (%) | Acumulada (%) | Kaiser ($\lambda > 1$) |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **PC1** | Indice de Nivel de Precio, Volatilidad y Escala | `3.1200` | `44.57%` | **`44.57%`** | Si |
| **PC2** | Indice de Choque Estacional e Inflacionario (MoM/YoY) | `1.3031` | `18.62%` | **`63.19%`** | Si |
| **PC3** | Indice de Amplitud Mayorista (Spread %) y Riesgo | `0.9835` | `14.05%` | **`77.24%`** | No |
| **PC4** | Indice de Contraste Impulso Mensual vs Anual | `0.7868` | `11.24%` | **`88.48%`** | No |
| **PC5** | Indice de Liquidez y Densidad de Plaza | `0.5513` | `7.88%` | **`96.35%`** | No |
| **PC6** | Componente Residual de Spread vs Volatilidad | `0.2522` | `3.60%` | **`99.96%`** | No |
| **PC7** | Componente Tipo de Cambio Efectivo (MXN vs USD) | `0.0030` | `0.04%` | **`100.00%`** | No |

- **Criterio de Kaiser:** Se retienen **`2` componentes** ($\lambda > 1.0$) que condensan **`63.19%`** de la varianza total (con `PC3` de $\lambda=0.9835$ alcanza **`77.24%`**).
- **Ortogonalidad verificada:** Error maximo $|\mathbf{V}^T\mathbf{V} - \mathbf{I}| = 0.0$.

---

## 4. MANOVA y Contraste contra ANOVAs Separados

| Factor | Prueba Multivariada | Valor | F | gl | p-valor | Signif. ($\alpha=0.05$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| Plaza (Colima, Guadalajara, Morelia) | `Wilks' lambda` | `0.13393` | `150.9788` | (14, 1220) | `0` | Si |
| Plaza (Colima, Guadalajara, Morelia) | `Pillai's trace` | `1.03008` | `92.7002` | (14, 1222) | `0` | Si |
| Plaza (Colima, Guadalajara, Morelia) | `Hotelling-Lawley trace` | `5.24217` | `228.1291` | (14, 973) | `0` | Si |
| Plaza (Colima, Guadalajara, Morelia) | `Roy's greatest root` | `4.99710` | `436.1758` | (7, 611) | `0` | Si |
| Producto (6 insumos base) | `Wilks' lambda` | `0.78464` | `4.3339` | (35, 2556) | `0` | Si |
| Producto (6 insumos base) | `Pillai's trace` | `0.22494` | `4.1119` | (35, 3055) | `0` | Si |
| Producto (6 insumos base) | `Hotelling-Lawley trace` | `0.26243` | `4.5416` | (35, 1715) | `0` | Si |
| Producto (6 insumos base) | `Roy's greatest root` | `0.20959` | `18.2938` | (7, 611) | `0` | Si |

- **Validacion no parametrica Puerta 3 (PERMANOVA, 999 permutaciones):**
  - Por **Plaza:** `pseudo-F = 141.7209`, `p = 0.001` (**Confirmado**).
  - Por **Producto:** `pseudo-F = 4.6119`, `p = 0.001` (**Confirmado**).

### Por que MANOVA NO equivale a correr 7 ANOVAs por separado
1. **Inflacion del error Tipo I familiar:** Correr 7 pruebas univariadas independientes al nivel $\alpha = 0.05$ eleva la probabilidad de al menos un falso positivo a $1 - (1 - 0.05)^7 = \mathbf{30.17\%}$ (requiriendo ajuste Bonferroni a $\alpha^* = 0.00714$).
2. **Estructura conjunta de covarianza:** MANOVA evalua simultaneamente combinaciones lineales de las 7 metricas aprovechando su matriz de correlaciones cruzadas (por ejemplo, diferencia conjuntamente una plaza donde el precio alto coincide con menor spread y mayor frecuencia de cotizaciones, patron que un ANOVA univariado ignora por completo).

| Variable | F univariado (Ciudad) | p-valor | Signif. ($\alpha=0.05$) | Signif. Bonferroni ($\alpha=0.00714$) |
| :--- | :---: | :---: | :---: | :---: |
| `precio_promedio_mxn` | `257.2827` | `0` | Si | Si |
| `precio_usd` | `251.8542` | `0` | Si | Si |
| `volatilidad_precio_std` | `90.0116` | `0` | Si | Si |
| `spread_pct` | `139.8345` | `0` | Si | Si |
| `variacion_mom_pct` | `0.4738` | `0.622843` | No | No |
| `variacion_yoy_pct` | `0.6694` | `0.512363` | No | No |
| `num_observaciones` | `969.0272` | `0` | Si | Si |

---

## 5. Interpretacion para el Cliente (*Restaurante Luisiana* y Comercios de Colima)
- **Separacion estructural en `PC1` (Unidades mayoristas, escala y dispersion):** En las 3 plazas, Colima reporta cotizaciones principalmente por **kilogramo** (media nominal `36.53` MXN, `spread = 24.1%`, `8.6` obs/mes), mientras Guadalajara (`23.1` obs/mes, `spread = 58.9%`) y Morelia (`20.6` obs/mes) comercializan mayormente por **caja o arpilla de mayor volumen**, concentrandose hacia la derecha en `PC1`.
- **Dinamica en `PC2` (Choque estacional e inflacionario MoM/YoY):** Los ANOVAs univariados confirman que las tasas de variacion porcentual mensual (`p = 0.623`) y anual (`p = 0.512`) no difieren de forma aislada entre plazas, pero **MANOVA** demuestra diferencias conjuntas altamente significativas (`Wilks = 0.13393`, `Pillai = 1.03008`, `p < 0.001`) al combinar precio, volatilidad, spread y liquidez de plaza; para una cocina economica conviene vigilar los repuntes de `PC2` sin importar en que plaza se abastezca.
