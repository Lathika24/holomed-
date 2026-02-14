"""Authentication window for login and registration"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QTabWidget, QWidget, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class AuthWindow(QDialog):
    """Login and registration dialog"""
    
    authenticated = pyqtSignal(str, str)  # username, token
    
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.setWindowTitle("HoloMed - Authentication")
        self.setFixedSize(400, 400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("HoloMed Desktop")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        subtitle = QLabel("Holographic Medical Visualization")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # Tabs for Login/Register
        tabs = QTabWidget()
        
        # Login Tab
        login_tab = QWidget()
        login_layout = QFormLayout()
        login_layout.setSpacing(15)
        login_layout.setContentsMargins(20, 20, 20, 20)
        
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Enter username")
        self.login_username.setMinimumHeight(30)
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Enter password")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password.setMinimumHeight(30)
        
        login_layout.addRow("Username:", self.login_username)
        login_layout.addRow("Password:", self.login_password)
        
        login_btn = QPushButton("Login")
        login_btn.setMinimumHeight(35)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        login_btn.clicked.connect(self.handle_login)
        login_layout.addRow(login_btn)
        
        # Allow Enter key to trigger login
        self.login_password.returnPressed.connect(self.handle_login)
        
        login_tab.setLayout(login_layout)
        tabs.addTab(login_tab, "Login")
        
        # Register Tab
        register_tab = QWidget()
        register_layout = QFormLayout()
        register_layout.setSpacing(15)
        register_layout.setContentsMargins(20, 20, 20, 20)
        
        self.register_username = QLineEdit()
        self.register_username.setPlaceholderText("Enter username")
        self.register_username.setMinimumHeight(30)
        self.register_email = QLineEdit()
        self.register_email.setPlaceholderText("Enter email")
        self.register_email.setMinimumHeight(30)
        self.register_password = QLineEdit()
        self.register_password.setPlaceholderText("Enter password")
        self.register_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.register_password.setMinimumHeight(30)
        
        register_layout.addRow("Username:", self.register_username)
        register_layout.addRow("Email:", self.register_email)
        register_layout.addRow("Password:", self.register_password)
        
        register_btn = QPushButton("Register")
        register_btn.setMinimumHeight(35)
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        register_btn.clicked.connect(self.handle_register)
        register_layout.addRow(register_btn)
        
        # Allow Enter key to trigger register
        self.register_password.returnPressed.connect(self.handle_register)
        
        register_tab.setLayout(register_layout)
        tabs.addTab(register_tab, "Register")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
    
    def handle_login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password")
            return
        
        try:
            result = self.api_client.login(username, password)
            token = result.get("access_token")
            if token:
                self.authenticated.emit(username, token)
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Login failed: No token received")
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                try:
                    import json
                    error_data = json.loads(e.response.text)
                    error_msg = error_data.get('detail', error_msg)
                except:
                    pass
            QMessageBox.critical(self, "Login Error", f"Login failed:\n{error_msg}")
    
    def handle_register(self):
        username = self.register_username.text().strip()
        email = self.register_email.text().strip()
        password = self.register_password.text()
        
        if not username or not email or not password:
            QMessageBox.warning(self, "Error", "Please fill all fields")
            return
        
        if len(password) < 6:
            QMessageBox.warning(self, "Error", "Password must be at least 6 characters")
            return
        
        try:
            self.api_client.register(username, email, password)
            QMessageBox.information(
                self, "Success", 
                "Registration successful!\n\nPlease login with your credentials."
            )
            # Switch to login tab and pre-fill username
            tabs = self.findChild(QTabWidget)
            if tabs:
                tabs.setCurrentIndex(0)
            self.login_username.setText(username)
            self.login_password.clear()
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                try:
                    import json
                    error_data = json.loads(e.response.text)
                    error_msg = error_data.get('detail', error_msg)
                except:
                    pass
            QMessageBox.critical(self, "Registration Error", f"Registration failed:\n{error_msg}")
