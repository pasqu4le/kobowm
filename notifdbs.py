import Tkinter as tk
from threading import Thread
from gi.repository import GLib
from pydbus import SessionBus
from pydbus.generic import signal
from utils import log, press, F9


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


class Notifications(object):
    """
    <node>
        <interface name="org.freedesktop.Notifications">
            <signal name="NotificationClosed">
                <arg direction="out" type="u" name="id"/>
                <arg direction="out" type="u" name="reason"/>
            </signal>
            <signal name="ActionInvoked">
                <arg direction="out" type="u" name="id"/>
                <arg direction="out" type="s" name="action_key"/>
            </signal>
            <method name="Notify">
                <arg direction="out" type="u"/>
                <arg direction="in" type="s" name="app_name"/>
                <arg direction="in" type="u" name="replaces_id"/>
                <arg direction="in" type="s" name="app_icon"/>
                <arg direction="in" type="s" name="summary"/>
                <arg direction="in" type="s" name="body"/>
                <arg direction="in" type="as" name="actions"/>
                <arg direction="in" type="a{sv}" name="hints"/>
                <arg direction="in" type="i" name="timeout"/>
            </method>
            <method name="CloseNotification">
                <arg direction="in" type="u" name="id"/>
            </method>
            <method name="GetCapabilities">
                <arg direction="out" type="as" name="caps"/>
            </method>
            <method name="GetServerInformation">
                <arg direction="out" type="s" name="name"/>
                <arg direction="out" type="s" name="vendor"/>
                <arg direction="out" type="s" name="version"/>
                <arg direction="out" type="s" name="spec_version"/>
            </method>
        </interface>
    </node>
    """

    NotificationClosed = signal()
    ActionInvoked = signal()

    def __init__(self, window):
        self.window = window

    def Notify(self, app_name, replaces_id, app_icon, summary, body, actions, hints, timeout):
        log("Received notification: {} {} {} {} {} {} {} {}".format(app_name, replaces_id, app_icon, summary, body,
                                                                    actions, hints, timeout))
        self.window.show_notification(summary, body, timeout)
        return 4  # chosen by fair dice roll. guaranteed to be random.

    def CloseNotification(self, id):
        pass

    def GetCapabilities(self):
        return []

    def GetServerInformation(self):
        return ("pydbus.examples.notifications_server", "pydbus", "?", "1.1")


def main():
    win = NotificationsWindow()
    bus = SessionBus()
    bus.publish("org.freedesktop.Notifications", Notifications(win))
    loop = GLib.MainLoop()
    th = Thread(target=loop.run)
    th.start()
    win.mainloop()

if __name__ == '__main__':
    main()
