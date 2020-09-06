#!/usr/bin/env python3
# A simple ncurses based spreadsheet for the commandline
# HanishKVC, 2020
# GPL, Vasudhaiva Kutumbakam (the World is One Family)
#

import sys, traceback, os, signal
import curses
import curses.ascii
from math import *
import tempfile
import cryptography.fernet
import base64
import secrets
import enum
import seckvc as sec
import helpdlg
import cuikvc as cui
import parsekvc as parse
import funcs
import re


bDebug = False
THEQUOTE = "'"
THEFIELDSEP = ';'
THEALT2INBTWQUOTE = '_'
DONTEXIT = -9999
# Whether to use internal or cryptography libraries AuthenticatedEncryption
# Both use similar concepts, but bitstreams are not directly interchangable
bInternalEncDec = True
gbStartHelp = True
# How to differentiate text cells compared to =expression cells
# This is the default, cattr_textnum will try and adjust at runtime.
CATTR_DATATEXT = (curses.A_ITALIC | curses.A_DIM)
CATTR_DATANUM = (curses.A_NORMAL)
# How many columns to left of current display viewport should one peek
# to see, if there is any overflowing text that needs to be displayed.
DATACOLSTART_OVERSCAN = 20
# Exit EditMode on pressing Enter
gbEnterExitsEditMode = True


'''
Notes:
    0th row or 0th col corresponds to spreadsheets address info
    1 to numRows and 1 to numCols corresponds to actual data.

    viewColStart and viewRowStart correspond to data cells, so
    they cant contain 0. Same with curCol and curRow.

    fixedCols|fixedRows for now corresponds to the single fixed
    row and col related to spreadsheet row|col address info.

    dirty tells if any modifications exist that havent been saved
    back to the disk yet.

    exit triggers a exit from the program, if its not DONTEXIT.
'''

me = {
        'cellWidth': 16, 'cellHeight': 1,
        'scrCols': 10, 'scrRows': 5,
        'numCols': 333, 'numRows': 200,
        'dispCols': 5, 'dispRows': 5,
        'curCol': 1, 'curRow': 1,
        'crsrOffset': 0,
        'viewColStart': 1, 'viewRowStart': 1,
        'fixedCols': 1, 'fixedRows': 1,
        'state': 'C',
        'readOnly': False,
        'helpModeSavedReadOnly': None,
        'data': dict(),
        'cdata': dict(),
        'cdataUpdate': True,
        'clipCell': False,
        'copyData': None,
        'copySrcCell': None,
        'gotStr': "",
        'dirty': False,
        'calcCnt': dict(),
        'callDepth': 0,
        'exit': DONTEXIT
        }

CursesKeys = [ curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT, curses.KEY_BACKSPACE ]


def cscreenadapt(stdscr):
    cui._screen_size(stdscr)
    me['scrRows'], me['scrCols'] = cui.me['scrRows'], cui.me['scrCols']
    me['dispRows'] = me['scrRows'] - 1
    me['dispCols'] = int(me['scrCols'] / me['cellWidth']) - 1


def cstart():
    cui.GERRFILE=GERRFILE
    cui.GLOGFILE=GLOGFILE
    stdscr = cui.cstart()
    cscreenadapt(stdscr)
    print(me, file=GLOGFILE)
    return stdscr


def cend(stdscr):
    cui.cend(stdscr)


def cattr_textnum(scr):
    '''
    Try and have Numeric cell brighter/standout compared to Text cell.
    '''
    global CATTR_DATATEXT, CATTR_DATANUM
    availAttrs = curses.termattrs()
    bItalic = ((availAttrs & curses.A_ITALIC) == curses.A_ITALIC)
    if bItalic:
        scr.attron(curses.A_ITALIC)
    bDim = ((availAttrs & curses.A_DIM) == curses.A_DIM)
    if bDim:
        scr.attron(curses.A_DIM)
    if bDim or bItalic:
        CATTR_DATATEXT = (curses.A_ITALIC | curses.A_DIM)
        CATTR_DATANUM = (curses.A_NORMAL)
    else:
        CATTR_DATATEXT = (curses.A_NORMAL)
        CATTR_DATANUM = (curses.A_BOLD)


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


def cellstr(stdscr, y, x, msg, attr, clipToCell=True, clipToScreen=True):
    '''
    Display contents of the cell, only if it is in the current display viewport
    as well as if the cell (not its contents) can be fully shown on the screen.

    In viewport or not is got indirectly from the cellpos call.
    '''
    cellWidth = me['cellWidth']
    if clipToCell:
        tmsg = msg[0:cellWidth]
    else:
        tmsg = msg
    mlen = len(tmsg)
    if mlen < cellWidth:
        for i in range(cellWidth-mlen):
            tmsg += " "
    ty,tx = cellpos(y,x)
    cellWidth=0
    if ((tx < 0) or ((tx+cellWidth) > me['scrCols'])) or ((ty < 0) or ((ty+1) > me['scrRows'])) :
        return
    #print("cellstr:{},{}:{},{}:{}".format(y, x, ty, tx, tmsg), file=GERRFILE)
    cui.cellstr(stdscr, ty, tx, tmsg, attr, clipToScreen)


def dlg(scr, msgs, y=0, x=0, attr=curses.A_NORMAL):
    '''
    Show a simple dialog, with the messages passed to it.
    And return a keypress from the user.

    y,x are specified interms of matrix of cells and not screen y,x.
    '''
    for i in range(len(msgs)):
        cellstr(scr, y+i, x, msgs[i], attr, clipToCell=False)
    return scr.getch()


def status(scr, msgs, y=0, x=0, attr=curses.A_NORMAL):
    '''
    Display the messages passed to it at a given location.
    If location not given, then show at top left corner.

    y,x are specified interms of matrix of cells and not screen y,x.
    '''
    for i in range(len(msgs)):
        cellstr(scr, y+i, x, msgs[i], attr, clipToCell=False)
    scr.refresh()


def cellcur(stdscr, y, x):
    '''
    Set the displayed cursor to the specified cell's start location, if the cell
    is in the viewport and if its (i.e cell's) clipped content can be shown fully.

        In edit and explicit command mode, the logic accounts for any crsrOffset
        that may be specified, which will be added to the start location of specified
        cell.

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
    if me['state'] == "E":
        tx += me['crsrOffset']
    elif me['state'] == ":":
        tx += (me['crsrOffset'] + 1)
    if (tx >= me['scrCols']):
        overflow = tx - me['scrCols']
        tx = (overflow % me['scrCols'])
        ty += (1+int(overflow / me['scrCols']))
    try:
        stdscr.move(ty,tx)
    except:
        print("cellcur:exception:move:ignoring:{}".format(sys.exc_info()), file=GERRFILE)


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
        if r > me['numRows']:
            r = me['numRows']
        if c > me['numCols']:
            c = me['numCols']
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


def coladdr_num2alpha(iAddr):
    iChr = iAddr-1
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
    return sColAddr


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
        sColAddr = coladdr_num2alpha(i)
        cellstr(stdscr, 0, i, sColAddr, ctype)


def _cdraw_rowaddrs(rowStart, rowEnd):
    for i in range(rowStart, rowEnd+1):
        if (i == me['curRow']):
            ctype = curses.A_NORMAL
        else:
            ctype = curses.A_REVERSE
        cellstr(stdscr, i, 0, "{}".format(i), ctype)


def cdata_update():
    '''
    Cache data calculation results.
    '''
    me['cdata'] = dict()
    for r in range(1, me['numRows']+1):
        for c in range(1, me['numCols']+1):
            me['calcCnt'] = dict()
            me['callDepth'] = 0
            sData = me['data'].get((r,c))
            if sData != None:
                if sData.startswith('='):
                    try:
                        val = nvalue((r,c))
                    except:
                        print("cdata_update:exception:{}:{}".format((r,c),sData), file=GERRFILE)
                        traceback.print_exc(file=GERRFILE)
                        val = 'None'
                else:
                    val = sData
                me['cdata'][r,c] = val


def _cdraw_data(rowStart, rowEnd, colStart, colEnd):
    '''
    Display the cells which are currently visible on the screen.
    '''
    if me['cdataUpdate']:
        cdata_update()
        me['cdataUpdate'] = False
    #print("cdrawdata:Starting", file=GERRFILE)
    dataColStart = colStart - DATACOLSTART_OVERSCAN
    if dataColStart < 1:
        dataColStart = 1
    for r in range(rowStart, rowEnd+1):
        sRemaining = ""
        for c in range(dataColStart, colEnd+1):
            if ((r == me['curRow']) and (c == me['curCol'])):
                ctype = curses.A_REVERSE
            else:
                ctype = curses.A_NORMAL
            sData = me['data'].get((r,c))
            #print("cdrawdata: {},{}={}".format(r,c,sData), file=GLOGFILE)
            if (sData == None) and bDebug:
                sData = "{},{}".format(r,c)
            if (sData != None):
                if sData.startswith("="):
                    #sData = value((r,c))
                    sData = me['cdata'].get((r,c))
                    ctype |= CATTR_DATANUM
                    sRemaining = ""
                else:
                    ctype |= CATTR_DATATEXT
                    sRemaining = sData[me['cellWidth']:]
            elif (not me['clipCell']):
                ctype |= CATTR_DATATEXT
                sData = sRemaining[0:me['cellWidth']]
                sRemaining = sRemaining[me['cellWidth']:]
                #if (sData != ""):
                #    print("cdrawdata:overflow:{}+{}".format(sData, sRemaining), file=GLOGFILE)
            else: # sData == None AND clipCell
                ctype |= CATTR_DATATEXT
                sData = ""
            if (c < colStart):
                continue
            cellstr(stdscr, r, c, str(sData), ctype, clipToCell=True)


def _cdraw_editbuffer(stdscr):
    '''
    Show the edit buffer as required, if in Edit or Explicit command mode.
    '''
    if me['state'] == 'E':
        cellstr(stdscr, me['curRow'], me['curCol'], me['gotStr'], curses.A_REVERSE, clipToCell=False, clipToScreen=False)
    if me['state'] == ':':
        #cellstr(stdscr, me['numRows']-1, 0, me['gotStr'], curses.A_REVERSE, False)
        cellstr(stdscr, 0, 0, ":{}".format(me['gotStr']), curses.A_REVERSE, clipToCell=False, clipToScreen=False)


def _cdraw_showcursor(stdscr):
    '''
    Show the text cursor at the appropriate location based on mode.
    '''
    if me['state'] == ":":
        cellcur(stdscr, 0, 0)
    else:
        cellcur(stdscr, me['curRow'], me['curCol'])


def _cdraw(stdscr):
    '''
    Draws the screen consisting of the spreadsheet address row and col
    as well as the data cells (i.e data rows and cols).

    It also ensures that the edit/explicit command edit buffer and cursor
    is shown, even if printing data raises any exception.
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
    print("_cdraw: rows {} to {}, cols {} to {}".format(rowStart, rowEnd, colStart, colEnd), file=GLOGFILE)
    _cdraw_coladdrs(colStart, colEnd)
    _cdraw_rowaddrs(rowStart, rowEnd)
    try:
        _cdraw_data(rowStart, rowEnd, colStart, colEnd)
    finally:
        _cdraw_editbuffer(stdscr)
        _cdraw_showcursor(stdscr)
    stdscr.refresh()


def cdraw(stdscr):
    bDone = False
    while not bDone:
        try:
            _cdraw(stdscr)
            bDone = True
        except:
            if me['state'] == 'E':
                a,b,c = sys.exc_info()
                print("cdraw:exception:{},{},{}".format(a,b,c), file=GERRFILE)
                me['viewRowStart'] += 3
                if (me['viewRowStart'] + me['dispRows']) > me['numRows']:
                    bDone = True
                stdscr.clear()
            else:
                bDone = True
            print("cdraw:exception:{}".format(sys.exc_info()), file=GLOGFILE)
            traceback.print_exc(file=GERRFILE)


def update_celladdrs_all(sIn, afterR, incR, afterC, incC, bUpdateFixed=True):
    '''
    Update any cell addresses found in given string,
    by adjusting the address by given incR or incC amount, provided
    the address is beyond afterR or afterC.

    If the row or col address is part of the deleted row or col list,
    then instead of ajdusting, error tag it.

    If bUpdateFixed is False, then  dont change cell address parts
    which have the $-prefix.

    NOTE: THis is for use by insert or delete row/col logics.
    They should set bUpdateFixed to True.

    NOTE: User can request to keep the row or col part of the celladdress
    to be fixed by using $-prefix.
    '''
    bDelRowMode = bDelColMode = False
    if (incR < 0):
        bDelRowMode = True
        sDR = afterR + 1
        eDR = afterR - incR
    if (incC < 0):
        bDelColMode = True
        sDC = afterC + 1
        eDC = afterC - incC
    bInsRowMode = bInsColMode = False
    if (incR > 0):
        bInsRowMode = True
    if (incC > 0):
        bInsColMode = True
    #print("updateCellAddrs:In:{}".format(sIn), file=GERRFILE)
    iPos = 0
    sOut = sIn
    while True:
        # Find token
        bToken, sToken, iPos = parse.get_celladdr(sOut, iPos)
        if not bToken:
            #print("updateCellAddrs:Out:{}".format(sOut), file=GERRFILE)
            return sOut
        #print("updateCellAddrs:Btw:{}".format(sToken), file=GERRFILE)
        bCellAddr, (r,c), (rFixed, cFixed) = _celladdr_valid_ex(sToken)
        # If not valid cell addr, skip it
        if not bCellAddr:
            iPos += len(sToken)
            continue
        # prepare the fixed $ tag anchors
        if rFixed:
            sRFixed ="$"
        else:
            sRFixed = ""
        if cFixed:
            sCFixed ="$"
        else:
            sCFixed = ""
        # Handle bUpdateFixed flag
        if bUpdateFixed:
            rFixed = False
            cFixed = False
        # A valid cell address, so update
        sErr = ""
        sBefore = sOut[0:iPos]
        sAfter = sOut[iPos+len(sToken):]
        if (bInsRowMode and (r > afterR)) and not rFixed:
            r += incR
        if (bInsColMode and (c > afterC)) and not cFixed:
            c += incC
        if bDelRowMode:
            if (r >= sDR) and (r <= eDR):
                sErr = "ErrR_"
            if (r > eDR) and not rFixed:
                r += incR
        if bDelColMode:
            if (c >= sDC) and (c <= eDC):
                sErr += "ErrC_"    # + not required bcas both row and col wont get deleted at same time, but for flexibility for future, just in case
            if (c > eDC) and not cFixed:
                c += incC
        sNewToken = "{}{}{}{}{}".format(sErr,sCFixed,coladdr_num2alpha(c),sRFixed,r)
        sOut = sBefore + sNewToken
        iPos = len(sOut)
        sOut += sAfter


def update_celladdrs_exceptfixed(sIn, afterR, incR, afterC, incC):
    '''
    Blindly update any cell addresses found in given string,
    by adjusting the address by given incR or incC amount,
    provided the address is beyond afterR or afterC.

    NOTE: This is for use by paste or equivalent logic.
    They should set afterR and afterC to 0.

    However if user has requested to keep the row or col part of the
    celladdress fixed by using $prefix, then dont modify it, other than
    error tagging if any due to the row or col being beyond spreadsheet.

    If ErrTagged, then set corresponding address part to original one.
    '''
    #print("updateCellAddrsExceptFixed:In:{}".format(sIn), file=GERRFILE)
    iPos = 0
    sOut = sIn
    while True:
        # Find token
        bToken, sToken, iPos = parse.get_celladdr(sOut, iPos)
        if not bToken:
            #print("updateCellAddrsExceptFixed:Out:{}".format(sOut), file=GERRFILE)
            return sOut
        #print("updateCellAddrsExceptFixed:Btw:{}".format(sToken), file=GERRFILE)
        bCellAddr, (r,c), (rFixed, cFixed) = _celladdr_valid_ex(sToken)
        rOrig, cOrig = r, c
        # If not valid cell addr, skip it
        if not bCellAddr:
            iPos += len(sToken)
            continue
        # prepare the fixed $ tag anchors
        if rFixed:
            sRFixed ="$"
        else:
            sRFixed = ""
        if cFixed:
            sCFixed ="$"
        else:
            sCFixed = ""
        # A valid cell address, so update
        sBefore = sOut[0:iPos]
        sAfter = sOut[iPos+len(sToken):]
        if (r > afterR) and not rFixed:
            r += incR
        if (c > afterC) and not cFixed:
            c += incC
        # Check for invalid row or col after update
        sErr = ""
        if (r <= 0):
            sErr = "ErrR_"
            r = rOrig
        if (c <= 0):
            sErr += "ErrC_"
            c = cOrig
        sNewToken = "{}{}{}{}{}".format(sErr,sCFixed,coladdr_num2alpha(c),sRFixed,r)
        sOut = sBefore + sNewToken
        iPos = len(sOut)
        sOut += sAfter



def insert_rc_ab(cmd, args):
    '''
    Insert n number of rows or columns, before or after the current row|column.

    Call update_celladdr to adjust =expressions where required.
    '''
    bRowMode = False
    bColMode = False
    cnt = int(args)
    incR = 0
    incC = 0
    if cmd[1] == 'r':
        bRowMode = True
        incR = cnt
    elif cmd[1] == 'c':
        bColMode = True
        incC = cnt

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
        curData = me['data'][k]
        newData = curData
        if len(curData) > 0:
            if (type(curData) == str) and (curData[0] == '='):
                newData = update_celladdrs_all(curData, cR, incR, cC, incC, bUpdateFixed=True)
        newDict[(nR,nC)] = newData
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
    cnt = int(args)
    incR = incC = 0
    sR = me['curRow']
    sC = me['curCol']
    if cmd[1] == 'r':
        bRowMode = True
        eR = sR + cnt -1
        if eR > me['numRows']:
            eR = me['numRows']
        cnt = eR - sR + 1
        incR = -1*cnt
    elif cmd[1] == 'c':
        bColMode = True
        eC = sC + cnt -1
        if eC > me['numCols']:
            eC = me['numCols']
        cnt = eC - sC + 1
        incC = -1*cnt

    newDict = dict()
    for k in me['data']:
        r,c = k
        curData = me['data'][k]
        if len(curData) > 0:
            if (type(curData) == str) and (curData[0] == '='):
                curData = update_celladdrs_all(curData, sR-1, incR, sC-1, incC, bUpdateFixed=True)
        if bRowMode:
            if r < sR:
                newDict[k] = curData
            elif r > eR:
                newDict[(r+incR,c)] = curData
        if bColMode:
            if c < sC:
                newDict[k] = curData
            elif c > eC:
                newDict[(r,c+incC)] = curData
    me['data'] = newDict
    if bRowMode:
        me['numRows'] -= cnt
    if bColMode:
        me['numCols'] -= cnt



def _do_rcopy(scr, srcSKey, srcEKey, dstSKey, dstEKey, bAdjustCellAddrs=True):
    '''
    Copy a block of cells from src to dst.

    The Src and Dst blocks need not be same nor multiple of one another.
    If the Src block is bigger, then only the part that fits in the dst
    block will be copied.
    If the Src block is smaller, then it will be duplicated as required
    to fill the dst block.

    If bAdjustCellAddrs is true, then cell addresses in the copied =expressions
    will be adjusted as required.

    NOTE: Doesnt alert if overwriting cells with data|content in them.
    NOTE: Ensure that the source and dest blocks dont overlap. Else cell content may get corrupted.
    '''
    srcRLen = srcEKey[0] - srcSKey[0] + 1
    srcCLen = srcEKey[1] - srcSKey[1] + 1
    baseSrcR = srcSKey[0]
    baseSrcC = srcSKey[1]
    r = 0
    for dR in range(dstSKey[0], dstEKey[0]+1):
        sR = baseSrcR + (r%srcRLen)
        c = 0
        for dC in range(dstSKey[1], dstEKey[1]+1):
            sC = baseSrcC + (c%srcCLen)
            sData = me['data'].get((sR,sC))
            if (sData != None) and (sData != ""):
                if sData.startswith("=") and bAdjustCellAddrs:
                    incR = dR - sR
                    incC = dC - sC
                    sData = update_celladdrs_exceptfixed(sData, 0, incR, 0, incC)
            me['data'][(dR,dC)] = sData
            c += 1
        r += 1
    if dstEKey[0] > me['numRows']:
        me['numRows'] = dstEKey[0]
    if dstEKey[1] > me['numCols']:
        me['numCols'] = dstEKey[1]
    return True


def _do_rclear(scr, dstSKey, dstEKey):
    '''
    Clear a block of cells at dst.

    NOTE: Doesnt alert if clearing cells with data|content in them.
    '''
    for dR in range(dstSKey[0], dstEKey[0]+1):
        for dC in range(dstSKey[1], dstEKey[1]+1):
            me['data'].pop((dR,dC), None)
    return True


def _do_rgennums(scr, startKey, endKey, tokens):
    '''
    Add numeric content to cells starting from startKey to endKey
    with values from start with delta increments.
    '''
    if len(tokens) > 0:
        start = int(tokens[0])
    else:
        start = 1
    if len(tokens) > 1:
        delta = int(tokens[1])
    else:
        delta = 1
    curValue = start
    for r in range(startKey[0], endKey[0]+1):
        for c in range(startKey[1], endKey[1]+1):
            me['data'][(r,c)] = "={}".format(curValue)
            curValue += delta
    if endKey[0] > me['numRows']:
        me['numRows'] = endKey[0]
    if endKey[1] > me['numCols']:
        me['numCols'] = endKey[1]
    return True


def do_rcmd(scr, cmd, args):
    bDone = False
    try:
        print("rcmd:{} {}".format(cmd, args), file=GERRFILE)
        lCAddr, lPos = parse.get_celladdrs(args)
        lKeys = []
        for cAddr in lCAddr:
            bCellAddr, key = _celladdr_valid(cAddr)
            if not bCellAddr:
                return False
            lKeys.append(key)
            print("rcmd:btw:{} {}".format(cAddr, key), file=GERRFILE)
        if cmd == "rcopy":
            bDone = _do_rcopy(scr, lKeys[0], lKeys[1], lKeys[2], lKeys[3])
        elif cmd == "rcopyasis":
            bDone = _do_rcopy(scr, lKeys[0], lKeys[1], lKeys[2], lKeys[3], False)
        elif cmd == "rclear":
            bDone = _do_rclear(scr, lKeys[0], lKeys[1])
        elif cmd == "rgennums":
            tokens, types = parse.get_tokens(args, lPos[-1], ['-','+'])
            bDone = _do_rgennums(scr, lKeys[0], lKeys[1], tokens[1:])
        if bDone:
            me['dirty'] = True
        me['cdataUpdate'] = True
    except:
        traceback.print_exc(file=GERRFILE)
        bDone = False
    if not bDone:
        dlg(scr, [ "Failed:{} {}".format(cmd, args), "Press any key to continue..." ])



def _save_file(scr, sFile, filePass=None):
    '''
    Save file in a csv format.

    If the cell data contains the field seperator in it, then
    the cell content is protected within single quotes.

    If successfully saved, then Clear the dirty bit.

    If filePass is provided then encrypt the file.

    If the file already exists, then alert the user about same.
    '''
    if (os.path.exists(sFile)):
        got = dlg(scr, ["File:{}:exists overwrite? [Y/n]".format(sFile)])
        if chr(got).upper() == "N":
            status(scr, ["Saving is aborted"])
            return
        else:
            status(scr, ["Overwriting {}".format(sFile)])
    f = open(sFile,"w+")
    if filePass != None:
        salt = secrets.token_bytes(16)
        userKey, fileKey = sec.get_basekeys(filePass, salt)
        salt = base64.urlsafe_b64encode(salt).decode()
        print("{}\n".format(salt), end="", file=f)
    for r in range(1, me['numRows']+1):
        curRow = ""
        for c in range(1, me['numCols']+1):
            data = me['data'].get((r,c))
            if (data != None):
                if data.find(THEFIELDSEP) != -1:
                    if not data.startswith(THEQUOTE):
                        data = "{}{}".format(THEQUOTE, data)
                    if not data.endswith(THEQUOTE):
                        data = "{}{}".format(data, THEQUOTE)
            else:
                data = ""
            curRow += "{}{}".format(data,THEFIELDSEP)
        curRow = curRow[:-1] # Remove the unwanted fieldsep at the end
        if filePass != None:
            lineKey = sec.get_linekey(r, userKey, fileKey)
            if bInternalEncDec:
                curRow = sec.aes_cbc_enc_b64(base64.urlsafe_b64decode(lineKey), curRow).decode()
            else:
                sym = cryptography.fernet.Fernet(lineKey)
                curRow = sym.encrypt(curRow.encode()).decode()
            #status(scr, ["saving line {}".format(r)],y=1)
        print("{}\n".format(curRow), end="", file=f)
    f.close()
    me['dirty'] = False
    print("savefile:{}".format(sFile), file=GLOGFILE)


def save_file(scr, sFile, filePass=None):
    try:
        _save_file(scr, sFile, filePass)
    except:
        a,b,c = sys.exc_info()
        print("savefile:exception:{}:{}".format((a,b,c), sFile), file=GLOGFILE)
        traceback.print_exc(file=GERRFILE)
        dlg(scr, ["savefile:exception:{}:{}".format(a, sFile), "Press any key to continue"])


def _load_file(sFile, filePass=None):
    '''
    Load the specified csv file
    '''
    f = open(sFile)
    if filePass != None:
        line = f.readline()
        salt = base64.urlsafe_b64decode(line.encode())
        userKey, fileKey = sec.get_basekeys(filePass, salt)
    print("loadfile:{}".format(sFile), file=GLOGFILE)
    me['data'] = dict()
    r = 0
    for line in f:
        r += 1
        if filePass != None:
            lineKey = sec.get_linekey(r, userKey, fileKey)
            if bInternalEncDec:
                line = sec.aes_cbc_dec_b64(base64.urlsafe_b64decode(lineKey), line.encode()).decode()
            else:
                sym = cryptography.fernet.Fernet(lineKey)
                line = sym.decrypt(line.encode()).decode()
        c = 1
        i = 0
        sCur = ""
        bInQuote = False
        while i < (len(line)-1): # Remove the newline at the end
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
        if sCur != "":
            me['data'][(r,c)] = sCur
            sCur = ""
    f.close()
    me['numRows'] = r
    me['numCols'] = c
    print("loadfile:done:{}".format(me), file=GLOGFILE)


def load_file(scr, sFile, filePass=None):
    '''
    load the specified spreadsheet into memory.

    It checks if there is a dirty spreadsheet in memory, in which case, it gives option
    to user to abort the load_file operation.

    As a user could come out of help mode by using load_file, so it reverts from help mode,
    if that is the case.

    It clears the dirty flag.
    It clears the screen as well as repositions to A1 cell, if _load_file succeeds.
    '''
    if me['dirty']:
        got = dlg(scr, ["Spreadsheet not saved, discard and load new file? [y/N]".format(sFile)])
        if chr(got).upper() == "Y":
            status(scr, ["Loading file {}".format(sFile)])
        else:
            status(scr, ["Canceled loading of {}".format(sFile)])
            return False
    try:
        me['cdataUpdate'] = True
        scr.clear()
        _load_file(sFile, filePass)
        me['dirty'] = False
        revertfrom_help_ifneeded()
        goto_cell(scr, "A1")
        print("\033]2; {} [{}] \007".format("SpreadsheetKVC", sFile), file=sys.stdout)
        return True
    except:
        a,b,c = sys.exc_info()
        print("loadfile:exception:{}:{}".format((a,b,c), sFile), file=GLOGFILE)
        traceback.print_exc(file=GERRFILE)
        dlg(scr, ["loadfile:exception:{}:{}".format((a,b), sFile), "Press any key to continue"])
        return False


def load_help(scr):
    '''
    load help.csv file in readonly mode.

    If already in help mode, dont do anything.
    '''
    if me['helpModeSavedReadOnly'] != None:
        return
    if load_file(scr, "{}/help.csv".format(sys.path[0])):
        me['helpModeSavedReadOnly'] = me['readOnly']
        me['readOnly'] = True
    else:
        dlg(scr, ["loadhelp: save current spreadsheet or allow discarding of changes", "for loading the help file", "Press any key to continue"])



def revertfrom_help_ifneeded():
    '''
    Revert from help mode, if already in help mode.
    '''
    if me['helpModeSavedReadOnly'] != None:
        me['readOnly'] = me['helpModeSavedReadOnly']
        me['helpModeSavedReadOnly'] = None


def new_file(scr):
    '''
    Create a new spreadsheet in memory.

    It checks if there is a dirty spreadsheet in memory, in which case, it gives option
    to user to abort the new_file operation.

    As a user could come out of help mode by using new_file, so it reverts from help mode,
    if that is the case.
    '''
    if me['dirty']:
        got = dlg(scr, ["Spreadsheet not saved, discard and create new? [y/N]"])
        if chr(got).upper() == "Y":
            status(scr, ["Creating new spreadsheet in memory"])
        else:
            status(scr, ["Canceled new spreadsheet creation"])
            return False
    revertfrom_help_ifneeded()
    goto_cell(scr, "A1")
    me['data'] = dict()
    me['dirty'] = False
    me['cdataUpdate'] = True


def shell_cmd(scr, cmd, args):
    scr.clear()
    scr.refresh()
    curses.reset_shell_mode()
    if args == None:
        args = ""
    cmd = cmd[1:]
    os.system("{} {}".format(cmd, args))
    input("\nPress any key to return to program...")
    curses.reset_prog_mode()
    scr.clear()
    cdraw(scr)


def quit(scr):
    '''
    Check that no unsaved changes exists, before gracefully quiting.

    If any unsaved changes exist, then the decision is passed to the
    user to decide whether to quit or not. The default if user just
    presses enter is to NOT quit. User has to explicitly enter y or Y
    to exit.

    The exit code can be used to indicate whether there was any unsaved
    changes when quiting.
    '''
    if me['dirty']:
        got = dlg(scr, ["Unsaved changes, Do you want to quit [y/N]:"])
        if chr(got).upper() == 'Y':
            me['exit'] = 1
    else:
        me['exit'] = 0


def explicit_commandmode(stdscr, cmdArgs):
    '''
    Explicit Command mode, which is entered by pressing ':' followed by
    one of the commands mentioned below.

    w|s path/file_to_save;   l path/file_to_open
    pw|ps path/file_to_save; pl path/file_to_open
    dr delete row;           dc delete column
    irb num_of_rows
        insert n rows before current row
    ira num_of_rows
        insert n rows after current row
    icb num_of_cols
        insert n columns before current column
    ica num_of_cols
        insert n columns after current column
    e path/file_to_export_into
    clear to clear the current spreadsheet
    help - show the help.csv file in temporary-readonly help mode.
    new - create a new spreadsheet in memory.
    mro|mreadonly - set readonly mode;  mrw|mreadwrite - set readwrite mode.
    rcopy, rclear
    !shell_command arguments
    q to quit the program

    if program in readOnly mode, dont allow
        insert, delete and clear operations
    '''
    if cmdArgs.find(' ') == -1:
        cmd = cmdArgs
        args = None
    else:
        cmd,args = cmdArgs.split(' ',1)
    print("cmd:{}, args:{}".format(cmd,args), file=GLOGFILE)
    if (cmd == 'w') or (cmd == 's'):
        save_file(stdscr, args)
    elif (cmd == 'pw') or (cmd == 'ps'):
        filePass, args = args.split(' ',1)
        save_file(stdscr, args, filePass)
    elif cmd == 'l':
        load_file(stdscr, args)
    elif cmd == 'pl':
        filePass, args = args.split(' ',1)
        load_file(stdscr, args, filePass)
    elif cmd.startswith('i') and not me['readOnly']:
        if args == None:
            args = "1"
        insert_rc_ab(cmd, args)
        me['dirty'] = True
        me['cdataUpdate'] = True
    elif cmd.startswith('d') and not me['readOnly']:
        if args == None:
            args = "1"
        delete_rc(cmd, args)
        me['dirty'] = True
        me['cdataUpdate'] = True
    elif cmd.startswith('g'):
        if args != None:
            goto_cell(stdscr, args)
    elif cmd == 'help':
        load_help(stdscr)
    elif (cmd == 'clear') and not me['readOnly']:
        if len(me['data']) > 0:
            me['data'] = dict()
            me['dirty'] = True
            me['cdataUpdate'] = True
    elif (cmd == 'new'):
        new_file(stdscr)
    elif (cmd == 'mreadonly') or (cmd == 'mro'):
        me['readOnly'] = True
    elif (cmd == 'mreadwrite') or (cmd == 'mrw'):
        me['readOnly'] = False
    elif cmd.startswith("r") and not me['readOnly']:
        do_rcmd(stdscr, cmd, args)
    elif cmd.startswith("!"):
        shell_cmd(stdscr, cmd, args)
    elif cmd == 'q':
        quit(stdscr)


def _celladdr_valid_ex(sAddr):
    '''
    Check if the given string is a cell address or not.

    Extract the alpha col address and numeric row address.
    Ignore $ prefix if any wrt col or row address.
    If there is garbage beyond numeric row address, then mark invalid
    '''
    m=re.fullmatch("(?P<colFixed>[$]?)(?P<colAddr>[a-zA-Z]+)(?P<rowFixed>[$]?)(?P<rowAddr>[0-9]+)", sAddr)
    if m == None:
        return False, (None, None), (None, None)
    if m['colFixed'] == '$':
        bColFixed = True
    else:
        bColFixed = False
    if m['rowFixed'] == '$':
        bRowFixed = True
    else:
        bRowFixed = False
    alphaAddr = m['colAddr']
    numAddr = m['rowAddr']
    # Get the data key for the cell
    i = 0
    alphaAddr = alphaAddr.upper()
    numAlphaAddr = 0
    while i < len(alphaAddr):
        num = (ord(alphaAddr[i]) - ord('A'))+1
        numAlphaAddr = numAlphaAddr*26 + num
        i += 1
    return True, (int(numAddr), int(numAlphaAddr)), (bRowFixed, bColFixed)


def _celladdr_valid(sAddr):
    '''
    Check if given string is a valid cell address or not.

    If valid return the row and col addresses in numeric format.
    '''
    bValid, key, fixed = _celladdr_valid_ex(sAddr)
    return bValid, key


TRAPCALCLOOP_DATALENMULT = 4
def trap_calclooping_old(cellKey):
    curCalcCnt = me['calcCnt'].get(cellKey)
    if curCalcCnt == None:
        curCalcCnt = 0
    curCalcCnt += 1
    print("TrapCalcLoop:BTW:{}".format(me['calcCnt']), file=GERRFILE)
    if curCalcCnt > (len(me['data'])*TRAPCALCLOOP_DATALENMULT):
        print("TrapCalcLoop:NoNo:{}".format(me['calcCnt']), file=GERRFILE)
        newCalcThreshold = curCalcCnt - 2
        for key in me['calcCnt']:
            if me['calcCnt'][key] > newCalcThreshold:
                sData = me['data'].get(key)
                if sData != None:
                    if sData.startswith('='):
                        me['data'][key] = "ErrCalcLoop:{}".format(sData)
        raise RuntimeError("CalcLoop:{}:{}".format(cellKey, curCalcCnt))
    me['calcCnt'][cellKey] = curCalcCnt


CALLDEPTHMAX = 100
def trap_calclooping(cellKey):
    curCalcCnt = me['calcCnt'].get(cellKey)
    if curCalcCnt == None:
        curCalcCnt = 0
    curCalcCnt += 1
    #print("TrapCalcLoop:IN:{}:{}:{}".format(cellKey, me['callDepth'], curCalcCnt), file=GERRFILE)
    if me['callDepth'] > CALLDEPTHMAX:
        print("TrapCalcLoop:NoNo:{}:{}".format(me['callDepth'], me['calcCnt']), file=GERRFILE)
        for key in me['calcCnt']:
            sData = me['data'].get(key)
            if sData != None:
                if sData.startswith('='):
                    me['data'][key] = "ErrCalcLoop:{}".format(sData)
        raise RuntimeError("CalcLoop:{}:{}".format(cellKey, me['callDepth']))
    me['calcCnt'][cellKey] = curCalcCnt
    me['cdataUpdate'] = True


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


def _nvalue(sData):
    '''
    Evaluate the given expression.

    It identifies sub parts of the expression like functions, celladdresses,
    groups etc and then try and find their value.

    Finally evaluate the simplified expression using python.
    '''
    # Remove spaces and identify independent subparts that can be simplified/evaluated.
    evalParts, evalTypes = parse.get_evalparts(sData)
    sNew = ""
    for i in range(len(evalParts)):
        if evalTypes[i] == parse.EvalPartType.Func: # Handle functions
            sCmd, sArgs = evalParts[i].split('(',1)
            sArgs = sArgs[:-1]
            # Handle celladdress callDepth here, so that do_func and partners dont have to worry about same
            bHasCellAddr = False
            tlArgs, tlArgTypes = parse.get_evalparts(sArgs)
            for ti in range(len(tlArgTypes)):
                if tlArgTypes[ti] == parse.EvalPartType.AlphaNum:
                    tbCellAddr, tsCellAddr, tPos = parse.get_celladdr(tlArgs[ti])
                    if tbCellAddr and (tPos == 0):
                        bHasCellAddr = True
            # Evaluate the function
            if bHasCellAddr:
                me['callDepth'] += 1
            sVal = funcs.do_func(sCmd, sArgs)
            if bHasCellAddr:
                me['callDepth'] -= 1
            sNew += str(sVal)
        elif evalTypes[i] == parse.EvalPartType.AlphaNum: # Handle cell addresses
            me['callDepth'] += 1
            sNew += _cellvalue_or_str(evalParts[i])
            me['callDepth'] -= 1
        elif evalTypes[i] == parse.EvalPartType.Group: # Bracket grouped subexpression
            sVal = _nvalue(evalParts[i][1:-1])
            sNew += "({})".format(sVal)
        else:
            sNew += evalParts[i]
    # Evaluate
    try:
        #print("_nvalue:eval:{}:{}".format(sData, sNew), file=GERRFILE)
        val = eval(sNew)
    except:
        print("_nvalue:exception:{}:{}".format(sData, sNew), file=GERRFILE)
        traceback.print_exc(file=GERRFILE)
        val = None
    return val


bUseCachedData = True
def nvalue(addr):
    '''
    Return the numeric value associated with the given cell.
    It will either return None (if not numeric or error in expression)
    or else will return the numeric value associated with the cell.
    If the cell contains a =expression, it will be evaluated.

    If the cell doesnt contain any data, it will return 0.
    This is unity operation for add++ but not for mult++.
    '''
    if bUseCachedData:
        val = me['cdata'].get(addr)
        if val != None:
            return val
    val = me['data'].get(addr)
    #print("nvalue:{}:{}".format(addr,val), file=GERRFILE)
    if val == None:
        return 0
    if not val.startswith("="):
        return None
    trap_calclooping(addr)
    nval = _nvalue(val[1:])
    if bUseCachedData:
        me['cdata'][addr] = nval
    return nval


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


def copy_cell():
    me['copyData'] = me['data'].get((me['curRow'],me['curCol']))
    if me['copyData'] != None:
        me['copySrcCell'] = (me['curRow'], me['curCol'])


def paste_cell(bAdjustCellAddress=True):
    if me['copyData'] != None:
        theData = me['copyData']
        if bAdjustCellAddress:
            # Calculate row and col adjustment required
            incR = me['curRow'] - me['copySrcCell'][0]
            incC = me['curCol'] - me['copySrcCell'][1]
            # Adjust cell addresses if =expression
            if theData.startswith('='):
                theData = update_celladdrs_exceptfixed(theData, 0, incR, 0, incC)
        # Paste data
        me['data'][(me['curRow'],me['curCol'])] = theData
        me['dirty'] = True
        me['cdataUpdate'] = True


def rl_commandmode(stdscr, key):
    '''
    Handle keys wrt the implicit command mode.

    By pressing
        e one enters the edit mode.
        i one enters the insert edit mode.
        : one enters the explicit command mode.
        arrow keys one can move around the cells.
        D one can delete current cell's content.
        c helps copy cell data.
        C helps Cut cell data.
        p Paste cell data with cell address adjustment.
        P Paste cell data as it is.
        h|? show help dialog

    If program is in readOnly Mode, it wont allow
        edit, insert, cut, paste and delete operations.
    '''
    if (key == curses.KEY_UP):
        cellcur_up()
    elif (key == curses.KEY_DOWN):
        cellcur_down()
    elif (key == curses.KEY_LEFT):
        cellcur_left()
    elif (key == curses.KEY_RIGHT):
        cellcur_right()
    elif (key == ord('D')) and not me['readOnly']:
        if me['data'].pop((me['curRow'],me['curCol']), None) != None:
            me['dirty'] = True
            me['cdataUpdate'] = True
    elif (key == ord('c')):
        copy_cell()
    elif (key == ord('C')) and not me['readOnly']:
        copy_cell()
        if me['data'].pop((me['curRow'],me['curCol']), None) != None:
            me['dirty'] = True
            me['cdataUpdate'] = True
    elif (key == ord('p')) and not me['readOnly']:
        paste_cell(True)
    elif (key == ord('P')) and not me['readOnly']:
        paste_cell(False)
    elif (key == ord('i')) and not me['readOnly']:
        me['state'] = 'E'
        me['gotStr'] = ""
        me['crsrOffset'] = 0
        curData = me['data'].get((me['curRow'],me['curCol']))
        me['backupEdit'] = curData
        if curData != None:
            me['dirty'] = True
            me['data'][(me['curRow'],me['curCol'])] = ""
    elif (key == ord('e')) and not me['readOnly']:
        me['state'] = 'E'
        me['gotStr'] = me['data'].get((me['curRow'], me['curCol']))
        if me['gotStr'] == None:
            me['gotStr'] = ""
        me['crsrOffset'] = len(me['gotStr'])
        me['backupEdit'] = me['gotStr']
        me['data'][(me['curRow'],me['curCol'])] = ""
    elif (key == ord(':')):
        me['state'] = ':'
        me['gotStr'] = ""
        me['crsrOffset'] = 0
    elif (key == ord('h')) or (key == ord('?')):
        helpdlg.help_dlg(stdscr)
    return True


def setdata_from_savededitbuf(scr):
    '''
    This is used when returning from edit mode.

    If there is a backed up edit buffer
        either when user entered some content and pressed enter
        or when the initial cell content was saved while entering edit mode
    then save it to the cell.

    If backedup edit buffer starts with quote, but doesnt end with the quote,
    then add a quote to the end.

    strip backedup edit buffer of any whitespace at begin and end of the buffer,
    before saving to cell. However if the quote is there at begin and end, then
    the spaces wont be removed.
    '''
    # Restore/set data to the latest backedup edit buffer
    if (me['backupEdit'] != None) and (me['backupEdit'] != ""):
        # Handle quote at begining or only quote
        if me['backupEdit'][0] == THEQUOTE:
            if len(me['backupEdit']) == 1:
                me['backupEdit'] += THEQUOTE
            if me['backupEdit'][-1] != THEQUOTE:
                me['backupEdit'] += THEQUOTE
        # Handle quote at end
        if me['backupEdit'][-1] == THEQUOTE:
            if me['backupEdit'][0] != THEQUOTE:
                me['backupEdit'] = THEQUOTE + me['backupEdit']
        sData = me['backupEdit'].strip()
        # Handle any in between quote, rather replace with predefined placeholder
        iPos = 0
        while True:
            iPos = sData.find(THEQUOTE, iPos+1)
            if (iPos == -1) or (iPos == (len(sData)-1)):
                break
            sBefore = sData[:iPos]
            sAfter = sData[iPos+1:]
            sData = sBefore + THEALT2INBTWQUOTE + sAfter
        me['data'][(me['curRow'],me['curCol'])] = sData
    else:
        me['data'].pop((me['curRow'],me['curCol']), None)



def rl_editplusmode(stdscr, key):
    '''
    Handle key presses in edit/insert/explicit command modes

    ESC key allows returning back to the implicit command mode.
    Enter key either saves the text entry/changes till now to
        a temporary buffer, if in edit/insert mode.
            It also sets the dirty flag.
        Or trigger the explicit command handling logic in
        explicit command mode.
    '''
    if (key == curses.ascii.ESC):
        if me['state'] == 'E':
            setdata_from_savededitbuf(stdscr)
        me['state'] = 'C'
    elif (key == curses.KEY_BACKSPACE):
        if me['crsrOffset'] > 0:
            sBefore = me['gotStr'][0:me['crsrOffset']-1]
            sAfter = me['gotStr'][me['crsrOffset']:]
            me['gotStr'] = sBefore+sAfter
            me['crsrOffset'] -= 1
            if me['crsrOffset'] < 0:
                me['crsrOffset'] = 0
    elif (key == curses.ascii.NL):
        if me['state'] == 'E':
            me['backupEdit'] = me['gotStr']
            if gbEnterExitsEditMode:
                setdata_from_savededitbuf(stdscr)
                me['state'] = 'C'
            me['dirty'] = True
            me['cdataUpdate'] = True
        elif me['state'] == ':':
            explicit_commandmode(stdscr, me['gotStr'])
            me['state'] = 'C'
        print("runLogic:{}".format(me), file=GLOGFILE)
    elif key == curses.KEY_LEFT:
        me['crsrOffset'] -= 1
        if me['crsrOffset'] < 0:
            me['crsrOffset'] = 0
    elif key == curses.KEY_RIGHT:
        me['crsrOffset'] += 1
        if me['crsrOffset'] > len(me['gotStr']):
            me['crsrOffset'] = len(me['gotStr'])
    elif not key in CursesKeys: # chr(key).isprintable() wont do
        sBefore = me['gotStr'][0:me['crsrOffset']]
        sAfter = me['gotStr'][me['crsrOffset']:]
        me['gotStr'] = "{}{}{}".format(sBefore, chr(key), sAfter)
        me['crsrOffset'] += 1


def runlogic(stdscr):
    '''
    RunLogic between the Command and the other modes

    Command Mode: (Default/Implicit) This mode is used to
        navigate across the matrix of cells,
        As well as to copy/cut/paste/delete contents,
        As well as to enter insert/edit or explicit command mode.

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
                    curses.curs_set(0)
                rl_commandmode(stdscr, key)
            else:                       #### Edit+ Mode
                if bBackInC:
                    bBackInC = False
                    curses.curs_set(2)
                rl_editplusmode(stdscr, key)
            if me['exit'] != DONTEXIT:
                break
        except:
            print("runlogic exception", file=GLOGFILE)
            traceback.print_exc(file=GERRFILE)


def cwinsize_change(sig, whatelse):
    global stdscr
    #print("cwinsizechange:in:{}".format(me), file=GLOGFILE)
    cend(stdscr)
    stdscr=cstart()
    #print("cwinsizechange:ou:{}".format(me), file=GLOGFILE)


def setup_sighandlers():
    signal.signal(signal.SIGWINCH, cwinsize_change)


def setup_funcs():
    funcs.me = me
    funcs._celladdr_valid = _celladdr_valid
    funcs.nvalue = nvalue
    funcs._nvalue = _nvalue
    funcs.GLOGFILE = GLOGFILE
    funcs.GERRFILE = GERRFILE


def setup_logfile(logfile="/dev/null"):
    '''
    create a file handle for logging.
    '''
    f = open(logfile, "w+")
    return f


def setup_errfile(errfile=None):
    '''
    create a file handle for logging error data.

    If file name is not specified explicitly, then use named temp file to log errors.
    It is not deleted on program exit.
    '''
    if (errfile == None):
        return tempfile.NamedTemporaryFile(mode="w+", prefix="sskvc_", delete=False)
    else:
        return open(errfile, "w+")


GLOGFILE=None
GERRFILE=None
def setup_files():
    '''
    Setup the global file handles related to log and error data.
    '''
    global GLOGFILE, GERRFILE
    GLOGFILE=setup_logfile()
    GERRFILE=setup_errfile()


CmdArgs = enum.Enum("CmdArgs", "help fieldsep quote startnohelp mreadonly calldepth")
def print_usage():
    print("{}:spreadsheetkvc: usage".format(sys.argv[0]))
    print("    --{}          Prints this commandline usage info".format(CmdArgs.help.name))
    print('    --{} "{}"  Specify the csv field seperator to use'.format(CmdArgs.fieldsep.name, THEFIELDSEP))
    print('    --{} "{}"     Specify the csv field text quote to use'.format(CmdArgs.quote.name, THEQUOTE))
    print("    --{}   Dont show the help dialog at the start".format(CmdArgs.startnohelp.name))
    print("    --{}     run in readonly|view mode".format(CmdArgs.mreadonly.name))
    print("    --{} <depth>    specify the maximum call depth | cell chaining allowed".format(CmdArgs.calldepth.name))
    exit(0)


def process_cmdline(args):
    '''
    Process commandline arguments for the program
    '''
    global THEFIELDSEP
    global THEQUOTE
    global gbStartHelp
    global CALLDEPTHMAX
    i = 1
    while i < len(args):
        cmd = args[i][2:]
        if cmd == CmdArgs.fieldsep.name:
            i += 1
            THEFIELDSEP = args[i][0]
        elif cmd == CmdArgs.quote.name:
            i += 1
            THEQUOTE = args[i][0]
        elif cmd == CmdArgs.help.name:
            print_usage()
        elif cmd == CmdArgs.startnohelp.name:
            gbStartHelp = False
        elif cmd == CmdArgs.mreadonly.name:
            me['readOnly'] = True
        elif cmd == CmdArgs.calldepth.name:
            i += 1
            CALLDEPTHMAX = int(args[i])
        i += 1



### Main logic starts ###

setup_files()
process_cmdline(sys.argv)
stdscr=cstart()
cattr_textnum(stdscr)
setup_sighandlers()
setup_funcs()
try:
    if gbStartHelp:
        helpdlg.help_dlg(stdscr)
    runlogic(stdscr)
except Exception as e:
    print("exception:{}".format(e), file=GLOGFILE)
    print("exc_info:{}".format(sys.exc_info()), file=GLOGFILE)
    traceback.print_exc(file=GERRFILE)
    print("exception: done", file=GLOGFILE)
finally:
    stdscr.clear()
    stdscr.refresh()
    cend(stdscr)
    GLOGFILE.close()
exit(me['exit'])

# vim: set sts=4 expandtab: #
