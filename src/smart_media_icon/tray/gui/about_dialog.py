#!/usr/bin/env python3
"""
Smart Media Icon About Dialog

Simple about dialog showing application information, version, and credits.
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap


class AboutDialog(QDialog):
    """Simple about dialog for the application"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("About Smart Media Icon")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Application title
        title_label = QLabel("Smart Media Icon System")
        title_font = QFont("Segoe UI", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Version info
        version_label = QLabel("Version 1.0.0 - Tray Application")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        # Description
        description = QLabel("""
        <p>Professional Windows desktop utility for automatic media icon management.</p>
        
        <p><b>Key Features:</b></p>
        <ul>
        <li>Smart TV series and movie detection</li>
        <li>Custom folder icons using Windows desktop.ini</li>
        <li>FFmpeg artwork embedding for movies</li>
        <li>Multi-API poster fetching</li>
        <li>Automatic folder monitoring</li>
        <li>System tray integration</li>
        </ul>
        
        <p><b>Copyright:</b> © 2024 Smart Media Icon Team<br>
        <b>License:</b> MIT License</p>
        """)
        
        description.setWordWrap(True)
        description.setOpenExternalLinks(True)
        layout.addWidget(description)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)