from numbers import Number
from pathlib import Path
from urllib.error import URLError, ContentTooShortError
from PIL import Image
import math, tempfile, shutil, os

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

    def __init__(self, index:int=0, lat:Number=float('nan'), lon:Number=float('nan'), resolution:int=DOWNLOAD_RES):
        """
        New Tile object defined by either index or by coordinates.
        """
        if not index and (math.isnan(lat) or math.isnan(lon)):
            raise ValueError('Invalid parameters. Should be given either index or lat and lon.')
        if index:
            self.index = index
        else:
            self.index = Tile.coordinates_to_index(lat, lon)
        self.coordinates = Tile.index_to_coordinates(self.index)
        self.proportion = (self.coordinates.lon_right - self.coordinates.lon_left) / 0.125 # Width / height
        if  MIN_RES <= resolution <= MAX_RES:
            self.resolution = resolution
        else:
            raise ValueError(f'Invalid resolution. Should be at least {MIN_RES} and at most {MAX_RES}.')

    def __repr__(self):
        return f'<{self.__class__.__name__}(lat={self.coordinates.lat_median}, lon={self.coordinates.lon_median})>'
    
    def __hash__(self):
        return self.index * 100 + self.resolution
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.index == other.index and self.resolution == other.resolution
        return False

    def _divide(self, image_service:ImageService, download_res:int) -> list:
        """
        Subdivide a tile for download based on image_service's maximum resolution
        and default download resolution. Each resulting cell will have at most
        default resolution height and image services's maximum resolution width.

        Arguments:
            image_service(ImageService): an object with max_size as resolution limit
            download_res: the exponent of two of the resolution (e.g. 1024 = 2**10;
                download_res will be 10)

        Returns:
            list: a list of lists of Coordinate objects in an xy grid
                ((coord1x1, coord1x2 ...), (coord2x1, coord2x2 ...), ...)
        """
        if download_res > self.resolution: download_res = self.resolution
        vertical = 2 ** (self.resolution - download_res)
        full_width = self.proportion * 2**self.resolution # Full image width
        if full_width / vertical > image_service.max_size:
            horizontal = int(full_width // image_service.max_size)
        else:
            horizontal = vertical
        print(f'Dividing tile in {vertical} lines and {horizontal} columns.')
        height = 0.125 / vertical
        if self.coordinates.lat_top <= 0:
            height = -height
        width = (self.coordinates.lon_right - self.coordinates.lon_left) / horizontal
        return [[Coordinates (
            lat1=self.coordinates.lat_top + y*height,
            lon1=self.coordinates.lon_left + x*width,
            lat2=self.coordinates.lat_top + y*height + height,
            lon2=self.coordinates.lon_left + x*width + width
            ) for x in range(horizontal)] for y in range(vertical)]

    def _glue(self, path:Path, base_name:str, lines:int, columns:int, size:[tuple,list], compress='smart') -> Path:
        """
        Join images into a single file. Returns path to file.
        
        Args:
            path(Path): path to the orthophotos folder, including it.
            base_name(str): base of the file name.
            lines(int): number of image lines.
            columns: number of image columns.
            size: image size (integer width x height)
        """
        result:Image = Image.new('RGB', size)
        for line in range(lines):
            for column in range(columns):
                with Image.open(path / f'{base_name}-{line}-{column}.png') as image:
                    result.paste(image, (int(size[0]/columns*column), int(size[1]/lines*line)))
        if compress == 'smart' or compress == 'png':
            filename = path / f'{base_name}.png'
            result.save(path / f'{base_name}.png', optimize = True)
            if compress == 'smart' and os.path.getsize(filename) > result.size[0] * result.size[1] * 3 / 6: # DXT1 has a 6:1 compression ratio
                compress = 'dds'
                print('DDS is smaller than optimized PNG.')
            elif compress == 'smart':
                print('Optimized PNG is smaller than DDS.')
        if compress == 'dds':
            filename = path / f'{base_name}.dds'
            result.save(filename, pixel_format='DXT1')
        return Path(filename)

    def retrieve(self, path:Path, image_service:ImageService, download_res=DOWNLOAD_RES, compress='smart'):
        """
        Tests if the image exists and is not needed to regenerate it. If Ok, touch the
        file in order to know that it has been used. The image should be generated again if it is smaller than the demanded
        resolution or there was an error in the previous processing.
        
        Args:
            path (Path): path to the orthophotos folder, including it.
            image_service (ImagerService): image downloader
            download_res(int): exponent of two representing vertical image size
            compress(str): compression method, either 'png', 'dds' or 'smart'. Defaults to 'smart'
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
            # divide
            # download parts
            # attempt to sanitize download errors (partially TODO)
            # glue
            # compress
        print(f'Processing tile {self.index} ({self.coordinates.lat_median}, {self.coordinates.lon_median})...')
        divisions = self._divide(image_service, download_res)
        try:
            with tempfile.TemporaryDirectory(prefix='util-paisagem-') as cache:
                # Download
                total = len(divisions) * len(divisions[0])
                current = 1
                errors = 0
                failures = []
                for line in range(len(divisions)):
                    for cell in range(len(divisions[line])):
                        text = f'Downloading image {current}/{total}...'
                        print(text, end='', flush=True)
                        exception, done = image_service.download(
                            Path(cache) / f'{self.index}-{line}-{cell}.png',
                            divisions[line][cell],
                            2**download_res
                        )
                        current += 1
                        if exception is not None:
                            errors += 1
                            if not done:
                                failures.append((line, cell))
                        else:
                            print('\b'*len(text), end='', flush=True)
                print(f'Downloaded tile {self.index}.     ')

                filename = self._glue(
                    path=Path(cache),
                    base_name=str(self.index),
                    lines=len(divisions),
                    columns=len(divisions[0]),
                    size=(int(2**self.resolution*self.proportion), int(2**self.resolution)),
                    compress=compress
                )

                #Move
                if not path.is_dir():
                    path.mkdir(parents=True)
                shutil.copy(filename, path)
                print(f'Tile {self.index}\'s photographic scenery placed at {path}.')
        except (URLError, ContentTooShortError) as e:
            if self.resolution > MIN_RES:
                print(f'Error downloading cell {self.index}[{line}][{cell}]: {e}.')
                #self.resolution -= 1
                #self.retrieve(path, image_service, download_res-1, compress)
            else:
                print(f'Error downloading cell {self.index}[{line}][{cell}]: {e}.')
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
                return width_table[i][1]

    @classmethod
    def index_to_coordinates(cls, tile_index):
        """
        Converts FlightGear scenery indexes into geographical coordinates.

        Args:
            tile_index (int): scenery tile index

        Returns:
            Coordinates instance
        """
        base_x    = (tile_index>>14) - 180
        base_y    = ((tile_index-((base_x+180)<<14)) >>6) - 90
        y         =  (tile_index-(((base_x+180)<<14)+ ((base_y+90) << 6))) >> 3
        x         =  tile_index-(((((base_x+180)<<14)+ ((base_y+90) << 6))) + (y << 3))
        tile_width = cls.tile_width(base_y)
        return Coordinates(
            lat1=(base_y + 0.125 * y),
            lat2=base_y + 0.125 * (y+1),
            lon1=base_x + x * tile_width,
            lon2=base_x + (x+1) * tile_width
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
