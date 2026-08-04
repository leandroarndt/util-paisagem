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
    state:str
    polygon:CanvasPolygon
    intermap:TkinterMapView

    def __init__(self, coordinates:Coordinates, color:str, intermap:TkinterMapView):
        self.coordinates, self.state, self.intermap = coordinates, color, intermap
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
            color=TileColors.great_tile,
            intermap=intermap, *args, **kwargs
        )

class TileManager(object):
    settings:Settings

    great_tiles:list

    def __init__(self):
        self.settings = Settings()