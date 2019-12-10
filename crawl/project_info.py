import json
import os


class Project:
    root = os.path.dirname(os.path.dirname(__file__))
    project_config = os.path.join(root, "config", "project.json")
    cookies = os.path.join(root, "config", "cookies.ck")
    try:
        with open(project_config) as fp:
            project_info = json.load(fp)
            urls = project_info["urls"]
            check_timeout = project_info["timeout"]
    except FileNotFoundError:
        urls = {
            "login": "https://passport.zujuan.com/login",
            "qrcode": "https://passport.zujuan.com/connect/weixin-qrcode?iframe=1&width=220&height=220",
            "wxlogin": "https://passport.zujuan.com/connect/wxlogin",
            "issubscribe": "https://passport.zujuan.com/connect/issubscribe",
            "user": "https://www.zujuan.com/u/index",
        }
        check_timeout = 300
    qrcode = os.path.join(root, "qrcode", "wx_qrcode.png")
    default_png = os.path.join(root, "qrcode", "default.png")

