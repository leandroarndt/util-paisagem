from typing import List, Dict, TYPE_CHECKING
import os, configparser
import tkinter as tk
from queue import Queue
from math import ceil
from pathlib import Path
from tkintermapview.canvas_polygon import CanvasPolygon
from utilpaisagem.gui.map_widget import MapWidget
from utilpaisagem.gui.common import Settings
from utilpaisagem.scenery.common import Coordinates
from utilpaisagem.scenery.tile import Tile

class TileColors:
        great_tile = 'hotpink4'
        degree_tile = 'hotpink2'
        good = 'green2'
        failed = 'yellow2'
        old = 'slategray3'
        selected = 'darkturquoise'

class ManagedTile(object):
    coordinates:Coordinates
    settings:Settings
    path:Path
    index:int
    state:str
    polygon:CanvasPolygon
    intermap:MapWidget

    def __init__(
        self,
        coordinates:Coordinates,
        index:int,
        color:str,
        map_widget:MapWidget
    ):
        self.settings = Settings()
        self.coordinates, self.index, self.state, self.map_widget = \
            coordinates, index, color, map_widget
        self.polygon = None

    def draw(self):
        if self.polygon is None or self.polygon.deleted():
            self.polygon = self.map_widget.set_polygon(
                [
                    (self.coordinates.lat_top, self.coordinates.lon_left),
                    (self.coordinates.lat_top, self.coordinates.lon_right),
                    (self.coordinates.lat_bottom, self.coordinates.lon_right),
                    (self.coordinates.lat_bottom, self.coordinates.lon_left)
                ],
                outline_color=self.state,
                fill_color=None,
                border_width=2,
            )
        else:
        #     self.map_widget.canvas.itemconfigure(self.polygon, state=tk.NORMAL)
            self.map_widget.canvas.itemconfigure(self.polygon.canvas_polygon, state=tk.NORMAL)

    def hide(self):
        if self.polygon is not None:
            # self.polygon.delete()
            self.map_widget.canvas.itemconfigure(self.polygon.canvas_polygon, state=tk.HIDDEN)

class DegreeTile(ManagedTile):
    tiles:Dict
    path:Path

    @staticmethod
    def coordinates_to_index(coordinates:Coordinates) -> int:
        """
        Returns a unique integer index from coordinates.
        Ranges from -360181000 to -10000.

        Arguments:
            coordinates(Coordinates)
        """
        return -1*abs(ceil(coordinates.lon_left-180) * 1000 \
                - ceil(coordinates.lat_top+90))*10000 - 10000, # -360181000 to -10000

    def __init__(self, coordinates:Coordinates, map_widget:MapWidget, path:Path, *args, **kwargs):
        super().__init__(
            coordinates=coordinates,
            index=self.coordinates_to_index(coordinates),
            color=TileColors.degree_tile,
            map_widget=map_widget, *args, **kwargs
        )
        self.path = path
        self.tiles = {}

    def find_tiles(self):
        for item in self.path.iterdir():
            if item.stem.isdigit():
                if (item.parent / (item.stem + '.log')).exists():
                    log = configparser.ConfigParser()
                    log.read(item.parent / (item.stem + '.log'))
                    tile = Tile(int(item.stem))
                    if tile.is_failed(log, item.parent / (item.stem + '.log')):
                        self.tiles[tile.index] = ManagedTile(
                            coordinates=tile.coordinates,
                            index=tile.index,
                            color=TileColors.failed,
                            map_widget=self.map_widget,
                        )
                    elif tile.is_old(log, item.parent / (item.stem + '.log')):
                        self.tiles[tile.index] = ManagedTile(
                            coordinates=tile.coordinates,
                            index=tile.index,
                            color=TileColors.old,
                            map_widget=self.map_widget,
                        )
                    else:
                        self.tiles[tile.index] = ManagedTile(
                            coordinates=tile.coordinates,
                            index=tile.index,
                            color=TileColors.good,
                            map_widget=self.map_widget,
                        )
                    self.tiles[tile.index].draw()
                elif item.suffix.lower() == '.png' or item.suffix.lower() == '.dds':
                    self.tiles[int(item.stem)] = ManagedTile(
                        coordinates=Tile.index_to_coordinates(int(item.stem)),
                        index=int(item.stem),
                        color=TileColors.failed,
                        map_widget=self.map_widget,
                    )
                    self.tiles[int(item.stem)].draw()

class GreatTile(ManagedTile):
    tiles:List[DegreeTile]

    def __init__(self, coordinates:Coordinates, map_widget:MapWidget, *args, **kwargs):
        super().__init__(
            coordinates=coordinates,
            index=self.coordinates_to_index(coordinates),
            color=TileColors.great_tile,
            map_widget=map_widget, *args, **kwargs
        )
        self.path = self.get_path(self.coordinates)
    
    @staticmethod
    def get_path(coordinates:Coordinates) -> Path:
        return Path(Settings().orthophotos_folder) / \
            (f'{'w' if coordinates.lon_left < 0 else 'e'}{abs(coordinates.lon_left):03}' + \
            f'{'s' if coordinates.lat_bottom < 0 else 'n'}{abs(coordinates.lat_bottom):-02}')

    @staticmethod
    def coordinates_to_index(coordinates:Coordinates) -> int:
        """
        Returns a unique integer index from coordinates.
        Ranges from -3619 to -1.

        Arguments:
            coordinates(Coordinates)
        """
        return -1*abs(int((coordinates.lon_left-180)/10) * 100 \
                - int((coordinates.lat_top+90)/10)) - 1, # -3619 to -1

    def find_degree_tiles(self):
        self.tiles = {}
        for item in self.path.iterdir():
            if item.is_dir():
                if os.listdir(item):
                    lat_bottom = -int(item.name[5:]) if item.name[4] == 's' else int(item.name[5:])
                    lon_left = -int(item.name[1:4]) if item.name[0] == 'w' else int(item.name[1:4])
                    dt = DegreeTile(
                        coordinates=Coordinates(
                            lat1=lat_bottom,
                            lon1=lon_left,
                            lat2=lat_bottom+1,
                            lon2=lon_left+1
                        ),
                        map_widget=self.map_widget,
                        path=item,
                    )
                    self.tiles[dt.index] = dt
                    dt.draw()
                    dt.find_tiles()
                else:
                    os.rmdir(item) # Removes empty folder


class TileManager(object):
    settings:Settings

    great_tiles:Dict
    
    upstream_queue:Queue
    map_widget:MapWidget
    tile_queue:Queue

    def __init__(self, upstream_queue:Queue, map_widget:MapWidget):
        self.settings = Settings()
        self.tile_queue = Queue()
        self.upstream_queue, self.map_widget = upstream_queue, map_widget
        self.find_great_tiles()

    def find_great_tiles(self):
        self.great_tiles = {}
        for item in Path(self.settings.orthophotos_folder).iterdir():
            if item.is_dir():
                if os.listdir(item):
                    lat_bottom = -int(item.name[5:]) if item.name[4] == 's' else int(item.name[5:])
                    lon_left = -int(item.name[1:4]) if item.name[0] == 'w' else int(item.name[1:4])
                    gt = GreatTile(
                        coordinates=Coordinates(
                            lat1=lat_bottom,
                            lon1=lon_left,
                            lat2=lat_bottom+10,
                            lon2=lon_left+10
                        ),
                        map_widget=self.map_widget,
                    )
                    gt.draw()
                    gt.find_degree_tiles()
                else:
                    os.rmdir(item) # Removes empty folder

class TileScraper(object):
    pass