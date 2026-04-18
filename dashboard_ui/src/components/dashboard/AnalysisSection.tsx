import { Sparkles } from "lucide-react";

interface Props {
  summary: string;
}

export function AnalysisSection({ summary }: Props) {
  return (
    <section className="rounded-xl border bg-card p-6">
      <div className="flex items-center gap-2 mb-4">
        <div className="size-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
          <Sparkles className="size-4" />
        </div>
        <div>
          <h2 className="text-base font-semibold">Análisis Claude</h2>
          <p className="text-xs uppercase tracking-wider text-muted-foreground">
            Insight engine summary
          </p>
        </div>
      </div>
      <p className="max-w-3xl text-sm leading-relaxed text-foreground/90">{summary}</p>
    </section>
  );
}
