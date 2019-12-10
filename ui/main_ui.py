import logging
import multiprocessing as mp
from functools import partial
from multiprocessing import freeze_support
import os
import threading
import tkinter as tk_
from ttkwidgets import *

from crawl.login_method import ScanLogin, CookiesLogin, ZuJuanView
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
worker = WorkProcess()


class MyDebugWindow(DebugWindow):

    # def write(self, line):
    #     self.text.insert(END, line)
    #     self.text.see(END)

    def quit(self):
        super(MyDebugWindow, self).quit()
        log.removeHandler(UI.handler)
        del UI["debug"], UI["handler"]


class MainUI:
    def __init__(self, root):
        self.root = root
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
        pil_image = Image.open(path).resize((220, 220))
        tk_image = ImageTk.PhotoImage(image=pil_image)
        self.root.img = tk_image
        return tk_image

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
            UI["user"] = Label(user_frame, text="昵称： 未登录")
            UI.user.pack(side="top", anchor="nw")

        def make_paper_records():
            Label(user_frame, text="组卷记录").pack(side="top", anchor="nw")
            box = ScrolledListbox(user_frame, width=80, height=12)
            UI["box"] = box.listbox

            box.pack(side="top", anchor="nw")

        make_user_info()
        make_paper_records()

    def login_by_cookies(self):
        pass

    def login_by_scan(self):
        pass


class LoginUI(MainUI):
    def __init__(self, root):
        super(LoginUI, self).__init__(root)
        self.build_pop_menu()
        self.init_login()
        UI.box.bind('<Button-3>', self.pop_menu_event)

    def build_pop_menu(self):
        self.menubar = Menu(self.root, tearoff=False)  # 制作一个菜单实例
        for menu in [
            ("生成", self.gen_exam),
        ]:
            self.menubar.add_command(label=menu[0], command=menu[1])

    def pop_menu_event(self, event):
        self.menubar.post(event.x_root, event.y_root)

    def init_login(self):
        self.wx_scan = ScanLogin()
        self.cookies_login = CookiesLogin()
        self.zujuan = ZuJuanView()
        self.get = self.wx_scan.get

    def check_scan(self, ticket):
        status = 0
        logging.info("等待扫码...")
        if worker.workers:
            p = worker.workers[-1]
            if not p.is_alive():
                status = 1
                logging.info("扫码完成，正在跳转...")
                # TODO
                threading.Thread(
                    target=self.update_by_thread, args=(ticket,)
                ).start()

        if not status:
            self.root.after(1000, lambda: self.check_scan(ticket))

    def login_by_scan(self):
        if not UI.debug:
            self.build_debug_ui()

        qrcode = self.wx_scan.get_qrcode_url()
        self.wx_scan.save_qrcode_pic(qrcode)
        self.update_qrcode(Project.qrcode)
        ticket = self.wx_scan.get_ticket(qrcode)
        worker.put(self.wx_scan.check_scan, ticket)
        worker.run()
        self.root.after(1000, lambda: self.check_scan(ticket))

    def login_by_cookies(self):
        if not UI.debug:
            self.build_debug_ui()

        self.cookies_login.login_by_cookies()
        self.update_user()
        self.update_exam_view()

    def update_user(self):
        username = self.zujuan.get_username()
        UI.user.config(text=username)

    def update_exam_view(self):
        UI.box.delete(0, END)
        records = self.zujuan.get_zujuan_view()
        for record_pid in records:
            UI.box.insert(END, records[record_pid].text + "-(%s)" % record_pid)
        # self.wx_scan.login_by_scan(ticket)
        # self.wx_scan.check_login_succ()

    def update_by_thread(self, ticket):
        self.wx_scan.login_by_scan(ticket)
        logging.info("更新界面记录")
        self.update_user()
        self.update_exam_view()

    def parse_record(self, record):
        text, pid = record.split('-')
        return text, pid

    def gen_exam(self):
        sel = UI.box.curselection()
        print(UI.box.get(sel))

if __name__ == "__main__":
    freeze_support()
    tk = Tk()
    # app = MainUI(tk)
    log = logging.getLogger()
    gui_thead = threading.Thread(target=LoginUI, args=(tk,))
    gui_thead.start()
    print(UI)
    mainloop()
