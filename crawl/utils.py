import logging
import multiprocessing as mp
import pickle
from functools import partial
from functools import wraps
from queue import Queue

import requests
from requests.cookies import RequestsCookieJar

from crawl.project_info import Project


def save_cookies(cookies):
    with open(Project.cookies, 'wb') as f:
        pickle.dump(cookies.get_dict(), f)


def load_cookies():
    try:
        with open(Project.cookies, 'rb') as f:
            cookies = requests.utils.cookiejar_from_dict(
                pickle.load(f)
            )
    except:
        cookies = RequestsCookieJar()
    return cookies


def logger(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info("-->running (%s)", func.__name__)
        return func(*args, **kwargs)

    return wrapper


class WorkProcess:
    workers = []
    result = mp.Manager().dict()

    def put(self, callback, args):
        self.workers.append(partial(callback, args))
        print(len(self.workers))

    def clear(self):
        self.workers.clear()

    def stop_old_work(self):
        for p in self.workers:
            if p.is_alive():
                logging.info("stop old worker: %s", p.pid)
                p.terminate()
        self.clear()

    @logger
    def run(self, rest):
        func = self.workers.pop()
        self.stop_old_work()

        def runner():
            r = func()
            rest[p.pid] = r

        p = mp.Process(target=runner)
        p.start()
        logging.info("child pid: %s", p.pid)
        self.workers.append(p)
        logging.info("p.is_alive: %s", p.is_alive())
        # p.join()


logging.basicConfig(level=logging.INFO)
# log = logging.getLogger(__name__)
# stdout_handler = logging.StreamHandler(sys.stdout)
# log.addHandler(stdout_handler)
mp.freeze_support()

if __name__ == "__main__":
    w = WorkProcess()
    import time
    from crawl.login_method import ScanLogin

    wx = ScanLogin()

    w.put(wx.check_scan, "test2")
    w.run(w.result)

    w.put(time.sleep, 2)
    w.run(w.result)

    print(w.result)
