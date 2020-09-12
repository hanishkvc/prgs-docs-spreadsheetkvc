#!/usr/bin/env python3
# A generic parse helping routines
# HanishKVC, 2020
#

import enum, re



class AlphaNumType(enum.IntFlag):
    NOTHING = 0
    NUMERIC = 1
    ALPHA   = 2
    SYMSET1 = 4
    SYMSET2 = 8
    OTHER   = 16

AlphaNumTypeId = { AlphaNumType.NUMERIC: 'N', AlphaNumType.ALPHA: 'A',
                    AlphaNumType.SYMSET1: '1', AlphaNumType.SYMSET2: '2',
                    AlphaNumType.OTHER: 'O' }

def alphanum_type(sIn, symbolSet1=None, symbolSet2=None):
    '''
    Identify the type of alphanumeric token.

    SymbolSets are independent list of characters. If characters in the
    provided string belong to these sets, then they will be identified
    as belonging to same in the anType and typeSeq list. Currently user
    can identify upto two independent set of chars/symbols, if any in
    the given string.

    It could be Nothing
    OR IT COULD consist of Alpha, Numeric, Symbol and or Other
    thus leading to different combinations of these like
    Alpha, Numeric, AlphaNum, AlphaPlus, NumPlus, AlphaNumPlus, Other, ...

    Characters which don't fit into alphabets, numeric, symbolsets get
    marked as OTHER.
    '''
    anType = AlphaNumType.NOTHING
    typeSeq = []
    i = 0
    while i < len(sIn):
        if sIn[i].isalpha():
            anType |= AlphaNumType.ALPHA
            typeSeq.append(AlphaNumType.ALPHA)
        elif sIn[i].isnumeric():
            anType |= AlphaNumType.NUMERIC
            typeSeq.append(AlphaNumType.NUMERIC)
        elif ((symbolSet1 != None) and (sIn[i] in symbolSet1)):
            anType |= AlphaNumType.SYMSET1
            typeSeq.append(AlphaNumType.SYMSET1)
        elif ((symbolSet2 != None) and (sIn[i] in symbolSet2)):
            anType |= AlphaNumType.SYMSET2
            typeSeq.append(AlphaNumType.SYMSET2)
        else:
            anType |= AlphaNumType.OTHER
            typeSeq.append(AlphaNumType.OTHER)
        i += 1
    return anType, typeSeq


def collapse_sametype(typeSeqIn, typeIdDict=None):
    '''
    Given a list of items, if adjacent items are the same,
    then collapse/reduce such group of items into a single item.

    If a dictionary which maps item to a string or rather char id
    is provided, then it also returns a typeIdString. This can help
    with easy pattern matching.
    '''
    prevType = None
    typeSeqOut = []
    typeIds = ""
    for t in typeSeqIn:
        if (t != prevType):
            typeSeqOut.append(t)
            if typeIdDict != None:
                typeIds += typeIdDict[t]
        prevType = t
    return typeSeqOut, typeIds


TokenType = enum.Enum("TokenType", "NoMore AlphaNum Symbol Sign BracketStart BracketEnd Unknown")
def get_token(sIn, startPos=0, ANAddOnDefault=['.','$'], ANAddOn=None):
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

    If a list of chars is passed in ANAddon, then any character
    in that list will be treated as part of AlphaNum token.
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
        if sIn[i].isalnum() or ((ANAddOnDefault != None) and (sIn[i] in ANAddOnDefault)) or ((ANAddOn != None) and (sIn[i] in ANAddOn)):
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


def get_tokens(sIn, startPos=0, ANAddOn=None):
    '''
    Return a list of tokens in the given string.

    It also returns a list of token types which corresponds to
    type of each token in the tokenList.

    startPos specifies the position in the input string from which to
    start parsing. Defaults to 0.

    If one wants the AlphaNumeric tokens to contain some additional symbols
    one can pass those in ANAddOn list. Defaults to empty list.
    '''
    iPos = startPos
    tokenList = []
    typeList = []
    while True:
        tokenType, sOut, iPos = get_token(sIn, iPos, ANAddOn=ANAddOn)
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
    tokens which match the CellAddr kind (or FuncName kind which
    follow cell address pattern). Numbers on their own will not be
    extracted, nor will operators or Plus/Minus or so.

    If the token contains single quotes, then it will be skipped.
    Similarly if the token is a string in single quotes, it will
    be skipped.

    Checks that AlphaNum tokens match valid cell address patterns,
    including $ in them.

    Handle $ being part of CellAddr in a simple yet powerful way.
    '''
    iPos = startPos
    sOut = ""
    while True:
        tokenType, sOut, iPos = get_token(sIn, iPos, ANAddOn=['$'])
        if tokenType == TokenType.NoMore:
            break
        elif tokenType == TokenType.AlphaNum:
            if not ("'" in sOut):
                anType, typeSeq = alphanum_type(sOut, symbolSet1=['$'])
                typeSeq, typeIds = collapse_sametype(typeSeq, AlphaNumTypeId)
                if typeIds in [ 'AN', '1AN', 'A1N', '1A1N']:
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


RangeState = enum.Enum("RangeState", "NoThing CanEnter Entered Done")
def get_celladdrs_incranges_old(sIn, startPos=0):
    '''
    Get list of cell address tokens and or cell address ranges.

    By using the startPos argument, one can start from anywhere
    in the string.

    NOTE: This is not a generic token parser. It mainly extracts
    tokens which match the CellAddr kind (and also potentially
    FuncName kind). Numbers on their own will not be extracted,
    nor will operators or Plus/Minus or so.

    If the token contains single quotes, then it will be skipped.
    Similarly if the token is a string in single quotes, it will
    be skipped.

    Checks that AlphaNum tokens match valid cell address patterns,
    including $ in them.

    Handle $ being part of CellAddr in a simple yet powerful way.
    '''
    lCellAddrs = []
    rangeState = RangeState.NoThing
    tokenList, typeList = get_tokens(sIn, startPos)
    for i in range(len(typeList)):
        if typeList[i] == TokenType.AlphaNum:
            if ("'" in tokenList[i]):
                rangeState = RangeState.NoThing
                continue
            if ((i+2) <= (len(tokenList)-1)):
                if (tokenList[i+1][0] == ':') and  (typeList[i+2] == TokenType.AlphaNum):
                    if rangeState == RangeState.NoThing:
                        rangeState = RangeState.CanEnter
                    else:
                        rangeState = RangeState.NoThing
                        print("getCellAddrsIncRanges:WARN:{}:{}".format(sIn, (tokenList[i], typeList[i])))
            anType, typeSeq = alphanum_type(tokenList[i], symbolSet1=['$'])
            typeSeq, typeIds = collapse_sametype(typeSeq, AlphaNumTypeId)
            if typeIds in [ 'AN', '1AN', 'A1N', '1A1N']:
                if rangeState == RangeState.CanEnter:
                    rangeState = RangeState.Entered
                elif rangeState == RangeState.Entered:
                    rangeState = RangeState.Done
                if rangeState == RangeState.NoThing:
                    lCellAddrs.append([tokenList[i]])
                elif rangeState == RangeState.Done:
                    lCellAddrs.append([tokenList[i-2], tokenList[i]])
                    rangeState = RangeState.NoThing
        else:
            continue
    return lCellAddrs


def get_celladdrs_incranges(sIn):
    rawList = re.findall("(.*?)([$]?[a-zA-Z]+[$]?[0-9]+[ ]*[:]?)(.*?)", sIn)
    caList = []
    bInCARange = False
    for raw in rawList:
        ca = raw[1]
        ca = ca.replace(' ', '')
        if ca[-1] == ':':
            pCA = ca[:-1]
        else:
            pCA = ca
        if bInCARange:
            caList[-1].append(pCA)
            bInCARange = False
        else:
            caList.append([pCA])
        if ca[-1] == ':':
            bInCARange = True
    return caList




def test_101():
    sFuncArgs = "123, BA12:BB20, { 1, 2, 3], 23;45, [1,2,{a,b,c}}"
    sFuncArgs = "123, BA12:BB20, { 1, 2, 3], 23;45, [1,2,{a,b,c}}, 'test what'  "
    print(get_funcargs(sFuncArgs))
    print(get_tokens("test 1, BA22:3 +123 test123 test(1,2 ,3, 4,5) 1-2 * / \ 'test what else' 123 1 2.234 3 "))
    print(get_evalparts("(=10 + 2.83 *sum(20:30, int(2)) -(AB20+2.9 / ([1,2,3])) + [a,b,c])"))
    print(get_evalparts("=10 + 2.83 *sum(20:30, int(2)) -(AB20+2.9 / ([1,2,3])) + [a,b,c]"))
    print(get_celladdrs("what else CA22:CB33 'Not AA22' +25-C33/(A20-30)*DD55 - 99AA + AA99"))
    print(get_celladdrs("what else CA$22:CB33 'Not $AA22' +25-$C33/(A20-30)*$DD$55 - 99AA + AA99"))
    print(get_tokens("rgennums A1:B10 10 -5 +60 8.5 det", 12, ['-','+']))
    print(get_celladdrs_incranges_old("=whatelse+A11:$B12+32/(A32)   + ZZ9999 - MN102 % CB102:DD321 + sum(B1 : B2) - sin(B99, int(JK10: KJ99))"))
    print(get_celladdrs_incranges("=whatelse+A11:$B12+32/(A32)   + ZZ9999 - MN102 % CB102:DD321 + sum(B1 : B2) - sin(B99, int(JK10: KJ99))"))
    print(re.findall(".*?([$]?[a-zA-Z]+[$]?[0-9]+).*?", "123+beA23-12+testit/$zze$54"))
    print(re.findall("(.*?)([$]?[a-zA-Z]+[$]?[0-9]+[ ]*[:]?)(.*?)", "123+beA23-12+testit/$zze$54 d  BE99     : CE10 :: MM1:NN99"))





# vim: set sts=4 expandtab: #
