import { Truck, Repeat, CircleCheck, CircleAlert, CircleX } from "lucide-react";
import type { AnalysisData } from "@/lib/mockData";
import { cn } from "@/lib/utils";

interface Props {
  data: AnalysisData;
}

const STATUS_MAP = {
  operational: { label: "Operacional", color: "text-success", bg: "bg-success/10", Icon: CircleCheck },
  degraded: { label: "Degradado", color: "text-warning", bg: "bg-warning/10", Icon: CircleAlert },
  offline: { label: "Offline", color: "text-destructive", bg: "bg-destructive/10", Icon: CircleX },
} as const;

function Card({
  label,
  value,
  sub,
  Icon,
  iconClass,
}: {
  label: string;
  value: string;
  sub?: string;
  Icon: React.ComponentType<{ className?: string }>;
  iconClass: string;
}) {
  return (
    <div className="group rounded-xl border bg-card p-5 transition-all duration-200 hover:border-primary/40 hover:shadow-[0_0_0_1px_rgba(59,130,246,0.15)]">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-wider text-muted-foreground">{label}</p>
        <div className={cn("size-9 rounded-lg flex items-center justify-center", iconClass)}>
          <Icon className="size-4" />
        </div>
      </div>
      <p className="mt-4 text-2xl font-semibold tracking-tight">{value}</p>
      {sub && <p className="mt-1 text-xs text-muted-foreground">{sub}</p>}
    </div>
  );
}

export function SummaryCards({ data }: Props) {
  // 1. Aseguramos el status (este estaba bien)
  const status = STATUS_MAP[data.insight_engine.operational_flag];

  // 2. ¡AQUÍ ESTÁ LA CORRECCIÓN! Añadimos .metadata antes de truck_pipeline y total_duration
  const roi = data.metadata.truck_pipeline.total_time_in_roi_seconds;
  const roiPct = ((roi / data.metadata.total_duration_seconds) * 100).toFixed(1);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Card
        label="Tiempo en ROI"
        value={`${roi.toFixed(1)}s`}
        sub={`${roiPct}% de duración total`}
        Icon={Truck}
        iconClass="bg-primary/10 text-primary"
      />
      <Card
        label="Total ciclos"
        value={String(data.video_pipeline.aggregated_metrics.total_cycles)}
        sub="Ciclos detectados"
        Icon={Repeat}
        iconClass="bg-blue-500/15 text-blue-500" // Ajuste genérico de Tailwind si no tienes "chart-5"
      />
      <Card
        label="Estado operativo"
        value={status.label}
        sub="Insight engine"
        Icon={status.Icon}
        iconClass={cn(status.bg, status.color)}
      />
    </div>
  );
}