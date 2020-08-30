#!/usr/bin/env python3
# CursesUI helper routines
# HanishKVC, 2020
#

import curses

me = {
        'scrCols': 10, 'scrRows': 5,
	}

GLOGFILE=None
GERRFILE=None


def dprint(sMsg, file=file, end="\n"):
    '''
    debug print to specified file, if not None
    '''
    if file != None:
        print(sMsg, end=end, file=toFile)


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


def cellstr(scr, y, x, msg, attr, clipToScreen=True):
    '''
    Display message onlyy if it is in the current display viewport
    '''
    if ((x < 0) or (x >= me['scrCols'])) or ((y < 0) or (y >= me['scrRows'])) :
        return
    if clipToScreen:
        msgLen = len(msg)
        msgSpace = me['scrCols'] - x
        if msgLen > msgSpace:
            msgLen = msgSpace
        msg = msg[:msgLen]
    dprint("cellstr:{},{}:{}".format(y, x, msg), file=GLOGFILE)
    scr.addstr(y, x, msg, attr)


def dlg(scr, msgs, y=0, x=0, attr=curses.A_NORMAL, border=False, newwin=False):
    '''
    Show a simple dialog, with the messages passed to it.
    And return a keypress from the user.
    If location not given, then show at top left corner.
    '''
    if border or newwin:
        borderWidth = 0
        for i in range(len(msgs)):
            msgLen = len(msgs[i])
            if borderWidth < msgLen:
                borderWidth = msgLen
        borderWidth += 2
        revAttr = curses.A_REVERSE
        if attr == curses.A_REVERSE:
            revAttr = curses.A_NORMAL
    if newwin:
        scr = curses.newwin(len(msgs), borderWidth, y, x)
        scr.clear()
        y = 0
        x = 0
    if border:
        tX = x+1
        borderStr = ""
        for i in range(borderWidth):
            borderStr += " "
        cellstr(scr, y, x, borderStr, revAttr)
        cellstr(scr, y+1, tX, msgs[0], attr)
        cellstr(scr, y+2, x, borderStr, revAttr)
        tY = y+2
    else:
        cellstr(scr, y, x, msgs[0], attr)
        tY = y
        tX = x
    for i in range(1, len(msgs)):
        cellstr(scr, tY+i, tX, msgs[i], attr)
    got = scr.getch()
    scr.clear()
    return got


def status(scr, msgs, y=0, x=0, attr=curses.A_NORMAL):
    '''
    Display the messages passed to it at a given location.
    If location not given, then show at top left corner.
    '''
    for i in range(len(msgs)):
        cellstr(scr, y+i, x, msgs[i], attr)
    scr.refresh()




# vim: set sts=4 expandtab: #
