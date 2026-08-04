import locale
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