import os
import json
import base64
from anthropic import Anthropic

def generate_placeholder_chart():
    # Retorna una imagen de 1x1 píxel transparente en base64 para que el dashboard no tire error de imagen rota
    return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

def main():
    print("--- Iniciando Insight Engine (Claude API) ---")
    
    output_file = "./outputs/metrics.json"
    
    # 1. Leer los datos preliminares que dejaron los otros pipelines
    if not os.path.exists(output_file):
        print(f"❌ Error: No se encontró {output_file}. ¿Corriste los pipelines anteriores?")
        return

    with open(output_file, "r") as f:
        metrics = json.load(f)

    # 2. Preparar los datos para Claude
    data_for_claude = {
        "duracion_total_segundos": metrics.get("metadata", {}).get("total_duration_seconds", 0),
        "tiempo_camion_roi_segundos": metrics.get("metadata", {}).get("truck_pipeline", {}).get("total_time_in_roi_seconds", 0),
        "total_ciclos": metrics.get("video_pipeline", {}).get("aggregated_metrics", {}).get("total_cycles", 0),
        "detalle_ciclos": metrics.get("video_pipeline", {}).get("cycles", [])
    }

    # 3. Configurar Anthropic y el Prompt
    # (Asegúrate de que la variable de entorno ANTHROPIC_API_KEY esté configurada en la laptop que corra esto)
    client = Anthropic() 
    
    system_prompt = """Actúas como un Ingeniero Senior de Confiabilidad y Productividad Minera. Analizas datos de una pala Hitachi EX-5600.
Tu objetivo es interpretar los datos JSON proporcionados y generar un reporte ejecutivo.
Reglas:
1. RMS Jerk > 0.60 = Movimiento brusco (fatiga).
2. fill_relative_percentage < 85% = Ineficiencia de carga.
Responde ÚNICAMENTE con un JSON válido con la siguiente estructura, sin formato markdown:
{
  "operational_flag": "operational" o "degraded" o "offline",
  "claude_summary": "Tu análisis y recomendación."
}"""

    try:
        print("Consultando a Claude 3.5 Sonnet...")
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022", # Modelo por defecto del hackathon
            max_tokens=300,
            temperature=0.2, # Baja temperatura para respuestas consistentes
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"Analiza estos datos y dame el JSON:\n{json.dumps(data_for_claude)}"}
            ]
        )
        
        # 4. Parsear la respuesta de Claude
        claude_response_text = response.content[0].text.strip()
        
        # Limpiar si Claude decide devolver bloques markdown a pesar de las instrucciones
        if claude_response_text.startswith("```json"):
            claude_response_text = claude_response_text[7:-3]
            
        claude_json = json.loads(claude_response_text)
        print("✅ Análisis de Claude generado con éxito.")
        
    except Exception as e:
        print(f"⚠️ Error al consultar la API de Claude: {e}")
        print("Generando análisis de respaldo (Fallback)...")
        claude_json = {
            "operational_flag": "degraded",
            "claude_summary": "Error de conexión con IA. Se detectaron ciclos en la sesión, pero se requiere revisión manual de los parámetros de suavidad y llenado."
        }

    # 5. Guardar los resultados finales en el métricas.json
    metrics["insight_engine"] = claude_json
    
    # 6. Añadir los gráficos (Si tu equipo no hizo gráficos reales, inyectamos placeholders)
    metrics["charts"] = {
        "imu_timeseries": generate_placeholder_chart(),
        "depth_disparity": generate_placeholder_chart()
    }

    with open(output_file, "w") as f:
        json.dump(metrics, f, indent=4)
        
    print("✅ metrics.json finalizado y guardado en ./outputs/")

if __name__ == "__main__":
    main()
