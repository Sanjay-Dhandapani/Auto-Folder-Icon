#!/usr/bin/env python3
"""
Smart Media Icon Processing Engine

Manages background processing of media directories with queue management,
threading, and integration with the existing SmartIconSetter functionality.
"""

import os
import time
import queue
import threading
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread

# Import existing smart_media_icon components
from ..core.icon_setter import SmartIconSetter
from ..apis.media_api import MediaAPI


@dataclass
class ProcessingTask:
    """Represents a processing task in the queue"""
    directory: str
    priority: int
    created_time: float
    retry_count: int = 0
    task_id: str = ""
    
    def __post_init__(self):
        if not self.task_id:
            self.task_id = f"{int(self.created_time)}_{hash(self.directory)}"


class TraySmartIconSetter(SmartIconSetter):
    """
    Extended SmartIconSetter with tray-specific functionality
    including progress callbacks and async processing
    """
    
    def __init__(self, config, progress_callback=None, notification_callback=None):
        super().__init__(config)
        
        self.progress_callback = progress_callback
        self.notification_callback = notification_callback
        
        # Processing state
        self.is_processing = False
        self.current_task = None
        self.processing_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'start_time': None
        }
    
    def process_directory_with_callbacks(self, directory_path: str) -> Dict[str, Any]:
        """
        Process directory with progress callbacks
        
        Args:
            directory_path: Directory to process
            
        Returns:
            Processing results dictionary
        """
        try:
            self.is_processing = True
            self.current_task = directory_path
            self.processing_stats['start_time'] = time.time()
            
            # Notify start
            if self.progress_callback:
                self.progress_callback("started", directory_path)
            
            if self.notification_callback:
                self.notification_callback("processing_started", {
                    'directory': directory_path,
                    'timestamp': self.processing_stats['start_time']
                })
            
            # Use existing process_media_collection logic
            results = self.process_media_collection(directory_path)
            
            # Update stats
            self.processing_stats['total_processed'] += results.get('total_processed', 0)
            self.processing_stats['successful'] += results.get('successful', 0)
            self.processing_stats['failed'] += results.get('failed', 0)
            
            # Notify completion
            if self.notification_callback:
                self.notification_callback("processing_completed", results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing directory {directory_path}: {e}")
            
            error_result = {
                'total_processed': 0,
                'successful': 0,
                'failed': 1,
                'error': str(e),
                'directory': directory_path
            }
            
            if self.notification_callback:
                self.notification_callback("processing_error", error_result)
            
            return error_result
            
        finally:
            self.is_processing = False
            self.current_task = None
            
            if self.progress_callback:
                self.progress_callback("completed", directory_path)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        stats = self.processing_stats.copy()
        if stats['start_time']:
            stats['elapsed_time'] = time.time() - stats['start_time']
        return stats
    
    def reset_stats(self):
        """Reset processing statistics"""
        self.processing_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'start_time': None
        }


class ProcessingEngine(QObject):
    """
    Main processing engine that manages background processing with threading
    """
    
    # Signals
    processingStarted = pyqtSignal(str)  # directory
    processingFinished = pyqtSignal(dict)  # results
    processingProgress = pyqtSignal(str, str)  # status, message
    statusChanged = pyqtSignal(str, str)  # status, message
    queueSizeChanged = pyqtSignal(int)  # queue size
    
    def __init__(self, settings_manager, notification_system):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # Store component references
        self.settings_manager = settings_manager
        self.notification_system = notification_system
        
        # Processing queue
        self.processing_queue = queue.PriorityQueue()
        self.processing_history = []
        
        # Worker threads
        self.worker_threads = []
        self.max_workers = self.settings_manager.MAX_CONCURRENT_PROCESSING
        self.workers_running = False
        
        # Initialize enhanced SmartIconSetter
        self.smart_icon_setter = TraySmartIconSetter(
            self.settings_manager.get_cli_compatible_config(),
            progress_callback=self.on_progress_update,
            notification_callback=self.on_notification_update
        )
        
        # Processing state
        self.active_tasks = {}  # task_id -> ProcessingTask
        self.is_running = False
        
        # Statistics
        self.stats = {
            'total_queued': 0,
            'total_processed': 0,
            'total_successful': 0,
            'total_failed': 0,
            'queue_size': 0,
            'active_workers': 0
        }
        
        # Queue monitor timer
        self.queue_monitor = QTimer()
        self.queue_monitor.timeout.connect(self.update_queue_stats)
        self.queue_monitor.start(2000)  # Update every 2 seconds
        
        self.logger.info("⚙️ Processing engine initialized")
    
    def start(self):
        """Start the processing engine"""
        if self.is_running:
            self.logger.warning("Processing engine is already running")
            return
        
        try:
            self.logger.info("🚀 Starting processing engine...")
            
            # Start worker threads
            self.start_worker_threads()
            
            self.is_running = True
            self.statusChanged.emit("started", "Processing engine started")
            
            self.logger.info(f"✅ Processing engine started with {self.max_workers} workers")
            
        except Exception as e:
            self.logger.error(f"Failed to start processing engine: {e}")
    
    def stop(self):
        """Stop the processing engine"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("🛑 Stopping processing engine...")
            
            # Stop accepting new tasks
            self.is_running = False
            
            # Signal workers to stop
            self.workers_running = False
            
            # Add poison pills to wake up workers
            for _ in range(self.max_workers):
                self.processing_queue.put((0, time.time(), None))  # Poison pill
            
            # Wait for workers to finish
            for thread in self.worker_threads:
                thread.join(timeout=5.0)
            
            self.worker_threads.clear()
            self.statusChanged.emit("stopped", "Processing engine stopped")
            
            self.logger.info("✅ Processing engine stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping processing engine: {e}")
    
    def start_worker_threads(self):
        """Start background worker threads"""
        self.workers_running = True
        
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self.worker_thread,
                name=f"ProcessingWorker-{i+1}",
                daemon=True
            )
            worker.start()
            self.worker_threads.append(worker)
            
        self.logger.info(f"Started {self.max_workers} worker threads")
    
    def queue_directory_for_processing(self, directory: str, priority: int = 1):
        """
        Queue a directory for processing
        
        Args:
            directory: Directory path to process
            priority: Processing priority (lower = higher priority)
        """
        try:
            if not self.is_running:
                self.logger.warning("Processing engine is not running")
                return
            
            # Create processing task
            task = ProcessingTask(
                directory=os.path.abspath(directory),
                priority=priority,
                created_time=time.time()
            )
            
            # Check if directory is already queued or being processed
            if self.is_task_duplicate(task):
                self.logger.debug(f"Task already queued/processing: {directory}")
                return
            
            # Add to queue
            self.processing_queue.put((priority, task.created_time, task))
            self.stats['total_queued'] += 1
            
            self.logger.info(f"📋 Queued for processing: {directory} (priority: {priority})")
            
            # Emit signals
            self.queueSizeChanged.emit(self.processing_queue.qsize())
            
        except Exception as e:
            self.logger.error(f"Failed to queue directory {directory}: {e}")
    
    def is_task_duplicate(self, new_task: ProcessingTask) -> bool:
        """Check if task is duplicate of existing queued or active tasks"""
        # Check active tasks
        for active_task in self.active_tasks.values():
            if active_task.directory == new_task.directory:
                return True
        
        # Check queue (this is more expensive but necessary)
        temp_items = []
        is_duplicate = False
        
        try:
            while not self.processing_queue.empty():
                item = self.processing_queue.get_nowait()
                temp_items.append(item)
                
                if len(item) >= 3 and item[2] and item[2].directory == new_task.directory:
                    is_duplicate = True
                    break
        except queue.Empty:
            pass
        
        # Restore queue
        for item in temp_items:
            self.processing_queue.put(item)
        
        return is_duplicate
    
    def worker_thread(self):
        """Worker thread that processes tasks from the queue"""
        thread_name = threading.current_thread().name
        self.logger.debug(f"Worker thread started: {thread_name}")
        
        while self.workers_running:
            try:
                # Get task from queue (blocking with timeout)
                try:
                    priority, timestamp, task = self.processing_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Check for poison pill (stop signal)
                if task is None:
                    break
                
                # Process the task
                self.process_task(task, thread_name)
                
                # Mark task as done
                self.processing_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Worker thread error in {thread_name}: {e}")
        
        self.logger.debug(f"Worker thread stopped: {thread_name}")
    
    def process_task(self, task: ProcessingTask, worker_name: str):
        """
        Process a single task
        
        Args:
            task: Processing task to execute
            worker_name: Name of the worker thread
        """
        try:
            self.logger.info(f"🔄 Processing: {task.directory} (worker: {worker_name})")
            
            # Add to active tasks
            self.active_tasks[task.task_id] = task
            self.stats['active_workers'] = len(self.active_tasks)
            
            # Emit processing started signal
            self.processingStarted.emit(task.directory)
            
            # Process using TraySmartIconSetter
            results = self.smart_icon_setter.process_directory_with_callbacks(task.directory)
            
            # Update statistics
            self.stats['total_processed'] += 1
            if results.get('successful', 0) > 0:
                self.stats['total_successful'] += 1
            else:
                self.stats['total_failed'] += 1
            
            # Add to processing history
            self.processing_history.append({
                'task': task,
                'results': results,
                'worker': worker_name,
                'completed_time': time.time()
            })
            
            # Keep history limited
            if len(self.processing_history) > 100:
                self.processing_history = self.processing_history[-50:]
            
            # Emit processing finished signal
            self.processingFinished.emit(results)
            
            self.logger.info(f"✅ Completed: {task.directory} ({results.get('successful', 0)} successful)")
            
        except Exception as e:
            self.logger.error(f"❌ Task processing failed for {task.directory}: {e}")
            
            # Create error result
            error_results = {
                'total_processed': 0,
                'successful': 0,
                'failed': 1,
                'error': str(e),
                'directory': task.directory
            }
            
            self.stats['total_failed'] += 1
            self.processingFinished.emit(error_results)
            
        finally:
            # Remove from active tasks
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
            self.stats['active_workers'] = len(self.active_tasks)
    
    def on_progress_update(self, status: str, message: str):
        """Handle progress updates from SmartIconSetter"""
        self.processingProgress.emit(status, message)
        self.statusChanged.emit(status, message)
    
    def on_notification_update(self, notification_type: str, data: Dict[str, Any]):
        """Handle notification updates from SmartIconSetter"""
        try:
            if notification_type == "processing_started":
                directory = data.get('directory', '')
                self.notification_system.show_processing_notification(
                    directory, 
                    data.get('item_count', 0)
                )
                
            elif notification_type == "processing_completed":
                self.notification_system.show_completion_notification(data)
                
            elif notification_type == "processing_error":
                self.notification_system.show_error_notification(
                    "Processing Error",
                    data.get('error', 'Unknown error'),
                    data
                )
                
        except Exception as e:
            self.logger.error(f"Error handling notification update: {e}")
    
    def update_queue_stats(self):
        """Update queue statistics"""
        try:
            self.stats['queue_size'] = self.processing_queue.qsize()
            self.queueSizeChanged.emit(self.stats['queue_size'])
            
        except Exception as e:
            self.logger.debug(f"Error updating queue stats: {e}")
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status"""
        return {
            'is_running': self.is_running,
            'queue_size': self.processing_queue.qsize(),
            'active_tasks': len(self.active_tasks),
            'worker_threads': len(self.worker_threads),
            'workers_running': self.workers_running,
            'stats': self.stats.copy(),
            'smart_icon_setter_stats': self.smart_icon_setter.get_processing_stats()
        }
    
    def get_active_tasks(self) -> Dict[str, ProcessingTask]:
        """Get currently active tasks"""
        return self.active_tasks.copy()
    
    def get_processing_history(self, limit: int = 20) -> list:
        """Get recent processing history"""
        return self.processing_history[-limit:] if self.processing_history else []
    
    def clear_queue(self):
        """Clear the processing queue"""
        try:
            while not self.processing_queue.empty():
                self.processing_queue.get_nowait()
                self.processing_queue.task_done()
            
            self.logger.info("Processing queue cleared")
            self.queueSizeChanged.emit(0)
            
        except Exception as e:
            self.logger.error(f"Error clearing queue: {e}")
    
    def pause_processing(self):
        """Pause processing (stop accepting new tasks)"""
        self.is_running = False
        self.statusChanged.emit("paused", "Processing paused")
        self.logger.info("Processing paused")
    
    def resume_processing(self):
        """Resume processing"""
        self.is_running = True
        self.statusChanged.emit("resumed", "Processing resumed")
        self.logger.info("Processing resumed")
    
    def retry_failed_tasks(self):
        """Retry failed tasks from history"""
        retry_count = 0
        
        for history_item in self.processing_history:
            results = history_item.get('results', {})
            if results.get('failed', 0) > 0 and results.get('successful', 0) == 0:
                task = history_item['task']
                if task.retry_count < 3:  # Max 3 retries
                    task.retry_count += 1
                    self.queue_directory_for_processing(task.directory, task.priority + 1)
                    retry_count += 1
        
        if retry_count > 0:
            self.logger.info(f"Queued {retry_count} failed tasks for retry")
            self.notification_system.show_notification(
                "Retry Queued",
                f"Queued {retry_count} failed tasks for retry",
                "info"
            )
    
    def update_settings(self, settings_manager):
        """Update settings and reconfigure if needed"""
        old_max_workers = self.max_workers
        self.settings_manager = settings_manager
        self.max_workers = settings_manager.MAX_CONCURRENT_PROCESSING
        
        # Update SmartIconSetter config
        self.smart_icon_setter.config = settings_manager.get_cli_compatible_config()
        
        # Restart workers if count changed
        if old_max_workers != self.max_workers and self.is_running:
            self.logger.info(f"Worker count changed: {old_max_workers} -> {self.max_workers}")
            # For simplicity, we'd need to implement dynamic worker management
            # For now, just log the change
        
        self.logger.info("Processing engine settings updated")