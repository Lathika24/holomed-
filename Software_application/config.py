"""Configuration settings for the desktop application"""

import os

class Config:
    # API Configuration
    API_BASE_URL = os.getenv("HOLOMED_API_URL", "http://localhost:8000")
    API_TIMEOUT = 30
    
    # Application Settings
    APP_NAME = "HoloMed Desktop"
    APP_VERSION = "1.0.0"
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    
    # Model Settings
    SUPPORTED_FORMATS = [".stl", ".obj", ".ply", ".vtk", ".gltf", ".glb"]
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    # Hand Tracking Settings
    PINCH_THRESHOLD = 0.05
    ROTATION_SENSITIVITY = 120
    SCALE_SENSITIVITY = 1.5
    TARGET_FPS = 30
    CAMERA_INDEX = 0
    
    # Visualization Settings
    HOLO_COLOR = "cyan"
    HOLO_EDGE_COLOR = "white"
    BG_DISTANCE = 20.0  # How far back the camera plane sits
