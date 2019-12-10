import logging
import os
import threading
import tkinter as tk_
from ttkwidgets import *

from crawl.login_method import ScanLogin, CookiesLogin
from crawl.project_info import Project
from ui.mttkinter import *
# from tkinter import *
from tkinter.ttk import *
from PIL import Image, ImageTk


class UIWidget(dict):
    def __getattribute__(self, item):
        if item in self:
            return self[item]
        return None


UI = UIWidget()


class MyDebugWindow(DebugWindow):

    def write(self, line):
        self.text.insert(END, line)
        self.text.see(END)


class MainUI:
    def __init__(self, root):
        self.root = root
        self.build_ui()
        UI["debug"] = MyDebugWindow(self.root)
        UI.debug.geometry("400x400+0+0")

    def build_ui(self):
        self.build_left_ui()
        self.build_right_ui()

    def resize_img(self, path):
        if hasattr(self.root, "img"):
            del self.root.img
        pilImage = Image.open(path).resize((220, 220))
        tkImage = ImageTk.PhotoImage(image=pilImage)
        self.root.img = tkImage
        return tkImage

    def update_qrcode(self, path):
        UI.qrcode_display.delete(ALL)
        tk_image = self.resize_img(path)
        image_id = UI.qrcode_display.create_image(3, 3, anchor='nw', image=tk_image)

    def build_left_ui(self):
        login_frame = Labelframe(self.root, text="扫描二维码登录", labelanchor="n")
        login_frame.pack(side="left", anchor="nw")

        def make_canvas():
            canvas_frame = Frame(login_frame)
            canvas_frame.pack(side="top", anchor="nw")
            qrcode_display = Canvas(canvas_frame, bg="grey", width=222, height=222)
            qrcode_display.pack(side="top", anchor="nw")
            UI["qrcode_display"] = qrcode_display
            self.update_qrcode(Project.qrcode)

        def make_buttons():
            bt_frame = Frame(login_frame)
            bt_frame.pack(side="top", anchor="nw", fill="both")

            Button(bt_frame, text="一键登录", command=self.login_by_cookies).pack(side="left")
            Button(bt_frame, text="扫码登录", command=self.login_by_scan).pack(side="right", anchor="e")

        make_canvas()
        make_buttons()

    def build_right_ui(self):
        user_frame = LabelFrame(self.root, text="用户信息", labelanchor="n")
        user_frame.pack(side="left", anchor="nw")

        def make_user_info():
            UI["user"] = Label(user_frame, text="用户名： 未登录")
            UI.user.pack(side="top", anchor="nw")

        def make_paper_records():
            Label(user_frame, text="组卷记录").pack(side="top", anchor="nw")
            box = ScrolledListbox(user_frame, width=80, height=12)
            UI["box"] = box
            for i in range(100):
                box.listbox.insert(i, i)
            box.pack(side="top", anchor="nw")

        make_user_info()
        make_paper_records()

    def login_by_scan(self):
        wx_scan = ScanLogin()
        qrcode = wx_scan.get_qrcode_url()
        wx_scan.save_qrcode_pic(qrcode)
        self.update_qrcode(Project.qrcode)
        # ticket = wx_scan.get_ticket(qrcode)
        # print(ticket)
        # wx_scan.login_by_scan(ticket)
        # wx_scan.check_login_succ()

    def login_by_cookies(self):
        pass


if __name__ == "__main__":
    tk = Tk()
    log = logging.getLogger()
    app = MainUI(tk)
    stdout_handler = logging.StreamHandler(UI.debug)
    log.addHandler(stdout_handler)
    mainloop()
