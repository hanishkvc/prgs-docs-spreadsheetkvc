#!/usr/bin/env python3
# A simple ncurses based spreadsheet
# HanishKVC, 2020

import curses

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

stdscr=cstart()
stdscr.getkey()
cend(stdscr)


