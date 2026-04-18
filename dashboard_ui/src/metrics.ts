// src/metrics.ts
export const metricsData = {
  "metadata": {
    "file_id": "imu_session_2024_03_14_A07",
    "total_duration_seconds": 1842,
    "truck_pipeline": {
      "total_time_in_roi_seconds": 1124.6
    }
  }, // <--- ESTA ES LA LLAVE QUE TE FALTABA (Cierra metadata)

  "video_pipeline": {
    "aggregated_metrics": {
      "total_cycles": 14
    },
    "cycles": [
      { "cycle_id": "C-001", "duration_seconds": 78.4, "fill_relative_percentage": 92.3, "smoothness_rms_jerk": 0.42 },
      { "cycle_id": "C-002", "duration_seconds": 81.1, "fill_relative_percentage": 88.7, "smoothness_rms_jerk": 0.51 },
      { "cycle_id": "C-003", "duration_seconds": 74.2, "fill_relative_percentage": 95.1, "smoothness_rms_jerk": 0.38 },
      { "cycle_id": "C-004", "duration_seconds": 85.6, "fill_relative_percentage": 79.4, "smoothness_rms_jerk": 0.67 },
      { "cycle_id": "C-005", "duration_seconds": 72.9, "fill_relative_percentage": 91.0, "smoothness_rms_jerk": 0.44 },
      { "cycle_id": "C-006", "duration_seconds": 79.8, "fill_relative_percentage": 86.5, "smoothness_rms_jerk": 0.49 },
      { "cycle_id": "C-007", "duration_seconds": 83.4, "fill_relative_percentage": 82.1, "smoothness_rms_jerk": 0.58 },
      { "cycle_id": "C-008", "duration_seconds": 76.7, "fill_relative_percentage": 93.8, "smoothness_rms_jerk": 0.41 },
      { "cycle_id": "C-009", "duration_seconds": 80.2, "fill_relative_percentage": 87.9, "smoothness_rms_jerk": 0.53 },
      { "cycle_id": "C-010", "duration_seconds": 77.5, "fill_relative_percentage": 90.2, "smoothness_rms_jerk": 0.46 },
      { "cycle_id": "C-011", "duration_seconds": 82.8, "fill_relative_percentage": 84.6, "smoothness_rms_jerk": 0.55 },
      { "cycle_id": "C-012", "duration_seconds": 75.1, "fill_relative_percentage": 94.4, "smoothness_rms_jerk": 0.39 },
      { "cycle_id": "C-013", "duration_seconds": 79.0, "fill_relative_percentage": 89.3, "smoothness_rms_jerk": 0.47 },
      { "cycle_id": "C-014", "duration_seconds": 81.7, "fill_relative_percentage": 85.8, "smoothness_rms_jerk": 0.52 }
    ]
  },
  "insight_engine": {
    "operational_flag": "operational",
    "claude_summary": "La sesión muestra un comportamiento operativo estable con 14 ciclos completos detectados..."
  },
  "charts": {
    "imu_timeseries": "",
    "depth_disparity": ""
  }
}; // Cierra el objeto principal