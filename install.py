import os, platform, webbrowser
from os import popen, _wrap_close
from venv import EnvBuilder
from pathlib import Path
from threading import Thread
from time import sleep
import tkinter as tk
from tkinter import ttk, messagebox

PADDING=6
REQUIRED_PYTHON_VERSION = (3, 13, 0)
if 'TEST' in os.environ:
    ENV_DIR = Path(__file__).parent / '.test_env'
else:
    ENV_DIR = Path(__file__).parent / '.env'
REQUIREMENTS = Path(__file__).parent / 'requirements.txt'

class VersionError(Exception):
    pass

class Installer(EnvBuilder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create(self, *args, **kwargs):
        super().create(*args, **kwargs)

    def post_setup(self, context):
        os.environ['VIRTUAL_ENV'] = context.env_dir
        self.context = context
    
    def install_requirements(self):
        print(self.context.bin_path)

class InstallerWindow(object):
    # Installation
    current_task:_wrap_close
    installer:Installer

    # GUI
    window:tk.Tk
    python_version_label:ttk.Label
    environment_var:tk.StringVar
    environment_label:ttk.Label
    pip_var:tk.StringVar
    pip_label:ttk.Label
    locales_var:tk.StringVar
    locales_label:ttk.Label
    shortcut_var:tk.StringVar
    shortcut_label:ttk.Label
    exit_button:ttk.Button

    def __init__(self):
        # Build GUI
        self.window = tk.Tk()
        self.window.title('Installing Útil paisagem')
        self.contents = ttk.Frame(self.window, padding=PADDING)
        self.contents.columnconfigure((0, 2), weight=1)
        self.contents.columnconfigure(1, weight=0)
        self.environment_var = tk.StringVar(self.contents, value='Create virtual environment.')
        self.environment_label = ttk.Label(self.contents, textvariable=self.environment_var)
        self.pip_var = tk.StringVar(self.contents, value='Install required packages.')
        self.pip_label = tk.Label(self.contents, textvariable=self.pip_var)
        self.locales_var = tk.StringVar(self.contents, value='Compile translations.')
        self.locales_label = ttk.Label(self.contents, textvariable=self.locales_var)
        self.shortcut_var = tk.StringVar(self.contents, value='Create shortcut.')
        self.shortcut_label = tk.Label(self.contents, textvariable=self.shortcut_var)
        self.exit_button = ttk.Button(self.contents, text='Quit', command=lambda: self.window.destroy())
        # Grid
        self.contents.pack(fill=tk.BOTH)
        self.environment_label.grid(column=0, row=0, columnspan=3, sticky=tk.W)
        self.pip_label.grid(column=0, row=1, columnspan=3, sticky=tk.W)
        self.locales_label.grid(column=0, row=2, columnspan=3, sticky=tk.W)
        self.shortcut_label.grid(column=0, row=3, columnspan=3, sticky=tk.W)
        self.exit_button.grid(column=1, row=4, sticky=tk.W+tk.E)

        self.window.after(1, self.install)

    def install(self):
        # Verify Python version >= 3.13
        python_version = platform.python_version_tuple()
        try:
            if int(python_version[0]) < REQUIRED_PYTHON_VERSION[0]:
                raise VersionError
            if int(python_version[1]) < REQUIRED_PYTHON_VERSION[1]:
                raise VersionError
            if int(python_version[2]) < REQUIRED_PYTHON_VERSION[2]:
                raise VersionError
        except VersionError:
            messagebox.showerror(
                title='Wrong Python version',
                message=f'The installer was invoked with Python {python_version[0]}.{python_version[1]}.{python_version[2]}. \
You must upgrade to Python {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]}.{REQUIRED_PYTHON_VERSION[2]} or greater in order to use Útil paisagem.'
            )
            webbrowser.open('https://www.python.org/downloads/')
            self.window.destroy()

        # Installation
        self.installer = Installer(
            clear=True,
            symlinks=False,
            with_pip=True,
            system_site_packages=False,
        )

        self.window.after(1, self.create_environment)

    def wait(self, thread:Thread, variable:tk.StringVar, message:str, next_step:callable):
        if thread.is_alive():
            self.window.after(100, self.wait, thread, variable, message, next_step)
        else:
            variable.set(message)
            next_step()

    def create_environment(self):
        self.environment_var.set('Creating virtual environment...')
        thread = Thread(target=self.installer.create, args=(ENV_DIR,))
        thread.start()
        self.wait(
            thread=thread,
            variable=self.environment_var,
            message='Virtual environment created.',
            next_step=self.install_packages,
        )
    
    def install_packages(self):
        self.pip_var.set('Installing required packages...')
        thread = Thread(target=self.installer.install_requirements)
        self.wait(
            thread=thread,
            variable=self.pip_var,
            message='Required packages installed.',
            next_step=self.compile_translations
        )
    
    def compile_translations(self):
        self.locales_var.set('Compiling translations...')
        self.window.update()
        self.window.update_idletasks()
        self.locales_var.set('Translations compiled.')
        self.window.after(1, self.create_shortcuts)
    
    def create_shortcuts(self):
        self.shortcut_var.set('Creating shortcuts...')
        self.window.update()
        self.window.update_idletasks()
        self.shortcut_var.set('Shortcuts created.')
        self.window.after(1, self.finish)
    
    def finish(self):
        messagebox.showinfo(
            title='Success',
            message='Útil paisagem has been successfully installed.\
A shortcut for the application has been created.'
        )
        self.window.destroy()

if __name__ == '__main__':
    gui = InstallerWindow()
    gui.window.mainloop()
