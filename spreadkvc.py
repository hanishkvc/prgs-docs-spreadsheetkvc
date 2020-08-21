#!/usr/bin/env python3
# A simple ncurses based spreadsheet
# HanishKVC, 2020

import curses

me = {
        'cw': 16, 'ch': 1,
        'scrCols': 10, 'scrRows': 5,
        'nc': 25, 'nr': 5,
        'cc': 3, 'cr': 1,
        }


def cstart():
    stdscr = curses.initscr()
    print(dir(stdscr))
    me['scrRows'], me['scrCols'] = stdscr.getmaxyx()
    print(me)
    exit()
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
    cw = me['cw']
    tmsg = msg[0:cw]
    mlen = len(tmsg)
    if mlen < cw:
        for i in range(cw-mlen):
            tmsg += " "
    stdscr.addstr(y, x*cw, tmsg, attr)


def cellcur(stdscr, y, x):
    stdscr.move(y,x*me['cw'])


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
    cellcur(stdscr, me['cr'], me['cc'])
    stdscr.refresh()


stdscr=cstart()
cdraw(stdscr)
stdscr.getkey()
cend(stdscr)


