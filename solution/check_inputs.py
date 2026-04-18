"""
solution/inspect.py - Valida inputs antes de correr el pipeline.
Verifica IMU (schema N×11) y que existan los videos.
"""
import numpy as np
import pandas as pd
import glob
import sys
import os


def find_imu():
    patterns = ['./inputs/*imu*.npy', './inputs/*imu*.csv',
                './inputs/*.npy',     './inputs/*.csv']
    for p in patterns:
        hits = glob.glob(p)
        if hits:
            return hits[0]
    return None


def find_videos():
    left  = glob.glob('./inputs/*left*.mp4')  + glob.glob('./inputs/*izq*.mp4')
    right = glob.glob('./inputs/*right*.mp4') + glob.glob('./inputs/*der*.mp4')
    return (left[0] if left else None), (right[0] if right else None)


def main():
    ok = True

    # ── IMU ────────────────────────────────────────────────────────────────
    imu_path = find_imu()
    if not imu_path:
        print("❌ IMU: no encontrado en ./inputs/"); ok = False
    else:
        try:
            arr = np.load(imu_path) if imu_path.endswith('.npy') else pd.read_csv(imu_path).values
            if arr.ndim != 2 or arr.shape[1] != 11:
                print(f"❌ IMU: schema inesperado {arr.shape}, esperado (N, 11)"); ok = False
            else:
                fps_est = arr.shape[0] / max((arr[-1,0] - arr[0,0]) / 1e9, 1)
                print(f"✓ IMU: {imu_path}  ({arr.shape[0]} muestras, ~{arr.shape[0]/15:.0f}s)")
        except Exception as e:
            print(f"❌ IMU: error al leer — {e}"); ok = False

    # ── Videos ─────────────────────────────────────────────────────────────
    vl, vr = find_videos()
    if not vl:
        print("❌ Video izquierdo: no encontrado"); ok = False
    else:
        print(f"✓ Video izquierdo: {vl}")
    if not vr:
        print("❌ Video derecho: no encontrado"); ok = False
    else:
        print(f"✓ Video derecho: {vr}")

    if not ok:
        sys.exit(1)
    print("✓ Validación de inputs OK")


if __name__ == '__main__':
    main()
