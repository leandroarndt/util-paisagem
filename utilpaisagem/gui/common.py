# format_status
from datetime import datetime
from babel.dates import LOCALTZ, format_datetime
# Settings
import configparser, ast, appdirs
from pathlib import Path
from enum import Enum
from utilpaisagem.scenery.common import DOWNLOAD_RES, MAX_RES, MIN_RES

# GUI defaults
PADDING = 6

# Text formatting

def format_status(text:str, obj) -> str:
    return f'{format_datetime(datetime.now(), format='short')} ({obj.__class__.__name__}): {text}'


# Preferences

class _Sections(Enum):
    DEFAULT = 'DEFAULT'
    PATH = 'PATH'
    DOWNLOAD = 'DOWNLOAD'
    RANGE = 'RANGE'

class Settings(object):
    """
    Settings parsing and storage singleton. The settings file is saved at the user's config folder
    ("~/.config/utilpaisagem/utilpaisagem.ini" on Linux) and only one `configparser` instance is
    shared app-wide.

    *ATTENTION:* changes must be saved in order to be restored in the next session!

    Attributes and default values, if any:
        orthophotos_folder:str = ''
        tile_threads:int = 4
        image_threads:int = 4
        radius:int = 50
        download_res = DOWNLOAD_RES # 10 from `utilpaisagem.gui.common`
        distances = {
            8: DOWNLOAD_RES + 2,
            20: DOWNLOAD_RES + 1,
            40100000: DOWNLOAD_RES,
        }
    """
    _file:Path
    _settings:configparser.ConfigParser
    fgdata_folder:str = Path.home() / '.fgdata'
    orthophotos_folder:str = '%(fgdata_folder)s/utilpaisagem/Orthophotos'
    tile_threads:int = 4
    image_threads:int = 4
    radius:int = 50
    download_res = DOWNLOAD_RES
    distances = {
        8: DOWNLOAD_RES + 2,
        20: DOWNLOAD_RES + 1,
        40100000: DOWNLOAD_RES,
    }
        
    _key_section = {
        'fgdata_folder': _Sections.PATH.value,
        'orthophotos_folder': _Sections.PATH.value,
        'tile_threads': _Sections.DOWNLOAD.value,
        'image_threads': _Sections.DOWNLOAD.value,
        'download_res': _Sections.DOWNLOAD.value,
        'radius': _Sections.RANGE.value,
        'distances': _Sections.RANGE.value,
    }

    def __getattribute__(self, name):
        if name in __class__._key_section:
            try:
                value = __class__._settings[__class__._key_section[name]][name]
                if not isinstance(__class__.__dict__[name], str):
                    return ast.literal_eval(value)
                return value
            except KeyError:
                pass
        return super().__getattribute__(name)


    def __setattr__(self, name, value):
        if name in __class__._key_section:
            __class__._settings[__class__._key_section[name]][name] = str(value)
        else:
            super().__setattr__(name, value)
    
    def __delattr__(self, name):
        if name in self._key_section:
            pass
        else:
            super().__delattr__(name)
    
    def __init__(self):
        self.__class__._file = Path(appdirs.user_config_dir(appname='utilpaisagem')) / 'utilpaisagem.ini'
        if not hasattr(self.__class__, '_settings'):
            create = not self.__class__._file.exists()
            self.__class__._settings = configparser.ConfigParser()
            # if create: # set default values
            for section in _Sections:
                if section.value != 'DEFAULT':
                    self.__class__._settings.add_section(section.value)
            for k, v in self.__class__.__dict__.items():
                try:
                    self.__class__._settings[self.__class__._key_section[k]][k] = str(v)
                except KeyError:
                    pass
            if create:
                if not self.__class__._file.parent.exists():
                    self.__class__._file.parent.mkdir(parents=True)
                with open(self.__class__._file, 'w') as file:
                    self.__class__._settings.write(file)
            else: # read exiting file (possibly with new values)
                self.__class__._settings.read(self.__class__._file)
    
    @classmethod
    def save(cls):
        with open(cls._file, 'w') as file:
            cls._settings.write(file)
