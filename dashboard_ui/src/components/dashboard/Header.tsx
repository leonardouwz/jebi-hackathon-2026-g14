import { Activity, RotateCcw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  fileId: string;
  totalDuration: number;
  onReset: () => void;
}

function formatDuration(s: number) {
  const m = Math.floor(s / 60);
  const sec = Math.round(s % 60);
  return `${m}m ${sec}s`;
}

export function DashboardHeader({ fileId, totalDuration, onReset }: HeaderProps) {
  return (
    <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b">
      <div className="flex items-center gap-3">
        <div className="size-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
          <Activity className="size-5" />
        </div>
        <div>
          <p className="text-xs uppercase tracking-wider text-muted-foreground">File ID</p>
          <h1 className="text-lg font-semibold font-mono">{fileId}</h1>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <Badge variant="secondary" className="text-xs px-3 py-1.5">
          Duración: {formatDuration(totalDuration)}
        </Badge>
        <Button variant="outline" size="sm" onClick={onReset}>
          <RotateCcw className="size-3.5" />
          Cargar nuevo archivo
        </Button>
      </div>
    </header>
  );
}
