"""
stereo_pipeline.py - Estima fill factor del balde por ciclo usando disparidad estéreo.

Lógica:
  - El truck bed (estructura rectangular) es visible en la mayoría de los frames.
  - Material acumulado → más cerca de la cámara → mayor disparidad.
  - Muestreamos frames cada ~2s y calculamos disparidad media en el truck bed ROI.
  - Normalizamos por ciclo (del truck_events.json) para obtener fill factor 0-1.

Input:  inputs/*left*.mp4  +  inputs/*right*.mp4
Output: outputs/fill_factor.json   (fill factor por ciclo)
        outputs/disparity_debug.json
"""
import cv2
import numpy as np
import json
import os
import glob
import sys

# ─── ROI del truck bed (en píxeles del frame 1280×720) ────────────────────────
# Zona donde el truck bed es visible: ajustar si la cámara es diferente
TRUCK_BED_ROI = (200, 80, 750, 320)   # (x1, y1, x2, y2) en la imagen IZQUIERDA

# ─── Parámetros SGBM ──────────────────────────────────────────────────────────
NUM_DISPARITIES = 96    # múltiplo de 16
BLOCK_SIZE      = 11    # impar
SAMPLE_EVERY_S  = 2.0   # muestrear 1 frame cada N segundos


def compute_disparity_score(img_l, img_r):
    """Retorna el score de disparidad media en el ROI del truck bed."""
    x1, y1, x2, y2 = TRUCK_BED_ROI
    h, w = img_l.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)

    gray_l = cv2.cvtColor(img_l, cv2.COLOR_BGR2GRAY)
    gray_r = cv2.cvtColor(img_r, cv2.COLOR_BGR2GRAY)

    # SGBM: más robusto que BM en escenas con poca textura
    sgbm = cv2.StereoSGBM_create(
        minDisparity=0,
        numDisparities=NUM_DISPARITIES,
        blockSize=BLOCK_SIZE,
        P1=8  * 3 * BLOCK_SIZE ** 2,
        P2=32 * 3 * BLOCK_SIZE ** 2,
        disp12MaxDiff=1,
        uniquenessRatio=10,
        speckleWindowSize=100,
        speckleRange=32,
        mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
    )

    disp = sgbm.compute(gray_l, gray_r).astype(np.float32) / 16.0

    roi_disp = disp[y1:y2, x1:x2]

    # Ignorar píxeles inválidos (disparidad < 0 o 0)
    valid = roi_disp[roi_disp > 1.0]
    if valid.size == 0:
        return 0.0

    return float(np.median(valid))


def run_stereo_pipeline(video_l, video_r, output_dir='./outputs'):
    cap_l = cv2.VideoCapture(video_l)
    cap_r = cv2.VideoCapture(video_r)

    fps          = cap_l.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap_l.get(cv2.CAP_PROP_FRAME_COUNT))
    sample_n     = max(1, int(fps * SAMPLE_EVERY_S))

    print(f"[stereo] {total_frames} frames @ {fps:.1f}fps  ROI={TRUCK_BED_ROI}")

    scores   = []   # (t_s, disparity_score)
    frame_idx = 0

    while True:
        ret_l, fl = cap_l.read()
        ret_r, fr = cap_r.read()
        if not ret_l or not ret_r:
            break

        if frame_idx % sample_n == 0:
            t = frame_idx / fps
            score = compute_disparity_score(fl, fr)
            scores.append({"t": float(t), "disparity": score})
            if frame_idx % (sample_n * 10) == 0:
                print(f"  t={t:.0f}s  disparity={score:.1f}")

        frame_idx += 1

    cap_l.release()
    cap_r.release()
    print(f"[stereo] {len(scores)} muestras procesadas")

    if not scores:
        return []

    # ── Normalizar fill factor por ciclo ──────────────────────────────────────
    # Cargar ciclos/eventos de camión si existen
    truck_events_path = os.path.join(output_dir, 'truck_events.json')
    if os.path.exists(truck_events_path):
        with open(truck_events_path) as f:
            exchanges = json.load(f)
        # Definir períodos de carga: de fin de intercambio a inicio del siguiente
        total_duration = total_frames / fps
        boundaries = [0.0]
        for e in exchanges:
            boundaries.append(e['t_departure'])
        boundaries.append(total_duration)
        loading_periods = [(boundaries[i], boundaries[i+1]) for i in range(len(boundaries)-1)]
    else:
        # Sin eventos: un solo período
        loading_periods = [(0.0, total_frames / fps)]

    # Calcular fill factor por período de carga (= fill factor por camión)
    disp_arr = np.array([s['disparity'] for s in scores if s['disparity'] > 0])
    d_min = np.percentile(disp_arr, 5)   # truck vacío (inicio de cada período)
    d_max = np.percentile(disp_arr, 95)  # truck lleno
    d_range = max(d_max - d_min, 1.0)

    fill_by_period = []
    for t_start, t_end in loading_periods:
        period_scores = [s['disparity'] for s in scores
                         if t_start <= s['t'] <= t_end and s['disparity'] > 0]
        if not period_scores:
            continue
        # Usar el máximo de la última mitad del período (cuando el truck está más lleno)
        last_half = period_scores[len(period_scores)//2:]
        d_period  = np.mean(last_half) if last_half else np.mean(period_scores)
        ff        = float(np.clip((d_period - d_min) / d_range, 0.0, 1.0))
        fill_by_period.append({
            "t_start": float(t_start),
            "t_end":   float(t_end),
            "duration_s": float(t_end - t_start),
            "disparity_mean": float(d_period),
            "fill_factor": ff
        })
        print(f"  [{t_start:.0f}s-{t_end:.0f}s] fill_factor={ff:.2f}  disp={d_period:.1f}")

    # ── Guardar ───────────────────────────────────────────────────────────────
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, 'fill_factor.json'), 'w') as f:
        json.dump(fill_by_period, f, indent=2)
    with open(os.path.join(output_dir, 'disparity_debug.json'), 'w') as f:
        json.dump(scores, f, indent=2)

    print(f"\n✓ fill_factor.json guardado ({len(fill_by_period)} períodos)")
    return fill_by_period


if __name__ == '__main__':
    video_l = next(iter(glob.glob('./inputs/*left*.mp4')),  None)
    video_r = next(iter(glob.glob('./inputs/*right*.mp4')), None)

    if not video_l or not video_r:
        print("ERROR: faltan videos en ./inputs/"); sys.exit(1)

    print(f"Left:  {video_l}")
    print(f"Right: {video_r}")
    run_stereo_pipeline(video_l, video_r)
