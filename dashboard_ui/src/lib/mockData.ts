export interface Cycle {
  cycle_id: string;
  duration_seconds: number;
  fill_relative_percentage: number;
  smoothness_rms_jerk: number;
}

export interface AnalysisData {
  // Ahora metadata envuelve estos campos
  metadata: {
    file_id: string;
    total_duration_seconds: number;
    truck_pipeline: {
      total_time_in_roi_seconds: number;
    };
  };
  video_pipeline: {
    aggregated_metrics: {
      total_cycles: number;
    };
    cycles: Cycle[];
  };
  insight_engine: {
    operational_flag: "operational" | "degraded" | "offline";
    claude_summary: string; // Cambiado para coincidir con tu JSON
  };
  charts: {
    imu_timeseries: string;
    depth_disparity: string;
  };
}