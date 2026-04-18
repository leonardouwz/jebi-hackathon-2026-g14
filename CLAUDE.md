# Contexto: Hackathon JEBI 2026 — Mining Productivity

## Quién soy
Somos un equipo de 3 en la Hackathon JEBI 2026. Estás ayudándonos a construir
una solución que cuantifique e incremente la productividad de una pala frontal
Hitachi EX-5600 cargando camiones CAT 793F y EH4000 AC-3 en minería a tajo
abierto. Tenemos 15 minutos de datos reales: video estéreo (shovel_left.mp4,
shovel_right.mp4) + IMU (imu_data.csv).

## Restricciones duras (no negociables)
- Tenemos 6 horas de coding total. Ya transcurrió [X] horas.
- El `run.sh` debe:
  - leer de ./inputs/, escribir a ./outputs/
  - ejecutarse en < 10 min en laptop estándar
  - funcionar en un dataset de testeo NO VISTO (misma operación, otra ventana)
  - no tener paths absolutos, API keys hardcodeadas, ni duración fija
- Modelo default: Sonnet 4.6. No sugieras usar Opus salvo para razonamiento
  excepcionalmente difícil.
- NO pre-descargar modelos pesados (YOLO, Detectron2, etc.). OpenCV clásico
  + scipy + numpy + pandas. Si algo requiere > 500 MB de descarga, no va.

## Hipótesis central del equipo
Definimos productividad como: toneladas cargadas por hora, descompuesta en
(ciclos/hora) × (fill factor) × (capacidad nominal bucket = 68 t).
Las 4 métricas que salen del pipeline son:
  1. Tiempo de ciclo (IMU → segmentación por picos de accel + gyro)
  2. Bucket fill factor (video estéreo → disparidad → volumen)
  3. Tiempo muerto por intercambio de camión (video → MOG2 background sub)
  4. Suavidad del operador (IMU → RMS del jerk)

El insight que buscamos: correlación negativa entre ciclo rápido y fill factor
(si se confirma, los operadores se apuran sacrificando toneladas reales).

## Stack
Python 3.11+, OpenCV 4.x, numpy, scipy, pandas, matplotlib. 
Para el reporte: HTML estático con gráficos embebidos en base64. 
Para recomendaciones: anthropic SDK con Sonnet 4.6.

## Contrato de archivos en outputs/
- metrics.json  → KPIs agregados
- cycles.json   → un registro por ciclo detectado
- report.html   → dashboard standalone
- summary.md    → narrativa con recomendación accionable

## Cómo quiero que me ayudes
- Respuestas cortas y ejecutables. No expliques conceptos básicos.
- Siempre dime qué archivo editar y qué función toca.
- Si propones una librería nueva, justifícalo en < 2 líneas y da el comando exacto de instalación.
- Antes de generar código largo, pregunta si ya existe una función equivalente en el repo.
- Cuando el código esté listo, dame el comando exacto para probarlo.
- Si detectas que estoy sobre-ingenierizando, dímelo en la primera frase.
- Si detectas que estoy haciendo algo que no corre en el dataset de testeo (hardcoding, paths absolutos, duración fija), detente y adviérteme.

## Cómo NO quiero que me ayudes
- No me pidas "más contexto" si no es estrictamente necesario — mira el repo primero.
- No sugieras reescribir lo que ya funciona.
- No uses Opus salvo si yo lo pido explícitamente.
- No proceses datos crudos (video/CSV) en el contexto de la conversación — eso lo hace el código.

## Prioridades cuando haya que cortar features
1. run.sh corre sin error sobre los inputs dados → INDISPENSABLE
2. metrics.json con las 4 métricas → INDISPENSABLE
3. summary.md con recomendación anclada en datos → INDISPENSABLE
4. report.html con gráficos → ALTA
5. video anotado con bucket ROI → MEDIA
6. insight de correlación fill-vs-ciclo → ALTA (es nuestro diferenciador)
7. detección de camión con MOG2 → MEDIA
8. todo lo demás → BAJA