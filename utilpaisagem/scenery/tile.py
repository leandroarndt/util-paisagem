from decimal import Decimal
import math

class Tile(object):
    """Scenery tiles with the corresponding index and coordinates.

    Index, coordinates and width "stolen" from
    https://web.archive.org/web/20170526193251/http://fgphotoscenery.square7.ch/#howto
    """
    index: int
    lat1: Decimal
    lon1: Decimal
    lat2: Decimal
    lon2: Decimal

    def __init__(self, index:int=0, lat:Decimal=Decimal('NaN'), lon:Decimal=Decimal('NaN')):
        """New Tile object defined by either index or by coordinates.
        """
        try:
            if index:
                self.index = index
            else:
                self.index = Tile.coordinates_to_index(lat, lon)
            self.lat1, self.lat2, self.lon1, self.lon2 = Tile.index_to_coordinates(self.index)[:4]
        except:
            raise ValueError

    @classmethod
    def tile_width(cls, lat):
        """Tile width in degrees
        FlightGear has a variable tile width according to the latitutde).
        """
        width_table=[[0,0.125],[22,0.25],[62,0.5],[76,1],[83,2],[86,4],[88,8],[89,360],[90,360]]
        for i in range(len(width_table)):
            if abs(lat)>=width_table[i][0] and abs(lat)<width_table[i+1][0]:
                return float (width_table[i][1])

    @classmethod
    def index_to_coordinates(cls, tile_index):
        base_x    = (tile_index>>14) - 180
        base_y    = ((tile_index-((base_x+180)<<14)) >>6) - 90
        y         =  (tile_index-(((base_x+180)<<14)+ ((base_y+90) << 6))) >> 3
        x         =  tile_index-(((((base_x+180)<<14)+ ((base_y+90) << 6))) + (y << 3))
        tile_width = cls.tile_width(base_y)
        return [
            (base_y + 0.125 * y),
            base_y + 0.125 * (y+1),
            base_x + x * tile_width,
            base_x + (x+1) * tile_width,
            0.5 * (base_y+0.125*y + base_y + 0.125*(y+1)),
            0.5 * (base_x + x * tile_width + base_x + (x+1) * tile_width)]
    
    @classmethod
    def coordinates_to_index(cls, lat, lon):
        base_y    = math.floor(lat)
        y         = int((lat-base_y)*8)
        tile_width = cls.tile_width(lat)
        base_x    = math.floor(math.floor(lon/tile_width)*tile_width)
        if base_x<-180:
            base_x=-180
        x         = int(math.floor((lon-base_x)/tile_width))
        tile_index = int(((int(math.floor(lon))+180)<<14) + ((int(math.floor(lat))+ 90) << 6) + (y << 3) + x)
        return tile_index