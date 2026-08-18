from typing import List, Dict, Union, TYPE_CHECKING
import os, configparser, math
import tkinter as tk
from queue import Queue
from math import ceil
from decimal import Decimal
from pathlib import Path
from threading import Thread
from datetime import datetime
from tkintermapview.canvas_polygon import CanvasPolygon
from babel.numbers import format_decimal
from utilpaisagem.gui.map_widget import MapWidget
from utilpaisagem.gui.common import Settings, format_status, TileColors, LOCALE
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
    for item in os.scandir(dir):
        return True
    return False

class TileAge(object):
    index:int
    age:float

    def __init__(self, index:int, timestamp:float):
        self.index, self.age = index, datetime.now() - datetime.fromtimestamp(timestamp)

    def __eq__(self, other):
        if isinstance(other, TileAge):
            return self.index == other.index
        elif isinstance(other, int):
            return self.index == other
        raise ValueError(f'Cannot compare TileAge with object of type {type(other)}')
    
    def __lt__(self, other):
        return self.age < other.age
    
    def __le__(self, other):
        return self.age <= other.age
    
    def __gt__(self, other):
        return self.age > other.age
    
    def __ge__(self, other):
        return self.age >= other.age

class AgeList(list):
    def put(self, item:TileAge):
        if item in self:
            self.pop(self.index(item))
        for i in range(len(self)):
            if item > self[i]:
                self.insert(i, item)
                return
        self.append(item)

class ManagedTile(object):
    coordinates:Coordinates
    settings:Settings
    path:Path
    index:int
    state:str
    polygon:CanvasPolygon
    intermap:MapWidget
    upstream_queue:Queue
    size_queue:Queue

    count = 0

    def __init__(
        self,
        coordinates:Coordinates,
        index:int,
        state:str,
        map_widget:MapWidget,
        upstream_queue,
        size_queue:Queue
    ):
        self.settings = Settings()
        self.coordinates, self.index, self.state, self.map_widget, self.upstream_queue, self.size_queue = \
            coordinates, index, state, map_widget, upstream_queue, size_queue
        self.polygon = None

        if DEBUG:
            ManagedTile.count += 1

    def draw(self, polygon:CanvasPolygon=None):
        if self.polygon is None or self.polygon.deleted:
            try:
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
            except ValueError:
                pass # tkintermapview/utility_functions.py", line 12:
                     # ytile = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
                     # ValueError: [math.log] expected a positive input, got 0.0
        else:
            self.map_widget.canvas.itemconfigure(self.polygon.canvas_polygon, state=tk.NORMAL)

    def hide(self):
        if self.polygon is not None:
            # self.map_widget.canvas.itemconfigure(self.polygon.canvas_polygon, state=tk.HIDDEN)
            self.polygon.delete()
            self.polygon = None

class DegreeTile(ManagedTile):
    tiles:Dict
    path:Path

    @staticmethod
    def coordinates_to_index(coordinates:Coordinates) -> int:
        """
        Returns a unique index from coordinates, corresponding to
        the second part of the tile path.

        Arguments:
            coordinates(Coordinates)
        """
        if coordinates.lat_median > 0:
            lat_dir = 'n'
        else:
            lat_dir = 's'
        if coordinates.lon_median > 0:
            lon_dir = 'e'
        else:
            lon_dir = 'w'
        return f'{lon_dir}{abs(math.floor(coordinates.lon_left)):03}' + \
            f'{lat_dir}{abs(math.floor(coordinates.lat_bottom)):02}'
    
    @staticmethod
    def index_to_coordinates(index:str) -> Coordinates:
        if 'w' in index:
            x_sign = -1
        else:
            x_sign = 1
        index = index.strip('we')
        if 'n' in index:
            y_sign = 1
            left, bottom = index.split('n')
        else:
            y_sign = -1
            left, bottom = index.split('s')
        return Coordinates(
            lat1=y_sign * int(bottom) + 1,
            lon1=x_sign * int(left) + 1,
            lat2=y_sign * int(bottom),
            lon2=x_sign * int(left),
        )

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
            if item.stem.isdigit() and (item.suffix.lower() == '.png' or item.suffix.lower() == '.dds'):
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
                            upstream_queue=self.upstream_queue,
                            size_queue=self.size_queue,
                        )
                    elif tile.is_old(log, item.parent / (item.stem + '.log')):
                        self.tiles[tile.index] = ManagedTile(
                            coordinates=tile.coordinates,
                            index=tile.index,
                            state=TileColors.old,
                            map_widget=self.map_widget,
                            upstream_queue=self.upstream_queue,
                            size_queue=self.size_queue,
                        )
                    else:
                        self.tiles[tile.index] = ManagedTile(
                            coordinates=tile.coordinates,
                            index=tile.index,
                            state=TileColors.good,
                            map_widget=self.map_widget,
                            upstream_queue=self.upstream_queue,
                            size_queue=self.size_queue,
                        )
                elif item.suffix.lower() == '.png' or item.suffix.lower() == '.dds':
                    self.tiles[int(item.stem)] = ManagedTile(
                        coordinates=Tile.index_to_coordinates(int(item.stem)),
                        index=int(item.stem),
                        state=TileColors.failed,
                        map_widget=self.map_widget,
                        upstream_queue=self.upstream_queue,
                        size_queue=self.size_queue,
                    )
                try:
                    self.size_queue.put_nowait((TileAge(int(item.stem), os.path.getmtime(item.with_suffix('.log'))), os.path.getsize(item)))
                except FileNotFoundError:
                    self.size_queue.put_nowait((TileAge(int(item.stem), 0), os.path.getsize(item)))

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
        Returns a unique index from coordinates, corresponding to
        the first part of the tile path.

        Arguments:
            coordinates(Coordinates)
        """
        if coordinates.lat_median > 0:
            lat_dir = 'n'
        else:
            lat_dir = 's'
        if coordinates.lon_median > 0:
            lon_dir = 'e'
        else:
            lon_dir = 'w'
        return f'{lon_dir}{abs(math.floor(coordinates.lon_left/10)) * 10:03}' + \
            f'{lat_dir}{abs(math.floor(coordinates.lat_bottom / 10) * 10):02}'
    
    @staticmethod
    def index_to_coordinates(index:str) -> Coordinates:
        if 'w' in index:
            x_sign = -1
        else:
            x_sign = 1
        index = index.strip('we')
        if 'n' in index:
            y_sign = 1
            left, bottom = index.split('n')
        else:
            y_sign = -1
            left, bottom = index.split('s')
        return Coordinates(
            lat1=y_sign * int(bottom) + 10,
            lon1=x_sign * int(left) + 10,
            lat2=y_sign * int(bottom),
            lon2=x_sign * int(left),
        )

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
                        upstream_queue=self.upstream_queue,
                        size_queue=self.size_queue,
                    )
                    self.tiles[dt.index] = dt
                    dt.find_tiles()
                    try:
                        self.upstream_queue.put_nowait(
                            format_status(
                                _('Finished scanning folder "{folder}".').format(folder=item),
                                self,
                            )
                        )
                        self.map_widget.master.update()
                        self.map_widget.master.update_idletasks()
                    except RuntimeError as e: # Happens if app closed before finishing
                        return
                else:
                    os.rmdir(item) # Removes empty folder


class TileManager(object):
    settings:Settings

    great_tiles:Dict
    active_tiles:List
    detail_level:int
    map_tiles:List
    disk_usage:int
    tile_list:AgeList
    search_complete:bool
    deleting_tiles:bool
    
    upstream_queue:Queue
    map_widget:MapWidget
    tile_queue:Queue
    size_queue:Queue

    def __init__(self, upstream_queue:Queue, map_widget:MapWidget):
        self.settings = Settings()
        self.tile_queue = Queue()
        self.size_queue = Queue()
        self.upstream_queue, self.map_widget = upstream_queue, map_widget
        self.active_tiles = []
        self.great_tiles = {}
        self.map_tiles = {}
        self.map_widget.after(200, self.update)
        self.disk_usage = 0
        self.tile_list = AgeList()
        self.search_complete = False
        self.deleting_tiles = False

        self.map_widget.after(200, self.read_size_queue)

    def read_size_queue(self):
        while not self.size_queue.empty():
            item = self.size_queue.get_nowait()
            if isinstance(item[0], TileAge):
                self.tile_list.put(item[0])
            else:
                try:
                    self.tile_list.pop(self.tile_list.index(item[0]))
                except ValueError:
                    pass # already poped from tile_list
            self.disk_usage += item[1]
        
        if self.settings.auto_clean:
            self.enforce_storage_limits()

        self.map_widget.after(200, self.read_size_queue)
    
    def enforce_storage_limits(self):
        if not self.settings.auto_clean and self.disk_usage < self.settings.max_disk_usage:
            self.upstream_queue.put_nowait(format_status(
                _('Current disk usage ({space} MB) does not exceed limit ({limit} MB).').format(
                    space=format_decimal(
                        Decimal(self.disk_usage / 1024 ** 2).quantize(Decimal('1.00')),
                        locale=LOCALE,
                    ),
                    limit=format_decimal(
                        Decimal(self.settings.max_disk_usage / 1024 ** 2).quantize(Decimal('1.00')),
                        locale=LOCALE,
                    ),
                ),
                self,
            ))
        if self.search_complete:
            if self.disk_usage > self.settings.max_disk_usage:
                self.deleting_tiles = True
                self.upstream_queue.put_nowait(format_status(
                    _('Disk space usage ({space} MB) exceeds limit ({limit} MB). Deleting unused tiles.').format(
                        space=format_decimal(
                            Decimal(self.disk_usage / 1024 ** 2).quantize(Decimal('1.00')),
                            locale=LOCALE,
                        ),
                        limit=format_decimal(
                            Decimal(self.settings.max_disk_usage / 1024 ** 2).quantize(Decimal('1.00')),
                            locale=LOCALE,
                        ),
                    ),
                    self,
                ))
                while self.disk_usage > self.settings.max_disk_usage:# and self.tile_list:
                    t = Tile(self.tile_list.pop(0).index)
                    path = t.get_path(self.settings.orthophotos_folder)
                    if (path / f'{t.index}.png').exists():
                        self.disk_usage -= os.path.getsize(path / f'{t.index}.png')
                    elif (path / f'{t.index}.dds').exists():
                        self.disk_usage -= os.path.getsize(path / f'{t.index}.dds')
                    t.delete_files(tile_manager_queue=self.tile_queue, auto_clean=True) # It already communicates with TileManager.tile_queue
                self.upstream_queue.put_nowait(format_status(
                    _('Finished deleting unused tiles. Current disk usage: {space} MB.').format(
                        space=format_decimal(
                            Decimal(self.disk_usage / 1024 ** 2).quantize(Decimal('1.00')),
                            locale=LOCALE,
                        ),
                    ),
                    self,
                ))
            self.deleting_tiles = False

    def find_great_tiles(self):
        def find_degrees():
            nonlocal all_gts
            while all_gts:
                gt = all_gts.pop(0)
                gt.find_degree_tiles()
        
        if self.deleting_tiles:
            return # Tasks may not be concomitant

        # Halts disk space management
        self.search_complete = False

        # Inform user
        self.upstream_queue.put_nowait(format_status(_('Searching for tiles to display'), self))

        # Reset tile management
        gt_keys = list(self.great_tiles.keys())
        for gt_key in gt_keys:
            gt = self.great_tiles.pop(gt_key)
            dt_keys = list(gt.tiles.keys())
            for dt_key in dt_keys:
                dt = gt.tiles.pop(dt_key)
                tile_keys = list(dt.tiles.keys())
                for tile_key in tile_keys:
                    tile = dt.tiles.pop(tile_key)
                    tile.hide()
                dt.hide()
            gt.hide()
        self.disk_usage = 0

        # Scan orthophotos folder
        if DEBUG:
            start = datetime.now()
            print(f'Starting benchmark at {start}...', flush=True)
        self.great_tiles = {}
        for item in Path(self.settings.orthophotos_folder).iterdir():
            if item.is_dir():
                if dir_has_contents(item):
                    for subitem in item.iterdir():
                        if not dir_has_contents(subitem):
                            os.rmdir(subitem)
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
                            upstream_queue=self.upstream_queue,
                            size_queue=self.size_queue,
                        )
                        self.great_tiles[gt.index] = gt
                    else:
                        os.rmdir(item)
                else:
                    os.rmdir(item) # Removes empty folder

        try:
            self.map_widget.master.update()
            self.map_widget.master.update_idletasks()
        except RuntimeError as e: # Happens if app closed before finishing
            return

        all_gts = list(self.great_tiles.values())
        # Should terminate when main thread quits
        threads = [Thread(target=find_degrees, daemon=True) for x in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.map_widget.updated = True

        self.upstream_queue.put_nowait(
            format_status(_('Finished searching for tiles to display.'), self)
            )
        self.search_complete = True

        if DEBUG:
            print(f'Time spent processing tiles: {datetime.now() - start}')
            print(f'Total: {ManagedTile.count} tiles.')
            print(f'Disk usage: {self.disk_usage} bytes.')
            print(f'Memory used to manage {ManagedTile.count} tiles: {asized(self)}')
            for gt in self.great_tiles.values():
                for dt in gt.tiles.values():
                    for tile in dt.tiles.values():
                        print(f'Memory used by a single tile: {asized(tile)}')
                        break
                    break
                break
    
    def update(self):
        updated_tiles = []

        while not self.tile_queue.empty():
            updated_tiles.append(self.tile_queue.get_nowait())
        for tile in updated_tiles:
            gt_index, dt_index = tile[-1]
            if tile[0] < 0:
                try:
                    # self.tile_list.pop(self.tile_list.index(abs(tile[0]))) # Fails if put by size reader
                    self.size_queue.put_nowait((abs(tile[0]), -tile[2]))
                except IndexError:
                    pass # self.read_size_queue() poped it already
                try:
                    t = self.great_tiles[gt_index].tiles[dt_index].tiles.pop(abs(tile[0]))
                except KeyError:
                    self.upstream_queue.put_nowait(format_status(
                        _('Could not delete tile {index}: not found.').format(
                            index=abs(tile[0]),
                        ),
                        self,
                    ))
                    continue
                try: t.polygon.delete()
                except AttributeError: pass
                if gt_index in self.great_tiles:
                    if dt_index in self.great_tiles[gt_index].tiles:
                        if not self.great_tiles[gt_index].tiles[dt_index].tiles:
                            t = self.great_tiles[gt_index].tiles.pop(dt_index)
                            t.hide()
                    if not self.great_tiles[gt_index].tiles:
                        t = self.great_tiles.pop(gt_index)
                        t.hide()
            else:
                self.size_queue.put_nowait((TileAge(tile[0], os.path.getmtime(tile[2].with_suffix('.log'))), os.path.getsize(tile[2])))
                try:
                    t = self.great_tiles[gt_index].tiles[dt_index].tiles[tile[0]]
                except KeyError:
                    t = ManagedTile(
                        coordinates=tile[1],
                        index=tile[0],
                        state=tile[3],
                        map_widget=self.map_widget,
                        upstream_queue=self.upstream_queue,
                        size_queue=self.size_queue,
                    )
                    if gt_index not in self.great_tiles:
                        gt = GreatTile(
                            coordinates=GreatTile.index_to_coordinates(gt_index),
                            map_widget=self.map_widget,
                            upstream_queue=self.upstream_queue,
                            size_queue=self.size_queue,
                        )
                        self.great_tiles[gt_index] = gt
                    if dt_index not in self.great_tiles[gt_index].tiles:
                        dt = DegreeTile(
                            coordinates=DegreeTile.index_to_coordinates(dt_index),
                            map_widget=self.map_widget,
                            path=tile[2].parent,
                            upstream_queue=self.upstream_queue,
                            size_queue=self.size_queue,
                        )
                        self.great_tiles[gt_index].tiles[dt_index] = dt
                if tile[0] not in self.great_tiles[gt_index].tiles[dt_index].tiles:
                    self.great_tiles[gt_index].tiles[dt_index].tiles[tile[0]] = t
                if self.great_tiles[gt_index].polygon is None and \
                    self.detail_level == self.settings.detail_zero:
                    self.great_tiles[gt_index].draw()
                elif self.great_tiles[gt_index].tiles[dt_index].polygon is None and \
                    self.detail_level == self.settings.detail_degree:
                    self.great_tiles[gt_index].tiles[dt_index].draw()
                elif self.great_tiles[gt_index].tiles[dt_index].tiles[tile[0]].polygon is None:
                    self.great_tiles[gt_index].tiles[dt_index].tiles[tile[0]].draw()
                else:
                    self.great_tiles[gt_index].tiles[dt_index].tiles[tile[0]].state = tile[3]
                    self.great_tiles[gt_index].tiles[dt_index].tiles[tile[0]].polygon.update(
                        color=tile[3]
                    )

        if updated_tiles or self.map_widget.updated:
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
        if canvas_limits.lat_top - canvas_limits.lat_bottom > self.settings.detail_degree or \
            canvas_limits.lon_right - canvas_limits.lon_left > self.settings.detail_degree:
            self.detail_level = self.settings.detail_zero
        elif canvas_limits.lat_top - canvas_limits.lat_bottom > self.settings.detail_tile or \
            canvas_limits.lon_right - canvas_limits.lon_left > self.settings.detail_tile:
            self.detail_level = self.settings.detail_degree
        else:
            self.detail_level = self.settings.detail_tile

        current_active_tiles = []
        for tile in self.great_tiles.values():
            if tile.coordinates.lat_top > canvas_limits.lat_bottom and \
                tile.coordinates.lat_bottom < canvas_limits.lat_top and \
                tile.coordinates.lon_left < canvas_limits.lon_right and \
                tile.coordinates.lon_right > canvas_limits.lon_left:
                if self.detail_level == self.settings.detail_zero:
                    current_active_tiles.append(tile)
                else:
                    if not tile.tiles:
                        tile.find_degree_tiles()
                    for dt in tile.tiles.values():
                        if dt.coordinates.lat_top > canvas_limits.lat_bottom - self.settings.detail_degree / 4 and \
                            dt.coordinates.lat_bottom < canvas_limits.lat_top + self.settings.detail_degree / 4 and \
                            dt.coordinates.lon_left < canvas_limits.lon_right + self.settings.detail_degree / 4 and \
                            dt.coordinates.lon_right > canvas_limits.lon_left - self.settings.detail_degree / 4:
                            if self.detail_level == self.settings.detail_degree:
                                current_active_tiles.append(dt)
                            else:
                                if not dt.tiles:
                                    dt.find_tiles()
                                for t in dt.tiles.values():
                                    if t.coordinates.lat_top > canvas_limits.lat_bottom - self.settings.detail_tile / 8 and \
                                        t.coordinates.lat_bottom < canvas_limits.lat_top + self.settings.detail_tile / 8 and \
                                        t.coordinates.lon_left < canvas_limits.lon_right + self.settings.detail_tile / 8 and \
                                        t.coordinates.lon_right > canvas_limits.lon_left - self.settings.detail_tile / 8:
                                        current_active_tiles.append(t)
                                    else:
                                        t.hide()
                        else:
                            dt.hide()

            else:
                tile.hide()

        for tile in current_active_tiles:
            if tile not in self.active_tiles:
                tile.draw()
        for tile in self.active_tiles:
            if tile not in current_active_tiles:
                tile.hide()
        
        self.active_tiles = current_active_tiles
