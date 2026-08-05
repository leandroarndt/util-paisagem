from typing import List, Dict, TYPE_CHECKING
from queue import Queue
from tkintermapview.map_widget import TkinterMapView
from tkintermapview.canvas_polygon import CanvasPolygon
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
    size:int
    polygon:CanvasPolygon
    intermap:TkinterMapView

    def __init__(
        self,
        coordinates:Coordinates,
        index:int, color:str,
        size:int,
        intermap:TkinterMapView
    ):
        self.coordinates, self.index, self.state, self.intermap = \
            coordinates, index, color, intermap
        intermap.set_polygon([
            (coordinates.lat_top, coordinates.lon_left),
            (coordinates.lat_top, coordinates.lon_right),
            (coordinates.lat_bottom, coordinates.lon_right),
            (coordinates.lat_bottom, coordinates.lon_left)
        ], outline_color=color, fill_color=None)

class GreatTile(ManagedTile):
    def __init__(self, coordinates:Coordinates, intermap:TkinterMapView, *args, **kwargs):
        super().__init__(
            coordinates=coordinates,
            index=-1*abs(int((gt.coordinates.lon_left-180)/10) * 1000 \
                - int((gt.coordinates.lat_top+90)/10)), # -3601 to -1
            color=TileColors.great_tile,
            size=0,
            intermap=intermap, *args, **kwargs
        )

class TileManager(object):
    settings:Settings

    great_tiles:list
    tiles:dict
    
    upstream_queue:Queue
    map_widget:TkinterMapView
    tile_queue:Queue

    def __init__(self, upstream_queue:Queue, map_widget:TkinterMapView):
        self.settings = Settings()
        self.tile_queue = Queue()
        self.upstream_queue, self.map_widget = upstream_queue, map_widget
