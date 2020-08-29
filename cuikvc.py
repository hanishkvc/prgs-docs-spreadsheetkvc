#!/usr/bin/env python3
# CursesUI helper routines
# HanishKVC, 2020
#

import curses

me = {
        'scrCols': 10, 'scrRows': 5,
	}


def cstart():
    '''
    Initialise the curses ui
    '''
    stdscr = curses.initscr()
    me['scrRows'], me['scrCols'] = stdscr.getmaxyx()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.clear()
    return stdscr


def cend(scr):
    '''
    Revert the cstart setup
    '''
    curses.nocbreak()
    scr.keypad(False)
    curses.echo()
    curses.endwin()


def cellstr(scr, y, x, msg, attr):
    '''
    Display message onlyy if it is in the current display viewport
    '''
    if ((x < 0) or (x >= me['scrCols'])) or ((y < 0) or (y >= me['scrRows'])) :
        return
    scr.addstr(y, x, msg, attr)


def dlg(scr, msgs, y=0, x=0, attr=curses.A_NORMAL):
    '''
    Show a simple dialog, with the messages passed to it.
    And return a keypress from the user.
    If location not given, then show at top left corner.
    '''
    for i in range(len(msgs)):
        cellstr(scr, y+i, x, msgs[i], attr)
    return scr.getch()


def status(scr, msgs, y=0, x=0, attr=curses.A_NORMAL):
    '''
    Display the messages passed to it at a given location.
    If location not given, then show at top left corner.
    '''
    for i in range(len(msgs)):
        cellstr(scr, y+i, x, msgs[i], attr)
    scr.refresh()




# vim: set sts=4 expandtab: #
