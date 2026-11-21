from utilpaisagem import prepare

if __name__ == '__main__':
    from utilpaisagem.app_info import resources_path
    from utilpaisagem.gui import main
    app = main.MainWindow(resources_path)
    app.window.mainloop()