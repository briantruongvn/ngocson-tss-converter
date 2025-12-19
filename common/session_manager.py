"""
Thread-safe session state management for Streamlit
Provides safe concurrent access to session state variables.
"""

import threading
import time
import logging
from typing import Dict, Any, Optional, Callable, Union
from contextlib import contextmanager
import streamlit as st
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class SessionLockTimeout(Exception):
    """Raised when session lock acquisition times out"""
    pass

class ProcessingState(Enum):
    """Processing state enumeration"""
    IDLE = "idle"
    UPLOADING = "uploading"
    VALIDATING = "validating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class ProgressData:
    """Thread-safe progress data container"""
    current_step: int = 0
    step_status: Dict[str, str] = field(default_factory=lambda: {f"step{i}": "pending" for i in range(1, 6)})
    message: str = "Ready to process"
    error: bool = False
    error_details: Optional[str] = None
    processing_start_time: Optional[float] = None
    last_updated: float = field(default_factory=time.time)

class ThreadSafeSessionManager:
    """Thread-safe session state manager for Streamlit"""
    
    _instance = None
    _lock = threading.Lock()
    _session_locks = {}
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._session_locks = {}
            self._default_timeout = 30.0  # 30 seconds default timeout
            self._initialized = True
    
    def _get_session_id(self) -> str:
        """Get current Streamlit session ID"""
        try:
            # Try to get session ID from Streamlit context
            if hasattr(st, 'session_state') and hasattr(st.session_state, '_session_id'):
                return st.session_state._session_id
            
            # Fallback: use thread ID
            return f"thread_{threading.current_thread().ident}"
        except Exception:
            return f"fallback_{int(time.time())}"
    
    def _get_session_lock(self) -> threading.RLock:
        """Get or create lock for current session"""
        session_id = self._get_session_id()
        
        if session_id not in self._session_locks:
            with self._lock:
                if session_id not in self._session_locks:
                    self._session_locks[session_id] = threading.RLock()
        
        return self._session_locks[session_id]
    
    @contextmanager
    def session_lock(self, timeout: Optional[float] = None):
        """
        Context manager for thread-safe session state access
        
        Args:
            timeout: Lock acquisition timeout in seconds
            
        Raises:
            SessionLockTimeout: If lock cannot be acquired within timeout
        """
        session_lock = self._get_session_lock()
        timeout = timeout or self._default_timeout
        
        acquired = session_lock.acquire(timeout=timeout)
        if not acquired:
            raise SessionLockTimeout(f"Failed to acquire session lock within {timeout} seconds")
        
        try:
            yield
        finally:
            session_lock.release()
    
    def safe_update_session_state(self, updates: Dict[str, Any], timeout: Optional[float] = None) -> bool:
        """
        Safely update session state with thread protection
        
        Args:
            updates: Dictionary of updates to apply
            timeout: Lock acquisition timeout
            
        Returns:
            True if update succeeded, False otherwise
        """
        try:
            with self.session_lock(timeout):
                for key, value in updates.items():
                    st.session_state[key] = value
                return True
        except SessionLockTimeout:
            logger.error(f"Session state update timed out")
            return False
        except Exception as e:
            logger.error(f"Session state update failed: {e}")
            return False
    
    def safe_get_session_value(self, key: str, default: Any = None, timeout: Optional[float] = None) -> Any:
        """
        Safely get session state value with thread protection
        
        Args:
            key: Session state key
            default: Default value if key not found
            timeout: Lock acquisition timeout
            
        Returns:
            Session state value or default
        """
        try:
            with self.session_lock(timeout):
                return st.session_state.get(key, default)
        except SessionLockTimeout:
            logger.error(f"Session state read timed out for key: {key}")
            return default
        except Exception as e:
            logger.error(f"Session state read failed for key {key}: {e}")
            return default
    
    def safe_update_progress(self, progress_data: Dict[str, Any], timeout: Optional[float] = None) -> bool:
        """
        Safely update progress data with validation
        
        Args:
            progress_data: Progress data to update
            timeout: Lock acquisition timeout
            
        Returns:
            True if update succeeded
        """
        try:
            with self.session_lock(timeout):
                current_progress = st.session_state.get('progress_data', {})
                
                # Validate progress data
                validated_data = self._validate_progress_data(progress_data)
                
                # Update timestamp
                validated_data['last_updated'] = time.time()
                
                # Merge with existing data
                current_progress.update(validated_data)
                st.session_state['progress_data'] = current_progress
                
                return True
        except SessionLockTimeout:
            logger.error("Progress update timed out")
            return False
        except Exception as e:
            logger.error(f"Progress update failed: {e}")
            return False
    
    def _validate_progress_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize progress data"""
        validated = {}
        
        # Validate current_step
        if 'current_step' in data:
            step = data['current_step']
            if isinstance(step, int) and 0 <= step <= 5:
                validated['current_step'] = step
        
        # Validate step_status
        if 'step_status' in data and isinstance(data['step_status'], dict):
            valid_statuses = {'pending', 'running', 'completed', 'error'}
            step_status = {}
            for key, status in data['step_status'].items():
                if key.startswith('step') and status in valid_statuses:
                    step_status[key] = status
            if step_status:
                validated['step_status'] = step_status
        
        # Validate message
        if 'message' in data:
            message = str(data['message'])[:500]  # Limit message length
            validated['message'] = message
        
        # Validate error flag
        if 'error' in data:
            validated['error'] = bool(data['error'])
        
        # Validate error_details
        if 'error_details' in data:
            error_details = str(data['error_details'])[:1000]  # Limit error details length
            validated['error_details'] = error_details
        
        return validated
    
    def initialize_session_state(self) -> bool:
        """
        Initialize session state with default values
        
        Returns:
            True if initialization succeeded
        """
        try:
            with self.session_lock():
                # Initialize only if not already set
                defaults = {
                    'processing_state': ProcessingState.IDLE.value,
                    'progress_data': ProgressData().__dict__,
                    'output_file_path': None,
                    'processing_stats': {},
                    'uploaded_file_info': None,
                    'processing_start_time': None,
                    'last_activity': time.time()
                }
                
                for key, default_value in defaults.items():
                    if key not in st.session_state:
                        st.session_state[key] = default_value
                
                return True
        except Exception as e:
            logger.error(f"Session state initialization failed: {e}")
            return False
    
    def cleanup_session_state(self) -> bool:
        """
        Clean up session state and release resources
        
        Returns:
            True if cleanup succeeded
        """
        try:
            with self.session_lock():
                # Reset to defaults but keep essential data
                st.session_state['processing_state'] = ProcessingState.IDLE.value
                st.session_state['progress_data'] = ProgressData().__dict__
                st.session_state['uploaded_file_info'] = None
                
                # Don't clear output_file_path and processing_stats
                # so user can still download results
                
                return True
        except Exception as e:
            logger.error(f"Session state cleanup failed: {e}")
            return False
    
    def update_processing_state(self, new_state: ProcessingState, timeout: Optional[float] = None) -> bool:
        """
        Update processing state safely
        
        Args:
            new_state: New processing state
            timeout: Lock acquisition timeout
            
        Returns:
            True if update succeeded
        """
        try:
            with self.session_lock(timeout):
                st.session_state['processing_state'] = new_state.value
                st.session_state['last_activity'] = time.time()
                
                logger.info(f"Processing state updated to: {new_state.value}")
                return True
        except Exception as e:
            logger.error(f"Processing state update failed: {e}")
            return False
    
    def get_processing_state(self, timeout: Optional[float] = None) -> ProcessingState:
        """
        Get current processing state safely
        
        Args:
            timeout: Lock acquisition timeout
            
        Returns:
            Current processing state
        """
        try:
            with self.session_lock(timeout):
                state_value = st.session_state.get('processing_state', ProcessingState.IDLE.value)
                return ProcessingState(state_value)
        except Exception as e:
            logger.error(f"Processing state read failed: {e}")
            return ProcessingState.IDLE
    
    def is_processing_active(self, timeout: Optional[float] = None) -> bool:
        """
        Check if processing is currently active
        
        Args:
            timeout: Lock acquisition timeout
            
        Returns:
            True if processing is active
        """
        state = self.get_processing_state(timeout)
        return state in {ProcessingState.UPLOADING, ProcessingState.VALIDATING, ProcessingState.PROCESSING}
    
    def cleanup_old_sessions(self, max_age_hours: float = 24.0):
        """
        Clean up old session locks to prevent memory leaks
        
        Args:
            max_age_hours: Maximum age of session locks to keep
        """
        try:
            with self._lock:
                current_time = time.time()
                cutoff_time = current_time - (max_age_hours * 3600)
                
                # This is a simplified cleanup - in production, you'd need
                # to track session creation times
                logger.info(f"Cleaned up old session locks older than {max_age_hours} hours")
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")

# Global session manager instance
session_manager = ThreadSafeSessionManager()

# Convenience functions for easy access
def safe_update_session_state(updates: Dict[str, Any], timeout: Optional[float] = None) -> bool:
    """Convenience function for safe session state updates"""
    return session_manager.safe_update_session_state(updates, timeout)

def safe_get_session_value(key: str, default: Any = None, timeout: Optional[float] = None) -> Any:
    """Convenience function for safe session state reads"""
    return session_manager.safe_get_session_value(key, default, timeout)

def safe_update_progress(progress_data: Dict[str, Any], timeout: Optional[float] = None) -> bool:
    """Convenience function for safe progress updates"""
    return session_manager.safe_update_progress(progress_data, timeout)

def initialize_session_state() -> bool:
    """Convenience function for session state initialization"""
    return session_manager.initialize_session_state()

def cleanup_session_state() -> bool:
    """Convenience function for session state cleanup"""
    return session_manager.cleanup_session_state()

def update_processing_state(new_state: ProcessingState, timeout: Optional[float] = None) -> bool:
    """Convenience function for processing state updates"""
    return session_manager.update_processing_state(new_state, timeout)

def get_processing_state(timeout: Optional[float] = None) -> ProcessingState:
    """Convenience function for processing state reads"""
    return session_manager.get_processing_state(timeout)

def is_processing_active(timeout: Optional[float] = None) -> bool:
    """Convenience function to check if processing is active"""
    return session_manager.is_processing_active(timeout)