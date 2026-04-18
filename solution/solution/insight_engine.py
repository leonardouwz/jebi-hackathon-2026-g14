"""Genera narrativa e insight con Claude API desde las métricas calculadas."""
import os
import json
from anthropic import Anthropic

PROMPT_TEMPLATE = """Eres un analista senior de productividad minera. Acabamos de analizar 
15 minutos de operación de una pala frontal Hitachi EX-5600 cargando camiones CAT 793F 
y EH4000 AC-3 en una mina a tajo abierto.

Aquí están los KPIs reales extraídos del IMU (sensor inercial con quaternion):

{metrics_json}

Escribe un reporte en español con EXACTAMENTE esta estructura:

## Hallazgo principal
[1 frase identificando el mayor cuello de botella, con número concreto del JSON]

## Evidencia cuantificada
- [3 bullets con números específicos del JSON]

## Recomendación accionable
[1 acción concreta para el operador o jefe de guardia. NO inventes soluciones genéricas.
Ánclala en los números del JSON.]

## Impacto estimado
[Cálculo simple: si X se reduce de A a B, la productividad sube de P a Q t/h. 
Asume bucket nominal = 68 toneladas, fill factor = 0.9, precio de material = USD 40/t.
Muestra el cálculo paso a paso en 2-3 líneas.]

## Próximos pasos (si tuviéramos 6h más)
[2-3 bullets de qué construiríamos]

Reglas:
- NO inventes números que no estén en el JSON.
- NO uses disclaimers ("sujeto a validación", "aproximadamente").
- Si los datos son insuficientes para una sección, di "Datos insuficientes" en lugar de rellenar.
- Tono profesional pero directo. Sin preámbulo ni cierre.
"""

def generate_summary(metrics_path, output_path):
    client = Anthropic()  # usa ANTHROPIC_API_KEY del entorno
    with open(metrics_path) as f:
        metrics = json.load(f)
    
    prompt = PROMPT_TEMPLATE.format(metrics_json=json.dumps(metrics, indent=2))
    
    msg = client.messages.create(
        model="claude-sonnet-4-5-20250929",  # Sonnet 4.6 / ajustar al nombre exacto del API key del evento
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    
    summary = msg.content[0].text
    with open(output_path, 'w') as f:
        f.write(summary)
    return summary


if __name__ == '__main__':
    import sys
    print(generate_summary(sys.argv[1], sys.argv[2]))
