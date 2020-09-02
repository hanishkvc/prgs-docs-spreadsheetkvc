#!/usr/bin/env python3
# A generic parse helping routines
# HanishKVC, 2020
#

import enum



class AlphaNumType(enum.IntFlag):
    UNKNOWN = 0
    NUMERIC = 1
    ALPHA   = 2
    SYMBOL  = 4
    OTHER   = 8


def alphanum_type(sIn, symbolList=None):
    '''
    Identify the type of alphanumeric token.

    SymbolList gives a list of characters which will be treated as symbols.

    It could be None (NOMORE)
    OR IT COULD consist of Alpha, Numeric, Symbol and or Other
    thus leading to different combinations of these like
    Alpha, Numeric, AlphaNum, AlphaNumPlus, Other, ...
    '''
    anType = AlphaNumType.UNKNOWN
    typeSeq = []
    i = 0
    while i < len(sIn):
        if sIn[i].isalpha():
            anType |= AlphaNumType.ALPHA
            typeSeq.append(AlphaNumType.ALPHA)
        elif sIn[i].isnumeric():
            anType |= AlphaNumType.NUMERIC
            typeSeq.append(AlphaNumType.NUMERIC)
        elif ((symbolList != None) and (sIn[i] in symbolList)):
            anType |= AlphaNumType.SYMBOL
            typeSeq.append(AlphaNumType.SYMBOL)
        else:
            anType |= AlphaNumType.OTHER
            typeSeq.append(AlphaNumType.OTHER)
        i += 1
    return anType, typeSeq


def collapse_sametype(typeSeqIn):
    '''
    Given a list of items, if adjacent items are the same,
    then collapse/reduce such group of items into a single item.
    '''
    prevType = None
    typeSeqOut = []
    for t in typeSeqIn:
        if (t != prevType):
            typeSeqOut.append(t)
        prevType = t
    return typeSeqOut


TokenType = enum.Enum("TokenType", "NoMore AlphaNum Symbol Sign BracketStart BracketEnd Unknown")
def get_token(sIn, startPos=0, bANTokenHasDecimal=True):
    '''
    Get first valid token from the given string and its position.

    By using the startPos argument, one can get the tokens in a
    given string one after the other by passing the last got
    position from this function back to it in the next call as
    its startPos argument.

    It drops white spaces and extracts other chars as logically
    related tokens of a predefined set of types.

    This could include brackets, symbols, signs, alphanumeric
    words/numbers (including decimal numbers).

        alphanumeric words could represent function names or
        celladdresses or so.

    If it finds a string quoted using single quotes, then it
    will be extracted as a single string token.
    '''
    if sIn == "":
        return TokenType.NoMore, "", -1
    if startPos >= len(sIn):
        return TokenType.NoMore, "", -1
    i = startPos
    sOut = ""
    iPosStart = i
    bInQuote = False
    bInToken = False
    while i < len(sIn):
        if sIn[i].isspace():
            if bInQuote:
                sOut += sIn[i]
                i += 1
                continue
            if bInToken:
                return TokenType.AlphaNum, sOut, iPosStart
            i += 1
            continue
        if sIn[i].isalnum() or (bANTokenHasDecimal and (sIn[i] == '.')):
            if not bInToken:
                bInToken = True
                iPosStart = i
            sOut += sIn[i]
            i += 1
            continue
        if sIn[i] == "'":
            if bInToken:
                if bInQuote:
                    bInQuote = False
                    sOut += sIn[i]
                    return TokenType.AlphaNum, sOut, iPosStart
                return TokenType.AlphaNum, sOut, iPosStart
            bInToken = True
            bInQuote = True
            sOut += sIn[i]
            iPosStart = i
            i += 1
            continue
        if sIn[i] in [ ',', ';', ':' ]:
            if bInToken:
                return TokenType.AlphaNum, sOut, iPosStart
            return TokenType.Symbol, sIn[i], i
        if sIn[i] in [ '+', '-' ]:
            if bInToken:
                return TokenType.AlphaNum, sOut, iPosStart
            return TokenType.Sign, sIn[i], i
        if sIn[i] in [ '(', '[', '{' ]:
            if bInToken:
                return TokenType.AlphaNum, sOut, iPosStart
            return TokenType.BracketStart, sIn[i], i
        if sIn[i] in [ ')', ']', '}' ]:
            if bInToken:
                return TokenType.AlphaNum, sOut, iPosStart
            return TokenType.BracketEnd, sIn[i], i
        break
    if bInToken:
        return TokenType.AlphaNum, sOut, iPosStart
    if i >= len(sIn):
        return TokenType.NoMore, "", -1
    return TokenType.Unknown, sIn[i], i


def get_funcargs(sIn):
    '''
    Extract function arguments of a function passed as a single
    string, as individual arguments.

    IF there are complex data structures like set or list or dict
    as a function argument, it will be identified as a single func
    argument rather than spliting its individual elements up into
    multiple args.

    It doesnt distinguish between the different types of brackets,
    however it does handle embedded brackets.

        [ 1, 2, 3 ] and [ 1, 2, 3 } are same to it, and treated
        as a single function argument.

        [ 1, 2, [a, {what, else} ], 99] will be treated as a single
        function argument.

    The sIn shouldnt contain the ( and ) at the begin and end of the
    sIn, else it will be returned as a single argument.
    '''
    iPos = 0
    sArgs = []
    curArg = ""
    iBracket = 0
    while True:
        tokenType, sOut, iPos = get_token(sIn, iPos)
        if tokenType == TokenType.NoMore:
            break
        iPos += len(sOut)
        if tokenType == TokenType.Symbol:
            if (iBracket == 0) and (sOut == ","):
                sArgs.append(curArg)
                curArg = ""
                continue
        if tokenType == TokenType.BracketStart:
            iBracket += 1
        if tokenType == TokenType.BracketEnd:
            iBracket -= 1
        curArg += sOut
    if (curArg != ""):
        sArgs.append(curArg)
    return sArgs


def get_tokens(sIn):
    '''
    Return a list of tokens in the given string.

    It also returns a list of token types which corresponds to
    type of each token in the tokenList.
    '''
    iPos = 0
    tokenList = []
    typeList = []
    while True:
        tokenType, sOut, iPos = get_token(sIn, iPos)
        if tokenType == TokenType.NoMore:
            break
        tokenList.append(sOut)
        typeList.append(tokenType)
        iPos += len(sOut)
    return tokenList, typeList


EvalPartType = enum.Enum("EvalPartType", "Any Group Func AlphaNum")
def get_evalparts(sIn):
    '''
    Extract parts that can be evaluated on their own and operations
    sorrounding them.

    The main parts include numbers, functions and cell addresses.

    The function element consists of the function name as well as
    the arguments to the function.

    The argument of a function could inturn be another function.

    An element could even be a complex data structure like a list
    or a set or a dict.

    It doesnt distinguish between the different types of brackets,
    however it does handle embedded brackets.

    The sIn shouldnt contain the ( and ) at the begin and end of the
    sIn, else it will be returned as a single argument.
    '''
    tokenList, typeList = get_tokens(sIn)
    lParts = []
    lTypes = []
    iBracket = 0
    i = 0
    while i < len(typeList):
        if typeList[i] == TokenType.BracketStart:
            if iBracket == 0:
                iStartBracket = i
            iBracket += 1
            i += 1
            continue
        if typeList[i] == TokenType.BracketEnd:
            iBracket -= 1
            if iBracket == 0:
                try:
                    bFunc = (typeList[iStartBracket-1] == TokenType.AlphaNum)
                except:
                    bFunc = False
                curPart = ""
                for j in range(iStartBracket, i+1):
                    curPart += tokenList[j]
                if bFunc:
                    try:
                        sFuncName = lParts[-1]
                        lParts[-1] = "{}{}".format(sFuncName, curPart)
                        lTypes[-1] = EvalPartType.Func
                    except: # This shouldnt trigger normally, but just in case
                        lParts.append(curPart)
                        lTypes.append(EvalPartType.Group)
                else:
                    lParts.append(curPart)
                    lTypes.append(EvalPartType.Group)
            i += 1
            continue
        if iBracket == 0:
            lParts.append(tokenList[i])
            if typeList[i] == TokenType.AlphaNum:
                lTypes.append(EvalPartType.AlphaNum)
            else:
                lTypes.append(EvalPartType.Any)
        i += 1
        continue
    return lParts, lTypes


def get_celladdr(sIn, startPos=0):
    '''
    Get first potentiall cell address token from the given string and its position.

    By using the startPos argument, one can get the tokens in a
    given string one after the other by passing the last got
    position from this function back to it in the next call as
    its startPos argument.

    NOTE: This is not a generic token parser. It mainly extracts
    tokens which match the CellAddr kind or FuncName kind. Numbers
    on their own will not be extracted, nor will operators or
    Plus/Minus or so.

    If the token contains single quotes, then it will be skipped.
    Similarly if the token is a string in single quotes, it will
    be skipped.

    Checks that AlphaNum starts with Alpha.

    TODO1: Need to allow $ to be part of alphanumeric.
    '''
    iPos = startPos
    sOut = ""
    while True:
        tokenType, sOut, iPos = get_token(sIn, iPos)
        if tokenType == TokenType.NoMore:
            break
        elif tokenType == TokenType.AlphaNum:
            if not ("'" in sOut):
                anType, typeSeq = alphanum_type(sOut)
                typeSeq = collapse_sametype(typeSeq)
                if (len(typeSeq) == 2) and (typeSeq[0] == AlphaNumType.ALPHA):
                    if (AlphaNumType.NUMERIC in anType) and (AlphaNumType.ALPHA in anType):
                        return True, sOut, iPos
        iPos += len(sOut)
    return False, sOut, iPos


def get_celladdrs(sIn, startPos = 0):
    '''
    Return a list of celladdrs in the given string.

    It also returns a list of positions which corresponds to
    type of each cell address in the cellAddrList.
    '''
    iPos = startPos
    cellAddrList = []
    posList = []
    while True:
        bToken, sOut, iPos = get_celladdr(sIn, iPos)
        if not bToken:
            break
        cellAddrList.append(sOut)
        posList.append(iPos)
        iPos += len(sOut)
    return cellAddrList, posList




def test_101():
    sFuncArgs = "123, BA12:BB20, { 1, 2, 3], 23;45, [1,2,{a,b,c}}"
    sFuncArgs = "123, BA12:BB20, { 1, 2, 3], 23;45, [1,2,{a,b,c}}, 'test what'  "
    print(get_funcargs(sFuncArgs))
    print(get_tokens("test 1, BA22:3 +123 test123 test(1,2 ,3, 4,5) 1-2 * / \ 'test what else' 123 1 2.234 3 "))
    print(get_evalparts("(=10 + 2.83 *sum(20:30, int(2)) -(AB20+2.9 / ([1,2,3])) + [a,b,c])"))
    print(get_evalparts("=10 + 2.83 *sum(20:30, int(2)) -(AB20+2.9 / ([1,2,3])) + [a,b,c]"))
    print(get_celladdrs("what else CA22:CB33 'Not AA22' +25-C33/(A20-30)*DD55 - 99AA + AA99"))




# vim: set sts=4 expandtab: #
