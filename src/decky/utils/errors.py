"""
Error handling utilities and boundaries for Decky.

Provides consistent error handling patterns across the codebase.
"""

import logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

# Type variable for generic function decoration
F = TypeVar("F", bound=Callable[..., Any])


def error_boundary(
    *,
    reraise: bool = False,
    default_return: Any = None,
    log_level: int = logging.ERROR,
) -> Callable[[F], F]:
    """
    Decorator to create consistent error boundaries around functions.

    This provides a standard way to handle exceptions across the codebase,
    ensuring errors are logged consistently and handled appropriately.

    Args:
        reraise: If True, re-raise the exception after logging
        default_return: Value to return if error occurs and not reraising
        log_level: Logging level for the error (default: ERROR)

    Returns:
        Decorated function with error handling

    Example:
        >>> @error_boundary(default_return=False)
        ... def execute_action(config):
        ...     # If this raises, it will be logged and return False
        ...     subprocess.run(config['command'], check=True)
        ...     return True
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Log the error with full context
                logger.log(
                    log_level,
                    f"Error in {func.__name__}: {e}",
                    exc_info=True,
                    extra={"function": func.__name__, "module": func.__module__},
                )

                # Re-raise if requested
                if reraise:
                    raise

                # Otherwise return default value
                return default_return

        return wrapper  # type: ignore

    return decorator


def safe_execute(
    func: Callable[[], Any],
    *,
    on_error: Optional[Callable[[Exception], Any]] = None,
    default: Any = None,
) -> Any:
    """
    Safely execute a function with error handling.

    Useful for one-off operations where a decorator isn't appropriate.

    Args:
        func: Function to execute
        on_error: Optional callback to call if error occurs (receives exception)
        default: Default value to return on error

    Returns:
        Function result, or default value on error

    Example:
        >>> result = safe_execute(
        ...     lambda: int(user_input),
        ...     on_error=lambda e: print(f"Invalid input: {e}"),
        ...     default=0
        ... )
    """
    try:
        return func()
    except Exception as e:
        logger.error(f"Error in safe_execute: {e}", exc_info=True)
        if on_error:
            on_error(e)
        return default


class DeckyError(Exception):
    """Base exception for all Decky-specific errors."""

    pass


class DeviceError(DeckyError):
    """Raised when there's an issue with the Stream Deck device."""

    pass


class ConfigurationError(DeckyError):
    """Raised when there's an issue with configuration."""

    pass


class ActionExecutionError(DeckyError):
    """Raised when an action fails to execute."""

    pass


class PlatformError(DeckyError):
    """Raised when there's a platform-specific error."""

    pass
