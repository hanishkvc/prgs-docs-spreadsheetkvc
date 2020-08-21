#!/usr/bin/env python3
# A simple ncurses based spreadsheet
# HanishKVC, 2020

import curses

me = {
        'cw': 5, 'ch': 1,
        'nc': 5, 'nr': 5, 
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


def cdraw(stdscr):
    for i in range(me['nc']):
        stdscr.addstr(0, i*me['cw'], "{}".format(i))
    for i in range(me['nr']):
        stdscr.addstr(i, 0, "{}".format(i))
    stdscr.refresh()


stdscr=cstart()
cdraw(stdscr)
stdscr.getkey()
cend(stdscr)


