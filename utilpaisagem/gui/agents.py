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
from utilpaisagem.gui.common import format_log

class UpstreamReader(object):
    log:str
    upstream_queue:Queue
    root:tk.Tk
    interval:int

    def __init__(self, root:tk.Tk, upstream_queue:Queue, interval:int=100):
        self.root = root
        self.upstream_queue = upstream_queue
        self.interval = interval
        self.log = ''
    
    def read(self):
        while not self.upstream_queue.empty():
            try:
                msg = self.upstream_queue.get_nowait()
            except Empty:
                break
            self.log = self.log + msg + '\n'
            print(msg)
        self.root.after(self.interval, self.read)

# TODO
class Downloader(object):
    root:tk.Tk
    upstream_queue:Queue
    download_manager:DownloadManager
    idle_interval:int
    download_queue:Queue
    wait_queue:Queue
    downloading:bool

    def __init__(self, root:tk.Tk, upstream_queue:Queue, download_manager:DownloadManager, idle_interval:int=100):
        self.root = root
        self.upstream_queue = upstream_queue
        self.download_manager = download_manager
        self.interval = idle_interval
        self.download_queue = Queue()
        self.wait_queue = Queue()
        self.downloading = False
    
    def _download_thread(self):
        tile:Tile = self.download_queue.get()
        tile.retrieve(path=Path('target'), image_service=IMAGE_SERVICES['ArcGIS'], upstream_queue=self.upstream_queue)
        self.wait_queue.put_nowait(tile.index)

    def _wait_download(self):
        if self.wait_queue.empty():
            self.root.after(100, self._wait_download)
        else:
            print(self.wait_queue.get_nowait())
            self.downloading = False
            self._download_tiles()

    def _download_tiles(self):
        if (not self.download_queue.empty()) and (not self.downloading):
            self.dowloading = True
            thread = Thread(target=self._download_thread)
            thread.start()
            self._wait_download()

    def download(self):
        while self.download_manager.queue:
            self.download_queue.put_nowait(self.download_manager.queue.pop(0))
        if not self.download_queue.empty():
            self._download_tiles()
        self.root.after(self.interval, self.download)

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
            self.upstream_queue.put_nowait(format_log(_('Could not connect to Flightgear.'), self))
            raise e
        else:
            self.upstream_queue.put_nowait(format_log(_('Sucessfuly connected to Flightgear.'), self))
    
    def follow(self):
        if not self.downstream_queue.is_shutdown:
            try:
                lat = self.connection.get_prop('/position/latitude-deg')
                lon = self.connection.get_prop('/position/longitude-deg')
            except FGCommunicationError: # Could not retrieve info from Flightgear
                self.upstream_queue.put_nowait(
                    format_log(_('Could not receive coordinates info from Flightgear'), self)
                )
            except Exception as e:
                self.upstream_queue.put_nowait(
                    format_log(_('Error while retrieving coordinates from flightgear ("{e}")').format(exception=e))
                )
                self.downstream_queue.shutdown(immediate=True) # Tell master thread that we have terminated
            else:
                self.download_manager.recenter(lat=lat, lon=lon) # Update download manager center
                self.upstream_queue.put_nowait(
                    format_log(_('Aircraft position is latitude {lat:.02f}, longitude {lon:.02f}').format(lat=lat, lon=lon), self)
                )
                self.root.after(self.interval, self.follow)

    def run(self):
        self.thread = Thread(target=self.follow)
        self.thread.start()
