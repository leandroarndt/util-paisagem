from typing import MutableMapping
from pathlib import Path
from urllib import request
from numbers import Number
from collections import OrderedDict
from urllib.error import URLError, ContentTooShortError
from utilpaisagem.scenery.common import Coordinates, DOWNLOAD_RES, MIN_RES

class ImageService(object):
    """
    Base class for image services. It has a `download` method, a `description` string,
    a license_link string and an `availability_area` string. ImageService objects may
    be compared and ordered by their names.

    Each child class should define its strings and a `_url` method, which returns a URL
    from `coordinates`, `width` and `height` parameters.
    """

    name:str
    description:str
    license_link:str
    availability_area:str
    max_size:int = 2**DOWNLOAD_RES

    def __gt__(self, other):
        return self.name > other.name
    
    def __ge__(self, other):
        return self.name >= other.name

    def __eq__(self, other):
        return self.name == other.name
    
    def __le__(self, other):
        return self.name <= other.name
    
    def __lt__(self, other):
        return self.name < other.name

    def _get_url(self, coordinates:Coordinates, width:int, height:int):
        """
        Returns a downloadable URL from `coordinates`, `width` and `height`.
        Should be rewritten for every child class.
        """
        pass

    def _trim(self, coordinates, height:int) -> list:
        """
        Trims image dimensions to be at most self.max_size.
        Returns (width, height).
        """

        if height > self.max_size: height = self.max_size
        width = abs(height * (coordinates.lon_left - coordinates.lon_right) / (coordinates.lat_top - coordinates.lat_bottom))
        if width > self.max_size:
            height = height * self.max_size / width
            width = self.max_size
        
        return int(width), int(height)

    def can_download(self, coordinates:Coordinates) -> bool:
        """
        Tells wether `coordinates` can be downloaded by the image service.
        This method must be overriden by each `ImageService` class.

        Arguments:
            coordinates(Coordinates): coordinates to be tested for download
        """
        return False

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

        exception = None
        try:
            response = request.urlretrieve(url, filename=file)
            assert response[1]['Content-Type'] == 'image/png'
        except URLError as e:
            exception = e
            print('URLError:', e)
        except ContentTooShortError as e:
            exception = e
            print(f'Content too short: "{url}" did not return its full contents.')
        except AssertionError as e:
            exception = e
            print(f'Failed to download PNG image from "{url}" into "{file}".')
        else:
            return None, True
        if height > 2**MIN_RES:
            print('Retrying download with lower resolution...')
            return exception, self.download(file, coordinates, height/2)[1]
        return exception, False

class _ArcGIS(ImageService):
    def __init__(self):
        self.name = 'ArcGIS'
        self.description = 'ArcGIS worldwide service under restrictive license'
        self.license_link = 'https://www.esri.com/en-us/legal/terms/full-master-agreement'
        self.availability_area = _('Worldwide')
        self.max_size = 4096

    def can_download(self, coordinates:Coordinates) -> bool:
        if coordinates.lat_top > 89 or coordinates.lat_bottom < -89:
            return False
        return True

    def _get_url(self, coordinates:Coordinates, width:int, height:int) -> str:
        return f'https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/export?bbox={coordinates.lon_left},{coordinates.lat_top},{coordinates.lon_right},{coordinates.lat_bottom}&bboxSR=4326&imageSR=4326&size={width},{height}&format=png24&f=image'

class _PNOA(ImageService):
    def __init__(self):
        self.name = 'PNOA'
        self.description = 'Plan Nacional de Ortofotografía Aérea by Instituto Geográfico Nacional (CC-BY 4.0)'
        self.license_link = 'https://creativecommons.org/licenses/by/4.0/'
        self.availability_area = _('Spain')
    
    def can_download(self, coordinates:Coordinates) -> bool:
        # https://www.ign.es/wms-inspire/pnoa-ma?Request=GetCapabilities&Service=WMS
        return coordinates.lon_left >= -19.0 and \
            coordinates.lat_bottom >= 27.0 and \
            coordinates.lon_right <= 5.0 and \
            coordinates.lat_top <= 44.0
    
    def _get_url(self, coordinates:Coordinates, width:int, height:int) -> str:
        # return f'https://www.ign.es/wms-inspire/pnoa-ma?SERVICE=WMS|VERSION=1.1.1|REQUEST=GetMap|LAYERS=OI.OrthoimageCoverage|SRS=EPSG:4326|BBOX={coordinates.lon_left},{coordinates.lat_top},{coordinates.lon_right},{coordinates.lat_bottom}|WIDTH={width}|HEIGHT={height}|FORMAT=image/png'
        return f'https://www.ign.es/wms-inspire/pnoa-ma?SERVICE=WMS|VERSION=1.3.0|REQUEST=GetMap|LAYERS=OI.OrthoimageCoverage|CRS=EPSG:4326|BBOX={coordinates.lon_left},{coordinates.lat_top},{coordinates.lon_right},{coordinates.lat_bottom}|WIDTH={width}|HEIGHT={height}|FORMAT=image/png'

class _USGS(ImageService):
    def __init__(self):
        self.name = 'USGS'
        self.description = 'U.S. Geographical Surveys (public domain)'
        self.license_link = 'https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits'
        self.availability_area = _('USA')
    
    #TODO
    def can_download(self, coordinates:Coordinates) -> bool:
        return True
    
    def _get_url(self, coordinates:Coordinates, width:int, height:int) -> str:
        return f'https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/export?bbox={coordinates.lon_left},{coordinates.lat_top},{coordinates.lon_right},{coordinates.lat_bottom}&bboxSR=4326&size={height},{width}&imageSR=4326&format=png24&f=image'

class _Bayern(ImageService):
    def __init__(self):
        self.name = 'Geobaisdaten Bayern'
        self.description = 'Kostenfreie Geodaten der Bayerischen Vermessungsverwaltung'
        self.license_link = 'https://creativecommons.org/licenses/by/4.0/deed.de'
        self.availability_area = _('Bavaria (Deutschland)')

    #TODO
    def can_download(self, coordinates:Coordinates) -> bool:
        return True
    
    def _get_url(self, coordinates:Coordinates, width:int, height:int) -> str:
        return f''

# There is no need for a singleton. This list is only a centralized place
# for image service classes stored in order to facilitate GUI development.
_IMAGE_SERVICES = [
    _ArcGIS(),
    # _PNOA(), # Not working. No photoscenery tool for FG can get its images
    _USGS(),
    # _Bayern(), # TODO
]

IMAGE_SERVICES:MutableMapping[str, ImageService] = OrderedDict()
_IMAGE_SERVICES.sort()
for im in _IMAGE_SERVICES:
    IMAGE_SERVICES[im.name] = im