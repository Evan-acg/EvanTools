import threading


class RWLock:
    """读写锁：允许多个读，一个写（非可重入）。"""

    def __init__(self):
        """初始化读写锁。"""
        self._read_ready = threading.Condition(threading.Lock())
        self._readers = 0

    def acquire_read(self):
        """获取读锁。"""
        with self._read_ready:
            self._readers += 1

    def release_read(self):
        """释放读锁。"""
        with self._read_ready:
            self._readers -= 1
            if self._readers == 0:
                self._read_ready.notify_all()

    def acquire_write(self):
        """获取写锁。"""
        self._read_ready.acquire()
        while self._readers > 0:
            self._read_ready.wait()

    def release_write(self):
        """释放写锁。"""
        self._read_ready.release()
