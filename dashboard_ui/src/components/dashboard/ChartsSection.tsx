import { LineChart, BarChart3 } from "lucide-react";

interface Props {
  imuTimeseries: string;
  depthDisparity: string;
}

function ChartCard({
  title,
  subtitle,
  src,
  Icon,
}: {
  title: string;
  subtitle: string;
  src: string;
  Icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div className="rounded-xl border bg-card overflow-hidden">
      <div className="px-5 py-4 border-b flex items-center gap-2">
        <div className="size-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
          <Icon className="size-4" />
        </div>
        <div>
          <h3 className="text-sm font-semibold">{title}</h3>
          <p className="text-xs uppercase tracking-wider text-muted-foreground">{subtitle}</p>
        </div>
      </div>
      <div className="p-4">
        <img
          src={src}
          alt={title}
          className="w-full h-auto rounded-lg"
          loading="lazy"
        />
      </div>
    </div>
  );
}

export function ChartsSection({ imuTimeseries, depthDisparity }: Props) {
  return (
    <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <ChartCard
        title="IMU Timeseries"
        subtitle="Aceleración / giroscopio"
        src={imuTimeseries}
        Icon={LineChart}
      />
      <ChartCard
        title="Depth Disparity"
        subtitle="Profundidad relativa"
        src={depthDisparity}
        Icon={BarChart3}
      />
    </section>
  );
}
