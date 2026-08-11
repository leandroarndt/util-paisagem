import locale
locale.setlocale(locale.LC_ALL, '')
import gettext, os
from pathlib import Path

base_path = Path(__file__).parent
resources_path = base_path / 'resources'

translation = gettext.translation('utilpaisagem', resources_path / 'locale', fallback=True, languages=[locale.getlocale()[0] or 'en_US'])
translation.install()

from utilpaisagem.gui import main

if __name__ == '__main__':
    app = main.MainWindow(resources_path)
    app.window.mainloop()