"""
Lightweight circuit breaker for external service calls.

Prevents cascade failures by failing fast when a dependency is down,
instead of waiting for timeouts on every request.

States:
  CLOSED   – requests flow normally; failures are counted
  OPEN     – requests are rejected immediately (fail-fast)
  HALF_OPEN – a limited number of probe requests are allowed through
"""
import time
import threading
import logging

logger = logging.getLogger(__name__)


class CircuitBreaker:
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'

    def __init__(self, name, failure_threshold=5, recovery_timeout=60,
                 half_open_max_calls=1):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self._state = self.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0
        self._half_open_calls = 0
        self._lock = threading.Lock()

    @property
    def state(self):
        with self._lock:
            if (self._state == self.OPEN
                    and time.time() - self._last_failure_time >= self.recovery_timeout):
                self._state = self.HALF_OPEN
                self._half_open_calls = 0
            return self._state

    def allow_request(self):
        s = self.state
        if s == self.CLOSED:
            return True
        if s == self.HALF_OPEN:
            with self._lock:
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
            return False
        return False  # OPEN

    def record_success(self):
        with self._lock:
            if self._state == self.HALF_OPEN:
                logger.info("Circuit breaker '%s' CLOSED (recovered)", self.name)
            self._failure_count = 0
            self._state = self.CLOSED

    def record_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._failure_count >= self.failure_threshold:
                prev = self._state
                self._state = self.OPEN
                if prev != self.OPEN:
                    logger.warning(
                        "Circuit breaker '%s' OPENED after %d failures",
                        self.name, self._failure_count,
                    )

    @property
    def metrics(self):
        """Return current state as a numeric value for Prometheus export."""
        s = self.state
        return {self.CLOSED: 0, self.HALF_OPEN: 1, self.OPEN: 2}.get(s, -1)


# Pre-configured breakers
vision_breaker = CircuitBreaker(
    'claude_vision', failure_threshold=3, recovery_timeout=120,
)
tesseract_breaker = CircuitBreaker(
    'tesseract_ocr', failure_threshold=5, recovery_timeout=60,
)
