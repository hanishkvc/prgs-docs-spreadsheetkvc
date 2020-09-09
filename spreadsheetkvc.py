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
import edit


THEQUOTE = "'"
THEFIELDSEP = ';'
THEALT2INBTWQUOTE = '_'
DONTEXIT = -9999

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
        'markers': dict(),
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


def cellstr(stdscr, r, c, msg, attr, clipToCell=True, clipToScreen=True):
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


def _cdata_update(rStart, cStart, rEnd, cEnd):
    '''
    Cache data calculation results.
    If exception, then dont store anything. Just in case if the exception
    is due to a long chain of cells in calc, then retrying it will help build
    the solution part by part.
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
                val = nvalue_key((r,c))
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
    dataColStart = colStart - DATACOLSTART_OVERSCAN
    if dataColStart < 1:
        dataColStart = 1
    if me['state'] != 'E':
        cstatusbar(scr, ['[status: processing ...]'], 1, 32)
    cdata_update(me['cdataUpdate'], rowStart, dataColStart, rowEnd, colEnd)
    me['cdataUpdate'] = False
    if me['state'] != 'E':
        cstatusbar(scr, ['                        '], 1, 32)
    rtype = CATTR_DATATEXT
    for r in range(rowStart, rowEnd+1):
        sRemaining = ""
        for c in range(dataColStart, colEnd+1):
            if ((r == me['curRow']) and (c == me['curCol'])):
                ctype = curses.A_REVERSE
            else:
                ctype = curses.A_NORMAL
            data = value_key((r,c))
            #print("cdrawdata: {},{}={}".format(r,c,data), file=GLOGFILE)
            if (data != ""):
                if type(data) != str:
                    ctype |= CATTR_DATANUM
                    sData = str(data)
                    if bNumericDisplayOverflow:
                        sRemaining = sData[me['cellWidth']:]
                    else:
                        sRemaining = ""
                    rtype = CATTR_DATANUM
                else:
                    sData = data
                    ctype |= CATTR_DATATEXT
                    sRemaining = sData[me['cellWidth']:]
                    rtype = CATTR_DATATEXT
            elif (not me['clipCell']):
                ctype |= rtype
                sData = sRemaining[0:me['cellWidth']]
                sRemaining = sRemaining[me['cellWidth']:]
                #if (sData != ""):
                #    print("cdrawdata:overflow:{}+{}".format(sData, sRemaining), file=GLOGFILE)
            else: # data == "" AND clipCell
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


def do_ccmd(scr, cmd, args):
    '''
    The Config commands handling

    cro, crw
    cfs, ctq
    '''
    global THEFIELDSEP, THEQUOTE

    if (cmd == 'creadonly') or (cmd == 'cro'):
        me['readOnly'] = True
    elif (cmd == 'creadwrite') or (cmd == 'crw'):
        me['readOnly'] = False
    elif (cmd == 'cfieldsep') or (cmd == 'cfs'):
        cstatusbar(scr, ['update fieldsep'])
        #replace_incontent(THEFIELDSEP, args[0])
        THEFIELDSEP = args[0]
    elif (cmd == 'ctextquote') or (cmd == 'ctq'):
        cstatusbar(scr, ['update textquote'])
        replace_incontent(args[0], THEALT2INBTWQUOTE)
        replace_incontent(THEQUOTE, args[0])
        THEQUOTE = args[0]
    setup_fileio()


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
        edit.insert_rc_ab(cmd, args)
        me['dirty'] = True
        me['cdataUpdate'] = True
    elif cmd.startswith('d') and not me['readOnly']:
        if args == None:
            args = "1"
        edit.delete_rc(cmd, args)
        me['dirty'] = True
        me['cdataUpdate'] = True
    elif cmd.startswith('g'):
        if args != None:
            goto_cell(stdscr, args)
    elif cmd == 'help':
        fileio.load_help(me, stdscr)
    elif (cmd == 'clear') and not me['readOnly']:
        if len(me['data']) > 0:
            me['data'] = dict()
            me['dirty'] = True
            me['cdataUpdate'] = True
    elif (cmd == 'new'):
        fileio.new_file(me, stdscr)
    elif (cmd[0] == 'c'):
        do_ccmd(stdscr, cmd, args)
    elif cmd.startswith("r") and not me['readOnly']:
        edit.do_rcmd(stdscr, cmd, args)
    elif cmd[0] == 'm':
        edit.do_mcmd(stdscr, cmd, args)
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


CALLDEPTHMAX = 1000
def trap_calclooping(cellKey):
    '''
    If callDepth crosses the set threshold, then raise a CalcLoop exception and
    Err tag all involved cells.

    This is currently set to a very high value of 1000, so that python system recursion
    limit will kick in and [_]cdata_update will do its magic of evaluating long chains
    by sliding over the long chain in parts over a configured number of calc runs.

        Inturn any cells still left hanging after [_]cdata_update is done is what gets
        ErrTagged by it.

        _cdata_update also resets callDepth counter, as it starts fresh recalculations.

    NOTE: Put differently this also has the side-effect of keeping this logic on hold in the back,
    indirectly, currently.
    '''
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
                    me['data'][key] = "{}:{}".format(ERRLOOP, sData)
        raise RuntimeError("CalcLoop:{}:{}".format(cellKey, me['callDepth']))
    me['calcCnt'][cellKey] = curCalcCnt
    me['cdataUpdate'] = True


def _nvalue_saddr_or_str(sAddrOr):
    '''
    If passed a cell address in AlphaNum notation,
        Return the corresponding cells numeric value
    Else return the passed string back again.
    '''
    bCellAddr, cellKey = _celladdr_valid(sAddrOr)
    if bCellAddr:
        val = nvalue_key(cellKey)
        #print("_nvalue_saddr_or_str:{}:{}:{}".format(sAddrOr, cellKey, val), file=GLOGFILE)
        return val
    return sAddrOr


def nvalue_expr(sData):
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
            sNew += str(_nvalue_saddr_or_str(evalParts[i]))
            me['callDepth'] -= 1
        elif evalTypes[i] == parse.EvalPartType.Group: # Bracket grouped subexpression
            sVal = nvalue_expr(evalParts[i][1:-1])
            sNew += "({})".format(sVal)
        else:
            sNew += evalParts[i]
    # Evaluate
    try:
        #print("nvalue_expr:eval:{}:{}".format(sData, sNew), file=GERRFILE)
        val = eval(sNew)
    except RecursionError as re:
        ##DBUG##print("nvalue_expr:RecursionError:{}:{}:{}".format(sData, sNew, re), file=GERRFILE)
        raise
    except:
        print("nvalue_expr:exception:{}:{}".format(sData, sNew), file=GERRFILE)
        traceback.print_exc(file=GERRFILE)
        val = None
        raise
    return val


ERRNUM = "#ErrNum#"
def nvalue_key(key, bUseCachedData=True, bText2Zero=True, bDontCacheText=True):
    '''
    Return the value associated with the given cell, preferably numeric.
    The cell is specified using its corresponding key.

    If the cell doesnt contain any data, it will return 0.
    This is unity operation for add++ but not for mult++.

    If it starts with =, (interpret as =expression)
        return nvalue_expr(data) ie its internal evaluation
        This will be None, if error while evaluating.
    If it starts with +/- or numeric,
        return eval(data), ERROR tag if exception
    Else return data

    '''
    # use cached data if available
    if bUseCachedData:
        val = me['cdata'].get(key)
        if val != None:
            return val
    # find the value
    sVal = me['data'].get(key)
    if sVal == None:
        val = 0
    elif len(sVal) == 0:
        val = 0
    elif sVal.startswith("="):
        trap_calclooping(key)
        val = nvalue_expr(sVal[1:])
    elif (sVal[0] in [ '+', '-']) or sVal[0].isnumeric():
        try:
            val = eval(sVal)
        except:
            val = '{}{}'.format(ERRNUM, sVal)
    else:
        if bDontCacheText:
            bUseCachedData = False
        if bText2Zero:
            val = 0
        else:
            val = sVal
    # update cache
    if bUseCachedData:
        me['cdata'][key] = val
    return val


def value_key(key):
    '''
    Return the value associated with the given cell.
    The cell is specified using its corresponding key.

    Mainly for use by display logic.

    If no data in the cell, return empty string.
    Else return nvalue of cell
    '''
    sVal = me['data'].get(key)
    if sVal == None:
        return ""
    if len(sVal) == 0:
        return ""
    return nvalue_key(key, bText2Zero=False)


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
        #print("runLogic:{}".format(me), file=GLOGFILE)
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
    funcs.nvalue_key = nvalue_key
    funcs.nvalue_expr = nvalue_expr
    funcs.GLOGFILE = GLOGFILE
    funcs.GERRFILE = GERRFILE


def setup_fileio():
    fileio.GLOGFILE = GLOGFILE
    fileio.GERRFILE = GERRFILE
    fileio.THEQUOTE = THEQUOTE
    fileio.THEFIELDSEP = THEFIELDSEP
    fileio.dlg = dlg
    fileio.status = status
    fileio.cstatusbar = cstatusbar
    fileio.goto_cell = goto_cell


def setup_edit():
    edit.GLOGFILE = GLOGFILE
    edit.GERRFILE = GERRFILE
    edit.me = me
    edit.dlg = dlg
    edit._celladdr_valid = _celladdr_valid
    edit._celladdr_valid_ex = _celladdr_valid_ex
    edit.cell_key2addr = cell_key2addr
    edit.coladdr_num2alpha = coladdr_num2alpha


def setup_helpermodules():
    setup_funcs()
    setup_fileio()
    setup_edit()


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


CmdArgs = enum.Enum("CmdArgs", "help fieldsep quote startnohelp creadonly calldepth")
def print_usage():
    print("{}:spreadsheetkvc: usage".format(sys.argv[0]))
    print("    --{}          Prints this commandline usage info".format(CmdArgs.help.name))
    print('    --{} "{}"  Specify the csv field seperator to use'.format(CmdArgs.fieldsep.name, THEFIELDSEP))
    print('    --{} "{}"     Specify the csv field text quote to use'.format(CmdArgs.quote.name, THEQUOTE))
    print("    --{}   Dont show the help dialog at the start".format(CmdArgs.startnohelp.name))
    print("    --{}     run in readonly|view mode".format(CmdArgs.creadonly.name))
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
        elif cmd == CmdArgs.creadonly.name:
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
setup_helpermodules()
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
