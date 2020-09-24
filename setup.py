from distutils.core import setup, Extension

csvload = Extension('csvload',
                    sources = ['csvload.c'])

setup (name = 'Helper for SpreadsheetKVC',
       version = '1.0',
       description = 'Allow loading csv lines by SpreadsheetKVC, a curses based spreadsheet for commandline with authenticated encryption support',
       author_email = 'hanishkvc@gmail.com',
       license = 'gpl',
       ext_modules = [csvload])
