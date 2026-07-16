import tkinter as tk
from tkinter import ttk
from idlelib.tooltip import Hovertip
from pathlib import Path
from queue import Queue
from LatLon23 import LatLon
from flightgear_python.fg_if import TelnetConnection
from flightgear_python.fg_util import FGConnectionError, FGCommunicationError
from babel.numbers import format_decimal, format_number, parse_decimal, parse_number, NumberFormatError
from tkintermapview import TkinterMapView
from tkintermapview.canvas_polygon import CanvasPolygon
from tkintermapview.canvas_path  import CanvasPath
from tkintermapview.canvas_position_marker import CanvasPositionMarker
from utilpaisagem.scenery.download_manager import DownloadManager
from utilpaisagem.scenery.tile import Tile
from utilpaisagem.gui.agents import Follower, UpstreamReader, Downloader
from utilpaisagem.gui.common import format_status, Settings, PADDING

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

    # Map
    search_frame:ttk.Frame
    search_var:tk.StringVar
    search_label:ttk.Label
    search_input:ttk.Entry
    search_button:ttk.Button
    map_frame:ttk.Frame
    map_widget:kinterMapView
    tile_polygon:CanvasPolygon
    waypoints:list[CanvasPositionMarker]
    marker:CanvasPositionMarker
    route:CanvasPath

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
    add_waypoint_button:tk.Button
    waypoints_var:tk.Variable
    waypoints_frame:ttk.Frame
    waypoints_label:ttk.Label
    waypoints_list:tk.Listbox
    waypoints_remove_button:tk.Button
    waypoints_up_button:tk.Button
    waypoints_down_button:tk.Button
    download_route_button:tk.Button
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
        # Map
        self.marker = None
        self.waypoints = []
        self.route = None
        self.map_frame = ttk.Frame(self.window)
        self.map_frame.grid(column=0,row=0, sticky=tk.N+tk.E+tk.S+tk.W)
        self.map_frame.columnconfigure(0, weight=10)
        self.map_frame.rowconfigure(1, weight=10)
        self.search_frame = ttk.Frame(self.map_frame, padding=PADDING)
        self.search_frame.columnconfigure(0, pad=PADDING)
        self.search_frame.columnconfigure(1, weight=10)
        self.search_frame.columnconfigure(2, pad=PADDING)
        self.search_var = tk.StringVar(self.search_frame)
        self.search_label = ttk.Label(self.search_frame, text=_('Address or ICAO code:'))
        # TODO search on enter
        self.search_input = ttk.Entry(self.search_frame, textvariable=self.search_var)
        self.search_button = ttk.Button(self.search_frame, text=_('Search'), command=self.search)
        self.search_label.grid(column=0, row=0)
        self.search_input.grid(column=1, row=0, sticky=tk.W+tk.E)
        self.search_button.grid(column=2, row=0)
        # TODO resize map properly, store window size and map coordinates
        self.map_widget = TkinterMapView(self.map_frame, width=800, height=600)
        self.map_widget.set_position(0, 0)
        self.map_widget.set_zoom(0)
        self.search_frame.grid(column=0, row=0, sticky=tk.W+tk.E)
        self.map_widget.grid(column=0, row=1, sticky=tk.N+tk.E+tk.S+tk.W)
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
        self.add_waypoint_button=ttk.Button(
            self.coordinates_frame,
            text=_('Add waypoint'),
            command=self.waypoint_button_press
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
        self.add_waypoint_button.grid(column=0, row=5, columnspan=2, sticky=tk.W+tk.E)
        self.index_var.set(Tile.coordinates_to_index(lat=0, lon=0))
        self.index_input.bind('<FocusOut>', lambda *args, **kwargs: self.int_input_focus_out('index', *args, **kwargs))
        self.lat_input.bind('<FocusOut>', lambda *args, **kwargs: self.float_input_focus_out('lat', *args, **kwargs))
        self.lon_input.bind('<FocusOut>', lambda *args, **kwargs: self.float_input_focus_out('lon', *args, **kwargs))
        # Waypoints list
        self.waypoints_var = tk.Variable(value=self.waypoints)
        self.waypoints_frame = ttk.Frame(self.toolbar_frame)
        self.waypoints_label = ttk.Label(self.waypoints_frame, text=_('Waypoints:'))
        self.waypoints_list = tk.Listbox(
            self.waypoints_frame,
            listvariable=self.waypoints_var,
            # TODO (moves wrongly) selectmode=tk.MULTIPLE,
        )
        self.waypoints_remove_button = tk.Button(
            self.waypoints_frame,
            text=_('Remove Waypoint'),
            command=self.remove_waypoint,
        )
        self.waypoints_up_button = tk.Button(
            self.waypoints_frame,
            text=_('Up'),
            command=lambda: self.move_waypoint(-1),
        )
        self.waypoints_down_button = tk.Button(
            self.waypoints_frame,
            text=_('Down'),
            command=lambda: self.move_waypoint(1),
        )
        self.download_route_button = tk.Button(
            self.waypoints_frame,
            text=_('Download route'),
            command=self.download_route,
        )
        self.waypoints_frame.columnconfigure(0, weight=1)
        self.waypoints_frame.columnconfigure(1, weight=1)
        self.waypoints_frame.columnconfigure(2, weight=1)
        self.waypoints_label.grid(column=0, row=0, columnspan=3)
        self.waypoints_list.grid(column=0, row=1, columnspan=3, sticky=tk.W+tk.E)
        self.waypoints_remove_button.grid(column=0, row=2, sticky=tk.W + tk.E)
        self.waypoints_up_button.grid(column=1, row=2)
        self.waypoints_down_button.grid(column=2, row=2)
        self.download_route_button.grid(column=0, row=3, columnspan=3, sticky=tk.W+tk.E)
        self.waypoints_frame.pack(fill=tk.X)
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

        # Init downloader
        self.downloader = Downloader(self.window, self.upstream_queue, self.download_manager, 100)
        self.downloader.download()

        # Init upstream reader
        self.upstream_reader = UpstreamReader(
            self.window,
            self.status_var,
            self.upstream_queue,
            self.downloader,
            interval=100)
        self.upstream_reader.read()

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
            self.index = Tile.coordinates_to_index(lat=self.lat, lon=self.lon)
            self.index_var.set(str(self.index))
            self.create_tile_polygon(self.index)
            self.place_marker(lat=self.lat, lon=self.lon)
        
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
            self.create_tile_polygon(self.index)

    def create_tile_polygon(self, index:int):
        """
        Creates a tile polygon from index and stores it at MainWindow.tile_polygon.

        Arguments:
            index(int): a tile index
        """
        if hasattr(self, 'tile_polygon'):
            self.tile_polygon.delete()
        coordinates = Tile.index_to_coordinates(self.index)
        self.tile_polygon = self.map_widget.set_polygon(
            [
                (coordinates.lat_top, coordinates.lon_left),
                (coordinates.lat_top, coordinates.lon_right),
                (coordinates.lat_bottom, coordinates.lon_right),
                (coordinates.lat_bottom, coordinates.lon_left)
            ],
            fill_color=None,
        )
        self.map_widget.fit_bounding_box(
            (coordinates.lat_top, coordinates.lon_left),
            (coordinates.lat_bottom, coordinates.lon_right),
        )

    def create_route(self):
        if hasattr(self.route, 'delete'):
            self.route.delete()
        if len(self.waypoints) > 1:
            self.route = self.map_widget.set_path(
                [wp.position for wp in self.waypoints]
            )

    def place_marker(self, marker:CanvasPositionMarker=None, lat:float=None, lon:float=None, text:str=''):
        if hasattr(self.marker, 'delete'):
            if self.marker not in self.waypoints:
                self.marker.delete()
        if marker:
            self.marker = marker
            return
        if not text:
            text = f'{lat:.02f}, {lon:.02f}'
        self.marker = self.map_widget.set_marker(lat, lon, text=text)

    def waypoint_button_press(self):
        if not isinstance(self.marker, CanvasPositionMarker):
            self.place_marker(lat=self.lat, lon=self.lon)
        self.add_waypoint(self.marker)

    def waypoints_to_var(self):
        self.waypoints_var.set([f'{n}: {self.waypoints[n].text}' for n in range(len(self.waypoints))])

    def add_waypoint(self, marker:CanvasPositionMarker):
        self.waypoints.append(marker)
        self.waypoints_to_var()
        self.create_route()

    def move_waypoint(self, amount:int):
        selected = self.waypoints_list.selection_get().split('\n')
        indexes = []
        for i in selected:
            indexes.append(self.waypoints_var.get().index(i))
        for i in indexes:
            waypoint = self.waypoints.pop(i)
            if i + amount < 0:
                insertion = len(self.waypoints) + amount + 1
            else:
                insertion = i + amount
            self.waypoints.insert(insertion, waypoint)
        self.waypoints_to_var()
        self.create_route()
        self.waypoints_list.selection_clear(0, len(self.waypoints)-1)
        for i in indexes:
            if i - amount < 0:
                self.waypoints_list.selection_set(i + amount + len(self.waypoints))
            else:
                self.waypoints_list.selection_set(i + amount)

    def remove_waypoint(self):
        selected = self.waypoints_list.selection_get().split('\n')
        for waypoint in selected:
            marker = self.waypoints.pop(self.waypoints_var.get().index(waypoint))
            marker.delete()
        self.waypoints_to_var()
        self.create_route()

    def search(self):
        error = self.map_widget.set_address(self.search_var.get(), text=self.search_var.get())
        if error is None:
            self.place_marker(self.map_widget.set_address(self.search_var.get(), marker=True, text=self.search_var.get()))
            self.lat = self.marker.position[0]
            self.lon = self.marker.position[1]
            self.lat_var.set(str(self.lat))
            self.lon_var.set(str(self.lon))
            self.index = Tile.coordinates_to_index(self.lat, self.lon)
            self.index_var.set(str(self.index))
            self.create_tile_polygon(self.index)
            self.upstream_queue.put_nowait(format_status(
                _('"{address}" found at {lat},{lon}.').format(
                    address=self.search_var.get(),
                    lat=self.lat,
                    lon=self.lon
                ),
                self
            ))
        else:
            self.upstream_queue.put_nowait(format_status(
                _('Could not find address {address}.').format(address=self.search_var.get()),
                self
            ))

    # Actions
    # TODO: set preferences here and at agents.py

    # Download based on latitude and longitude
    def download_tile(self):
        self.downloader.add_tile(self.index)
    
    def download_region(self):
        self.download_manager.recenter(lat=self.lat, lon=self.lon)

    def download_route(self):
        distances = list(self.settings.distances.keys())
        distances.sort()
        step = distances[0]
        route = self.waypoints.copy()
        route.reverse() # DownloadManager puts last center first
        for i, wp in enumerate(route[:-1]):
            coord1 = LatLon(*wp.position)
            coord2 = LatLon(*route[i+1].position)
            stops = int(coord1.distance(coord2) // step)
            heading = coord1.heading_initial(coord2)
            for s in range(stops):
                mid_coord = coord1.offset(heading, s*step)
                self.download_manager.recenter(
                    float(mid_coord.lat),
                    float(mid_coord.lon),
                )
            self.download_manager.recenter(
                float(coord2.lat),
                float(coord2.lon),
            )

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
                self.following_queue.shutdown(immediate=True)
                return
            self.follow_button['text'] = _('Stop following')
            self.follow_button_tip.text = _('Stop following aircraft on FlightGear')
            self.follower.follow()
        else: # Stop following
            self.following_queue.shutdown(immediate=True)
            self.follow_button['text'] = _('Follow aircraft')
            self.follow_button_tip.text = _('Follow aircraft on Flightgear over telnet connection.')