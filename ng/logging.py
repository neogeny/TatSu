import sys
import threading

# Global registry to ensure one SyncStream per physical stream object
_SYNC_STREAMS = {}
_REGISTRY_LOCK = threading.Lock()

class SyncStream:
    """Wraps a stream to ensure atomic write and flush operations."""
    def __init__(self, stream):
        self._stream = stream
        self._lock = threading.Lock()

    def write(self, data):
        with self._lock:
            return self._stream.write(data)

    def flush(self):
        with self._lock:
            return self._stream.flush()

    def __getattr__(self, name):
        return getattr(self._stream, name)

def get_sync_stream(stream):
    """Retrieves or creates a SyncStream for the given stream."""
    if isinstance(stream, SyncStream):
        return stream

    stream_id = id(stream)
    with _REGISTRY_LOCK:
        if stream_id not in _SYNC_STREAMS:
            _SYNC_STREAMS[stream_id] = SyncStream(stream)
        return _SYNC_STREAMS[stream_id]

class Logger:
    def __init__(self, fmt="[{name}] {level}: {message}", stream=sys.stderr):
        self.fmt = fmt
        self.stream = get_sync_stream(stream)
        self.defaults = {"name": "tatsu"}

    def log(self, level, message, **kwargs):
        context = {**self.defaults, "level": level, "message": message, **kwargs}
        # Format outside the lock, write inside the lock
        self.stream.write(self.fmt.format(**context) + "\n")
        self.stream.flush()
