from typing import List, Dict, TYPE_CHECKING
import tkinter as tk
from queue import Queue
from math import ceil
from tkintermapview.canvas_polygon import CanvasPolygon
from utilpaisagem.gui.map_widget import MapWidget
from utilpaisagem.gui.common import Settings
from utilpaisagem.scenery.common import Coordinates

BORDER_WIDTH = 3

class TileColors:
        great_tile = 'green'
        good = 'green2'
        failed = 'yellow2'
        old = 'slategray3'
        selected = 'darkturquoise'

class ManagedTile(object):
    coordinates:Coordinates
    index:int
    state:str
    polygon:CanvasPolygon
    intermap:MapWidget

    def __init__(
        self,
        coordinates:Coordinates,
        index:int, color:str,
        intermap:MapWidget
    ):
        self.coordinates, self.index, self.state, self.intermap = \
            coordinates, index, color, intermap

    def draw(self):
        if self.polygon is None:
            self.polygon = self.intermap.set_polygon([
                (coordinates.lat_top, coordinates.lon_left),
                (coordinates.lat_top, coordinates.lon_right),
                (coordinates.lat_bottom, coordinates.lon_right),
                (coordinates.lat_bottom, coordinates.lon_left)
            ], outline_color=color, fill_color=None)
        else:
            self.intermap.canvas.itemconfigure(self.polygon, state=tk.NORMAL)

    def hide(self):
        if self.polygon is not None:
            self.intermap.canvas.itemconfigure(self.polygon, state=tk.HIDDEN)

class GreatTile(ManagedTile):
    def __init__(self, coordinates:Coordinates, intermap:MapWidget, *args, **kwargs):
        super().__init__(
            coordinates=coordinates,
            index=-1*abs(int((self.coordinates.lon_left-180)/10) * 100 \
                - int((self.coordinates.lat_top+90)/10)) - 1, # -3619 to -1
            color=TileColors.great_tile,
            intermap=intermap, *args, **kwargs
        )

class DegreeTile(ManagedTile):
    def __init__(self, coordinates:Coordinates, intermap:MapWidget, *args, **kwargs):
        super().__init__(
            coordinates=coordinates,
            index=-1*abs(ceil(self.coordinates.lon_left-180) * 1000 \
                - ceil(self.coordinates.lat_top+90))*10000 - 10000, # -360181000 to -10000
            color=TileColors.great_tile,
            intermap=intermap, *args, **kwargs
        )

class TileManager(object):
    settings:Settings

    great_tiles:list
    tiles:dict
    
    upstream_queue:Queue
    map_widget:MapWidget
    tile_queue:Queue

    def __init__(self, upstream_queue:Queue, map_widget:MapWidget):
        self.settings = Settings()
        self.tile_queue = Queue()
        self.upstream_queue, self.map_widget = upstream_queue, map_widget
