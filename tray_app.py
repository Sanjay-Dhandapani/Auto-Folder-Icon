import sys
import threading
import os
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QFileDialog, QMessageBox
from PyQt5.QtCore import QCoreApplication
from win_icon import WinIconSetter
from media_watcher import MediaWatcher
from config import Config

# Load config as an object
cfg = Config()

def run_media_watcher():
    watcher = MediaWatcher(cfg)
    watcher.watch(cfg.MEDIA_ROOT_DIR)

class TrayApp(QtWidgets.QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)
        self.icon_setter = WinIconSetter()
        # Use default icon if icon.ico is missing
        icon_path = "icon.ico"
        if os.path.exists(icon_path):
            icon = QtGui.QIcon(icon_path)
        else:
            icon = self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon)
        self.tray = QSystemTrayIcon(icon, self)
        self.menu = QMenu()

        choose_dir_action = QAction("Choose Directory", self)
        choose_dir_action.triggered.connect(self.choose_directory)
        self.menu.addAction(choose_dir_action)

        revert_action = QAction("Revert Folder Icon", self)
        revert_action.triggered.connect(self.revert_icon)
        self.menu.addAction(revert_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_app)
        self.menu.addAction(exit_action)

        self.tray.setContextMenu(self.menu)
        self.tray.setToolTip("Media Iconer")
        self.tray.show()

        # Show a message box to confirm startup
        QMessageBox.information(None, "Media Iconer", "Tray app started! Check your system tray.")

        self.watcher_thread = None
        self.current_dir = cfg.MEDIA_ROOT_DIR
        self.start_watcher(self.current_dir)

    def start_watcher(self, directory):
        if self.watcher_thread and self.watcher_thread.is_alive():
            QMessageBox.information(None, "Media Iconer", "Stopping previous watcher...")
            # Not a clean stop, but for demo purposes
        def run():
            watcher = MediaWatcher(cfg)
            watcher.watch(directory)
        self.watcher_thread = threading.Thread(target=run, daemon=True)
        self.watcher_thread.start()

    def choose_directory(self):
        folder = QFileDialog.getExistingDirectory(None, "Select Directory to Watch")
        if folder:
            self.current_dir = folder
            cfg.MEDIA_ROOT_DIR = folder
            QMessageBox.information(None, "Media Iconer", f"Now watching: {folder}\nApplying icons...")
            # Scan and apply icons immediately
            watcher = MediaWatcher(cfg)
            watcher.scan_and_apply_icons(folder)
            self.start_watcher(folder)

    def revert_icon(self):
        folder = QFileDialog.getExistingDirectory(None, "Select Folder to Revert")
        if folder:
            try:
                self.icon_setter.revert_folder_icon(folder)
                QMessageBox.information(None, "Revert", f"Reverted icon for: {folder}")
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Failed to revert: {e}")

    def exit_app(self):
        self.tray.hide()
        QCoreApplication.quit()

if __name__ == "__main__":
    app = TrayApp(sys.argv)
    sys.exit(app.exec_())
