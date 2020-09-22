#
# Functions related to getting value in a cell
# HanishKVC, 2020
#


import traceback
import parsekvc as parse
import funcs


me = None


GBFLYPYTHON = False
GBTEXT2ZERO = True


CALLDEPTHMAX = 10000
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
    bCellAddr, cellKey = parse.celladdr_valid(sAddrOr)
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
        if GBFLYPYTHON:
            val = eval(sNew)
        else:
            val = eval(sNew, {}, {})
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
def nvalue_key(key, bUseCachedData=True, bText2Zero=None, bDontCacheText=True):
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
    Else (return data if bText2Zero is False; otherwise return 0)

    Dont cache None or empty cells. Also by default dont cache text cells.
    '''
    if bText2Zero == None:
        bText2Zero = GBTEXT2ZERO
    # use cached data if available
    if bUseCachedData:
        val = me['cdata'].get(key)
        if val != None:
            return val
    # find the value
    sVal = me['data'].get(key)
    if sVal == None:
        bUseCachedData = False
        val = 0
    elif len(sVal) == 0:
        bUseCachedData = False
        val = 0
    elif sVal.startswith("="):
        trap_calclooping(key)
        val = nvalue_expr(sVal[1:])
    elif (sVal[0] in [ '+', '-']) or sVal[0].isnumeric():
        try:
            if GBFLYPYTHON:
                val = eval(sVal)
            else:
                val = eval(sVal, {}, {})
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


def value_key(key, raw=False):
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
    if not raw:
        return nvalue_key(key, bText2Zero=False)
    return sVal


