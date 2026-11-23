from typing import List, TYPE_CHECKING
from xml.etree import ElementTree
from pathlib import Path

if TYPE_CHECKING:
    from utilpaisagem.airports.aptdat import AptDat
else:
    class AptDat:
        pass
    class FGFP:
        pass

class Airport(object):
    icao:str
    sid:str
    star:str
    transition:str
    runway:str
    # These are not part of the XML file:
    lon:float
    lat:float
    ident:str

class Waypoint(object):
    wp_type:str
    alt_restrict:str
    altitude_ft:float
    ident:str
    icao:str
    lon:float
    lat:float
    radial_deg:float
    distance_nm:float

class FGFP(object):
    """FlightGear flight plan. See https://wiki.flightgear.org/Flightplan_XML_formats
    for details. Use pass `file` argument or use `open` to open a FlightGear XML
    flightplan. fg_airports must be set to an instance of `utilpaisagem.airports.AptDat`."""
    fg_airports:AptDat
    departure:Airport
    destination:Airport
    waypoints:List[Waypoint]

    def __init__(self, file:[str|Path|None], fg_airports:AptDat, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fg_airports = fg_airports
        self.waypoints = []

        if file:
            self.open(file)

    def open(self, file) -> FGFP:
        fp_tree = ElementTree.parse(file)
        try:
            dep = fp_tree.find('departure').find('airport').text
            fg_apt = self.fg_airports.search_by_id(dep)
            self.departure = Airport()
            self.departure.icao, self.departure.ident = dep, dep
            self.departure.lat = float(fg_apt.latitude)
            self.departure.lon = float(fg_apt.longitude)
            self.waypoints.append(self.departure)
        except AttributeError:
            pass
        route = fp_tree.find('route')
        if route:
            for wp in route.findall('wp'):
                try:
                    wp_data = Waypoint()
                    wp_data.lat = float(wp.find('lat').text)
                    wp_data.lon = float(wp.find('lon').text)
                    wp_data.ident = wp.find('ident').text
                    self.waypoints.append(wp_data)
                except AttributeError:
                    pass
        try:
            dest = fp_tree.find('destination').find('airport').text
            fg_apt = self.fg_airports.search_by_id(dest)
            self.departure = Airport()
            self.departure.icao, self.departure.ident = dest, dest
            self.departure.lat = float(fg_apt.latitude)
            self.departure.lon = float(fg_apt.longitude)
            self.waypoints.append(self.departure)
        except AttributeError:
            pass
        try:
            if self.waypoints[0].ident == self.waypoints[1].ident:
                self.waypoints.pop(0)
        except IndexError:
            pass
        if len(self.waypoints) > 1:
            if self.waypoints[-1].ident == self.waypoints[-2].ident:
                self.waypoints.pop(-1)
