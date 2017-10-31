import Tkinter as tk
from Tkinter import PhotoImage
from time import sleep
from threading import Thread
from functools import partial
from utils import *


class Dock(tk.Frame):
    def __init__(self, master=None):
        # init, configure and draw window
        tk.Frame.__init__(self, master)
        self.master.title('kobowm-dock')
        self.configure(background='white')
        self.rowconfigure(0, minsize=60)
        for i in range(10):
            self.columnconfigure(i, minsize=60)
        self.grid()
        self.tasks_icon = PhotoImage(file=kobowm_path + '/icons/view-paged-symbolic.symbolic.png')
        self.keyboard_icon = PhotoImage(file=kobowm_path + '/icons/input-keyboard-symbolic.symbolic.png')
        self.xterm_icon = PhotoImage(file=kobowm_path + '/icons/utilities-terminal-symbolic.symbolic.png')
        self.close_icon = PhotoImage(file=kobowm_path + '/icons/window-close-symbolic.symbolic.png')
        self.wifi_icon = PhotoImage(file=kobowm_path + '/icons/network-wireless-symbolic.symbolic.png')
        self.usb_icon = PhotoImage(file=kobowm_path + '/icons/media-removable-symbolic.symbolic.png')
        self.sdcard_icon = PhotoImage(file=kobowm_path + '/icons/media-floppy-symbolic.symbolic.png')
        self.lock_icon = PhotoImage(file=kobowm_path + '/icons/system-lock-screen-symbolic.symbolic.png')
        self.battery_icon = PhotoImage(file=kobowm_path + '/icons/battery-empty-symbolic.symbolic.png')
        self.charging_icon = PhotoImage(file=kobowm_path + '/icons/battery-empty-charging-symbolic.symbolic.png')
        # widgets creation
        button = tk.Button(self, image=self.tasks_icon, command=partial(press, F1), bg='white')
        button.grid(column=0, row=0, sticky=tk.N + tk.E + tk.S + tk.W)
        button = tk.Button(self, image=self.keyboard_icon, command=partial(press, F2), bg='white')
        button.grid(column=1, row=0, sticky=tk.N + tk.E + tk.S + tk.W)
        button = tk.Button(self, image=self.xterm_icon, command=partial(press, F3), bg='white')
        button.grid(column=2, row=0, sticky=tk.N + tk.E + tk.S + tk.W)
        button = tk.Button(self, image=self.close_icon, command=partial(press, F4), bg='white')
        button.grid(column=3, row=0, sticky=tk.N + tk.E + tk.S + tk.W)
        button = tk.Button(self, image=self.wifi_icon, command=partial(system, wifi_toggle), bg='white')
        button.grid(column=4, row=0, sticky=tk.N + tk.E + tk.S + tk.W)
        button = tk.Button(self, image=self.usb_icon, command=partial(system, usb_toggle), bg='white')
        button.grid(column=5, row=0, sticky=tk.N + tk.E + tk.S + tk.W)
        button = tk.Button(self, image=self.sdcard_icon, command=partial(system, sdcard_toggle), bg='white')
        button.grid(column=6, row=0, sticky=tk.N + tk.E + tk.S + tk.W)
        button = tk.Button(self, image=self.lock_icon, command=partial(system, suspend_script), bg='white')
        button.grid(column=7, row=0, sticky=tk.N + tk.E + tk.S + tk.W)
        self.battery_label = tk.Label(self, bg='white', compound="right", font=(None, 16))
        self.battery_label.grid(column=8, row=0, columnspan=2, sticky=tk.E)
        self.update_battery(0, False)

    def update_battery(self, percentage, charging):
        if charging:
            image = self.charging_icon
        else:
            image = self.battery_icon
        self.battery_label.configure(text=str(percentage), image=image)


def updater(update_func):
    last_val, charging = 0, False
    while True:
        sleep(5)
        new_val, new_charge = battery_status()
        if last_val != new_val or charging != new_charge:
            last_val, charging = new_val, new_charge
            try:
                update_func(last_val, charging)
            except RuntimeError:
                # you will receive this if the dock is not in the mainloop anymore, just terminate
                exit(0)


def main():
    dock = Dock()
    th = Thread(target=updater, args=[dock.update_battery])
    th.start()
    dock.mainloop()


if __name__ == '__main__':
    main()
