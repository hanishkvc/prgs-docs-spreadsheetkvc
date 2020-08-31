#!/usr/bin/env python3
# A generic parse helping routines
# HanishKVC, 2020
#

import enum

TokenType = enum.Enum("TokenType", "NoMore AlphaNum Symbol Sign BracketStart BracketEnd Unknown")
def get_token(sIn, startPos=0, bGetTokenDecimalAlso=True):
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
        if sIn[i].isalnum() or (bGetTokenDecimalAlso and (sIn[i] == '.')):
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


def print_tokens(sIn):
    iPos = 0
    while True:
        tokenType, sOut, iPos = get_token(sIn, iPos)
        if tokenType == TokenType.NoMore:
            break
        print("Token:[{}]".format(sOut))
        iPos += len(sOut)


def test_101():
    sFuncArgs = "123, BA12:BB20, { 1, 2, 3], 23;45, [1,2,{a,b,c}}"
    print(get_funcargs(sFuncArgs))
    print_tokens("test 1, BA22:3 +123 test123 test(1,2 ,3, 4,5) 1-2 * / \ 'test what else' 123 1 2 3 ")




# vim: set sts=4 expandtab: #
