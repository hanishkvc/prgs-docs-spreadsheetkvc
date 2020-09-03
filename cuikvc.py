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


def dprint(sMsg, file=GLOGFILE, end="\n"):
    '''
    debug print to specified file, if not None
    '''
    if file != None:
        print(sMsg, end=end, file=file)


def _screen_size(scr):
    me['scrRows'], me['scrCols'] = scr.getmaxyx()


def cstart():
    '''
    Initialise the curses ui
    '''
    stdscr = curses.initscr()
    _screen_size(stdscr)
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.clear()
    dprint(me, file=GLOGFILE)
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

    if clipToScreen is true, then clip message such that it fits the
    screen horizontally.
    '''
    if ((x < 0) or (x >= me['scrCols'])) or ((y < 0) or (y >= me['scrRows'])) :
        return
    if clipToScreen:
        msgLen = len(msg)
        # Even text cursor going beyond screen after text is written till edge
        # also seems to trigger a exception. So when clipToScreen is true,
        # clip by 1 additional char to take care of this.
        msgSpace = me['scrCols'] - x -1
        if msgLen > msgSpace:
            msgLen = msgSpace
        msg = msg[:msgLen]
    dprint("cellstr:{},{}:[{}]".format(y, x, msg), file=GLOGFILE)
    scr.addstr(y, x, msg, attr)


def _extend_str(strIn, length, filler=' '):
    '''
    Extended the string to given length, if its smaller, by using given filler.
    '''
    strLen = len(strIn)
    strOut = strIn
    for i in range(length-strLen):
        strOut += filler
    return strOut


def dlg(scr, msgsIn, y=0, x=0, attr=curses.A_NORMAL, border=False, newwin=False, clear=True):
    '''
    Show a simple dialog, with the messages passed to it.
    And return a keypress from the user.

    If location not given, then show at top left corner.
    If border, then show a border covering full width above and below 0th message.
    If clear, clear the screen after getting input from user.
        also clear the screen till borderWidth for each line printed.
    borderWidth is the length of the longest message+2.
    '''
    if border or newwin or clear:
        borderWidth = 0
        for i in range(len(msgsIn)):
            msgLen = len(msgsIn[i])
            if borderWidth < msgLen:
                borderWidth = msgLen
        revAttr = curses.A_REVERSE
        if attr == curses.A_REVERSE:
            revAttr = curses.A_NORMAL
    if clear:
        msgs = []
        for i in range(len(msgsIn)):
            msgs.append(_extend_str(msgsIn[i], borderWidth, " "))
    else:
        msgs = msgsIn
    if newwin:
        scr = curses.newwin(len(msgs), borderWidth, y, x)
        scr.clear()
        y = 0
        x = 0
    if border:
        tX = x
        borderStr = ""
        borderStr = _extend_str(borderStr, borderWidth, " ")
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
    if clear:
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
