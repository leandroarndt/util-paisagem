import appdirs
from pathlib import Path

VERSION = 0
SUBVERSION = 7
REVISION = 0
RC = 0

base_path = Path(__file__).parent.parent
resources_path = base_path / 'resources'
translations_path = Path(appdirs.user_data_dir('utilpaisagem')) / 'locale'

def string_version():
    return f'{VERSION}.{SUBVERSION}.{REVISION}{"rc" + str(RC) if RC else ""}'
