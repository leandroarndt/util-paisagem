#!.env/bin/python
from pathlib import Path
from pyshortcuts import make_shortcut

make_shortcut(
    script=str(Path(__file__).parent / 'run.py'),
    name='Útil paisagem',
    description='Útil paisagem FlightGear photo scenery',
    terminal=False,
    icon=str(Path(__file__).parent/'resources'/'images'/'utilpaisagem.ico'),
)
