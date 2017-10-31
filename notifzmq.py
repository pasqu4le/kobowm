import Tkinter as tk
from threading import Thread
from sys import argv
from utils import log, press, F9
import zmq


class NotificationsWindow(tk.Frame):
    def __init__(self, master=None):
        # init, configure and draw window
        tk.Frame.__init__(self, master)
        self.master.title('kobowm-notifications')
        self.configure(background='black', bd=5, relief='raised')
        self.columnconfigure(0, minsize=190)
        self.rowconfigure(0, minsize=30)
        self.rowconfigure(1, minsize=55)
        self.grid()
        # labels string var
        self.title_var = tk.StringVar()
        self.title_var.set('Title')
        self.body_var = tk.StringVar()
        self.body_var.set('Body')
        # widgets creation
        label = tk.Label(self, textvariable=self.title_var, bg='black', fg='white', font=(None, 18))
        label.grid(column=0, row=0, sticky=tk.W)
        label = tk.Label(self, textvariable=self.body_var, bg='black', fg='white', font=(None, 10))
        label.grid(column=0, row=1, sticky=tk.W)
        # id of the after-created task, to allow elimination
        self.after_id = None

    def show_notification(self, title, body, timeout):
        # change the labels value in any case
        self.title_var.set(title)
        self.body_var.set(body)
        if self.after_id:
            # there was a notification already up, stop the closing task and start a new one
            self.master.after_cancel(self.after_id)
        else:
            # un-hide the window
            press(F9)
        # let the notification up for at least 1 second, but 5 at most; then hide it again
        self.after_id = self.master.after(max(min(timeout, 5000), 1000), self.auto_close)

    def auto_close(self):
        # hide the notification window after the timeout
        self.after_id = None
        press(F9)


class Receiver(object):
    def __init__(self, window):
        self.window = window
        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.bind("tcp://127.0.0.1:5555")

    def loop(self):
        while True:
            message = self.socket.recv_string()
            title, body, timeout = message.split('\n')
            # notify the sender of the reception
            self.socket.send('confirmed')
            log("Received notification: {} {} {}".format(title, body, timeout))
            self.window.show_notification(title, body, int(timeout))


def main():
    win = NotificationsWindow()
    recv = Receiver(win)
    th = Thread(target=recv.loop)
    th.start()
    win.mainloop()


def send(title, body, timeout):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect('tcp://127.0.0.1:5555')
    socket.send_string("\n".join((title, body, timeout)))
    socket.recv()  # wait for the receiver response


if __name__ == '__main__':
    if len(argv) == 1:
        main()
    elif len(argv) == 2:
        print('To send a notification you need at least a title and a body')
    else:
        send(argv[1], argv[2], '0' if len(argv) == 3 else argv[3])
