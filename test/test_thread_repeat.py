import datetime, threading, time


class Repeat():
    def __init__(self, callback):
        self.callback = callback
    def run(self,dt):
        next_call = time.time()
        while True:
            #### Target function
            self.callback('run')
            ####
            next_call = next_call+dt;
            time.sleep(next_call - time.time())


def foo():
    next_call = time.time()
    while True:
        #### Target function
        print(datetime.datetime.now())
        ####
        next_call = next_call+1;
        time.sleep(next_call - time.time())
def hoge(v):
    print(time.time())

# timerThread = threading.Thread(target=foo)
myfoo = Repeat(hoge)
myfoo.run(1)
