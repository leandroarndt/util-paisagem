from numbers import Number
from pathlib import Path
from urllib.error import URLError, ContentTooShortError
from queue import Queue
from PIL import Image
import math, tempfile, shutil, os, configparser, ast
from utilpaisagem.scenery.common import Coordinates, DOWNLOAD_RES, MIN_RES, MAX_RES
from utilpaisagem.scenery.image_service import ImageService
from utilpaisagem.gui.common import format_status

class Tile(object):
    """
    Scenery tiles with the corresponding index and coordinates.
    """
    # Index, coordinates and width based on
    # https://web.archive.org/web/20170526193251/http://fgphotoscenery.square7.ch/#howto
    
    index:int
    coordinates:Coordinates
    resolution:int
    upstream_queue:Queue|None

    def __init__(
        self,
        index:int=0,
        lat:Number=float('nan'),
        lon:Number=float('nan'), 
        resolution:int=DOWNLOAD_RES,
        upstream_queue:Queue|None=None,
    ):
        """
        New Tile object defined by either index or by coordinates.
        """
        self.upstream_queue = upstream_queue

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
        if self.upstream_queue is None:
            print(f'Dividing tile in {vertical} lines and {horizontal} columns.')
        else:
            self.upstream_queue.put_nowait(format_status(
                    _('Dividing tile {index} in {vertical} lines and {horizontal} columns.').format(
                    index=self.index,
                    vertical=vertical,
                    horizontal=horizontal
                ), self)
            )
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
        cell_size = (int(size[0]/columns), int(size[1]/lines))
        result:Image = Image.new('RGB', size)
        for line in range(lines):
            for column in range(columns):
                with Image.open(path / f'{base_name}-{line}-{column}.png') as image:
                    if image.size != cell_size:
                        image = image.resize(cell_size)
                    result.paste(image, (cell_size[0]*column, cell_size[1]*line))
        if compress == 'smart' or compress == 'png':
            filename = path / f'{base_name}.png'
            result.save(path / f'{base_name}.png', optimize = True)
            if compress == 'smart' and os.path.getsize(filename) > result.size[0] * result.size[1] * 3 / 6: # DXT1 has a 6:1 compression ratio
                compress = 'dds'
                if self.upstream_queue is None:
                    print('DDS is smaller than optimized PNG.')
                else:
                    self.upstream_queue.put_nowait(format_status(
                        _('Tile {index}: DDS is smaller than optimized PNG.').format(index=self.index),
                        self
                    ))
            elif compress == 'smart':
                if self.upstream_queue is None:
                    print('Optimized PNG is smaller than DDS.')
                else:
                    self.upstream_queue.put_nowait(format_status(
                        _('Tile {index}: optimized PNG is smaller than DDS.').format(index=self.index),
                        self
                    ))
        if compress == 'dds':
            filename = path / f'{base_name}.dds'
            result.save(filename, pixel_format='DXT1')
        return Path(filename)

    def retrieve(self, path:Path, image_service:ImageService, download_res=DOWNLOAD_RES, compress='smart', upstream_queue:Queue=None):
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
            f'{lat_dir}{abs(math.floor(self.coordinates.lat_bottom / 10) * 10):02}') / \
            Path(f'{lon_dir}{abs(math.floor(self.coordinates.lon_left)):03}' + \
            f'{lat_dir}{abs(math.floor(self.coordinates.lat_bottom)):02}')
        # Ok? Touch it.
        # Else:
            # divide
            # download parts
            # attempt to sanitize download errors (partially TODO)
            # glue
            # compress
        if self.upstream_queue is None:
            print(f'Processing tile {self.index} ({self.coordinates.lat_median}, {self.coordinates.lon_median})...')
        else:
            self.upstream_queue.put_nowait(format_status(
                _('Processing tile {index} ({lat_median}, {lon_median})...').format(
                    index=self.index,
                    lat_median=self.coordinates.lat_median,
                    lon_median=self.coordinates.lon_median,
                ),
                self
            ))

        # Verify if exists, resolution is equal or higher and there were no failures
        logpath = Path(path / f'{self.index}.log')
        if logpath.exists():
            log = configparser.ConfigParser()
            log.read(logpath)
            try:
                if int(log['INFO']['resolution']) < self.resolution:
                    if self.upstream_queue is None:
                        print('Previously downloaded file has smaller resolution. Downloading again.')
                    else:
                        self.upstream_queue.put_nowait(format_status(
                            _('Previously downloaded file has smaller resolution. Downloading again.'),
                            self
                        ))
                    raise AssertionError
                if log['INFO']['success'] != 'True' or ast.literal_eval(log['INFO']['failures']) != []:
                    if self.upstream_queue is None:
                        print('Failure on previous download. Downloading again.')
                    else:
                        self.upstream_queue.put_nowait(format_status(
                            _('Failure on previous download. Downloading again.'),
                            self
                        ))
                    raise AssertionError
                if compress != 'smart':
                    if log['INFO']['format'] != compress:
                        if self.upstream_queue is None:
                            print(f'Tile {self.index} has not been saved as a {compress.upper()} file. Downloading again.')
                        else:
                            self.upstream_queue.put_nowait(format_status(
                                _('Tile {index} has not been saved as a {format} file. Downloading again.').format(
                                    index=self.index,
                                    format=compress.upper(),
                                ),
                                self
                            ))
                        Path(path / f'{self.index}.{log["INFO"]["format"]}').unlink()
                        raise AssertionError
                if not Path(path / f"{self.index}.{log['INFO']['format']}").exists():
                    p = (Path(path / f"{self.index}.{log['INFO']['format']}"))
                    if self.upstream_queue is None:
                        print('Previous download was not found where expected ("{p}"). Downloading again.')
                    else:
                        self.upstream_queue.put_nowait(format_status(
                            _('Previous download was not found where expected ("{p}"). Downloading again.').format(p=p),
                            self
                        ))
                    raise AssertionError
                if self.upstream_queue is None:
                    print(f'Tile {self.index} has already been downloaded. Skipping.')
                else:
                    self.upstream_queue.put_nowait(format_status(
                        _('Tile {index} has already been downloaded. Skipping.').format(index=self.index),
                        self
                    ))
                Path(path / f"{self.index}.{log['INFO']['format']}").touch(exist_ok=True)
                Path(path / f"{self.index}.log").touch(exist_ok=True)
                return # skips processing if everything is fine
            except (AssertionError, ValueError, KeyError, FileNotFoundError) as e:
                if not isinstance(e, AssertionError):
                    if self.upstream_queue is None:
                        print(f'Failed to check previous download ("{e}"). Downloading again.')
                    else:
                        self.upstream_queue.put_nowait(format_status(
                            _('Failed to check previous download ("{e}"). Downloading again.').format(e=e),
                            self
                        ))
                # Remove previously downloaded file
                if Path(path / f'{self.index}.png').exists():
                    Path(path / f'{self.index}.png').unlink()
                if Path(path / f'{self.index}.dds').exists():
                    Path(path / f'{self.index}.dds').unlink()

        # Download
        divisions = self._divide(image_service, download_res)
        errors = 0
        failures = []
        try:
            with tempfile.TemporaryDirectory(prefix='util-paisagem-') as cache:
                # Download
                total = len(divisions) * len(divisions[0])
                current = 1
                for line in range(len(divisions)):
                    for cell in range(len(divisions[line])):
                        if self.upstream_queue is None:
                            text = f'Downloading image {current}/{total}...'
                            print(text, end='', flush=True)
                        else:
                            self.upstream_queue.put_nowait(format_status(
                                _('Downloading image {current}/{total} of tile {index}...').format(
                                    current=current,
                                    total=total,
                                    index=self.index
                                ),
                                self
                            ))
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
                        elif not self.upstream_queue:
                            print('\b'*len(text), end='', flush=True)
                if self.upstream_queue is None:
                    print(f'Downloaded tile {self.index}.     ')
                else:
                    self.upstream_queue.put_nowait(format_status(
                        _('Downloaded tile {index}.').format(index=self.index),
                        self
                    ))

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
                if self.upstream_queue is None:
                    print(f'Tile {self.index}\'s photographic scenery placed at {path}.')
                else:
                    self.upstream_queue.put_nowait(format_status(
                        _('Tile {index}\'s photographic scenery placed at {path}.').format(
                            index=self.index,
                            path=path
                        ),
                        self
                    ))

                # Write log
                log = configparser.ConfigParser()
                log['INFO'] = {
                    'resolution': self.resolution,
                    'format': filename.suffix[1:],
                    'success': errors == 0,
                    'lines': len(divisions),
                    'columns': len(divisions[0]),
                    'failures': failures,
                }
                with open(path / f'{self.index}.log', 'w') as logfile:
                    log.write(logfile)

        except (URLError, ContentTooShortError) as e:
            if self.resolution > MIN_RES:
                if self.upstream_queue is None:
                    print(f'Error downloading cell {self.index}[{line}][{cell}]: {e}.')
                else:
                    self.upstream_queue.put_nowait(format_status(
                        _('Error downloading cell {index}[{line}][{cell}]: {e}.').format(
                            index=self.index,
                            line=line,
                            cell=cell,
                            e=e,
                        ),
                        self
                    ))
                #self.resolution -= 1
                #self.retrieve(path, image_service, download_res-1, compress)
            else:
                if self.upstream_queue is None:
                    print(f'Error downloading cell {self.index}[{line}][{cell}]: {e}.')
                else:
                    self.upstream_queue.put_nowait(format_status(
                        _('Error downloading cell {index}[{line}][{cell}]: {e}.').format(
                            index=self.index,
                            line=line,
                            cell=cell,
                            e=e,
                        ),
                        self
                    ))
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
