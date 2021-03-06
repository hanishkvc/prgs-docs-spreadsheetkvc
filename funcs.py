#!/usr/bin/env python3
# Internal functions and channel to builtin python funcs logic
# HanishKVC, 2020
#

import sys
import traceback
import math
from math import *
import parsekvc as parse
import cellval


BFILTERPYFUNC = True
me = None
GLOGFILE = None
GERRFILE = None
_do_cformat = None


def _cellrange_to_list(lRange, bIgnoreEmpty=True):
    bCellAddr, (sR,sC) = parse.celladdr_valid(lRange[0])
    if not bCellAddr:
        return False, []
    bCellAddr, (eR,eC) = parse.celladdr_valid(lRange[2])
    if not bCellAddr:
        return False, []
    lOut = []
    for r in range(sR, eR+1):
        for c in range(sC, eC+1):
            if ((me['data'].get((r,c)) == None) and bIgnoreEmpty):
                continue
            lOut.append(cellval.nvalue_key((r,c)))
    return True, lOut


def cellrange_to_list(sIn):
    '''
    Expand a cell range into a list of its values.
    The cell range could be either given directly or within brackets.
        Only one set of brackets allowed i.e [cellRange] is ok, but [[cellRange]] will be ignored.
    '''
    tokens, types = parse.get_evalparts(sIn)
    if (len(tokens) == 1):
        if types[0] == parse.EvalPartType.Group:
            grpStart = tokens[0][0]
            grpEnd = tokens[0][-1]
            maybeCellRange = tokens[0][1:-1]
            if maybeCellRange != "":
                tokens, types = parse.get_evalparts(maybeCellRange)
    if len(tokens) == 3:
        if (types[0] == parse.EvalPartType.AlphaNum) and ((types[1] == parse.EvalPartType.Any) and (tokens[1] == ':')) and (types[2] == parse.EvalPartType.AlphaNum):
            bList, theList = _cellrange_to_list(tokens)
            if bList:
                return True, theList
    return False, sIn


def _do_minmax(args, bIgnoreEmpty=True):
    '''
    Find the min and max from the matrix of cells.
    '''
    start,end = args.split(':')
    bCellAddr, (sR,sC) = parse.celladdr_valid(start)
    if not bCellAddr:
        return None, None, None
    bCellAddr, (eR,eC) = parse.celladdr_valid(end)
    if not bCellAddr:
        return None, None, None
    lItems = []
    for r in range(sR, eR+1):
        for c in range(sC, eC+1):
            if ((me['data'].get((r,c)) == None) and bIgnoreEmpty):
                continue
            lItems.append(cellval.nvalue_key((r,c)))
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
    bIgnoreEmpty can be used to control whether empty cells are considered or not.
    '''
    start,end = args.split(':')
    bCellAddr, (sR,sC) = parse.celladdr_valid(start)
    if not bCellAddr:
        return None, None
    bCellAddr, (eR,eC) = parse.celladdr_valid(end)
    if not bCellAddr:
        return None, None
    total = 0
    cnt = 0
    for r in range(sR, eR+1):
        for c in range(sC, eC+1):
            if ((me['data'].get((r,c)) == None) and bIgnoreEmpty):
                continue
            total += cellval.nvalue_key((r,c))
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
    bCellAddr, (sR,sC) = parse.celladdr_valid(start)
    if not bCellAddr:
        return None, None
    bCellAddr, (eR,eC) = parse.celladdr_valid(end)
    if not bCellAddr:
        return None, None
    avg = do_avg(args)
    total = 0
    cnt = 0
    for r in range(sR, eR+1):
        for c in range(sC, eC+1):
            if ((me['data'].get((r,c)) == None) and bIgnoreEmpty):
                continue
            total += (cellval.nvalue_key((r,c)) - avg)**2
            cnt += 1
    varp = total/cnt
    stdevp = sqrt(varp)
    try:
        var = total/(cnt-1)
        stdev = sqrt(var)
    except:
        var = None
        stdev = None
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
    bCellAddr, (sR,sC) = parse.celladdr_valid(start)
    if not bCellAddr:
        return None, None
    bCellAddr, (eR,eC) = parse.celladdr_valid(end)
    if not bCellAddr:
        return None, None
    prod = 1
    cnt = 0
    for r in range(sR, eR+1):
        for c in range(sC, eC+1):
            if ((me['data'].get((r,c)) == None) and bIgnoreEmpty):
                continue
            prod *= cellval.nvalue_key((r,c))
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


def do_mode(args):
    pass


def do_median(args):
    pass


def do_config(args):
    '''
    Config spreadsheet from within

    format, iffloat, precision
    '''
    argsList = parse.get_funcargs(args)
    if argsList[0] == "cformat":
        return _do_cformat(argsList[0], argsList[1:])


pyFuncs = [ 'min', 'round', 'pow', 'int', 'float', 'ord', 'chr', 'sin', 'cos', 'tan' ]
def allowed_pyfunc(sCmd, sArgs):
    '''
    Check if the specified python function should be allowed or not.

    If BFILTERPYFUNC is not true, then allow any python function to be called/evaluated.
    '''
    if not BFILTERPYFUNC:
        return True
    if sCmd in dir(math):
        return True
    if sCmd in pyFuncs:
        return True
    return False


ERRPFN = "#ErrPFn#"
def do_pyfunc(sCmd, sArgs):
    '''
    Try evaluating the command and the arguments as a python function

    In the process expand any cellAddress, to the numeric value corresponding
    to the specified cell.

    It also allows any argument which is a function call to be handled properly.

    NOTE: If a cellAddressRange is specified, it wont be handled properly.
    However maybe in future, I may expand a cell address range into a list
    or so, time permitting.
    '''
    if not allowed_pyfunc(sCmd, sArgs):
        return ERRPFN
    #print("do_pyfunc:{}:{}".format(sCmd, sArgs), file=GERRFILE)
    argsList = parse.get_funcargs(sArgs)
    theArgs = ""
    for curArg in argsList:
        # Handle a pure CellRange Group
        bList, theList = cellrange_to_list(curArg)
        if bList:
            sValOrArg = theList
        else:
            # Evaluate the argument
            sValOrArg = cellval.nvalue_expr(curArg)
        theArgs += ",{}".format(sValOrArg)
    if theArgs.startswith(','):
        theArgs = theArgs[1:]
    sPyFunc = "{}({})".format(sCmd, theArgs)
    #print("do_pyfunc:{}".format(sPyFunc), file=GERRFILE)
    return eval(sPyFunc)


def do_func(sCmdIn, sArgs):
    '''
    Demux the internally supported functions.
    Next try and solve it has a python function.
    Unknown and invalid/exception rising function will return None.
    '''
    sCmd = sCmdIn.upper()
    try:
        print("do_func:{}:{}".format(sCmdIn, sArgs), file=GLOGFILE)
        if sCmd == "SUM":
            return do_sum(sArgs)
        elif (sCmd == "AVG") or (sCmd == "AVERAGE"):
            return do_avg(sArgs)
        elif (sCmd == "CNT") or (sCmd == "COUNT"):
            return do_cnt(sArgs)
        #elif sCmd == "MIN":
        #    return do_min(sArgs)
        elif sCmd == "MAX":
            return do_max(sArgs)
        elif sCmd == "PROD":
            return do_prod(sArgs)
        elif (sCmd.startswith("STDDEV") or sCmd.startswith("STDEV")):
            return do_stddev(sCmd, sArgs)
        elif sCmd.startswith("VAR"):
            return do_stddev(sCmd, sArgs)
        elif sCmd == "CONFIG":
            return do_config(sArgs)
        else:
            return do_pyfunc(sCmdIn, sArgs)
    except RecursionError:
        ##DBUG##print("do_func:recursionErr:{}:{}".format(sCmdIn, sArgs), file=GERRFILE)
        raise
    except:
        print("do_func:exception:{}:{}:{}".format(sys.exc_info()[1], sCmdIn, sArgs), file=GERRFILE)
        #traceback.print_exc(file=GERRFILE)
    return None




# vim: set sts=4 expandtab: #
