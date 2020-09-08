#!/usr/bin/env python3
# edit and related helper routines
# HanishKVC, 2020
#


me = None
dlg = None
_celladdr_valid = None
cell_key2addr = None



def copy_cell():
    '''
    Copy the current cell
    '''
    me['copyData'] = me['data'].get((me['curRow'],me['curCol']))
    if me['copyData'] != None:
        me['copySrcCell'] = (me['curRow'], me['curCol'])


def paste_cell(bAdjustCellAddress=True):
    '''
    Paste into current cell.

    Adjust the cell addresses if any in the =expression, during paste, if requested.

    Also set dirty and cdataupate flags.
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
        me['cdataUpdate'] = True


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
