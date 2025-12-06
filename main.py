import os
import sys
import time
from datetime import datetime
from pathlib import Path
import argparse

import cv2
from ultralytics import YOLO
from ultralytics.utils import SETTINGS
from detection_frames import *

def parse_main_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--video",
        type=str,
        default=str(Path("videos") / "output2.mp4"),
        help="Ruta del vídeo a procesar",
    )
    p.add_argument(
        "--camera-id",
        type=str,
        default="camara_1",
        help="Identificador lógico de la cámara (se guarda en los JSON)",
    )
    # reusar algunos argumentos de detection_frames.parse_args si quieres
    p.add_argument("--weights", type=str, default=str(YOLO_DIR / "weights" / "yolo11n.pt"))
    p.add_argument("--conf", type=float, default=0.5)
    p.add_argument("--imgsz", type=int, default=960)
    p.add_argument("--skip", type=int, default=3, help="Run inference every N frames")
    p.add_argument("--display", action="store_true", default=True, help="Show window (press Q to quit)")
    p.add_argument("--reuse-last", action="store_true", default=True, help="Draw last detections on skipped frames")
    return p.parse_args()

def main():
    args = parse_main_args()

    video_path = Path(args.video)

    try:
        cap = open_capture(video_path)
    except Exception as e:
        print(e)
        sys.exit(1)

    # El writer y el nombre de salida se gestionan dentro de process_frames
    writer = None
    out_path = None
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps_in = cap.get(cv2.CAP_PROP_FPS) or 30.0

    model = init_model(args.weights)
    setup_display_if_needed(args.display, width, height)
    tracker = Tracker_predict()
    # tracker = TrackerHíbrido(...)

    # Pasamos camera_id al process_frames
    process_frames(cap, writer, model, args, width, height, fps_in, out_path, tracker, camera_id=args.camera_id)

if __name__ == "__main__":
    main()