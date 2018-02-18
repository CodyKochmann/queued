import os, sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from functools import wraps, partial
from multiprocessing.pool import ThreadPool
from multiprocessing import Pool
from inspect import isgeneratorfunction
from strict_functions import strict_globals, overload
from greater_context import logged_exceptions
import logging
import atexit
from time import sleep

class default(object):
    ''' this class is used as a shared namespace for queued's defaults '''
    logger=logging.exception
    workers=1
    multiprocessing=False

class storage(object):
    queues = []

@atexit.register
def wait_for_queues_to_finish():
    while all((not q._taskqueue.empty()) for q in storage.queues):
        sleep(0.25)

def call(fn, logger):
    #logging.warning('call is being called with - {}'.format(locals()))
    with logged_exceptions(logger):
        return fn()

def queued(fn, workers=1, logger=default.logger, multiprocessing=default.multiprocessing):
    assert callable(fn), 'fn needs to be callable'
    assert type(workers)==int
    assert workers>0
    assert not isgeneratorfunction(fn)
    #print('making {} into a queued function with {} workers'.format(fn, workers))
    pool = (Pool if multiprocessing else ThreadPool)(workers)
    storage.queues.append(pool)
    return wraps(fn)(
        lambda *args, **kwargs: pool.starmap_async(call, [(partial(fn, *args, **kwargs), logger)])
    )


@overload
def queued(fn, workers=1):
    ''' this adapts queued to accept generator functions as wrapped input '''
    assert isgeneratorfunction(fn)
    #print('converting coroutine fn into a function')
    f=fn().send # convert the coroutine into a function
    f(None) # start the coroutine
    return wraps(fn)(queued(
        lambda *a: f(*a) if len(a) == 1 else f(a),
        workers
    ))

@overload
def queued(workers=1):
    ''' this adapts queued to take arguments before wrapping a function '''
    assert type(workers)==int
    assert workers>1
    return partial(queued, workers=workers)

def test():
    ''' this tests/demos different uses of queued '''
    @queued
    def my_adder(a, b):
        ''' my_adder as a nonblocking function '''
        #sleep(1)
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
    def three_adders(a, b):
        ''' my_adder with multiple workers '''
        print('three_adders',locals())
        #sleep(1)
        c=a+b
        print(('three',a,b,c))

    for i in range(10):
        my_adder(i, i*2)
        adder_gen(i, i*2)
        three_adders(i, i*2)

if __name__ == '__main__':
    # run the demo if this is the script being ran
    test()
