from typing import List, Dict, Union, TYPE_CHECKING
import os, configparser
import tkinter as tk
from queue import Queue
from math import ceil
from pathlib import Path
from threading import Thread
from tkintermapview.canvas_polygon import CanvasPolygon
from utilpaisagem.gui.map_widget import MapWidget
from utilpaisagem.gui.common import Settings
from utilpaisagem.scenery.common import Coordinates
from utilpaisagem.scenery.tile import Tile
if 'DEBUG' in os.environ:
    print('*** TILE MANAGER DEBUG MODE ***')
    from pympler.asizeof import asized
    from datetime import datetime
    DEBUG = True
else:
    DEBUG = False

def dir_has_contents(dir:Path):
    for item in os.scandir():
        return True
    return False

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

    count = 0

    def __init__(
        self,
        coordinates:Coordinates,
        index:int,
        state:str,
        map_widget:MapWidget
    ):
        self.settings = Settings()
        self.coordinates, self.index, self.state, self.map_widget = \
            coordinates, index, state, map_widget
        self.polygon = None

        if DEBUG:
            ManagedTile.count += 1

    def draw(self, polygon:CanvasPolygon=None):
        if self.polygon is None or self.polygon.deleted:
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
            self.map_widget.canvas.itemconfigure(self.polygon.canvas_polygon, state=tk.NORMAL)

    def hide(self):
        if self.polygon is not None:
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
                - ceil(coordinates.lat_top+90))*10000 - 10000 # -360181000 to -10000

    def __init__(self, coordinates:Coordinates, map_widget:MapWidget, path:Path, *args, **kwargs):
        super().__init__(
            coordinates=coordinates,
            index=self.coordinates_to_index(coordinates),
            state=TileColors.degree_tile,
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
                            state=TileColors.failed,
                            map_widget=self.map_widget,
                        )
                    elif tile.is_old(log, item.parent / (item.stem + '.log')):
                        self.tiles[tile.index] = ManagedTile(
                            coordinates=tile.coordinates,
                            index=tile.index,
                            state=TileColors.old,
                            map_widget=self.map_widget,
                        )
                    else:
                        self.tiles[tile.index] = ManagedTile(
                            coordinates=tile.coordinates,
                            index=tile.index,
                            state=TileColors.good,
                            map_widget=self.map_widget,
                        )
                elif item.suffix.lower() == '.png' or item.suffix.lower() == '.dds':
                    self.tiles[int(item.stem)] = ManagedTile(
                        coordinates=Tile.index_to_coordinates(int(item.stem)),
                        index=int(item.stem),
                        state=TileColors.failed,
                        map_widget=self.map_widget,
                    )

class GreatTile(ManagedTile):
    tiles:List[DegreeTile]

    def __init__(self, coordinates:Coordinates, map_widget:MapWidget, *args, **kwargs):
        super().__init__(
            coordinates=coordinates,
            index=self.coordinates_to_index(coordinates),
            state=TileColors.great_tile,
            map_widget=map_widget, *args, **kwargs
        )
        self.tiles = {}
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
                - int((coordinates.lat_top+90)/10)) - 1 # -3619 to -1

    def find_degree_tiles(self):
        self.tiles = {}
        for item in self.path.iterdir():
            if item.is_dir():
                if dir_has_contents(item):
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
                else:
                    os.rmdir(item) # Removes empty folder


class TileManager(object):
    class DetailLevels:
        great_tile = 0
        degree_tile = 30
        tile = 3

    settings:Settings

    great_tiles:Dict
    active_tiles:List
    detail_level:int
    map_tiles:List
    
    upstream_queue:Queue
    map_widget:MapWidget
    tile_queue:Queue

    def __init__(self, upstream_queue:Queue, map_widget:MapWidget):
        self.settings = Settings()
        self.tile_queue = Queue()
        self.upstream_queue, self.map_widget = upstream_queue, map_widget
        self.active_tiles = []
        self.great_tiles = {}
        self.map_tiles = {}
        self.map_widget.after(200, self.update)

    def find_great_tiles(self):
        if DEBUG:
            start = datetime.now()
            print(f'Starting benchmark at {start}...', flush=True)
        self.great_tiles = {}
        for item in Path(self.settings.orthophotos_folder).iterdir():
            if item.is_dir():
                if dir_has_contents(item):
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
                    self.great_tiles[gt.index] = gt
                else:
                    os.rmdir(item) # Removes empty folder

        if DEBUG:
            print(f'Time spent processing tiles: {datetime.now() - start}')
            print(f'Total: {ManagedTile.count} tiles.')
            print(f'Memory used to manage {ManagedTile.count} tiles: {asized(self)}')
            for gt in self.great_tiles.values():
                print(f'Memory used by a single tile: {asized(gt)}')
                break
    
    def update(self):
        if self.map_widget.updated:
            try:
                self.update_active_tiles()
            except OverflowError:
                pass # Needs to wait until ready
            except ValueError:
                pass # Randomly throws "ValueError: math domain error"
                     # at tkintermapview\utility_functions.py", line 12
        self.map_widget.after(200, self.update)
    
    def update_active_tiles(self):
        canvas_limits = self.map_widget.get_canvas_coords()
        if canvas_limits.lat_top - canvas_limits.lat_bottom > 30 or \
            canvas_limits.lon_right - canvas_limits.lon_left > 30:
            self.detail_level = TileManager.DetailLevels.great_tile
        elif canvas_limits.lat_top - canvas_limits.lat_bottom > 3 or \
            canvas_limits.lon_right - canvas_limits.lon_left > 3:
            self.detail_level = TileManager.DetailLevels.degree_tile
        else:
            self.detail_level = TileManager.DetailLevels.tile

        for tile in self.active_tiles:
            tile.hide()
        
        self.active_tiles = []
        for tile in self.great_tiles.values():
            if tile.coordinates.lat_top > canvas_limits.lat_bottom and \
                tile.coordinates.lat_bottom < canvas_limits.lat_top and \
                tile.coordinates.lon_left < canvas_limits.lon_right and \
                tile.coordinates.lon_right > canvas_limits.lon_left:
                if self.detail_level == TileManager.DetailLevels.great_tile:
                    self.active_tiles.append(tile)
                else:
                    if not tile.tiles:
                        tile.find_degree_tiles()
                    for dt in tile.tiles.values():
                        if dt.coordinates.lat_top > canvas_limits.lat_bottom - TileManager.DetailLevels.degree_tile and \
                            dt.coordinates.lat_bottom < canvas_limits.lat_top + TileManager.DetailLevels.degree_tile and \
                            dt.coordinates.lon_left < canvas_limits.lon_right + TileManager.DetailLevels.degree_tile and \
                            dt.coordinates.lon_right > canvas_limits.lon_left - TileManager.DetailLevels.degree_tile:
                            if self.detail_level == TileManager.DetailLevels.degree_tile:
                                self.active_tiles.append(dt)
                            else:
                                if not dt.tiles:
                                    dt.find_tiles()
                                for t in dt.tiles.values():
                                    if t.coordinates.lat_top > canvas_limits.lat_bottom - TileManager.DetailLevels.tile and \
                                        t.coordinates.lat_bottom < canvas_limits.lat_top + TileManager.DetailLevels.tile and \
                                        t.coordinates.lon_left < canvas_limits.lon_right + TileManager.DetailLevels.tile and \
                                        t.coordinates.lon_right > canvas_limits.lon_left - TileManager.DetailLevels.tile:
                                        self.active_tiles.append(t)
                                    else:
                                        t.hide()
                        else:
                            dt.hide()

            else:
                tile.hide()

        for tile in self.active_tiles:
            tile.draw()
            

class TileScraper(object):
    pass