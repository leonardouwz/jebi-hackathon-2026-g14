"""
truck_pipeline.py - Detecta intercambios de camión (tiempo muerto).

Estrategia principal: IMU (derivada del cuaternión) → períodos idle del operador = intercambio.
Fallback:            Video MOG2 si no hay IMU disponible.

Input:  video .mp4  +  imu .npy  (opcional)
Output: outputs/truck_events.json
"""
import cv2
import numpy as np
import json
import os
import glob
import sys
from scipy.ndimage import uniform_filter1d


# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────
ROI_X, ROI_Y, ROI_W, ROI_H = 0, 182, 725, 226
SAMPLE_INTERVAL_S   = 2.0
SMOOTH_WINDOW_S     = 30
PRESENCE_THRESHOLD  = 0.1
MIN_EVENT_DURATION_S = 15

# IMU
IMU_SMOOTH_S        = 5     # ventana suavizado cuaternión
IMU_IDLE_PERCENTILE = 40    # por debajo de este percentil = idle
IMU_MERGE_GAP_S     = 5     # unir períodos idle separados < 5s
IMU_MIN_DURATION_S  = 12    # intercambio real dura > 12s


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────
def detect_truck_events(video_path, imu_path=None, output_dir='./outputs'):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    print(f"[video] {total_frames} frames @ {fps:.1f}fps = {total_frames/fps:.0f}s")

    if imu_path and os.path.exists(imu_path):
        print(f"[imu]   usando {imu_path}")
        events = _detect_imu(imu_path, fps, output_dir)
    else:
        print("[imu]   no disponible, usando video MOG2")
        events = _detect_video(video_path, fps, output_dir)

    print(f"\n✓ {len(events)} intercambios detectados → {output_dir}/truck_events.json")
    return events


# ─── DETECTOR IMU ─────────────────────────────────────────────────────────────
def _detect_imu(imu_path, fps, output_dir):
    """
    Derivada del cuaternión (cols 7-10) = velocidad angular real de la pala.
    Idle sostenido > 12s → intercambio de camión.
    """
    data = np.load(imu_path, allow_pickle=True)
    print(f"[imu]   {data.shape[0]} muestras × {data.shape[1]} columnas")

    quat   = data[:, 7:11]
    dq     = np.diff(quat, axis=0)
    dq_mag = np.append(np.sqrt((dq ** 2).sum(axis=1)), 0)

    smooth    = uniform_filter1d(dq_mag, size=max(1, int(IMU_SMOOTH_S * fps)))
    times     = np.arange(len(smooth)) / fps
    threshold = np.percentile(smooth, IMU_IDLE_PERCENTILE)
    print(f"[imu]   dQ mean={smooth.mean():.5f}  p{IMU_IDLE_PERCENTILE}={threshold:.5f}  max={smooth.max():.5f}")

    is_idle = smooth < threshold

    # Rellenar gaps activos cortos para unir períodos idle cercanos
    merge_frames = int(IMU_MERGE_GAP_S * fps)
    is_idle_merged, in_idle, gap_start = is_idle.copy(), False, 0
    for i, idle in enumerate(is_idle):
        if not idle and in_idle:
            gap_start = i
        elif idle and not in_idle and gap_start > 0:
            if (i - gap_start) < merge_frames:
                is_idle_merged[gap_start:i] = True
            gap_start = 0
        in_idle = idle

    events, in_event, t_start = [], False, 0
    for t, idle in zip(times, is_idle_merged):
        if idle and not in_event:
            in_event, t_start = True, t
        elif not idle and in_event:
            in_event = False
            duration = t - t_start
            if duration >= IMU_MIN_DURATION_S:
                events.append({"t_arrival": float(t_start),
                                "t_departure": float(t),
                                "exchange_duration_s": float(duration)})
                print(f"  → intercambio [{t_start:05.1f}s → {t:05.1f}s]  {duration:.1f}s")

    if in_event:
        duration = times[-1] - t_start
        if duration >= IMU_MIN_DURATION_S:
            events.append({"t_arrival": float(t_start),
                           "t_departure": float(times[-1]),
                           "exchange_duration_s": float(duration)})

    _save(events, [{"t": float(t), "signal": float(s)} for t, s in zip(times, smooth)], output_dir)
    return events


# ─── DETECTOR VIDEO (fallback) ────────────────────────────────────────────────
def _detect_video(video_path, fps, output_dir):
    cap       = cv2.VideoCapture(video_path)
    bg_sub    = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=False)
    kernel    = np.ones((5, 5), np.uint8)
    sample_n  = int(fps * SAMPLE_INTERVAL_S)
    presence_signal, timestamps = [], []
    frame_idx = sample_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % sample_n == 0:
            h, w = frame.shape[:2]
            roi  = frame[max(0,ROI_Y):min(h,ROI_Y+ROI_H), max(0,ROI_X):min(w,ROI_X+ROI_W)]
            mask = bg_sub.apply(roi)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            presence_signal.append(np.sum(mask > 0) / mask.size if sample_idx >= 30 else 0.0)
            timestamps.append(frame_idx / fps)
            sample_idx += 1
        frame_idx += 1
    cap.release()

    presence_arr = np.array(presence_signal)
    times_arr    = np.array(timestamps)
    window_size  = max(3, int(SMOOTH_WINDOW_S / SAMPLE_INTERVAL_S))
    smooth       = uniform_filter1d(presence_arr, size=window_size)
    is_present   = smooth > PRESENCE_THRESHOLD

    events, in_event, t_start = [], False, None
    for t, present in zip(times_arr, is_present):
        if present and not in_event:
            in_event, t_start = True, t
        elif not present and in_event:
            in_event = False
            duration = t - t_start
            if duration >= MIN_EVENT_DURATION_S:
                events.append({"t_arrival": float(t_start),
                                "t_departure": float(t),
                                "exchange_duration_s": float(duration)})
                print(f"  → evento [{t_start:05.1f}s → {t:05.1f}s]  {duration:.1f}s")
    if in_event:
        duration = times_arr[-1] - t_start
        if duration >= MIN_EVENT_DURATION_S:
            events.append({"t_arrival": float(t_start),
                           "t_departure": float(times_arr[-1]),
                           "exchange_duration_s": float(duration)})

    _save(events, [{"t": float(t), "presence_raw": float(p), "presence_smooth": float(s)}
                   for t, p, s in zip(times_arr, presence_arr, smooth)], output_dir)
    return events


# ─── GUARDAR ──────────────────────────────────────────────────────────────────
def _save(events, debug, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, 'truck_events.json'), 'w') as f:
        json.dump(events, f, indent=2)
    with open(os.path.join(output_dir, 'motion_debug.json'), 'w') as f:
        json.dump(debug, f, indent=2)


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    video_path = sys.argv[1] if len(sys.argv) > 1 else (
        next(iter(glob.glob('./inputs/*left*.mp4') or glob.glob('./inputs/*.mp4')), None))
    if not video_path:
        print("ERROR: no se encontró video en ./inputs/"); sys.exit(1)

    imu_path = sys.argv[2] if len(sys.argv) > 2 else (
        next(iter(glob.glob('./inputs/*.npy') + glob.glob('./inputs/*.csv')), None))

    detect_truck_events(video_path, imu_path)
