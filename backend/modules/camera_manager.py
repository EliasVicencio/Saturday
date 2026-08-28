# camera_manager.py - Captura de snapshots bajo demanda
import os
import time
import base64
from datetime import datetime
from typing import Optional

class CameraManager:
    def __init__(self):
        self.is_available = False
        self.last_capture = None
        self._cv2 = None
        self._capture_dir = os.path.join(os.path.dirname(__file__), "..", "data", "snapshots")
        os.makedirs(self._capture_dir, exist_ok=True)
        try:
            import cv2
            self._cv2 = cv2
            self.is_available = True
            print("[Camera] OK - OpenCV disponible")
        except ImportError:
            self.is_available = False
            print("[Camera] WARN - OpenCV no disponible, modo sin camara")

    def capture(self, save: bool = False) -> Optional[str]:
        if not self.is_available or not self._cv2:
            return self._placeholder()
        try:
            cap = self._cv2.VideoCapture(0)
            if not cap.isOpened():
                return self._placeholder()
            ret, frame = cap.read()
            cap.release()
            if not ret or frame is None:
                return self._placeholder()
            _, buf = self._cv2.imencode(".jpg", frame, [self._cv2.IMWRITE_JPEG_QUALITY, 85])
            img_bytes = buf.tobytes()
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            self.last_capture = {"timestamp": datetime.now().isoformat(), "simulated": False, "size_bytes": len(img_bytes)}
            if save:
                path = os.path.join(self._capture_dir, f"snapshot_{int(time.time())}.jpg")
                with open(path, "wb") as f:
                    f.write(img_bytes)
                self.last_capture["saved_to"] = path
            return img_b64
        except Exception as e:
            print(f"[Camera] ERROR: {e}")
            return self._placeholder()

    def capture_to_file(self) -> Optional[str]:
        if not self.is_available or not self._cv2:
            return None
        try:
            cap = self._cv2.VideoCapture(0)
            if not cap.isOpened():
                return None
            ret, frame = cap.read()
            cap.release()
            if not ret or frame is None:
                return None
            path = os.path.join(self._capture_dir, f"snapshot_{int(time.time())}.jpg")
            self._cv2.imwrite(path, frame)
            self.last_capture = {"timestamp": datetime.now().isoformat(), "simulated": False, "saved_to": path}
            return path
        except Exception as e:
            return None

    def _placeholder(self) -> str:
        self.last_capture = {"timestamp": datetime.now().isoformat(), "simulated": True}
        return base64.b64encode(b"PLACEHOLDER").decode("utf-8")

    def get_status(self) -> dict:
        return {"available": self.is_available, "opencv": self._cv2 is not None, "last_capture": self.last_capture}
