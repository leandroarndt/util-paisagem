import webbrowser
import tkinter as tk
import pyperclip
from tkinter import ttk
from idlelib.tooltip import Hovertip
from pathlib import Path
from queue import Queue
from LatLon23 import LatLon
from flightgear_python.fg_if import TelnetConnection
from flightgear_python.fg_util import FGConnectionError, FGCommunicationError
from babel.numbers import format_decimal, format_number, parse_decimal, parse_number, NumberFormatError
from PIL import Image, ImageTk
from tkintermapview import TkinterMapView
from tkintermapview.canvas_polygon import CanvasPolygon
from tkintermapview.canvas_path  import CanvasPath
from tkintermapview.canvas_position_marker import CanvasPositionMarker
from showinfm import show_in_file_manager
from utilpaisagem.app_info import VERSION, SUBVERSION, REVISION, RC, resources_path
from utilpaisagem.scenery.download_manager import DownloadManager
from utilpaisagem.scenery.tile import Tile
from utilpaisagem.gui.agents import Follower, UpstreamReader, Downloader
from utilpaisagem.gui.common import format_status, Settings, PADDING, LOCALE
from utilpaisagem.gui.settings import SettingsWindow

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
    contents:ttk.Frame
    status_var:tk.StringVar
    menu:tk.Menu
    file_menu:tk.Menu
    edit_menu:tk.Menu
    help_menu:tk.Menu

    # Map
    search_frame:ttk.Frame
    search_var:tk.StringVar
    search_label:ttk.Label
    search_input:ttk.Entry
    search_button:ttk.Button
    map_frame:ttk.Frame
    map_widget:TkinterMapView
    tile_polygon:CanvasPolygon
    waypoints:list[CanvasPositionMarker]
    marker:CanvasPositionMarker
    route:CanvasPath
    active_aircraft_icon:ImageTk
    greyed_aircraft_icon:ImageTk

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
    lat_input:tk.Text
    lon:float
    lon_var:tk.StringVar
    lon_label:ttk.Label
    lon_input:tk.Text
    download_tile_button:tk.Button
    download_region_button:tk.Button
    add_waypoint_button:tk.Button
    current_waypoint:int # index in self.waypoints
    waypoints_var:tk.Variable
    waypoints_frame:ttk.Frame
    waypoints_label:ttk.Label
    waypoints_list:tk.Listbox
    waypoint_name_var:tk.StringVar
    waypoint_name_entry:ttk.Entry
    waypoint_rename_button:ttk.Button
    waypoints_remove_button:tk.Button
    waypoints_up_button:tk.Button
    waypoints_down_button:tk.Button
    download_route_button:tk.Button
    follow_button:ttk.Button
    follow_button_tip:Hovertip
    center_on_aircraft_button:ttk.Button
    center_on_aircraft_tip:Hovertip
    others_frame:ttk.Frame
    settings_button:ttk.Button

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
        self.window.title(
            f'Útil paisagem {VERSION}.{SUBVERSION}.{REVISION}{"rc" + str(RC) if RC else ""}'
        )

        # Menu
        self.menu = tk.Menu(self.window)
        self.file_menu = tk.Menu(self.menu)
        self.file_menu.add_command(
            label=_('Show orthophotos folder'),
            command=lambda: show_in_file_manager(str(self.settings.orthophotos_folder)),
        )
        self.file_menu.add_command(
            label=_('Show tile image'),
            command=self.show_tile_image,
        )
        self.file_menu.add_command(
            label=_('Delete tile'),
            command=self.delete_tile,
        )
        self.file_menu.add_separator()
        self.file_menu.add_command(
            label=_('Quit'),
            command=lambda: self.window.destroy(),
        )
        self.edit_menu = tk.Menu(self.menu)
        self.edit_menu.add_command(
            label=_('Copy coordinates'),
            command=lambda: pyperclip.copy(f'{self.lat}, {self.lon}'),
        )
        self.edit_menu.add_command(
            label=_('Copy tile index'),
            command=lambda: pyperclip.copy(str(self.index)),
        )
        self.edit_menu.add_separator()
        self.edit_menu.add_command(
            label=_('Settings'),
            command=lambda: SettingsWindow(self.window, main_window=self),
        )
        self.help_menu = tk.Menu(self.menu)
        self.help_menu.add_command(
            label=_('Online manual'),
            command=lambda: webbrowser.open('https://github.com/leandroarndt/util-paisagem/wiki')
        )
        self.help_menu.add_command(
            label=_('Latest release'),
            command=lambda: webbrowser.open('https://github.com/leandroarndt/util-paisagem/releases/latest'),
        )
        self.help_menu.add_command(
            label=_('Found a bug?'),
            command=lambda: webbrowser.open('https://github.com/leandroarndt/util-paisagem/issues'),
        )
        self.help_menu.add_command(
            label=_('Contribute'),
            command=lambda: webbrowser.open('https://github.com/leandroarndt/util-paisagem'),
        )
        self.help_menu.add_command(
            label=_('Donate'),
            command=lambda: webbrowser.open('https://buymeacoffee.com/leandro.a')
        )
        self.menu.add_cascade(
            label=_('File'),
            menu=self.file_menu,
        )
        self.menu.add_cascade(
            label=_('Edit'),
            menu=self.edit_menu,
        )
        self.menu.add_cascade(
            label=_('Help'),
            menu=self.help_menu,
        )
        self.window.configure(menu=self.menu)
        # Grid
        self.window.columnconfigure(0, weight=10, pad=PADDING)
        self.window.columnconfigure(1, weight=0, pad=PADDING)
        self.window.rowconfigure(0, weight=10)
        self.window.rowconfigure(1, weight=0, pad=PADDING)
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
        self.search_input = ttk.Entry(self.search_frame, textvariable=self.search_var)
        self.search_input.bind('<Return>', self.search)
        self.search_input.bind('<Control-Return>', self.search_waypoint)
        self.search_button = ttk.Button(self.search_frame, text=_('Search'), command=self.search)
        self.search_label.grid(column=0, row=0)
        self.search_input.grid(column=1, row=0, sticky=tk.W+tk.E)
        self.search_button.grid(column=2, row=0)
        # TODO resize map properly, store window size and map coordinates
        self.map_widget = TkinterMapView(self.map_frame, width=800, height=600)
        self.map_widget.set_position(0, 0)
        self.map_widget.set_zoom(0)
        self.map_widget.add_right_click_menu_command(
            label=_('Select tile'),
            command=self.right_click_select_tile,
            pass_coords=True,
        )
        self.map_widget.add_right_click_menu_command(
            label=_('Add waypoint'),
            command=self.right_click_add_waypoint,
            pass_coords=True,
        )
        self.search_frame.grid(column=0, row=0, sticky=tk.W+tk.E)
        self.map_widget.grid(column=0, row=1, sticky=tk.N+tk.E+tk.S+tk.W)
        self.active_aircraft_icon = ImageTk.PhotoImage(Image.open(resources_path / 'images' / 'aircraft.png'))
        self.greyed_aircraft_icon = ImageTk.PhotoImage(Image.open(resources_path / 'images' / 'greyed aircraft.png'))
        self.aircraft = None
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
        self.lat_var = tk.StringVar(self.coordinates_frame, value=format_decimal(0.0, locale=LOCALE))
        self.lat = 0.0
        self.lat_label = ttk.Label(self.coordinates_frame, text=_('Latitude:'))
        self.lat_input = ttk.Entry(
            self.coordinates_frame,
            textvariable=self.lat_var,
            justify=tk.LEFT,
            name='lat'
        )
        self.lon_var = tk.StringVar(self.coordinates_frame, value=format_decimal(0.0, locale=LOCALE))
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
        self.current_waypoint = -1
        self.waypoints_var = tk.Variable(value=self.waypoints)
        self.waypoints_frame = ttk.Frame(self.toolbar_frame, padding=PADDING)
        self.waypoints_label = ttk.Label(self.waypoints_frame, text=_('Waypoints:'))
        self.waypoints_list = tk.Listbox(
            self.waypoints_frame,
            listvariable=self.waypoints_var,
            # TODO (moves wrongly) selectmode=tk.MULTIPLE,
        )
        self.waypoints_list.bind('<<ListboxSelect>>', self.select_waypoint)
        self.waypoint_name_var = tk.StringVar(self.waypoints_frame)
        self.waypoint_name_entry = ttk.Entry(self.waypoints_frame, textvariable=self.waypoint_name_var)
        self.waypoint_rename_button = ttk.Button(
            self.waypoints_frame,
            text=_('Rename'),
            command=self.rename_waypoint,
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
        self.waypoint_name_entry.grid(column=0, row=2, sticky=tk.W+tk.E)
        self.waypoint_rename_button.grid(column=1, row=2, columnspan=2, sticky=tk.W+tk.E)
        self.waypoints_remove_button.grid(column=0, row=3, sticky=tk.W + tk.E)
        self.waypoints_up_button.grid(column=1, row=3)
        self.waypoints_down_button.grid(column=2, row=3)
        self.download_route_button.grid(column=0, row=4, columnspan=3, sticky=tk.W+tk.E)
        self.waypoints_frame.pack(fill=tk.X)
        # Following
        self.follow_frame = ttk.Frame(self.toolbar_frame, padding=PADDING)
        self.follow_frame.pack(fill=tk.X)
        self.follow_frame.columnconfigure(0, weight=10)
        self.follow_button = ttk.Button(
            self.follow_frame,
            text=_('Follow aircraft'),
            command=self.follow,
        )
        self.follow_button_tip = Hovertip(
            self.follow_button,
            text=_('Follow aircraft on Flightgear over telnet connection.')
        )
        self.center_on_aircraft_button = ttk.Button(
            self.follow_frame,
            text=_('Center on aircraft'),
            command=self.center_on_aircraft,
        )
        self.center_on_aircraft_tip = Hovertip(
            self.center_on_aircraft_button,
            text=_('Center map on aircraft and show the corresponding scenery tile.')
        )
        self.follow_button.grid(column=0, row=0, sticky=tk.W+tk.E)
        self.center_on_aircraft_button.grid(column=0, row=1, sticky=tk.W+tk.E)
        # Settings, about etc.
        self.others_frame = ttk.Frame(self.toolbar_frame, padding=PADDING)
        self.others_frame.columnconfigure(0, weight=1)
        self.others_frame.pack(fill=tk.X)
        self.settings_button = ttk.Button(
            self.others_frame,
            text=_('Settings'),
            command=lambda: SettingsWindow(self.window, main_window=self),
        )
        self.settings_button.grid(column=0, row=0, sticky=tk.W+tk.E)

        # Status bar
        self.status_var = tk.StringVar(self.window, _('Welcome to Útil paisagem'))
        self.status_bar = ttk.Label(self.window, textvariable=self.status_var, justify=tk.LEFT)
        self.status_bar.grid(column=0, row=1, columnspan=2, sticky=tk.W)

        # Size
        self.window.update()
        self.window.minsize(self.window.winfo_width(), self.window.winfo_height()+32) # Account for menu bar
        # Settings
        self.settings = Settings()

        # Útil paisagem things
        self.download_manager = DownloadManager(
            center_lat=0,
            center_lon=0,
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

    # Menu commands

    def show_tile_image(self):
        dds = Tile(self.index).get_path(self.settings.orthophotos_folder) / f'{self.index}.dds'
        png = Tile(self.index).get_path(self.settings.orthophotos_folder) / f'{self.index}.png'
        if dds.exists():
            show_in_file_manager(str(dds))
        elif png.exists():
            show_in_file_manager(str(png))
        else:
            tk.messagebox.showerror(
                title=_('Image not found'),
                message=_('No image found for tile {index}.').format(index=self.index)
            )

    def delete_tile(self):
        answer = tk.messagebox.askyesno(
            title=_('Delete tile?'),
            message=_('Are you sure you want to delete tile {index}?').format(index=self.index)
        )
        if answer:
            Tile(self.index).delete_files()

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
            return float(parse_decimal(input, locale=LOCALE))

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
            return parse_number(input, locale=LOCALE)
        
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
            self.select_tile(mark=True, set_index=True)
    
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
            self.select_tile(mark=False, set_index=False)

    # Map and route operations

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

    def select_tile(self, mark:bool=False, set_index=False):
        """Creates a polygon around a scenery tile. If `mark` is true, a map marker is created.
        If `set_index` is true, `self.index` is set according to `self.lat` and `self.lon`, otherwise
        `self.lat` and `self.lon` are set according to `self.index`."""
        if set_index:
            self.index = Tile.coordinates_to_index(lat=self.lat, lon=self.lon)
            self.index_var.set(str(self.index))
        else:
            coordinates = Tile.index_to_coordinates(self.index)
            self.lat = coordinates.lat_median
            self.lon = coordinates.lon_median
            self.lat_var.set(str(self.lat))
            self.lon_var.set(str(self.lon))
        self.create_tile_polygon(self.index)
        if mark:
            self.place_marker(lat=self.lat, lon=self.lon)
        else:
            if isinstance(self.marker, CanvasPositionMarker) and \
                self.marker not in self.waypoints and \
                self.marker.position != (self.lat, self.lon):
                self.marker.delete()

    def place_marker(self, marker:CanvasPositionMarker=None, lat:float=None, lon:float=None, text:str=''):
        if isinstance(self.marker, CanvasPositionMarker):
            if self.marker not in self.waypoints:
                self.marker.delete()
        if marker:
            self.marker = marker
            self.marker.command = self.select_marker
            return
        if not text:
            text = f'{lat:.02f}, {lon:.02f}'
        self.marker = self.map_widget.set_marker(lat, lon, text=text)
        self.marker.command = self.select_marker

    def create_route(self):
        if hasattr(self.route, 'delete'):
            self.route.delete()
        if len(self.waypoints) > 1:
            self.route = self.map_widget.set_path(
                [wp.position for wp in self.waypoints]
            )

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

    def rename_waypoint(self, *args, **kwargs):
        selected = self.waypoints_list.curselection()
        print(self.waypoint_name_var.get())
        self.waypoints[selected[0]].set_text(self.waypoint_name_var.get())
        self.waypoints_to_var()
        self.waypoints_list.select_set(self.current_waypoint)

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
        self.waypoints_list.selection_clear(0, 'end')
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

    def search(self, *args, **kwargs):
        error = self.map_widget.set_address(self.search_var.get(), text=self.search_var.get())
        if error is None:
            self.place_marker(self.map_widget.set_address(self.search_var.get(), marker=True, text=self.search_var.get()))
            self.lat, self.lon = self.marker.position
            self.lat_var.set(str(self.lat))
            self.lon_var.set(str(self.lon))
            self.select_tile(mark=False, set_index=True)
            self.upstream_queue.put_nowait(format_status(
                _('"{address}" found at {lat},{lon}.').format(
                    address=self.search_var.get(),
                    lat=self.lat,
                    lon=self.lon
                ),
                self
            ))
            return True
        else:
            self.upstream_queue.put_nowait(format_status(
                _('Could not find address {address}.').format(address=self.search_var.get()),
                self
            ))
            return False

    def search_waypoint(self, *args, **kwargs):
        if self.search():
            self.add_waypoint(self.marker)

    def right_click_select_tile(self, coords:tuple[float]):
        self.lat, self.lon = coords
        self.lat_var.set(str(coords[0]))
        self.lon_var.set(str(coords[1]))
        self.select_tile(mark=False, set_index=True)
    
    def right_click_add_waypoint(self, coords:tuple[float]):
        self.lat, self.lon = coords
        self.lat_var.set(str(coords[0]))
        self.lon_var.set(str(coords[1]))
        self.select_tile(mark=True, set_index=True)
        self.add_waypoint(self.marker)

    def select_waypoint(self, event):
        self.current_waypoint = self.waypoints_list.curselection()[0]
        self.waypoint_name_var.set(self.waypoints[self.current_waypoint].text)
        self.select_marker(self.waypoints[self.current_waypoint])

    def select_marker(self, marker:CanvasPositionMarker):
        self.lat, self.lon = marker.position
        self.lat_var.set(str(marker.position[0]))
        self.lon_var.set(str(marker.position[1]))
        self.waypoints_list.select_clear(0, 'end')
        self.current_waypoint = self.waypoints.index(marker)
        self.waypoints_list.select_set(self.current_waypoint)
        self.waypoint_name_var.set(marker.text)
        self.select_tile(mark=False, set_index=True)

    def place_aircraft(self, lat, lon, active=True):
        if isinstance(self.aircraft, CanvasPositionMarker):
            self.aircraft.delete()
        self.aircraft = self.map_widget.set_marker(lat, lon, icon=self.active_aircraft_icon if active else self.greyed_aircraft_icon)
    
    def center_on_aircraft(self):
        self.lat, self.lon = self.aircraft.position
        self.lat_var.set(str(self.lat))
        self.lon_var.set(str(self.lon))
        self.select_tile(mark=False, set_index=True)

    # Download based on latitude and longitude
    def download_tile(self):
        self.downloader.add_tile(
            self.index,
            resolution=sorted(self.settings.distances.values())[-1],
        )
    
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
                    main_window=self,
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
            if isinstance(self.aircraft, CanvasPositionMarker):
                self.aircraft.change_icon(self.greyed_aircraft_icon)