#!/usr/bin/env python3
# A simple ncurses based spreadsheet for the commandline
# HanishKVC, 2020
# GPL, Vasudhaiva Kutumbakam (the World is One Family)
#

import sys, traceback
import curses
import curses.ascii
from math import *


bDebug = False
THEQUOTE = '`'
THEFIELDSEP = ','


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
        'numCols': 333, 'numRows': 200,
        'dispCols': 5, 'dispRows': 5,
        'curCol': 1, 'curRow': 1,
        'viewColStart': 1, 'viewRowStart': 1,
        'fixedCols': 1, 'fixedRows': 1,
        'state': 'C',
        'data': dict(),
        'clipCell': False,
        'copyData': None,
        'gotStr': ""
        }


def cstart():
    stdscr = curses.initscr()
    me['scrRows'], me['scrCols'] = stdscr.getmaxyx()
    me['dispRows'] = me['scrRows'] - 1
    me['dispCols'] = int(me['scrCols'] / me['cellWidth']) - 1
    print(me, file=GLOGFILE)
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
    print("cellpos: {},{} => {},{}".format(row,col,y,x), file=GLOGFILE)
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
    print("cellstr: {},{} = {}".format(ty, tx, tmsg), file=GLOGFILE)
    stdscr.addstr(ty, tx, tmsg, attr)


def cellcur(stdscr, y, x):
    '''
    Set the displayed cursor to the specified cell's start location, if the cell
    is in the viewport and if its (i.e cell's) clipped content can be shown fully.

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


def _goto_cell(stdscr, r, c):
    '''
    Center the specified cell on the screen. It also sets
        the program's current cell info variables as well as
        the cursor libraries cursor position to this cell.
    '''
    tr = r - int(me['dispRows']/2)
    if tr < 1:
        tr = 1
    me['viewRowStart'] = tr
    tc = c - int(me['dispCols']/2)
    if tc < 1:
        tc = 1
    me['viewColStart'] = tc
    me['curRow'] = r
    me['curCol'] = c
    stdscr.clear()
    cdraw(stdscr)
    cellcur(stdscr, r, c)


def goto_cell(stdscr, args):
    bCellAddr, (r,c) = _celladdr_valid(args)
    if bCellAddr:
        _goto_cell(stdscr, r, c)


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
        print("cellcur_right:adjust viewport:{}".format(me), file=GLOGFILE)


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
        print("cellcur_down:adjust viewport:{}".format(me), file=GLOGFILE)


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
            print("cdrawdata: {},{}={}".format(r,c,sData), file=GLOGFILE)
            if (sData == None) and bDebug:
                sData = "{},{}".format(r,c)
            if (sData != None):
                if sData.startswith("="):
                    sData = value((r,c))
                else:
                    sRemaining = sData[me['cellWidth']:]
            elif (not me['clipCell']):
                sData = sRemaining[0:me['cellWidth']]
                sRemaining = sRemaining[me['cellWidth']:]
                if (sData != ""):
                    print("cdrawdata:overflow:{}+{}".format(sData, sRemaining), file=GLOGFILE)
            else: # sData == None AND clipCell
                sData = ""
            cellstr(stdscr, r, c, str(sData), ctype, True)
    if me['state'] == 'E':
        cellstr(stdscr, me['curRow'], me['curCol'], me['gotStr'], curses.A_REVERSE, False)
    if me['state'] == ':':
        #cellstr(stdscr, me['numRows']-1, 0, me['gotStr'], curses.A_REVERSE, False)
        cellstr(stdscr, 0, 0, ":{}".format(me['gotStr']), curses.A_REVERSE, False)


def cdraw(stdscr):
    '''
    Draws the screen consisting of the spreadsheet address row and col
    as well as the data cells (i.e data rows and cols).
    '''
    #stdscr.clear()
    cellstr(stdscr, 0, 0, "SpreadSheetKVC", curses.A_NORMAL)
    colStart = me['viewColStart']
    colEnd = colStart + me['dispCols']
    if (colEnd > me['numCols']):
        colEnd = me['numCols']
    rowStart = me['viewRowStart']
    rowEnd = rowStart + me['dispRows']
    if (rowEnd > me['numRows']):
        rowEnd = me['numRows']
    print("cdraw: rows {} to {}, cols {} to {}".format(rowStart, rowEnd, colStart, colEnd), file=GLOGFILE)
    _cdraw_coladdrs(colStart, colEnd)
    _cdraw_rowaddrs(rowStart, rowEnd)
    _cdraw_data(rowStart, rowEnd, colStart, colEnd)
    cellcur(stdscr, me['curRow'], me['curCol'])
    stdscr.refresh()


def insert_rc_ab(cmd, args):
    '''
    Insert n number of rows or columns, before or after the current row|column.
    '''
    bRowMode = False
    bColMode = False
    if cmd[1] == 'r':
        bRowMode = True
    elif cmd[1] == 'c':
        bColMode = True
    cnt = int(args)

    cR = me['curRow']
    cC = me['curCol']
    # Logic inserts after cur, so adjust cur, if before
    if cmd[2] == 'b':
        cR -= 1
        cC -= 1

    newDict = dict()
    for k in me['data']:
        r,c = k
        if bRowMode:
            nC = c
            if (r > cR):
                nR = r + cnt
            else:
                nR = r
        if bColMode:
            nR = r
            if (c > cC):
                nC = c + cnt
            else:
                nC = c
        newDict[(nR,nC)] = me['data'][k]
    me['data'] = newDict
    if bRowMode:
        me['numRows'] += cnt
    if bColMode:
        me['numCols'] += cnt


def delete_rc(cmd, args):
    '''
    Delete the current row or column, as specified in the cmd.
    '''
    bRowMode = False
    bColMode = False
    if cmd[1] == 'r':
        bRowMode = True
        me['numRows'] -= 1
    elif cmd[1] == 'c':
        bColMode = True
        me['numCols'] -= 1

    cR = me['curRow']
    cC = me['curCol']
    newDict = dict()
    for k in me['data']:
        r,c = k
        if bRowMode:
            if r < cR:
                newDict[k] = me['data'][k]
            elif r > cR:
                newDict[(r-1,c)] = me['data'][k]
        if bColMode:
            if c < cC:
                newDict[k] = me['data'][k]
            elif c > cC:
                newDict[(r,c-1)] = me['data'][k]
    me['data'] = newDict


def save_file(sFile):
    '''
    Save file in a csv format.

    If the cell data contains comma in it, then the cell content
    is protected within single quotes.
    '''
    f = open(sFile,"w+")
    for r in range(1, me['numRows']+1):
        for c in range(1, me['numCols']+1):
            data = me['data'].get((r,c))
            if (data != None):
                if data.find(THEFIELDSEP) != -1:
                    data = "{}{}{}".format(THEQUOTE, data, THEQUOTE)
                print(data, end="", file=f)
            print(THEFIELDSEP, end="", file=f)
        print("\n", end="", file=f)
    f.close()


def load_file(sFile):
    '''
    Load the specified csv file
    '''
    f = open(sFile)
    print("loadfile:{}".format(sFile), file=GLOGFILE)
    me['data'] = dict()
    r = 0
    for line in f:
        r += 1
        c = 1
        i = 0
        sCur = ""
        bInQuote = False
        while i < len(line):
            t = line[i]
            if t == THEQUOTE:
                bInQuote = not bInQuote
                sCur += t
            elif t == THEFIELDSEP:
                if bInQuote:
                    sCur += t
                else:
                    if sCur != "":
                        me['data'][(r,c)] = sCur
                        sCur = ""
                    c += 1
            else:
                sCur += t
            i += 1
        sCur = sCur[:-1]
        if sCur != "":
            me['data'][(r,c)] = sCur
            sCur = ""
    f.close()
    me['numRows'] = r
    me['numCols'] = c
    print("loadfile:done:{}".format(me), file=GLOGFILE)


def explicit_commandmode(stdscr, cmdArgs):
    '''
    Explicit Command mode, which is entered by pressing ':' followed by
    one of the commands mentioned below.

    w path/file_to_save
    l path/file_to_open
    dr delete row
    dc delete column
    irb num_of_rows
        insert n rows before current row
    ira num_of_rows
        insert n rows after current row
    icb num_of_cols
        insert n columns before current column
    ica num_of_cols
        insert n columns after current column
    e path/file_to_export_into
    '''
    if cmdArgs.find(' ') == -1:
        cmd = cmdArgs
        args = None
    else:
        cmd,args = cmdArgs.split(' ',1)
    print("cmd:{}, args:{}".format(cmd,args), file=GLOGFILE)
    if cmd == 'w':
        save_file(args)
    elif cmd == 'l':
        load_file(args)
    elif cmd.startswith('i'):
        if args == None:
            args = "1"
        insert_rc_ab(cmd, args)
    elif cmd.startswith('d'):
        delete_rc(cmd, args)
    elif cmd.startswith('g'):
        if args != None:
            goto_cell(stdscr, args)


def _do_minmax(args, bIgnoreEmpty=True):
    '''
    Find the min and max from the matrix of cells.
    '''
    start,end = args.split(':')
    bCellAddr, (sR,sC) = _celladdr_valid(start)
    if not bCellAddr:
        return None, None, None
    bCellAddr, (eR,eC) = _celladdr_valid(end)
    if not bCellAddr:
        return None, None, None
    lItems = []
    for r in range(sR, eR+1):
        for c in range(sC, eC+1):
            if ((me['data'].get((r,c)) == None) and bIgnoreEmpty):
                continue
            lItems.append(nvalue((r,c)))
    tMin = min(lItems)
    tMax = max(lItems)
    return tMin, tMax, len(lItems)


def do_min(args):
    tmin, tmax, tcnt = _do_minmax(args)
    return tmin


def do_max(args):
    tmin, tmax, tcnt = _do_minmax(args)
    return tmax


def _do_sum(args, bIgnoreEmpty=True):
    '''
    sum up contents of a matrix of cells.
    It also returns the number of cells involved.
    '''
    start,end = args.split(':')
    bCellAddr, (sR,sC) = _celladdr_valid(start)
    if not bCellAddr:
        return None, None
    bCellAddr, (eR,eC) = _celladdr_valid(end)
    if not bCellAddr:
        return None, None
    total = 0
    cnt = 0
    for r in range(sR, eR+1):
        for c in range(sC, eC+1):
            if ((me['data'].get((r,c)) == None) and bIgnoreEmpty):
                continue
            total += nvalue((r,c))
            cnt += 1
    return total, cnt


def do_sum(args):
    '''
    Return the sum of specified range of cells.
    It could be 1D vector or 2D vector.
    '''
    total, cnt = _do_sum(args)
    return total


def _do_stddev(args, bIgnoreEmpty=True):
    '''
    get variance/standard deviation wrt sample/population space,
    for the contents of a matrix of cells.
    It also returns the number of cells involved.
    '''
    start,end = args.split(':')
    bCellAddr, (sR,sC) = _celladdr_valid(start)
    if not bCellAddr:
        return None, None
    bCellAddr, (eR,eC) = _celladdr_valid(end)
    if not bCellAddr:
        return None, None
    avg = do_avg(args)
    total = 0
    cnt = 0
    for r in range(sR, eR+1):
        for c in range(sC, eC+1):
            if ((me['data'].get((r,c)) == None) and bIgnoreEmpty):
                continue
            total += (nvalue((r,c)) - avg)**2
            cnt += 1
    varp = total/cnt
    stdevp = sqrt(varp)
    var = total/(cnt-1)
    stdev = sqrt(var)
    return varp, stdevp, var, stdev, cnt


def do_stddev(sCmd, args):
    '''
    Return variance assuming the cell range represents a sample space
    Return variance assuming the cell range represents a full population
    Return stddev assuming the cell range represents a sample space
    Return stddevp assuming the cell range represents a full population
    '''
    varp, stdevp, var, stdev, cnt = _do_stddev(args)
    if (sCmd == "STDDEV") or (sCmd == "STDEV"):
        return stdev
    if (sCmd == "STDDEVP") or (sCmd == "STDEVP"):
        return stdevp
    if (sCmd == "VAR"):
        return var
    if (sCmd == "VARP"):
        return varp


def _do_prod(args, bIgnoreEmpty=True):
    '''
    Multiply the contents of a matrix of cells.
    It also returns the number of cells involved.
    '''
    start,end = args.split(':')
    bCellAddr, (sR,sC) = _celladdr_valid(start)
    if not bCellAddr:
        return None, None
    bCellAddr, (eR,eC) = _celladdr_valid(end)
    if not bCellAddr:
        return None, None
    prod = 1
    cnt = 0
    for r in range(sR, eR+1):
        for c in range(sC, eC+1):
            if ((me['data'].get((r,c)) == None) and bIgnoreEmpty):
                continue
            prod *= nvalue((r,c))
            cnt += 1
    return prod, cnt


def do_prod(args):
    '''
    Return the product of values in the specified range of cells.
    It could be 1D vector or 2D vector of cells.
    '''
    prod, cnt = _do_prod(args)
    return prod


def do_cnt(args):
    '''
    Return the cnt of non-empty cells in the specified range of cells.
    It could be 1D vector or 2D vector of cells.
    '''
    total, cnt = _do_sum(args)
    return cnt


def do_avg(args):
    '''
    Return the avg for specified range of cells.
    It could be 1D vector or 2D vector of cells.
    '''
    total, cnt = _do_sum(args)
    if (total == None):
        return None
    return total/cnt


def do_func(sCmd, sArgs):
    '''
    Demux the internally supported functions.
    Unknown function will return None.
    '''
    try:
        print("do_func:{}:{}".format(sCmd, sArgs), file=GLOGFILE)
        if sCmd == "SUM":
            return do_sum(sArgs)
        elif (sCmd == "AVG") or (sCmd == "AVERAGE"):
            return do_avg(sArgs)
        elif (sCmd == "CNT") or (sCmd == "COUNT"):
            return do_cnt(sArgs)
        elif sCmd == "MIN":
            return do_min(sArgs)
        elif sCmd == "MAX":
            return do_max(sArgs)
        elif sCmd == "PROD":
            return do_prod(sArgs)
        elif (sCmd.startswith("STDDEV") or sCmd.startswith("STDEV")):
            return do_stddev(sCmd, sArgs)
        elif sCmd.startswith("VAR"):
            return do_stddev(sCmd, sArgs)
    except:
        print("do_func exception", file=GLOGFILE)
        traceback.print_exc()
    return None


def _nvalue_funcs(sData):
    '''
    Find func calls in the given expression and call them
    to get the numeric value corresponding to them and
    replace the func call with its returned value.
    '''
    sBase = ""
    sCur = ""
    i = 0
    while i < len(sData):
        c = sData[i]
        if c.isalnum():
            sCur += c
        else:
            if c == "(":
                if (sCur == ""):
                    sBase += c
                else:
                    # Currently one cant embed one func call
                    # within another
                    sCmd = sCur
                    sArgs = ""
                    i += 1
                    while i < len(sData):
                        c = sData[i]
                        if c == ')':
                            break
                        else:
                            sArgs += c
                        i += 1
                    val = do_func(sCmd, sArgs)
                    sBase += str(val)
                    sCur = ""
            else:
                sBase = sBase + sCur + c
                sCur = ""
        i += 1
    sBase += sCur
    return sBase


def _celladdr_valid(sAddr):
    '''
    Check if the given string is a cell address or not.
    '''
    iChars = 0
    i = 0
    alphaAddr = ""
    while i < len(sAddr):
        if not sAddr[i].isalpha():
            break
        alphaAddr += sAddr[i]
        iChars += 1
        i += 1
    if (iChars == 0) or (iChars > 2): # This limits number of cols
        return False, None
    iNums = 0
    numAddr = ""
    while i < len(sAddr):
        if not sAddr[i].isnumeric():
            break
        numAddr += sAddr[i]
        iNums += 1
        i += 1
    if (iNums == 0) or (iNums > 4): # This limits number of rows
        return False, None
    if i != len(sAddr):
        return False, None
    # Get the data key for the cell
    i = 0
    alphaAddr = alphaAddr.upper()
    numAlphaAddr = 0
    while i < len(alphaAddr):
        num = (ord(alphaAddr[i]) - ord('A'))+1
        numAlphaAddr = numAlphaAddr*26 + num
        i += 1
    return True, (int(numAddr), int(numAlphaAddr))


def _cellvalue_or_str(sCheck):
    '''
    If passed a cell address, then return the corresponding cells numeric value
    Else return the passed string back again.
    '''
    bCellAddr, cellKey = _celladdr_valid(sCheck)
    if bCellAddr:
        val = nvalue(cellKey)
        print("_cellvalue_or_str:{}:{}:{}".format(sCheck, cellKey, val), file=GLOGFILE)
        return str(val)
    return sCheck


def _nvalue_cells(sData):
    '''
    Identify the cell addresses in the given string and replace them
    with the numeric value got from the corresponding cell.
    '''
    sBase = ""
    sCur = ""
    i = 0
    while i < len(sData):
        c = sData[i]
        if c.isalnum():
            sCur += c
        else:
            sBase += _cellvalue_or_str(sCur)
            sBase += c
            sCur = ""
        i += 1
    sBase += _cellvalue_or_str(sCur)
    return sBase


def _nvalue(sData):
    # Remove spaces and convert to upper case wrt eval expression
    sDATA = sData.replace(" ","").upper()
    # Handle functions first
    sBase = _nvalue_funcs(sDATA)
    # Handle cell addresses
    sBase = _nvalue_cells(sBase)
    # Evaluate
    try:
        val = float(eval(sBase))
    except:
        print("_nvalue exception:{}".format(sData), file=GLOGFILE)
        traceback.print_exc()
        val = None
    return val


def nvalue(addr):
    '''
    Return the numeric value associated with the given cell.
    It will either return None (if not numeric or error in expression)
    or else will return the numeric value associated with the cell.
    If the cell contains a =expression, it will be evaluated.
    '''
    val = me['data'].get(addr)
    if val == None:
        return val
    if not val.startswith("="):
        return None
    return _nvalue(val[1:])


def nvalue_saddr(saddr):
    '''
    Given the cell address in string notation, return the numeric
    value corresponding to that cell.
    If the address is invalid, then None is returned.
    '''
    bCellAddr, cellKey = _celladdr_valid(saddr)
    if bCellAddr:
        val = nvalue(cellKey)
        return val
    return None


def value(addr):
    '''
    Return the value associated with the given cell.
    It will be a empty string if no data in the cell.
    It will be the numeric value if the cell has a =expression.
    Else it will return the textual data in the cell.
    '''
    val = me['data'].get(addr)
    if val == None:
        return ""
    if not val.startswith("="):
        return val
    return _nvalue(val[1:])


def rl_commandmode(stdscr, key):
    if (key == curses.KEY_UP):
        cellcur_up()
    elif (key == curses.KEY_DOWN):
        cellcur_down()
    elif (key == curses.KEY_LEFT):
        cellcur_left()
    elif (key == curses.KEY_RIGHT):
        cellcur_right()
    elif (key == ord('d')):
        me['data'].pop((me['curRow'],me['curCol']), None)
    elif (key == ord('c')):
        me['copyData'] = me['data'].get((me['curRow'],me['curCol']))
    elif (key == ord('C')):
        me['copyData'] = me['data'].get((me['curRow'],me['curCol']))
        me['data'].pop((me['curRow'],me['curCol']), None)
    elif (key == ord('p')):
        if me['copyData'] != None:
            me['data'][(me['curRow'],me['curCol'])] = me['copyData']
    elif (key == ord('i')):
        me['state'] = 'E'
        me['gotStr'] = ""
        me['backupEdit'] = None
        me['data'][(me['curRow'],me['curCol'])] = ""
    elif (key == ord('e')):
        me['state'] = 'E'
        me['gotStr'] = me['data'].get((me['curRow'], me['curCol']))
        if me['gotStr'] == None:
            me['gotStr'] = ""
        me['backupEdit'] = me['gotStr']
        me['data'][(me['curRow'],me['curCol'])] = ""
    elif (key == ord(':')):
        me['state'] = ':'
        me['gotStr'] = ""
    elif (key == ord('Q')):
        return False
    return True


def rl_editplusmode(stdscr, key):
    if (key == curses.ascii.ESC):
        if me['state'] == 'E':
            # Restore/set data to the latest backedup edit buffer
            if me['backupEdit'] != None:
                me['data'][(me['curRow'],me['curCol'])] = me['backupEdit']
        me['state'] = 'C'
    elif (key == curses.KEY_BACKSPACE):
        me['gotStr'] = me['gotStr'][0:-1]
    elif (key == curses.ascii.NL):
        if me['state'] == 'E':
            me['backupEdit'] = me['gotStr']
        elif me['state'] == ':':
            explicit_commandmode(stdscr, me['gotStr'])
            me['state'] = 'C'
        print("runLogic:{}".format(me), file=GLOGFILE)
    else:
        me['gotStr'] += chr(key)


def runlogic(stdscr):
    '''
    RunLogic between the Command and the other modes

    Command Mode:
        One can move around the cells.
        Enter insert mode by pressing i
        Enter edit mode by pressing e
        Delete cell content by pressing d
        Copy cell data by pressing c
        Cut cell data by pressing C
        Paste cell data by pressing p
        Quit by pressing Q

    Edit/Insert Mode:
        Edit mode: Edit existing cell data
        Insert mode: Put new data in the cell

        Enter alpha numeric values, follwed by enter key.
        Escape from the edit/insert mode by pressing Esc.
            Only data locked in by pressing enter will be saved.
            And or data which was already in the edit buffer.

    '''
    bBackInC = False
    while True:
        cdraw(stdscr)
        key = stdscr.getch()
        try:
            if (me['state'] == 'C'):    #### Command Mode
                if not bBackInC:
                    stdscr.clear()
                    bBackInC = True
                if not rl_commandmode(stdscr, key):
                    break
            else:                       #### Edit+ Mode
                bBackInC = False
                rl_editplusmode(stdscr, key)
        except:
            traceback.print_exc()


def setup_logfile(logfile="/dev/null"):
    f = open(logfile, "w+")
    return f


GLOGFILE=setup_logfile()
stdscr=cstart()
try:
    runlogic(stdscr)
except Exception as e:
    print("exception:{}".format(e), file=GLOGFILE)
    print("exc_info:{}".format(sys.exc_info()), file=GLOGFILE)
    traceback.print_exc()
    print("exception: done", file=GLOGFILE)
finally:
    cend(stdscr)
    GLOGFILE.close()

# vim: set sts=4 expandtab: #
