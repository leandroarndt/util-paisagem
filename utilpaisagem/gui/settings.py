"""Settings window and ini file reader."""
import math
from decimal import Decimal
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from babel.numbers import format_decimal
from utilpaisagem.gui.common import Settings, PADDING, LOCALE
from utilpaisagem.scenery.common import RESOLUTIONS

class Distance(ttk.Frame):
    resolution:int
    distance:tk.IntVar
    status:tk.BooleanVar
    toggle:ttk.Checkbutton
    distance_entry:ttk.Spinbox
    km_label:ttk.Label

    def __init__(self, master, resolution:int, distance:int, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.resolution = resolution
        self.distance = tk.IntVar(self, value=distance)
        self.status = tk.BooleanVar(self)
        self.columnconfigure(0, pad=PADDING)
        self.columnconfigure(1, pad=PADDING)
        self.columnconfigure(2, pad=PADDING)
        self.toggle = ttk.Checkbutton(
            master,
            text=_('{res} m/px range:').format(
                res=format_decimal(Decimal(RESOLUTIONS[resolution]).quantize(Decimal('1.00')), locale=LOCALE)
            ),
            variable=self.status,
        )
        self.distance_entry = ttk.Spinbox(
            master,
            textvariable=self.distance,
            from_=-1,
            to=44100,
        )
        self.km_label = ttk.Label(master, text=_('Km'))
        if distance > 0:
            self.status.set(True)
        else:
            self.status.set(False)
            self.distance_entry.configure(state=tk.DISABLED)
        self.status.trace_add('write', self.status_change)
    
    def get(self) -> dict[int:int]|None:
        if self.status.get():
            return {self.resolution: int(self.distance.get())}
        return None

    def grid_items(self, column, row):
        self.toggle.grid(column=column, row=row, sticky=tk.W)
        self.distance_entry.grid(column=column+1, row=row, sticky=tk.E)
        self.km_label.grid(column=column+2, row=row, sticky=tk.W)
    
    def status_change(self, *args, **kwargs):
        if self.status.get():
            self.distance_entry.config(state='enable')
        else:
            self.distance_entry.config(state='disable')

class SettingsWindow(object):
    # Útil paisagem things
    settings:Settings
    sizes:list
    distances:list
    main_window:object # MainWindow object. Import cannot be done due to recurrence.

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
    download_frame:ttk.LabelFrame
    radius_var:tk.IntVar
    radius_label:ttk.Label
    radius_input:ttk.Spinbox
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
    resolution_option:ttk.Combobox
    buttons_frame:ttk.Frame
    ok_button:ttk.Button
    apply_button:ttk.Button
    cancel_button:ttk.Button

    def __init__(self, master, main_window, *args, **kwargs):
        # Útil paisagem things
        self.main_window = main_window
        self.settings = Settings()
        self.sizes = []
        for r in RESOLUTIONS.keys():
            self.sizes.append(self.format_size(r))

        # GUI
        self.window = tk.Toplevel(master, *args, **kwargs)
        self.window.protocol('WM_DELETE_WINDOW', lambda: self.cancel())
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
        self.fg_path_button = ttk.Button(
            self.path_frame,
            text=_('Choose folder'),
            command=self.choose_fgdata_dir,
        )
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
        self.orthophotos_button = ttk.Button(
            master=self.path_frame,
            text=_('Choose folder'),
            command=self.choose_orthophotos_dir,
        )
        self.fg_path_name.grid(column=0, row=0, sticky=tk.E)
        self.fg_path_label.grid(column=1, row=0, sticky=tk.W)
        self.fg_path_button.grid(column=2, row=0, sticky=tk.E)
        self.orthophotos_name.grid(column=0, row=1, sticky=tk.E)
        self.orthophotos_label.grid(column=1, row=1, sticky=tk.W)
        self.orthophotos_button.grid(column=2, row=1, sticky=tk.E)
        # Threading and download range
        self.download_frame = ttk.LabelFrame(self.window, text=_('Download'), padding=PADDING)
        self.radius_var = tk.IntVar(self.download_frame, value=self.settings.radius)
        self.radius_label = ttk.Label(
            self.download_frame,
            text=_('Download radius:')
        )
        self.radius_input = ttk.Spinbox(
            self.download_frame,
            textvariable=self.radius_var,
            from_=0,
            to=44100,
        )
        self.tiles_var = tk.IntVar(self.download_frame, value=self.settings.tile_threads)
        self.tiles_label = ttk.Label(
            self.download_frame,
            text=_('Maximum simultaneous tiles to download:'),
            justify=tk.RIGHT
        )
        self.tiles_input = ttk.Spinbox(
            self.download_frame,
            textvariable=self.tiles_var,
            from_=1,
            to=36,
        )
        # TODO
        # threads_var:tk.IntVar
        # threads_var:tk.IntVar
        # threads_label:tk.Label
        # threads_input:ttk.Spinbox
        self.radius_label.grid(column=0, row=0, sticky=tk.E)
        self.radius_input.grid(column=1, row=0, sticky=tk.W)
        self.tiles_label.grid(column=0, row=1, sticky=tk.E)
        self.tiles_input.grid(column=1, row=1, sticky=tk.W)
        # Image resolutions
        self.image_frame = ttk.LabelFrame(self.window, text=_('Image'), padding=PADDING)
        self.resolution_var = tk.StringVar(
            self.image_frame,
            self.format_size(self.settings.download_res),
        )
        self.resolution_label = ttk.Label(self.image_frame, text=_('Download size:'))
        self.resolution_option = ttk.Combobox(
            self.image_frame,
            values=self.sizes,
            textvariable=self.resolution_var,
        )
        self.resolution_label.grid(column=0, row=0, sticky=tk.E)
        self.resolution_option.grid(column=1, row=0, sticky=tk.W)
        self.distances = []
        row = 1
        resolution_distance = {}
        for d, r in self.settings.distances.items():
            resolution_distance[r] = d
        for r in RESOLUTIONS.keys():
            try:
                d = resolution_distance[r]
            except KeyError:
                d = -1
            distance_frame = Distance(self.image_frame, resolution=r, distance=d)
            self.distances.append(distance_frame)
            distance_frame.grid_items(column=0, row=row)
            row += 1
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
        # Place frames
        self.path_frame.grid(column=0, row=0, sticky=tk.W+tk.E)
        self.download_frame.grid(column=0, row=1, sticky=tk.W+tk.E)
        self.image_frame.grid(column=0, row=2, sticky=tk.W+tk.E)
        self.buttons_frame.grid(column=0, row=3, sticky=tk.E)

    def format_size(self, res:int) -> str:
        """Formats image size to a readable format."""
        return _('{size} lines').format(size=2**res)
    
    def unformat_size(self, formatted:str) -> int:
        """Returns the exponent of a download size readable string."""
        return int(math.log2(int(formatted.split()[0])))

    def choose_fgdata_dir(self):
        path = tk.filedialog.askdirectory(
            parent=self.window,
            title=_('Choose FlightGear data directory'),
            initialdir=self.settings.fgdata_folder,
        )
        if path and Path(path).is_dir():
            self.fg_path_var.set(path)

    def choose_orthophotos_dir(self):
        path = tk.filedialog.askdirectory(
            parent=self.window,
            title=_('Choose "Orthophotos" directory'),
            initialdir=self.orthophotos_var.get(),
        )
        if not path:
            return
        path = Path(path)
        path = path.expanduser()
        if Path(path).is_dir():
            if path.name.lower() != 'orthophotos': # Invalid path
                tk.messagebox.showerror(
                    title=_('Invalid folder'),
                    message=_('Please choose a folder named "Orthophotos".')
                )
            if path.name != 'Orthophotos': # Normalize
                path = path.rename(path.parent / 'Orthophotos')
            self.orthophotos_var.set(path)

    def cancel(self):
        self.settings.reload()
        self.make_changes()
        self.window.destroy()

    def apply(self):
        self.settings.fgdata_folder = self.fg_path_var.get()
        self.settings.orthophotos_folder = self.orthophotos_var.get()
        self.settings.radius = int(self.radius_var.get())
        self.settings.tile_threads = int(self.tiles_var .get())
        self.settings.download_res = self.unformat_size(self.resolution_var.get())
        distances = {}
        max_distance = 0
        for d in self.distances:
            if d.status.get() and d.distance.get() > 0:
                dist = int(d.distance.get())
                distances[dist] = d.resolution
                if dist > max_distance:
                    max_distance = dist
        if max_distance < self.settings.radius:
            res = distances.pop(sorted(distances.keys())[-1])
            distances[self.settings.radius] = res
        self.settings.distances = distances
        self.make_changes()
    
    def make_changes(self):
        self.main_window.download_manager.radius = self.settings.radius
        self.main_window.download_manager.resolutions = self.settings.distances
        self.main_window.download_manager.max_downloads = self.settings.tile_threads
    
    def apply_and_close(self):
        self.apply()
        self.settings.save()
        self.window.destroy()
