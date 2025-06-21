#!/usr/bin/env python3
"""Logging utilities for {{cookiecutter.project_name}}."""

import logging
import sys
from pathlib import Path
from typing import Optional

import structlog
from pythonjsonlogger import jsonlogger


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    format_type: str = "json",
    include_context: bool = True
) -> None:
    """Set up logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        format_type: Log format type ("json" or "plain")
        include_context: Whether to include context information
    """
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if format_type == "json" else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Set up standard logging
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if format_type == "json":
        formatter = jsonlogger.JsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s",
            timestamp=True
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


class LogContext:
    """Context manager for adding temporary log context."""
    
    def __init__(self, logger: structlog.BoundLogger, **kwargs):
        """Initialize log context.
        
        Args:
            logger: Logger instance
            **kwargs: Context key-value pairs
        """
        self.logger = logger
        self.context = kwargs
        self.bound_logger = None
    
    def __enter__(self):
        """Enter context and bind values."""
        self.bound_logger = self.logger.bind(**self.context)
        return self.bound_logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and unbind values."""
        # Context is automatically cleaned up
        pass


def log_execution_time(func):
    """Decorator to log function execution time.
    
    Args:
        func: Function to decorate
    
    Returns:
        Decorated function
    """
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(
                "function_executed",
                function=func.__name__,
                execution_time=execution_time,
                status="success"
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                "function_failed",
                function=func.__name__,
                execution_time=execution_time,
                error=str(e),
                status="error"
            )
            raise
    
    return wrapper


def log_data_shape(df, operation: str, logger: structlog.BoundLogger) -> None:
    """Log dataframe shape information.
    
    Args:
        df: Pandas DataFrame
        operation: Description of the operation
        logger: Logger instance
    """
    logger.info(
        "data_shape",
        operation=operation,
        rows=len(df),
        columns=len(df.columns),
        memory_usage=df.memory_usage(deep=True).sum() / 1024 / 1024,  # MB
        dtypes=df.dtypes.value_counts().to_dict()
    )


class MLFlowLogHandler(logging.Handler):
    """Custom log handler for MLflow integration."""
    
    def __init__(self):
        """Initialize MLflow log handler."""
        super().__init__()
        try:
            import mlflow
            self.mlflow = mlflow
        except ImportError:
            self.mlflow = None
    
    def emit(self, record):
        """Emit log record to MLflow."""
        if self.mlflow and hasattr(self.mlflow, "active_run"):
            if self.mlflow.active_run():
                # Log important messages as MLflow tags
                if record.levelno >= logging.WARNING:
                    self.mlflow.set_tag(
                        f"warning_{record.created}",
                        self.format(record)
                    )