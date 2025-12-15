"""
Rate limiting utilities for TSS Converter Web Application
Provides protection against abuse and resource exhaustion
"""

import time
from collections import defaultdict, deque
from typing import Dict, Optional
import threading
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int = 10
    requests_per_hour: int = 100
    max_file_size_mb: int = 50
    max_concurrent_sessions: int = 3
    cleanup_interval_minutes: int = 10

class RateLimiter:
    """
    Thread-safe rate limiter for web application
    Tracks requests per IP address and session
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        
        # Track requests by IP address
        self._requests_per_minute: Dict[str, deque] = defaultdict(deque)
        self._requests_per_hour: Dict[str, deque] = defaultdict(deque)
        
        # Track active sessions
        self._active_sessions: Dict[str, float] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Start cleanup thread
        self._start_cleanup_thread()
        
    def _start_cleanup_thread(self):
        """Start background thread for cleanup"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(self.config.cleanup_interval_minutes * 60)
                    self._cleanup_old_entries()
                except Exception as e:
                    logger.error(f"Rate limiter cleanup error: {e}")
                    
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.info("Rate limiter cleanup thread started")
        
    def _cleanup_old_entries(self):
        """Remove old entries to prevent memory buildup"""
        current_time = time.time()
        
        with self._lock:
            # Cleanup minute tracking
            for ip, requests in list(self._requests_per_minute.items()):
                while requests and current_time - requests[0] > 60:
                    requests.popleft()
                if not requests:
                    del self._requests_per_minute[ip]
            
            # Cleanup hour tracking  
            for ip, requests in list(self._requests_per_hour.items()):
                while requests and current_time - requests[0] > 3600:
                    requests.popleft()
                if not requests:
                    del self._requests_per_hour[ip]
            
            # Cleanup old sessions (assume session timeout of 30 minutes)
            old_sessions = [
                session_id for session_id, timestamp in self._active_sessions.items()
                if current_time - timestamp > 1800  # 30 minutes
            ]
            for session_id in old_sessions:
                del self._active_sessions[session_id]
                
        logger.debug(f"Rate limiter cleanup completed. Active IPs: {len(self._requests_per_minute)}")
        
    def check_rate_limit(self, client_ip: str) -> tuple[bool, str]:
        """
        Check if request should be allowed based on rate limits
        
        Args:
            client_ip: Client IP address
            
        Returns:
            Tuple of (allowed, reason)
        """
        current_time = time.time()
        
        with self._lock:
            # Check minute limit
            minute_requests = self._requests_per_minute[client_ip]
            while minute_requests and current_time - minute_requests[0] > 60:
                minute_requests.popleft()
                
            if len(minute_requests) >= self.config.requests_per_minute:
                return False, f"Rate limit exceeded: {self.config.requests_per_minute} requests per minute"
            
            # Check hour limit
            hour_requests = self._requests_per_hour[client_ip]
            while hour_requests and current_time - hour_requests[0] > 3600:
                hour_requests.popleft()
                
            if len(hour_requests) >= self.config.requests_per_hour:
                return False, f"Rate limit exceeded: {self.config.requests_per_hour} requests per hour"
            
            # Record this request
            minute_requests.append(current_time)
            hour_requests.append(current_time)
            
            return True, "Request allowed"
    
    def check_concurrent_sessions(self, session_id: str) -> tuple[bool, str]:
        """
        Check and track concurrent sessions
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Tuple of (allowed, reason)
        """
        current_time = time.time()
        
        with self._lock:
            # Update this session's timestamp
            self._active_sessions[session_id] = current_time
            
            # Count active sessions (last 30 minutes)
            active_count = sum(
                1 for timestamp in self._active_sessions.values()
                if current_time - timestamp <= 1800
            )
            
            if active_count > self.config.max_concurrent_sessions:
                return False, f"Too many concurrent sessions: {active_count}/{self.config.max_concurrent_sessions}"
            
            return True, f"Session allowed: {active_count}/{self.config.max_concurrent_sessions}"
    
    def get_stats(self) -> Dict[str, int]:
        """Get current rate limiter statistics"""
        current_time = time.time()
        
        with self._lock:
            # Count active IPs in last minute
            active_ips_minute = sum(
                1 for requests in self._requests_per_minute.values()
                if any(current_time - req <= 60 for req in requests)
            )
            
            # Count active sessions
            active_sessions = sum(
                1 for timestamp in self._active_sessions.values()
                if current_time - timestamp <= 1800
            )
            
            return {
                "active_ips_per_minute": active_ips_minute,
                "active_sessions": active_sessions,
                "total_tracked_ips": len(self._requests_per_minute),
                "total_sessions": len(self._active_sessions)
            }

# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None

def get_rate_limiter(config: Optional[RateLimitConfig] = None) -> RateLimiter:
    """Get or create global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(config)
    return _rate_limiter

def check_request_allowed(client_ip: str, session_id: str) -> tuple[bool, str]:
    """
    Convenience function to check if request should be allowed
    
    Args:
        client_ip: Client IP address
        session_id: Session identifier
        
    Returns:
        Tuple of (allowed, reason)
    """
    limiter = get_rate_limiter()
    
    # Check rate limits
    allowed, reason = limiter.check_rate_limit(client_ip)
    if not allowed:
        logger.warning(f"Rate limit exceeded for {client_ip}: {reason}")
        return False, reason
    
    # Check concurrent sessions
    allowed, reason = limiter.check_concurrent_sessions(session_id)
    if not allowed:
        logger.warning(f"Concurrent session limit exceeded for session {session_id}: {reason}")
        return False, reason
    
    return True, "Request allowed"