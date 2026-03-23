import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import time
import threading
from .base_camera import VideoCamera

# Import sound library - using winsound for Windows or os.system for cross-platform
import platform
if platform.system() == 'Windows':
    import winsound
else:
    import os

class ExamCamera(VideoCamera):
    def __init__(self):
        super().__init__()
        print("📝 ExamCamera initialized!")
        
        # Initialize MediaPipe Face Landmarker
        base_options = python.BaseOptions(
            model_asset_path='face_landmarker.task'
        )
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=5,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        try:
            self.detector = vision.FaceLandmarker.create_from_options(options)
            print("✅ Face Landmarker loaded successfully")
        except Exception as e:
            print(f"\n⚠️  Error: face_landmarker.task model file not found!")
            print("\nPlease download the model file:")
            print("1. Visit: https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task")
            print("2. Download and save it in the project root folder")
            print("3. Make sure it's named: face_landmarker.task")
            raise e
        
        # Alert tracking with timestamps
        self.eyes_away_start_time = None
        self.no_face_start_time = None
        self.multiple_person_detected = False
        
        # Thresholds (in seconds)
        self.EYES_AWAY_THRESHOLD = 3.0  # 3 seconds
        self.NO_FACE_THRESHOLD = 3.0    # 3 seconds
        # Multiple person alert is immediate (0 seconds)
        
        # Eye landmarks - iris center points
        self.LEFT_IRIS = [474, 475, 476, 477]
        self.RIGHT_IRIS = [469, 470, 471, 472]
        
        # Eye corner landmarks for reference
        self.LEFT_EYE_CORNERS = [33, 133]  # left inner, left outer
        self.RIGHT_EYE_CORNERS = [362, 263]  # right inner, right outer
        
        # Landmarks for vertical gaze detection
        self.LEFT_EYE_TOP = 159
        self.LEFT_EYE_BOTTOM = 145
        self.RIGHT_EYE_TOP = 386
        self.RIGHT_EYE_BOTTOM = 374
        
        # Nose tip and chin for head tilt detection
        self.NOSE_TIP = 4
        self.CHIN = 152
        self.FOREHEAD = 10
        
        # Session tracking
        self.session_start_time = None
        self.total_eyes_away_time = 0
        self.total_no_face_time = 0
        self.total_multiple_person_time = 0
        self.alert_count = 0
        
        # Sound alert control
        self.sound_thread = None
        self.should_beep = False
        self.beep_lock = threading.Lock()
        self.is_windows = platform.system() == 'Windows'

    def release(self):
        """Cleanup MediaPipe and camera"""
        # Stop any ongoing beeps
        self.stop_beep()
        
        try:
            if hasattr(self, 'detector') and self.detector:
                self.detector.close()
            print("🧹 ExamCamera MediaPipe cleaned up")
        except Exception as e:
            print(f"Warning during MediaPipe cleanup: {e}")
        
        # Call parent release
        super().release()

    def start_beep(self):
        """Start continuous beeping in a separate thread"""
        with self.beep_lock:
            if not self.should_beep:
                self.should_beep = True
                self.sound_thread = threading.Thread(target=self._beep_loop, daemon=True)
                self.sound_thread.start()

    def stop_beep(self):
        """Stop continuous beeping"""
        with self.beep_lock:
            self.should_beep = False
            if self.sound_thread:
                self.sound_thread.join(timeout=0.5)
                self.sound_thread = None

    def _beep_loop(self):
        """Continuous beep loop running in separate thread"""
        while True:
            with self.beep_lock:
                if not self.should_beep:
                    break
            
            try:
                if self.is_windows:
                    # Windows beep: frequency 1000Hz, duration 300ms
                    winsound.Beep(1000, 300)
                    time.sleep(0.2)  # Short pause between beeps
                else:
                    # Cross-platform beep using system bell
                    print('\a', end='', flush=True)
                    # Alternative for Linux/Mac with sound
                    try:
                        os.system('paplay /usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga 2>/dev/null || afplay /System/Library/Sounds/Funk.aiff 2>/dev/null || beep 2>/dev/null')
                    except:
                        pass
                    time.sleep(0.5)  # Short pause between beeps
            except Exception as e:
                print(f"Beep error: {e}")
                # Fallback to print bell character
                print('\a', end='', flush=True)
                time.sleep(0.5)

    def check_head_tilt(self, landmarks, frame_height):
        """
        Check if head is tilted up or down significantly
        Returns True if head is in normal position, False if tilted
        """
        try:
            nose_y = landmarks[self.NOSE_TIP].y * frame_height
            chin_y = landmarks[self.CHIN].y * frame_height
            forehead_y = landmarks[self.FOREHEAD].y * frame_height
            
            # Calculate vertical distances
            nose_to_chin = chin_y - nose_y
            forehead_to_nose = nose_y - forehead_y
            
            # Normal ratio is around 1.0-1.3
            # Looking up: ratio > 1.5
            # Looking down: ratio < 0.7
            if forehead_to_nose > 0:
                ratio = nose_to_chin / forehead_to_nose
                
                # Head in normal range
                if 0.7 < ratio < 1.6:
                    return True, ratio, "Normal"
                elif ratio >= 1.6:
                    return False, ratio, "Looking Up"
                else:
                    return False, ratio, "Looking Down"
            
            return True, 1.0, "Normal"
        except Exception as e:
            print(f"⚠️ Head tilt check error: {e}")
            return True, 1.0, "Normal"

    def check_eye_direction(self, landmarks, frame_width, frame_height):
        """
        Check if eyes are looking at screen (center) or away
        Also checks vertical gaze (up/down)
        Returns (looking_at_screen, horizontal_ratio, vertical_ratio, status_text)
        """
        try:
            # HORIZONTAL GAZE CHECK
            # Get left eye iris center
            left_iris_x = np.mean([landmarks[i].x for i in self.LEFT_IRIS]) * frame_width
            left_eye_left = landmarks[self.LEFT_EYE_CORNERS[0]].x * frame_width
            left_eye_right = landmarks[self.LEFT_EYE_CORNERS[1]].x * frame_width
            left_eye_width = abs(left_eye_right - left_eye_left)
            
            # Get right eye iris center
            right_iris_x = np.mean([landmarks[i].x for i in self.RIGHT_IRIS]) * frame_width
            right_eye_left = landmarks[self.RIGHT_EYE_CORNERS[0]].x * frame_width
            right_eye_right = landmarks[self.RIGHT_EYE_CORNERS[1]].x * frame_width
            right_eye_width = abs(right_eye_right - right_eye_left)
            
            # Calculate horizontal iris position (0 = far left, 0.5 = center, 1 = far right)
            left_h_ratio = (left_iris_x - left_eye_left) / left_eye_width if left_eye_width > 0 else 0.5
            right_h_ratio = (right_iris_x - right_eye_left) / right_eye_width if right_eye_width > 0 else 0.5
            avg_h_ratio = (left_h_ratio + right_h_ratio) / 2
            
            # VERTICAL GAZE CHECK
            # Get iris vertical position
            left_iris_y = np.mean([landmarks[i].y for i in self.LEFT_IRIS]) * frame_height
            left_eye_top = landmarks[self.LEFT_EYE_TOP].y * frame_height
            left_eye_bottom = landmarks[self.LEFT_EYE_BOTTOM].y * frame_height
            left_eye_height = abs(left_eye_bottom - left_eye_top)
            
            right_iris_y = np.mean([landmarks[i].y for i in self.RIGHT_IRIS]) * frame_height
            right_eye_top = landmarks[self.RIGHT_EYE_TOP].y * frame_height
            right_eye_bottom = landmarks[self.RIGHT_EYE_BOTTOM].y * frame_height
            right_eye_height = abs(right_eye_bottom - right_eye_top)
            
            # Calculate vertical iris position (0 = top, 0.5 = center, 1 = bottom)
            left_v_ratio = (left_iris_y - left_eye_top) / left_eye_height if left_eye_height > 0 else 0.5
            right_v_ratio = (right_iris_y - right_eye_top) / right_eye_height if right_eye_height > 0 else 0.5
            avg_v_ratio = (left_v_ratio + right_v_ratio) / 2
            
            # Determine status
            # Horizontal: center range 0.30-0.70
            # Vertical: center range 0.35-0.65
            horizontal_ok = 0.28 < avg_h_ratio < 0.72
            vertical_ok = 0.32 < avg_v_ratio < 0.68
            
            looking_at_screen = horizontal_ok and vertical_ok
            
            # Generate status text
            if not horizontal_ok and not vertical_ok:
                if avg_h_ratio <= 0.28:
                    status = "Looking Left & " + ("Up" if avg_v_ratio <= 0.32 else "Down")
                else:
                    status = "Looking Right & " + ("Up" if avg_v_ratio <= 0.32 else "Down")
            elif not horizontal_ok:
                status = "Looking Left" if avg_h_ratio <= 0.28 else "Looking Right"
            elif not vertical_ok:
                status = "Looking Up" if avg_v_ratio <= 0.32 else "Looking Down"
            else:
                status = "Looking at Screen"
            
            return looking_at_screen, avg_h_ratio, avg_v_ratio, status
            
        except Exception as e:
            print(f"⚠️ Eye direction check error: {e}")
            return True, 0.5, 0.5, "Unknown"

    def draw_alert_box(self, frame, alert_text, position, color, blink=False):
        """Draw alert box on frame with optional blinking"""
        if blink and int(time.time() * 2) % 2 == 0:  # Blink twice per second
            return
            
        x, y = position
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(alert_text, font, 0.9, 2)[0]
        
        # Background rectangle
        cv2.rectangle(frame, 
                     (x - 10, y - text_size[1] - 15),
                     (x + text_size[0] + 10, y + 10),
                     color, -1)
        
        # Border
        cv2.rectangle(frame,
                     (x - 10, y - text_size[1] - 15),
                     (x + text_size[0] + 10, y + 10),
                     (255, 255, 255), 3)
        
        # Text
        cv2.putText(frame, alert_text, (x, y),
                   font, 0.9, (255, 255, 255), 2)

    def get_frame(self):
        """Process each frame for exam proctoring"""
        frame = self.get_raw_frame()
        if frame is None:
            return None

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        
        current_time = time.time()
        should_alert = False
        
        try:
            # Convert frame to MediaPipe Image
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
            # Detect faces
            detection_result = self.detector.detect(mp_image)
            
            num_faces = len(detection_result.face_landmarks) if detection_result.face_landmarks else 0
            looking_at_screen = True
            h_ratio = 0.5
            v_ratio = 0.5
            eye_status = "Unknown"
            head_normal = True
            head_ratio = 1.0
            head_status = "Normal"
            
            # CASE 1: Multiple people detected - IMMEDIATE ALERT
            if num_faces > 1:
                if not self.multiple_person_detected:
                    self.multiple_person_detected = True
                    self.alert_count += 1
                should_alert = True
                
                # Reset other timers
                self.eyes_away_start_time = None
                self.no_face_start_time = None
                
            # CASE 2: No face detected
            elif num_faces == 0:
                self.multiple_person_detected = False
                
                if self.no_face_start_time is None:
                    self.no_face_start_time = current_time
                
                elapsed = current_time - self.no_face_start_time
                
                if elapsed >= self.NO_FACE_THRESHOLD:
                    should_alert = True
                
                # Reset eyes away timer
                self.eyes_away_start_time = None
                
            # CASE 3: Exactly one face detected
            elif num_faces == 1:
                self.multiple_person_detected = False
                self.no_face_start_time = None
                
                landmarks = detection_result.face_landmarks[0]
                
                # Check head tilt
                head_normal, head_ratio, head_status = self.check_head_tilt(landmarks, h)
                
                # Check eye direction (horizontal and vertical)
                looking_at_screen, h_ratio, v_ratio, eye_status = self.check_eye_direction(landmarks, w, h)
                
                # Consider both eye direction and head tilt
                if not looking_at_screen or not head_normal:
                    if self.eyes_away_start_time is None:
                        self.eyes_away_start_time = current_time
                    
                    elapsed = current_time - self.eyes_away_start_time
                    
                    if elapsed >= self.EYES_AWAY_THRESHOLD:
                        should_alert = True
                else:
                    # Reset timer when looking at screen with normal head position
                    self.eyes_away_start_time = None
                
                # Draw iris points for visualization
                for idx in self.LEFT_IRIS + self.RIGHT_IRIS:
                    x = int(landmarks[idx].x * w)
                    y = int(landmarks[idx].y * h)
                    cv2.circle(frame, (x, y), 3, (0, 0, 255), -1)
                
                # Draw eye corners and vertical markers
                for idx in self.LEFT_EYE_CORNERS + self.RIGHT_EYE_CORNERS:
                    x = int(landmarks[idx].x * w)
                    y = int(landmarks[idx].y * h)
                    cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
                
                # Draw head tilt reference points
                for idx in [self.NOSE_TIP, self.CHIN, self.FOREHEAD]:
                    x = int(landmarks[idx].x * w)
                    y = int(landmarks[idx].y * h)
                    cv2.circle(frame, (x, y), 3, (255, 0, 255), -1)
            
            # Control beeping based on alert status
            if should_alert:
                self.start_beep()
            else:
                self.stop_beep()
            
            # Display alerts
            alert_y = 50
            
            # Multiple people alert (IMMEDIATE - BLINKING)
            if num_faces > 1:
                self.draw_alert_box(frame, "🚨 ALERT: MULTIPLE PEOPLE DETECTED! 🚨", 
                                  (50, alert_y), (0, 0, 255), blink=True)
                alert_y += 80
            
            # No face detected alert
            if num_faces == 0:
                if self.no_face_start_time:
                    elapsed = current_time - self.no_face_start_time
                    if elapsed >= self.NO_FACE_THRESHOLD:
                        self.draw_alert_box(frame, "⚠️  ALERT: NO FACE DETECTED! ⚠️", 
                                          (50, alert_y), (0, 0, 255), blink=True)
                    else:
                        remaining = self.NO_FACE_THRESHOLD - elapsed
                        self.draw_alert_box(frame, f"WARNING: No face - Alert in {remaining:.1f}s", 
                                          (50, alert_y), (0, 140, 255))
                    alert_y += 80
            
            # Eyes not on screen / head tilted alert
            if num_faces == 1 and (not looking_at_screen or not head_normal):
                if self.eyes_away_start_time:
                    elapsed = current_time - self.eyes_away_start_time
                    if elapsed >= self.EYES_AWAY_THRESHOLD:
                        reason = head_status if not head_normal else eye_status
                        self.draw_alert_box(frame, f"⚠️  WARNING: {reason.upper()}! ⚠️", 
                                          (50, alert_y), (0, 140, 255), blink=True)
                    else:
                        remaining = self.EYES_AWAY_THRESHOLD - elapsed
                        reason = head_status if not head_normal else eye_status
                        self.draw_alert_box(frame, f"Warning: {reason} - Alert in {remaining:.1f}s", 
                                          (50, alert_y), (0, 200, 255))
            
            # Status panel - TOP RIGHT CORNER
            status_x = w - 510  # 510 pixels from right edge
            status_y = 10
            panel_width = 500
            panel_height = 190
            
            cv2.rectangle(frame, (status_x, status_y), (status_x + panel_width, status_y + panel_height), (40, 40, 40), -1)
            cv2.rectangle(frame, (status_x, status_y), (status_x + panel_width, status_y + panel_height), (255, 255, 255), 2)
            
            # Status text
            text_x = status_x + 10
            cv2.putText(frame, "EXAM PROCTORING SYSTEM", (text_x, status_y + 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            cv2.putText(frame, f"Faces Detected: {num_faces}", (text_x, status_y + 55),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Eye status with color coding
            status_color = (0, 255, 0) if looking_at_screen and head_normal else (0, 0, 255)
            cv2.putText(frame, f"Eye Status: {eye_status}", (text_x, status_y + 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
            
            # Head status
            head_color = (0, 255, 0) if head_normal else (0, 0, 255)
            cv2.putText(frame, f"Head Position: {head_status} ({head_ratio:.2f})", 
                       (text_x, status_y + 105),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, head_color, 1)
            
            cv2.putText(frame, f"Gaze H: {h_ratio:.2f} V: {v_ratio:.2f}", 
                       (text_x, status_y + 130),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            # Alert indicator
            alert_text = "🔊 ALERT ACTIVE" if should_alert else "✓ Normal"
            alert_color = (0, 0, 255) if should_alert else (0, 255, 0)
            cv2.putText(frame, alert_text, (text_x, status_y + 155), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, alert_color, 2)
            
            cv2.putText(frame, f"Total Alerts: {self.alert_count}", (text_x, status_y + 180),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Add mode indicator
            cv2.putText(frame, "EXAM MODE", (30, h - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            
        except Exception as e:
            print(f"⚠️ Frame processing error: {e}")
            cv2.putText(frame, "Processing Error", (30, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            self.stop_beep()

        ret, jpeg = cv2.imencode(".jpg", frame)
        if not ret:
            return None
        return jpeg.tobytes()