#!/usr/bin/env python3
# edit and related helper routines
# HanishKVC, 2020
#


import traceback
import parsekvc as parse
import syncd



GLOGFILE = None
GERRFILE = None
me = None
dlg = None
_celladdr_valid = None
_celladdr_valid_ex = None
cell_key2addr = None
coladdr_num2alpha = None



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
                sErr = ERRROW
            if (r > eDR) and not rFixed:
                r += incR
        if bDelColMode:
            if (c >= sDC) and (c <= eDC):
                sErr += ERRCOL    # + not required bcas both row and col wont get deleted at same time, but for flexibility for future, just in case
            if (c > eDC) and not cFixed:
                c += incC
        sNewToken = "{}{}{}{}{}".format(sErr,sCFixed,coladdr_num2alpha(c),sRFixed,r)
        sOut = sBefore + sNewToken
        iPos = len(sOut)
        sOut += sAfter


ERRROW = "#ErrRow#"
ERRCOL = "#ErrCol#"
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
            sErr = ERRROW
            r = rOrig
        if (c <= 0):
            sErr += ERRCOL
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


def copy_cell():
    '''
    Copy the current cell
    '''
    me['copyData'] = me['data'].get((me['curRow'],me['curCol']))
    if me['copyData'] != None:
        me['copySrcCell'] = (me['curRow'], me['curCol'])


def del_cell():
    '''
    Delete current cell's content, if available.

    If there was content to del, then set dirty flag and
    clear calc cache as required.
    '''
    if me['data'].pop((me['curRow'],me['curCol']), None) != None:
        me['dirty'] = True
        syncd.cell_updated((me['curRow'], me['curCol']), "", clearedSet=set())


def cut_cell():
    '''
    Cut the current cell content.

    If there was content to cut, then set dirty flag and
    clear calc cache as required.
    '''
    copy_cell()
    del_cell()


def paste_cell(bAdjustCellAddress=True):
    '''
    Paste into current cell.

    Adjust the cell addresses if any in the =expression, during paste, if requested.

    Also set dirty flag and clear calc cache as required.
    '''
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
        syncd.cell_updated((me['curRow'], me['curCol']), theData, clearedSet=set())


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


def _do_rclear_err(scr, dstSKey, dstEKey):
    '''
    Clear error tags in the specified block of cells at dst.
    '''
    for dR in range(dstSKey[0], dstEKey[0]+1):
        for dC in range(dstSKey[1], dstEKey[1]+1):
            sData = me['data'].get((dR,dC), None)
            if sData != None:
                if sData.startswith("#Err") and (sData[7] == '#'):
                    sData = sData[8:]
                    me['data'][(dR,dC)] = sData
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
            me['data'][(r,c)] = "{}".format(curValue)
            curValue += delta
    if endKey[0] > me['numRows']:
        me['numRows'] = endKey[0]
    if endKey[1] > me['numCols']:
        me['numCols'] = endKey[1]
    return True


def do_rcmd(scr, cmd, args):
    '''
    RCommands demuxer.

    It converts cell markers, if any, to cell addresses.
    Gets the cell keys for the given cell addresses.
    '''
    bDone = False
    try:
        print("rcmd:{} {}".format(cmd, args), file=GERRFILE)
        # Handle Markers
        lTokens, lTTypes = parse.get_tokens(args,0,['@'])
        sAdjustedArgs = ""
        for i in range(len(lTTypes)):
            if (lTTypes[i] == parse.TokenType.AlphaNum) and (lTokens[i][0] == '@'):
                key = me['markers'].get(lTokens[i][2:])
                sAdjustedArgs += "{} ".format(cell_key2addr(key))
            else:
                sAdjustedArgs += "{} ".format(lTokens[i])
        # Handle cell addresses
        lCAddr, lPos = parse.get_celladdrs(sAdjustedArgs)
        lKeys = []
        for cAddr in lCAddr:
            bCellAddr, key = _celladdr_valid(cAddr)
            if not bCellAddr:
                return False
            lKeys.append(key)
            print("rcmd:btw:{} {}".format(cAddr, key), file=GERRFILE)
        # Execute the commands
        numKeys = len(lKeys)
        if numKeys == 3:
            lKeys.append((lKeys[2][0] + (lKeys[1][0] - lKeys[0][0]), lKeys[2][1] + (lKeys[1][1] - lKeys[0][1])))
        if cmd == "rcopy":
            bDone = _do_rcopy(scr, lKeys[0], lKeys[1], lKeys[2], lKeys[3])
        elif cmd == "rcopyasis":
            bDone = _do_rcopy(scr, lKeys[0], lKeys[1], lKeys[2], lKeys[3], False)
        elif cmd == "rclear":
            bDone = _do_rclear(scr, lKeys[0], lKeys[1])
        elif cmd == "rclearerr":
            bDone = _do_rclear_err(scr, lKeys[0], lKeys[1])
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


def do_mcmd(scr, cmd, args):
    '''
    Handle marker commands

    mclear to clear current markers
    mshow to show current markers
    mMarkerId assign current cell (i.e row/col) to specified marker id.
    '''
    if cmd[0] != 'm':
        dlg(scr, ['DBUG {} {}'.format(cmd, args)])
        return False
    if cmd == 'mclear':
        me['markers'] = dict()
        return True
    if cmd == 'mshow':
        lMarkers = ['********         Markers         ********']
        if len(me['markers']) <= 0:
            lMarkers.append("  {:36}  ".format("None"))
        for m in me['markers']:
            k = me['markers'][m]
            lMarkers.append("  m{:17} : {:16}  ".format(m, cell_key2addr(k)))
        lMarkers.append("{:40}".format("Press any key..."))
        dlg(scr, lMarkers)
        return True
    markerId = cmd[1:]
    me['markers'][markerId] = (me['curRow'], me['curCol'])
    return True





# vim: set sts=4 expandtab: #
