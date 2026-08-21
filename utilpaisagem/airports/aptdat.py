import gzip, tempfile, shutil, codecs
from pathlib import Path
from xplane_airports.AptDat import AptDat, Airport

class FGAirports(AptDat):
    def __init__(self, path, *args, **kwargs):
        with tempfile.TemporaryDirectory(prefix='util-paisagem-') as cache:
            with gzip.open(path) as gz_file:
                with open(Path(cache) / 'apt.dat', 'w', encoding='utf-8') as dat_file:
                    contents = gz_file.readline() # FG apt.dat starts with "I"
                    while True:
                        contents = gz_file.read(1024**2)
                        if not contents:
                            break
                        dat_file.write(codecs.decode(contents, 'iso8859-1'))
            super().__init__(Path(cache) / 'apt.dat', *args, **kwargs)
