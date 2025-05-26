import os
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip
from typing import Tuple


class VerticalVideoProcessor:
    def __init__(self):
        try:
            from insightface.app import FaceAnalysis
            self.face_analyser = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
            self.face_analyser.prepare(ctx_id=0, det_size=(320, 320))
        except ImportError:
            self.face_analyser = None

    def detect_face(self, frame: np.ndarray) -> Tuple[int, int, int, int]:
        # InsightFace Detection
        if self.face_analyser:
            faces = self.face_analyser.get(frame)
            if faces:
                largest = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
                x1, y1, x2, y2 = map(int, largest.bbox)
                return x1, y1, x2 - x1, y2 - y1

        # Fallback: center box
        h, w = frame.shape[:2]
        fw = int(w * 0.3)
        fh = int(fw / (16 / 9))
        x = (w - fw) // 2
        y = (h - fh) // 3
        return x, y, fw, fh

    def convert_to_vertical(self, input_path: str, output_path: str):
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise RuntimeError("Cannot open input video")

        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        ret, frame = cap.read()
        if not ret:
            raise RuntimeError("Cannot read frame from video")

        fx, fy, fw, fh = self.detect_face(frame)

        # Red zone: full height center crop
        red_w = int(width * 0.55)
        red_h = height
        red_x = (width - red_w) // 2
        red_y = 0

        # Output video writer (vertical 1080x1920)
        out_w, out_h = 1080, 1920
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        temp_noaudio_path = output_path.replace('.mp4', '_noaudio.mp4')
        writer = cv2.VideoWriter(temp_noaudio_path, fourcc, fps, (out_w, out_h))

        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Crop top (green)
            top = frame[fy:fy+fh, fx:fx+fw]
            top = cv2.resize(top, (out_w, int(out_h * 0.3)))

            # Crop bottom (red)
            bottom = frame[red_y:red_y+red_h, red_x:red_x+red_w]
            bottom = cv2.resize(bottom, (out_w, int(out_h * 0.7)))

            combined = np.vstack((top, bottom))
            writer.write(combined)

        cap.release()
        writer.release()

        # Add audio
        clip = VideoFileClip(temp_noaudio_path)
        audio = AudioFileClip(input_path)
        final = clip.set_audio(audio)
        final.write_videofile(output_path, codec="libx264", audio_codec="aac")
        os.remove(temp_noaudio_path)