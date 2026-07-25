from pathlib import Path
import gettext
from utilpaisagem.gui import main

base_path = Path(__file__).parent
resources_path = base_path / 'resources'
print(base_path)

translation = gettext.translation('utilpaisagem', resources_path / 'locale', fallback=True)
translation.install()

if __name__ == '__main__':
    app = main.MainWindow(resources_path)
    app.window.mainloop()