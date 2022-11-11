__version__ = '0.0.1'

from .scrapli_ipython import ScrapliMagics
def load_ipython_extension(ipython):
    ipython.register_magics(ScrapliMagics)
