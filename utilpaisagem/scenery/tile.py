from decimal import Decimal
from pathlib import Path
from urllib.error import URLError, ContentTooShortError
import math, tempfile, shutil

from utilpaisagem.scenery.common import Coordinates, DOWNLOAD_RES, MIN_RES, MAX_RES
from utilpaisagem.scenery.image_service import ImageService

class Tile(object):
    """
    Scenery tiles with the corresponding index and coordinates.
    """
    # Index, coordinates and width based on
    # https://web.archive.org/web/20170526193251/http://fgphotoscenery.square7.ch/#howto
    
    index:int
    coordinates:Coordinates
    resolution:int

    def __init__(self, index:int=0, lat:Decimal=Decimal('NaN'), lon:Decimal=Decimal('NaN'), resolution:int=DOWNLOAD_RES):
        """
        New Tile object defined by either index or by coordinates.
        """
        lat, lon = Decimal(lat), Decimal(lon)
        if not index and (Decimal.is_nan(lat) or Decimal.is_nan(lon)):
            raise ValueError('Invalid parameters. Should be given either index or lat and lon.')
        if index:
            self.index = index
        else:
            self.index = Tile.coordinates_to_index(lat, lon)
        self.coordinates = Tile.index_to_coordinates(self.index)
        if  MIN_RES <= resolution <= MAX_RES:
            self.resolution = resolution
        else:
            raise ValueError(f'Invalid resolution. Should be at least {MIN_RES} and at most {MAX_RES}.')

    def __repr__(self):
        return f'<{self.__class__.__name__}(lat={self.coordinates.lat_median}, lon={self.coordinates.lon_median})>'
    
    def __hash__(self):
        return self.index
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.index == other.index
        return False

    def _divide(self, image_service:ImageService, download_res:int) -> tuple:
        """
        Subdivide a tile for download based on image_service's maximum resolution
        and default download resolution. Each resulting cell will have at most
        default resolution height and image services's maximum resolution width.

        Arguments:
            image_service(ImageService): an object with max_size as resolution limit
            download_res: the exponent of two of the resolution (e.g. 1024 = 2**10;
                download_res will be 10)

        Returns:
            tuple: a tuple of tuples of Coordinate objects in an xy grid
                ((coord1x1, coord1x2 ...), (coord2x1, coord2x2 ...), ...)
        """
        if download_res > self.resolution: download_res = self.resolution
        vertical = 2 ** (self.resolution - download_res)
        tw = self.coordinates.lon_right - self.coordinates.lon_left # This tile width
        proportion = tw / Decimal(0.125) # Width / height
        full_width = proportion * 2**self.resolution # Full image width
        if full_width / vertical > image_service.max_size:
            horizontal = int(full_width // image_service.max_size)
        else:
            horizontal = vertical
        print(f'Dividing tile in {vertical} lines and {horizontal} columns.')
        height = Decimal(0.125) / vertical
        width = tw / horizontal
        return [[Coordinates (
            lat1=self.coordinates.lat_top + y*height,
            lon1=self.coordinates.lon_left + x*width,
            lat2=self.coordinates.lat_top + y*height + height,
            lon2=self.coordinates.lon_left + x*width + width
            ) for x in range(horizontal)] for y in range(vertical)]

    # TODO
    def _glue(self, path:Path) -> tuple:
        """
        Join images into a single file.
        
        Args:
            path (Path): path to the orthophotos folder, including it.
        """
        pass

    # TODO
    def retrieve(self, path:Path, image_service:ImageService, compress=False):
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
        # Path directions
        if self.coordinates.lat_median > 0:
            lat_dir = 'n'
        else:
            lat_dir = 's'
        if self.coordinates.lon_median > 0:
            lon_dir = 'e'
        else:
            lon_dir = 'w'
        path = path / Path(f'{lon_dir}{abs(math.floor(self.coordinates.lon_left/10)) * 10:03}' + \
            f'{lat_dir}{abs(math.floor(self.coordinates.lat_bottom / 10) * 10)}') / \
            Path(f'{lon_dir}{abs(math.floor(self.coordinates.lon_left)):03}' + \
            f'{lat_dir}{abs(math.floor(self.coordinates.lat_bottom))}')
        # Ok? Touch it.
        # Else:
            # divide(TODO)
            # download parts
            # attempt to sanitize download errors (TODO)
            # glue (TODO)
            # compress (TODO)
        
        try:
            with tempfile.TemporaryDirectory(prefix='util-paisagem-') as cache:
                image_service.download(Path(cache) / f'{self.index}.png', self.coordinates, 2**self.resolution)
                if not path.is_dir():
                    path.mkdir(parents=True)
                shutil.copy(Path(cache) / f'{self.index}.png', path)
                print(f'Downloaded tile {self.index} into {path}.')
        except (URLError, ContentTooShortError) as e:
            if self.resolution > MIN_RES:
                print(f'Error downloading tile {self.index}: {e}. Will retry with reduced resolution.')
                self.resolution -= 1
                self.retrieve(path, image_service, compile, threads)
            else:
                print(f'Error downloading tile {self.index}: {e}.')
                # TODO: download wider area and crop; use neighboring image, if any

    @classmethod
    def tile_width(cls, lat):
        """
        Tile width in degrees according to the latitude
        (FlightGear uses a variable tile width according to the latitude).
        """
        width_table=[[0,0.125],[22,0.25],[62,0.5],[76,1],[83,2],[86,4],[88,8],[89,360],[90,360]]
        for i in range(len(width_table)):
            if abs(lat)>=width_table[i][0] and abs(lat)<width_table[i+1][0]:
                return Decimal(width_table[i][1])

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
    def coordinates_to_index(cls, lat:Decimal, lon:Decimal):
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
