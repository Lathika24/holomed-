"""Main entry point for the desktop application"""

import sys
from PyQt6.QtWidgets import QApplication
from app import MainWindow

def main():
    """Launch the desktop application"""
    app = QApplication(sys.argv)
    app.setApplicationName("HoloMed Desktop")
    app.setApplicationVersion("1.0.0")
    
    # High DPI scaling is enabled by default in PyQt6
    # No need to set these attributes
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
