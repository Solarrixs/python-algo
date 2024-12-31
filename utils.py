from functools import wraps
import time
import logging

def retry(max_attempts=3, delay=5, backoff=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        logging.error(f"Final attempt failed: {e}")
                        raise
                    logging.warning(f"Attempt {attempts} failed: {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff
            return None
        return wrapper
    return decorator