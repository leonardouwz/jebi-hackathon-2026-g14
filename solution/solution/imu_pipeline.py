"""Pipeline IMU: carga, segmentación de swings, detección de paradas, métricas."""
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.signal import savgol_filter

# ─── CONFIG ──────────────────────────────────────────────────────────
STOP_THRESHOLD_DEG_S = 5.0   # umbral de "pala quieta" en °/s
MIN_STOP_DURATION = 1.5       # segundos mínimos para considerar parada
LONG_STOP_THRESHOLD = 30.0   # paradas "muertas"
MED_STOP_THRESHOLD = 10.0    # esperas

# ─── LOADER ─────────────────────────────────────────────────────────
def load_imu(path):
    """Carga IMU desde .npy o .csv. Devuelve dict con arrays + metadata."""
    p = Path(path)
    if p.suffix == '.npy':
        arr = np.load(p, allow_pickle=True)
    elif p.suffix == '.csv':
        df = pd.read_csv(p)
        arr = df.values
    else:
        raise ValueError(f"Formato IMU no soportado: {p.suffix}")
    
    if arr.ndim != 2 or arr.shape[1] != 11:
        raise ValueError(f"Schema IMU inesperado: shape={arr.shape}, esperado (N, 11)")
    
    # Timestamps: inferir unidad (ns, ms, o s)
    ts = arr[:, 0]
    dt_raw = np.median(np.diff(ts))
    if dt_raw > 1e6:      # nanosegundos
        t = (ts - ts[0]) / 1e9
    elif dt_raw > 1:      # milisegundos
        t = (ts - ts[0]) / 1e3
    else:                 # segundos
        t = ts - ts[0]
    
    return {
        't': t,
        'accel': arr[:, 1:4],
        'gyro': arr[:, 4:7],
        'quat': arr[:, 7:11],  # wxyz
        'duration': t[-1],
        'fs_mean': len(t) / t[-1] if t[-1] > 0 else 0,
    }


# ─── YAW DESDE QUATERNION ────────────────────────────────────────────
def quaternion_to_yaw(quat):
    """Extrae yaw (rotación alrededor del eje Z global) desde quaternion wxyz."""
    qw, qx, qy, qz = quat[:,0], quat[:,1], quat[:,2], quat[:,3]
    yaw = np.arctan2(2*(qw*qz + qx*qy), 1 - 2*(qy**2 + qz**2))
    return np.unwrap(yaw)  # quita saltos de ±180°


# ─── DETECCIÓN DE PARADAS ────────────────────────────────────────────
def detect_stops(t, yaw_rate_deg_s, 
                 stop_threshold=STOP_THRESHOLD_DEG_S, 
                 min_duration=MIN_STOP_DURATION):
    """Detecta segmentos donde la pala está quieta. Devuelve lista de dicts."""
    is_low = np.abs(yaw_rate_deg_s) < stop_threshold
    stops = []
    i = 0
    n = len(is_low)
    while i < n:
        if is_low[i]:
            j = i
            while j < n and is_low[j]:
                j += 1
            duration = t[j-1] - t[i]
            if duration >= min_duration:
                if duration > LONG_STOP_THRESHOLD:
                    category = "dead_time"
                elif duration > MED_STOP_THRESHOLD:
                    category = "wait"
                else:
                    category = "operational"  # probablemente dig o dump
                stops.append({
                    'stop_id': len(stops) + 1,
                    't_start': float(t[i]),
                    't_end': float(t[j-1]),
                    'duration_s': float(duration),
                    'category': category,
                })
            i = j
        else:
            i += 1
    return stops


# ─── SEGMENTACIÓN DE CICLOS ──────────────────────────────────────────
def segment_cycles(t, yaw_deg, stops):
    """Un ciclo = segmento entre dos paradas operativas consecutivas (digs)."""
    op_stops = [s for s in stops if s['category'] == 'operational']
    cycles = []
    for i in range(len(op_stops) - 1):
        s1, s2 = op_stops[i], op_stops[i+1]
        # Yaw swept durante el ciclo
        mask = (t >= s1['t_end']) & (t <= s2['t_start'])
        if not mask.any():
            continue
        yaw_slice = yaw_deg[mask]
        cycles.append({
            'cycle_id': i + 1,
            't_start': s1['t_end'],
            't_end': s2['t_start'],
            'duration_s': s2['t_start'] - s1['t_end'],
            'yaw_sweep_deg': float(yaw_slice.max() - yaw_slice.min()),
            'dig_stop_id': s1['stop_id'],
        })
    return cycles


# ─── SUAVIDAD DEL OPERADOR (JERK) ────────────────────────────────────
def compute_smoothness(t, accel):
    """RMS del jerk = smoothness. Menor = más suave = mejor operador."""
    acc_mag = np.linalg.norm(accel, axis=1)
    # Jerk = derivada de aceleración
    jerk = np.gradient(acc_mag, t)
    return float(np.sqrt(np.mean(jerk**2)))


# ─── ENTRY POINT ─────────────────────────────────────────────────────
def analyze_imu(imu_path):
    """Análisis completo. Devuelve dict listo para serializar a JSON."""
    data = load_imu(imu_path)
    t = data['t']
    
    # Yaw
    yaw_rad = quaternion_to_yaw(data['quat'])
    yaw_deg = np.degrees(yaw_rad)
    yaw_smooth = savgol_filter(yaw_deg, 
                                window_length=min(31, len(yaw_deg)//2*2-1), 
                                polyorder=3)
    
    # Yaw rate (irregular sampling → usar np.gradient con t)
    yaw_rate = np.gradient(yaw_smooth, t)
    yaw_rate_smooth = savgol_filter(yaw_rate, 
                                     window_length=min(21, len(yaw_rate)//2*2-1), 
                                     polyorder=3)
    
    # Paradas
    stops = detect_stops(t, yaw_rate_smooth)
    
    # Ciclos
    cycles = segment_cycles(t, yaw_smooth, stops)
    
    # Métricas agregadas
    total = data['duration']
    stop_by_cat = {'dead_time': 0.0, 'wait': 0.0, 'operational': 0.0}
    for s in stops:
        stop_by_cat[s['category']] += s['duration_s']
    active_swing = total - sum(stop_by_cat.values())
    
    productive_pct = (active_swing + stop_by_cat['operational']) / total * 100
    
    # Suavidad
    smoothness = compute_smoothness(t, data['accel'])
    
    return {
        'summary': {
            'duration_s': float(total),
            'fs_mean_hz': float(data['fs_mean']),
            'n_stops_total': len(stops),
            'n_stops_dead': sum(1 for s in stops if s['category'] == 'dead_time'),
            'n_stops_wait': sum(1 for s in stops if s['category'] == 'wait'),
            'n_stops_operational': sum(1 for s in stops if s['category'] == 'operational'),
            'n_cycles_detected': len(cycles),
            'longest_stop_s': float(max((s['duration_s'] for s in stops), default=0)),
            'time_dead_s': stop_by_cat['dead_time'],
            'time_wait_s': stop_by_cat['wait'],
            'time_operational_stops_s': stop_by_cat['operational'],
            'time_active_swing_s': active_swing,
            'pct_productive_time': productive_pct,
            'pct_dead_time': stop_by_cat['dead_time'] / total * 100,
            'smoothness_rms_jerk': smoothness,
        },
        'stops': stops,
        'cycles': cycles,
    }


if __name__ == '__main__':
    import sys, json
    result = analyze_imu(sys.argv[1])
    print(json.dumps(result['summary'], indent=2))
