#!/usr/bin/env python3
# A generic parse helping routines
# HanishKVC, 2020
#

import enum

TokenType = enum.Enum("TokenType", "NoMore AlphaNum Symbol Sign Brackets Unknown")
def get_token(sIn, startPos=0, bGetTokenDecimalAlso=True):
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
        if sIn[i] in [ '(', ')' ]:
            if bInToken:
                return TokenType.AlphaNum, sOut, iPosStart
            return TokenType.Brackets, sIn[i], i
        break
    if bInToken:
        return TokenType.AlphaNum, sOut, iPosStart
    if i >= len(sIn):
        return TokenType.NoMore, "", -1
    return TokenType.Unknown, sIn[i], i


def print_tokens(sIn):
    iPos = 0
    while True:
        tokenType, sOut, iPos = get_token(sIn, iPos)
        if tokenType == TokenType.NoMore:
            break
        print("Token:[{}]".format(sOut))
        iPos += len(sOut)


# vim: set sts=4 expandtab: #
