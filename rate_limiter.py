import time

class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period
        self.calls = []

    def __enter__(self):
        now = time.time()
        self.calls = [call for call in self.calls if call > now - self.period]
        if len(self.calls) >= self.max_calls:
            sleep_time = self.calls[0] - (now - self.period)
            sleep_time = max(sleep_time, 0)
            time.sleep(sleep_time)
        self.calls.append(now)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass