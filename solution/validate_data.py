import os
import json
import pandas as pd
import numpy as np
import subprocess
import sys

def validate_imu_data(file_path):
    print(f"--- Iniciando inspección de: {file_path} ---")
    
    # 1. Carga de datos según extensión
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
        data = df.values
    elif file_path.endswith('.npy'):
        data = np.load(file_path)
    else:
        raise ValueError("Formato de archivo no soportado. Debe ser .csv o .npy")

    # 2. Validación del Esquema (N, 11)
    shape = data.shape
    if len(shape) != 2 or shape[1] != 11:
        raise ValueError(f"Error de esquema: Se esperaba (N, 11), se obtuvo {shape}")
    
    print(f"✅ Esquema validado: {shape[0]} filas y {shape[1]} columnas.")

    # 3. Inferencia de Timestamp (Asumiendo que es la primera columna)
    # Si los valores son muy grandes, podrían ser milisegundos; si son pequeños, segundos.
    first_ts = data[0, 0]
    last_ts = data[-1, 0]
    duration = last_ts - first_ts
    
    unit = "segundos" if duration < 10000 else "milisegundos"
    total_seconds = duration if unit == "segundos" else duration / 1000
    
    print(f"✅ Timestamps inferidos en {unit}. Duración total: {total_seconds:.2f}s")
    
    return {
        "file_id": os.path.basename(file_path),
        "total_duration_seconds": float(total_seconds),
        "rows": shape[0]
    }

def run_pipeline(script_name):
    print(f"--- Ejecutando {script_name} ---")
    try:
        # Ejecuta el script y espera a que termine
        result = subprocess.run(['python3', f'./solution/{script_name}'], 
                               capture_output=True, text=True, check=True)
        print(f"✅ {script_name} completado con éxito.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {script_name}:")
        print(e.stderr)
        return False

def main():
    # Rutas relativas según contrato de Jebi
    input_dir = "./inputs"
    output_dir = "./outputs"
    os.makedirs(output_dir, exist_ok=True)

    # Buscar el archivo IMU (prioridad al .csv por el contrato de Jebi)
    imu_file = None
    for f in os.listdir(input_dir):
        if f.endswith('.csv') and 'imu' in f.lower():
            imu_file = os.path.join(input_dir, f)
            break
    
    if not imu_file:
        # Backup por si aún usan .npy en desarrollo
        for f in os.listdir(input_dir):
            if f.endswith('.npy'):
                imu_file = os.path.join(input_dir, f)
                break

    if not imu_file:
        print("❌ Error: No se encontró el archivo IMU en ./inputs/")
        sys.exit(1)

    try:
        # 1. Validar datos
        metadata = validate_imu_data(imu_file)
        
        # Crear el esqueleto del metrics.json
        metrics = {
            "metadata": metadata,
            "video_pipeline": {"status": "pending", "cycles": []},
            "truck_pipeline": {"status": "pending"},
            "insight_engine": {"status": "pending"}
        }

        # 2. Correr pipelines en secuencia
        pipelines = ["truck_pipeline.py", "video_pipeline.py", "insight_engine.py"]
        for p in pipelines:
            success = run_pipeline(p)
            if not success:
                print(f"⚠️ El pipeline {p} falló, pero el orquestador continúa...")

        # Guardar resultados preliminares si es necesario
        with open(os.path.join(output_dir, "metrics.json"), "w") as f:
            json.dump(metrics, f, indent=4)

    except Exception as e:
        print(f"❌ Fallo crítico en el orquestador: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()