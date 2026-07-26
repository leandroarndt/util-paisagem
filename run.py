import locale
locale.setlocale(locale.LC_ALL, '')
from pathlib import Path
import gettext, os
from utilpaisagem.gui import main

base_path = Path(__file__).parent
resources_path = base_path / 'resources'
print(base_path)

translation = gettext.translation('utilpaisagem', resources_path / 'locale', fallback=True, languages=[locale.getlocale()[0] or 'en_US'])
translation.install()

if __name__ == '__main__':
    app = main.MainWindow(resources_path)
    app.window.mainloop()