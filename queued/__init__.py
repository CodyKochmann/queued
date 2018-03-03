import os, sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from functools import wraps, partial
from multiprocessing.pool import ThreadPool
from threading import Thread, Lock
from inspect import isgeneratorfunction
from strict_functions import strict_globals, overload
from greater_context import logged_exceptions
import logging
import atexit
from time import sleep
from collections import defaultdict, deque
from itertools import cycle

import signal

@partial(signal.signal, signal.SIGINT)
def kill_process(*args):
    os.kill(os.getpid(), signal.SIGKILL)


class default(object):
    ''' this class is used as a shared namespace for queued's defaults '''
    logger=logging.exception
    workers=1

class task_collection(set):
    ''' this is used as a storage for threading tasks to identify when all
        async tasks have been finished '''
    def __init__(self):
        set.__init__(self)
        self.autocleaning = False
        self.autoclean_thread = Thread(target=self.autoclean)
        self.autoclean_thread.setDaemon(True)
        self.lock = Lock()
        self.start_autoclean()
    def toggle(self, target, add=False):
        with self.lock:
            (self.add if add else self.discard)(target)
    def store(self, target):
        self.toggle(target, True)
    def delete(self, target):
        self.toggle(target, False)
    def clean(self):
        if len(self):
            with self.lock:
                l = list(self)
            for task in l:
                if task.ready():
                    self.delete(task)
    def autoclean(self):
        if self.autocleaning:
            raise Exception('task_collection is already autocleaning')
        while 1:
            sleep(6)
            self.clean()
    def start_autoclean(self):
        self.autoclean_thread.start()
    @property
    def has_unfinished_tasks(self):
        ''' returns true if there are still unfinished jobs in self '''
        self.clean()
        return bool(len(tasks))

tasks = task_collection()

def store_task(task, tasks=tasks):
    tasks.store(task)

def wait_for_queues_to_finish(tasks=tasks):
    while tasks.has_unfinished_tasks:
        sleep(0.2)

atexit.register(wait_for_queues_to_finish)

def call(fn, logger):
    with logged_exceptions(logger):
        fn()
    finished_job(fn)

def queued(fn, workers=1, logger=default.logger):
    assert callable(fn), 'fn needs to be callable'
    assert type(workers)==int
    assert workers>0
    assert not isgeneratorfunction(fn)
    pool = ThreadPool(workers)
    return wraps(fn)(
        lambda *a, **k: (store_task(pool.apply_async(call, (partial(fn, *a, **k), logger))), pool._cache.clear())[0]
    )

@overload
def queued(fn, workers=default.workers, logger=default.logger):
    ''' this adapts queued to accept generator functions as a valid input '''
    assert isgeneratorfunction(fn)
    # multiple generator workers means starting multiple generators since they are
    # sequential state machines and cant run non-linearly
    _gens = [fn().send for _ in range(workers)]
    # start each generator
    {i(None) for i in _gens}
    # turn each function into a queued service
    worker_queues=[queued(i, logger=logger) for i in _gens]
    # make a round-robin dispatcher for the generator workers
    def next_worker(cycler=cycle(worker_queues)):
        return next(cycler)
    @wraps(fn)
    @queued # the dispatcher needs to be a single threaded queue
    def dispatcher(*args): # sending to generators is only positional
        if len(args)==1:
            next_worker()(*args)
        else:
            next_worker()(args)
    return dispatcher


@overload
def queued(workers=1, logger=default.logger):
    ''' this adapts queued to take arguments before wrapping a function '''
    assert type(workers)==int
    assert workers>1
    return partial(queued, workers=workers, logger=logger)


def test():
    ''' this tests/demos different uses of queued '''
    @queued
    def my_adder(a, b):
        ''' my_adder as a nonblocking function '''
        sleep(1)
        c=a+b
        print(('adder',a,b,c))

    @queued
    def adder_gen():
        ''' my_adder as a nonblocking coroutine '''
        while 1:
            a, b = yield
            with logged_exceptions():
                c=a+b
                print(('gen',a,b,c))

    @queued(workers=3)
    def three_adder_gen():
        ''' this as a nonblocking coroutine run under three working generators '''
        while 1:
            a, b = yield
            c=a+b
            print(('three_adder_gen',a,b,c))

    @queued(workers=3)
    def three_adders(a, b):
        ''' my_adder with multiple workers '''
        #print('three_adders',locals())
        sleep(1)
        c=a+b
        print(('three',a,b,c))
        #my_adder(a,b)
        #my_adder(b,c)

    for i in range(10):
        my_adder(i, i*2)
        adder_gen(i, i*2)
        three_adders(i, i*2)
        three_adder_gen(i, i*2)

if __name__ == '__main__':
    # run the demo if this is the script being ran
    test()
