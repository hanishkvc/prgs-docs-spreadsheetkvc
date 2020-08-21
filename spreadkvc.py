#!/usr/bin/env python3
# A simple ncurses based spreadsheet
# HanishKVC, 2020

import curses

me = {
        'cw': 5, 'ch': 1,
        'nc': 5, 'nr': 5,
        'cc': 1, 'cr': 1,
        }


def cstart():
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.clear()
    return stdscr


def cend(stdscr):
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()


def cellstr(stdscr, y, x, msg, attr):
    stdscr.addstr(y, x*me['cw'], msg, attr)


def cdraw(stdscr):
    for i in range(me['nc']):
        if (i == me['cc']):
            ctype = curses.A_NORMAL
        else:
            ctype = curses.A_REVERSE
        cellstr(stdscr, 0, i, "{}".format(i), ctype)
    for i in range(me['nr']):
        if (i == me['cr']):
            ctype = curses.A_NORMAL
        else:
            ctype = curses.A_REVERSE
        cellstr(stdscr, i, 0, "{}".format(i), ctype)
    stdscr.refresh()


stdscr=cstart()
cdraw(stdscr)
stdscr.getkey()
cend(stdscr)


