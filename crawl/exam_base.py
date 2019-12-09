import logging

import bs4
import requests

from crawl.project_info import Project


class URLs:
    login = Project.urls["login"]
    qrcode = Project.urls["qrcode"]
    wxlogin = Project.urls["wxlogin"]
    issubscribe = Project.urls["issubscribe"]
    user = Project.urls["user"]


class ExamPaperBase:
    sess = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/"
                      "537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    @staticmethod
    def get(*args, **kwargs):
        return ExamPaperBase.sess.get(*args, **kwargs)

    @logger
    def check_login_succ(self):
        resp = self.sess.get(URLs.user)
        soup = bs4.BeautifulSoup(resp.text, "html.parser")
        login_fail = soup.find("div", attrs={"class": "mistack-content"})
        if login_fail and login_fail.text.find("未登录") != -1:
            logging.info("未登录，请重新扫码登录")
            return False
        login_succ = soup.find("legend", attrs={"class": "form-title"})
        if login_succ and login_succ.text.find("第三方账号绑定") != -1:
            logging.info("一键登录成功")
            return True
        return False
