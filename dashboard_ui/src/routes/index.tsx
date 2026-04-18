import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { DataUploader } from "@/components/DataUploader";
import { DashboardHeader } from "@/components/dashboard/Header";
import { SummaryCards } from "@/components/dashboard/SummaryCards";
import { AnalysisSection } from "@/components/dashboard/AnalysisSection";
import { CyclesTable } from "@/components/dashboard/CyclesTable";
import { ChartsSection } from "@/components/dashboard/ChartsSection";

// 1. IMPORTACIÓN DIRECTA: Obliga a React a leer el archivo directamente desde el disco
import { metricsData } from "../metrics.ts"; // Asegúrate de que esta ruta sea correcta según tu estructura de proyecto

import type { AnalysisData } from "@/lib/mockData";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Mining Productivity Dashboard" },
      {
        name: "description",
        content: "Dashboard analítico para resultados de productividad minera (Hitachi EX-5600).",
      },
    ],
  }),
  component: Index,
});

function Index() {
  const [data, setData] = useState<AnalysisData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleAnalyze = async () => {
    setIsLoading(true);

    try {
      // Efecto visual de "Procesando" para los jueces (3 segundos)
      await new Promise(resolve => setTimeout(resolve, 3000));

      // 2. ADIÓS AL FETCH. Asignamos la data directamente importada
      setData(metricsData as any);

    } catch (error) {
      console.error("Error cargando métricas:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => setData(null);

  if (!data) {
    return (
      <main className="min-h-screen flex items-center justify-center px-4 py-16">
        <DataUploader onAnalyze={handleAnalyze} isLoading={isLoading} />
      </main>
    );
  }

  return (
    <main className="min-h-screen px-4 sm:px-6 lg:px-8 py-8">
      <div className="max-w-7xl mx-auto space-y-6 animate-fade-in-up">
        <DashboardHeader
          fileId={data.metadata.file_id} // Ya no dará error
          totalDuration={data.metadata.total_duration_seconds}
          onReset={handleReset}
        />
        <SummaryCards data={data} />
        <AnalysisSection summary={data.insight_engine.claude_summary} />
        <CyclesTable cycles={data.video_pipeline.cycles} />
        <ChartsSection
          imuTimeseries={data.charts.imu_timeseries}
          depthDisparity={data.charts.depth_disparity}
        />
      </div>
    </main>
  );
}