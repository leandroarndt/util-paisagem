from tkintermapview import TkinterMapView
from utilpaisagem.scenery.common import Coordinates

class MapWidget(TkinterMapView):
    """TkinterMapView with extra get_canvas_coords() and updated(bool)."""
    updated:bool = True

    def draw_initial_array(self, *args, **kwargs):
        super().draw_initial_array(*args, **kwargs)
        self.updated = True

    def get_canvas_coords(self):
        """Returns a Coordinates object covering the entirety of the map widget area."""
        top, left = self.convert_canvas_coords_to_decimal_coords(0, 0)
        bottom, right = self.convert_canvas_coords_to_decimal_coords(self.width, self.height)
        updated = False
        return Coordinates(lat1=top, lat2=bottom, lon1=left, lon2=right)

    def draw_move(self, *args, **kwrags):
        super().draw_move(*args, **kwargs)
        self.updated = True
    
    def draw_zoom(self, *args, **kwargs):
        super().draw_zoom(*args, **kwargs)
        self.updated = True
