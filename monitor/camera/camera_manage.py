import cv2
import platform

class CameraManager:
    """Manages camera detection and selection"""
    
    def __init__(self):
        self._available_cameras = []
        self._selected_camera = 0
        self.detect_cameras()
    
    def detect_cameras(self):
        """Detect all available cameras"""
        self._available_cameras = []
        
        # Try up to 10 camera indices
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    # Get camera properties
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = int(cap.get(cv2.CAP_PROP_FPS))
                    
                    camera_info = {
                        'index': i,
                        'name': f'Camera {i}',
                        'type': 'USB' if i > 0 else 'Built-in',
                        'width': width,
                        'height': height,
                        'fps': fps if fps > 0 else 30,
                        'source': i
                    }
                    
                    self._available_cameras.append(camera_info)
                    print(f"📷 Found camera {i}: {width}x{height} @ {fps}fps")
                
                cap.release()
        
        if not self._available_cameras:
            print("⚠️ No cameras detected!")
        else:
            print(f"✅ Total cameras found: {len(self._available_cameras)}")
        
        return self._available_cameras
    
    def get_available_cameras(self):
        """Return list of available cameras"""
        return self._available_cameras
    
    def get_selected_camera(self):
        """Get currently selected camera info"""
        if 0 <= self._selected_camera < len(self._available_cameras):
            return self._available_cameras[self._selected_camera]
        return None
    
    def get_selected_camera_index(self):
        """Get the index of selected camera"""
        camera = self.get_selected_camera()
        return camera['index'] if camera else 0
    
    def set_selected_camera(self, camera_id):
        """Set the active camera by ID"""
        if 0 <= camera_id < len(self._available_cameras):
            self._selected_camera = camera_id
            print(f"✅ Selected camera: {self._available_cameras[camera_id]['name']}")
            return True
        print(f"❌ Invalid camera ID: {camera_id}")
        return False
    
    def refresh_cameras(self):
        """Refresh the camera list"""
        print("🔄 Refreshing camera list...")
        self.detect_cameras()