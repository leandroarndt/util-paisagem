"""
Common classes and constants for scenery.

Constants (a tile is 0.125 degree high):
    METER_RESOLUTION: power of 2 to get 0.82 m/pixel (that is, 2**14)
    METER: one meter converted to tile units (~0.00007)
    RESOLUTIONS: resolution in meters/pixel, from 0.84 (16384 px) to 108 (128 px)
"""
from decimal import Decimal

METER_RESOLUTION = 14 # One tile height has circa 13892 meters, thus 2**14 (16384 pixels)
METER = 1/Decimal(13892.375) # One meter converted to tile units

# meters/pixel, from 0.84 (16384 px) to 108 (128 px)
RESOLUTIONS = {
    14: METER/2**14,
    13: METER/2**13,
    12: METER/2**12,
    11: METER/2**11,
    10: METER/2**10,
    9:  METER/2**9,
    8:  METER/2**8,
    7:  METER/2**7
}
MAX_RES = 14
DOWNLOAD_RES = 10 # Preferred download resolution to compose high-res tiles
MIN_RES = 7

class Coordinates(object):
    """
    Class used to store tile coordinates.
    """
    lat_top: Decimal
    lat_bottom: Decimal
    lon_left: Decimal
    lon_right: Decimal
    lat_median: Decimal
    lon_median: Decimal

    def __init__(self, lat1:Decimal, lat2:Decimal, lon1:Decimal, lon2:Decimal):
        if lat1 > lat2:
            self.lat_top, self.lat_bottom = Decimal(lat1), Decimal(lat2)
        else:
            self.lat_top, self.lat_bottom = Decimal(lat2), Decimal(lat1)
        self.lat_median = Decimal((lat1 + lat2) / 2)
        if lon1 < lon2:
            self.lon_left, self.lon_right = Decimal(lon1), Decimal(lon2)
        else:
            self.lon_left, self.lon_right = Decimal(lon2), Decimal(lon1)
        self. lon_median = Decimal((lon1 + lon2) / 2)
    
    def __str__(self):
        s = f"Latitude: {self.lat_top} to {self.lat_bottom} (median: {self.lat_median})\n"
        s = s + f"Longitude: {self.lon_left} to {self.lon_right} (median: {self.lon_median})"
        return s