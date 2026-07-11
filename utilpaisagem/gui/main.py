import tkinter as tk
from tkinter import ttk
from idlelib.tooltip import Hovertip
from pathlib import Path
from queue import Queue
from flightgear_python.fg_if import TelnetConnection
from flightgear_python.fg_util import FGConnectionError, FGCommunicationError
from utilpaisagem.scenery.download_manager import DownloadManager
from utilpaisagem.gui.agents import Follower, UpstreamReader, Downloader
from utilpaisagem.gui.common import format_status, Settings

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
    follow_button:ttk.Button

    # Status bar
    status_frame:ttk.Frame

    def __init__(self, resources_path:Path):
        # Prepare queue for processing status communication
        self.upstream_queue = Queue()
        self.tasks = {}

        # Create GUI
        self.resources_path = resources_path
        self.window = tk.Tk()
        self.window.title('Útil paisagem')
        self.window.columnconfigure(0, weight=10)
        self.window.rowconfigure(0, weight=10)
        self.toolbar_frame = ttk.Frame(self.window)
        self.toolbar_frame.grid(column=1, row=0, sticky=tk.N)
        self.follow_button = ttk.Button(self.toolbar_frame, text=_('Follow aircraft'), command=self.follow)
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
        self.status_bar = ttk.Label(self.window, textvariable=self.status_var)
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

    # TODO: set preferences here and at agents.py
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