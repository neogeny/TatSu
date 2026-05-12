import sys
import time


class Logger:
    def __init__(self, fmt="[{name}] {level}: {message}", stream=sys.stderr):
        self.fmt = fmt
        self.stream = stream
        self.defaults = {"name": "tatsu"}

    def log(self, level, message, **kwargs):
        # Merge defaults with dynamic context (like timestamps or line numbers)
        context = {
            **self.defaults,
            "level": level,
            "message": message,
            "timestamp": time.strftime("%H:%M:%S"),
            **kwargs,
        }
        # Explicit write to the chosen stream
        self.stream.write(self.fmt.format(**context) + "\n")
        self.stream.flush()


# Usage:
# logger = Logger(fmt="{timestamp} | {level} | {message}")
# logger.log("INFO", "Parsing grammar...")
