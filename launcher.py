import Tkinter as tk
from Tkinter import PhotoImage
from os import listdir
from os.path import isfile, join, exists
from functools import partial
from json import dump, load
from utils import system, kobowm_path, find_full_path, xterm_launch


class Launcher(tk.Frame):
    def __init__(self, master=None):
        self.apps = []
        self.page = -1
        # init, configure and draw window
        tk.Frame.__init__(self, master)
        self.master.title('kobowm-launcher')
        self.configure(background='white')
        for i in range(20):
            self.rowconfigure(i, minsize=37)
        self.columnconfigure(0, minsize=563)
        self.columnconfigure(1, minsize=37)
        self.grid()
        # icons
        self.reload_icon = PhotoImage(file=kobowm_path + '/icons/view-refresh-symbolic.symbolic.png')
        self.next_icon = PhotoImage(file=kobowm_path + '/icons/go-next-symbolic.symbolic.png')
        # side buttons
        button = tk.Button(self, bg='white', image=self.reload_icon, command=self.load_apps)
        button.grid(column=1, row=0, sticky=tk.N + tk.E + tk.S + tk.W)
        button = tk.Button(self, bg='white', image=self.next_icon, command=self.show_next_page)
        button.grid(column=1, row=1, rowspan=19, sticky=tk.N + tk.E + tk.S + tk.W)
        # apps buttons
        self.buttons = []
        for i in range(10):
            button = tk.Button(self, bg='white')
            button.grid(column=0, row=i*2, rowspan=2, sticky=tk.N + tk.E + tk.S + tk.W)
            self.buttons.append(button)
        # load the apps and fill the buttons
        self.load_apps(re_gen=False)

    def load_apps(self, re_gen=True):
        cache_path = kobowm_path + '/data/app_cache.json'
        if re_gen or not exists(cache_path):
            # (re)generate the app cache file
            apps_path = '/usr/share/applications/'
            dtop_files = [f for f in listdir(apps_path) if isfile(join(apps_path, f)) and f.endswith('.desktop')]
            all_apps = []
            for entry in dtop_files:
                name, run, term, runnable = entry[:-8], None, False, False
                with open(join(apps_path, entry), 'r') as f:
                    line = f.readline()
                    while line:
                        if line.startswith('Exec='):
                            run = line[5:].rstrip().split()
                            if not run[0].startswith('/'):
                                full_path = find_full_path(run[0])
                                if full_path:
                                    run[0] = full_path
                            # check path existence
                            if exists(run[0]):
                                runnable = True
                        elif line.startswith('Name='):
                            name = line[5:].rstrip()
                        elif line.startswith('Terminal=true'):
                            term = True
                        line = f.readline()
                all_apps.append(
                    {
                        'entry': entry,
                        'name': name,
                        'run': run,
                        'term': term,
                        'runnable': runnable
                    }
                )
            # save all apps
            with open(cache_path, 'w') as f:
                dump(all_apps, fp=f)
        else:
            # read the app list from the cache file
            with open(cache_path, 'r') as f:
                all_apps = load(fp=f)
        # anyway, select only the runnable apps
        self.apps = [app for app in all_apps if app['runnable'] is True]
        # and finally show the first page
        self.page = -1
        self.show_next_page()

    def show_next_page(self):
        self.page += 1
        if self.page * 10 >= len(self.apps):
            # start over if reached the end
            self.page = 0
        i = self.page * 10
        for button in self.buttons:
            if i < len(self.apps):
                button.config(text=self.apps[i]['name'])
                button.config(command=partial(launch_app, self.apps[i]))
                button.grid()
            else:
                button.grid_remove()
            i += 1


def launch_app(app):
    comm = app['run']
    if app['term']:
        comm = xterm_launch + comm
    system(comm)


def main():
    launcher = Launcher()
    launcher.mainloop()


if __name__ == '__main__':
    main()
