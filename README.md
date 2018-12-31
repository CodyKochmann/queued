# queued

[![Downloads](https://pepy.tech/badge/queued)](https://pepy.tech/project/queued)
[![Downloads](https://pepy.tech/badge/queued/month)](https://pepy.tech/project/queued)
[![Downloads](https://pepy.tech/badge/queued/week)](https://pepy.tech/project/queued)

Simple function decorators that make Python functions and generators queued and async for nonblocking operations

### How to Install?

```bash
pip install queued
```

### How to use it?

```python
from queued import queued

@queued
def mah_high_performance_log(queued_items):
    ''' this logs input to a file in the background '''
    with open('my_result.log', 'a') as f:
        for item in queued_items:
            f.write('{}\n'.format(item))

mah_high_performance_log('yay Im loggin!')
```

<!--

> before we add edits
>
> ### What does it do?
>
> Decorating a function with `@queued` two new things happen:
>
> 1. The decorated function in a separate thread becomes nonblocking
> 2. The function running in the background thread gains a queue.

-->

### What does it do?

Decorating a function with `@queued` by default does two things:

1. The decorated function is placed in a separate thread and becomes nonblocking.
2. The now backgrounded function is now fed inputs through a queue.

### What is the benefit?

`queued` allows you to put functions that have blocking operations in the background so your main thread or process can focus on the main task. This is beneficial for functions that you don't need the return value from, like logging. Since queues preserve order though, you'll still get the sequential benefits of straight line programming without the unordered mess or memory consumption that comes from just spawning off a background thread to do some job in the background.

### Can I have multiple worker threads/processes for a `queued` function?

Yes. Feeding `queued` the `workers` argument will tell `queued` to create however many threads or processes you want to have watching the queue that feeds your function. CAUTION - This does mean that you will need to consider syncing issues for certain operations.

```python
from queued import queued
from requests import get

# this will download up to 4 files at the same time
@queued(workers=4)
def download(queued_items):
    for file_path, url in queued_items:
        with open(file_path, 'w') as f:
            for chunk in get(url).iter_content():
                f.write(chunk)

download(('/tmp/google.html', 'https://google.com'))
```

### Can I limit the size of the queues of each function?

Yes, the `maxsize` argument allows you to limit the number of items that are in a function's queue. If you top off the queue, the main thread will wait for the background thread/process to make room in the queue. This is handy if you have memory consumption concerns

```python
from queued import queued

# all calls to result_logger will be non-blocking unless
# the background job has 10 objects in its queue
@queued(maxsize=10)
def result_logger(queued_items):
    with open('my_result.log', 'a') as f:
        for input_string in queued_items:
            f.write(input_string + '\n')

result_logger('yay Im loggin!')
```

### What happens when a queued function crashes?

`queued` will log the error. If you want to specify the logger function that you want to send the log messages to, use the `logger` argument. By default `logger=logging.warning`.

```python
from queued import queued
from requests import get

# this logs to a file in the background
@queued
def custom_error_logger(queued_items):
    with open('my_result.log', 'a') as f:
        for input_string in queued_items:
            f.write(input_string + '\n')

# this will download links in the background
# and send error messages to result_logger
@queued(logger=custom_error_logger)
def download(queued_items):
    for file_path, url in queued_items:
        with open(file_path, 'w') as f:
            for chunk in get(url).iter_content():
                f.write(chunk)

download(('/tmp/google.html', 'https://google.com'))
```

<!--
### Can I control the consumption rate of the queues to make the function work in batches?

Yes, but I'm bored writing documentation.
-->
