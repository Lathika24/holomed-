"""Main application window"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QSplitter, QStatusBar, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QAction
import sys
from pathlib import Path
import tempfile
import threading

from api_client import APIClient
from auth_window import AuthWindow
from model_manager import ModelManager
from viewer_window import ViewerWindow
from config import Config

# Lazy import HandTrackerThread to avoid MediaPipe/TensorFlow import issues
def get_hand_tracker_thread():
    """Get HandTrackerThread class, returns None if MediaPipe unavailable"""
    try:
        from viewer_window import HandTrackerThread
        return HandTrackerThread
    except Exception:
        return None

class ViewerThread(QThread):
    """Thread to run the PyVista viewer"""
    finished = pyqtSignal()
    
    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer
    
    def run(self):
        try:
            self.viewer.show()
        except Exception as e:
            print(f"Viewer error: {e}")
        finally:
            self.finished.emit()

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.api_client = APIClient(Config.API_BASE_URL)
        self.current_username = None
        self.current_token = None
        self.viewer = None
        self.tracker_thread = None
        self.viewer_thread = None
        self.selected_model_id = None
        self.setup_ui()
        self.show_auth()
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle(f"{Config.APP_NAME} v{Config.APP_VERSION}")
        self.setGeometry(100, 100, Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
        
        # Menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        logout_action = QAction("Logout", self)
        logout_action.triggered.connect(self.logout)
        file_menu.addAction(logout_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        open_viewer_action = QAction("Open 3D Viewer", self)
        open_viewer_action.setShortcut("Ctrl+V")
        open_viewer_action.triggered.connect(self.open_viewer)
        view_menu.addAction(open_viewer_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Central widget
        central = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Welcome label
        self.welcome_label = QLabel("Welcome to HoloMed Desktop")
        welcome_font = QFont()
        welcome_font.setPointSize(16)
        welcome_font.setBold(True)
        self.welcome_label.setFont(welcome_font)
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setStyleSheet("padding: 10px;")
        layout.addWidget(self.welcome_label)
        
        # Splitter for model manager
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Model manager
        self.model_manager = ModelManager(self.api_client)
        self.model_manager.model_selected.connect(self.on_model_selected)
        splitter.addWidget(self.model_manager)
        
        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)
        right_layout.setContentsMargins(15, 15, 15, 15)
        
        info_label = QLabel("Model Viewer")
        info_font = QFont()
        info_font.setPointSize(12)
        info_font.setBold(True)
        info_label.setFont(info_font)
        right_layout.addWidget(info_label)
        
        instructions = QTextEdit()
        instructions.setReadOnly(True)
        instructions.setMaximumHeight(200)
        instructions.setText("""
<b>Instructions:</b><br><br>
1. Select a model from the list<br>
2. Click "View Selected Model" to open the 3D viewer<br><br>
<b>Hand Controls:</b><br>
• <b>Rotate:</b> Pinch thumb and index finger together and move your hand<br>
• <b>Zoom:</b> Use two hands - bring together to zoom in, apart to zoom out<br><br>
<b>Note:</b> A separate window will open for the 3D visualization. Make sure your camera is connected.
        """)
        instructions.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 5px; padding: 10px;")
        right_layout.addWidget(instructions)
        
        self.view_btn = QPushButton("View Selected Model")
        self.view_btn.setMinimumHeight(40)
        self.view_btn.setEnabled(False)
        self.view_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
        """)
        self.view_btn.clicked.connect(self.open_viewer)
        right_layout.addWidget(self.view_btn)
        
        right_layout.addStretch()
        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([800, 400])
        
        layout.addWidget(splitter)
        central.setLayout(layout)
        self.setCentralWidget(central)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def show_auth(self):
        """Show authentication dialog"""
        auth_dialog = AuthWindow(self.api_client, self)
        auth_dialog.authenticated.connect(self.on_authenticated)
        result = auth_dialog.exec()
        
        # If user closed dialog without logging in, close app
        if result == 0 and not self.current_token:
            self.close()
    
    def on_authenticated(self, username: str, token: str):
        """Handle successful authentication"""
        self.current_username = username
        self.current_token = token
        self.api_client.set_token(token)
        self.welcome_label.setText(f"Welcome, {username}!")
        self.statusBar().showMessage(f"Logged in as {username}")
    
    def on_model_selected(self, model_id: str):
        """Handle model selection"""
        self.selected_model_id = model_id
        self.view_btn.setEnabled(True)
        self.statusBar().showMessage(f"Model selected")
    
    def open_viewer(self):
        """Open 3D viewer window"""
        if not self.selected_model_id:
            QMessageBox.warning(self, "Error", "Please select a model first")
            return
        
        # Check if viewer is already open
        if self.viewer and self.viewer.running:
            QMessageBox.information(
                self, "Viewer Already Open",
                "The 3D viewer is already running.\nPlease close it first."
            )
            return
        
        try:
            # Get model info
            self.statusBar().showMessage("Loading model...")
            model_info = None
            for model in self.api_client.get_models():
                if model['id'] == self.selected_model_id:
                    model_info = model
                    break
            
            if not model_info:
                QMessageBox.warning(self, "Error", "Model not found")
                return
            
            # Download model to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{model_info.get('file_format', 'stl')}") as tmp:
                tmp_path = tmp.name
            
            self.statusBar().showMessage("Downloading model...")
            try:
                self.api_client.download_model_file(model_info, tmp_path)
            except Exception as e:
                QMessageBox.critical(
                    self, "Download Error",
                    f"Failed to download model:\n{str(e)}\n\n"
                    "Make sure the backend server is running and the file exists."
                )
                return
            
            self.statusBar().showMessage("Initializing viewer...")
            
            # Create viewer
            self.viewer = ViewerWindow(tmp_path)
            self.viewer.setup_scene()
            
            # Start hand tracking
            try:
                HandTrackerThread = get_hand_tracker_thread()
                if HandTrackerThread is None:
                    raise Exception("MediaPipe/TensorFlow not available")
                
                self.tracker_thread = HandTrackerThread()
                self.tracker_thread.frame_ready.connect(self.viewer.update_frame)
                self.tracker_thread.gesture_detected.connect(
                    lambda rot, scale: (
                        self.viewer.update_rotation(rot),
                        self.viewer.update_scale(scale)
                    )
                )
                self.tracker_thread.start_tracking()
            except Exception as e:
                QMessageBox.warning(
                    self, "Hand Tracking Unavailable",
                    f"Hand tracking is not available:\n{str(e)}\n\n"
                    "The viewer will open without hand tracking.\n"
                    "You can still interact with the model using mouse controls."
                )
            
            # Show viewer in separate thread
            self.viewer_thread = ViewerThread(self.viewer)
            self.viewer_thread.finished.connect(self.on_viewer_closed)
            self.viewer_thread.start()
            
            self.statusBar().showMessage("Viewer opened - check for separate window")
            
            QMessageBox.information(
                self, "Viewer Opened",
                "The 3D viewer has been opened in a separate window.\n\n"
                "Controls:\n"
                "• Pinch thumb and index finger to rotate\n"
                "• Use two hands to zoom in/out\n\n"
                "Close the viewer window when done."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open viewer:\n{str(e)}")
            self.statusBar().showMessage("Error opening viewer")
    
    def on_viewer_closed(self):
        """Handle viewer window closing"""
        if self.tracker_thread:
            self.tracker_thread.stop_tracking()
            self.tracker_thread = None
        self.viewer = None
        self.viewer_thread = None
        self.statusBar().showMessage("Viewer closed")
    
    def logout(self):
        """Logout user"""
        reply = QMessageBox.question(
            self, "Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Close viewer if open
            if self.viewer and self.viewer.running:
                self.viewer.close()
                self.on_viewer_closed()
            
            self.current_username = None
            self.current_token = None
            self.api_client.set_token(None)
            self.welcome_label.setText("Welcome to HoloMed Desktop")
            self.statusBar().showMessage("Logged out")
            self.selected_model_id = None
            self.view_btn.setEnabled(False)
            self.model_manager.refresh_models()
            self.show_auth()
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About HoloMed",
            f"<b>{Config.APP_NAME} v{Config.APP_VERSION}</b><br><br>"
            "Holographic Medical Visualization<br>"
            "with Hand Tracking Control<br><br>"
            "© 2024 HoloMed<br><br>"
            "Built with PyQt6, PyVista, and MediaPipe"
        )
    
    def closeEvent(self, event):
        """Handle window close"""
        if self.viewer and self.viewer.running:
            self.viewer.close()
        if self.tracker_thread:
            self.tracker_thread.stop_tracking()
        event.accept()
