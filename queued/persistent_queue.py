from multiprocessing import Lock, Queue
from queue import Empty
from stat import S_IRUSR, S_IWUSR
from typing import Any, Iterator
from uuid import uuid4
import shelve, os, logging

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)

class PersistentQueue(object):
    def __init__(self, path:str):
        self._path = path[:-3] if path.endswith('.db') else path
        new_db = not os.path.exists(self._path + '.db')
        self._db = shelve.open(self._path)
        self._path = self._path + '.db'
        self._lock = Lock() # protects from multiple writers to the db
        self._q = Queue() # provides multiprocessing queue logic, this wont inherit cleanly
        if new_db:
            logging.debug('new database detected at - %s', self._path)
            self._tighten_permissions()
        else:
            logging.debug('loading queued values from - %s', self._path)
            for key in self._db:
                self._q.put(key)

    def put(self, item:Any) -> None:
        with self._lock:
            key = self._new_key()
            self._db[key] = item
            self._q.put(key)

    def get(self, block=True, timeout=None) -> Any:
        key = self._q.get(block=block, timeout=timeout)
        with self._lock:
            return self._db.pop(key)

    def put_nowait(self, item:Any) -> None:
        return self.put(item, block=False)

    def get_nowait(self) -> Any:
        return self.get(block=False)

    def __iter__(self) -> Iterator[Any]:
        stopper = object()
        yield from iter(self.get, stopper)

    def iter_until_empty(self) -> Iterator[Any]:
        stopper = object()
        try:
            yield from iter(self.get_nowait, stopper)
        except Empty:
            pass

    def __len__(self) -> int:
        with self._lock:
            return len(self._db)

    def __repr__(self) -> str:
        return 'PersistentQueue(path={})'.format(repr(self._path))

    def _new_key(self) -> str:
        for i in iter(uuid4, None):
            key = i.hex
            if key not in self._db:
                return key

    def _tighten_permissions(self) -> None:
        '''sets the permissions to user read/write'''
        logging.debug('tightening permissions for - %s', self._path)
        try:
            os.chmod(self._path, (S_IRUSR | S_IWUSR))  # set read and write permissions
        except Exception as ex:
            logging.exception(ex)

    def disk_size(self) -> int:
        '''returns the used disk size in bytes (1,000,000 = 1MB)'''
        return os.path.getsize(self._path)

if __name__ == '__main__':
    p = os.path.join('/tmp', str(uuid4()))
    q = PersistentQueue(p)
    for i in range(2):
        q.put(i)
        q.put(str(i))
        q.put(repr(str(i)))
        q.put(i*30)
    for i in range(8):
        logging.debug('get - %s - %s', i, repr(q.get()))
    for i in range(2):
        q.put(i)
        q.put(str(i))
        q.put(repr(str(i)))
        q.put(i*30)
    for i,v in enumerate(q.iter_until_empty()):
        logging.debug('iter_until_empty - %s - %s', i, v)
    for i in range(2000):
        q.put(i)
        q.put(str(i))
        q.put(repr(str(i)))
        q.put(i*30)
        logging.debug('size - %s %s', len(q), q.disk_size())
    for i in q:
        logging.debug('size - %s %s', len(q), q.disk_size())
    
