import logging
import pickle
import sys
from functools import wraps

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


logging.basicConfig(level=logging.INFO)
# log = logging.getLogger(__name__)
# stdout_handler = logging.StreamHandler(sys.stdout)
# log.addHandler(stdout_handler)
