#!/usr/bin/env python3
"""
Smart Media Icon Progress Dialog

Shows processing progress with cancellation support and detailed status information.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QTextEdit, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont


class ProgressDialog(QDialog):
    """
    Progress dialog for showing processing status
    """
    
    # Signals
    cancelRequested = pyqtSignal()
    
    def __init__(self, title="Processing", parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setMinimumSize(500, 300)
        self.setModal(True)
        
        self.is_cancelled = False
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        status_font = QFont("Segoe UI", 10, QFont.Bold)
        self.status_label.setFont(status_font)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Details section
        details_group = QGroupBox("Details")
        details_layout = QVBoxLayout(details_group)
        
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(150)
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)
        
        layout.addWidget(details_group)
        
        # Statistics
        stats_layout = QHBoxLayout()
        
        self.processed_label = QLabel("Processed: 0")
        self.successful_label = QLabel("Successful: 0")
        self.failed_label = QLabel("Failed: 0")
        
        stats_layout.addWidget(self.processed_label)
        stats_layout.addWidget(self.successful_label)
        stats_layout.addWidget(self.failed_label)
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_processing)
        button_layout.addWidget(self.cancel_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setEnabled(False)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def update_progress(self, value: int, status: str = None):
        """Update progress bar value and status"""
        self.progress_bar.setValue(value)
        
        if status:
            self.status_label.setText(status)
        
        # Enable close button when complete
        if value >= 100:
            self.cancel_btn.setEnabled(False)
            self.close_btn.setEnabled(True)
    
    def update_status(self, status: str):
        """Update status label"""
        self.status_label.setText(status)
    
    def add_detail(self, message: str):
        """Add a detail message to the text area"""
        self.details_text.append(message)
        # Auto-scroll to bottom
        scrollbar = self.details_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_statistics(self, processed: int, successful: int, failed: int):
        """Update processing statistics"""
        self.processed_label.setText(f"Processed: {processed}")
        self.successful_label.setText(f"Successful: {successful}")
        self.failed_label.setText(f"Failed: {failed}")
    
    def cancel_processing(self):
        """Cancel the current processing"""
        self.is_cancelled = True
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("Cancelling...")
        self.cancelRequested.emit()
    
    def processing_complete(self, success: bool = True):
        """Mark processing as complete"""
        if success:
            self.status_label.setText("Processing completed successfully")
            self.progress_bar.setValue(100)
        else:
            self.status_label.setText("Processing failed")
        
        self.cancel_btn.setEnabled(False)
        self.close_btn.setEnabled(True)
    
    def closeEvent(self, event):
        """Handle close event"""
        if not self.close_btn.isEnabled():
            # Processing is still active, ask for confirmation
            self.cancel_processing()
            event.ignore()
        else:
            event.accept()