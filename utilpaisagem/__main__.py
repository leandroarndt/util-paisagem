import locale, os
try:
    locale.setlocale(locale.LC_ALL, f'{locale.getlocale()[0]}.UTF-8')
    os.environ['LANG'] = f'{locale.getlocale()[0]}.UTF-8'
except locale.Error:
    locale.setlocale(locale.LC_ALL, '')
import gettext
from pathlib import Path
from utilpaisagem.app_info import resources_path

translation = gettext.translation('utilpaisagem', resources_path / 'locale', fallback=True)
translation.install()

from utilpaisagem.gui import main

if __name__ == '__main__':
    app = main.MainWindow(resources_path)
    app.window.mainloop()