"""
solution/video_pipeline.py
Paso 3 del pipeline (run.sh): Análisis IMU + fill factor estéreo.

Lee:   ./inputs/*imu*.{npy,csv}
       ./tmp/frames_left/*.jpg   (extraídos por ffmpeg a 0.5 fps)
       ./tmp/frames_right/*.jpg
       ./outputs/truck_events.json  (generado por truck_pipeline.py)

Genera: ./outputs/metrics.json   ← estructura que consume insight_engine.py
        ./outputs/cycles.json
        ./outputs/fill_factor.json
"""
import cv2
import numpy as np
import json
import os
import glob
import sys

sys.path.insert(0, os.path.dirname(__file__))
from imu_pipeline import analyze_imu

OUTPUT_DIR       = './outputs'
TRUCK_BED_ROI    = (200, 80, 750, 320)   # (x1,y1,x2,y2) en frame 1280×720
FRAME_INTERVAL_S = 2.0                   # ffmpeg extrajo 1 frame cada 2s
NUM_DISPARITIES  = 64
BLOCK_SIZE       = 9
SCALE            = 0.5                   # downscale para SGBM más rápido
BUCKET_CAP_T     = 68                    # EX-5600 capacidad nominal (t)


# ─── IMU ──────────────────────────────────────────────────────────────────────

def run_imu():
    patterns = ['./inputs/*imu*.npy', './inputs/*imu*.csv',
                './inputs/*.npy',     './inputs/*.csv']
    imu_path = next((f for p in patterns for f in glob.glob(p)), None)
    if not imu_path:
        print("[imu] No se encontró IMU — skipping")
        return None, None
    print(f"[imu] Analizando {imu_path}")
    result = analyze_imu(imu_path)
    s = result['summary']
    print(f"[imu] {s['n_cycles_detected']} ciclos  |  "
          f"jerk={s['smoothness_rms_jerk']:.4f}  |  "
          f"dead={s['time_dead_s']:.1f}s")
    return result, imu_path


# ─── STEREO FILL FACTOR ───────────────────────────────────────────────────────

def run_stereo():
    frames_l = sorted(glob.glob('./tmp/frames_left/*.jpg'))
    frames_r = sorted(glob.glob('./tmp/frames_right/*.jpg'))
    if not frames_l or not frames_r:
        print("[stereo] Sin frames en ./tmp/ — skipping fill factor")
        return [], []

    n = min(len(frames_l), len(frames_r))
    print(f"[stereo] {n} pares de frames  (~{n * FRAME_INTERVAL_S:.0f}s de video)")

    sgbm = cv2.StereoSGBM_create(
        minDisparity=0,      numDisparities=NUM_DISPARITIES,
        blockSize=BLOCK_SIZE,
        P1 = 8  * 3 * BLOCK_SIZE ** 2,
        P2 = 32 * 3 * BLOCK_SIZE ** 2,
        disp12MaxDiff=1,     uniquenessRatio=10,
        speckleWindowSize=80, speckleRange=32,
        mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
    )

    s  = SCALE
    x1 = int(TRUCK_BED_ROI[0] * s); y1 = int(TRUCK_BED_ROI[1] * s)
    x2 = int(TRUCK_BED_ROI[2] * s); y2 = int(TRUCK_BED_ROI[3] * s)
    scores = []

    for i in range(n):
        fl = cv2.imread(frames_l[i])
        fr = cv2.imread(frames_r[i])
        if fl is None or fr is None:
            continue
        fl_s = cv2.resize(fl, None, fx=s, fy=s)
        fr_s = cv2.resize(fr, None, fx=s, fy=s)
        h, w = fl_s.shape[:2]
        gl = cv2.cvtColor(fl_s, cv2.COLOR_BGR2GRAY)
        gr = cv2.cvtColor(fr_s, cv2.COLOR_BGR2GRAY)
        disp  = sgbm.compute(gl, gr).astype(np.float32) / 16.0
        roi_d = disp[max(0,y1):min(h,y2), max(0,x1):min(w,x2)]
        valid = roi_d[roi_d > 1.0]
        score = float(np.median(valid)) if valid.size > 0 else 0.0
        scores.append({"t": float(i * FRAME_INTERVAL_S), "disparity": score})
        if i % 30 == 0:
            print(f"  t={i*FRAME_INTERVAL_S:.0f}s  disp={score:.1f}")

    # Normalizar por período de carga
    truck_path = os.path.join(OUTPUT_DIR, 'truck_events.json')
    exchanges  = json.load(open(truck_path)) if os.path.exists(truck_path) else []
    total_s    = n * FRAME_INTERVAL_S
    boundaries = [0.0] + [e['t_departure'] for e in exchanges] + [total_s]
    periods    = [(boundaries[i], boundaries[i+1]) for i in range(len(boundaries)-1)]

    vals   = [s['disparity'] for s in scores if s['disparity'] > 0]
    d_min  = float(np.percentile(vals, 5))  if vals else 0
    d_max  = float(np.percentile(vals, 95)) if vals else 1
    d_rng  = max(d_max - d_min, 1.0)

    fill_by_period = []
    for t0, t1 in periods:
        pts = [s['disparity'] for s in scores if t0 <= s['t'] <= t1 and s['disparity'] > 0]
        if not pts:
            continue
        last = pts[len(pts)//2:] or pts
        dm   = float(np.mean(last))
        ff   = float(np.clip((dm - d_min) / d_rng, 0.0, 1.0))
        fill_by_period.append({
            "t_start": float(t0), "t_end": float(t1),
            "duration_s": float(t1 - t0),
            "disparity_mean": round(dm, 2),
            "fill_factor": round(ff, 3)
        })
        print(f"  [{t0:.0f}s-{t1:.0f}s] fill_factor={ff:.2f}")

    with open(os.path.join(OUTPUT_DIR, 'disparity_debug.json'), 'w') as f:
        json.dump(scores, f, indent=2)

    print(f"[stereo] ✓ {len(fill_by_period)} períodos procesados")
    return fill_by_period, scores


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=== video_pipeline: IMU + Stereo ===\n")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. IMU
    imu_result, imu_path = run_imu()
    print()

    # 2. Stereo
    fill_factors, _ = run_stereo()
    print()

    # 3. Leer truck_events
    truck_path = os.path.join(OUTPUT_DIR, 'truck_events.json')
    exchanges  = json.load(open(truck_path)) if os.path.exists(truck_path) else []

    # 4. Calcular métricas agregadas
    imu_summary = imu_result['summary'] if imu_result else {}
    cycles      = imu_result['cycles']  if imu_result else []

    valid_dur   = [c['duration_s'] for c in cycles if 5 < c['duration_s'] < 120]
    mean_cycle  = float(np.mean(valid_dur))   if valid_dur else 0.0
    cycles_per_h= 3600 / mean_cycle           if mean_cycle > 0 else 0.0

    ff_list     = [f['fill_factor'] for f in fill_factors]
    mean_fill   = float(np.mean(ff_list))     if ff_list else 0.70

    productivity= cycles_per_h * mean_fill * BUCKET_CAP_T
    dead_times  = [e['exchange_duration_s'] for e in exchanges]
    total_dead  = float(sum(dead_times))
    mean_dead   = float(np.mean(dead_times))  if dead_times else 0.0
    total_dur_s = imu_summary.get('duration_s', 0)

    # 5. metrics.json — estructura compatible con insight_engine.py
    metrics = {
        "metadata": {
            "total_duration_seconds": round(total_dur_s, 1),
            "imu_file": os.path.basename(imu_path) if imu_path else "unknown",
            "truck_pipeline": {
                "n_exchanges":               len(exchanges),
                "total_time_in_roi_seconds": round(total_dead, 1),
                "mean_exchange_duration_s":  round(mean_dead, 1)
            }
        },
        "video_pipeline": {
            "status": "ok",
            "aggregated_metrics": {
                "total_cycles":        len(cycles),
                "mean_cycle_time_s":   round(mean_cycle, 1),
                "cycles_per_hour":     round(cycles_per_h, 2),
                "mean_fill_factor":    round(mean_fill, 3),
                "productivity_t_per_h":round(productivity, 1),
                "bucket_capacity_t":   BUCKET_CAP_T,
                "smoothness_rms_jerk": round(imu_summary.get('smoothness_rms_jerk', 0), 4),
                "pct_productive_time": round(imu_summary.get('pct_productive_time', 0), 1)
            },
            "cycles":       cycles,
            "fill_factors": fill_factors
        }
    }

    with open(os.path.join(OUTPUT_DIR, 'metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=2)
    with open(os.path.join(OUTPUT_DIR, 'cycles.json'), 'w') as f:
        json.dump({'summary': imu_summary, 'cycles': cycles}, f, indent=2)
    with open(os.path.join(OUTPUT_DIR, 'fill_factor.json'), 'w') as f:
        json.dump(fill_factors, f, indent=2)

    agg = metrics['video_pipeline']['aggregated_metrics']
    print(f"✓ metrics.json:  {agg['total_cycles']} ciclos  |  "
          f"fill={agg['mean_fill_factor']:.0%}  |  "
          f"{agg['productivity_t_per_h']:.0f} t/h")
