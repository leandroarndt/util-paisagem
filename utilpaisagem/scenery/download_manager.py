"""
Manages download jobs:
  - create downloaders
  - manage tiles to retrieve
"""
from pathlib import Path
from decimal import Decimal
from utilpaisagem.scenery.image_service import IMAGE_SERVICES, ImageService
from utilpaisagem.scenery.tile import Tile
from utilpaisagem.scenery.common import Coordinates, distance

class DownloadManager(object):
    """
    Manages photo scenery downloads.

    Attributes:
        queue(list): list of tile indexes to download
        radius(int): range in kilometers of photo scenery to download
        center_lat(Decimal): center latitude
        center_lon(Decimal): center longitude
    """
    queue:list
    radius:int
    center_lat:Decimal
    center_lon:Decimal

    def __init__(self, center_lat, center_lon, radius=50):
        self.queue = []
        self.radius = radius
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
            self.queue.pop(tile)
        self.queue.insert(order, tile)
        
    def recenter(self, lat:Decimal, lon:Decimal):
        """
        Recenters the download manager, attributing greater priority to
        the new center and its adjacent tiles.

        Arguments:
            lat(Decimal): new center latitude
            lon(Decimal): new center longitude
        """
        self.center_lat, self.center_lon = lat, lon
        center_tile = Tile(lat=lat, lon=lon)
        n = 0
        self.add(center_tile, n)
        done = []
        todo = [center_tile]
        while todo:
            current = todo[0]
            dif_lat = Decimal(0.07) # Another tile from the center
            dif_lon = abs(current.coordinates.lon_left - current.coordinates.lon_median) + Decimal(0.01)
            for m in ((-1,0), (0,1), (1,0), (0, -1)):
                next_lat = current.coordinates.lat_median + m[0] * dif_lat
                next_lon = current.coordinates.lon_median + m[1] * dif_lon
                if distance(lat, lon, next_lat, next_lon) <= self.radius:
                    next_tile = Tile(lat=next_lat, lon=next_lon)
                    if next_tile not in done and next_tile not in todo:
                        todo.append(next_tile)
                    if next_tile not in self.queue:
                        self.add(next_tile, n)
                        n += 1
            done.append(todo[0])
            todo.pop(0)

    def download_next(self, path:Path, image_service:ImageService):
        """
        Downloads next queued tile into `path` using `downloader`.

        Arguments:
            path(Path): path to download folder.
            image_service(ImageService): image service from which to download the tile.
        """
        tile:Tile = self.queue.pop(0)
        tile.retrieve(path, image_service)

