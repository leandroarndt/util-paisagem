from utilpaisagem import prepare
from utilpaisagem.app_info import resources_path
from utilpaisagem.gui import main

if __name__ == '__main__':
    app = main.MainWindow(resources_path)
    app.window.mainloop()