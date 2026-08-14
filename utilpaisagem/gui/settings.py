"""Settings window and ini file reader."""
from typing import TYPE_CHECKING, List, Dict
import math
from decimal import Decimal
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from babel.numbers import format_decimal
from utilpaisagem.gui.common import Settings, PADDING, LOCALE
from utilpaisagem.scenery.common import RESOLUTIONS, COMPRESSION
from utilpaisagem.scenery.image_service import IMAGE_SERVICES

if TYPE_CHECKING:
    from utilpaisagem.gui.main import MainWindow
else:
    class MainWindow:
        pass
    
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
    sizes:List
    distances:List
    main_window:MainWindow

    # GUI
    window:tk.Toplevel
    notebook:ttk.Notebook
    flightgear_tab:ttk.Frame
    path_frame:ttk.LabelFrame
    fg_path_name:ttk.Label
    fg_path_var:tk.StringVar
    fg_path_label:ttk.Label
    fg_path_button:ttk.Button
    orthophotos_name:ttk.Label
    orthophotos_var:tk.StringVar
    orthophotos_label:ttk.Label
    orthophotos_button:ttk.Button
    connection_frame:ttk.LabelFrame
    host_var:tk.StringVar
    host_label:ttk.Label
    host_input:ttk.Entry
    port_var:tk.IntVar
    port_label:ttk.Label
    port_input:ttk.Entry
    interval_var:tk.IntVar
    interval_label:ttk.Label
    interval_input:ttk.Entry
    interval_seconds_label:ttk.Label
    download_tab:ttk.Frame
    image_service_frame:ttk.LabelFrame
    image_service_var:tk.StringVar
    image_service_label:ttk.Label
    image_service_entry:ttk.Combobox
    image_service_full_name_var:tk.StringVar
    image_service_full_name_label:ttk.Label
    image_service_license_var:t.StringVar
    image_service_license_label:ttk.Label
    download_frame:ttk.LabelFrame
    radius_var:tk.IntVar
    radius_label:ttk.Label
    radius_input:ttk.Spinbox
    radius_km_label:ttk.Label
    tiles_var:tk.IntVar
    tiles_label:ttk.Label
    tiles_var:tk.IntVar
    tiles_input:ttk.Spinbox
    resolution_var:tk.IntVar
    resolution_label:ttk.Label
    resolution_entry:ttk.Combobox
    image_format_var:tk.StringVar
    image_format_label:tk.Label
    image_format_entry:ttk.Combobox
    threads_var:tk.IntVar
    threads_var:tk.IntVar
    threads_label:tk.Label
    threads_input:ttk.Spinbox
    image_frame:ttk.LabelFrame
    tile_management_tab:ttk.Frame
    tile_age_frame:ttk.Labelframe
    renewal_age_var:tk.IntVar
    renewal_age_label:ttk.Label
    renewal_age_entry:ttk.Entry
    deletion_age_var:tk.IntVar
    deletion_age_label:ttk.Label
    deletion_age_input:ttk.Entry
    disk_usage_frame:ttk.Labelframe
    disk_space_limit_var:tk.IntVar
    disk_space_limit_label:ttk.Label
    disk_space_limit_input:ttk.Entry
    auto_clean_var:tk.BooleanVar
    auto_clean_entry:ttk.Checkbutton
    disk_space_label:ttk.Label
    interface_tab:ttk.Frame
    detail_frame:ttk.LabelFrame
    detail_degree_var:tk.IntVar
    detail_degree_label:ttk.Label
    detail_degree_entry:ttk.Spinbox
    detail_tile_var:tk.IntVar
    detail_tile_label:ttk.Label
    detail_tile_entry:ttk.Spinbox
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
        self.window.title(_('Útil paisagem settings'))
        self.window.protocol('WM_DELETE_WINDOW', lambda: self.cancel())
        self.window.columnconfigure(0, weight=10, pad=PADDING)
        self.window.rowconfigure(0, weight=10, pad=PADDING)
        self.window.rowconfigure(1, pad=PADDING)
        self.window.rowconfigure(2, pad=PADDING)
        self.window.rowconfigure(3, pad=PADDING)
        self.notebook = ttk.Notebook(self.window)
        self.notebook.grid(column=0, row=0, sticky=tk.N+tk.E+tk.S+tk.W)
        # FlightGear tab
        self.flightgear_tab = ttk.Frame(self.notebook, padding=PADDING)
        self.flightgear_tab.columnconfigure(0, weight=10)
        self.notebook.add(self.flightgear_tab, text=_('FlightGear'))
        # Paths
        self.path_frame = ttk.LabelFrame(self.flightgear_tab, text=_('Paths'), padding=PADDING)
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
        # Connection
        self.connection_frame = ttk.Labelframe(
            self.flightgear_tab,
            text=_('FlightGear connection'),
            padding=PADDING
        )
        self.host_var = tk.StringVar(self.connection_frame, value=self.settings.host)
        self.host_label = ttk.Label(self.connection_frame, text=_('Host:'))
        self.host_input = ttk.Entry(self.connection_frame, textvariable=self.host_var)
        self.port_var = tk.IntVar(self.connection_frame, value=self.settings.port)
        self.port_label = ttk.Label(self.connection_frame, text=_('Port:'))
        self.port_input = ttk.Entry(self.connection_frame, textvariable=self.port_var)
        self.interval_var = tk.IntVar(
            self.connection_frame,
            value=int(self.settings.following_interval/1000),
        )
        self.interval_label = ttk.Label(
            self.connection_frame,
            text=_('Interval retrieving aircraft location:'),
        )
        self.interval_input = ttk.Entry(self.connection_frame, textvariable=self.interval_var)
        self.interval_seconds_label = ttk.Label(self.connection_frame, text=_('seconds'))
        self.host_label.grid(column=0, row=0, sticky=tk.E)
        self.host_input.grid(column=1, row=0, sticky=tk.W)
        self.port_label.grid(column=0, row=1, sticky=tk.E)
        self.port_input.grid(column=1, row=1, sticky=tk.W)
        self.interval_label.grid(column=0, row=2, sticky=tk.E)
        self.interval_input.grid(column=1, row=2, sticky=tk.W)
        self.interval_seconds_label.grid(column=2, row=2, sticky=tk.W)
        self.path_frame.grid(column=0, row=0, sticky=tk.W+tk.E)
        self.connection_frame.grid(column=0, row=1, sticky=tk.W+tk.E)
        # Download tab
        self.download_tab = ttk.Frame(self.notebook, padding=PADDING)
        self.download_tab.columnconfigure(0, weight=10)
        self.notebook.add(self.download_tab, text=_('Download'))
        # Image services
        self.image_service_frame = ttk.LabelFrame(
            self.download_tab,
            text=_('Image service')
        )
        self.image_service_frame.columnconfigure(0, weight=0)
        self.image_service_frame.columnconfigure(1, weight=10)
        self.image_service_var = tk.StringVar(
            self.image_service_frame,
            value=self.settings.image_service
        )
        self.image_service_var.trace('w', self.change_image_service)
        self.image_service_label = ttk.Label(
            self.image_service_frame,
            text=_('Image service:')
        )
        self.image_service_entry = ttk.Combobox(
            self.image_service_frame,
            values=list(IMAGE_SERVICES.keys()),
            textvariable=self.image_service_var,
        )
        self.image_service_description_var = tk.StringVar(
            self.image_service_frame,
            value=IMAGE_SERVICES[self.settings.image_service].description,
        )
        self.image_service_description_label = ttk.Label(
            self.image_service_frame,
            textvariable=self.image_service_description_var,
        )
        self.image_service_license_var = tk.StringVar(
            self.image_service_frame,
            value=_('Image service license at {link}').format(
                link=IMAGE_SERVICES[self.settings.image_service].license_link
            ),
        )
        self.image_service_license_label = ttk.Label(
            self.image_service_frame,
            textvariable=self.image_service_license_var,
        )
        self.image_service_label.grid(column=0, row=0, sticky=tk.E)
        self.image_service_entry.grid(column=1, row=0, sticky=tk.W)
        self.image_service_description_label.grid(column=0, row=1, columnspan=2, sticky=tk.W)
        self.image_service_license_label.grid(column=0, row=2, columnspan=2, sticky=tk.W)
        # Threading and download range
        self.download_frame = ttk.LabelFrame(
            self.download_tab,
            text=_('Download'),
            padding=PADDING
        )
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
        self.radius_km_label = ttk.Label(self.download_frame, text=_('Km'))
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
        self.threads_var = tk.IntVar(self.download_frame, value=self.settings.image_threads)
        self.threads_label=ttk.Label(
            self.download_frame,
            text=_('Maximum simultaneous downloads for each tile:'),
            justify=tk.RIGHT,
        )
        self.threads_input = ttk.Spinbox(
            self.download_frame,
            textvariable=self.threads_var,
            from_=1,
            to=36,
        )
        self.resolution_var = tk.StringVar(
            self.download_frame,
            self.format_size(self.settings.download_res),
        )
        self.resolution_label = ttk.Label(self.download_frame, text=_('Download size:'))
        self.resolution_entry = ttk.Combobox(
            self.download_frame,
            values=self.sizes,
            textvariable=self.resolution_var,
        )
        self.image_format_var = tk.StringVar(self.download_frame)
        for k, v in COMPRESSION.items():
            if v == self.settings.image_format:
                self.image_format_var.set(k)
        self.image_format_label = ttk.Label(self.download_frame, text=_('Image file format:'))
        self.image_format_entry = ttk.Combobox(
            self.download_frame,
            values=list(COMPRESSION.keys()),
            textvariable=self.image_format_var
        )
        self.radius_label.grid(column=0, row=0, sticky=tk.E)
        self.radius_input.grid(column=1, row=0, sticky=tk.W+tk.E)
        self.radius_km_label.grid(column=2, row=0, sticky=tk.W)
        self.resolution_label.grid(column=0, row=1, sticky=tk.E)
        self.resolution_entry.grid(column=1, row=1, sticky=tk.W+tk.E)
        self.image_format_label.grid(column=0, row=2, sticky=tk.E)
        self.image_format_entry.grid(column=1, row=2, sticky=tk.W+tk.E)
        self.tiles_label.grid(column=0, row=3, sticky=tk.E)
        self.tiles_input.grid(column=1, row=3, sticky=tk.W+tk.E)
        self.threads_label.grid(column=0, row=4, sticky=tk.E)
        self.threads_input.grid(column=1, row=4, sticky=tk.W+tk.E)
        self.image_service_frame.grid(column=0, row=0, sticky=tk.W+tk.E)
        self.download_frame.grid(column=0, row=1, sticky=tk.W+tk.E)
        # Image tab
        self.image_tab = ttk.Frame(self.notebook, padding=PADDING)
        self.image_tab.rowconfigure(0, weight=10)
        self.notebook.add(self.image_tab, text=_('Image resolution'))
        # Image resolutions
        self.image_frame = ttk.LabelFrame(self.image_tab, text=_('Image'), padding=PADDING)
        self.image_frame.grid(column=0, row=0, sticky=tk.W+tk.E)
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
        # Tile management
        self.tile_management_tab = ttk.Frame(self.notebook, padding=PADDING)
        self.tile_management_tab.columnconfigure(0, weight=10)
        self.notebook.add(self.tile_management_tab, text=_('Tile management'))
        # Tile age
        self.tile_age_frame = ttk.Labelframe(
            self.tile_management_tab,
            text=_('Tile age'),
            padding=PADDING
        )
        self.renewal_age_var = tk.IntVar(self.tile_age_frame, value=self.settings.renewal_age)
        self.renewal_age_label = ttk.Label(
            self.tile_age_frame,
            text=_('Days until downloading new image for tile:'),
        )
        self.renewal_age_entry = ttk.Entry(self.tile_age_frame, textvariable=self.renewal_age_var)
        self.deletion_age_var = tk.IntVar(
            self.tile_age_frame,
            value=self.settings.deletion_age,
        )
        self.deletion_age_label = ttk.Label(
            self.tile_age_frame,
            text=_('Days before deleting unused tiles:')
        )
        self.deletion_age_input = ttk.Entry(
            self.tile_age_frame,
            textvariable=self.deletion_age_var,
        )
        self.renewal_age_label.grid(column=0, row=0, sticky=tk.E)
        self.renewal_age_entry.grid(column=1, row=0, sticky=tk.W)
        self.deletion_age_label.grid(column=0, row=1, sticky=tk.E)
        self.deletion_age_input.grid(column=1, row=1, sticky=tk.W)
        self.disk_usage_frame = ttk.Labelframe(
            self.tile_management_tab,
            text=_('Disk usage'),
            padding=PADDING,
        )
        self.disk_space_limit_var = tk.IntVar(self.disk_usage_frame, value=int(self.settings.max_disk_usage / 1024**2))
        self.disk_space_limit_label = ttk.Label(
            self.disk_usage_frame,
            text=_('Maximum disk usage in megabytes:'),
        )
        self.disk_space_limit_input = ttk.Entry(self.disk_usage_frame, textvariable=self.disk_space_limit_var)
        self.auto_clean_var = tk.BooleanVar(self.disk_usage_frame, self.settings.auto_clean)
        self.auto_clean_entry = ttk.Checkbutton(
            self.disk_usage_frame,
            text=_('Automatically enforce disk usage limit'),
            variable=self.auto_clean_var,
        )
        self.disk_space_label = ttk.Label(
            self.disk_usage_frame,
            text=_('Disk space used: {space} MB').format(
                space=format_decimal(
                    Decimal(self.main_window.tile_manager.disk_usage / 1024**2).quantize(Decimal('1.00')),
                    locale=LOCALE
                ),
            ),
        )
        self.disk_space_limit_label.grid(column=0, row=0, sticky=tk.E)
        self.disk_space_limit_input.grid(column=1, row=0, sticky=tk.W)
        self.auto_clean_entry.grid(column=0, row=1, sticky=tk.W)
        self.disk_space_label.grid(column=0, row=2, sticky=tk.W)
        self.tile_age_frame.grid(column=0, row=0, sticky=tk.W+tk.E)
        self.disk_usage_frame.grid(column=0, row=1, sticky=tk.W+tk.E)
        # Interface
        self.interface_tab = ttk.Frame(self.notebook, padding=PADDING)
        self.interface_tab.columnconfigure(0, weight=10)
        self.notebook.add(self.interface_tab, text=_('Interface'))
        # Detail levels
        self.detail_frame = ttk.LabelFrame(
            self.interface_tab,
            text=_('Detail levels'),
        )
        self.detail_degree_var = tk.IntVar(self.detail_frame, value=self.settings.detail_degree)
        self.detail_degree_label = ttk.Label(
            self.detail_frame,
            text=_('Maximum latitude and longitude range for 1 degree tiles display:')
        )
        self.detail_degree_entry = ttk.Spinbox(
            self.detail_frame,
            textvariable=self.detail_degree_var,
            from_=2,
            to=180,
        )
        self.detail_tile_var = tk.IntVar(self.detail_frame, value=self.settings.detail_tile)
        self.detail_tile_label = ttk.Label(
            self.detail_frame,
            text=_('Maximum latitude and longitude range for scenery tiles display:'),
        )
        self.detail_tile_entry = ttk.Spinbox(
            self.detail_frame,
            textvariable=self.detail_tile_var,
            from_=1,
            to=180,
        )
        self.detail_degree_label.grid(column=0, row=0, sticky=tk.E)
        self.detail_degree_entry.grid(column=1, row=0, sticky=tk.W)
        self.detail_tile_label.grid(column=0, row=1, sticky=tk.E)
        self.detail_tile_entry.grid(column=1, row=1, sticky=tk.W)
        self.detail_frame.grid(column=0, row=0, sticky=tk.W+tk.E)
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
                return
            if path.name != 'Orthophotos': # Normalize
                path = path.rename(path.parent / 'Orthophotos')
            self.orthophotos_var.set(path)

    def change_image_service(self, *args, **kwargs):
        self.image_service_description_var.set(IMAGE_SERVICES[self.image_service_var.get()].description)
        self.image_service_license_var.set(_('Image service license at {link}').format(
            link=IMAGE_SERVICES[self.image_service_var.get()].license_link,
        ))

    def cancel(self):
        self.settings.reload()
        self.window.destroy()

    def apply(self):
        self.settings.fgdata_folder = self.fg_path_var.get()
        self.settings.orthophotos_folder = self.orthophotos_var.get()
        self.settings.host = self.host_var.get()
        try:
            self.settings.port = int(self.port_var.get())
        except tk.TclError:
            tk.messagebox.showerror(
                    title=_('Invalid value'),
                    message=_('Invalid value in port configuration. Please inform an integer value.'),
            )
            return
        try:
            self.settings.following_interval = int(self.interval_var.get())*1000
        except tk.TclError:
            tk.messagebox.showerror(
                    title=_('Invalid value'),
                    message=_('Invalid value in following interval configuration. Please inform an integer value.'),
            )
            return
        self.settings.image_service = self.image_service_var.get()
        try:
            self.settings.radius = int(self.radius_var.get())
        except tk.TclError:
            tk.messagebox.showerror(
                    title=_('Invalid value'),
                    message=_('Invalid value in download radius configuration. Please inform an integer value.'),
            )
            return
        try:
            self.settings.tile_threads = int(self.tiles_var.get())
        except tk.TclError:
            tk.messagebox.showerror(
                    title=_('Invalid value'),
                    message=_('Invalid value in maximum simultaneous tiles configuration. Please inform an integer value.'),
            )
            return
        try:
            self.settings.image_threads = int(self.threads_var.get())
        except tk.TclError:
            tk.messagebox.showerror(
                    title=_('Invalid value'),
                    message=_('Invalid value in maximum simultaneous downloads for each tile configuration. Please inform an integer value.'),
            )
            return
        self.settings.download_res = self.unformat_size(self.resolution_var.get())
        self.settings.image_format = COMPRESSION[self.image_format_var.get()]
        distances = {}
        max_distance = 0
        try:
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
        except tk.TclError:
            tk.messagebox.showerror(
                    title=_('Invalid value'),
                    message=_('Invalid distance value in image resolution configuration ({r}). Please inform an integer value.')\
                        .format(r=_('{res} m/px').format(
                            res=format_decimal(Decimal(RESOLUTIONS[d.resolution]).quantize(Decimal('1.00')), locale=LOCALE)),
                        )
            )
            return
        try:
            self.settings.renewal_age = int(self.renewal_age_var.get())
        except tk.TclError:
            tk.messagebox.showerror(
                    title=_('Invalid value'),
                    message=_('Invalid value in tile renewal age configuration. Please inform an integer value.'),
            )
            return
        try:
            self.settings.deletion_age = int(self.deletion_age_var.get())
        except tk.TclError:
            tk.messagebox.showerror(
                title=_('Invalid value'),
                message=_('Invalid value in tile deletion age configuration. Please inform an integer value.')
            )
        try:
            self.settings.max_disk_usage = int(self.disk_space_limit_var.get() * 1024 ** 2)
        except tk.TclError:
            tk.messagebox.showerror(
                title=_('Invalid value'),
                message=_('Invalid value in disk usage limit configuration. Please inform an integer value.')
            )
        self.settings.auto_clean = self.auto_clean_var.get()
        try:
            self.settings.detail_degree = int(self.detail_degree_var.get())
        except tk.TclError:
            tk.messagebox.showerror(
                title=_('Invalid value'),
                message=_('Invalid value in degree tile visualization configuration. Please inform an integer value.')
            )
        try:
            self.settings.detail_tile = int(self.detail_tile_var.get())
        except tk.TclError:
            tk.messagebox.showerror(
                title=_('Invalid value'),
                message=_('Invalid value in scenery tile visualization configuration. Please inform an integer value.')
            )
    
    def apply_and_close(self):
        self.apply()
        self.settings.save()
        self.window.destroy()
