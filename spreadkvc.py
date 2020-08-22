#!/usr/bin/env python3
# A simple ncurses based spreadsheet
# HanishKVC, 2020
# GPL

import sys
import curses
import curses.ascii


bDebug = False


'''
Notes:
    0th row or 0th col corresponds to spreadsheets address info
    1 to numRows and 1 to numCols corresponds to actual data.

    viewColStart and viewRowStart correspond to data cells, so
    they cant contain 0. Same with curCol and curRow.

    fixedCols|fixedRows for now corresponds to the single fixed
    row and col related to spreadsheet row|col address info.
'''

me = {
        'cellWidth': 16, 'cellHeight': 1,
        'scrCols': 10, 'scrRows': 5,
        'numCols': 100, 'numRows': 200,
        'dispCols': 5, 'dispRows': 5,
        'curCol': 1, 'curRow': 1,
        'viewColStart': 1, 'viewRowStart': 1,
        'fixedCols': 1, 'fixedRows': 1,
        'state': 'C',
        'data': dict(),
        'clipCell': True
        }


def cstart():
    stdscr = curses.initscr()
    me['scrRows'], me['scrCols'] = stdscr.getmaxyx()
    me['dispRows'] = me['scrRows'] - 1
    me['dispCols'] = int(me['scrCols'] / me['cellWidth']) - 1
    print(me, file=sys.stderr)
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
    '''
    Identify the position of the cell in the screen.

    If the col corresponds to the spreadsheet row addresses related column,
    then handle it directly. It will be 0, but for now indirectly calculated.

    If the col corresponds to a data cell, then check if it is within viewport
    or not and inturn based on it, calculate the screen x position.
    '''
    if (col == 0):
        x = col * me['cellWidth']
    elif (col < me['viewColStart']):
        x = -1
    else:
        x = (col - me['viewColStart']) * me['cellWidth']
        x += me['fixedCols']*me['cellWidth']
    if (row == 0):
        y = row
    elif (row < me['viewRowStart']):
        y = -1
    else:
        y = (row - me['viewRowStart'])
        y += me['fixedRows']
    print("cellpos: {},{} => {},{}".format(row,col,y,x), file=sys.stderr)
    return y, x


def cellstr(stdscr, y, x, msg, attr, clipped=True):
    '''
    Display contents of the cell, only if it is in the current display viewport
    as well as if it's contents can be fully shown on the screen.

    In viewport or not is got indirectly from the cellpos call.
    '''
    cellWidth = me['cellWidth']
    if clipped:
        tmsg = msg[0:cellWidth]
    else:
        tmsg = msg
    mlen = len(tmsg)
    if mlen < cellWidth:
        for i in range(cellWidth-mlen):
            tmsg += " "
    ty,tx = cellpos(y,x)
    if ((tx < 0) or ((tx+cellWidth) > me['scrCols'])) or ((ty < 0) or ((ty+1) > me['scrRows'])) :
        return
    print("cellstr: {},{} = {}".format(ty, tx, tmsg), file=sys.stderr)
    stdscr.addstr(ty, tx, tmsg, attr)


def cellcur(stdscr, y, x):
    '''
    Set the displayed cursor to the specified cell, if it is in the viewport
    and if its clipped content can be shown fully.

    As of now the logic will only show that much content as can fit within
    the cellWidth specified, so the check is done wrt cellWidth and not the
    length of the specific content in the cell.

    As cellHeight and amount of data in a cell can only be 1 line, so nothing
    etc required, or put differently both match to 1.
    '''
    cellWidth = me['cellWidth']
    ty,tx = cellpos(y,x)
    if ((tx < 0) or ((tx+cellWidth) > me['scrCols'])) or ((ty < 0) or ((ty+1) > me['scrRows'])) :
        return
    stdscr.move(ty,tx)


def cellcur_left():
    '''
    Move the current cell cursor to the left, if possible.

    It also ensures that the cursor position is 1 or greater.
    It also adjusts the viewport if required.
    '''
    me['curCol'] -= 1
    if (me['curCol'] <= 0):
        me['curCol'] = 1
    if (me['viewColStart'] > me['curCol']):
        me['viewColStart'] = me['curCol']


def cellcur_right():
    '''
    Move the current cell cursor to the right, if possible.

    It also ensures that the cursor position is within the available data cells.
    It also adjusts the viewport as required.
    '''
    me['curCol'] += 1
    if (me['curCol'] > me['numCols']):
        me['curCol'] = me['numCols']
    diff = me['curCol'] - me['viewColStart'] + 1
    if (diff > me['dispCols']):
        me['viewColStart'] = me['curCol'] - me['dispCols'] + 1
        print("cellcur_right:adjust viewport:{}".format(me), file=sys.stderr)


def cellcur_up():
    '''
    Move the current cell cursor up, if possible.

    It also ensures that the cursor position is 1 or greater.
    It also adjusts the viewport if required.
    '''
    me['curRow'] -= 1
    if (me['curRow'] < 1):
        me['curRow'] = 1
    if (me['viewRowStart'] > me['curRow']):
        me['viewRowStart'] = me['curRow']


def cellcur_down():
    '''
    Move the current cell cursor down, if possible.

    It also ensures that the cursor position is within the available data cells.
    It also adjusts the viewport as required.
    '''
    me['curRow'] += 1
    if (me['curRow'] > me['numRows']):
        me['curRow'] = me['numRows']
    diff = me['curRow'] - me['viewRowStart'] + 1
    if (diff > me['dispRows']):
        me['viewRowStart'] = me['curRow'] - me['dispRows'] + 1
        print("cellcur_down:adjust viewport:{}".format(me), file=sys.stderr)


def _cdraw_coladdrs(colStart, colEnd):
    '''
    As columns are named alphabetically and not numerically, so the
    internal numeric address is changed to equivalent alphabetic address.
    '''
    for i in range(colStart, colEnd+1):
        if (i == me['curCol']):
            ctype = curses.A_NORMAL
        else:
            ctype = curses.A_REVERSE
        iChr = i-1
        iMajor = int(iChr/26)
        if (iMajor < 1):
            sMajor = ""
        elif (iMajor > 26):
            print("ERROR: More than {} cols not supported".format(26*26))
            exit()
        else:
            sMajor=chr(ord('A')-1+iMajor)
        sMinor = chr(ord('A')+iChr%26)
        sColAddr = sMajor+sMinor
        cellstr(stdscr, 0, i, sColAddr, ctype)


def _cdraw_rowaddrs(rowStart, rowEnd):
    for i in range(rowStart, rowEnd+1):
        if (i == me['curRow']):
            ctype = curses.A_NORMAL
        else:
            ctype = curses.A_REVERSE
        cellstr(stdscr, i, 0, "{}".format(i), ctype)


def _cdraw_data(rowStart, rowEnd, colStart, colEnd):
    for r in range(rowStart, rowEnd+1):
        sRemaining = ""
        for c in range(colStart, colEnd+1):
            if ((r == me['curRow']) and (c == me['curCol'])):
                ctype = curses.A_REVERSE
            else:
                ctype = curses.A_NORMAL
            sData = me['data'].get((r,c))
            print("cdrawdata: {},{}={}".format(r,c,sData), file=sys.stderr)
            if (sData == None) and bDebug:
                sData = "{},{}".format(r,c)
            if (sData != None):
                sRemaining = sData[me['cellWidth']:]
            elif (not me['clipCell']):
                sData = sRemaining[0:me['cellWidth']]
                sRemaining = sRemaining[me['cellWidth']:]
                if (sData != ""):
                    print("cdrawdata:overflow:{}+{}".format(sData, sRemaining), file=sys.stderr)
            else: # sData == None AND clipCell
                sData = ""
            cellstr(stdscr, r, c, str(sData), ctype, True)
    if me['state'] == 'I':
        cellstr(stdscr, me['curRow'], me['curCol'], me['gotStr'], curses.A_REVERSE, False)


def cdraw(stdscr):
    '''
    Draws the screen consisting of the spreadsheet address row and col
    as well as the data cells (i.e data rows and cols).
    '''
    #stdscr.clear()
    colStart = me['viewColStart']
    colEnd = colStart + me['dispCols']
    if (colEnd > me['numCols']):
        colEnd = me['numCols']
    rowStart = me['viewRowStart']
    rowEnd = rowStart + me['dispRows']
    if (rowEnd > me['numRows']):
        rowEnd = me['numRows']
    print("cdraw: rows {} to {}, cols {} to {}".format(rowStart, rowEnd, colStart, colEnd), file=sys.stderr)
    _cdraw_coladdrs(colStart, colEnd)
    _cdraw_rowaddrs(rowStart, rowEnd)
    _cdraw_data(rowStart, rowEnd, colStart, colEnd)
    cellcur(stdscr, me['curRow'], me['curCol'])
    stdscr.refresh()


def runlogic(stdscr):
    '''
    RunLogic between the Command and the other modes

    Command Mode:
        One can move around the cells.
        Enter insert mode by pressing i
        Quit by pressing Q

    Insert Mode:
        Enter alpha numeric values, follwed by enter key.
        Escape from the insert mode by pressing Esc

    '''
    while True:
        cdraw(stdscr)
        key = stdscr.getch()
        if (me['state'] == 'C'):
            if (key == curses.KEY_UP):
                cellcur_up()
            elif (key == curses.KEY_DOWN):
                cellcur_down()
            elif (key == curses.KEY_LEFT):
                cellcur_left()
            elif (key == curses.KEY_RIGHT):
                cellcur_right()
            elif (key == ord('i')):
                me['state'] = 'I'
                me['gotStr'] = ""
            elif (key == ord('Q')):
                break
        else:
            if (key == curses.ascii.ESC):
                me['state'] = 'C'
            elif (key == curses.ascii.NL):
                me['data'][(me['curRow'],me['curCol'])] = me['gotStr']
                print("runLogic:{}".format(me), file=sys.stderr)
            else:
                me['gotStr'] += chr(key)


stdscr=cstart()
try:
    runlogic(stdscr)
except Exception as e:
    print(e, file=sys.stderr)
    a,b,c = sys.exc_info()
    print(sys.exc_info(), file=sys.stderr)
    for n in c:
        print(n, file=sys.stderr)
cend(stdscr)

