import os, sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from functools import wraps, partial
from multiprocessing.pool import ThreadPool
from inspect import isgeneratorfunction
from overload import overload
from strict_functions import strict_globals

def queued(fn, workers=1):
    assert callable(fn), 'fn needs to be callable'
    assert type(workers)==int
    assert workers>0
    #print('making {} into a queued function with {} workers'.format(fn, workers))
    return wraps(fn)(
        lambda *a, f=fn, p=ThreadPool(workers):(
            p.starmap_async(f, [a])
        )
    )
    
@overload
def queued(fn, workers=1):
    ''' this adapts queued to accept generator functions as wrapped input '''
    assert isgeneratorfunction(fn)
    #print('converting coroutine fn into a function')
    f=fn().send # convert the coroutine into a function
    f(None) # start the coroutine
    return wraps(fn)(queued(
        (lambda *a, f=f:(f(*a) if len(a)==1 else f(a))),
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
    from time import sleep
    
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
            c=a+b
            print(('gen',a,b,c))

    @queued(workers=3)
    def three_adders(a, b):
        ''' my_adder with multiple workers '''
        sleep(1)
        c=a+b
        print(('three',a,b,c))

    for i in range(10):
        my_adder(i, i*2)
        adder_gen(i, i*2)
        three_adders(i, i*2)
        
if __name__ == '__main__':
    # run the demo if this is the script being ran
    test()
