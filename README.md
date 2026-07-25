# Útil paisagem FlightGear Photoscenery

_There's no use of a Moonlight glow...._  
_Or the Peaks where Winter Snows...._  
_What's the use of the waves that will break in the cool of the evening...._  
_What is the Evening?_  
_Without you..._  
_It's Nothing._  
(Tom Jobim and Aloysio de Oliveira, [Useless landscape](https://www.youtube.com/watch?v=dzjH5P2J10E))

And "you", in a flight simulator, is a photo scenery. This project is dedicated to put the player inside a FlightGear airplane with an as useful landscape as possible.

## Installation

First make sure you have [Python 3.13](https://www.python.org/downloads/) or greater installed.
On Linux, run the `install.sh` script in this directory. You may need to provide the Python
binary path to the installation script (e.g.: `source install.sh -p python3.13`). Útil paisagem
can now be run by clicking the newly created application shortcut.

### Other operational systems

While Mac and Windows scripts are not made, do the following inside a terminal window
(`Logo+R` and then `command` on Windows):

1. If you have already installed Python 3.13 or greater, open a terminal window, get into this directory and run Python with the arguments "-m venv .env" (e.g.: `py -m venv .env`)
2. Still inside the terminal, run the proper activation script inside ".env/bin" folder.
3. Run Python with `-m pip install -r requirements.txt` as arguments
(`py -m pip install -r requirements.txt` on Windows).
4. Lastly run shortcut.py (e.g.: `py shortcut.py`).

If everything went fine, you can now run Útil paisagem by clicking on the newly created application shortcut.
