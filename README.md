kobowm
======

kobowm is an X window manager written in python using Xlib

Why?
----

I originally wrote this for a Debian installation on my Kobo Touch (N905C), because any existing window manager I tried lacked some basic functionality for a touch screen device, didn't play well with some of the hardware, was too memory hungry or had other similar issues.

This started after finding Nick Welch's [tinywm](https://github.com/mackstann/tinywm) and reading J. D. Bartlett's article about a [simplewm](https://sqizit.bartletts.id.au/2011/03/28/how-to-write-a-window-manager-in-python/).

I ended up creating this repo on github mostly to give an example to anyone else interested in writing their own wm in python (you are warned: there aren't a lot of resources or examples out there and the python-xlib documentation is pretty much terrible)


Using it
--------

If you are interested in the multiboot debian installation on the kobo touch you can read about [marek's work on mobileread](https://www.mobileread.com/forums/showthread.php?t=222123) and/or download my image containing kobowm and some changes from [dropbpx](https://www.dropbox.com/s/2hql5f651xhz8cx/kobowm.zip?dl=0).

If you want to run it on another system you'll likely have to read and edit the source (for example some absolute paths), meet the requirements and edit your ~/.xinitrc file to execute kobowm.sh

All hard-coded values should be inside the utils.py file and there is no configuration of any kind. I apologize for this, bus as said I made it for the purpose of being simple and run on my device.

What's inside and features
--------------------------

Kobowm launches 4 applications when starting, never closing them and treating their windows differently from the others:
- launcher.py: a simple applications launcher that reads every .desktop file in the /usr/share/applications/ directory and sorts out any app it's not sure it can run. Also has a simple json cache, if you want to refresh it press the button in the top-right corner
- dock.py: an always-visible dock to the bottom of the screen that emulates key presses that the wm will catch or launches simple scripts for wifi, sdcard, usb and suspension. It also contain a battery percentage and status indicator.
- notif*.py a notification server that receives notifications and asks the wm to show and hide them, see requirements for the 2 differents implementation
- [matchbox-keyboard](http://git.yoctoproject.org/cgit/cgit.cgi/matchbox-keyboard/about), which is assumed to be installed

Kobowm has only a small set of features, it will:
- resize every window to take all the screen (minus the space occupied by the dock)
- keep track of an active window (the only one visible at any given time, except the apps mentioned in the previous list)
- keep track and manage transient and non-transient windows, cycle through the latter with F1
- show/hide the virtual keyboard and redirect it's key event to the active window (toggle with F2)
- launch an xterm instance (launch with F3)
- kill the current active window and go back to the empty screen, or the window the one destroyed was transient for (with F4)
- show/hide the latest notification (with F9)
- exit (with the power-off button or F12)
- show/hide the launcher (with the launch1 button or the F11)
- keep the log of the current and the last session (in the data directory)


Requirements
------------

- [python-xlib](https://github.com/python-xlib/python-xlib) to communicate with the X server
- [Tkinter](https://wiki.python.org/moin/TkInter) used by the launcher, dock and notif* applications
- [pydbus](https://github.com/LEW21/pydbus) and it's requirements, if you use notifdbs for a notification server compatible with the org.freedesktop.Notifications specification (you can send notifications using the command notify-send for example)
- [pyzmq](https://github.com/zeromq/pyzmq) if you use notifszmq for a notification server based on the zmq protocol (you can send notifications to it executing notifszmq.py with title, body and optionally timeout as arguments)
- [matchbox-keyboard](http://git.yoctoproject.org/cgit/cgit.cgi/matchbox-keyboard/about) a virtual keyboard

It has been tested with python 2.7 and a little with python 3.6 but should work fine with the latter as well

Also, it has 2 different notification servers to choose from because pydbus has proved to be challenging to use reliably on Debian Jessie, which is installed on my Kobo Touch, and that's why I made one with zmq to use with some scripts I have.

Licence and Attribution
-----------------------

The icons included (in the icons/ folder) come from the [Adwaita Icon Theme](https://github.com/GNOME/adwaita-icon-theme), part of the [GNOME Project](http://www.gnome.org), licenced under the Creative Commons Attribution-Share Alike 3.0

This work as well is licenced under the Creative Commons Attribution-Share Alike 3.0. United States License.
To view a copy of this licence, visit http://creativecommons.org/licenses/by-sa/3.0/ or send a letter to Creative
Commons, 171 Second Street, Suite 300, San Francisco, California 94105, USA.

Please link to the this project page where available.