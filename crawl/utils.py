import logging
import pickle
from functools import wraps

import requests

from crawl.project_info import Project


def save_cookies(cookies):
    with open(Project.cookies, 'wb') as f:
        pickle.dump(cookies.get_dict(), f)


def load_cookies():
    with open(Project.cookies, 'rb') as f:
        cookies = requests.utils.cookiejar_from_dict(
            pickle.load(f)
            # {}
        )
    return cookies


def logger(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info("-->running (%s)", func.__name__)
        return func(*args, **kwargs)

    return wrapper


logging.basicConfig(level=logging.INFO)
