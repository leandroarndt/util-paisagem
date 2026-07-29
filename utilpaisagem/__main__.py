from pathlib import Path
import gettext
from utilpaisagem.gui import main
from utilpaisagem.app_info import resources_path

translation = gettext.translation('utilpaisagem', resources_path / 'locale', fallback=True)
translation.install()

if __name__ == '__main__':
    app = main.MainWindow(resources_path)
    app.window.mainloop()