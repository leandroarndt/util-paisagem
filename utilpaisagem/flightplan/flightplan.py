from typing import List
from pathlib import Path
from utilpaisagem.airports.aptdat import AptDat
from utilpaisagem.flightplan.fgfp import FGFP

class FlightPlanError(Exception):
    pass

class Waypoint(object):
    """Waypoint object with name, latitude and longitude properties."""
    name:str
    lat:float
    lon:float

class FlightPlan(object):
    """Flight plan as a list of waypoints. Use `FlightPlan.open(file:[str|Path], format='fgfp')`
    to open a flight plan file."""
    waypoints:List[Waypoint]
    fg_airports:AptDat

    def __init__(self, fg_airports:AptDat):
        self.waypoints = []
        self.fg_airports = fg_airports

    def open(self, file:[str|Path], format:str='fgfp'):
        self.waypoints = []
        if format == 'fgfp':
            fp = FGFP(file, self.fg_airports)
            self.waypoints = fp.waypoints
        if not self.waypoints:
            raise FlightPlanError(_('Flight plan "{file}" seems to be void!').format(
                file=file,
            ))

