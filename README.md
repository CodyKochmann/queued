# queued
Simple function decorators that make Python functions and generators queued and async for nonblocking operations

### How to Install?

```pip install queued```

### How to use it?

```python
from queued import queued

@queued  # queued puts functions in the background
def result_logger(input_string):
    with open('my_result.log', 'a') as f:
        f.write(input_string + '\n')

result_logger('yay Im loggin!')
```
---

> before we add edits
> 
> ### What does it do?
> 
> Decorating a function with `@queued` two new things happen: 
> 
> 1. The decorated function in a separate thread becomes nonblocking
> 2. The function running in the background thread gains a queue.

---

### What does it do?

Decorating a function with `@queued` by default does two things:

1. the decorated function is placed in a separate thread to make it nonblocking
2. A queue is built that acts as a task buffer for the background task

### What is the benefit?

`queued` allows you to put functions that have blocking operations in the background so your main thread or process can focus on the main task. This is beneficial for functions that you don't need the return value from, like logging. Since queues preserve order though, you'll still get the sequential benefits of straight line programming without the unordered mess or memory consumption that comes from just spawning off a background thread to do some job in the background.

### Does this support background processes if you don't want the background job running on the same core?

Yes. The `multiprocessing` argument provides you with the option to send the background job to run in another process instead of a different thread.

```python
from queued import queued

# this will run result_logger in a separate process
@queued(multiprocessing=True)
def result_logger(input_string):
    with open('my_result.log', 'a') as f:
        f.write(input_string + '\n')

result_logger('yay Im loggin!')
```

### Can I have multiple worker threads/processes for a `queued` function?

Yes. Feeding `queued` the `workers` argument will tell `queued` to create however many threads or processes you want to have watching the queue that feeds your function. CAUTION - This does mean that you will need to consider syncing issues for certain operations.

```python
from queued import queued
from requests import get

# this will download up to 4 files at the same time
@queued(workers=4)
def download(file_path, url):
    with open(file_path, 'w') as f:
        for chunk in get(url).iter_content():
            f.write(chunk)

download('/tmp/google.html', 'https://google.com')
```

### Can I limit the size of the queues of each function?

Yes, the `max_size` argument allows you to limit the number of items that are in a function's queue. If you top off the queue, the main thread will wait for the background thread/process to make room in the queue. This is handy if you have memory consumption concerns

```python
from queued import queued

# all calls to result_logger will be non-blocking unless
# the background job has 10 objects in its queue 
@queued(max_size=10)
def result_logger(input_string):
    with open('my_result.log', 'a') as f:
        f.write(input_string + '\n')

result_logger('yay Im loggin!')
```

### What happens when a queued function crashes?

`queued` will log the error. If you want to specify the logger function that you want to send the log messages to, use the `logger` argument. By default `logger=logging.warning`.

```python
from queued import queued
from requests import get


@queued  # log in the background
def result_logger(input_string):
    with open('my_result.log', 'a') as f:
        f.write(input_string + '\n')

# this will download links in the background 
# and send error messages to result_logger
@queued(logger=result_logger)
def download(file_path, url):
    with open(file_path, 'w') as f:
        for chunk in get(url).iter_content():
            f.write(chunk)

download('/tmp/google.html', 'https://google.com')
```

### Can I control the consumption rate of the queues to make the function work in batches?

Yes, but I'm bored writing documentation.








