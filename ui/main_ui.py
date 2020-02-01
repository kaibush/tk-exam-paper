import logging
import os
import threading
from multiprocessing import freeze_support, Pool
from tkinter import messagebox
# from tkinter import *
import requests

from ui.mttkinter import *
from tkinter.ttk import *

from PIL import Image, ImageTk
from ttkwidgets import *

from crawl.exam_zujuan import ScanLogin, CookiesLogin, ZuJuanView, ZuJuanTasks
from crawl.project_info import Project
from crawl.utils import WorkProcess


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

            Button(bt_frame, text="一键登录", command=self.login_by_cookies).grid(
                row=0, column=0, ipadx=12.5
            )
            Button(bt_frame, text="扫码登录", command=self.login_by_scan).grid(
                row=0, column=1, ipadx=12.5
            )
            Button(bt_frame, text="生成", command=self.run_tasks).grid(
                row=1, column=0, ipadx=12.5
            )
            Button(bt_frame, text="终止任务", command=self.stop_tasks).grid(
                row=1, column=1, ipadx=12.5
            )

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

        def make_tasks():
            Label(user_frame, text="添加任务").pack(side="top", anchor="nw")
            box = ScrolledListbox(user_frame, width=80, height=6)
            UI["task"] = box.listbox
            box.pack(side="top", anchor="nw")

        make_user_info()
        make_paper_records()
        make_tasks()

    def show_msg(self):
        top = Toplevel(self.root)
        Label(top, text="等待task完成").pack()

    def login_by_cookies(self):
        pass

    def login_by_scan(self):
        pass

    def run_tasks(self):
        pass

    def stop_tasks(self):
        pass


class LoginUI(MainUI):
    def __init__(self, root):
        self.pool = None
        self.login_scan_ids = []
        self.check_scan_ids = []
        super(LoginUI, self).__init__(root)
        self.build_pop_menu()
        self.init_login()
        UI.box.bind('<Button-3>', self.pop_menu_event)

    def build_pop_menu(self):
        self.menubar = Menu(self.root, tearoff=False)  # 制作一个菜单实例
        for menu in [
            ("添加任务", self.make_task),
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
            if not p.is_alive() and self.wx_scan.get_scan_flag():
                status = 1
                logging.info("扫码完成，正在跳转...")
                threading.Thread(
                    target=self.update_by_thread, args=(ticket,)
                ).start()

        if not status:
            check_scan_id = self.root.after(1000, lambda: self.check_scan(ticket))
            self.check_scan_ids.append(check_scan_id)

    def login_by_scan(self):
        if not UI.debug:
            self.build_debug_ui()
        self.clear_view()
        qrcode = self.wx_scan.get_qrcode_url()
        self.wx_scan.save_qrcode_pic(qrcode)
        self.update_qrcode(Project.qrcode)
        ticket = self.wx_scan.get_ticket(qrcode)
        worker.put(self.wx_scan.check_scan, ticket)
        worker.run()
        self.cancel_before_scan()
        login_scan_id = self.root.after(
            1000, lambda: self.check_scan(ticket)
        )
        self.login_scan_ids.append(login_scan_id)

    def login_by_cookies(self):
        if not UI.debug:
            self.build_debug_ui()
        self.clear_view()
        self.cancel_before_scan()
        self.cookies_login.login_by_cookies()
        self.update_user()
        self.update_exam_view()

    def cancel_before_scan(self):
        logging.info("清除登录历史")
        for _id in self.login_scan_ids:
            self.root.after_cancel(_id)
        for _id in self.check_scan_ids:
            self.root.after_cancel(_id)
        self.login_scan_ids.clear()
        self.check_scan_ids.clear()
        worker.stop_old_work()

    def update_user(self):
        username = self.zujuan.get_username()
        UI.user.config(text=username)

    def clear_view(self):
        logging.info("清除视图")
        UI.box.delete(0, END)
        UI.task.delete(0, END)

    def update_exam_view(self):
        if UI.records:
            del UI["records"]
        records = self.zujuan.get_zujuan_view()
        UI["records"] = records
        for record_pid in records:
            UI.box.insert(END, records[record_pid].text + "-%s" % record_pid)
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

    def is_add_task(self, add):
        tasks = UI.task.get(0, END)
        for task in tasks:
            if task == add:
                return True
        return False

    def make_task(self):
        sel = UI.box.curselection()
        if sel:
            sel_text = UI.box.get(sel)
            if self.is_add_task(sel_text):
                return messagebox.showinfo("提示", "任务已存在")
            UI.task.insert(END, sel_text)

    def all_tasks_pending(self):
        tasks = UI.task.get(0, END)
        href_pool = []
        if UI.records:
            for task in tasks:
                text, pid = self.parse_record(task)
                href_pool.append(
                    [task, UI.records[pid].href]
                )
        return href_pool

    def run_tasks(self):
        threading.Thread(target=self._run_tasks).start()

    def _run_tasks(self):
        logging.info("执行组卷任务")
        yes = messagebox.askyesno("提示", "组卷tasks启动?")
        if yes:
            self.show_msg()
            self.pool = Pool()
            ZuJuanTasks().task_run(
                self.pool, self.all_tasks_pending()
            )
            messagebox.showinfo("提示", "组卷tasks已结束")

    def stop_tasks(self):
        ZuJuanTasks().task_shutdown(self.pool)


def network_heart(root):
    root.withdraw()
    try:
        requests.get("http://www.baidu.com")
    except:
        messagebox.showerror("网络错误", "无法访问互联网，退出程序", parent=root)
        os._exit(-1)
    else:
        root.deiconify()


if __name__ == "__main__":
    freeze_support()
    tk = Tk()
    tk.title("zujuan")
    log = logging.getLogger()

    threading.Thread(target=network_heart, args=(tk,)).start()
    gui_thead = threading.Timer(0.5, LoginUI, args=(tk,))
    gui_thead.start()

    tk.mainloop()
