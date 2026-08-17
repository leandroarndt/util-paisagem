"""
Manages download jobs:
  - create downloaders
  - manage tiles to retrieve
"""
from typing import List
from pathlib import Path
from numbers import Number
from queue import Queue
from utilpaisagem.scenery.image_service import ImageService
from utilpaisagem.scenery.tile import Tile
from utilpaisagem.scenery.common import Coordinates, distance, DOWNLOAD_RES, MIN_RES
from utilpaisagem.gui.common import Settings

class DownloadManager(object):
    """
    Manages photo scenery downloads.

    Attributes:
        queue(list): list of tile indexes to download
        radius(int): range in kilometers of photo scenery to download
        center_lat(Number): center latitude
        center_lon(Number): center longitude
    """
    queue:List
    radius:int
    center_lat:Number
    center_lon:Number
    resolutions:dict
    upstream_queue:Queue|None
    setings:Settings

    def __init__(
        self,
        center_lat,
        center_lon,
        upstream_queue:Queue|None=None
    ):
        self.settings = Settings()
        self.upstream_queue = upstream_queue
        self.queue = []
        self.recenter(center_lat, center_lon)

    def add(self, tile:Tile, order:int):
        """
        Adds a new tile to the queue at index. If the tile is already queued,
        places it at the new order.

        Arguments:
            tile(Tile): Tile instance
            order(int): tile place at the queue
        """
        if tile  in self.queue:
            self.queue.pop(self.queue.index(tile))
        self.queue.insert(order, tile)
    
    def clear(self):
        self.queue.clear()

    def get_region(self, lat:Number, lon:Number, add=True) -> List[Tile]:
        """
        Returns list of tiles of a region centered at `lat` and `lon`. If `add` is True,
        adds them to the download queue.

        Arguments:
            lat(Number): latitude of the region center
            lon(Number): longitude of the region center
            add(bool=True): whether to add each tile to the download queue.
        """
        center_tile = Tile(lat=lat, lon=lon)
        n = 0
        done = []
        todo = [center_tile]
        while todo:
            current = todo.pop(0)
            dif_lat = 0.07 # Another tile from the center
            dif_lon = abs(current.coordinates.lon_left - current.coordinates.lon_median) + 0.01
            for m in ((-1,0), (0,1), (1,0), (0, -1)):
                next_lat = current.coordinates.lat_median + m[0] * dif_lat
                next_lon = current.coordinates.lon_median + m[1] * dif_lon
                dist = distance(lat, lon, next_lat, next_lon)
                if dist <= self.settings.radius:
                    res = MIN_RES
                    for d, r in self.settings.distances.items():
                        if dist <= d and r > res:
                            res = r
                    next_tile = Tile(lat=next_lat, lon=next_lon, resolution=res, upstream_queue=self.upstream_queue)
                    if next_tile not in done and next_tile not in todo:
                        todo.append(next_tile)
                    if add and next_tile not in self.queue:
                        self.add(next_tile, n)
                        n += 1
            done.append(current)
        return done

    def recenter(self, lat:Number, lon:Number):
        """
        Recenters the download manager, attributing greater priority to
        the new center and its adjacent tiles.

        Arguments:
            lat(Number): new center latitude
            lon(Number): new center longitude
        """
        self.center_lat, self.center_lon = lat, lon
        tiles = self.get_region(lat, lon, add=True)

    def download_next(self, path:Path, image_service:ImageService, download_res=DOWNLOAD_RES, compress='smart'):
        """
        Downloads next queued tile into `path` using `downloader`.

        Arguments:
            path(Path): path to download folder.
            image_service(ImageService): image service from which to download the tile.
        """
        tile:Tile = self.queue.pop(0)
        tile.retrieve(path=path, image_service=image_service, download_res=download_res, compress=compress)

