"""3D visualization window with hand tracking"""

import cv2
import pyvista as pv
import numpy as np
import threading
import time
from typing import Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from config import Config

# Lazy import for MediaPipe to avoid TensorFlow DLL issues on Windows
_mediapipe_available = None
_mp = None

def _get_mediapipe():
    """Lazy import MediaPipe, return None if unavailable"""
    global _mediapipe_available, _mp
    if _mediapipe_available is None:
        try:
            import mediapipe as mp_module
            _mp = mp_module
            _mediapipe_available = True
        except ImportError as e:
            print(f"Warning: MediaPipe not available: {e}")
            _mediapipe_available = False
            _mp = None
    return _mp

@dataclass
class SharedState:
    """Thread-safe state for hand tracking"""
    video_frame: Optional[np.ndarray] = None
    rotation_delta: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale_factor: float = 1.0
    is_tracking: bool = False
    lock: threading.Lock = None
    new_frame_available: bool = False
    
    def __post_init__(self):
        if self.lock is None:
            self.lock = threading.Lock()

class HandTrackerThread(QThread):
    """Hand tracking in separate thread"""
    
    frame_ready = pyqtSignal(np.ndarray)
    gesture_detected = pyqtSignal(tuple, float)  # rotation_delta, scale_factor
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.cap = None
        self.hands = None
        self.last_pinch_pos = None
        self.last_pinch_dist = None
    
    def start_tracking(self):
        """Start hand tracking"""
        self.running = True
        try:
            # Lazy import MediaPipe
            mp = _get_mediapipe()
            if mp is None:
                raise Exception("MediaPipe is not available. Hand tracking disabled.")
            
            self.cap = cv2.VideoCapture(Config.CAMERA_INDEX)
            if not self.cap.isOpened():
                raise Exception("Could not open camera")
            self.hands = mp.solutions.hands.Hands(
                max_num_hands=2,
                model_complexity=0,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.7
            )
            self.start()
        except Exception as e:
            self.frame_ready.emit(None)  # Signal error
            raise
    
    def stop_tracking(self):
        """Stop hand tracking"""
        self.running = False
        if self.cap:
            self.cap.release()
        if self.hands:
            self.hands.close()
        self.wait()
    
    def run(self):
        """Main tracking loop"""
        while self.running and self.cap and self.cap.isOpened():
            success, frame = self.cap.read()
            if not success:
                time.sleep(0.1)
                continue
            
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)
            
            rot_delta = (0, 0, 0)
            scale_mult = 1.0
            
            if results.multi_hand_landmarks:
                h1 = results.multi_hand_landmarks[0]
                p1 = np.array([h1.landmark[8].x, h1.landmark[8].y])
                p2 = np.array([h1.landmark[4].x, h1.landmark[4].y])
                pinch_dist = np.linalg.norm(p1 - p2)
                
                # Pinch to rotate
                if pinch_dist < Config.PINCH_THRESHOLD:
                    center = (p1 + p2) / 2
                    if self.last_pinch_pos is not None:
                        dx = (center[0] - self.last_pinch_pos[0]) * Config.ROTATION_SENSITIVITY
                        dy = (center[1] - self.last_pinch_pos[1]) * Config.ROTATION_SENSITIVITY
                        rot_delta = (dy, dx, 0)
                    self.last_pinch_pos = center
                else:
                    self.last_pinch_pos = None
                
                # Two-hand zoom
                if len(results.multi_hand_landmarks) == 2:
                    h2 = results.multi_hand_landmarks[1]
                    h1_pos = np.array([h1.landmark[8].x, h1.landmark[8].y])
                    h2_pos = np.array([h2.landmark[8].x, h2.landmark[8].y])
                    hand_dist = np.linalg.norm(h1_pos - h2_pos)
                    
                    if self.last_pinch_dist is not None and self.last_pinch_dist > 0.01:
                        scale_mult = hand_dist / self.last_pinch_dist
                        # Clamp scale multiplier
                        scale_mult = max(0.9, min(1.1, scale_mult))
                    self.last_pinch_dist = hand_dist
                else:
                    self.last_pinch_dist = None
            else:
                self.last_pinch_pos = None
                self.last_pinch_dist = None
            
            self.frame_ready.emit(rgb)
            if rot_delta != (0, 0, 0) or scale_mult != 1.0:
                self.gesture_detected.emit(rot_delta, scale_mult)
            
            time.sleep(1.0 / Config.TARGET_FPS)

class ViewerWindow:
    """3D visualization window using PyVista"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.plotter = None
        self.mesh = None
        self.texture = None
        self.actor = None
        self.actor_inner = None
        self.actor_outer = None
        self.bg_actor = None
        self.current_rot = [0, 0, 0]
        self.current_scale = 1.0
        self.tracker = None
        self.running = False
    
    def load_model(self, model_path: str):
        """Load a 3D model with texture support"""
        self.texture = None
        
        try:
            if not model_path:
                print("No model path provided, using default brain model")
                self.mesh = pv.examples.download_brain()
            else:
                print(f"Loading model from: {model_path}")
                
                # Try to load mesh with texture support
                if model_path.lower().endswith('.obj'):
                    # OBJ files may have textures - try to load them
                    self.mesh, self.texture = self.load_obj_with_texture(model_path)
                else:
                    # For other formats, try standard loading
                    self.mesh = pv.read(model_path)
                    # Check if mesh has texture coordinates
                    if hasattr(self.mesh, 'texture_coordinates') and self.mesh.texture_coordinates is not None:
                        self.texture = self.load_texture_from_path(model_path)
            
            # Normalize
            self.mesh.translate(-np.array(self.mesh.center), inplace=True)
            if model_path and model_path.lower().endswith('.obj'):
                self.mesh.rotate_x(-90, inplace=True)
            
            bounds = self.mesh.bounds
            max_dim = max(
                bounds[1] - bounds[0],
                bounds[3] - bounds[2],
                bounds[5] - bounds[4]
            )
            if max_dim > 0:
                scale_factor = 5.0 / max_dim
                self.mesh.scale(scale_factor, inplace=True)
            
            if self.texture:
                print("✓ Model loaded with texture")
            else:
                print("✓ Model loaded successfully (no texture)")
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Falling back to default brain model")
            self.mesh = pv.examples.download_brain()
            self.texture = None
    
    def load_obj_with_texture(self, obj_path: str):
        """Loads OBJ file and attempts to load associated texture files."""
        mesh = pv.read(obj_path)
        texture = None
        
        # OBJ files often have associated .mtl files and texture images
        obj_dir = Path(obj_path).parent
        obj_name = Path(obj_path).stem
        
        # Common texture file extensions
        texture_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tga', '.tiff']
        
        # Try to find texture files in the same directory
        for ext in texture_extensions:
            # Try various naming conventions
            possible_names = [
                obj_name + ext,
                obj_name + '_texture' + ext,
                obj_name + '_diffuse' + ext,
                'texture' + ext,
                'diffuse' + ext,
            ]
            
            for tex_name in possible_names:
                tex_path = obj_dir / tex_name
                if tex_path.exists():
                    try:
                        texture = pv.read_texture(str(tex_path))
                        print(f"✓ Found texture: {tex_path}")
                        return mesh, texture
                    except Exception as e:
                        print(f"⚠️ Could not load texture {tex_path}: {e}")
                        continue
        
        # Try loading from MTL file if it exists
        mtl_path = obj_dir / (obj_name + '.mtl')
        if mtl_path.exists():
            texture = self.load_texture_from_mtl(str(mtl_path), obj_dir)
            if texture is not None:
                return mesh, texture
        
        # Check if mesh already has texture coordinates but no texture loaded
        if hasattr(mesh, 'texture_coordinates') and mesh.texture_coordinates is not None:
            # Try to find any image file in the directory
            for img_file in obj_dir.glob('*.png'):
                try:
                    texture = pv.read_texture(str(img_file))
                    print(f"✓ Found texture: {img_file}")
                    return mesh, texture
                except:
                    continue
            for img_file in obj_dir.glob('*.jpg'):
                try:
                    texture = pv.read_texture(str(img_file))
                    print(f"✓ Found texture: {img_file}")
                    return mesh, texture
                except:
                    continue
        
        return mesh, None
    
    def load_texture_from_mtl(self, mtl_path: str, obj_dir: Path):
        """Attempts to load texture referenced in MTL file."""
        try:
            with open(mtl_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Look for map_Kd (diffuse texture) or map_Ka (ambient texture)
                    if line.startswith('map_Kd') or line.startswith('map_Ka'):
                        tex_file = line.split()[-1]
                        # Handle relative paths
                        tex_path = obj_dir / tex_file
                        if tex_path.exists():
                            return pv.read_texture(str(tex_path))
                        # Try with just filename if path doesn't work
                        tex_path = obj_dir / Path(tex_file).name
                        if tex_path.exists():
                            return pv.read_texture(str(tex_path))
        except Exception as e:
            print(f"⚠️ Error reading MTL file: {e}")
        return None
    
    def load_texture_from_path(self, model_path: str):
        """Attempts to find and load texture file based on model path."""
        model_dir = Path(model_path).parent
        model_name = Path(model_path).stem
        
        texture_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tga']
        for ext in texture_extensions:
            tex_path = model_dir / (model_name + ext)
            if tex_path.exists():
                try:
                    return pv.read_texture(str(tex_path))
                except:
                    continue
        return None
    
    def setup_scene(self):
        """Setup the 3D scene"""
        if not self.mesh:
            self.load_model(self.model_path)
        
        self.plotter = pv.Plotter(window_size=(1280, 720))
        self.plotter.set_background('black')
        self.plotter.disable()
        
        if self.mesh:
            # Display model with original texture if available
            if self.texture is not None:
                # Model has texture - apply it
                self.actor = self.plotter.add_mesh(
                    self.mesh,
                    texture=self.texture,
                    style='surface',
                    show_edges=False,
                    lighting=True,
                    smooth_shading=True
                )
                print("✓ Displaying model with texture")
            else:
                # No texture - use default material or hologram style
                # Inner volume
                self.actor_inner = self.plotter.add_mesh(
                    self.mesh,
                    color=Config.HOLO_COLOR,
                    opacity=0.15,
                    style='surface',
                    lighting=False
                )
                # Outer wireframe
                self.actor_outer = self.plotter.add_mesh(
                    self.mesh,
                    color=Config.HOLO_EDGE_COLOR,
                    opacity=0.8,
                    style='wireframe',
                    lighting=False,
                    line_width=2
                )
        
        # Background plane for camera feed
        bg_plane = pv.Plane(
            center=(0, 0, -Config.BG_DISTANCE),
            direction=(0, 0, 1),
            i_size=32, j_size=18
        )
        self.bg_actor = self.plotter.add_mesh(bg_plane, lighting=False)
        
        self.plotter.camera.position = (0, 0, 10)
        self.plotter.camera.focal_point = (0, 0, 0)
        self.plotter.camera.up = (0, 1, 0)
    
    def update_frame(self, frame: np.ndarray):
        """Update background with camera frame"""
        if frame is None:
            return
        if self.bg_actor and self.plotter:
            try:
                tex = pv.numpy_to_texture(frame)
                self.bg_actor.texture = tex
            except Exception as e:
                print(f"Error updating frame: {e}")
    
    def update_rotation(self, rot_delta: Tuple[float, float, float]):
        """Update model rotation"""
        if rot_delta != (0, 0, 0):
            self.current_rot[0] += rot_delta[0]
            self.current_rot[1] += rot_delta[1]
            
            if self.actor:
                self.actor.orientation = self.current_rot
            elif self.actor_inner and self.actor_outer:
                self.actor_inner.orientation = self.current_rot
                self.actor_outer.orientation = self.current_rot
    
    def update_scale(self, scale_mult: float):
        """Update model scale"""
        if scale_mult != 1.0:
            self.current_scale *= scale_mult
            self.current_scale = max(0.2, min(self.current_scale, 5.0))
            
            if self.actor:
                self.actor.scale = [self.current_scale] * 3
            elif self.actor_inner and self.actor_outer:
                self.actor_inner.scale = [self.current_scale] * 3
                self.actor_outer.scale = [self.current_scale] * 3
    
    def show(self):
        """Show the visualization"""
        if not self.plotter:
            self.setup_scene()
        
        self.running = True
        self.plotter.show(interactive_update=True)
        
        # Update loop
        while self.running and self.plotter.iren.initialized:
            self.plotter.update()
            time.sleep(1.0 / Config.TARGET_FPS)
    
    def close(self):
        """Close the visualization"""
        self.running = False
        if self.plotter:
            try:
                self.plotter.close()
            except:
                pass
