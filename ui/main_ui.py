import logging
import multiprocessing as mp
import os
import threading
import tkinter as tk_
from ttkwidgets import *

from crawl.login_method import ScanLogin, CookiesLogin
from crawl.project_info import Project
from crawl.utils import WorkProcess
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
WORKER = WorkProcess()


class MyDebugWindow(DebugWindow):

    def write(self, line):
        self.text.insert(END, line)
        self.text.see(END)

    def quit(self):
        super(MyDebugWindow, self).quit()
        log.removeHandler(UI.handler)
        del UI["debug"], UI["handler"]


class MainUI:
    def __init__(self, root):
        self.root = root
        self.init_login()
        self.build_debug_ui()
        self.build_ui()

    def build_debug_ui(self):
        UI["debug"] = MyDebugWindow(self.root)
        UI.debug.geometry("400x400+0+0")
        stdout_handler = logging.StreamHandler(UI.debug)
        log.addHandler(stdout_handler)
        UI["handler"] = stdout_handler

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
        image_id = UI.qrcode_display.create_image(3, 3, anchor='nw',
                                                  image=tk_image)

    def build_left_ui(self):
        login_frame = Labelframe(self.root, text="扫描二维码登录", labelanchor="n")
        login_frame.pack(side="left", anchor="nw")

        def make_canvas():
            canvas_frame = Frame(login_frame)
            canvas_frame.pack(side="top", anchor="nw")
            qrcode_display = Canvas(canvas_frame, bg="grey", width=222,
                                    height=222)
            qrcode_display.pack(side="top", anchor="nw")
            UI["qrcode_display"] = qrcode_display
            self.update_qrcode(Project.qrcode)

        def make_buttons():
            bt_frame = Frame(login_frame)
            bt_frame.pack(side="top", anchor="nw", fill="both")

            Button(bt_frame, text="一键登录", command=self.login_by_cookies).pack(
                side="left")
            Button(bt_frame, text="扫码登录", command=self.login_by_scan).pack(
                side="right", anchor="e")

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

    def init_login(self):
        self.wx_scan = ScanLogin()
        self.cookies_login = CookiesLogin()

    def login_by_scan(self):
        if not UI.debug:
            self.build_debug_ui()

        qrcode = self.wx_scan.get_qrcode_url()
        self.wx_scan.save_qrcode_pic(qrcode)
        self.update_qrcode(Project.qrcode)
        ticket = self.wx_scan.get_ticket(qrcode)
        print(ticket)
        p = mp.Process(target=self.wx_scan.check_scan, args=(ticket, ))
        p.start()
        p.join()
        # WORKER.put(self.wx_scan.check_scan, ticket)
        # WORKER.run(WORKER.result)
        # print(WORKER.result)
        # self.wx_scan.login_by_scan(ticket)
        # self.wx_scan.check_login_succ()

    def login_by_cookies(self):
        if not UI.debug:
            self.build_debug_ui()

    def check_scan(self):
        self.root.after(100, self.wx_scan.check_scan)


if __name__ == "__main__":
    mp.freeze_support()
    tk = Tk()
    # app = MainUI(tk)
    log = logging.getLogger()
    gui_thead = threading.Thread(target=MainUI, args=(tk,))
    gui_thead.start()
    print(UI)
    mainloop()
