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
import base64
import enum
import seckvc as sec
import helpdlg
import cuikvc as cui
import parsekvc as parse
import funcs
import re
import fileio
import edit, nav, syncd, cellval
import taber
import time


THEQUOTE = "'"
THEFIELDSEP = ';'
THEALT2INBTWQUOTE = '_'
DONTEXIT = -9999

GBFLYPYTHON = False
gbStartHelp = True
GBUSECOLOR  = False
GBRAWVIEW = False
GBSHOWCOLHDR = True


# How to differentiate text cells compared to =expression cells
# This is the default, cattr_textnum will try and adjust at runtime.
CATTR_DATATEXT = (curses.A_ITALIC | curses.A_DIM)
CATTR_DATANUM = (curses.A_NORMAL)

# How many columns to left or right of current display viewport should one
# peek to see, if there is any overflowing text that needs to be displayed.
DATACOL_OVERSCAN = 20

#Align = enum.Enum("Align", "Left Right Default Mixed")
Align = enum.Enum("Align", "Left Right Default")
GALIGN = Align.Default

# Exit EditMode on pressing Enter
gbEnterExitsEditMode = True


'''
Notes:
    State can be one of C, E or :

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
        'markers': dict(),
        'fpc': dict(),
        'tc': dict(),
        'cformat.iffloat': None,
        'cformat.number2float': False,
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
    stdscr = cui.cstart(GBUSECOLOR)
    cscreenadapt(stdscr)
    #print(me, file=GLOGFILE)
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


def cellstr(stdscr, r, c, msg, attr, clipToCell=True, clipToScreen=True, align=Align.Left):
    '''
    Display contents of the cell, only if it is in the current display viewport
    as well as if the cell (not its contents) can be fully shown on the screen.

    In viewport or not is got indirectly from the cellpos call.
    '''
    cellWidth = me['cellWidth']
    if clipToCell:
        if (align == Align.Left) or (align == Align.Default):
            tmsg = msg[0:cellWidth]
        else:
            tmsg = msg[-cellWidth:]
    else:
        tmsg = msg
    mlen = len(tmsg)
    if mlen < cellWidth:
        if (align == Align.Left) or (align == Align.Default):
            tmsg = "{:<{width}}".format(tmsg, width=cellWidth)
        else:
            tmsg = "{:>{width}}".format(tmsg, width=cellWidth)
    ty,tx = cellpos(r,c)
    cellWidth=0
    if ((tx < 0) or ((tx+cellWidth) > me['scrCols'])) or ((ty < 0) or ((ty+1) > me['scrRows'])) :
        return
    #print("cellstr:{},{}:{},{}:{}".format(r, c, ty, tx, tmsg), file=GERRFILE)
    cui.cellstr(stdscr, ty, tx, tmsg, attr, clipToScreen)


def dlg(scr, msgs, r=0, c=0, attr=curses.A_NORMAL):
    '''
    Show a simple dialog, with the messages passed to it.
    And return a keypress from the user.

    r,c are specified interms of matrix of data cells (except 0,
    which is always the top most row on screen) and not screen y,x
    and neither screen row,col.

    i.e the row and col of the cell in the matrix/table of data cells.
    So if the specified starting row/col relates to a data cell that
    is not visible, then the dlg wont be seen by user.
    '''
    ty,tx = cellpos(r,c)
    for i in range(len(msgs)):
        cui.cellstr(scr, ty+i, tx, msgs[i], attr)
    return scr.getch()


def status(scr, msgs, r=0, c=0, attr=curses.A_NORMAL):
    '''
    Display the messages passed to it at a given location.
    If location not given, then show at top left corner.

    r,c are specified interms of matrix of data cells (except 0,
    which is always the top most row on screen) and not screen y,x
    and neither screen row,col.

    i.e the row and col of the cell in the matrix/table of data cells.
    So if the specified starting row/col relates to a data cell that
    is not visible, then the status wont be seen by user.
    '''
    ty,tx = cellpos(r,c)
    for i in range(len(msgs)):
        cui.cellstr(scr, ty+i, tx, msgs[i], attr)
    scr.refresh()


def cstatusbar(scr, msg, height=-1, width=-1):
    '''
    Used to show a status bar for the program, at the bottom right corner.
    '''
    if height == -1:
        height = len(msg)
    if width == -1:
        for l in msg:
            if width < len(l):
                width = len(l)
        width += 6
    cui.status(scr, msg, y=me['scrRows']-height,x=me['scrCols']-width)


def cellcur(stdscr, r, c):
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
    ty,tx = cellpos(r,c)
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


def coladdr_num2alpha(iAddr):
    '''
    Generate alphabetic col address given the column number.
    The column number starts from 1 internally (and not 0).
    '''
    curAddr = iAddr - 1
    sAddr = ""
    while True:
        low = curAddr%26
        sAddr = (chr(ord('A')+low) + sAddr)
        up = int(curAddr/26)
        if up == 0:
            break
        curAddr = (up - 1)
    return sAddr


def _cdraw_coladdrs(colStart, colEnd):
    '''
    As columns are named alphabetically and not numerically, so the
    internal numeric address is changed to equivalent alphabetic address.
    '''
    if not GBSHOWCOLHDR:
        return
    for i in range(colStart, colEnd+1):
        if (i == me['curCol']):
            ctype = curses.A_NORMAL
        else:
            ctype = curses.A_REVERSE
        sColAddr = coladdr_num2alpha(i)
        cellstr(stdscr, 0, i, "{:^{width}}".format(sColAddr, width=me['cellWidth']-1), ctype)


def _cdraw_rowaddrs(rowStart, rowEnd):
    '''
    Show the row numbers in the address col at the left.

    It centers the row numbers, shown.
    '''
    for i in range(rowStart, rowEnd+1):
        if not GBUSECOLOR:
            if (i == me['curRow']):
                ctype = curses.A_NORMAL
            else:
                ctype = curses.A_REVERSE
        else:
            if (i == me['curRow']):
                ctype = curses.A_REVERSE
            else:
                ctype = curses.A_NORMAL
            if (i%2) == 0:
                ctype |= curses.color_pair(2)
            else:
                ctype |= curses.color_pair(1)
        cellstr(stdscr, i, 0, "{:^{width}}|".format(i, width=me['cellWidth']-1), ctype)


def _cdata_update(rStart, cStart, rEnd, cEnd):
    '''
    Cache data calculation results for the given block of cells, if not already cached.

    If exception, then ignore that cell and try calculating other cells in the specified block.
    Just in case if the exception is due to a long chain of cells in calc, then trying other cells
    and coming back later to this cell, could potentially help build the solution part by part.

    Caching is handled by nvalue_key logic.

    If any exceptions while handling the block, it will return to the caller which cells had a
    recursion limit exception and which cells if any had other exceptions.
    '''
    bRecursionError = False
    bException = False
    lExcCells = []
    lRecCells = []
    for r in range(rStart, rEnd+1):
        for c in range(cStart, cEnd+1):
            data = me['cdata'].get((r,c))
            if data != None:
                continue
            me['calcCnt'] = dict()
            me['callDepth'] = 0
            try:
                val = cellval.nvalue_key((r,c))
            except RecursionError:
                bRecursionError = True
                lRecCells.append((r,c))
            except:
                bException = True
                lExcCells.append((r,c))
                print("_cdata_update:exception:{}".format((r,c)), file=GERRFILE)
                traceback.print_exc(file=GERRFILE)
    return bRecursionError, lRecCells, bException, lExcCells


ERREXCEPTION = "#ErrExc#"
ERRLOOP = "#ErrLop#"
def cdata_update(bClearCache=True, rStart=1, cStart=1, rEnd=-1, cEnd=-1):
    '''
    Help calculate, if needed, and cache calcd values for a given block of cells.

    If there is recursion limit errors, even after multiple tries, then it will
    force a all cells calc mode/phase. Which should help build solution for all
    cells over multiple passes. NOTE: The i loop provides this multi pass, when
    j loop is at j == 1, because full set of cells is tried to be calculated
    as best as possible in any given pass, thus building over prev evaluated cells,
    in deep chained scenarios.
    '''
    if bClearCache:
        me['cdata'] = dict()
    if rEnd == -1:
        rEnd = me['numRows']
    if cEnd == -1:
        cEnd = me['numCols']
    for j in range(2):
        for i in range(4):
            bRecErr, lRecCells, bExc, lExcCells = _cdata_update(rStart, cStart, rEnd, cEnd)
            if not bRecErr:
                break
            print("cdata_update:{},{}-{},{}:{}:recover".format(rStart, cStart, rEnd, cEnd, j*10+i), file=GERRFILE)
        if not bRecErr:
            break
        print("cdata_update:{},{}-{},{}:fullcalc".format(rStart, cStart, rEnd, cEnd), file=GERRFILE)
        rStart, cStart = 1, 1
        rEnd, cEnd = me['numRows'], me['numCols']
    for eCell in lExcCells:
        me['data'][eCell] = ERREXCEPTION+me['data'][eCell]
    for eCell in lRecCells:
        me['data'][eCell] = ERRLOOP+me['data'][eCell]


bNumericDisplayOverflow=True
def _cdraw_data(scr, rowStart, rowEnd, colStart, colEnd):
    '''
    Display the cells which are currently visible on the screen.
    '''
    #print("cdrawdata:Starting", file=GERRFILE)
    # Adjust the data viewport
    if (GALIGN == Align.Left) or (GALIGN == Align.Default):
        dataColStart = colStart - DATACOL_OVERSCAN
        if dataColStart < 1:
            dataColStart = 1
        dataColEnd = colEnd
        crangeStart = dataColStart
        crangeEnd = dataColEnd+1
        crangeDelta = 1
        align = Align.Left
    else:
        dataColStart = colStart
        dataColEnd = colEnd + DATACOL_OVERSCAN
        if dataColEnd > me['numCols']:
            dataColEnd = me['numCols']
        crangeStart = dataColEnd
        crangeEnd = dataColStart-1
        crangeDelta = -1
        align = Align.Right
    # Evaluate any cells in the viewport that may require to be evaluated
    if me['state'] != 'E':
        cstatusbar(scr, ['[status: processing ...]'], 1, 32)
    cdata_update(me['cdataUpdate'], rowStart, dataColStart, rowEnd, dataColEnd)
    me['cdataUpdate'] = False
    if me['state'] != 'E':
        cstatusbar(scr, ['                        '], 1, 32)
    # Update the display
    rtype = CATTR_DATATEXT
    for r in range(rowStart, rowEnd+1):
        sRemaining = ""
        for c in range(crangeStart, crangeEnd, crangeDelta):
            curAlign = align
            if ((r == me['curRow']) and (c == me['curCol'])):
                ctype = curses.A_REVERSE
            else:
                ctype = curses.A_NORMAL
            data = cellval.value_key((r,c), GBRAWVIEW)
            #print("cdrawdata: {},{}={}".format(r,c,data), file=GLOGFILE)
            if (data != ""):
                if type(data) != str:
                    ctype |= CATTR_DATANUM
                    if type(data) == int:
                        num2flt = me.get('cformat.number2float')
                        if num2flt:
                            try:
                                data = data * 1.0
                            except:
                                pass
                    sData = str(data)
                    if type(data) == float:
                        floatPrecision = me.get('cformat.iffloat')
                        if floatPrecision != None:
                            sData = "{:.{preci}f}".format(data, preci=floatPrecision)
                    if bNumericDisplayOverflow:
                        if (GALIGN == Align.Left) or ((GALIGN == Align.Default) and (len(sData) > me['cellWidth'])):
                            sRemaining = sData[me['cellWidth']:]
                            sData = sData[:me['cellWidth']]
                        else:
                            curAlign = Align.Right # Align numbers to right, if it fits in a cell, in default mode.
                            sRemaining = sData[:-me['cellWidth']]
                            sData = sData[-me['cellWidth']:]
                    else:
                        sRemaining = ""
                    rtype = CATTR_DATANUM
                else:
                    sData = data
                    ctype |= CATTR_DATATEXT
                    if (GALIGN == Align.Left) or (GALIGN == Align.Default):
                        sRemaining = sData[me['cellWidth']:]
                        sData = sData[:me['cellWidth']]
                    else:
                        sRemaining = sData[:-me['cellWidth']]
                        sData = sData[-me['cellWidth']:]
                    rtype = CATTR_DATATEXT
            elif (not me['clipCell']):
                ctype |= rtype
                if (GALIGN == Align.Left) or (GALIGN == Align.Default):
                    sData = sRemaining[0:me['cellWidth']]
                    sRemaining = sRemaining[me['cellWidth']:]
                else:
                    sData = sRemaining[-me['cellWidth']:]
                    sRemaining = sRemaining[:-me['cellWidth']]
                #if (sData != ""):
                #    print("cdrawdata:overflow:{}+{}".format(sData, sRemaining), file=GLOGFILE)
            else: # data == "" AND clipCell
                ctype |= CATTR_DATATEXT
                sData = ""
            if (c < colStart):
                continue
            if GBUSECOLOR:
                if (r%2) == 0:
                    ctype |= curses.color_pair(2)
                else:
                    ctype |= curses.color_pair(1)
            cellstr(stdscr, r, c, str(sData), ctype, clipToCell=True, align=curAlign)


def _cdraw_editbuffer(stdscr):
    '''
    Show the edit buffer as required, if in Edit or Explicit command mode.
    '''
    if me['state'] == 'E':
        cellstr(stdscr, me['curRow'], me['curCol'], me['gotStr'], curses.A_REVERSE, clipToCell=False, clipToScreen=False)
    if me['state'] == ':':
        #cellstr(stdscr, me['numRows']-1, 0, me['gotStr'], curses.A_REVERSE, False)
        if GBSHOWCOLHDR:
            cellstr(stdscr, 0, 0, "{:{width}}".format(' ', width=len(me['gotStr'])+8), curses.A_REVERSE, clipToCell=False, clipToScreen=False)
        else:
            cellstr(stdscr, 0, 0, "{:{width}}".format(' ', width=me['scrCols']), curses.A_REVERSE, clipToCell=False, clipToScreen=False)
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
    if me['state'] == 'C':
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
        _cdraw_data(stdscr, rowStart, rowEnd, colStart, colEnd)
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


bConvertTextOnly = True
def replace_incontent(cOld, cNew):
    '''
    Convert given old char in cell contents with the new replacement char.

    If bConvertTextOnly is True, then it doesnt touch cells whose contents start with
    '=' character.

    [ForFuture:TODO: If we make cells store basic python types int,float,text as strings
    with no special prefix to identify non text values]
    Ensure that the old char specified is not part of valid integer or float values,
    else it may get replaced from integer and float values also.
    '''
    for r in range(1, me['numRows']+1):
        for c in range(1, me['numCols']+1):
            sData = me['data'].get((r,c))
            if (sData != None):
                if bConvertTextOnly and (sData[0] == '='):
                    continue
                sData = sData.replace(cOld, cNew)
                me['data'][(r,c)] = sData


def _do_calign(cmd, lArgs):
    '''
    configure the global alignment
    '''
    global GALIGN
    if (lArgs[0] == 'left'):
        GALIGN = Align.Left
    elif (lArgs[0] == 'right'):
        GALIGN = Align.Right
    elif (lArgs[0] == 'default'):
        GALIGN = Align.Default
    else:
        raise Exception('calign: Invalid argument')


def _do_cformat(cmd, lArgs):
    '''
    configure global formatting

    NOTE: If these return None, and inturn they are used as part of a =config(cformat
    expression in a cell, then as None results arent cached, so they will get executed
    each time the corresponding cell is displayed. This can allow one to selectively
    change formating for few cells in a hackish way. But it will require the =config
    expression to be on either side of the cells which needs formating, because depending
    on global left or right alignment, the cells may be evaluated in either direction.
    But this is not guarenteed to work always, and behaviour may change in future.

        Also it leads to a ugly None result shown corresponding to the cell with the
        =config(cformat... expression.
    '''
    if lArgs[0] == "iffloat":
        if lArgs[1].upper() == 'NONE':
            me['cformat.iffloat'] = None
        else:
            me['cformat.iffloat'] = int(lArgs[1])
        return "'FltPreci:{}'".format(me['cformat.iffloat'])
        #return round(1.11111111111111111111, me['cformat.iffloat'])
        #return 1.11111111111111111111
    elif lArgs[0] == "number2float":
        if lArgs[1].upper() == 'NO':
            me['cformat.number2float'] = False
        elif lArgs[1].upper() == 'YES':
            me['cformat.number2float'] = True
        else:
            raise Exception('cformat: Invalid argument')
        return "'Num2Float:{}'".format(me['cformat.number2float'])
    elif lArgs[0] == "neat":
        me['cformat.number2float'] = True
        me['cformat.iffloat'] = 2
        return "'CFormat:Neat'"
    elif lArgs[0] == "raw":
        me['cformat.number2float'] = False
        me['cformat.iffloat'] = None
        return "'CFormat:Raw'"


def do_ccmd(scr, cmd, args):
    '''
    The Config commands handling

    cro, crw
    cfs, ctq
    calign, cformat,
    '''
    global THEFIELDSEP, THEQUOTE

    print("ccmd:{}, args:{}".format(cmd,args), file=GERRFILE)
    if (cmd == 'creadonly') or (cmd == 'cro'):
        me['readOnly'] = True
    elif (cmd == 'creadwrite') or (cmd == 'crw'):
        me['readOnly'] = False
    elif (cmd == 'cfieldsep') or (cmd == 'cfs'):
        fieldSep = args.split(' ',1)[0]
        if (len(fieldSep) == 2) and (fieldSep == '\\t'):
            fieldSep = '\t'
        if len(fieldSep) != 1:
            dlg(scr, ['fieldsep:invalid[{}]: need singleChar like ; or , or \\t'.format(fieldSep), 'Press any key...'])
        else:
            #replace_incontent(THEFIELDSEP, args[0])
            THEFIELDSEP = fieldSep
            dlg(scr, ['fieldsep: updated [{}]'.format(THEFIELDSEP), 'Press any key...'])
    elif (cmd == 'ctextquote') or (cmd == 'ctq'):
        cstatusbar(scr, ['update textquote'])
        replace_incontent(args[0], THEALT2INBTWQUOTE)
        replace_incontent(THEQUOTE, args[0])
        THEQUOTE = args[0]
    elif cmd.startswith('calign'):
        lArgs, lTypes = parse.get_tokens(args)
        _do_calign(cmd, lArgs)
    elif cmd.startswith('cformat'):
        lArgs, lTypes = parse.get_tokens(args)
        _do_cformat(cmd, lArgs)
    setup_fileio()


def do_xcmd(scr, cmd, args):
    '''
    The x commands handling
    '''
    global GBRAWVIEW

    if (cmd == 'xrecalc'):
        me['cdataUpdate'] = True
    elif (cmd == 'xrows'):
        newRows = int(args)
        if newRows < me['numRows']:
            dlg(scr, ["xrows: cant reduce the number of rows", "Use dr to remove rows, as required"])
            return
        me['numRows'] = newRows
    elif (cmd == 'xcols'):
        newCols = int(args)
        if newCols < me['numCols']:
            dlg(scr, ["xcols: cant reduce the number of cols", "Use dc to remove cols, as required"])
            return
        me['numCols'] = newCols
    elif (cmd == 'xviewraw'):
        GBRAWVIEW = True
    elif (cmd == 'xviewnormal'):
        GBRAWVIEW = False


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


def path_completion(fpc, cmdArgs):
    # Extract the args
    if cmdArgs.find(' ') == -1:
        cmd = cmdArgs
        args = ""
    else:
        cmd, args = cmdArgs.split(' ',1)
    # Check if its a valid command
    if (cmd in ['w', 's', 'l', '!ls']):
        theArg = args
        theBase = cmd
    elif (cmd in ['pw', 'ps', 'pl']):
        if args == "":
            return cmd + " SPECIFY**YouR@FilEPassWord**"
        if args.find(' ') == -1:
            theBase =  "{} {}".format(cmd, args)
            theArg = ""
        else:
            lArgs = args.split(' ',1)
            theBase =  "{} {}".format(cmd, lArgs[0])
            theArg = lArgs[1]
    else:
        #return cmdArgs
        return taber.tab_complete(me['tc'], taber.treeDB, cmdArgs)
    # Try find a path
    if theArg == "":
        theArg = "~"
    theArg = os.path.expanduser(theArg)
    sNew = fileio.path_completion(fpc, theArg)
    return "{} {}".format(theBase, sNew)


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
    cro|creadonly - set readonly mode;  crw|creadwrite - set readwrite mode.
    rcopy[asis], rclear[err]
    mcmds (mclear, mshow, mmarkerid)
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
        fileio.save_file(me, stdscr, args)
    elif (cmd == 'pw') or (cmd == 'ps'):
        filePass, args = args.split(' ',1)
        fileio.save_file(me, stdscr, args, filePass)
    elif cmd == 'l':
        fileio.load_file(me, stdscr, args)
    elif cmd == 'pl':
        filePass, args = args.split(' ',1)
        fileio.load_file(me, stdscr, args, filePass)
    elif cmd.startswith('i') and not me['readOnly']:
        if args == None:
            args = "1"
        cstatusbar(stdscr, ['[insert in progress...]'])
        t1 = time.time()
        edit.insert_rc_ab(cmd, args)
        t2 = time.time()
        print("DBUG:InsertRC:{}".format(t2-t1), file=GERRFILE)
        cstatusbar(stdscr, ['[sync deps progress...]'])
        syncd.create_links()
        cstatusbar(stdscr, ['                       '])
        me['dirty'] = True
        # insert_rc_ab adjusts calc cache as required so not force clearing full cache.
        #me['cdataUpdate'] = True
    elif cmd.startswith('d') and not me['readOnly']:
        if args == None:
            args = "1"
        cstatusbar(stdscr, ['[delete in progress...]'])
        t1 = time.time()
        edit.delete_rc(cmd, args)
        t2 = time.time()
        print("DBUG:DeleteRC:{}".format(t2-t1), file=GERRFILE)
        cstatusbar(stdscr, ['[sync deps progress...]'])
        syncd.create_links()
        cstatusbar(stdscr, ['                       '])
        me['dirty'] = True
        # delete_rc adjusts calc cache as required so not force clearing full cache.
        #me['cdataUpdate'] = True
    elif cmd.startswith('g'):
        if args != None:
            nav.goto_cell(stdscr, args)
    elif cmd == 'help':
        fileio.load_help(me, stdscr)
    elif (cmd == 'clear') and not me['readOnly']:
        if len(me['data']) > 0:
            me['data'] = dict()
            syncd.create_links()
            me['dirty'] = True
            me['cdataUpdate'] = True
    elif (cmd == 'new'):
        fileio.new_file(me, stdscr)
    elif (cmd[0] == 'c'):
        do_ccmd(stdscr, cmd, args)
    elif cmd.startswith("r") and not me['readOnly']:
        edit.do_rcmd(stdscr, cmd, args)
    elif cmd[0] == 'm':
        if args == None:
            args = ""
        edit.do_mcmd(stdscr, cmd, args)
    elif (cmd[0] == 'x'):
        do_xcmd(stdscr, cmd, args)
    elif cmd.startswith("!"):
        shell_cmd(stdscr, cmd, args)
    elif cmd == 'q':
        quit(stdscr)


def cell_key2addr(key):
    '''
    Convert the cells dictionary key to alphanumeric cell addr
    '''
    r,c = key
    return "{}{}".format(coladdr_num2alpha(c),r)


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
    global GBSHOWCOLHDR

    if (key == curses.KEY_UP):
        nav.cellcur_up()
    elif (key == curses.KEY_DOWN):
        nav.cellcur_down()
    elif (key == curses.KEY_LEFT):
        nav.cellcur_left()
    elif (key == curses.KEY_RIGHT):
        nav.cellcur_right()
    elif (key == ord('D')) and not me['readOnly']:
        edit.del_cell()
    elif (key == ord('c')):
        edit.copy_cell()
    elif (key == ord('C')) and not me['readOnly']:
        edit.cut_cell()
    elif (key == ord('p')) and not me['readOnly']:
        edit.paste_cell(True)
    elif (key == ord('P')) and not me['readOnly']:
        edit.paste_cell(False)
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
        GBSHOWCOLHDR = False
    elif (key == ord('h')) or (key == ord('?')):
        helpdlg.help_dlg(stdscr)
    return True


def text_textquote_safe(sIn, theQuote=None):
    '''
    Make text string textquote safe

    If textquote is there only at the begin or end of string, add to other end.
    If textquote somewhere inbetween in the string, replace it with predefined placeholder.
    '''
    if theQuote == None:
        theQuote = THEQUOTE
    # Handle quote at begining or only quote
    if sIn[0] == theQuote:
        if len(sIn) == 1:
            sIn += theQuote
        if sIn[-1] != theQuote:
            sIn += theQuote
    # Handle quote at end
    if sIn[-1] == theQuote:
        if sIn[0] != theQuote:
            sIn = theQuote + sIn
    sData = sIn.strip()
    # Handle any in between quote, rather replace with predefined placeholder
    iPos = 0
    while True:
        iPos = sData.find(theQuote, iPos+1)
        if (iPos == -1) or (iPos == (len(sData)-1)):
            break
        sBefore = sData[:iPos]
        sAfter = sData[iPos+1:]
        sData = sBefore + THEALT2INBTWQUOTE + sAfter
    return sData


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
        sData = text_textquote_safe(me['backupEdit'])
        me['data'][(me['curRow'],me['curCol'])] = sData
    else:
        me['data'].pop((me['curRow'],me['curCol']), None)


def tabcomplete_clear():
    me['gotStrUpdated'] = False
    me['gotStrBase'] = ""


def tabcomplete_baseupdate():
    me['gotStrUpdated'] = True


def tabcomplete_usebase():
    if me['gotStrUpdated']:
        me['gotStrBase'] = me['gotStr']
        me['gotStrUpdated'] = False


def _colhdr_explicit_rcmds():
    '''
    Enable col hdr for certain commands in the explicit cmd mode.

    currently it is enabled for the explicit rcmds.
    '''
    global GBSHOWCOLHDR

    if me['state'] == ':':
        if (me['gotStr'] != None) and (me['gotStr'].startswith('r')):
            GBSHOWCOLHDR = True
        else:
            GBSHOWCOLHDR = False


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
    global GBSHOWCOLHDR

    if (key == curses.ascii.ESC):
        tabcomplete_clear()
        GBSHOWCOLHDR = True
        if me['state'] == 'E':
            setdata_from_savededitbuf(stdscr)
        me['state'] = 'C'
    elif (key == curses.KEY_BACKSPACE):
        if me['crsrOffset'] > 0:
            _colhdr_explicit_rcmds()
            tabcomplete_baseupdate()
            sBefore = me['gotStr'][0:me['crsrOffset']-1]
            sAfter = me['gotStr'][me['crsrOffset']:]
            me['gotStr'] = sBefore+sAfter
            me['crsrOffset'] -= 1
            if me['crsrOffset'] < 0:
                me['crsrOffset'] = 0
    elif (key == curses.ascii.NL):
        tabcomplete_clear()
        GBSHOWCOLHDR = True
        if me['state'] == 'E':
            me['backupEdit'] = me['gotStr']
            if gbEnterExitsEditMode:
                setdata_from_savededitbuf(stdscr)
                me['state'] = 'C'
            me['dirty'] = True
            # sync up things
            #me['cdataUpdate'] = True
            tData = me['data'].get((me['curRow'],me['curCol']))
            if tData != None:
                syncd.cell_updated((me['curRow'], me['curCol']), tData, clearedSet=set())
        elif me['state'] == ':':
            explicit_commandmode(stdscr, me['gotStr'])
            me['state'] = 'C'
            me['fpc'] = dict()
            me['tc'] = dict()
        #print("runLogic:{}".format(me), file=GLOGFILE)
    elif key == curses.KEY_LEFT:
        me['crsrOffset'] -= 1
        if me['crsrOffset'] < 0:
            me['crsrOffset'] = 0
    elif key == curses.KEY_RIGHT:
        me['crsrOffset'] += 1
        if me['crsrOffset'] > len(me['gotStr']):
            me['crsrOffset'] = len(me['gotStr'])
    elif key == curses.ascii.TAB:
        if me['state'] == ':':
            _colhdr_explicit_rcmds()
            tabcomplete_usebase()
            sNew = path_completion(me['fpc'], me['gotStrBase'])
            me['gotStr'] = sNew
            me['crsrOffset'] = len(me['gotStr'])
    elif not key in CursesKeys: # chr(key).isprintable() wont do
        sBefore = me['gotStr'][0:me['crsrOffset']]
        sAfter = me['gotStr'][me['crsrOffset']:]
        me['gotStr'] = "{}{}{}".format(sBefore, chr(key), sAfter)
        me['crsrOffset'] += 1
        tabcomplete_baseupdate()
        _colhdr_explicit_rcmds()


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


def setup_parse(load=False):
    parse.GLOGFILE = GLOGFILE
    parse.GERRFILE = GERRFILE
    if load:
        parse.load_cext()


def setup_cellval():
    cellval.GBFLYPYTHON = GBFLYPYTHON
    if GBFLYPYTHON:
        cellval.GBTEXT2ZERO = False
    else:
        cellval.GBTEXT2ZERO = True
    cellval.me = me
    cellval.GLOGFILE = GLOGFILE
    cellval.GERRFILE = GERRFILE


def setup_funcs():
    if GBFLYPYTHON:
        funcs.BFILTERPYFUNC = False
    else:
        funcs.BFILTERPYFUNC = True
    funcs.me = me
    funcs.GLOGFILE = GLOGFILE
    funcs.GERRFILE = GERRFILE
    funcs._do_cformat = _do_cformat


def setup_fileio(load=False):
    fileio.GLOGFILE = GLOGFILE
    fileio.GERRFILE = GERRFILE
    fileio.THEQUOTE = THEQUOTE
    fileio.THEFIELDSEP = THEFIELDSEP
    fileio.dlg = dlg
    fileio.status = status
    fileio.cstatusbar = cstatusbar
    if load:
        fileio.load_cext()


def setup_edit():
    edit.GLOGFILE = GLOGFILE
    edit.GERRFILE = GERRFILE
    edit.me = me
    edit.dlg = dlg
    edit.cstatusbar = cstatusbar
    edit.cell_key2addr = cell_key2addr
    edit.coladdr_num2alpha = coladdr_num2alpha


def setup_nav():
    nav.me = me
    nav.cdraw = cdraw
    nav.cellcur = cellcur


def setup_syncd():
    syncd.GLOGFILE = GLOGFILE
    syncd.GERRFILE = GERRFILE
    syncd.me = me
    syncd.init()


def setup_helpermodules():
    setup_parse(True)
    setup_syncd()
    setup_cellval()
    setup_funcs()
    setup_nav()
    setup_fileio(True)
    setup_edit()
    tabcomplete_clear()


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


CmdArgs = enum.Enum("CmdArgs", "help fieldsep quote startnohelp creadonly calldepth flypython usecolor")
def print_usage():
    print("{}:spreadsheetkvc: usage".format(sys.argv[0]))
    print("    --{}          Prints this commandline usage info".format(CmdArgs.help.name))
    print('    --{} "{}"  Specify the csv field seperator to use'.format(CmdArgs.fieldsep.name, THEFIELDSEP))
    print('    --{} "{}"     Specify the csv field text quote to use'.format(CmdArgs.quote.name, THEQUOTE))
    print("    --{}   Dont show the help dialog at the start".format(CmdArgs.startnohelp.name))
    print("    --{}     run in readonly|view mode".format(CmdArgs.creadonly.name))
    print("    --{} <depth>    specify the maximum call depth | cell chaining allowed".format(CmdArgs.calldepth.name))
    print("    --{}     allow more varied python expressions in cells".format(CmdArgs.flypython.name))
    print("    --{}      use alternate color rows on the terminal".format(CmdArgs.usecolor.name))
    exit(0)


def process_cmdline(args):
    '''
    Process commandline arguments for the program
    '''
    global THEFIELDSEP
    global THEQUOTE
    global gbStartHelp
    global CALLDEPTHMAX, GBFLYPYTHON, GBUSECOLOR
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
        elif cmd == CmdArgs.creadonly.name:
            me['readOnly'] = True
        elif cmd == CmdArgs.calldepth.name:
            i += 1
            CALLDEPTHMAX = int(args[i])
        elif cmd == CmdArgs.flypython.name:
            GBFLYPYTHON = True
        elif cmd == CmdArgs.usecolor.name:
            GBUSECOLOR = True
        i += 1



### Main logic starts ###

setup_files()
process_cmdline(sys.argv)
stdscr=cstart()
cattr_textnum(stdscr)
setup_sighandlers()
setup_helpermodules()
sys.setrecursionlimit(5000)
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
