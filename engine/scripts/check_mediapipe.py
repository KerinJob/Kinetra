"""Comprueba que MediaPipe carga el modelo real en CPU y ejecuta inferencia.

Usa una imagen sintética en blanco: se espera 0 poses. No mide nada clínico;
solo verifica compatibilidad SO/Python/MediaPipe/modelo.
"""
import platform, sys
from pathlib import Path
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mpp
from mediapipe.tasks.python import vision

model = Path(__file__).resolve().parent.parent / "models" / "pose_landmarker_full.task"
opts = vision.PoseLandmarkerOptions(
    base_options=mpp.BaseOptions(model_asset_path=str(model), delegate=mpp.BaseOptions.Delegate.CPU),
    running_mode=vision.RunningMode.VIDEO, num_poses=2)
with vision.PoseLandmarker.create_from_options(opts) as lm:
    img = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.full((480, 640, 3), 255, np.uint8))
    poses = [len(lm.detect_for_video(img, t).pose_landmarks) for t in (0, 33, 66)]
print(f"OK python={sys.version.split()[0]} os={platform.platform()} mediapipe={mp.__version__} "
      f"model={model.name} poses_en_imagen_blanca={poses}")
