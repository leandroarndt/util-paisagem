from pathlib import Path
from urllib import request
from urllib.error import URLError, ContentTooShortError
from utilpaisagem.scenery.common import Coordinates

class ImageService(object):
    """
    Base class for image services. It has a `download` method, a `description` string,
    a license_link string and an `availability_area` string.
    Each child class should define its strings and a `_url` method, which returns a URL
    from `coordinates`, `width` and `height` parameters.
    """

    description:str
    license_link:str
    availability_area:str
    _max_size:int = 1024

    def _get_url(self, coordinates:Coordinates, width:int, height:int):
        """
        Returns a downloadable URL from `coordinates`, `width` and `height`.
        Should be rewritten for every child class.
        """
        pass

    def _trim(self, coordinates, height:int) -> list:
        """
        Trims image dimensions to be at most self._max_size.
        Returns (width, height).
        """

        if height > self._max_size: height = self._max_size
        width = abs(height * (coordinates.lon_left - coordinates.lon_right) / (coordinates.lat_top - coordinates.lat_bottom))
        if width > self._max_size:
            height = height * self._max_size / width
            width = self._max_size
        
        return width, height

    def download(self, file:Path, coordinates:Coordinates, height:int):
        """
        Downloads an image from `coordinates` with `height` pixels and writes it
        as `file`.

        Args:
            file: full file name with path.
            coordinates: coordinates as a Coordinates instance.
            height: image height in pixels. Width is calculated from this and the
                coordinates latitude/longitude ratio.
        """
        width, height = self._trim(coordinates, height)

        url = self._get_url(coordinates, width, height)

        try:
            response = request.urlretrieve(url, filename=file)
            assert response[1]['Content-Type'] == 'image/png'
        except URLError as e:
            print('URLError:', e)
        except ContentTooShortError:
            print(f'Content too short: "{url}" did not return its full contents.')
        except AssertionError:
            print(f'Failed to download PNG image from "{url}" into "{file}".')

class _ArcGIS(ImageService):
    def __init__(self):
        self.description = 'Worldwide service under restrictive license'
        self.license_link = 'https://www.esri.com/en-us/legal/terms/full-master-agreement'
        self.availability_area = 'Worldwide'
        self._max_size = 4096

    def _get_url(self, coordinates:Coordinates, width:int, height:int) -> str:
        return f'https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/export?bbox={coordinates.lon_left},{coordinates.lat_top},{coordinates.lon_right},{coordinates.lat_bottom}&bboxSR=4326&size={width},{height}&format=png24&f=image'
