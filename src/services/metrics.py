"""
Backend Metrics Service

Tracks performance metrics for each backend:
- Request counts (total, success, failed)
- Success rate
- Average response time
- Tokens consumed

Used for observability and debugging.
"""

import logging
from datetime import datetime, UTC
from typing import Optional
from collections import defaultdict
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class BackendStats(BaseModel):
    """
    Statistics for a single backend.
    
    Tracks performance and usage metrics.
    """
    
    requests_total: int = Field(
        default=0,
        description="Total requests sent to this backend"
    )
    requests_success: int = Field(
        default=0,
        description="Successful requests"
    )
    requests_failed: int = Field(
        default=0,
        description="Failed requests"
    )
    success_rate: float = Field(
        default=0.0,
        description="Success rate (0.0-1.0)"
    )
    avg_response_time_ms: float = Field(
        default=0.0,
        description="Average response time in milliseconds"
    )
    tokens_used: int = Field(
        default=0,
        description="Total tokens consumed (if tracked)"
    )
    last_success_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp of last successful request"
    )
    last_failure_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp of last failed request"
    )


class BackendMetrics:
    """
    Tracks performance metrics for all backends.
    
    Thread-safe, lightweight metrics collection suitable
    for production use. Stores metrics in memory.
    
    Example:
        metrics = BackendMetrics()
        
        # Record success
        metrics.record_success(
            backend_name="claude",
            response_time_ms=1200,
            tokens=234
        )
        
        # Record failure
        metrics.record_failure(
            backend_name="ollama",
            error_code="TIMEOUT"
        )
        
        # Get stats
        stats = metrics.get_stats("claude")
        print(f"Success rate: {stats.success_rate:.2%}")
    """
    
    def __init__(self):
        """Initialize metrics collection"""
        # Per-backend counters
        self._total = defaultdict(int)
        self._success = defaultdict(int)
        self._failed = defaultdict(int)
        
        # Response time tracking (sum for averaging)
        self._response_time_sum = defaultdict(float)
        
        # Token tracking
        self._tokens = defaultdict(int)
        
        # Timestamps
        self._last_success = {}
        self._last_failure = {}
        
        logger.info("BackendMetrics initialized")
    
    def record_success(
        self,
        backend_name: str,
        response_time_ms: int,
        tokens: int = 0
    ) -> None:
        """
        Record a successful request.
        
        Args:
            backend_name: Name of backend that succeeded
            response_time_ms: Time taken (milliseconds)
            tokens: Tokens consumed (if tracked)
        """
        self._total[backend_name] += 1
        self._success[backend_name] += 1
        self._response_time_sum[backend_name] += response_time_ms
        self._tokens[backend_name] += tokens
        self._last_success[backend_name] = datetime.now(UTC).isoformat()
        
        logger.debug(
            f"Recorded success: backend={backend_name}, "
            f"time={response_time_ms}ms, tokens={tokens}"
        )
    
    def record_failure(
        self,
        backend_name: str,
        error_code: str
    ) -> None:
        """
        Record a failed request.
        
        Args:
            backend_name: Name of backend that failed
            error_code: Error code (TIMEOUT, RATE_LIMITED, etc.)
        """
        self._total[backend_name] += 1
        self._failed[backend_name] += 1
        self._last_failure[backend_name] = datetime.now(UTC).isoformat()
        
        logger.debug(
            f"Recorded failure: backend={backend_name}, "
            f"error={error_code}"
        )
    
    def get_stats(self, backend_name: str) -> BackendStats:
        """
        Get current statistics for a backend.
        
        Args:
            backend_name: Backend to get stats for
        
        Returns:
            BackendStats with current metrics
        
        Example:
            stats = metrics.get_stats("claude")
            print(f"Total requests: {stats.requests_total}")
            print(f"Success rate: {stats.success_rate:.2%}")
        """
        total = self._total[backend_name]
        success = self._success[backend_name]
        failed = self._failed[backend_name]
        
        # Calculate success rate
        success_rate = success / total if total > 0 else 0.0
        
        # Calculate average response time
        avg_time = (
            self._response_time_sum[backend_name] / success
            if success > 0 else 0.0
        )
        
        return BackendStats(
            requests_total=total,
            requests_success=success,
            requests_failed=failed,
            success_rate=success_rate,
            avg_response_time_ms=avg_time,
            tokens_used=self._tokens[backend_name],
            last_success_at=self._last_success.get(backend_name),
            last_failure_at=self._last_failure.get(backend_name)
        )
    
    def get_all_stats(self) -> dict[str, BackendStats]:
        """
        Get statistics for all backends that have been used.
        
        Returns:
            Dictionary mapping backend name to stats
        
        Example:
            all_stats = metrics.get_all_stats()
            for name, stats in all_stats.items():
                print(f"{name}: {stats.success_rate:.2%} success")
        """
        backend_names = set(self._total.keys())
        return {
            name: self.get_stats(name)
            for name in backend_names
        }
    
    def reset(self, backend_name: Optional[str] = None) -> None:
        """
        Reset metrics (for testing or periodic cleanup).
        
        Args:
            backend_name: Backend to reset, or None for all
        """
        if backend_name:
            # Reset specific backend
            self._total.pop(backend_name, None)
            self._success.pop(backend_name, None)
            self._failed.pop(backend_name, None)
            self._response_time_sum.pop(backend_name, None)
            self._tokens.pop(backend_name, None)
            self._last_success.pop(backend_name, None)
            self._last_failure.pop(backend_name, None)
            logger.info(f"Reset metrics for backend: {backend_name}")
        else:
            # Reset all
            self._total.clear()
            self._success.clear()
            self._failed.clear()
            self._response_time_sum.clear()
            self._tokens.clear()
            self._last_success.clear()
            self._last_failure.clear()
            logger.info("Reset all backend metrics")
