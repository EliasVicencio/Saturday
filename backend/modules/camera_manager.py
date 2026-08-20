import base64
import random
from datetime import datetime
import os

class CameraManager:
    """Gestor de cámara para Saturday"""
    
    def __init__(self):
        self.is_available = True  # Simulado - en realidad verificaría hardware
        self.last_capture = None
        print("📷 CameraManager inicializado (modo simulado)")
    
    def capture(self):
        """Captura una imagen de la cámara (simuleada)"""
        try:
            # Generar una imagen simulada en base64 (patrones eléctricos)
            # En producción real, aquí iría: cv2.VideoCapture(0).read()
            width, height = 300, 200
            # Crear un patrón simulado con colores electricos
            import struct
            image_data = bytearray()
            for y in range(height):
                for x in range(width):
                    # Patrón aleatorio eléctrico
                    r = random.randint(100, 255)
                    g = random.randint(50, 150) 
                    b = random.randint(200, 255)
                    image_data.extend([b, g, r])  # BGR para JPEG
            
            # Convertir a base64 "imagen"
            simulated_image = base64.b64encode(bytes(image_data)).decode('utf-8')
            self.last_capture = {
                'timestamp': datetime.now().isoformat(),
                'simulated': True,
                'data': simulated_image[:50] + "..." + simulated_image[-50:]  # Truncado para el ejemplo
            }
            return f"✅ Cámara capturada (simulada)"
        except Exception as e:
            return f"❌ Error accediendo a cámara: {str(e)}"
    
    def get_status(self):
        """Obtiene estado de la cámara"""
        return {
            'available': self.is_available,
            'last_capture': self.last_capture
        }