"""Entry point: orquesta todas las etapas y escribe a ./outputs/."""
import argparse
import json
import os
import traceback
from pathlib import Path

def safe_run(fn, name, *args, **kwargs):
    """Ejecuta una etapa capturando errores sin romper el pipeline."""
    print(f"[{name}] iniciando...")
    try:
        result = fn(*args, **kwargs)
        print(f"[{name}] ✓ OK")
        return result
    except Exception as e:
        print(f"[{name}] ✗ FALLÓ: {e}")
        traceback.print_exc()
        return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--left', required=True)
    p.add_argument('--right', required=True)
    p.add_argument('--imu', required=True)
    p.add_argument('--outputs', default='./outputs')
    args = p.parse_args()
    
    out = Path(args.outputs)
    out.mkdir(exist_ok=True)
    
    # ─ Etapa 1: IMU (crítico) ──────────────────────
    from solution.imu_pipeline import analyze_imu
    imu_result = safe_run(analyze_imu, 'IMU', args.imu)
    if imu_result is None:
        print("CRÍTICO: IMU falló. No se puede continuar.")
        return 1
    
    with open(out / 'cycles.json', 'w') as f:
        json.dump(imu_result['cycles'], f, indent=2)
    with open(out / 'stops.json', 'w') as f:
        json.dump(imu_result['stops'], f, indent=2)
    
    # ─ Etapa 2: Truck detection (opcional) ─────────
    truck_result = None
    try:
        from solution.truck_pipeline import detect_truck_events
        truck_result = safe_run(detect_truck_events, 'TRUCKS', args.left)
    except ImportError:
        print("[TRUCKS] pipeline no disponible, skipping")
    
    # ─ Etapa 3: Métricas agregadas ─────────────────
    metrics = {
        'imu_summary': imu_result['summary'],
        'truck_events': truck_result if truck_result else {'status': 'not_computed'},
    }
    with open(out / 'metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # ─ Etapa 4: Insight con Claude ─────────────────
    try:
        from solution.insight_engine import generate_summary
        if os.environ.get('ANTHROPIC_API_KEY'):
            safe_run(generate_summary, 'INSIGHT', str(out / 'metrics.json'), str(out / 'summary.md'))
        else:
            print("[INSIGHT] ANTHROPIC_API_KEY no set — generando fallback")
            with open(out / 'summary.md', 'w') as f:
                f.write(f"# Resumen\n\n{json.dumps(metrics, indent=2)}")
    except Exception as e:
        print(f"[INSIGHT] fallback: {e}")
    
    # ─ Etapa 5: Reporte HTML ───────────────────────
    try:
        from solution.report_generator import build_report
        safe_run(build_report, 'REPORT', str(out / 'metrics.json'), str(out / 'summary.md'), str(out / 'report.html'))
    except ImportError:
        print("[REPORT] no disponible")
    
    print("\n✓ Pipeline completo. Outputs en:", out)
    return 0


if __name__ == '__main__':
    exit(main())
