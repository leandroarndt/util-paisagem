import locale, os
if os.name == 'nt':
    try:
        locale.setlocale(locale.LC_ALL, f'{locale.getlocale()[0]}.UTF-8')
        os.environ['LANG'] = f'{locale.getlocale()[0]}.UTF-8'
    except locale.Error:
        locale.setlocale(locale.LC_ALL, '')
import gettext, appdirs, shutil
from pathlib import Path
from utilpaisagem.app_info import resources_path

# Prepare translation files
translation_path = Path(appdirs.user_data_dir('utilpaisagem')) / 'locale'
if translation_path.exists() and not translation_path.is_dir():
    os.unlink(translation_path)
if not translation_path.exists:
    translation_path.mkdir(parents=True)
if not (translation_path.parent / 'translation.sha').exists():
    shutil.copytree(resources_path / 'locale', translation_path, dirs_exist_ok=True)

# Activate translations
translation = gettext.translation('utilpaisagem', translation_path, fallback=True)
translation.install()