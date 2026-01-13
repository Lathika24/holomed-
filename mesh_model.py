import cv2
import mediapipe as mp
import pyvista as pv
import numpy as np
import threading
import time

class HandTracker(threading.Thread):
    def __init__(self, shared_state: dict):
        super().__init__(daemon=True)
        self.shared_state = shared_state
        self.running = True
        self.cap = cv2.VideoCapture(0)
        
        # Optimize MediaPipe for speed
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            model_complexity=0,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )

        self.prev_pinch_pos = None

    def run(self):
        while self.running:
            success, frame = self.cap.read()
            if not success: continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)

            # Draw landmarks for the HUD
            if results.multi_hand_landmarks:
                for landmarks in results.multi_hand_landmarks:
                    mp.solutions.drawing_utils.draw_landmarks(
                        rgb, landmarks, self.mp_hands.HAND_CONNECTIONS)
            
            self._calculate_gestures(results)

            with self.shared_state['lock']:
                self.shared_state['video_frame'] = rgb
                self.shared_state['updated'] = True

    def _calculate_gestures(self, results):
        if not results.multi_hand_landmarks:
            with self.shared_state['lock']:
                self.shared_state['rotation_delta'] = (0, 0)
                self.prev_pinch_pos = None
            return

        # Gesture 1: Rotation (Pinch)
        hand = results.multi_hand_landmarks[0]
        thumb = hand.landmark[4]
        index = hand.landmark[8]
        
        dist = np.linalg.norm([thumb.x - index.x, thumb.y - index.y])
        
        with self.shared_state['lock']:
            if dist < 0.05: # Pinch detected
                current_pos = np.array([index.x, index.y])
                if self.prev_pinch_pos is not None:
                    delta = (current_pos - self.prev_pinch_pos) * 150 # Sensitivity
                    self.shared_state['rotation_delta'] = (delta[1], delta[0])
                self.prev_pinch_pos = current_pos
            else:
                self.shared_state['rotation_delta'] = (0, 0)
                self.prev_pinch_pos = None

        # Gesture 2: Zoom (Two Hands)
        if len(results.multi_hand_landmarks) > 1:
            h1 = results.multi_hand_landmarks[0].landmark[8]
            h2 = results.multi_hand_landmarks[1].landmark[8]
            dist = np.linalg.norm([h1.x - h2.x, h1.y - h2.y])
            with self.shared_state['lock']:
                # Simple exponential scaling
                self.shared_state['current_scale'] = np.clip(dist * 2.5, 0.2, 3.0)

class HoloMedVisualizer:
    def __init__(self):
        self.shared_state = {
            'video_frame': None,
            'rotation_delta': (0, 0),
            'current_scale': 1.0,
            'lock': threading.Lock(),
            'updated': False
        }
        
        self.plotter = pv.Plotter()
        self.plotter.set_background('black')
        # --- CAMERA SETUP FOR LIVE VIDEO BACKGROUND ---
        # self.plotter.enable_parallel_projection()

        self.plotter.camera.position = (0, 0, 5)
        self.plotter.camera.focal_point = (0, 0, 0)
        self.plotter.camera.up = (0, 1, 0)


        # Disable mouse-based interaction (gesture-only control)
        self.plotter.disable()

        
        # Load Mesh
        self.base_mesh = pv.examples.download_brain()
        self.display_mesh = self.base_mesh.copy()

        self.display_mesh.scale(0.7, inplace=True)

        
        # Add Actor once
        self.actor = self.plotter.add_mesh(
            self.display_mesh, 
            color='cyan', 
            opacity=0.7, 
            smooth_shading=True,
            show_edges=True,
            edge_color='#004444'
        )

        # Setup Video Plane
        self.bg_plane = pv.Plane(
            center=(0, 0, -3),   # far behind the brain
            direction=(0, 0, 1),
            i_size=10,
            j_size=7
        )
        self.bg_actor = None

        self.tracker = HandTracker(self.shared_state)
        self.rot_x, self.rot_y = 0, 0
        self.frame_counter = 0


    def start(self):
        self.tracker.start()
        # Non-blocking render loop
        self.plotter.show(interactive_update=True)
        
        while self.plotter.iren.initialized:
            self.update()
            self.plotter.update()
            time.sleep(0.04)  # ~25 FPS


    def update(self):
        with self.shared_state['lock']:
            frame = self.shared_state['video_frame']
            rot_delta = self.shared_state['rotation_delta']
            scale = self.shared_state['current_scale']
            new_data = self.shared_state['updated']
            self.shared_state['updated'] = False

    # -------------------------------
    # Update live camera background
    # -------------------------------
        self.frame_counter += 1
        if frame is not None and new_data and self.frame_counter % 2 == 0:

            tex = pv.numpy_to_texture(np.flipud(frame))

            if self.bg_actor is None:
                self.bg_actor = self.plotter.add_mesh(
                    self.bg_plane,
                    texture=tex,
                    lighting=False
                )
            else:
                self.bg_actor.texture = tex

        # -------------------------------
        # Update 3D model using gestures
        # -------------------------------
        if rot_delta != (0, 0) or scale != 1.0:
            self.rot_x += rot_delta[0]
            self.rot_y += rot_delta[1]

            self.actor.SetOrientation(self.rot_x, self.rot_y, 0)
            self.actor.SetScale(scale)




if __name__ == "__main__":
    HoloMedVisualizer().start()