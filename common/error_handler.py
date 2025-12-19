"""
Safe error handling utilities for TSS Converter
Prevents infinite loops, handles resource cleanup, and provides recovery mechanisms.
"""

import logging
import time
import threading
import traceback
from typing import Dict, Any, Optional, Callable, Type, List
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import signal
import sys

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RecoveryAction(Enum):
    """Recovery action types"""
    RETRY = "retry"
    SKIP = "skip"
    ABORT = "abort"
    RESET = "reset"
    CLEANUP = "cleanup"

@dataclass
class ErrorContext:
    """Error context information"""
    error_id: str
    timestamp: float = field(default_factory=time.time)
    function_name: str = ""
    file_path: str = ""
    line_number: int = 0
    user_context: Dict[str, Any] = field(default_factory=dict)
    system_context: Dict[str, Any] = field(default_factory=dict)
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    recovery_action: RecoveryAction = RecoveryAction.ABORT

class CircuitBreaker:
    """Circuit breaker to prevent infinite loops and cascading failures"""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open
        self._lock = threading.Lock()
        
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self._lock:
            if self.state == "open":
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = "half-open"
                    logger.info(f"Circuit breaker half-open for {func.__name__}")
                else:
                    raise RuntimeError(f"Circuit breaker open for {func.__name__}")
                    
            try:
                result = func(*args, **kwargs)
                
                # Success - reset if we were in half-open state
                if self.state == "half-open":
                    self.state = "closed"
                    self.failure_count = 0
                    logger.info(f"Circuit breaker closed for {func.__name__}")
                    
                return result
                
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "open"
                    logger.warning(f"Circuit breaker opened for {func.__name__} after {self.failure_count} failures")
                
                raise e

class TimeoutHandler:
    """Timeout handler to prevent infinite execution"""
    
    def __init__(self, timeout_seconds: float = 300.0):  # 5 minutes default
        self.timeout_seconds = timeout_seconds
        self.active_operations = {}
        self._lock = threading.Lock()
        
    def __call__(self, func: Callable):
        """Decorator for timeout protection"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            operation_id = f"{func.__name__}_{threading.current_thread().ident}_{time.time()}"
            
            def timeout_handler(signum, frame):
                logger.error(f"Operation {func.__name__} timed out after {self.timeout_seconds}s")
                raise TimeoutError(f"Operation {func.__name__} timed out")
            
            # Set up timeout
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(self.timeout_seconds))
            
            try:
                with self._lock:
                    self.active_operations[operation_id] = {
                        'start_time': time.time(),
                        'function': func.__name__,
                        'thread_id': threading.current_thread().ident
                    }
                
                result = func(*args, **kwargs)
                return result
                
            finally:
                # Clear timeout
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                
                with self._lock:
                    self.active_operations.pop(operation_id, None)
                    
        return wrapper
    
    def get_active_operations(self) -> List[Dict[str, Any]]:
        """Get list of currently active operations"""
        with self._lock:
            return list(self.active_operations.values())

class SafeErrorHandler:
    """Comprehensive error handler with recovery mechanisms"""
    
    def __init__(self):
        self.circuit_breakers = {}
        self.error_history = []
        self.max_history = 1000
        self.retry_policies = {}
        self._lock = threading.Lock()
        
    def register_retry_policy(self, operation_name: str, max_retries: int = 3, 
                            backoff_factor: float = 1.5, max_delay: float = 60.0):
        """Register retry policy for an operation"""
        self.retry_policies[operation_name] = {
            'max_retries': max_retries,
            'backoff_factor': backoff_factor,
            'max_delay': max_delay
        }
        
    def get_circuit_breaker(self, operation_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for operation"""
        if operation_name not in self.circuit_breakers:
            self.circuit_breakers[operation_name] = CircuitBreaker()
        return self.circuit_breakers[operation_name]
    
    def safe_execute(self, func: Callable, operation_name: str, 
                    error_context: Optional[Dict[str, Any]] = None,
                    recovery_func: Optional[Callable] = None) -> Any:
        """Safely execute function with comprehensive error handling"""
        
        error_context = error_context or {}
        start_time = time.time()
        
        # Get retry policy
        retry_policy = self.retry_policies.get(operation_name, {
            'max_retries': 1,
            'backoff_factor': 1.0,
            'max_delay': 10.0
        })
        
        # Get circuit breaker
        circuit_breaker = self.get_circuit_breaker(operation_name)
        
        last_exception = None
        
        for attempt in range(retry_policy['max_retries'] + 1):
            try:
                # Use circuit breaker
                result = circuit_breaker.call(func)
                
                # Log successful execution if retried
                if attempt > 0:
                    logger.info(f"Operation {operation_name} succeeded on attempt {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Create error context
                error_ctx = ErrorContext(
                    error_id=f"{operation_name}_{int(time.time())}",
                    function_name=func.__name__,
                    user_context=error_context,
                    system_context={
                        'attempt': attempt + 1,
                        'max_retries': retry_policy['max_retries'],
                        'operation_name': operation_name,
                        'execution_time': time.time() - start_time
                    }
                )
                
                # Log error
                self._log_error(e, error_ctx)
                
                # Determine if we should retry
                if attempt < retry_policy['max_retries']:
                    if self._should_retry(e, error_ctx):
                        delay = min(
                            retry_policy['backoff_factor'] ** attempt,
                            retry_policy['max_delay']
                        )
                        logger.info(f"Retrying {operation_name} in {delay}s (attempt {attempt + 1})")
                        time.sleep(delay)
                        continue
                    else:
                        logger.warning(f"Error not retryable for {operation_name}: {e}")
                        break
                else:
                    logger.error(f"Max retries exceeded for {operation_name}: {e}")
                    break
        
        # If we get here, all retries failed
        if recovery_func:
            try:
                logger.info(f"Attempting recovery for {operation_name}")
                return recovery_func(last_exception, error_context)
            except Exception as recovery_error:
                logger.error(f"Recovery failed for {operation_name}: {recovery_error}")
        
        # Final error handling
        self._handle_final_error(last_exception, operation_name, error_context)
        
        raise last_exception
    
    def _should_retry(self, exception: Exception, context: ErrorContext) -> bool:
        """Determine if an error should be retried"""
        
        # Don't retry security errors
        from .security import SecurityError
        if isinstance(exception, SecurityError):
            return False
            
        # Don't retry validation errors
        from .exceptions import ValidationError, FileFormatError
        if isinstance(exception, (ValidationError, FileFormatError)):
            return False
            
        # Don't retry timeout errors
        if isinstance(exception, TimeoutError):
            return False
            
        # Don't retry permission errors
        if isinstance(exception, PermissionError):
            return False
            
        # Retry transient errors
        transient_errors = (
            ConnectionError,
            FileNotFoundError,
            OSError
        )
        
        return isinstance(exception, transient_errors)
    
    def _log_error(self, exception: Exception, context: ErrorContext):
        """Log error with context"""
        with self._lock:
            error_entry = {
                'timestamp': context.timestamp,
                'error_id': context.error_id,
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'function_name': context.function_name,
                'severity': context.severity.value,
                'context': context.user_context,
                'system_context': context.system_context,
                'traceback': traceback.format_exc()
            }
            
            self.error_history.append(error_entry)
            
            # Limit history size
            if len(self.error_history) > self.max_history:
                self.error_history = self.error_history[-self.max_history:]
            
            # Log based on severity
            if context.severity == ErrorSeverity.CRITICAL:
                logger.critical(f"Critical error {context.error_id}: {exception}")
            elif context.severity == ErrorSeverity.HIGH:
                logger.error(f"High severity error {context.error_id}: {exception}")
            else:
                logger.warning(f"Error {context.error_id}: {exception}")
    
    def _handle_final_error(self, exception: Exception, operation_name: str, context: Dict[str, Any]):
        """Handle final error when all retries failed"""
        
        # Cleanup resources
        self._cleanup_operation_resources(operation_name, context)
        
        # Notify monitoring systems
        self._notify_error_monitoring(exception, operation_name, context)
    
    def _cleanup_operation_resources(self, operation_name: str, context: Dict[str, Any]):
        """Cleanup resources for failed operation"""
        try:
            # Cleanup temporary files
            temp_files = context.get('temp_files', [])
            for file_path in temp_files:
                try:
                    from pathlib import Path
                    Path(file_path).unlink(missing_ok=True)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temp file {file_path}: {cleanup_error}")
            
            # Reset processing state
            from .session_manager import session_manager, ProcessingState
            try:
                session_manager.update_processing_state(ProcessingState.ERROR)
            except Exception:
                pass
                
        except Exception as cleanup_error:
            logger.error(f"Resource cleanup failed for {operation_name}: {cleanup_error}")
    
    def _notify_error_monitoring(self, exception: Exception, operation_name: str, context: Dict[str, Any]):
        """Notify error monitoring systems"""
        try:
            # Log structured error for monitoring
            error_data = {
                'operation': operation_name,
                'error_type': type(exception).__name__,
                'error_message': str(exception),
                'timestamp': time.time(),
                'context': context
            }
            
            logger.error(f"MONITORING_ERROR: {error_data}")
            
        except Exception as monitor_error:
            logger.error(f"Error monitoring notification failed: {monitor_error}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors"""
        with self._lock:
            if not self.error_history:
                return {"total_errors": 0, "recent_errors": []}
            
            recent_errors = self.error_history[-10:]  # Last 10 errors
            error_counts = {}
            
            for error in self.error_history:
                error_type = error['exception_type']
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
            
            return {
                "total_errors": len(self.error_history),
                "error_types": error_counts,
                "recent_errors": recent_errors,
                "circuit_breaker_states": {
                    name: cb.state for name, cb in self.circuit_breakers.items()
                }
            }
    
    def reset_circuit_breakers(self):
        """Reset all circuit breakers"""
        with self._lock:
            for name, cb in self.circuit_breakers.items():
                cb.state = "closed"
                cb.failure_count = 0
                cb.last_failure_time = 0
                logger.info(f"Reset circuit breaker for {name}")

# Global error handler instance
global_error_handler = SafeErrorHandler()

# Convenience functions
def safe_execute(func: Callable, operation_name: str, **kwargs) -> Any:
    """Convenience function for safe execution"""
    return global_error_handler.safe_execute(func, operation_name, **kwargs)

def register_retry_policy(operation_name: str, **kwargs):
    """Convenience function for registering retry policies"""
    return global_error_handler.register_retry_policy(operation_name, **kwargs)

def get_error_summary() -> Dict[str, Any]:
    """Convenience function for getting error summary"""
    return global_error_handler.get_error_summary()

def reset_error_handlers():
    """Reset all error handling state"""
    global_error_handler.reset_circuit_breakers()
    global_error_handler.error_history.clear()

# Decorator for safe function execution
def safe_operation(operation_name: str, **error_handler_kwargs):
    """Decorator for safe operation execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return global_error_handler.safe_execute(
                lambda: func(*args, **kwargs),
                operation_name,
                **error_handler_kwargs
            )
        return wrapper
    return decorator

# Initialize default retry policies
register_retry_policy("file_operation", max_retries=3, backoff_factor=1.5)
register_retry_policy("network_operation", max_retries=5, backoff_factor=2.0)
register_retry_policy("data_processing", max_retries=2, backoff_factor=1.0)
register_retry_policy("pipeline_step", max_retries=1, backoff_factor=0.5)