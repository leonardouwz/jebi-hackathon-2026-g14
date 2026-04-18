import { useMemo, useState } from "react";
import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Cycle } from "@/lib/mockData";
import { cn } from "@/lib/utils";

interface Props {
  cycles: Cycle[];
}

type SortKey = keyof Cycle;
type SortDir = "asc" | "desc";

const COLUMNS: { key: SortKey; label: string; align?: "right" }[] = [
  { key: "cycle_id", label: "Cycle ID" },
  { key: "duration_seconds", label: "Duración (s)", align: "right" },
  { key: "fill_relative_percentage", label: "Fill %", align: "right" },
  { key: "smoothness_rms_jerk", label: "Smoothness (RMS jerk)", align: "right" },
];

export function CyclesTable({ cycles }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("cycle_id");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const sorted = useMemo(() => {
    const arr = [...cycles];
    arr.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === "number" && typeof bv === "number") {
        return sortDir === "asc" ? av - bv : bv - av;
      }
      return sortDir === "asc"
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av));
    });
    return arr;
  }, [cycles, sortKey, sortDir]);

  const toggle = (key: SortKey) => {
    if (key === sortKey) setSortDir(sortDir === "asc" ? "desc" : "asc");
    else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  return (
    <section className="rounded-xl border bg-card overflow-hidden">
      <div className="px-6 py-4 border-b">
        <h2 className="text-base font-semibold">Ciclos detectados</h2>
        <p className="text-xs uppercase tracking-wider text-muted-foreground mt-0.5">
          {cycles.length} registros
        </p>
      </div>
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            {COLUMNS.map((c) => {
              const active = sortKey === c.key;
              const Icon = active ? (sortDir === "asc" ? ArrowUp : ArrowDown) : ArrowUpDown;
              return (
                <TableHead key={c.key} className={cn("px-6", c.align === "right" && "text-right")}>
                  <button
                    onClick={() => toggle(c.key)}
                    className={cn(
                      "inline-flex items-center gap-1.5 text-xs uppercase tracking-wider hover:text-foreground transition-colors",
                      active ? "text-foreground" : "text-muted-foreground",
                      c.align === "right" && "flex-row-reverse",
                    )}
                  >
                    {c.label}
                    <Icon className="size-3" />
                  </button>
                </TableHead>
              );
            })}
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.map((cycle) => (
            <TableRow key={cycle.cycle_id}>
              <TableCell className="px-6 font-mono text-sm">{cycle.cycle_id}</TableCell>
              <TableCell className="px-6 text-right tabular-nums">
                {cycle.duration_seconds.toFixed(1)}
              </TableCell>
              <TableCell className="px-6 text-right tabular-nums">
                <span
                  className={cn(
                    cycle.fill_relative_percentage >= 90
                      ? "text-success"
                      : cycle.fill_relative_percentage >= 80
                        ? "text-foreground"
                        : "text-warning",
                  )}
                >
                  {cycle.fill_relative_percentage.toFixed(1)}%
                </span>
              </TableCell>
              <TableCell className="px-6 text-right tabular-nums">
                {cycle.smoothness_rms_jerk.toFixed(2)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </section>
  );
}
