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


bDebug = False
THEQUOTE = "'"
THEFIELDSEP = ';'
DONTEXIT = -9999
# Whether to use internal or cryptography libraries AuthenticatedEncryption
# Both use similar concepts, but bitstreams are not directly interchangable
bInternalEncDec = True
gbStartHelp = True
CATTR_TEXT = (curses.A_ITALIC)
CATTR_TEXT = (curses.A_ITALIC | curses.A_DIM)


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
        'data': dict(),
        'clipCell': False,
        'copyData': None,
        'gotStr': "",
        'dirty': False,
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


def _cdraw_data(rowStart, rowEnd, colStart, colEnd):
    '''
    Display the cells which are currently visible on the screen.
    '''
    for r in range(rowStart, rowEnd+1):
        sRemaining = ""
        for c in range(colStart, colEnd+1):
            if ((r == me['curRow']) and (c == me['curCol'])):
                ctype = curses.A_REVERSE
            else:
                ctype = curses.A_NORMAL
            ctype |= CATTR_TEXT
            sData = me['data'].get((r,c))
            print("cdrawdata: {},{}={}".format(r,c,sData), file=GLOGFILE)
            if (sData == None) and bDebug:
                sData = "{},{}".format(r,c)
            if (sData != None):
                if sData.startswith("="):
                    sData = value((r,c))
                    ctype &= (~CATTR_TEXT & 0xFFFF_FFFF)
                else:
                    sRemaining = sData[me['cellWidth']:]
            elif (not me['clipCell']):
                sData = sRemaining[0:me['cellWidth']]
                sRemaining = sRemaining[me['cellWidth']:]
                if (sData != ""):
                    print("cdrawdata:overflow:{}+{}".format(sData, sRemaining), file=GLOGFILE)
            else: # sData == None AND clipCell
                sData = ""
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


TType = enum.Enum("TType", ["CellAddr", "Func"])
def get_token(sIn, startPos=0, ttype=TType.CellAddr):
    '''
    Get first valid token from the given string and its position.

    By using the startPos argument, one can get the tokens in a
    given string one after the other by passing the last got
    position from this function back to it in the next call as
    its startPos argument.

    One could either fetch a CellAddr or FuncName token.

    NOTE: This is not a generic token parser. It mainly extracts
    tokens which match the CellAddr kind or Func kind. Numbers
    on their own will not be extracted, nor will operators or
    Plus/Minus or so.

    TODO: In future, if I support functions which take string
    arguments, then I will have to look for strings and skip
    their contents.
    '''
    i = startPos
    sOut = ""
    iPos = i
    bInToken = False
    while i < len(sIn):
        if not bInToken:
            if sIn[i].isalpha():
                iPos = i
                bInToken = True
            elif (ttype == TType.CellAddr) and (sIn[i] == "$"):
                iPos = i
                bInToken = True
        if bInToken:
            if sIn[i].isalnum():
                sOut += sIn[i]
            elif (ttype == TType.CellAddr) and (sIn[i] == "$"):
                sOut += sIn[i]
            else:
                if (sOut != ""):
                    break
        i += 1
    if sOut == "$": # If nothing but $ only, then not valid
        bInToken = False
    return bInToken, sOut, iPos


def update_celladdrs(sIn, afterR, incR, afterC, incC):
    '''
    Update any cell addresses found in given string,
    by adjusting the address by given incR or incC amount, provided
    the address is beyond afterR or afterC.
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
        bToken, sToken, iPos = get_token(sOut, iPos, TType.CellAddr)
        if not bToken:
            #print("updateCellAddrs:Out:{}".format(sOut), file=GERRFILE)
            return sOut
        #print("updateCellAddrs:Btw:{}".format(sToken), file=GERRFILE)
        bCellAddr, (r,c) = _celladdr_valid(sToken)
        # If not valid cell addr, skip it
        if not bCellAddr:
            iPos += len(sToken)
            continue
        # A valid cell address, so update
        sErr = ""
        sBefore = sOut[0:iPos]
        sAfter = sOut[iPos+len(sToken):]
        if (bInsRowMode and (r > afterR)):
            r += incR
        if (bInsColMode and (c > afterC)):
            c += incC
        if bDelRowMode:
            if (r >= sDR) and (r <= eDR):
                sErr = "ErrR_"
            if (r > eDR):
                r += incR
        if bDelColMode:
            if (c >= sDC) and (c <= eDC):
                sErr += "ErrC_"    # + not required but for flexibility for future, just in case
            if (c > eDC):
                c += incC
        sNewToken = "{}{}{}".format(sErr,coladdr_num2alpha(c),r)
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
                newData = update_celladdrs(curData, cR, incR, cC, incC)
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
                curData = update_celladdrs(curData, sR-1, incR, sC-1, incC)
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


def _save_file(scr, sFile, filePass=None):
    '''
    Save file in a csv format.

    If the cell data contains the field seperator in it, then
    the cell content is protected within single quotes.

    If successfully saved, then Clear the dirty bit.

    If filePass is provided then encrypt the file.
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
                    if not data.startswith('`'):
                        data = "{}{}".format(THEQUOTE, data)
                    if not data.endswith('`'):
                        data = "{}{}".format(data, THEQUOTE)
            else:
                data = ""
            curRow += "{}{}".format(data,THEFIELDSEP)
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


def load_file(scr, sFile, filePass=None):
    try:
        _load_file(sFile, filePass)
        me['dirty'] = False
    except:
        a,b,c = sys.exc_info()
        print("loadfile:exception:{}:{}".format((a,b,c), sFile), file=GLOGFILE)
        traceback.print_exc(file=GERRFILE)
        dlg(scr, ["loadfile:exception:{}:{}".format((a,b), sFile), "Press any key to continue"])


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
    clear to clear the current spreadsheet
    help to show the help dialogs.
    q to quit the program
    '''
    if cmdArgs.find(' ') == -1:
        cmd = cmdArgs
        args = None
    else:
        cmd,args = cmdArgs.split(' ',1)
    print("cmd:{}, args:{}".format(cmd,args), file=GLOGFILE)
    if cmd == 'w':
        save_file(stdscr, args)
    elif cmd == 'pw':
        filePass, args = args.split(' ',1)
        save_file(stdscr, args, filePass)
    elif cmd == 'l':
        load_file(stdscr, args)
    elif cmd == 'pl':
        filePass, args = args.split(' ',1)
        load_file(stdscr, args, filePass)
    elif cmd.startswith('i'):
        if args == None:
            args = "1"
        insert_rc_ab(cmd, args)
        me['dirty'] = True
    elif cmd.startswith('d'):
        if args == None:
            args = "1"
        delete_rc(cmd, args)
        me['dirty'] = True
    elif cmd.startswith('g'):
        if args != None:
            goto_cell(stdscr, args)
    elif cmd == 'help':
        helpdlg.help_dlg(stdscr)
    elif cmd == 'clear':
        if len(me['data']) > 0:
            me['data'] = dict()
            me['dirty'] = True
    elif cmd == 'q':
        quit(stdscr)


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
        return False, (None, None)
    iNums = 0
    numAddr = ""
    while i < len(sAddr):
        if not sAddr[i].isnumeric():
            break
        numAddr += sAddr[i]
        iNums += 1
        i += 1
    if (iNums == 0) or (iNums > 4): # This limits number of rows
        return False, (None, None)
    if i != len(sAddr):
        return False, (None, None)
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
            sVal = funcs.do_func(sCmd, sArgs)
            sNew += str(sVal)
        elif evalTypes[i] == parse.EvalPartType.AlphaNum: # Handle cell addresses
            sNew += _cellvalue_or_str(evalParts[i])
        elif evalTypes[i] == parse.EvalPartType.Group: # Bracket grouped subexpression
            sVal = _nvalue(evalParts[i][1:-1])
            sNew += "({})".format(sVal)
        else:
            sNew += evalParts[i]
    # Evaluate
    try:
        val = eval(sNew)
    except:
        print("_nvalue:exception:{}:{}".format(sData, sNew), file=GERRFILE)
        traceback.print_exc(file=GERRFILE)
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
        p helps Paste cell data.
        h|? show help dialog
    '''
    if (key == curses.KEY_UP):
        cellcur_up()
    elif (key == curses.KEY_DOWN):
        cellcur_down()
    elif (key == curses.KEY_LEFT):
        cellcur_left()
    elif (key == curses.KEY_RIGHT):
        cellcur_right()
    elif (key == ord('D')):
        me['data'].pop((me['curRow'],me['curCol']), None)
    elif (key == ord('c')):
        me['copyData'] = me['data'].get((me['curRow'],me['curCol']))
    elif (key == ord('C')):
        me['copyData'] = me['data'].get((me['curRow'],me['curCol']))
        if me['data'].pop((me['curRow'],me['curCol']), None) != None:
            me['dirty'] = True
    elif (key == ord('p')):
        if me['copyData'] != None:
            me['data'][(me['curRow'],me['curCol'])] = me['copyData']
            me['dirty'] = True
    elif (key == ord('i')):
        me['state'] = 'E'
        me['gotStr'] = ""
        me['crsrOffset'] = 0
        me['backupEdit'] = None
        curData = me['data'].get((me['curRow'],me['curCol']))
        if curData != None:
            me['dirty'] = True
            me['data'][(me['curRow'],me['curCol'])] = ""
    elif (key == ord('e')):
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
            # Restore/set data to the latest backedup edit buffer
            if me['backupEdit'] != None:
                me['data'][(me['curRow'],me['curCol'])] = me['backupEdit'].strip()
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
            me['dirty'] = True
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
    print("cwinsizechange:in:{}".format(me), file=GERRFILE)
    cend(stdscr)
    stdscr=cstart()
    print("cwinsizechange:ou:{}".format(me), file=GERRFILE)


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


CmdArgs = enum.Enum("CmdArgs", "help fieldsep quote startnohelp")
def print_usage():
    print("{}:spreadsheetkvc: usage".format(sys.argv[0]))
    print("    --{}          Prints this commandline usage info".format(CmdArgs.help.name))
    print('    --{} "{}"  Specify the csv field seperator to use'.format(CmdArgs.fieldsep.name, THEFIELDSEP))
    print('    --{} "{}"     Specify the csv field text quote to use'.format(CmdArgs.quote.name, THEQUOTE))
    print("    --{}   Dont show the help dialog at the start".format(CmdArgs.startnohelp.name))
    exit(0)


def process_cmdline(args):
    '''
    Process commandline arguments for the program
    '''
    global THEFIELDSEP
    global THEQUOTE
    global gbStartHelp
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
        i += 1



### Main logic starts ###

setup_files()
process_cmdline(sys.argv)
stdscr=cstart()
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
    cend(stdscr)
    GLOGFILE.close()
exit(me['exit'])

# vim: set sts=4 expandtab: #
