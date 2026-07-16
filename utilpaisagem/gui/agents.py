from pathlib import Path
from threading import Thread
from queue import Queue, ShutDown, Empty
import tkinter as tk
import os
from flightgear_python.fg_if import TelnetConnection
from flightgear_python.fg_util import FGCommunicationError, FGConnectionError
from utilpaisagem.scenery.download_manager import DownloadManager
from utilpaisagem.scenery.tile import Tile
from utilpaisagem.scenery.image_service import ImageService, IMAGE_SERVICES
from utilpaisagem.gui.common import format_status, Settings

settings = Settings()

class Downloader(object):
    """
    Manages download threads.
    """
    root:tk.Tk
    upstream_queue:Queue
    download_manager:DownloadManager
    interval:int
    idle_interval:int
    download_queue:Queue
    wait_queue:Queue
    current_downloads:int
    max_downloads:int

    def __init__(self, root:tk.Tk, upstream_queue:Queue, download_manager:DownloadManager, interval:int=100, idle_interval:int=1000, max_downloads:int=4):
        self.root = root
        self.upstream_queue = upstream_queue
        self.download_manager = download_manager
        self.interval = interval
        self.idle_interval = idle_interval
        self.download_queue = Queue()
        self.wait_queue = Queue()
        self.current_downloads = 0
        self.max_downloads = max_downloads
    
    def _download_thread(self):
        tile:Tile = self.download_queue.get()
        tile.retrieve(path=Path(settings.orthophotos_folder), image_service=IMAGE_SERVICES['ArcGIS'], upstream_queue=self.upstream_queue)
        self.wait_queue.put_nowait(tile.index)

    def _wait_download(self):
        # if self.wait_queue.empty():
        #     self.root.after(self.interval, self._wait_download)
        # else:
        if not self.wait_queue.empty():
            self.wait_queue.get_nowait()
            self.current_downloads -= 1
            self._download_tiles()

    def _download_tiles(self):
        if (not self.download_queue.empty()):
            if self.current_downloads < self.max_downloads:
                self.current_downloads += 1
                thread = Thread(target=self._download_thread)
                thread.start()
            self._wait_download()

    def add_tile(self, index):
        self.download_queue.put_nowait(Tile(index, upstream_queue=self.upstream_queue))
        self.upstream_queue.put_nowait(format_status(
            _('Tile {index} added to download queue.').format(index=index),
            self
        ))

    # def add_region(self, )

    def download(self):
        while self.download_manager.queue:
            self.download_queue.put_nowait(self.download_manager.queue.pop(0))
        if not self.download_queue.empty():
            self._download_tiles()
            self.root.after(self.interval, self.download)
        else:
            self.root.after(self.idle_interval, self.download)

class Follower(object):
    """Class used to follow a Flightgear aircraft in a separate thread."""
    root:tk.Tk
    connection:TelnetConnection
    upstream_queue:Queue
    downstream_queue:Queue
    download_manager:DownloadManager
    interval:int

    def __init__(self,
        root:tk.Tk,
        upstream_queue:Queue,
        downstream_queue:Queue,
        download_manager,
        host:str='localhost',
        port:int=5000,
        interval:int=10000
    ):
        self.root = root
        self.upstream_queue = upstream_queue
        self.downstream_queue = downstream_queue
        self.download_manager = download_manager
        self.interval = interval
        self.connection = TelnetConnection(host, port)
        try:
            self.connection.connect() # Raises FGConnectionError if fails
        except FGConnectionError as e:
            self.upstream_queue.put_nowait(format_status(_('Could not connect to Flightgear.'), self))
            raise e
        else:
            self.upstream_queue.put_nowait(format_status(_('Sucessfuly connected to Flightgear.'), self))
    
    def follow(self):
        if not self.downstream_queue.is_shutdown: # If the following has not been canceled
            try:
                lat = self.connection.get_prop('/position/latitude-deg')
                lon = self.connection.get_prop('/position/longitude-deg')
            except FGCommunicationError: # Could not retrieve info from Flightgear
                self.upstream_queue.put_nowait(
                    format_status(_('Could not receive coordinates info from Flightgear'), self)
                )
            except Exception as e:
                self.upstream_queue.put_nowait(
                    format_status(_('Error while retrieving coordinates from flightgear ("{exception}")').format(exception=e), self)
                )
                # self.downstream_queue.shutdown(immediate=True) # Tell master thread that we have terminated
            else:
                self.download_manager.recenter(lat=lat, lon=lon) # Update download manager center
                self.upstream_queue.put_nowait(
                    format_status(_('Aircraft position is latitude {lat:.02f}, longitude {lon:.02f}').format(lat=lat, lon=lon), self)
                )
            self.root.after(self.interval, self.follow)

class UpstreamReader(object):
    """
    Reads the upstream queue and puts its content at the status bar.
    """
    upstream_queue:Queue
    downloader:Downloader
    root:tk.Tk
    interval:int
    status_var:tk.StringVar
    show_tiles:bool

    def __init__(
        self,
        root:tk.Tk,
        status_var:tk.StringVar,
        upstream_queue:Queue,
        downloader:Downloader,
        interval:int=100,
    ):
        self.root = root
        self.upstream_queue = upstream_queue
        self.interval = interval
        self.downloader = downloader
        self.status_var = status_var
        self.status_var.set(_('Welcome to Útil paisagem'))
        self.show_tiles = False
    
    def read(self):
        if not self.show_tiles:
            if self.downloader.download_queue.qsize():
                self.show_tiles = True
        msg = ''
        while not self.upstream_queue.empty():
            try:
                msg = self.upstream_queue.get_nowait()
            except Empty:
                break
            # self.log = self.log + msg + '\n'
            print(msg)
        if msg and self.show_tiles:
            self.status_var.set(' '.join([
                msg,
                _('(Remaining tiles: {n})').format(
                    n=self.downloader.download_queue.qsize() + self.downloader.current_downloads
                )
            ]))
        elif self.show_tiles and self.downloader.current_downloads == 0:
            self.status_var.set(_('All tiles have been downloaded.'))
            self.show_tiles = False
        elif msg:
            self.status_var.set(msg)
        self.root.after(self.interval, self.read)

