import cv2
import json
import os
import glob
import sys

ROI_X, ROI_Y, ROI_W, ROI_H = 0, 182, 725, 226


def generate_annotated_video(video_path, events, output_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        t_sec = frame_idx / fps

        # Dibujar ROI
        cv2.rectangle(frame, (ROI_X, ROI_Y),
                      (ROI_X + ROI_W, ROI_Y + ROI_H),
                      (0, 255, 0), 2)

        # Estado actual
        in_event = any(e['t_arrival'] <= t_sec <= e['t_departure']
                       for e in events)
        status = "INTERCAMBIO" if in_event else "cargando..."
        color = (0, 165, 255) if in_event else (0, 255, 0)

        cv2.putText(frame, f"t={t_sec:.1f}s  {status}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        out.write(frame)
        frame_idx += 1

    cap.release()
    out.release()
    print(f"✓ Video guardado: {output_path}")


if __name__ == '__main__':
    video_path = sys.argv[1] if len(sys.argv) > 1 else (
        next(iter(glob.glob('./inputs/*left*.mp4') or glob.glob('./inputs/*.mp4')), None))
    if not video_path:
        print("ERROR: no se encontró video en ./inputs/"); sys.exit(1)

    with open('./outputs/truck_events.json') as f:
        events = json.load(f)

    os.makedirs('./outputs', exist_ok=True)
    generate_annotated_video(video_path, events, './outputs/annotated_video.mp4')
