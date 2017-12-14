# -*- coding: utf-8 -*-
# @Author: Cody Kochmann
# @Date:   2017-12-12 14:01:56
# @Last Modified 2017-12-14
# @Last Modified time: 2017-12-14 13:59:12

from multiprocessing import Queue
from functools import wraps
from threading import Thread
from time import sleep, time

try:
    from strict_functions import noglobals, strict_globals
except ImportError:
    exit('failed importing strict_functions\n\nyou can fix this by running:\n    pip install strict_functions')


def log_quesizes(log_path):
    ''' this writes the size of each of the queues to a log so you can profile queue pipelines '''
    with open(log_path, 'a') as f:
        prev_s = ''
        try:
            while 1:
                sleep(0.2)
                mah_queues = log_quesizes.queues
                if len(mah_queues):
                    s=(' '+' '.join('{}:{}'.format(q.name,int(q.qsize())) for q in mah_queues)+'\n')
                    if s != prev_s:
                        prev_s = s
                        f.write(str(time())+s)
        except NotImplementedError:
            from logging import warning
            warning('multiprocessing.Queue.qsize() is not supported by this system')

log_quesizes.queues = []
@strict_globals(log_quesizes=log_quesizes, Thread=Thread)
def enable_queue_size_logging(log_path='queue_sizes.log'):
    assert isinstance(log_path, str) and len(log_path), 'enable_queue_size_logging needs a non-empty string as its argument, not {}'.format(log_path)
    Thread(target=log_quesizes, args=(log_path,)).start()


@strict_globals(
    noglobals=noglobals,
    Queue=Queue,
    Thread=Thread,
    strict_globals=strict_globals,
    wraps=wraps,
    log_quesizes=log_quesizes
)
def queued(fn):
    '''
This decorator makes a function queued by putting it behind a queue
and letting the function run in a separate thread. Use this for functions
that you don't care about the output of like logging or things that waste
a lot of the main threads time like sending data to another server

Example usage below:
```
@queued
def f2(a):
    print('f2-called with',a)

@queued
def f1(a,b):
    print('f1 called with',a,b)
    print('f1 sending',a,'to f2')
    f2(a=a)


for i in range(5):
    f1(a=i,b=i+2)

print('done sending things to f1')
```
    '''
    fn_q = Queue()
    fn_q.name = '{:}.{:}'.format(fn.__module__, fn.__name__)
    fn_q.name = '{:}'.format(fn.__name__)
    log_quesizes.queues.append(fn_q)

    @noglobals
    def feeder(fn, q):
        q_g = q.get
        while 1:
            a,k = q_g()
            fn(*a,**k)
    #start_new_thread(feeder, (fn, fn_q))
    Thread(target=feeder, args=(fn, fn_q), daemon=False).start()
    @wraps(fn)
    @strict_globals(fn_q=fn_q)
    def wrapper(*a,**k):
        fn_q.put((a,k))
    return wrapper


@strict_globals(
    noglobals=noglobals,
    Queue=Queue,
    Thread=Thread,
    wraps=wraps,
    strict_globals=strict_globals,
    log_quesizes=log_quesizes
)
def queued_generator(fn):
    '''
This decorator puts a generator function behind a queue and returns the
attached queue's get function. this way, you send data to the generator
like you would any other regular function but underneath the arguments
are queued and ran by the generator once it can.

This is useful for times when you have really complex programs and you
want to split everything off into little async containers.

Example usage below:
```
@queued_generator
def step2():
    # set up the inner environment here
    from itertools import count
    c = count()
    # inputs sent to this function are processed in the loop below
    while 1:
        i = yield
        print('step2-recieved', i, 'totaling', next(c), 'elements')


@queued_generator
def step1():
    # inputs sent to this function are processed in the loop below
    while 1:
        i = yield
        print('step1 recieved', i)
        print('step1 sending', i, 'to step2')
        step2(i)

for i in range(10):
    step1(i)

print('done sending data to step1')
```
    '''
    fn_q = Queue()
    fn_q.name = '{:}.{:}'.format(fn.__module__, fn.__name__)
    fn_q.name = '{:}'.format(fn.__name__)
    log_quesizes.queues.append(fn_q)

    gen = fn()
    next(gen) # start the generator
    @noglobals
    def feeder(gen, q):
        g_s = gen.send
        q_g = q.get
        while 1:
            i = q_g()
            if len(i) == 1:
                g_s(i[0])
            else:
                g_s(i)
    #start_new_thread(feeder,(gen, fn_q))
    Thread(target=feeder, args=(gen, fn_q), daemon=False).start()
    @wraps(fn)
    @strict_globals(fn_q=fn_q)
    def wrapper(*a):
        fn_q.put(a)
    return wrapper

del Queue
del wraps
del Thread
del sleep
del time
del log_quesizes

if __name__ == '__main__':
    #=============================================================
    # queued tutorial below
    #=============================================================

    @queued
    def f2(a):
        print('f2-called with',a)

    @queued
    def f1(a,b):
        print('f1 called with',a,b)
        print('f1 sending',a,'to f2')
        f2(a=a)


    for i in range(5):
        f1(a=i,b=i+2)

    print('done sending things to f1')

    #=============================================================
    # queued_generator tutorial below
    #=============================================================

    @queued_generator
    def step2():
        # set up the inner environment here
        from itertools import count
        c = count()
        # inputs sent to this function are processed in the loop below
        while 1:
            i = yield
            print('step2-recieved', i, 'totaling', next(c), 'elements')


    @queued_generator
    def step1():
        # inputs sent to this function are processed in the loop below
        while 1:
            i = yield
            print('step1 recieved', i)
            print('step1 sending', i, 'to step2')
            step2(i)

    for i in range(10):
        step1(i)

    print('done sending data to step1')






