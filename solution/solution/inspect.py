"""Ejecutar al inicio del día para verificar que los datos coinciden con lo esperado."""
import numpy as np, cv2, glob, os, sys
from pathlib import Path

inputs = Path(sys.argv[1] if len(sys.argv) > 1 else "./inputs")

imu_files = list(inputs.glob("*imu*.npy")) + list(inputs.glob("*imu*.csv")) + list(inputs.glob("imu_data.*"))
left_files = list(inputs.glob("*left*.mp4"))
right_files = list(inputs.glob("*right*.mp4"))

print(f"IMU:   {imu_files}")
print(f"Left:  {left_files}")
print(f"Right: {right_files}
")

if imu_files:
    imu_path = imu_files[0]
    if imu_path.suffix == '.npy':
        a = np.load(imu_path, allow_pickle=True)
    else:
        import pandas as pd
        a = pd.read_csv(imu_path).values
    print(f"[IMU] {imu_path.name}")
    print(f"  shape={a.shape}, dtype={a.dtype}")
    print(f"  primeras 2 filas:
{a[:2]}")
    if a.shape[1] == 11:
        t = (a[:,0] - a[0,0]) / 1e9
        print(f"  → Duración: {t[-1]:.1f}s | fs medio: {len(a)/t[-1]:.1f} Hz")
        print(f"  → Schema esperado: t, ax,ay,az, gx,gy,gz, qw,qx,qy,qz ✓")
    else:
        print(f"  ⚠️ Schema NO coincide con (N,11). Revisar columnas.")

for path in left_files + right_files:
    cap = cv2.VideoCapture(str(path))
    print(f"[VIDEO] {path.name}: {int(cap.get(3))}x{int(cap.get(4))} @ {cap.get(cv2.CAP_PROP_FPS):.1f}fps, {int(cap.get(7))} frames")
    cap.release()
