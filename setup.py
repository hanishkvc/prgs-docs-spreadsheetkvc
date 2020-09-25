from distutils.core import setup, Extension

chelper = Extension('chelper',
                    sources = ['chelper.c'])

setup (name = 'C Helpers for SpreadsheetKVC',
       version = '1.0',
       description = 'C helpers for SpreadsheetKVC, a curses based spreadsheet for commandline with authenticated encryption support',
       author_email = 'hanishkvc@gmail.com',
       license = 'gpl',
       ext_modules = [chelper])
