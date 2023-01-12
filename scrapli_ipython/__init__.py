def load_ipython_extension(ipython):
    from .scrapli_ipython import ScrapliMagics
    ipython.register_magics(ScrapliMagics)
