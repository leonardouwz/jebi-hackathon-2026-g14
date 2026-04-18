# Resumen de Productividad — Hitachi EX-5600
**Estado: DEGRADED**

## Diagnóstico
Productividad estimada: 2902 t/h (113.6 ciclos/h × 38% fill × 68 t). Tiempo muerto por intercambio: 14.3s (3 intercambios). Recomendaciones: (1) Reducir tiempo muerto coordinando posición del camión vacío. (2) Monitorear ciclos rápidos vs fill factor — velocidad puede sacrificar tonelaje. (3) Revisar suavidad del operador para reducir desgaste del equipo.

## KPIs
| Métrica | Valor |
|---------|-------|
| Productividad | **2902 t/h** |
| Ciclo promedio | 31.7s |
| Ciclos/hora | 113.6 |
| Fill factor | 38% |
| Tiempo muerto/intercambio | 14.3s (3 intercambios) |
| RMS Jerk | 25.4844 |
| % tiempo productivo | 18.3% |
# Resumen

{
  "imu_summary": {
    "duration_s": 899.87083904,
    "fs_mean_hz": 10.44927737633026,
    "n_stops_total": 28,
    "n_stops_dead": 7,
    "n_stops_wait": 9,
    "n_stops_operational": 12,
    "n_cycles_detected": 11,
    "longest_stop_s": 205.40087603199999,
    "time_dead_s": 603.669262848,
    "time_wait_s": 131.53368627199984,
    "time_operational_stops_s": 52.06724121599998,
    "time_active_swing_s": 112.60064870400015,
    "pct_productive_time": 18.299058351048593,
    "pct_dead_time": 67.0839899081524,
    "smoothness_rms_jerk": 25.484443634707862
  },
  "truck_events": {
    "status": "not_implemented"
  }
}
