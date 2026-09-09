import logging
import sys
import os
from collections import deque
from typing import List, Dict, Any

# In-memory log buffer for UI streaming (max 500 lines)
LOG_BUFFER = deque(maxlen=500)

class MemoryLogHandler(logging.Handler):
    """Custom logging handler that buffers logs in memory for UI streaming."""
    def emit(self, record):
        try:
            msg = self.format(record)
            LOG_BUFFER.append({
                "timestamp": record.created,
                "asctime": self.formatter.formatTime(record) if self.formatter else "",
                "level": record.levelname,
                "name": record.name,
                "message": record.getMessage()
            })
        except Exception:
            self.handleError(record)

def setup_logger(log_file: str = "lazy_jobber.log", level: int = logging.INFO) -> logging.Logger:
    """Configures root logger with console, file, and memory ring buffer handlers."""
    logger = logging.getLogger("lazy_jobber")
    logger.setLevel(level)

    # Avoid duplicate handlers if re-initialized
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler
    try:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception as e:
        sys.stderr.write(f"Warning: Could not set up file logger: {e}\n")

    # Memory Handler for Web Dashboard
    mh = MemoryLogHandler()
    mh.setLevel(level)
    mh.setFormatter(formatter)
    logger.addHandler(mh)

    return logger

def get_logger(name: str = "app") -> logging.Logger:
    return logging.getLogger(f"lazy_jobber.{name}")

def get_recent_logs(limit: int = 100) -> List[Dict[str, Any]]:
    """Returns recent log entries from the ring buffer."""
    logs = list(LOG_BUFFER)
    return logs[-limit:]
