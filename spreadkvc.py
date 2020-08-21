#!/usr/bin/env python3
# A simple ncurses based spreadsheet
# HanishKVC, 2020

import sys
import curses

me = {
        'cellWidth': 16, 'cellHeight': 1,
        'scrCols': 10, 'scrRows': 5,
        'numCols': 25, 'numRows': 5,
        'dispCols': 5, 'dispRows': 5,
        'curCol': 1, 'curRow': 1,
        'viewColStart': 0, 'viewRowStart': 0,
        'fixedCols': 1, 'fixedRows': 0,
        }


def cstart():
    stdscr = curses.initscr()
    me['scrRows'], me['scrCols'] = stdscr.getmaxyx()
    me['dispRows'] = me['scrRows'] - 1
    me['dispCols'] = int(me['scrCols'] / me['cellWidth']) - 1
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


def cellpos(row, col):
    if (col < me['fixedCols']):
        x = col * me['cellWidth']
    elif (col < me['viewColStart']):
        x = -1
    else:
        x = ((col-1) - me['viewColStart']) * me['cellWidth']
        x += me['fixedCols']*me['cellWidth']
    y = row
    print("cellpos: {},{} => {},{}".format(row,col,y,x), file=sys.stderr)
    return y, x


def cellstr(stdscr, y, x, msg, attr):
    cellWidth = me['cellWidth']
    tmsg = msg[0:cellWidth]
    mlen = len(tmsg)
    if mlen < cellWidth:
        for i in range(cellWidth-mlen):
            tmsg += " "
    ty,tx = cellpos(y,x)
    if ((tx < 0) or ((tx+cellWidth) > me['scrCols'])) or (ty > me['scrRows']) :
        return
    print("cellstr: {},{} = {}".format(ty, tx, tmsg), file=sys.stderr)
    stdscr.addstr(ty, tx, tmsg, attr)


def cellcur(stdscr, y, x):
    ty,tx = cellpos(y,x)
    if ((tx <0) or (tx > me['scrCols'])) or (ty > me['scrRows']) :
        return
    stdscr.move(ty,tx)


def cellcur_left():
    me['curCol'] -= 1
    if (me['curCol'] < 0):
        me['curCol'] = 0
    if (me['viewColStart'] > me['curCol']):
        me['viewColStart'] = me['curCol']


def cellcur_right():
    me['curCol'] += 1
    if (me['curCol'] > me['numCols']):
        me['curCol'] = me['numCols']
    if (me['curCol'] > me['dispCols']):
        me['viewColStart'] = me['curCol'] - me['dispCols']
        print("cellcur_right:adjust viewport:{}".format(me), file=sys.stderr)


def cdraw(stdscr):
    #stdscr.clear()
    colStart = me['viewColStart']
    colEnd = colStart + me['dispCols']
    if (colEnd > me['numCols']):
        colEnd = me['numCols']
    print("cdraw: cols {} to {}".format(colStart, colEnd), file=sys.stderr)
    for i in range(colStart, colEnd+1):
        if (i == me['curCol']):
            ctype = curses.A_NORMAL
        else:
            ctype = curses.A_REVERSE
        cellstr(stdscr, 0, i, "{}".format(i), ctype)
    for i in range(me['numRows']+1):
        if (i == me['curRow']):
            ctype = curses.A_NORMAL
        else:
            ctype = curses.A_REVERSE
        cellstr(stdscr, i, 0, "{}".format(i), ctype)
    for r in range(1, me['numRows']+1):
        for c in range(1, me['numCols']+1):
            cellstr(stdscr, r, c, "{},{}".format(r,c), curses.A_NORMAL)
    cellcur(stdscr, me['curRow'], me['curCol'])
    stdscr.refresh()


def runlogic(stdscr):
    while True:
        cdraw(stdscr)
        key = stdscr.getch()
        if (key == curses.KEY_UP):
            me['curRow'] -= 1
            if (me['curRow'] < 1):
                me['curRow'] = 1
        elif (key == curses.KEY_DOWN):
            me['curRow'] += 1
            if (me['curRow'] > me['numRows']):
                me['curRow'] = me['numRows']
        elif (key == curses.KEY_LEFT):
            cellcur_left()
        elif (key == curses.KEY_RIGHT):
            cellcur_right()
        elif (key == ord('Q')):
            break


stdscr=cstart()
try:
    runlogic(stdscr)
except Exception as e:
    print(e, file=sys.stderr)
    print(sys.exc_info(), file=sys.stderr)
cend(stdscr)

