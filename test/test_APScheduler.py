from apscheduler.schedulers.blocking import BlockingScheduler
sched = BlockingScheduler()

def my_interval_job():
    print('Hello World!')
sched.add_job(my_interval_job, 'interval', seconds=5)
sched.start()
