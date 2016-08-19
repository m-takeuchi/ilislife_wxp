from sched import scheduler
from time import time, sleep

s = scheduler(time, sleep)

def run_periodically(start, end, interval, func):
    event_time = start
    while event_time < end:
        s.enterabs(event_time, 0, func, ())
        event_time += interval
    s.run()

def say_hello():
    print('hello')


if __name__ == '__main__':


    run_periodically(time()+5, time()+10, 1, say_hello)
