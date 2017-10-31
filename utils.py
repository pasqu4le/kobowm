import os
import sys
from os.path import dirname, realpath, exists
from random import randint
from datetime import datetime
from shutil import copyfile
from subprocess import check_output, CalledProcessError
from Xlib.display import Display
from Xlib import X, XK
from Xlib.ext.xtest import fake_input

kobowm_path = str(dirname(realpath(__file__)))
wifi_toggle = ['/home/marek/scripts/wifi/toggle']
usb_toggle = ['/home/marek/scripts/usb/toggle']
sdcard_toggle = ['/home/marek/scripts/sdcard/toggle']
suspend_script = ['/home/marek/scripts/power/suspend']
xterm_launch = ['/usr/bin/xterm', '-e ']
battery_path = '/sys/class/power_supply/mc13892_bat/'

display = Display()
# see kobowm.py
F1 = display.keysym_to_keycodes(XK.XK_F1)[0][0]
F2 = display.keysym_to_keycodes(XK.XK_F2)[0][0]
F3 = display.keysym_to_keycodes(XK.XK_F3)[0][0]
F4 = display.keysym_to_keycodes(XK.XK_F4)[0][0]
F9 = display.keysym_to_keycodes(XK.XK_F9)[0][0]


def battery_status():
    # Returns percentage string and a charging boolean
    val, charging = 0, False
    if exists(battery_path):
        try:
            with open(battery_path + 'capacity', 'r') as f:
                val = int(f.readline().rstrip())
            with open(battery_path + 'status', 'r') as f:
                charging = f.readline().rstrip() == 'Charging'
        except:
            log('could not read some battery info')
    else:
        # dummy values just for testing
        val = randint(0, 100)
        charging = val <= 50
    return val, charging


def press(keysym):
    # simulates the press (key down then release) of a button; NOTE: found from pyautogui's source code
    fake_input(display, X.KeyPress, keysym)
    fake_input(display, X.KeyRelease, keysym)
    display.sync()


def find_full_path(command):
    # tries to find a command full path using which
    try:
        return check_output(['/usr/bin/which', command]).rstrip()
    except CalledProcessError:
        return None


def system(command):
    # Forks a command and disowns it.
    log('sys launching command: ' + str(command))
    if os.fork() != 0:
        return
    try:
        # Child.
        os.setsid()     # Become session leader.
        if os.fork() != 0:
            os._exit(0)
        os.chdir(os.path.expanduser('~'))
        os.umask(0)

        # Close all file descriptors.
        import resource
        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        if maxfd == resource.RLIM_INFINITY:
            maxfd = 1024
        for fd in range(maxfd):
            try:
                os.close(fd)
            except OSError:
                pass
        # Open /dev/null for stdin, stdout, stderr.
        os.open('/dev/null', os.O_RDWR)
        os.dup2(0, 1)
        os.dup2(0, 2)
        os.execve(command[0], command, os.environ)
    except Exception as e:
        log('Error in child process: ' + str(e))
        sys.exit(1)


def log(data):
    with open(kobowm_path + '/data/log.out', 'a') as f:
        f.write("\n[{}]\t{}\n".format(datetime.now().strftime("%H:%M:%S"), data))


def clear_log():
    with open(kobowm_path + '/data/log.out', 'w') as f:
        f.write("[kobowm session started on {}]\n\n".format(datetime.now().strftime("%d/%m/%Y %H:%M")))


def close_log():
    with open(kobowm_path + '/data/log.out', 'a') as f:
        f.write("\n\n[kobowm session ended on {}]\n".format(datetime.now().strftime("%d/%m/%Y %H:%M")))
    copyfile(kobowm_path + '/data/log.out', kobowm_path + '/data/log.prev')
