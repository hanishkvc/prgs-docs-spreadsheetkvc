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
    me['scrRows'], me['scrCols'] = stdscr.getmaxyx()
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
    tx = x*cw
    ty = y
    if (tx > me['scrCols']) or (ty > me['scrRows']) :
        return
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


def runlogic(stdscr):
    while True:
        cdraw(stdscr)
        key = stdscr.getch()
        #print(key, me['cr'], me['cc'])
        #print(curses.KEY_UP)
        if (key == curses.KEY_UP):
            me['cr'] -= 1
            if (me['cr'] < 1):
                me['cr'] = 1
        elif (key == curses.KEY_DOWN):
            me['cr'] += 1
            if (me['cr'] > me['nr']):
                me['cr'] = me['nr']
        elif (key == ord('Q')):
            break


stdscr=cstart()
runlogic(stdscr)
cend(stdscr)

