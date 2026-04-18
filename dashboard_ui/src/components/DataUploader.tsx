import { useCallback, useRef, useState } from "react";
import { Upload, FileText, Film, X, Loader2, Play, AlertCircle } from "lucide-react";
// Ajusta estas rutas según cómo Lovable estructuró tu proyecto
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface DataUploaderProps {
  onAnalyze: () => void;
  isLoading: boolean;
}

const REQUIRED_PATTERNS = {
  imu: "Archivo IMU (*imu*.csv)",
  shovel_left: "Video izquierdo (*left*.mp4)",
  shovel_right: "Video derecho (*right*.mp4)",
} as const;

const REQUIRED_NAMES = Object.values(REQUIRED_PATTERNS);
type FileKind = "imu" | "shovel_left" | "shovel_right";
interface StagedFile {
  id: string;
  file: File;
  kind: FileKind;
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function classify(file: File): FileKind | null {
  const name = file.name.toLowerCase();

  // 1. Ahora acepta CSV o NPY siempre que contenga "imu"
  if ((name.endsWith('.csv') || name.endsWith('.npy')) && name.includes('imu')) {
    return "imu";
  }

  // 2. Videos MP4 (Izquierdo)
  if (name.endsWith('.mp4') && (name.includes('left') || name.includes('izq'))) {
    return "shovel_left";
  }

  // 3. Videos MP4 (Derecho)
  if (name.endsWith('.mp4') && (name.includes('right') || name.includes('der'))) {
    return "shovel_right";
  }

  return null;
}

const KIND_LABEL: Record<FileKind, string> = {
  imu: "Datos IMU",
  shovel_left: "Cámara izquierda",
  shovel_right: "Cámara derecha",
};

export function DataUploader({ onAnalyze, isLoading }: DataUploaderProps) {
  const [staged, setStaged] = useState<StagedFile[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const accepted: StagedFile[] = [];
    const rejected: string[] = [];

    Array.from(files).forEach((f) => {
      const kind = classify(f);
      if (!kind) {
        rejected.push(f.name);
        return;
      }
      accepted.push({
        id: `${f.name}-${f.size}-${f.lastModified}-${Math.random().toString(36).slice(2, 7)}`,
        file: f,
        kind,
      });
    });

    if (rejected.length > 0) {
      setError(
        `Archivo no reconocido (${rejected.join(", ")}). Solo se aceptan: ${REQUIRED_NAMES.join(", ")}`
      );
    } else {
      setError(null);
    }

    if (accepted.length > 0) {
      setStaged((prev) => {
        const existing = new Set(prev.map((s) => `${s.file.name}-${s.file.size}`));
        const next = accepted.filter((a) => !existing.has(`${a.file.name}-${a.file.size}`));
        return [...prev, ...next];
      });
    }
  };

  const removeFile = (id: string) => {
    setStaged((prev) => prev.filter((s) => s.id !== id));
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    handleFiles(e.dataTransfer.files);
  }, []);

  // Lógica estricta de validación para habilitar el botón
  const hasImu = staged.some((s) => s.kind === "imu");
  const hasLeft = staged.some((s) => s.kind === "shovel_left");
  const hasRight = staged.some((s) => s.kind === "shovel_right");
  const canAnalyze = hasImu && hasLeft && hasRight && !isLoading;

  return (
    <div className="w-full max-w-2xl mx-auto animate-fade-in-up">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-primary">Mining Productivity 2.0</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Sube los datos de la Hitachi EX-5600 para generar el reporte de productividad
        </p>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "rounded-2xl border-2 border-dashed p-10 text-center cursor-pointer transition-all duration-200",
          dragActive
            ? "border-primary bg-primary/5 shadow-[0_0_0_4px_rgba(59,130,246,0.15)]"
            : "border-border hover:border-primary/50 hover:bg-card/40"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.mp4,.npy"
          multiple
          className="hidden"
          onChange={(e) => {
            handleFiles(e.target.files);
            if (inputRef.current) inputRef.current.value = "";
          }}
        />
        <div className="flex flex-col items-center gap-4">
          <div
            className={cn(
              "size-16 rounded-2xl flex items-center justify-center transition-colors",
              dragActive ? "bg-primary text-primary-foreground" : "bg-card text-primary"
            )}
          >
            <Upload className="size-7" />
          </div>
          <div>
            <p className="text-base font-medium">
              Arrastra tus datos de sensores (.csv o .npy) y los videos estéreo (.mp4) aquí
            </p>
            <p className="mt-2 text-xs uppercase tracking-wider text-muted-foreground">
              Se requiere: 1 archivo IMU, 1 cámara Izquierda, 1 cámara Derecha
            </p>
          </div>
        </div>
      </div>

      {/* Lista de archivos subidos */}
      {staged.length > 0 && (
        <ul className="mt-4 space-y-2">
          {staged.map((s) => {
            const isVideo = s.kind !== "imu";
            const Icon = isVideo ? Film : FileText;
            return (
              <li
                key={s.id}
                className="rounded-xl border bg-card p-3 flex items-center gap-3 animate-fade-in-up"
              >
                <div
                  className={cn(
                    "size-10 rounded-lg flex items-center justify-center shrink-0",
                    isVideo ? "bg-green-500/10 text-green-600" : "bg-blue-500/10 text-blue-600"
                  )}
                >
                  <Icon className="size-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate text-sm">{s.file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {KIND_LABEL[s.kind]} · {formatSize(s.file.size)}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(s.id);
                  }}
                  disabled={isLoading}
                  className="size-8 rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-accent transition-colors disabled:opacity-50"
                >
                  <X className="size-4" />
                </button>
              </li>
            );
          })}
        </ul>
      )}

      {/* Mensajes de error y validación */}
      {error && (
        <div className="mt-4 flex items-center gap-2 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-600">
          <AlertCircle className="size-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {staged.length > 0 && !canAnalyze && !isLoading && (
        <p className="mt-3 text-xs font-semibold text-orange-500 text-center">
          Faltan archivos para procesar:{" "}
          {[
            !hasImu && "imu_data.csv",
            !hasLeft && "shovel_left.mp4",
            !hasRight && "shovel_right.mp4",
          ]
            .filter(Boolean)
            .join(", ")}
        </p>
      )}

      {/* Botón de Acción Principal */}
      <div className="mt-6 flex justify-end">
        <Button size="lg" onClick={onAnalyze} disabled={!canAnalyze} className="min-w-44 bg-primary hover:bg-primary/90 text-primary-foreground">
          {isLoading ? (
            <>
              <Loader2 className="mr-2 size-4 animate-spin" />
              Procesando Pipelines...
            </>
          ) : (
            <>
              <Play className="mr-2 size-4" />
              Ejecutar Análisis
            </>
          )}
        </Button>
      </div>
    </div>
  );
}