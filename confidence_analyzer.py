# pyright: reportOptionalCall=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportOptionalSubscript=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportMissingImports=false
# pyright: reportArgumentType=false
"""
Confidence Analyzer Module (Pillar 2)
Analyze interview video for confidence indicators
Evaluates: Facial expressions, Eye contact, Body posture, Overall confidence
Uses: TensorFlow emotion_model.h5, MediaPipe for face/eye tracking
Output: Confidence Score percentage
"""
import os
import json
from typing import Optional, Dict, Any, Tuple

# NumPy
np = None
try:
    import numpy as np_module
    np = np_module
except ImportError:
    print("[CONFIDENCE_ANALYZER] NumPy not available")

# OpenCV
cv2 = None
try:
    import cv2 as cv2_module
    cv2 = cv2_module
except ImportError:
    print("[CONFIDENCE_ANALYZER] OpenCV not available")

# MediaPipe for face analysis
mp = None
mp_face_mesh = None
mp_face_landmarker = None
MEDIAPIPE_AVAILABLE = False
MEDIAPIPE_TASKS_API = False

try:
    import mediapipe as mp_module
    mp = mp_module
    
    # Try old solutions API first (MediaPipe < 0.10.x)
    if hasattr(mp, 'solutions') and hasattr(mp.solutions, 'face_mesh'):
        mp_face_mesh = mp.solutions.face_mesh
        MEDIAPIPE_AVAILABLE = True
        print("[CONFIDENCE_ANALYZER] MediaPipe (solutions API) loaded successfully")
    # Try new Tasks API (MediaPipe >= 0.10.x)
    elif hasattr(mp, 'tasks'):
        try:
            from mediapipe.tasks import python as mp_tasks
            from mediapipe.tasks.python import vision as mp_vision
            mp_face_landmarker = mp_vision
            MEDIAPIPE_AVAILABLE = True
            MEDIAPIPE_TASKS_API = True
            print("[CONFIDENCE_ANALYZER] MediaPipe (Tasks API) loaded successfully")
        except Exception as e:
            print(f"[CONFIDENCE_ANALYZER] MediaPipe Tasks API not available: {e}")
    else:
        print("[CONFIDENCE_ANALYZER] MediaPipe loaded but face_mesh not available - using OpenCV fallback")
        
except (ImportError, AttributeError, Exception) as e:
    print(f"[CONFIDENCE_ANALYZER] MediaPipe not available: {e}")

# TensorFlow/Keras - lazy loading
tf = None
load_model = None
img_to_array = None
_tf_loaded = False


def _load_tensorflow():
    """Lazy load TensorFlow to avoid slow startup"""
    global tf, load_model, img_to_array, _tf_loaded
    
    if _tf_loaded:
        return tf is not None
    
    _tf_loaded = True
    
    try:
        import tensorflow as tf_module
        tf = tf_module
        
        try:
            from tensorflow.keras.models import load_model as lm
            from tensorflow.keras.preprocessing.image import img_to_array as ita
        except:
            from keras.models import load_model as lm
            from keras.preprocessing.image import img_to_array as ita
        
        load_model = lm
        img_to_array = ita
        print("[CONFIDENCE_ANALYZER] TensorFlow loaded")
        return True
        
    except Exception as e:
        print(f"[CONFIDENCE_ANALYZER] TensorFlow not available: {e}")
        return False


# Model paths
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'emotion_model.h5')
LABELS_PATH = os.path.join(os.path.dirname(__file__), 'labels.txt')


class ConfidenceAnalyzer:
    """
    Independent Confidence Analysis Module
    Analyzes video for confidence indicators
    Returns Confidence Score %
    """
    
    def __init__(self):
        self.emotion_model = None
        self.emotion_labels = None
        self.face_cascade = None
        self.face_mesh = None
        self.input_shape = None
        
        # Positive emotions that indicate confidence
        self.confidence_emotions = ['happy', 'neutral', 'surprise']
        self.negative_emotions = ['angry', 'sad', 'fear', 'disgust']
        
        # Eye contact landmark indices (MediaPipe)
        self.left_eye_indices = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        self.right_eye_indices = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        self.iris_left = [468, 469, 470, 471, 472]
        self.iris_right = [473, 474, 475, 476, 477]
        
        self._initialize()
    
    def _initialize(self):
        """Initialize models and resources"""
        # Load emotion model
        if _load_tensorflow() and os.path.exists(MODEL_PATH):
            try:
                self.emotion_model = load_model(MODEL_PATH, compile=False)  # type: ignore
                self.input_shape = self.emotion_model.input_shape[1:3]  # type: ignore
                print(f"   ✅ Emotion model loaded: {self.input_shape}")
            except Exception as e:
                print(f"   ⚠️ Failed to load emotion model: {e}")
        
        # Load emotion labels
        if os.path.exists(LABELS_PATH):
            try:
                with open(LABELS_PATH, 'r') as f:
                    self.emotion_labels = [line.strip() for line in f.readlines()]
                print(f"   ✅ Labels loaded: {self.emotion_labels}")
            except:
                self.emotion_labels = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
        else:
            self.emotion_labels = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
        
        # Load face cascade
        if cv2 is not None:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            if os.path.exists(cascade_path):
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Initialize MediaPipe Face Mesh
        if MEDIAPIPE_AVAILABLE and mp_face_mesh is not None and not MEDIAPIPE_TASKS_API:
            try:
                self.face_mesh = mp_face_mesh.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                print("   ✅ MediaPipe Face Mesh initialized")
            except Exception as e:
                print(f"   ⚠️ MediaPipe init failed: {e}")
    
    def detect_emotion(self, face_img) -> Tuple[str, float]:
        """Detect emotion from face image"""
        if self.emotion_model is None or face_img is None:
            return 'unknown', 0.0
        
        try:
            # Preprocess face for model
            input_h, input_w = self.input_shape if self.input_shape else (48, 48)
            
            # Convert to grayscale if needed
            if len(face_img.shape) == 3:
                gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            else:
                gray = face_img
            
            # Resize to model input
            resized = cv2.resize(gray, (input_w, input_h))
            
            # Normalize and reshape
            normalized = resized.astype('float32') / 255.0
            input_data = normalized.reshape(1, input_h, input_w, 1)
            
            # Predict
            predictions = self.emotion_model.predict(input_data, verbose=0)  # type: ignore
            emotion_idx = int(np.argmax(predictions[0]))  # type: ignore
            confidence = float(predictions[0][emotion_idx])
            
            emotion = self.emotion_labels[emotion_idx] if emotion_idx < len(self.emotion_labels) else 'unknown'  # type: ignore
            
            return emotion, confidence
            
        except Exception as e:
            return 'unknown', 0.0
    
    def calculate_eye_contact(self, face_landmarks, frame_width, frame_height) -> float:
        """Calculate eye contact score based on gaze direction"""
        if face_landmarks is None:
            return 0.0
        
        try:
            # Get iris positions
            landmarks = face_landmarks.landmark
            
            # Left eye center
            left_eye_center_x = sum(landmarks[i].x for i in self.left_eye_indices) / len(self.left_eye_indices)
            left_eye_center_y = sum(landmarks[i].y for i in self.left_eye_indices) / len(self.left_eye_indices)
            
            # Right eye center
            right_eye_center_x = sum(landmarks[i].x for i in self.right_eye_indices) / len(self.right_eye_indices)
            right_eye_center_y = sum(landmarks[i].y for i in self.right_eye_indices) / len(self.right_eye_indices)
            
            # Get iris center if available
            if len(self.iris_left) > 0 and self.iris_left[0] < len(landmarks):
                left_iris_x = landmarks[self.iris_left[0]].x
                right_iris_x = landmarks[self.iris_right[0]].x
            else:
                left_iris_x = left_eye_center_x
                right_iris_x = right_eye_center_x
            
            # Calculate deviation from center
            left_deviation = abs(left_iris_x - left_eye_center_x)
            right_deviation = abs(right_iris_x - right_eye_center_x)
            avg_deviation = (left_deviation + right_deviation) / 2
            
            # Convert to score (lower deviation = higher score)
            eye_contact_score = max(0, 100 - (avg_deviation * 1000))
            
            return min(100, eye_contact_score)
            
        except Exception as e:
            return 50.0
    
    def analyze_frame(self, frame) -> Dict:
        """Analyze a single frame for confidence indicators"""
        if frame is None or cv2 is None:
            return {'face_detected': False, 'emotion': None, 'eye_contact': 0}
        
        result = {
            'face_detected': False,
            'emotion': None,
            'emotion_confidence': 0,
            'eye_contact': 0
        }
        
        try:
            height, width = frame.shape[:2]
            
            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect face and landmarks
            if self.face_mesh:
                mesh_results = self.face_mesh.process(rgb_frame)
                
                if mesh_results.multi_face_landmarks:
                    result['face_detected'] = True
                    face_landmarks = mesh_results.multi_face_landmarks[0]
                    
                    # Calculate eye contact
                    result['eye_contact'] = self.calculate_eye_contact(face_landmarks, width, height)
            
            # Detect faces for emotion analysis
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if self.face_cascade is not None:
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                
                if len(faces) > 0:
                    result['face_detected'] = True
                    x, y, w, h = faces[0]
                    face_roi = gray[y:y+h, x:x+w]
                    
                    # Detect emotion
                    emotion, confidence = self.detect_emotion(face_roi)
                    result['emotion'] = emotion
                    result['emotion_confidence'] = confidence
            
            return result
            
        except Exception as e:
            return {'face_detected': False, 'emotion': None, 'eye_contact': 0, 'error': str(e)}
    
    def analyze(self, video_path: str, sample_rate: int = 30) -> Dict:
        """
        Main analysis method - analyze video for confidence
        
        Args:
            video_path: Path to video file
            sample_rate: Analyze every Nth frame
        
        Returns:
            dict: {
                'score': float (0-100),
                'status': 'success' or 'error',
                'face_presence': float,
                'eye_contact': float,
                'emotion_breakdown': dict,
                'analysis_detail': str (JSON),
                'error': str or None
            }
        """
        try:
            print(f"\n{'='*50}")
            print(f"😊 [CONFIDENCE_ANALYZER] Starting video analysis...")
            print(f"{'='*50}")
            print(f"   🎬 Video: {video_path}")
            
            if not os.path.exists(video_path):
                return {
                    'score': 0,
                    'status': 'error',
                    'face_presence': 0,
                    'eye_contact': 0,
                    'emotion_breakdown': {},
                    'analysis_detail': json.dumps({'error': 'Video not found'}),
                    'error': f'Video file not found: {video_path}'
                }
            
            if cv2 is None:
                return {
                    'score': 0,
                    'status': 'error',
                    'face_presence': 0,
                    'eye_contact': 0,
                    'emotion_breakdown': {},
                    'analysis_detail': json.dumps({'error': 'OpenCV not available'}),
                    'error': 'OpenCV is required for video analysis'
                }
            
            # Open video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {
                    'score': 0,
                    'status': 'error',
                    'face_presence': 0,
                    'eye_contact': 0,
                    'emotion_breakdown': {},
                    'analysis_detail': json.dumps({'error': 'Could not open video'}),
                    'error': 'Failed to open video file'
                }
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            
            print(f"   📊 Total frames: {total_frames}, FPS: {fps:.1f}, Duration: {duration:.1f}s")
            
            # Analysis metrics
            frames_analyzed = 0
            faces_detected = 0
            eye_contact_scores = []
            emotion_counts = {}
            emotion_confidences = []
            
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Sample frames
                if frame_count % sample_rate != 0:
                    continue
                
                frames_analyzed += 1
                
                # Analyze frame
                frame_result = self.analyze_frame(frame)
                
                if frame_result['face_detected']:
                    faces_detected += 1
                    
                    # Track emotions
                    emotion = frame_result.get('emotion')
                    if emotion:
                        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                        emotion_confidences.append(frame_result.get('emotion_confidence', 0))
                    
                    # Track eye contact
                    eye_contact_scores.append(frame_result.get('eye_contact', 0))
                
                # Progress indicator
                if frames_analyzed % 50 == 0:
                    print(f"   📹 Analyzed {frames_analyzed} frames...")
            
            cap.release()
            
            if frames_analyzed == 0:
                return {
                    'score': 0,
                    'status': 'error',
                    'face_presence': 0,
                    'eye_contact': 0,
                    'emotion_breakdown': {},
                    'analysis_detail': json.dumps({'error': 'No frames analyzed'}),
                    'error': 'Could not analyze any frames'
                }
            
            # Calculate metrics
            face_presence = (faces_detected / frames_analyzed) * 100
            avg_eye_contact = sum(eye_contact_scores) / len(eye_contact_scores) if eye_contact_scores else 0
            
            # Emotion breakdown
            total_emotions = sum(emotion_counts.values())
            emotion_breakdown = {e: (c / total_emotions) * 100 for e, c in emotion_counts.items()} if total_emotions > 0 else {}
            
            # Calculate confidence score
            # Positive emotions contribute positively
            positive_emotion_score = sum(emotion_breakdown.get(e, 0) for e in self.confidence_emotions)
            negative_emotion_score = sum(emotion_breakdown.get(e, 0) for e in self.negative_emotions)
            
            # Weighted confidence score
            emotion_score = positive_emotion_score - (negative_emotion_score * 0.5)
            emotion_score = max(0, min(100, emotion_score))
            
            # Final confidence score
            confidence_score = (
                face_presence * 0.25 +        # Being present
                avg_eye_contact * 0.35 +       # Eye contact
                emotion_score * 0.40           # Positive emotions
            )
            
            # Ensure non-zero if face was detected
            if faces_detected > 0 and confidence_score < 20:
                confidence_score = max(20, confidence_score)
            
            print(f"\n   ✅ Frames analyzed: {frames_analyzed}")
            print(f"   ✅ Face presence: {face_presence:.1f}%")
            print(f"   ✅ Eye contact: {avg_eye_contact:.1f}%")
            print(f"   ✅ Emotion breakdown: {emotion_breakdown}")
            
            analysis_detail = {
                'frames_analyzed': frames_analyzed,
                'faces_detected': faces_detected,
                'face_presence_pct': round(face_presence, 2),
                'avg_eye_contact': round(avg_eye_contact, 2),
                'emotion_breakdown': {k: round(v, 2) for k, v in emotion_breakdown.items()},
                'video_duration': round(duration, 2),
                'model_loaded': self.emotion_model is not None,
                'mediapipe_available': MEDIAPIPE_AVAILABLE
            }
            
            print(f"\n{'='*50}")
            print(f"✅ [CONFIDENCE_ANALYZER] Analysis complete!")
            print(f"   📊 Overall Confidence Score: {confidence_score:.1f}%")
            print(f"{'='*50}")
            
            return {
                'score': round(confidence_score, 2),
                'status': 'success',
                'face_presence': round(face_presence, 2),
                'eye_contact': round(avg_eye_contact, 2),
                'emotion_breakdown': {k: round(v, 2) for k, v in emotion_breakdown.items()},
                'analysis_detail': json.dumps(analysis_detail),
                'error': None
            }
            
        except Exception as e:
            print(f"   ❌ Analysis error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'score': 0,
                'status': 'error',
                'face_presence': 0,
                'eye_contact': 0,
                'emotion_breakdown': {},
                'analysis_detail': json.dumps({'error': str(e)}),
                'error': str(e)
            }


# Singleton instance
_analyzer_instance = None

def get_analyzer():
    """Get or create singleton analyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = ConfidenceAnalyzer()
    return _analyzer_instance


def analyze_confidence(video_path: str, sample_rate: int = 30) -> Dict:
    """
    Convenience function for confidence analysis
    
    Args:
        video_path: Path to video file
        sample_rate: Analyze every Nth frame
    
    Returns:
        dict with 'score', 'status', 'face_presence', 'eye_contact', 'emotion_breakdown', 'error'
    """
    analyzer = get_analyzer()
    return analyzer.analyze(video_path, sample_rate)


if __name__ == "__main__":
    print("Confidence Analyzer Module - Test")
    print("="*50)
    print(f"OpenCV Available: {cv2 is not None}")
    print(f"MediaPipe Available: {MEDIAPIPE_AVAILABLE}")
    print(f"TensorFlow Available: {_load_tensorflow()}")
    print(f"Emotion Model Exists: {os.path.exists(MODEL_PATH)}")
    print("\nModule loaded successfully.")
