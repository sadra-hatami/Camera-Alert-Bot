import os
import sys
import subprocess
import importlib
import json
import time
import logging
import threading
import queue
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from collections import deque

# ============================================================
# بررسی و نصب خودکار کتابخانه‌ها
# ============================================================

REQUIRED_PACKAGES = {
    "opencv-python": "cv2",
    "numpy": "numpy",
    "ultralytics": "ultralytics",
    "deepface": "deepface",
    "pyTelegramBotAPI": "telebot",
    "Pillow": "PIL"
}

def check_and_install_packages():
    """بررسی و نصب خودکار کتابخانه‌های مورد نیاز"""
    print("🔍 در حال بررسی کتابخانه‌های مورد نیاز...")
    
    for package, module in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(module)
            print(f"✅ {package} نصب است.")
        except ImportError:
            print(f"📦 {package} یافت نشد. در حال نصب...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", package],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                print(f"✅ {package} با موفقیت نصب شد.")
            except subprocess.CalledProcessError as e:
                print(f"❌ خطا در نصب {package}: {e}")
                print("لطفاً به صورت دستی نصب کنید:")
                print(f"pip install {package}")
                sys.exit(1)

# ============================================================
# بررسی نسخه Python
# ============================================================

def check_python_version():
    """بررسی نسخه Python"""
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 یا بالاتر مورد نیاز است.")
        print(f"نسخه فعلی: {sys.version}")
        sys.exit(1)
    
    if sys.version_info >= (3, 12):
        print("⚠️ Python 3.12 ممکن است با برخی کتابخانه‌ها سازگاری نداشته باشد.")
        print("پیشنهاد می‌شود از Python 3.11 استفاده کنید.")

# ============================================================
# تنظیمات اولیه
# ============================================================

BOT_TOKEN = ""
ADMIN_CHAT_ID = your id num

PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"
FACES_DIR = PROJECT_DIR / "faces"
EVENTS_DIR = PROJECT_DIR / "events"
MODELS_DIR = PROJECT_DIR / "models"

PEOPLE_FILE = DATA_DIR / "people.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
EVENTS_FILE = DATA_DIR / "events.json"

DEFAULT_SETTINGS = {
    "camera_index": 0,
    "camera_width": 640,
    "camera_height": 480,
    "person_confidence": 0.55,
    "face_threshold": 0.45,
    "confirm_frames": 3,
    "cooldown_seconds": 30,
    "scan_interval": 0.3,
    "height_estimation_enabled": False,
    "roi_enabled": False,
    "roi": {"x": 0, "y": 0, "w": 640, "h": 480},
    "deepface_model": "Facenet",
    "max_events": 1000
}

# ============================================================
# ایجاد ساختار پوشه‌ها
# ============================================================

def create_directories():
    """ایجاد پوشه‌های مورد نیاز"""
    for dir_path in [DATA_DIR, FACES_DIR, EVENTS_DIR, MODELS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 ایجاد پوشه: {dir_path}")

# ============================================================
# مدیریت JSON با Safe Write
# ============================================================

def safe_json_write(data: Any, filepath: Path):
    """نوشتن امن JSON با استفاده از فایل موقت"""
    temp_file = filepath.with_suffix(filepath.suffix + ".tmp")
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, filepath)
        return True
    except Exception as e:
        logging.error(f"خطا در نوشتن {filepath}: {e}")
        if temp_file.exists():
            temp_file.unlink()
        return False

def safe_json_read(filepath: Path, default: Any = None) -> Any:
    """خواندن ایمن JSON با بازگشت به مقدار پیش‌فرض"""
    if not filepath.exists():
        return default
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"خطا در خواندن {filepath}: {e}")
        backup_file = filepath.with_suffix(filepath.suffix + ".backup")
        try:
            shutil.copy2(filepath, backup_file)
            logging.info(f"پشتیبان از فایل خراب: {backup_file}")
        except:
            pass
        return default
    except Exception as e:
        logging.error(f"خطا در خواندن {filepath}: {e}")
        return default

# ============================================================
# مدیریت فایل‌های JSON
# ============================================================

def init_json_files():
    """ایجاد فایل‌های JSON در صورت عدم وجود"""
    if not PEOPLE_FILE.exists():
        safe_json_write([], PEOPLE_FILE)
        print("📄 ایجاد people.json")
    
    if not SETTINGS_FILE.exists():
        safe_json_write(DEFAULT_SETTINGS, SETTINGS_FILE)
        print("📄 ایجاد settings.json")
    else:
        settings = safe_json_read(SETTINGS_FILE, {})
        if not settings or not isinstance(settings, dict):
            safe_json_write(DEFAULT_SETTINGS, SETTINGS_FILE)
            print("🔄 بازسازی settings.json با تنظیمات پیش‌فرض")
        else:
            needs_update = False
            for key, value in DEFAULT_SETTINGS.items():
                if key not in settings:
                    settings[key] = value
                    needs_update = True
            if needs_update:
                safe_json_write(settings, SETTINGS_FILE)
                print("🔄 به‌روزرسانی settings.json")
    
    if not EVENTS_FILE.exists():
        safe_json_write([], EVENTS_FILE)
        print("📄 ایجاد events.json")

# ============================================================
# کلاس مدیریت رویدادها
# ============================================================

@dataclass
class Event:
    id: int
    name: str
    status: str
    confidence: float
    timestamp: str
    image: str
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

class EventManager:
    def __init__(self):
        self.events: List[Event] = []
        self._load()
        self._next_id = self._get_next_id()
    
    def _load(self):
        data = safe_json_read(EVENTS_FILE, [])
        self.events = [Event.from_dict(item) for item in data if isinstance(item, dict)]
    
    def _save(self):
        data = [event.to_dict() for event in self.events]
        safe_json_write(data, EVENTS_FILE)
    
    def _get_next_id(self) -> int:
        if not self.events:
            return 1
        return max(e.id for e in self.events) + 1
    
    def add_event(self, name: str, status: str, confidence: float, image_path: str) -> Event:
        event = Event(
            id=self._next_id,
            name=name,
            status=status,
            confidence=confidence,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            image=image_path
        )
        self.events.append(event)
        self._next_id += 1
        
        max_events = self.get_settings().get("max_events", 1000)
        if len(self.events) > max_events:
            self.events = self.events[-max_events:]
        
        self._save()
        return event
    
    def get_events(self, limit: int = 10) -> List[Event]:
        return self.events[-limit:][::-1]
    
    def get_settings(self) -> dict:
        return safe_json_read(SETTINGS_FILE, DEFAULT_SETTINGS)

# ============================================================
# کلاس مدیریت افراد
# ============================================================

@dataclass
class Person:
    id: int
    name: str
    image: str
    embedding: List[float]
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

class PeopleManager:
    def __init__(self):
        self.people: List[Person] = []
        self._load()
        self._next_id = self._get_next_id()
    
    def _load(self):
        data = safe_json_read(PEOPLE_FILE, [])
        self.people = [Person.from_dict(item) for item in data if isinstance(item, dict)]
    
    def _save(self):
        data = [person.to_dict() for person in self.people]
        safe_json_write(data, PEOPLE_FILE)
    
    def _get_next_id(self) -> int:
        if not self.people:
            return 1
        return max(p.id for p in self.people) + 1
    
    def add_person(self, name: str, image_path: str, embedding: List[float]) -> Person:
        person = Person(
            id=self._next_id,
            name=name,
            image=image_path,
            embedding=embedding
        )
        self.people.append(person)
        self._next_id += 1
        self._save()
        return person
    
    def delete_person(self, person_id: int) -> bool:
        for i, person in enumerate(self.people):
            if person.id == person_id:
                try:
                    image_path = Path(person.image)
                    if image_path.exists():
                        image_path.unlink()
                except:
                    pass
                del self.people[i]
                self._save()
                return True
        return False
    
    def get_person(self, person_id: int) -> Optional[Person]:
        for person in self.people:
            if person.id == person_id:
                return person
        return None
    
    def find_best_match(self, embedding: List[float], threshold: float) -> Tuple[Optional[Person], float]:
        if not self.people:
            return None, 1.0
        
        import numpy as np
        from scipy.spatial.distance import cosine
        
        best_person = None
        best_distance = 1.0
        
        emb = np.array(embedding)
        
        for person in self.people:
            person_emb = np.array(person.embedding)
            distance = cosine(emb, person_emb)
            if distance < best_distance:
                best_distance = distance
                best_person = person
        
        if best_distance <= threshold:
            return best_person, best_distance
        return None, best_distance
    
    def get_people(self) -> List[Person]:
        return self.people.copy()
    
    def get_people_count(self) -> int:
        return len(self.people)

# ============================================================
# کلاس تشخیص چهره با DeepFace
# ============================================================

class FaceRecognizer:
    def __init__(self):
        self.model_name = "Facenet"
        self._loaded = False
        self._load_model()
    
    def _load_model(self):
        try:
            from deepface import DeepFace
            self.deepface = DeepFace
            self._loaded = True
            print("✅ مدل DeepFace بارگذاری شد.")
        except Exception as e:
            logging.error(f"خطا در بارگذاری DeepFace: {e}")
            self._loaded = False
    
    def extract_embedding(self, image_path: str) -> Optional[List[float]]:
        if not self._loaded:
            logging.error("DeepFace بارگذاری نشده است.")
            return None
        
        try:
            embedding = self.deepface.represent(
                img_path=image_path,
                model_name=self.model_name,
                enforce_detection=True,
                detector_backend='opencv'
            )
            
            if embedding and len(embedding) > 0:
                return embedding[0]["embedding"]
            return None
        except Exception as e:
            logging.error(f"خطا در استخراج embedding: {e}")
            return None
    
    def extract_embedding_from_frame(self, frame, face_crop) -> Optional[List[float]]:
        if not self._loaded:
            return None
        
        try:
            import cv2
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                temp_path = f.name
                cv2.imwrite(temp_path, face_crop)
            
            embedding = self.extract_embedding(temp_path)
            
            try:
                os.unlink(temp_path)
            except:
                pass
            
            return embedding
        except Exception as e:
            logging.error(f"خطا در استخراج embedding از فریم: {e}")
            return None

# ============================================================
# کلاس اصلی سیستم نظارت
# ============================================================

class SurveillanceSystem:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.settings = self.load_settings()
        self.people_manager = PeopleManager()
        self.event_manager = EventManager()
        self.face_recognizer = FaceRecognizer()
        
        self.camera = None
        self.is_camera_on = False
        self.is_running = False
        
        self.camera_lock = threading.Lock()
        self.frame_queue = queue.Queue(maxsize=2)
        self.detection_queue = queue.Queue(maxsize=2)
        self.stop_event = threading.Event()
        
        self.tracked_frames = {}
        self.tracked_known = {}
        self.tracked_cooldown = {}
        self.tracked_names = {}
        
        self.camera_thread = None
        self.detection_thread = None
        
        self.yolo_model = None
        self._load_yolo()
        
        print("✅ سیستم نظارت آماده شد.")
    
    def load_settings(self) -> dict:
        return safe_json_read(SETTINGS_FILE, DEFAULT_SETTINGS)
    
    def save_settings(self):
        safe_json_write(self.settings, SETTINGS_FILE)
    
    def _load_yolo(self):
        try:
            from ultralytics import YOLO
            model_path = MODELS_DIR / "yolo11n.pt"
            if not model_path.exists():
                print("📥 دانلود مدل YOLO...")
            self.yolo_model = YOLO(str(model_path))
            print("✅ مدل YOLO بارگذاری شد.")
        except Exception as e:
            logging.error(f"خطا در بارگذاری YOLO: {e}")
            self.yolo_model = None
    
    def start_camera(self):
        with self.camera_lock:
            if self.is_camera_on:
                return False, "📷 دوربین از قبل روشن است."
            
            try:
                import cv2
                self.camera = cv2.VideoCapture(self.settings.get("camera_index", 0))
                
                width = self.settings.get("camera_width", 640)
                height = self.settings.get("camera_height", 480)
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                
                if not self.camera.isOpened():
                    self.camera = None
                    return False, "❌ دوربین باز نشد."
                
                self.is_camera_on = True
                self.is_running = True
                self.stop_event.clear()
                
                self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
                self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
                self.camera_thread.start()
                self.detection_thread.start()
                
                return True, "✅ دوربین روشن شد."
            except Exception as e:
                logging.error(f"خطا در روشن کردن دوربین: {e}")
                return False, f"❌ خطا در روشن کردن دوربین: {e}"
    
    def stop_camera(self):
        with self.camera_lock:
            if not self.is_camera_on:
                return False, "📷 دوربین از قبل خاموش است."
            
            self.is_running = False
            self.stop_event.set()
            
            while not self.frame_queue.empty():
                try:
                    self.frame_queue.get_nowait()
                except:
                    break
            while not self.detection_queue.empty():
                try:
                    self.detection_queue.get_nowait()
                except:
                    break
            
            if self.camera_thread and self.camera_thread.is_alive():
                self.camera_thread.join(timeout=2)
            if self.detection_thread and self.detection_thread.is_alive():
                self.detection_thread.join(timeout=2)
            
            if self.camera:
                self.camera.release()
                self.camera = None
            
            self.is_camera_on = False
            self.tracked_frames.clear()
            self.tracked_known.clear()
            self.tracked_cooldown.clear()
            self.tracked_names.clear()
            
            return True, "✅ دوربین خاموش شد."
    
    def _camera_loop(self):
        import cv2
        
        while self.is_running and not self.stop_event.is_set():
            try:
                if not self.camera or not self.camera.isOpened():
                    break
                
                ret, frame = self.camera.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                
                if self.frame_queue.qsize() < 2:
                    self.frame_queue.put(frame.copy())
                else:
                    try:
                        self.frame_queue.get_nowait()
                    except:
                        pass
                    self.frame_queue.put(frame.copy())
                
                time.sleep(0.01)
            except Exception as e:
                logging.error(f"خطا در حلقه دوربین: {e}")
                time.sleep(0.5)
        
        with self.camera_lock:
            if self.camera:
                self.camera.release()
                self.camera = None
            self.is_camera_on = False
        
        logging.info("حلقه دوربین متوقف شد.")
    
    def _detection_loop(self):
        import cv2
        import numpy as np
        
        while self.is_running and not self.stop_event.is_set():
            try:
                try:
                    frame = self.frame_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                if frame is None:
                    continue
                
                roi_enabled = self.settings.get("roi_enabled", False)
                if roi_enabled:
                    roi = self.settings.get("roi", {"x": 0, "y": 0, "w": 640, "h": 480})
                    x, y, w, h = roi["x"], roi["y"], roi["w"], roi["h"]
                    roi_frame = frame[y:y+h, x:x+w]
                    if roi_frame.size > 0:
                        frame = roi_frame
                
                if self.yolo_model is not None:
                    results = self.yolo_model.track(
                        frame,
                        persist=True,
                        conf=self.settings.get("person_confidence", 0.55),
                        classes=[0],
                        verbose=False
                    )
                    
                    if results and len(results) > 0:
                        result = results[0]
                        boxes = result.boxes
                        
                        if boxes is not None and len(boxes) > 0:
                            self._process_detections(frame, boxes)
                
                time.sleep(self.settings.get("scan_interval", 0.3))
                
            except Exception as e:
                logging.error(f"خطا در حلقه تشخیص: {e}")
                time.sleep(1)
        
        logging.info("حلقه تشخیص متوقف شد.")
    
    def _process_detections(self, frame, boxes):
        import cv2
        import numpy as np
        
        try:
            if hasattr(boxes, 'id') and boxes.id is not None:
                track_ids = boxes.id.cpu().numpy() if hasattr(boxes.id, 'cpu') else boxes.id.numpy()
            else:
                track_ids = np.array([-1] * len(boxes))
            
            confidences = boxes.conf.cpu().numpy() if hasattr(boxes.conf, 'cpu') else boxes.conf.numpy()
            xyxy = boxes.xyxy.cpu().numpy() if hasattr(boxes.xyxy, 'cpu') else boxes.xyxy.numpy()
            
            current_time = time.time()
            
            for i, track_id in enumerate(track_ids):
                track_id = int(track_id)
                confidence = float(confidences[i]) if i < len(confidences) else 0
                x1, y1, x2, y2 = map(int, xyxy[i])
                
                if track_id < 0:
                    track_id = i + 1000
                
                if track_id in self.tracked_cooldown:
                    cooldown_time = self.settings.get("cooldown_seconds", 30)
                    if current_time - self.tracked_cooldown[track_id] < cooldown_time:
                        continue
                
                if track_id not in self.tracked_frames:
                    self.tracked_frames[track_id] = 1
                    self.tracked_known[track_id] = False
                else:
                    self.tracked_frames[track_id] += 1
                
                confirm_frames = self.settings.get("confirm_frames", 3)
                if self.tracked_frames[track_id] >= confirm_frames and not self.tracked_known[track_id]:
                    self.tracked_known[track_id] = True
                    
                    face_crop = frame[y1:y2, x1:x2]
                    if face_crop.size > 0:
                        name, status, face_confidence = self._recognize_face(face_crop)
                        
                        event_image_path = self._save_event_image(frame, x1, y1, x2, y2, name)
                        
                        self.event_manager.add_event(
                            name=name,
                            status=status,
                            confidence=face_confidence,
                            image_path=str(event_image_path)
                        )
                        
                        self._send_telegram_alert(frame, x1, y1, x2, y2, name, status, face_confidence, confidence)
                        
                        self.tracked_cooldown[track_id] = current_time
                        self.tracked_names[track_id] = name
                    
                    self.tracked_frames[track_id] = 0
            
            current_track_ids = set(int(t) for t in track_ids)
            for tid in list(self.tracked_frames.keys()):
                if tid not in current_track_ids:
                    if self.tracked_frames[tid] < 3:
                        self.tracked_frames.pop(tid, None)
                        self.tracked_known.pop(tid, None)
                    else:
                        if not self.tracked_known.get(tid, False):
                            self.tracked_frames[tid] = 0
        
        except Exception as e:
            logging.error(f"خطا در پردازش تشخیص‌ها: {e}")
    
    def _recognize_face(self, face_crop) -> Tuple[str, str, float]:
        try:
            embedding = self.face_recognizer.extract_embedding_from_frame(None, face_crop)
            if embedding is None:
                return "ناشناس", "unknown", 0.0
            
            threshold = self.settings.get("face_threshold", 0.45)
            person, distance = self.people_manager.find_best_match(embedding, threshold)
            
            if person is not None:
                confidence = (1 - distance) * 100
                return person.name, "known", confidence
            else:
                confidence = (1 - distance) * 100
                return "ناشناس", "unknown", max(0, min(100, confidence))
        
        except Exception as e:
            logging.error(f"خطا در تشخیص چهره: {e}")
            return "ناشناس", "unknown", 0.0
    
    def _save_event_image(self, frame, x1, y1, x2, y2, name: str) -> Path:
        import cv2
        
        try:
            img = frame.copy()
            
            color = (0, 255, 0) if name != "ناشناس" else (0, 0, 255)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            
            label = f"{name}" if name != "ناشناس" else "⚠️ Unknown"
            cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"event_{timestamp}.jpg"
            filepath = EVENTS_DIR / filename
            cv2.imwrite(str(filepath), img)
            
            return filepath
        except Exception as e:
            logging.error(f"خطا در ذخیره عکس رویداد: {e}")
            return Path("")
    
    def _send_telegram_alert(self, frame, x1, y1, x2, y2, name: str, status: str, face_confidence: float, person_confidence: float):
        try:
            if self.bot is None:
                return
            
            import cv2
            img = frame.copy()
            color = (0, 255, 0) if status == "known" else (0, 0, 255)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            label = f"{name}" if status == "known" else "⚠️ Unknown"
            cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                temp_path = f.name
                cv2.imwrite(temp_path, img)
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if status == "known":
                caption = (
                    f"👤 {name} شناسایی شد\n"
                    f"🎯 اعتماد تشخیص شخص: {person_confidence*100:.1f}%\n"
                    f"🎯 تطابق چهره: {face_confidence:.1f}%\n"
                    f"🕐 زمان: {timestamp}"
                )
            else:
                caption = (
                    f"⚠️ فرد ناشناس شناسایی شد\n"
                    f"🎯 اعتماد تشخیص شخص: {person_confidence*100:.1f}%\n"
                    f"🕐 زمان: {timestamp}"
                )
            
            with open(temp_path, 'rb') as photo:
                self.bot.send_photo(
                    ADMIN_CHAT_ID,
                    photo,
                    caption=caption,
                    parse_mode='HTML'
                )
            
            try:
                os.unlink(temp_path)
            except:
                pass
            
        except Exception as e:
            logging.error(f"خطا در ارسال هشدار تلگرام: {e}")
    
    def get_status(self) -> dict:
        status = {
            "camera": "روشن" if self.is_camera_on else "خاموش",
            "people_count": self.people_manager.get_people_count(),
            "events_count": len(self.event_manager.events),
            "settings": self.settings
        }
        return status


class TelegramBot:
    def __init__(self, system):
        self.system = system
        self.bot = None
        self.pending_people = {}
        self._init_bot()
        self.is_running = False
        self.bot_thread = None
        self.stop_event = threading.Event()
    
    def _init_bot(self):
        try:
            import telebot
            if BOT_TOKEN == "YOUR_BOT_TOKEN":
                print("⚠️ لطفاً BOT_TOKEN را در فایل تنظیم کنید.")
                return
            
            self.bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')
            
            # ثبت handlerها
            self._register_handlers()
            
            print("✅ ربات تلگرام آماده شد.")
        except Exception as e:
            logging.error(f"خطا در راه‌اندازی ربات: {e}")
            self.bot = None
    
    def _register_handlers(self):
        if self.bot is None:
            return
        
        @self.bot.message_handler(commands=['start'])
        def start_command(message):
            if message.chat.id != ADMIN_CHAT_ID:
                self.bot.reply_to(message, "⛔ شما دسترسی مدیریت ندارید.")
                return
            self._handle_start(message)
        
        @self.bot.message_handler(commands=['status'])
        def status_command(message):
            if message.chat.id != ADMIN_CHAT_ID:
                self.bot.reply_to(message, "⛔ شما دسترسی مدیریت ندارید.")
                return
            self._handle_status(message)
        
        @self.bot.message_handler(commands=['camera_on'])
        def camera_on_command(message):
            if message.chat.id != ADMIN_CHAT_ID:
                self.bot.reply_to(message, "⛔ شما دسترسی مدیریت ندارید.")
                return
            self._handle_camera_on(message)
        
        @self.bot.message_handler(commands=['camera_off'])
        def camera_off_command(message):
            if message.chat.id != ADMIN_CHAT_ID:
                self.bot.reply_to(message, "⛔ شما دسترسی مدیریت ندارید.")
                return
            self._handle_camera_off(message)
        
        @self.bot.message_handler(commands=['addperson'])
        def addperson_command(message):
            if message.chat.id != ADMIN_CHAT_ID:
                self.bot.reply_to(message, "⛔ شما دسترسی مدیریت ندارید.")
                return
            self._handle_addperson(message)
        
        @self.bot.message_handler(commands=['list'])
        def list_command(message):
            if message.chat.id != ADMIN_CHAT_ID:
                self.bot.reply_to(message, "⛔ شما دسترسی مدیریت ندارید.")
                return
            self._handle_list(message)
        
        @self.bot.message_handler(commands=['deleteperson'])
        def deleteperson_command(message):
            if message.chat.id != ADMIN_CHAT_ID:
                self.bot.reply_to(message, "⛔ شما دسترسی مدیریت ندارید.")
                return
            self._handle_deleteperson(message)
        
        @self.bot.message_handler(commands=['events'])
        def events_command(message):
            if message.chat.id != ADMIN_CHAT_ID:
                self.bot.reply_to(message, "⛔ شما دسترسی مدیریت ندارید.")
                return
            self._handle_events(message)
        
        @self.bot.message_handler(commands=['settings'])
        def settings_command(message):
            if message.chat.id != ADMIN_CHAT_ID:
                self.bot.reply_to(message, "⛔ شما دسترسی مدیریت ندارید.")
                return
            self._handle_settings(message)
        
        @self.bot.message_handler(commands=['help'])
        def help_command(message):
            if message.chat.id != ADMIN_CHAT_ID:
                self.bot.reply_to(message, "⛔ شما دسترسی مدیریت ندارید.")
                return
            self._handle_help(message)
        
        @self.bot.message_handler(content_types=['photo'])
        def photo_handler(message):
            if message.chat.id != ADMIN_CHAT_ID:
                self.bot.reply_to(message, "⛔ شما دسترسی مدیریت ندارید.")
                return
            self._handle_photo(message)
        
        @self.bot.message_handler(func=lambda message: True, content_types=['text'])
        def text_handler(message):
            if message.chat.id != ADMIN_CHAT_ID:
                return
            self._handle_text(message)
        
        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_handler(call):
            if call.message.chat.id != ADMIN_CHAT_ID:
                self.bot.answer_callback_query(call.id, "⛔ شما دسترسی مدیریت ندارید.")
                return
            self._handle_callback(call)
    
    def _handle_start(self, message):
        status = self.system.get_status()
        camera_status = "✅ روشن" if status["camera"] == "روشن" else "❌ خاموش"
        
        text = (
            "🤖 <b>سیستم نظارت تصویری</b>\n\n"
            f"📷 دوربین: {camera_status}\n"
            f"👥 افراد ثبت‌شده: {status['people_count']}\n"
            f"📋 رویدادها: {status['events_count']}\n\n"
            "دستورات:\n"
            "/status - وضعیت سیستم\n"
            "/camera_on - روشن کردن دوربین\n"
            "/camera_off - خاموش کردن دوربین\n"
            "/addperson - ثبت شخص جدید\n"
            "/list - لیست افراد\n"
            "/deleteperson - حذف شخص\n"
            "/events - رویدادهای اخیر\n"
            "/settings - تنظیمات\n"
            "/help - راهنما"
        )
        self.bot.reply_to(message, text, parse_mode='HTML')
    
    def _handle_status(self, message):
        status = self.system.get_status()
        settings = status["settings"]
        
        text = (
            "<b>📊 وضعیت سیستم</b>\n\n"
            f"📷 دوربین: {status['camera']}\n"
            f"👥 افراد ثبت‌شده: {status['people_count']}\n"
            f"📋 رویدادها: {status['events_count']}\n\n"
            "<b>⚙️ تنظیمات:</b>\n"
            f"▪️ حداقل اطمینان شخص: {settings['person_confidence']}\n"
            f"▪️ آستانه تشخیص چهره: {settings['face_threshold']}\n"
            f"▪️ فریم‌های تأیید: {settings['confirm_frames']}\n"
            f"▪️ زمان خنک‌سازی: {settings['cooldown_seconds']} ثانیه\n"
            f"▪️ فاصله اسکن: {settings['scan_interval']} ثانیه\n"
            f"▪️ ROI: {'فعال' if settings['roi_enabled'] else 'غیرفعال'}"
        )
        self.bot.reply_to(message, text, parse_mode='HTML')
    
    def _handle_camera_on(self, message):
        success, msg = self.system.start_camera()
        self.bot.reply_to(message, msg)
    
    def _handle_camera_off(self, message):
        success, msg = self.system.stop_camera()
        self.bot.reply_to(message, msg)
    
    def _handle_addperson(self, message):
        self.bot.reply_to(message, "👤 لطفاً عکس شخص را ارسال کنید.\n(تصویر باید واضح و فقط شامل یک چهره باشد)")
    
    def _handle_photo(self, message):
        try:
            file_id = message.photo[-1].file_id
            file_info = self.bot.get_file(file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                temp_path = f.name
                f.write(downloaded_file)
            
            face_recognizer = self.system.face_recognizer
            embedding = face_recognizer.extract_embedding(temp_path)
            
            if embedding is None:
                self.bot.reply_to(message, "❌ چهره‌ای در تصویر پیدا نشد.\nلطفاً عکس واضح‌تری ارسال کنید.")
                try:
                    os.unlink(temp_path)
                except:
                    pass
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            face_filename = f"face_{timestamp}.jpg"
            face_path = FACES_DIR / face_filename
            shutil.copy2(temp_path, face_path)
            
            self.bot.reply_to(
                message,
                "✅ چهره شناسایی شد.\n"
                "لطفاً نام شخص را وارد کنید:"
            )
            
            self.pending_people[message.chat.id] = {
                'temp_path': temp_path,
                'face_path': str(face_path),
                'embedding': embedding
            }
            
        except Exception as e:
            logging.error(f"خطا در پردازش عکس: {e}")
            self.bot.reply_to(message, f"❌ خطا در پردازش عکس: {e}")
    
    def _handle_text(self, message):
        try:
            if message.chat.id in self.pending_people:
                data = self.pending_people.pop(message.chat.id)
                name = message.text.strip()
                
                if not name:
                    self.bot.reply_to(message, "❌ نام نمی‌تواند خالی باشد.")
                    return
                
                person = self.system.people_manager.add_person(
                    name=name,
                    image_path=data['face_path'],
                    embedding=data['embedding']
                )
                
                try:
                    os.unlink(data['temp_path'])
                except:
                    pass
                
                self.bot.reply_to(
                    message,
                    f"✅ {name} با موفقیت ثبت شد.\n"
                    f"🆔 شناسه: {person.id}"
                )
        except Exception as e:
            logging.error(f"خطا در پردازش متن: {e}")
            self.bot.reply_to(message, f"❌ خطا: {e}")
    
    def _handle_list(self, message):
        people = self.system.people_manager.get_people()
        if not people:
            self.bot.reply_to(message, "👥 هیچ شخصی ثبت نشده است.")
            return
        
        text = "👥 <b>افراد ثبت‌شده:</b>\n\n"
        for person in people:
            text += f"{person.id}. {person.name}\n"
        
        self.bot.reply_to(message, text, parse_mode='HTML')
    
    def _handle_deleteperson(self, message):
        people = self.system.people_manager.get_people()
        if not people:
            self.bot.reply_to(message, "👥 هیچ شخصی ثبت نشده است.")
            return
        
        import telebot
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        
        for person in people:
            button = telebot.types.InlineKeyboardButton(
                f"🗑 {person.name}",
                callback_data=f"delete_{person.id}"
            )
            markup.add(button)
        
        self.bot.reply_to(
            message,
            "🗑 لطفاً شخص مورد نظر را انتخاب کنید:",
            reply_markup=markup
        )
    
    def _handle_callback(self, call):
        try:
            if call.data.startswith("delete_"):
                person_id = int(call.data.split("_")[1])
                person = self.system.people_manager.get_person(person_id)
                
                if person is None:
                    self.bot.answer_callback_query(call.id, "❌ شخص یافت نشد.")
                    return
                
                success = self.system.people_manager.delete_person(person_id)
                
                if success:
                    self.bot.edit_message_text(
                        f"✅ {person.name} با موفقیت حذف شد.",
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id
                    )
                    self.bot.answer_callback_query(call.id, "✅ حذف شد")
                else:
                    self.bot.answer_callback_query(call.id, "❌ خطا در حذف")
            
        except Exception as e:
            logging.error(f"خطا در callback: {e}")
            self.bot.answer_callback_query(call.id, f"❌ خطا: {e}")
    
    def _handle_events(self, message):
        events = self.system.event_manager.get_events(limit=10)
        if not events:
            self.bot.reply_to(message, "📋 هیچ رویدادی ثبت نشده است.")
            return
        
        text = "📋 <b>آخرین رویدادها:</b>\n\n"
        for event in events:
            status_emoji = "👤" if event.status == "known" else "⚠️"
            text += f"{status_emoji} {event.name}\n"
            text += f"🕐 {event.timestamp}\n"
            text += f"📊 اعتماد: {event.confidence:.1f}%\n\n"
        
        self.bot.reply_to(message, text, parse_mode='HTML')
    
    def _handle_settings(self, message):
        settings = self.system.settings
        
        text = (
            "<b>⚙️ تنظیمات فعلی</b>\n\n"
            f"▪️ دوربین: {settings.get('camera_index', 0)}\n"
            f"▪️ رزولوشن: {settings.get('camera_width', 640)}x{settings.get('camera_height', 480)}\n"
            f"▪️ حداقل اطمینان شخص: {settings.get('person_confidence', 0.55)}\n"
            f"▪️ آستانه تشخیص چهره: {settings.get('face_threshold', 0.45)}\n"
            f"▪️ فریم‌های تأیید: {settings.get('confirm_frames', 3)}\n"
            f"▪️ زمان خنک‌سازی: {settings.get('cooldown_seconds', 30)} ثانیه\n"
            f"▪️ فاصله اسکن: {settings.get('scan_interval', 0.3)} ثانیه\n"
            f"▪️ تخمین قد: {'فعال' if settings.get('height_estimation_enabled', False) else 'غیرفعال'}\n"
            f"▪️ ROI: {'فعال' if settings.get('roi_enabled', False) else 'غیرفعال'}"
        )
        self.bot.reply_to(message, text, parse_mode='HTML')
    
    def _handle_help(self, message):
        text = (
            "🤖 <b>راهنمای ربات</b>\n\n"
            "/start - منوی اصلی\n"
            "/status - وضعیت سیستم\n"
            "/camera_on - روشن کردن دوربین\n"
            "/camera_off - خاموش کردن دوربین\n"
            "/addperson - ثبت شخص جدید\n"
            "/list - لیست افراد\n"
            "/deleteperson - حذف شخص\n"
            "/events - رویدادهای اخیر\n"
            "/settings - تنظیمات\n"
            "/help - این راهنما"
        )
        self.bot.reply_to(message, text, parse_mode='HTML')
    
    def start(self):
        if self.bot is None:
            print("❌ ربات راه‌اندازی نشد.")
            return
        
        self.is_running = True
        self.stop_event.clear()
        
        self.bot_thread = threading.Thread(target=self._bot_loop, daemon=True)
        self.bot_thread.start()
        
        print("✅ ربات تلگرام در حال اجرا است...")
    
    def _bot_loop(self):
        try:
            self.bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            logging.error(f"خطا در حلقه ربات: {e}")
        finally:
            self.is_running = False
    
    def stop(self):
        self.is_running = False
        self.stop_event.set()
        
        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=3)
        
        if self.bot:
            try:
                self.bot.stop_polling()
            except:
                pass
        
        logging.info("ربات تلگرام متوقف شد.")

# ============================================================
# تابع اصلی
# ============================================================

def main():
    print("=" * 50)
    print("🤖 سیستم نظارت تصویری با Telegram Bot")
    print("=" * 50)
    
    check_python_version()
    check_and_install_packages()
    create_directories()
    init_json_files()
    
    system = SurveillanceSystem(None)
    bot = TelegramBot(system)
    system.bot = bot.bot
    
    bot.start()
    
    print('ok')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹ در حال توقف برنامه...")
        system.stop_camera()
        bot.stop()
        print("✅ برنامه متوقف شد.")
        sys.exit(0)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    main()
