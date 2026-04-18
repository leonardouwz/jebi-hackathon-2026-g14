import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

with open('./outputs/motion_debug.json') as f:
    debug = json.load(f)

times = [d['t'] for d in debug]

# Soporta tanto formato IMU (signal) como video (presence_raw / presence_smooth)
if 'signal' in debug[0]:
    raw    = [d['signal'] for d in debug]
    smooth = raw  # ya viene suavizado desde el pipeline
    ylabel = 'Actividad (dQ cuaternión)'
    source = 'IMU'
else:
    raw    = [d['presence_raw']    for d in debug]
    smooth = [d['presence_smooth'] for d in debug]
    ylabel = 'Presencia (% píxeles)'
    source = 'Video MOG2'

with open('./outputs/truck_events.json') as f:
    events = json.load(f)

fig, ax = plt.subplots(figsize=(14, 4))
ax.plot(times, raw,    color='lightgray', alpha=0.7, linewidth=1, label='señal cruda')
ax.plot(times, smooth, color='steelblue', linewidth=2, label='suavizada')

for e in events:
    ax.axvspan(e['t_arrival'], e['t_departure'], alpha=0.25, color='green')

# Leyenda manual para los intercambios
patch = mpatches.Patch(color='green', alpha=0.4, label=f'Intercambio ({len(events)} detectados)')
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles=handles + [patch])

ax.set_title(f'Detección de intercambios de camión — fuente: {source}')
ax.set_xlabel('Tiempo (s)')
ax.set_ylabel(ylabel)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('./outputs/truck_signal_viz.png', dpi=100)
plt.close()
print("✓ Guardado: ./outputs/truck_signal_viz.png")
