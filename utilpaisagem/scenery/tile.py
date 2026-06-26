from numbers import Number
from decimal import Decimal
from pathlib import Path
import math, tempfile, shutil

from utilpaisagem.scenery.common import Coordinates, DOWNLOAD_RES, MIN_RES, MAX_RES
from utilpaisagem.scenery.downloader import ImageService

class Tile(object):
    """
    Scenery tiles with the corresponding index and coordinates.
    """
    # Index, coordinates and width based on
    # https://web.archive.org/web/20170526193251/http://fgphotoscenery.square7.ch/#howto
    
    index: int
    coordinates: Coordinates
    resolution:int

    def __init__(self, index:int=0, lat:Decimal=Decimal('NaN'), lon:Decimal=Decimal('NaN'), resolution:int=DOWNLOAD_RES):
        """
        New Tile object defined by either index or by coordinates.
        """
        try:
            if index:
                self.index = index
            else:
                self.index = Tile.coordinates_to_index(lat, lon)
            self.coordinates = Tile.index_to_coordinates(self.index)
        except:
            raise ValueError('Invalid parameters. Should be given either index or lat and lon.')
        if  MIN_RES <= resolution <= MAX_RES:
            self.resolution = resolution
        else:
            raise ValueError(f'Invalid resolution. Should be at least {MIN_RES} and at most {MAX_RES}.')

    # TODO
    def _divide(self, n:int):
        """
        Subdivide a tile for download.
        
        Returns:
            tuple: a tuple of tuples withcoordinate quadrants
                ((lat1, lat2, lon1, lon2), (lat1, lat2, lon1, lon2), ...).
        """
        pass

    # TODO
    def _glue(self, path:Path) -> tuple:
        """
        Join images into a single file.
        
        Args:
            path (Path): path to the orthophotos folder, including it.
        """
        pass

    # TODO
    def retrieve(self, path:Path, image_service:ImageService, compress=False, threads:int=1):
        """
        Tests if the image exists and is not needed to regenerate it. If Ok, touch the
        file in order to know that it has been used. The image should be generated again if it is smaller than the demanded
        resolution or there was an error in the previous processing.
        
        Args:
            path (Path): path to the orthophotos folder, including it.
            lat (Decimal): a latitude at the tile.
            lon (Decimal): a longitude at the tile.
            image_service (ImagerService): image downloader
            threads (int): downloading threads
        """

        # Ok? Touch it.
        # Else:
            # divide(TODO)
            # download parts
            # attempt to sanitize download errors (TODO)
            # glue (TODO)
            # compress (TODO)
        with tempfile.TemporaryDirectory(prefix='util-paisagem-') as cache:
            image_service.download(Path(cache) / f'{self.index}.png', self.coordinates, 2**self.resolution)
            shutil.copy(Path(cache) / f'{self.index}.png', path)

    @classmethod
    def tile_width(cls, lat):
        """
        Tile width in degrees according to the latitude
        (FlightGear uses a variable tile width according to the latitude).
        """
        width_table=[[0,0.125],[22,0.25],[62,0.5],[76,1],[83,2],[86,4],[88,8],[89,360],[90,360]]
        for i in range(len(width_table)):
            if abs(lat)>=width_table[i][0] and abs(lat)<width_table[i+1][0]:
                return float (width_table[i][1])

    @classmethod
    def index_to_coordinates(cls, tile_index):
        """
        Converts FlightGear scenery indexes into geographical coordinates.

        Args:
            tile_index (int): scenery tile index

        Returns:
            list: coordinate values as [lat1, lat2, lon1, lon2, middle_lat, middle_lon]
        """
        base_x    = (tile_index>>14) - 180
        base_y    = ((tile_index-((base_x+180)<<14)) >>6) - 90
        y         =  (tile_index-(((base_x+180)<<14)+ ((base_y+90) << 6))) >> 3
        x         =  tile_index-(((((base_x+180)<<14)+ ((base_y+90) << 6))) + (y << 3))
        tile_width = cls.tile_width(base_y)
        return Coordinates(
            (base_y + 0.125 * y),
            base_y + 0.125 * (y+1),
            base_x + x * tile_width,
            base_x + (x+1) * tile_width
        )
    
    @classmethod
    def coordinates_to_index(cls, lat:Number, lon:Number):
        """Converts a coordinate pair into a FlightGear scenery tile index.

        Args:
            lat: latitude
            lon: longitude
        """
        base_y    = math.floor(lat)
        y         = int((lat-base_y)*8)
        tile_width = cls.tile_width(lat)
        base_x    = math.floor(math.floor(lon/tile_width)*tile_width)
        if base_x<-180:
            base_x=-180
        x         = int(math.floor((lon-base_x)/tile_width))
        tile_index = int(((int(math.floor(lon))+180)<<14) + ((int(math.floor(lat))+ 90) << 6) + (y << 3) + x)
        return tile_index
