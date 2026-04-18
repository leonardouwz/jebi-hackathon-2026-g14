#!/bin/bash
# Jebi Hackathon 2026 — Grupo 7
# Ejecutar desde la raíz del repo: bash run.sh
#
# Inputs esperados en ./inputs/:
#   - *left*.mp4  o  shovel_left.mp4
#   - *right*.mp4 o  shovel_right.mp4
#   - *.npy       o  imu_data.csv
#
# Outputs en ./outputs/:
#   - metrics.json, cycles.json, truck_events.json, fill_factor.json
#   - report.html, summary.md

# --- 0. CONFIGURACIÓN Y LIMPIEZA ---
# Si algo falla, el script se detiene (opcional, pero ayuda a debuggear)
# set -e 

echo "🚀 Iniciando Pipeline: Mining Productivity 2.0 - Grupo 14"

# Asegurar que las carpetas existan y estén vacías para evitar mezclar datos
mkdir -p ./outputs
mkdir -p ./tmp/frames_left ./tmp/frames_right
rm -rf ./tmp/frames_left/* ./tmp/frames_right/*
rm -rf ./outputs/*

# --- 1. VALIDACIÓN INICIAL DINÁMICA ---
# Buscar cualquier .csv o .npy que contenga la palabra 'imu'
IMU_FILE=$(find ./inputs -type f \( -iname "*imu*.csv" -o -iname "*imu*.npy" \) | head -n 1)

if [ -z "$IMU_FILE" ]; then
    echo "❌ ERROR: No se encontró el archivo IMU (.csv o .npy) en ./inputs/"
    exit 1
fi
echo "📊 Archivo IMU detectado: $IMU_FILE"

# --- 2. INSPECCIÓN DE DATOS ---
# Este script ya valida el esquema (N, 11) que hicimos
python3 ./solution/inspect.py

# --- 3. BÚSQUEDA DINÁMICA Y PROCESAMIENTO DE VIDEO ---

# Buscar cualquier .mp4 que contenga la palabra 'left' o 'izq'
VIDEO_LEFT=$(find ./inputs -type f -iname "*left*.mp4" -o -iname "*izq*.mp4" | head -n 1)
# Buscar cualquier .mp4 que contenga la palabra 'right' o 'der'
VIDEO_RIGHT=$(find ./inputs -type f -iname "*right*.mp4" -o -iname "*der*.mp4" | head -n 1)

# Validar que los encontró
if [ -z "$VIDEO_LEFT" ] || [ -z "$VIDEO_RIGHT" ]; then
    echo "❌ ERROR: No se encontraron los videos estéreo (left/right) en ./inputs/"
    exit 1
fi

echo "🎥 Videos detectados para procesar:"
echo "  - Izquierdo: $VIDEO_LEFT"
echo "  - Derecho: $VIDEO_RIGHT"

echo "📸 Extrayendo frames (esto tomará ~30 segundos)..."

# Fíjate que ahora usamos "$VIDEO_LEFT" en vez del nombre quemado
ffmpeg -i "$VIDEO_LEFT" -vf fps=1/2 -q:v 2 ./tmp/frames_left/f%03d.jpg -hide_banner -loglevel error
ffmpeg -i "$VIDEO_RIGHT" -vf fps=1/2 -q:v 2 ./tmp/frames_right/f%03d.jpg -hide_banner -loglevel error

echo "✅ Frames listos."

# --- 4. EJECUCIÓN DE PIPELINES ---

# A) Detección de Camión (Background Subtraction)
python3 ./solution/truck_pipeline.py

# B) Análisis de Ciclos y Disparidad Estéreo
python3 ./solution/video_pipeline.py

# C) Generación de Insights con Claude API
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️ ADVERTENCIA: ANTHROPIC_API_KEY no está configurada. El Insight Engine fallará."
fi
python3 ./solution/insight_engine.py

# --- 5. CIERRE ---
echo "---"
echo "✅ Proceso completado con éxito."
echo "📂 Resultados guardados en ./outputs/metrics.json"
exit 0