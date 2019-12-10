import json
import logging
import random
import time
from urllib import parse

import bs4
import requests

from crawl.exam_base import ExamPaperBase, URLs, LogoutError
from crawl.utils import save_cookies, load_cookies, logger
from crawl.project_info import Project


class ScanLogin(ExamPaperBase):
    def __init__(self):
        self.sess.get(URLs.login)

    @logger
    def get_qrcode_url(self):
        resp = self.sess.get(URLs.qrcode)
        soup = bs4.BeautifulSoup(resp.text, "html.parser")
        wrp_code = soup.find("div", attrs={"class": "wrp_code"})
        qrcode_url = wrp_code.contents[0].attrs["src"]
        return qrcode_url

    @staticmethod
    @logger
    def get_ticket(qrcode_url):
        query = dict(
            parse.parse_qsl(
                parse.urlsplit(qrcode_url).query
            )
        )
        return query["ticket"]

    @logger
    def save_qrcode_pic(self, qrcode_url):
        resp = self.sess.get(qrcode_url)
        with open(Project.qrcode, "wb") as fp:
            fp.write(resp.content)

    @logger
    def check_scan(self, ticket):
        logging.info("等待扫码")
        query = {
            "ticket": ticket,
            "jump_url": "https://www.zujuan.com",
            "r": random.random()
        }
        check_login_url = URLs.issubscribe + "?" + parse.urlencode(query)
        check_cnt = 0
        scan_status = False
        while check_cnt < Project.check_timeout:
            is_login_resp = self.sess.get(check_login_url)
            resp = json.loads(is_login_resp.text)
            # code = 0 等待扫码
            if resp["code"] == 1:
                scan_status = True
                break
            time.sleep(1)
            check_cnt += 1
        return scan_status

    @logger
    def login_by_scan(self, ticket):
        scan_status = self.check_scan(ticket)
        if scan_status:
            wx_query = {
                'ticket': ticket,
                'jump_url': 'https://www.zujuan.com'
            }
            resp = self.sess.get(
                URLs.wxlogin + '?' + parse.urlencode(wx_query)
            )
            if resp.status_code == 200:
                save_cookies(self.sess.cookies)
            else:
                raise requests.HTTPError("wechat login failed")


class CookiesLogin(ExamPaperBase):
    @logger
    def login_by_cookies(self):
        cookies = load_cookies()
        self.sess.cookies = cookies
        if not self.check_login_succ():
            raise LogoutError("pls scan qrcode to login again")


if __name__ == "__main__":
    wx_scan = ScanLogin()
    qrcode = wx_scan.get_qrcode_url()
    wx_scan.save_qrcode_pic(qrcode)
    ticket = wx_scan.get_ticket(qrcode)
    print(ticket)
    wx_scan.login_by_scan(ticket)
    wx_scan.check_login_succ()

    cookies_login = CookiesLogin()
    cookies_login.login_by_cookies()
