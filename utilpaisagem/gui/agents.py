from pathlib import Path
from threading import Thread
from queue import Queue, ShutDown, Empty
from decimal import Decimal
import tkinter as tk
import os
from babel.numbers import format_decimal
from flightgear_python.fg_if import TelnetConnection
from flightgear_python.fg_util import FGCommunicationError, FGConnectionError
from utilpaisagem.scenery.download_manager import DownloadManager
from utilpaisagem.scenery.tile import Tile
from utilpaisagem.scenery.image_service import ImageService, IMAGE_SERVICES
from utilpaisagem.scenery.common import DOWNLOAD_RES
from utilpaisagem.gui.common import format_status, Settings, LOCALE
from utilpaisagem.gui.tile_manager import TileManager

class Downloader(object):
    """
    Manages download threads.
    """
    root:tk.Tk
    settings:Settings
    upstream_queue:Queue
    download_manager:DownloadManager
    interval:int
    idle_interval:int
    download_queue:Queue
    wait_queue:Queue
    current_downloads:int
    max_downloads:int
    total:int

    def __init__(
        self,
        root:tk.Tk,
        upstream_queue:Queue,
        tile_manager_queue:Queue,
        download_manager:DownloadManager,
        interval:int=100,
        idle_interval:int=1000,
        max_downloads:int=4,
    ):
        self.root = root
        self.upstream_queue = upstream_queue
        self.tile_manager_queue = tile_manager_queue
        self.download_manager = download_manager
        self.settings = Settings()
        self.interval = interval
        self.idle_interval = idle_interval
        self.download_queue = Queue()
        self.wait_queue = Queue()
        # self.max_downloads = max_downloads
        self.current_downloads = 0
        self.finished_downloads = 0
    
    def _download_thread(self):
        tile:Tile = self.download_queue.get()
        tile.retrieve(
            path=Path(self.settings.orthophotos_folder),
            image_service=IMAGE_SERVICES[0],
            upstream_queue=self.upstream_queue,
            download_res=self.settings.download_res,
            compress=self.settings.image_format,
            tile_manager_queue=self.tile_manager_queue
        )
        self.wait_queue.put_nowait(tile.index)

    def _wait_download(self):
        # if self.wait_queue.empty():
        #     self.root.after(self.interval, self._wait_download)
        # else:
        if not self.wait_queue.empty():
            self.wait_queue.get_nowait()
            self.current_downloads -= 1
            self.finished_downloads += 1
            self._download_tiles()

    def _download_tiles(self):
        if (not self.download_queue.empty()):
            if self.current_downloads < self.settings.tile_threads:
                self.current_downloads += 1
                thread = Thread(target=self._download_thread)
                thread.start()
            self._wait_download()

    def add_tile(self, index, resolution=DOWNLOAD_RES):
        self.download_queue.put_nowait(Tile(
            index,
            resolution=resolution,
            upstream_queue=self.upstream_queue,
        ))
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
        elif self.current_downloads: # No queue, but still downloading
            self._wait_download()
            self.root.after(self.interval, self.download)
        else:
            self.root.after(self.idle_interval, self.download)

class Follower(object):
    """Class used to follow a Flightgear aircraft in a separate thread."""
    root:tk.Tk
    settings:Settings
    connection:TelnetConnection
    upstream_queue:Queue
    downstream_queue:Queue
    download_manager:DownloadManager
    interval:int
    lat:float
    lon:float

    def __init__(self,
        main_window,
        upstream_queue:Queue,
        downstream_queue:Queue,
        download_manager,
        *args,
        **kwargs
    ):
        self.main_window = main_window
        self.settings = Settings()
        self.upstream_queue = upstream_queue
        self.downstream_queue = downstream_queue
        self.download_manager = download_manager
        self.connection = TelnetConnection(self.settings.host, self.settings.port, rx_timeout_s=1.0)
        self.lat = 0.0
        self.lon = 0.0

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
                self.lat = self.connection.get_prop('/position/latitude-deg')
                self.lon = self.connection.get_prop('/position/longitude-deg')
            except FGCommunicationError: # Could not retrieve info from Flightgear
                self.upstream_queue.put_nowait(
                    format_status(_('Could not receive coordinates info from Flightgear'), self)
                )
                self.main_window.place_aircraft(self.lat, self.lon, active=False)
                self.main_window.window.after(self.settings.following_interval*10, self.follow)
            except Exception as e:
                self.upstream_queue.put_nowait(
                    format_status(_('Error while retrieving coordinates from flightgear ("{exception}")').format(exception=e), self)
                )
                self.main_window.place_aircraft(self.lat, self.lon, active=False)
                self.main_window.window.after(self.settings.following_interval*10, self.follow)
                # self.downstream_queue.shutdown(immediate=True) # Tell master thread that we have terminated
            else:
                self.download_manager.recenter(lat=self.lat, lon=self.lon) # Update download manager center
                self.main_window.place_aircraft(self.lat, self.lon, active=True)
                self.upstream_queue.put_nowait(
                    format_status(_('Aircraft position is latitude {lat:.02f}, longitude {lon:.02f}').format(lat=self.lat, lon=self.lon), self)
                )
                self.main_window.window.after(self.settings.following_interval, self.follow)
        else:
            self.close_connection()
    
    def close_connection(self):
        self.connection.sock.close()

class UpstreamReader(object):
    """
    Reads the upstream queue and puts its content at the status bar.
    """
    upstream_queue:Queue
    tile_manager:TileManager
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
        tile_manager:TileManager,
        downloader:Downloader,
        interval:int=100,
    ):
        self.root = root
        self.upstream_queue = upstream_queue
        self.tile_manager = tile_manager
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
                _('(Remaining tiles: {n}/{total})').format(
                    n=self.downloader.download_queue.qsize() + self.downloader.current_downloads,
                    total=self.downloader.download_queue.qsize() + \
                        self.downloader.finished_downloads + \
                        self.downloader.current_downloads
                )
            ]))
        elif self.show_tiles and self.downloader.current_downloads == 0:
            self.status_var.set(format_status(
                _('All {total} tiles have been processed. Used disk space: {space} MB.').format(
                    total=self.downloader.download_queue.qsize() + \
                        self.downloader.finished_downloads + \
                        self.downloader.current_downloads,
                    space = format_decimal(
                        Decimal(
                            self.tile_manager.disk_usage / 1024**2).quantize(Decimal('1.00'),
                            locale=LOCALE
                        )
                    ),
                ),
                self
            ))
            self.show_tiles = False
        elif msg:
            self.status_var.set(msg)
        self.root.after(self.interval, self.read)

