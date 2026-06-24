"""
Common classes for scenery.
"""
from decimal import Decimal

class Coordinates(object):
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