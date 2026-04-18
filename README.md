# Jebi Hackathon 2026 - Grupo 14

**Mining Productivity 2.0** — Cuantificación de productividad de pala Hitachi EX-5600 cargando camiones CAT 793F usando video estéreo + IMU.

---

## Cómo funciona

El sistema mide productividad como:

> **Productividad (t/h) = (ciclos/hora) × fill factor × 68 t/bucket**

Las 4 métricas que extrae el pipeline:
1. **Tiempo de ciclo** — segmentación por IMU (acelerómetro + giroscopio)
2. **Fill factor del bucket** — disparidad estéreo (StereoSGBM sobre frames extraídos por ffmpeg)
3. **Tiempo muerto por intercambio de camión** — derivada de quaternion IMU
4. **Suavidad del operador** — RMS del jerk (derivada de aceleración)

---

## Requisitos previos

### Sistema
- macOS / Linux
- Python 3.11+
- ffmpeg
- Node.js 18+ (solo para el dashboard visual)

### Instalar dependencias del sistema (macOS)

```bash
# Instalar Homebrew si no lo tienes
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/homebrew/install/HEAD/install.sh)"

# Instalar ffmpeg
brew install ffmpeg

# Instalar Node.js (si no lo tienes)
brew install node
```

### Instalar dependencias Python

```bash
pip3 install -r requirements.txt
```

### API Key de Anthropic

El paso final del pipeline llama a Claude (claude-sonnet-4-6) para generar el reporte narrativo. Necesitas exportar tu API key antes de correr:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## Inputs esperados

Coloca los 3 archivos en `./inputs/` antes de correr:

| Archivo | Descripción |
|---|---|
| `*imu*.csv` o `*imu*.npy` | Datos IMU — shape (N, 11): timestamp, accel xyz, gyro xyz, quaternion wxyz |
| `*left*.mp4` | Video cámara izquierda (estéreo) |
| `*right*.mp4` | Video cámara derecha (estéreo) |

El script detecta los archivos dinámicamente por nombre — no importa el prefijo.

---

## Correr el pipeline

```bash
# Desde la raíz del repositorio
bash run.sh
```

El pipeline hace lo siguiente en orden:
1. Valida que los 3 inputs existan y tengan el schema correcto
2. Extrae frames a 0.5 fps con ffmpeg → `./tmp/frames_left/` y `./tmp/frames_right/`
3. Detecta intercambios de camión via derivada de quaternion IMU → `outputs/truck_events.json`
4. Analiza ciclos IMU + fill factor estéreo → `outputs/metrics.json`, `cycles.json`, `fill_factor.json`
5. Llama a Claude API para generar insights → `outputs/report.html`, `summary.md`
6. Copia `outputs/metrics_dashboard.json` → `dashboard_ui/src/metrics.json` para el dashboard

**Tiempo estimado: 3–8 minutos** dependiendo de la duración del video.

---

## Outputs generados

Todos en `./outputs/`:

| Archivo | Contenido |
|---|---|
| `metrics.json` | KPIs agregados (ciclos, fill factor, productividad t/h, jerk) |
| `cycles.json` | Un registro por ciclo detectado |
| `truck_events.json` | Tiempos de intercambio de camión |
| `fill_factor.json` | Fill factor por período de carga |
| `report.html` | Dashboard HTML standalone con gráficos |
| `summary.md` | Narrativa con recomendación accionable |

---

## Ver el dashboard visual (opcional)

El dashboard es una app React/Vite que se alimenta de los resultados del pipeline.

### Primera vez

```bash
cd dashboard_ui
npm install
npm run dev
```

### Veces siguientes

```bash
cd dashboard_ui
npm run dev
```

Abre `http://localhost:5173` en el navegador.

**Para ver los datos reales:**
1. Corre `bash run.sh` primero (actualiza `dashboard_ui/src/metrics.json` automáticamente)
2. Con el dev server corriendo, arrastra los 3 archivos de `./inputs/` al área de drop del dashboard
3. Click en **"Ejecutar Análisis"** — espera 3 segundos y aparece el reporte completo

> Los archivos arrastrados solo desbloquean el botón para la demo. El procesamiento real lo hace `run.sh`.

---

## Estructura del repositorio

```
.
├── run.sh                      # Entrypoint principal
├── requirements.txt            # Dependencias Python
├── inputs/                     # Datos de entrada (no commiteados)
├── outputs/                    # Resultados generados (no commiteados)
├── tmp/                        # Frames temporales de ffmpeg (no commiteados)
├── solution/
│   ├── check_inputs.py         # Validación de schema de inputs
│   ├── truck_pipeline.py       # Detección de intercambios de camión (IMU)
│   ├── imu_pipeline.py         # Análisis de ciclos y suavidad (IMU)
│   ├── video_pipeline.py       # Stereo fill factor + métricas agregadas
│   ├── insight_engine.py       # Reporte Claude API + gráficos + dashboard JSON
│   └── video/
│       ├── stereo_pipeline.py  # Pipeline estéreo alternativo (VideoCapture)
│       ├── grafico.py          # Visualización de señal de detección
│       └── generador_video.py  # Video anotado con ROI y estado
└── dashboard_ui/               # App React/Vite para demo visual
    └── src/
        ├── metrics.json        # Generado por run.sh — datos reales del pipeline
        └── metrics.ts          # Re-exporta metrics.json al dashboard
```

---

## Entrega final

```bash
git add .
git commit -m "Final submission"
git push origin main
git tag submission
git push --tags
```

La entrega cierra el **18 de abril a las 17:00**. Jebi clonará este repo y correrá `bash run.sh` contra un dataset distinto — el script detecta archivos dinámicamente, sin paths ni duraciones hardcodeadas.
