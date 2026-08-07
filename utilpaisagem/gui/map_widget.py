from typing import List
import tkinter as tk
from tkintermapview import TkinterMapView
from tkintermapview.canvas_polygon import CanvasPolygon
from utilpaisagem.scenery.common import Coordinates

class MapPolygon(CanvasPolygon):
    def delete(self):
        self.map_widget.canvas.coords(self.canvas_polygon, [(0,0)])
        self.map_widget.canvas.itemconfigure(self.canvas_polygon, state=tk.HIDDEN)

        if self in self.map_widget.canvas_polygon_list:
            self.map_widget.canvas_polygon_list.remove(self)
        if self not in self.map_widget.unused_polygons:
            self.map_widget.unused_polygons.append(self)
    
    def update(self, **kwargs):
        configs = {}
        if 'position_list' in kwargs:
            # self.map_widget.canvas.coords(self.canvas_polygon, kwargs['position_list'])
            self.position_list = kwargs['position_list']
            self.canvas_polygon_positions = []
            self.last_upper_left_tile_pos = None
        if 'data' in kwargs:
            self.data = kwargs['data']
        if 'name' in kwargs:
            self.name = name
        if 'outline_color' in kwargs:
            self.outline_color = kwargs['outline_color']
            configs['outline'] = kwargs['outline_color']
        if 'fill_color' in kwargs:
            self.fill_color = kwargs['fill_color']
            configs['fill'] = self.fill_color
        if 'border_width' in kwargs:
            self.border_width = kwargs['border_width']
            configs['width'] =self.border_width
        if 'command' in kwargs:
            self.command = kwargs['command']
        if 'state' in kwargs:
            configs['state'] = kwargs['state']
        else:
            configs['state'] = tk.NORMAL
        
        self.map_widget.canvas.itemconfigure(self.canvas_polygon, **configs)

        if self.last_upper_left_tile_pos is None:
            self.draw()

class MapWidget(TkinterMapView):
    """TkinterMapView with extra get_canvas_coords() and updated(bool)."""
    updated:bool = True
    unused_polygons:List[CanvasPolygon]

    def __init__(self, position_list, *args, **kwargs):
        self.unused_polygons = []
        super().__init__(*args, **kwargs)

    def set_polygon(self, position_list:List, **kwargs) -> MapPolygon:
        if self.unused_polygons:
            polygon = self.unused_polygons.pop(0)
            polygon.update(position_list=position_list, **kwargs)
        else:
            polygon = MapPolygon(self, position_list, **kwargs)
        polygon.draw()
        self.canvas_polygon_list.append(polygon)
        return polygon

    def draw_initial_array(self, *args, **kwargs):
        super().draw_initial_array(*args, **kwargs)
        self.updated = True

    def get_canvas_coords(self):
        """Returns a Coordinates object covering the entirety of the map widget area."""
        top, left = self.convert_canvas_coords_to_decimal_coords(0, 0)
        bottom, right = self.convert_canvas_coords_to_decimal_coords(self.width, self.height)
        self.updated = False
        return Coordinates(lat1=top, lat2=bottom, lon1=left, lon2=right)

    def draw_move(self, *args, **kwargs):
        super().draw_move(*args, **kwargs)
        self.updated = True
    
    def draw_zoom(self, *args, **kwargs):
        super().draw_zoom(*args, **kwargs)
        self.updated = True
