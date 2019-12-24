import os, time
from functools import wraps, partial, lru_cache
from logging import exception, root
import multiprocessing
import multiprocessing.queues
from strict_functions import overload
from threading import Thread
from multiprocessing import Process
from time import sleep
from atexit import register
from gc import collect
from signal import signal, SIGINT, SIGKILL
from os import kill, getpid
import threading
 
@partial(signal, SIGINT)
def kill_process(*args):
    kill(getpid(), SIGKILL)
    
IterableQueue = multiprocessing.queues.JoinableQueue

def _iter(self):
    while True:
        yield self.get()

IterableQueue.__iter__ = _iter
IterableQueue.__len__ = IterableQueue.qsize

class STORAGE(object):
    settings={
        'maxsize':0,
        'workers':1,
        'restart':True,
        'logger':exception
    }
    queues=[]
    threads=[]
 
def queue_sizes():
    return [len(q) for q in STORAGE.queues]
 
def finish_tasks(kill_threads=False):
    # wait for all tasks to finish
    while sum(len(q) for q in STORAGE.queues):
        #print('+',sum(queue_sizes()))
        #print(queue_sizes())
        sleep(0.1)
    # then kill all threads
    if kill_threads:
        for t in STORAGE.threads:
            t.terminate()
        STORAGE.threads = []
        STORAGE.queues = []
        collect(1)
        
register(partial(finish_tasks, True))

def start_queue_worker(fn, q, restart, logger):
    assert callable(fn)
    assert isinstance(q, IterableQueue)
    assert isinstance(restart, bool)
    assert callable(logger)
 
    if restart:
        def runner(fn, q, logger):
            try:
                while 1:
                    try:
                        fn(q)
                    except Exception as ex:
                        logger(ex)
                        sleep(0.1)
            finally:
                kill(getpid(), SIGKILL)
    else:
        def runner(fn, q, logger):
            try:
                fn(q)
            except Exception as ex:
                logger(ex)
            finally:
                kill(getpid(), SIGKILL)
 
    t=Process(target=runner, args=[fn, q, logger], daemon=False)
    STORAGE.threads.append(t)
    t.start()
 
@overload
def queued(firin, settings={}):
    assert isinstance(settings, dict)
    assert callable(firin)
    if not settings:
        settings=STORAGE.settings
 
    q = IterableQueue(maxsize=settings['maxsize'], ctx=multiprocessing.get_context())
    STORAGE.queues.append(q)
 
    for _ in range(settings['workers']):
        start_queue_worker(
            firin,
            q,
            settings['restart'],
            settings['logger']
        )
 
    @wraps(firin)
    def imma_firin(mah_lazarz):
        ''' this replacces the function with q.put but preserves docstrings of the wrapped function '''
        q.put(mah_lazarz)
 
    return imma_firin
 
@overload
def queued(maxsize=0, workers=1, restart=True, logger=exception):
    assert isinstance(maxsize, int) and maxsize>=0
    assert isinstance(workers, int) and workers>0
    assert isinstance(restart, bool)
    assert callable(logger)
    return partial(
        queued,
        settings={
            'maxsize':maxsize,
            'workers':workers,
            'restart':restart,
            'logger':logger
        })
 
 
 
if __name__ == '__main__':
    @queued(workers=10)
    def add(queued_items):
        total = 0
        for i in queued_items:
            total += i
            print(total, os.getpid(), os.getppid())
            time.sleep(0.1)

    @queued(workers=10)
    def add_parallel(queued_items):
        total = 0
        for i in queued_items:
            sleep(3)
            total += i
            print(total, '-', os.getpid(), os.getppid())
            add(i)
    for i in range(30):
        add(1)
        add_parallel(1)
 
    add(1)
    add(1)
    add(1)
    print('finishing')
    finish_tasks()
    print('finished')
    exit()