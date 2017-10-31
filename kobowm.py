import sys
from utils import system, log, clear_log, close_log, find_full_path, kobowm_path
from Xlib import X, XK
from Xlib.error import CatchError, BadAccess, ConnectionClosedError
from Xlib.display import Display
from Xlib.ext.xtest import fake_input

MAX_EXCEPTIONS = 25
XTERM_COMMAND = ['/usr/bin/xterm']


class WM(object):
    def __init__(self):
        self.display = Display()
        self.root_win = self.display.screen().root
        self.go_on = True  # var to keep looping events (or not)
        self.notifs_on = False
        self.poweroff_time = 0
        clear_log()  # clear the log file once
        # kobo touch screen dimension: 600x800px (minus the dock)
        self.full_width = 600
        self.full_height = 740
        self.keyboard_height = 0
        self.keyboard_on = False
        self.active_window = None # may be transient
        self.top_win_list = []  # list of the top window to cycle in
        self.top_win_pos = -1  # postition in the top win list, -1 means you have to start over
        self.transient_of = {}  # key: win, val: set of windows transient for win
        # windows of wm-related apps
        self.wm_keyboard, self.wm_launcher, self.wm_dock, self.wm_notifs = None, None, None, None
        # codes for the keys to catch
        self.f1_codes = set(code for code, index in self.display.keysym_to_keycodes(XK.XK_F1))
        self.f2_codes = set(code for code, index in self.display.keysym_to_keycodes(XK.XK_F2))
        self.f3_codes = set(code for code, index in self.display.keysym_to_keycodes(XK.XK_F3))
        self.f4_codes = set(code for code, index in self.display.keysym_to_keycodes(XK.XK_F4))
        self.f9_codes = set(code for code, index in self.display.keysym_to_keycodes(XK.XK_F9))
        XK.load_keysym_group('xf86')
        self.poweroff_codes = set(code for code, index in self.display.keysym_to_keycodes(XK.XK_XF86_PowerOff))
        self.poweroff_codes.update(set(code for code, index in self.display.keysym_to_keycodes(XK.XK_F12)))
        self.launch1_codes = set(code for code, index in self.display.keysym_to_keycodes(XK.XK_XF86_Launch1))
        self.launch1_codes.update(set(code for code, index in self.display.keysym_to_keycodes(XK.XK_F11)))
        # error catcher
        error_catcher = CatchError(BadAccess)
        self.root_win.change_attributes(
            event_mask=X.SubstructureRedirectMask,
            onerror=error_catcher,
            background_pixel=self.display.screen().white_pixel
        ) 
        self.display.sync()
        error = error_catcher.get_error()
        if error:
            sys.exit(1)
        # grab root window key events
        self.grab_root_key(self.poweroff_codes, X.NONE)
        self.grab_root_key(self.launch1_codes, X.NONE)
        self.grab_root_key(self.f1_codes, X.NONE)
        self.grab_root_key(self.f2_codes, X.NONE)
        self.grab_root_key(self.f3_codes, X.NONE)
        self.grab_root_key(self.f4_codes, X.NONE)
        self.grab_root_key(self.f9_codes, X.NONE)
        # handlers
        self.display.set_error_handler(self.x_error_handler)
        self.event_dispatch_table = {
            X.MapRequest: self.handle_map_request,
            X.ConfigureRequest: self.handle_configure_request,
            X.MappingNotify: self.handle_mapping_notify,
            X.UnmapNotify: self.handle_unmapping_notify,
            X.KeyPress: self.handle_key_press,
            X.KeyRelease: self.handle_key_release
        }

    def grab_root_key(self, codes, modifier):
        for code in codes:
            self.root_win.grab_key(code, modifier, 1, X.GrabModeAsync, X.GrabModeAsync)

    # top level window utility functions

    def win_show(self):
        window = self.top_win_list[self.top_win_pos]  # assumes it exists
        # map the window
        window.map()
        # map transient window if any
        if window in self.transient_of:
            win = None
            for win in self.transient_of[window]:
                win.map()
            # use last transient as active window
            if win:
                self.active_window = win
            else:
                self.active_window = window
        else:
            # set the window as the active one
            self.active_window = window

    def win_hide(self):
        window = self.top_win_list[self.top_win_pos]  # assumes it exists
        # unmap the window
        window.unmap()
        # un map transient window if any
        if window in self.transient_of:
            for win in self.transient_of[window]:
                win.unmap()
        # unset active window
        self.active_window = None

    def win_remove(self):
        window = self.top_win_list.pop(self.top_win_pos)  # assumes it exists
        # remove entry in transient dict if any
        if window in self.transient_of:
            del self.transient_of[window]
        window.destroy()
        self.active_window = None

    # event handling functions

    def x_error_handler(self, err, request):
        log('X protocol error: {0}'.format(err))

    def loop(self):
        # Load every wm app before starting the actual loop
        try:
            self.load_wmapps()
        except KeyboardInterrupt:
            raise
        # Loop until go_on, Ctrl+C or exceptions > MAX_EXCEPTION times.
        errors = 0
        while self.go_on:
            try:
                self.handle_event()
            except KeyboardInterrupt:
                raise
            except:
                errors += 1
                if errors > MAX_EXCEPTIONS:
                    sys.exit(1)
        close_log()
        self.display.close()

    def load_wmapps(self):
        # launch the other apps:
        python_path = find_full_path('python')
        keyboard_path = find_full_path('matchbox-keyboard')
        if not keyboard_path or not python_path:
            raise KeyboardInterrupt
        system([python_path, kobowm_path + '/launcher.py'])
        system([python_path, kobowm_path + '/dock.py'])
        system([python_path, kobowm_path + '/notifzmq.py'])
        system([keyboard_path])
        # catch the events until every wm app has a window
        while not all((self.wm_notifs, self.wm_keyboard, self.wm_launcher, self.wm_dock)):
            try:
                event = self.display.next_event()
            except ConnectionClosedError:
                log('Display connection closed by server')
                raise KeyboardInterrupt
            # ignore events that are not map requests
            if event.type == X.MapRequest:
                event.window.map()
                if str(event.window.get_wm_name()) == 'Keyboard':
                    self.wm_keyboard = event.window
                    self.keyboard_height = event.window.get_geometry().height
                    event.window.configure(x=0, y=self.full_height-self.keyboard_height, width=self.full_width)
                    # catch the keyboard events to later redirect them to the active window
                    event.window.change_attributes(event_mask=X.KeyPressMask | X.KeyReleaseMask)
                    event.window.unmap()
                elif str(event.window.get_wm_name()) == 'kobowm-dock':
                    self.wm_dock = event.window
                    event.window.configure(x=0, y=self.full_height, width=self.full_width, height=60)
                    event.window.unmap()
                elif str(event.window.get_wm_name()) == 'kobowm-launcher':
                    self.wm_launcher = event.window
                    event.window.configure(x=0, y=0, height=self.full_height, width=self.full_width)
                    event.window.unmap()
                elif str(event.window.get_wm_name()) == 'kobowm-notifications':
                    self.wm_notifs = event.window
                    event.window.configure(x=380, y=20, height=100, width=200)
                    event.window.unmap()
                else:
                    # there is an unexpexted window: stop
                    raise KeyboardInterrupt
        # finally map again the dock
        self.wm_dock.map()

    def handle_event(self):
        try:
            event = self.display.next_event()
        except ConnectionClosedError:
            log('Display connection closed by server')
            raise KeyboardInterrupt
        if event.type in self.event_dispatch_table:
            self.event_dispatch_table[event.type](event)
        else:
            log('unhandled event: {event}'.format(event=event))

    def handle_configure_request(self, event):
        window = event.window
        args = {'border_width': 1}
        if event.value_mask & X.CWX:
            args['x'] = event.x
        if event.value_mask & X.CWY:
            args['y'] = event.y
        if event.value_mask & X.CWWidth:
            args['width'] = event.width
        if event.value_mask & X.CWHeight:
            args['height'] = event.height
        if event.value_mask & X.CWSibling:
            args['sibling'] = event.above
        if event.value_mask & X.CWStackMode:
            args['stack_mode'] = event.stack_mode
        window.configure(**args)

    def handle_map_request(self, event):
        event.window.map()
        # handle transient windows
        transient_for = event.window.get_wm_transient_for()
        if transient_for:
            self.active_window = event.window
            if transient_for not in self.transient_of:
                self.transient_of[transient_for] = []
            self.transient_of[transient_for].append(event.window)
        else:
            if self.active_window:
                self.active_window.unmap()
            self.active_window = event.window
            self.top_win_list.append(event.window)
            self.top_win_pos = len(self.top_win_list) - 1
        # use all the available screen
        self.active_window.configure(x=-1, y=-1, width=self.full_width, height=self.full_height)
        # hide the keyboard if it was open
        if self.keyboard_on:
            self.wm_keyboard.unmap()
            self.keyboard_on = False

    def handle_mapping_notify(self, event):
        # necessary by documentation
        self.display.refresh_keyboard_mapping(event)

    def handle_unmapping_notify(self, event):
        # used to handle windows that get unmapped not by this wm directly
        transient_for = event.window.get_wm_transient_for()
        if transient_for:
            self.transient_of[transient_for].remove(event.window)
            if self.active_window == event.window:
                self.active_window = transient_for
        elif event.window in self.top_win_list:
            self.top_win_list.remove(event.window)
            if self.active_window == event.window:
                self.active_window = None
                self.top_win_pos = -1

    def handle_key_press(self, event):
        if event.window == self.wm_keyboard:
            return  # do nothing: will be sent to the active window on release
        if event.detail in self.poweroff_codes:
            self.go_on = False
        elif event.detail in self.launch1_codes:
            self.action_apps()
        elif event.detail in self.f1_codes:
            self.action_tasks()
        elif event.detail in self.f2_codes:
            self.action_keyboard()
        elif event.detail in self.f3_codes:
            system(XTERM_COMMAND)
        elif event.detail in self.f4_codes:
            self.action_close()
        elif event.detail in self.f9_codes:
            self.action_notifs()

    def handle_key_release(self, event):
        if event.window == self.wm_keyboard:
            # focus on the active window and emulate key press/release
            self.display.sync()
            self.display.set_input_focus(self.active_window, X.RevertToParent, X.CurrentTime)
            fake_input(self.display, X.KeyPress, event.detail)
            fake_input(self.display, X.KeyRelease, event.detail)
            self.display.sync()

    # action performer functions

    def action_apps(self):
        if not self.active_window:
            self.active_window = self.wm_launcher
            self.active_window.map()
        elif self.active_window == self.wm_launcher:
            self.active_window.unmap()
            self.active_window = None
        else:
            # hide the active window (and the stack if it's transient)
            self.win_hide()
            # start over with the cycling
            self.top_win_pos = -1
            self.active_window = self.wm_launcher
            self.active_window.map()

    def action_tasks(self):
        if not self.top_win_list:
            return
        if self.top_win_pos != -1 and self.top_win_pos < len(self.top_win_list):
            self.win_hide()
        self.top_win_pos += 1
        if self.top_win_pos >= len(self.top_win_list):
            self.top_win_pos = 0
        self.win_show()

    def action_keyboard(self):
        if self.keyboard_on:
            self.wm_keyboard.unmap()
            self.active_window.configure(height=self.full_height)
            self.keyboard_on = False
        elif self.active_window and self.active_window != self.wm_launcher:
            self.wm_keyboard.map()
            self.active_window.configure(height=self.full_height-self.keyboard_height)
            self.wm_keyboard.configure(stack_mode=X.Above)
            self.keyboard_on = True

    def action_close(self):
        if not self.active_window:
            return  # nothing to close here
        if self.active_window in self.top_win_list:
            self.win_remove()
        else:
            # it's a transient window
            transient_for = self.active_window.get_wm_transient_for()
            self.transient_of[transient_for].remove(self.active_window)
            self.active_window.destroy()
            self.active_window = transient_for
        # close the keyboard if open
        if self.keyboard_on:
            self.wm_keyboard.unmap()
            self.keyboard_on = False

    def action_notifs(self):
        if self.notifs_on:
            self.wm_notifs.unmap()
            log('Notification window hidden')
        else:
            self.wm_notifs.configure(stack_mode=X.Above)
            self.wm_notifs.map()
            log('Notification window visible')
        self.notifs_on = not self.notifs_on


if __name__ == '__main__':
    wm = WM()
    wm.loop()
