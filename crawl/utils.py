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
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error("running (%s) error", func.__name__)
            raise

    return wrapper


class WorkProcess:
    workers = []

    def put(self, callback, *args, **kwargs):
        self.workers.append(partial(callback, *args, **kwargs))

    def clear(self):
        self.workers.clear()

    def stop_old_work(self):
        for p in self.workers:
            if p.is_alive():
                logging.info("stop old worker: %s", p.pid)
                p.terminate()
        self.clear()

    def run(self):
        if self.workers:
            func = self.workers.pop()
            self.stop_old_work()

            p = mp.Process(target=func)
            p.start()
            logging.info("child pid: %s", p.pid)
            self.workers.append(p)
            logging.info("p.is_alive: %s", p.is_alive())
            # p.join()


logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    mp.freeze_support()
    result = mp.Manager().dict()
    w = WorkProcess()
