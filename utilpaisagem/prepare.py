import locale, os
if os.name == 'nt':
    try:
        locale.setlocale(locale.LC_ALL, f'{locale.getlocale()[0]}.UTF-8')
        os.environ['LANG'] = f'{locale.getlocale()[0]}.UTF-8'
    except locale.Error:
        locale.setlocale(locale.LC_ALL, '')
import gettext, appdirs, shutil
from pathlib import Path
from utilpaisagem.app_info import resources_path, translations_path, string_version

# Prepare translation files
if translations_path.exists() and not translations_path.is_dir():
    os.unlink(translations_path)
if not translations_path.exists:
    translations_path.mkdir(parents=True)
translation_version = None
try:
    with open(translations_path.parent / 'translations.version', 'r') as version:
        translation_version = version.read()
except FileNotFoundError:
    pass
if not (
    (translations_path.parent / 'translations.sha').exists() and
    translation_version == string_version()
):
    shutil.copytree(resources_path / 'locale', translations_path, dirs_exist_ok=True)
    with open(translations_path.parent / 'translations.sha', 'w') as digest:
        digest.truncate()
    with open(translations_path.parent / 'translations.version', 'w') as version:
        version.write(string_version())

# Activate translations
translation = gettext.translation('utilpaisagem', translations_path, fallback=True)
translation.install()