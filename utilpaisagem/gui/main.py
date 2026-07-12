import tkinter as tk
from tkinter import ttk
from idlelib.tooltip import Hovertip
from pathlib import Path
from queue import Queue
from flightgear_python.fg_if import TelnetConnection
from flightgear_python.fg_util import FGConnectionError, FGCommunicationError
from utilpaisagem.scenery.download_manager import DownloadManager
from utilpaisagem.scenery.tile import Tile
from utilpaisagem.gui.agents import Follower, UpstreamReader, Downloader
from utilpaisagem.gui.common import format_status, Settings, PADDING
from babel.numbers import format_decimal, format_number, parse_decimal, parse_number, NumberFormatError

class MainWindow(object):
    """
    Main window. The window itself (`tkinter.Tk`) is under `MainWindow.window`.
    """
    # Útil paisagem things
    download_manager:DownloadManager
    connection:TelnetConnection
    downloader:Downloader
    settings:Settings

    # Threading things
    upstream_queue:Queue # Processing status
    upstream_reader:UpstreamReader
    following_queue:Queue # Talk with aircraft following thread
    follower:Follower

    # GUI things
    resources_path:Path
    window:tk.Tk
    status_var:tk.StringVar

    # Toolbar
    toolbar_frame:ttk.Frame
    coordinates_frame:ttk.Frame
    index:int
    index_var:tk.StringVar
    index_label:ttk.Label
    index_input:ttk.Entry
    lat:float
    lat_var:tk.StringVar
    lat_label:ttk.Label
    lat_input:tk.text(self.coordinates_frame)
    lon:float
    lon_var:tk.StringVar
    lon_label:ttk.Label
    lon_input:tk.text(self.coordinates_frame)
    download_tile_button:tk.Button
    download_region_button:tk.Button
    follow_button:ttk.Button

    # Status bar
    status_var:tk.StringVar
    status_bar:ttk.Label

    def __init__(self, resources_path:Path):
        # Prepare queue for processing status communication
        self.upstream_queue = Queue()
        self.tasks = {}

        # Create GUI
        self.resources_path = resources_path
        self.window = tk.Tk()
        self.window.title('Útil paisagem')
        self.window.columnconfigure(0, weight=10, pad=PADDING)
        self.window.columnconfigure(1, pad=PADDING)
        self.window.rowconfigure(0, weight=10)
        self.window.rowconfigure(1, pad=PADDING)

        # Toolbar
        self.toolbar_frame = ttk.Frame(self.window)
        self.toolbar_frame.grid(column=1, row=0, sticky=tk.N)
        # Coordinates
        self.coordinates_frame = ttk.Frame(self.toolbar_frame, padding=PADDING)
        self.coordinates_frame.pack(fill=tk.X)
        self.index_var = tk.StringVar(self.coordinates_frame)
        self.index = Tile.coordinates_to_index(lat=0, lon=0)
        self.index_label = ttk.Label(self.coordinates_frame, text=_('Tile index:'))
        self.index_input = ttk.Entry(
            self.coordinates_frame,
            textvariable=self.index_var,
            justify=tk.LEFT,
        )
        self.lat_var = tk.StringVar(self.coordinates_frame, value=format_decimal(0.0))
        self.lat = 0.0
        self.lat_label = ttk.Label(self.coordinates_frame, text=_('Latitude:'))
        self.lat_input = ttk.Entry(
            self.coordinates_frame,
            textvariable=self.lat_var,
            justify=tk.LEFT,
            name='lat'
        )
        self.lon_var = tk.StringVar(self.coordinates_frame, value=format_decimal(0.0))
        self.lon = 0.0
        self.lon_label = ttk.Label(self.coordinates_frame, text=_('Longitude:'))
        self.lon_input = ttk.Entry(
            self.coordinates_frame,
            textvariable=self.lon_var,
            justify=tk.LEFT,
        )
        self.download_tile_button = ttk.Button(
            self.coordinates_frame,
            text=_('Download tile'),
            command=self.download_tile,
        )
        self.download_region_button = ttk.Button(
            self.coordinates_frame,
            text=_('Download region'),
            command=self.download_region,
        )
        self.coordinates_frame.columnconfigure(1, weight=1)
        self.index_label.grid(column=0, row=0, sticky=tk.E)
        self.index_input.grid(column=1, row=0)
        self.lat_label.grid(column=0, row=1, sticky=tk.E)
        self.lat_input.grid(column=1, row=1)
        self.lon_label.grid(column=0, row=2, sticky=tk.E)
        self.lon_input.grid(column=1, row=2)
        self.download_tile_button.grid(column=0, row=3, columnspan=2, sticky=tk.W+tk.E)
        self.download_region_button.grid(column=0, row=4, columnspan=2, sticky=tk.W+tk.E)
        self.index_var.set(Tile.coordinates_to_index(lat=0, lon=0))
        self.index_input.bind('<FocusOut>', lambda *args, **kwargs: self.int_input_focus_out('index', *args, **kwargs))
        self.lat_input.bind('<FocusOut>', lambda *args, **kwargs: self.float_input_focus_out('lat', *args, **kwargs))
        self.lon_input.bind('<FocusOut>', lambda *args, **kwargs: self.float_input_focus_out('lon', *args, **kwargs))

        # Following
        self.follow_frame = ttk.Frame(self.toolbar_frame, padding=PADDING)
        self.follow_frame.pack(fill=tk.X)
        self.follow_button = ttk.Button(
            self.follow_frame,
            text=_('Follow aircraft'),
            command=self.follow,
        )
        self.follow_button.pack(fill=tk.X)
        self.follow_button_tip = Hovertip(
            self.follow_button,
            text=_('Follow aircraft on Flightgear over telnet connection.')
        )

        # Map
        self.map_label = ttk.Label(text='Reserved for map')
        self.map_label.grid(column=0, row=0)

        # Status bar
        self.status_var = tk.StringVar(self.window, _('Welcome to Útil paisagem'))
        self.status_bar = ttk.Label(self.window, textvariable=self.status_var, justify=tk.LEFT)
        self.status_bar.grid(column=0, row=1, columnspan=2, sticky=tk.W)

        # Settings
        self.settings = Settings()

        # Útil paisagem things
        self.download_manager = DownloadManager(
            center_lat=0,
            center_lon=0,
            radius=self.settings.radius,
            resolutions=self.settings.distances,
            upstream_queue=self.upstream_queue,
            )
        self.download_manager.clear()

        # Init upstream reader
        self.upstream_reader = UpstreamReader(self.window, self.status_var, self.upstream_queue, 100)
        self.upstream_reader.read()

        # Init downloader
        self.downloader = Downloader(self.window, self.upstream_queue, self.download_manager, 100)
        self.downloader.download()

    # Validation
    def validate_float(self, input:str):
        """
        Validates a floating point number and returns it as a float.
        Raises error if not possible both using float() and using babel.numbers.parse_decimal().

        Arguments:
            input(str): text to validate and convert
        """
        try:
            return float(input)
        except ValueError:
            return float(parse_decimal(input))

    def validate_int(self, input:str):
        """
        Validates an integer number and returns it as an integer.
        Raises error if not possible both using int() and using babel.numbers.parse_number().

        Arguments:
            input(str): text to validate and convert
        """
        try:
            return int(input)
        except ValueError:
            return parse_number(input)

    def float_input_focus_out(self, what:str, event:tk.Event):
        what_var = {
            'lat': self.lat_var,
            'lon': self.lon_var,
        }
        try:
            value = self.validate_float(what_var[what].get())
            if what == 'lat' and not (-90 <= value <= 90):
                what_var[what].set(str(self.lat))
                return
            elif what == 'lon' and not (-180 <= value <= 180):
                what_var[what].set(str(self.lon))
                return
            self.__dict__[what] = value
        except NumberFormatError:
            what_var[what].set(str(self.__dict__[what]))
            return
        if what in ['lat', 'lon']:
            self.index_var.set(str(Tile.coordinates_to_index(lat=self.lat, lon=self.lon)))
        
    def int_input_focus_out(self, what:str, event:tk.Event):
        what_var = {
            'index': self.index_var,
        }
        try:
            value = self.validate_int(what_var[what].get())
            self.__dict__[what] = value
        except NumberFormatError:
            what_var[what].set(str(self.__dict__[what]))
            return
        if what == 'index':
            coordinates = Tile.index_to_coordinates(self.index)
            self.lat = coordinates.lat_median
            self.lon = coordinates.lon_median
            self.lat_var.set(str(self.lat))
            self.lon_var.set(str(self.lon))

    # Actions
    # TODO: set preferences here and at agents.py

    # Download based on latitude and longitude
    def download_tile(self):
        self.downloader.add_tile(self.index)
    
    def download_region(self):
        self.download_manager.recenter(lat=self.lat, lon=self.lon)

    # Aircraft following
    def follow(self):
        """Starts aircraft following thread."""
        if not hasattr(self, 'following_queue') or self.following_queue.is_shutdown:
            self.following_queue = Queue()
        try:
            self.follower = Follower(
                root=self.window,
                upstream_queue=self.upstream_queue,
                downstream_queue=self.following_queue,
                download_manager=self.download_manager,
                # host=host,
                # port=port,
                # interval=interval,
            )
        except FGConnectionError:
            return
        self.follower.follow()