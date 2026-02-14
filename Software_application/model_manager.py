"""Model management widget"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QLabel, QFileDialog, QMessageBox, QProgressDialog,
    QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from pathlib import Path
import logging
from config import Config

logger = logging.getLogger(__name__)

class UploadThread(QThread):
    """Thread for uploading models without blocking UI"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, api_client, file_path, name, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.file_path = file_path
        self.name = name
    
    def run(self):
        try:
            result = self.api_client.upload_model(self.file_path, self.name)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class ModelManager(QWidget):
    """Widget for managing 3D models"""
    
    model_selected = pyqtSignal(str)  # model_id
    model_uploaded = pyqtSignal()
    
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.models = []
        self.setup_ui()
        self.refresh_models()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("3D Models")
        title_font = title.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        header.addWidget(title)
        header.addStretch()
        
        # Buttons
        self.upload_btn = QPushButton("Upload Model")
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.upload_btn.clicked.connect(self.upload_model)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_models)
        
        header.addWidget(self.upload_btn)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)
        
        # Model list
        self.model_list = QListWidget()
        self.model_list.itemDoubleClicked.connect(self.on_model_selected)
        self.model_list.itemClicked.connect(self.on_model_clicked)
        self.model_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidgetItem {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidgetItem:hover {
                background-color: #f0f0f0;
            }
            QListWidgetItem:selected {
                background-color: #0078d4;
                color: white;
            }
        """)
        layout.addWidget(self.model_list)
        
        # Delete button
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_selected)
        layout.addWidget(self.delete_btn)
        
        # Add keyboard shortcuts
        self.upload_btn.setShortcut("Ctrl+U")
        self.refresh_btn.setShortcut("F5")
        self.delete_btn.setShortcut("Delete")
        
        self.setLayout(layout)
    
    def refresh_models(self):
        """Refresh the model list from API"""
        try:
            logger.info("Refreshing model list")
            self.models = self.api_client.get_models()
            self.model_list.clear()
            
            if not self.models:
                item = QListWidgetItem("No models yet. Click 'Upload Model' to add one.")
                item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make it non-selectable
                self.model_list.addItem(item)
            else:
                for model in self.models:
                    # Format file size
                    file_size = model.get('file_size', 0)
                    size_str = f"{file_size / (1024*1024):.2f} MB" if file_size > 0 else "Unknown size"
                    
                    # Get upload date if available
                    upload_date = model.get('created_at', '')
                    if upload_date:
                        try:
                            from datetime import datetime
                            # Parse ISO format date
                            dt = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                            date_str = dt.strftime('%Y-%m-%d')
                        except:
                            date_str = ''
                    else:
                        date_str = ''
                    
                    item_text = f"{model['name']} ({model.get('file_format', 'unknown').upper()}) - {size_str}"
                    if date_str:
                        item_text += f" - {date_str}"
                    
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.ItemDataRole.UserRole, model['id'])
                    
                    # Add tooltip with more details
                    tooltip = f"Name: {model['name']}\n"
                    tooltip += f"Format: {model.get('file_format', 'unknown').upper()}\n"
                    tooltip += f"Size: {size_str}\n"
                    if upload_date:
                        tooltip += f"Uploaded: {date_str}\n"
                    tooltip += f"ID: {model['id']}"
                    item.setToolTip(tooltip)
                    
                    self.model_list.addItem(item)
            logger.info(f"Loaded {len(self.models)} models")
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load models:\n{str(e)}")
    
    def upload_model(self):
        """Upload a new 3D model"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select 3D Model",
            "",
            "3D Models (*.stl *.obj *.ply *.vtk *.gltf *.glb);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        # Check file size
        file_size = Path(file_path).stat().st_size
        if file_size > Config.MAX_FILE_SIZE:
            QMessageBox.warning(
                self, "Error",
                f"File too large.\nMaximum size: {Config.MAX_FILE_SIZE / (1024*1024):.0f}MB\n"
                f"Your file: {file_size / (1024*1024):.2f}MB"
            )
            return
        
        # Get model name (optional, defaults to filename)
        name, ok = QInputDialog.getText(
            self, "Model Name", "Enter a name for this model (optional):",
            text=Path(file_path).stem
        )
        
        if not ok:
            return
        
        if not name.strip():
            name = Path(file_path).name
        
        # Disable upload button during upload
        self.upload_btn.setEnabled(False)
        self.upload_btn.setText("Uploading...")
        
        # Show progress dialog
        self.progress_dialog = QProgressDialog("Uploading model...", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setCancelButton(None)  # Can't cancel during upload
        self.progress_dialog.show()
        
        # Upload in background thread
        self.upload_thread = UploadThread(self.api_client, file_path, name.strip())
        self.upload_thread.finished.connect(self.on_upload_success)
        self.upload_thread.error.connect(self.on_upload_error)
        self.upload_thread.start()
        logger.info(f"Starting upload of {name}")
    
    def on_upload_success(self, result):
        """Handle successful upload"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        self.upload_btn.setEnabled(True)
        self.upload_btn.setText("Upload Model")
        logger.info(f"Model '{result.get('name', 'Unknown')}' uploaded successfully")
        QMessageBox.information(
            self, "Success", 
            f"Model '{result.get('name', 'Unknown')}' uploaded successfully!"
        )
        self.refresh_models()
        self.model_uploaded.emit()
    
    def on_upload_error(self, error_msg):
        """Handle upload error"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        self.upload_btn.setEnabled(True)
        self.upload_btn.setText("Upload Model")
        logger.error(f"Upload failed: {error_msg}")
        QMessageBox.critical(self, "Upload Error", f"Upload failed:\n{error_msg}")
    
    def on_model_clicked(self, item):
        """Handle model click (enable delete button)"""
        model_id = item.data(Qt.ItemDataRole.UserRole)
        self.delete_btn.setEnabled(model_id is not None)
    
    def on_model_selected(self, item):
        """Handle model selection"""
        model_id = item.data(Qt.ItemDataRole.UserRole)
        if model_id:
            self.model_selected.emit(model_id)
    
    def delete_selected(self):
        """Delete selected model"""
        current = self.model_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Error", "Please select a model to delete")
            return
        
        model_id = current.data(Qt.ItemDataRole.UserRole)
        if not model_id:
            return
        
        # Get model name for confirmation
        model_name = current.text().split(' (')[0]  # Extract name from display text
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{model_name}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.api_client.delete_model(model_id)
                self.refresh_models()
                self.delete_btn.setEnabled(False)
                QMessageBox.information(self, "Success", "Model deleted successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Delete failed:\n{str(e)}")
