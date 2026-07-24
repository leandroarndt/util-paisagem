"""Settings window and ini file reader."""
from decimal import Decimal
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from babel.numbers import format_decimal
from utilpaisagem.gui.common import Settings, PADDING
from utilpaisagem.scenery.common import RESOLUTIONS

class SettingsWindow(object):
    # Útil paisagem things
    settings:Settings
    resolutions:dict

    # GUI
    window:tk.Toplevel
    path_frame:ttk.LabelFrame
    fg_path_name:ttk.Label
    fg_path_var:tk.StringVar
    fg_path_label:ttk.Label
    fg_path_button:ttk.Button
    orthophotos_name:ttk.Label
    orthophotos_var:tk.StringVar
    orthophotos_label:ttk.Label
    orthophotos_button:ttk.Button
    threading_frame:ttk.LabelFrame
    tiles_var:tk.IntVar
    tiles_label:ttk.Label
    tiles_var:tk.IntVar
    tiles_input:ttk.Spinbox
    threads_var:tk.IntVar
    threads_var:tk.IntVar
    threads_label:tk.Label
    threads_input:ttk.Spinbox
    image_frame:ttk.LabelFrame
    resolution_var:tk.IntVar
    resolution_label:ttk.Label
    resolution_option:ttk.OptionMenu
    buttons_frame:ttk.Frame
    ok_button:ttk.Button
    apply_button:ttk.Button
    cancel_button:ttk.Button

    def __init__(self, master, *args, **kwargs):
        # Útil paisagem things
        self.settings = Settings()
        self.resolutions = {}
        for k, v in RESOLUTIONS.items():
            self.resolutions[_('{res} m/px').format(
                res=format_decimal(Decimal(v).quantize(Decimal('1.00')))
            )] = k

        # GUI
        self.window = tk.Toplevel(master, *args, **kwargs)
        self.window.columnconfigure(0, weight=10, pad=PADDING)
        self.window.rowconfigure(0, pad=PADDING)
        self.window.rowconfigure(1, pad=PADDING)
        self.window.rowconfigure(2, pad=PADDING)
        self.window.rowconfigure(3, pad=PADDING)
        # Paths
        self.path_frame = ttk.LabelFrame(self.window, text=_('Paths'), padding=PADDING)
        self.path_frame.columnconfigure(1, weight=10)
        self.fg_path_var = tk.StringVar(self.path_frame, value=self.settings.fgdata_folder)
        self.fg_path_name = ttk.Label(
            self.path_frame,
            text=_('Path to FlightGear data folder:'),
            justify=tk.RIGHT,
        )
        self.fg_path_label = ttk.Label(
            self.path_frame,
            textvariable=self.fg_path_var,
            justify=tk.LEFT,
            font=tk.font.Font(slant='italic'),
        )
        # TODO
        # self.fg_path_button = ttk.Button
        self.orthophotos_var = tk.StringVar(self.path_frame, value=self.settings.orthophotos_folder)
        self.orthophotos_name = ttk.Label(
            self.path_frame,
            text=_('Path to scenery imagery:'),
            justify=tk.RIGHT,
        )
        self.orthophotos_label = ttk.Label(
            self.path_frame,
            textvariable=self.orthophotos_var,
            justify=tk.LEFT,
            font=tk.font.Font(slant='italic'),
        )
        self.fg_path_name.grid(column=0, row=0, sticky=tk.E)
        self.fg_path_label.grid(column=1, row=0, sticky=tk.W)
        self.orthophotos_name.grid(column=0, row=1, sticky=tk.E)
        self.orthophotos_label.grid(column=1, row=1, sticky=tk.W)
        # TODO
        # self.orthophotos_button = ttk.Button
        # Threading
        self.threading_frame =ttk.LabelFrame(self.window, text=_('Threading'), padding=PADDING)
        self.tiles_var = tk.IntVar(self.threading_frame, value=self.settings.tile_threads)
        self.tiles_label = ttk.Label(
            self.threading_frame,
            text=_('Maximum simultaneous tiles to download:'),
            justify=tk.RIGHT
        )
        self.tiles_input = ttk.Spinbox(
            self.threading_frame,
            textvariable=self.tiles_var,
            from_=1,
            to=36,
        )
        # TODO
        # threads_var:tk.IntVar
        # threads_var:tk.IntVar
        # threads_label:tk.Label
        # threads_input:ttk.Spinbox
        self.tiles_label.grid(column=0, row=0, sticky=tk.E)
        self.tiles_input.grid(column=1, row=0, sticky=tk.W)
        # Image resolutions
        self.image_frame = ttk.LabelFrame(self.window, padding=PADDING)
        self.resolution_var = tk.IntVar(self.image_frame, self.settings.download_res)
        self.resolution_label = ttk.Label
        resolution_option:ttk.OptionMenu
        # Buttons
        self.buttons_frame = ttk.Frame(self.window, padding=PADDING)
        self.cancel_button = ttk.Button(
            self.buttons_frame,
            text=_('Cancel'),
            command=self.cancel,
        )
        self.apply_button = ttk.Button(
            self.buttons_frame,
            text=_('Apply'),
            command=self.apply,
        )
        self.ok_button = ttk.Button(
            self.buttons_frame,
            text=_('Ok'),
            command=self.apply_and_close,
        )
        self.cancel_button.grid(column=0, row=0)
        self.apply_button.grid(column=1, row=0)
        self.ok_button.grid(column=2, row=0)

        self.path_frame.grid(column=0, row=0, sticky=tk.W+tk.E)
        self.threading_frame.grid(column=0, row=1, sticky=tk.W+tk.E)
        self.buttons_frame.grid(column=0, row=2, sticky=tk.E)

    def cancel(self):
        self.settings.reload()
        self.window.destroy()

    def apply(self):
        self.settings.fgdata_folder = self.fg_path_var.get()
        self.settings.orthophotos_folder = self.orthophotos_var.get()
        self.settings.tile_threads = int(self.tiles_var .get())
    
    def apply_and_close(self):
        self.apply()
        self.settings.save()
        self.window.destroy()

