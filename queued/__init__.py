import os, sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from functools import wraps, partial
from multiprocessing.pool import ThreadPool
from inspect import isgeneratorfunction
from strict_functions import strict_globals, overload
from greater_context import logged_exceptions
import logging
import atexit
from time import sleep
from collections import defaultdict
from itertools import cycle

class default(object):
    ''' this class is used as a shared namespace for queued's defaults '''
    logger=logging.exception
    workers=1

job_counter = defaultdict(int)
    
def new_job(fn):
    job_counter[getattr(fn, 'func', fn)]+=1
    
def finished_job(fn):
    job_counter[getattr(fn, 'func', fn)]+=-1
    
def workers_are_busy():
    return any(job_counter.values())

def wait_for_queues_to_finish():
    while workers_are_busy():
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
        lambda *a, **k: [
            new_job(fn), 
            pool.starmap_async(call, [[partial(fn, *a, **k), logger]])
        ]
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
