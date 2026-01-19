import logging
import traceback

logger = logging.getLogger(__name__)

def catch_error(error_id):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"[{error_id}] Exception in {func.__name__}: {e}")
                logger.debug(traceback.format_exc())
                return {"error": error_id}
        return wrapper
    return decorator

__all__ = ["catch_error"]
