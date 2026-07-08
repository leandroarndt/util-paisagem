import tkinter as tk
from tkinter import ttk
from idlelib.tooltip import Hovertip
from pathlib import Path
from queue import Queue
from flightgear_python.fg_if import TelnetConnection
from flightgear_python.fg_util import FGConnectionError, FGCommunicationError
from utilpaisagem.scenery.download_manager import DownloadManager
from utilpaisagem.gui.agents import Follower, UpstreamReader, Downloader
from utilpaisagem.gui.common import format_log

class MainWindow(object):
    # Útil paisagem things
    download_manager:DownloadManager
    connection:TelnetConnection
    downloader:Downloader

    # Threading things
    upstream_queue:Queue # Processing status
    upstream_reader:UpstreamReader
    following_queue:Queue # Talk with aircraft following thread
    follower:Follower

    # GUI things
    resources_path:Path
    window:tk.Tk

    # Toolbar
    toolbar_frame:ttk.Frame
    follow_button:ttk.Button

    def __init__(self, resources_path:Path):
        # Prepare queue for processing status communication
        self.upstream_queue = Queue()
        self.tasks = {}

        # Útil paisagem things
        self.download_manager = DownloadManager(0,0, upstream_queue=self.upstream_queue)
        self.download_manager.clear()
        # self.connection = TelnetConnection('localhost', 5000)

        # Create GUI
        self.resources_path = resources_path
        self.window = tk.Tk()
        self.window.title('Útil paisagem')

        # Toolbar
        self.toolbar_frame = ttk.Frame(self.window)
        self.toolbar_frame.pack(fill=tk.BOTH, anchor=tk.NE)
        self.follow_button = ttk.Button(self.toolbar_frame, text=_('Follow aircraft'), command=self.follow)
        self.follow_button.pack(side=tk.LEFT)
        self.follow_button_tip = Hovertip(
            self.follow_button,
            text=_('Follow aircraft on Flightgear over telnet connection.')
        )

        # Init upstream reader
        self.upstream_reader = UpstreamReader(self.window, self.upstream_queue, 100)
        self.upstream_reader.read()

        # Init downloader
        self.downloader = Downloader(self.window, self.upstream_queue, self.download_manager, 100)
        self.downloader.download()

    def follow(self):
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