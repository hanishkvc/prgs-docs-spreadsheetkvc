#!/usr/bin/env python3
# Help tab complete based on given completion tree
# HanishKVC, 2020
#


import parsekvc as parse


treeDB = {
            'help': None,
            'calign': { 'left': None, 'right': None, 'default': None },
            'cformat': { 'iffloat': None, 'number2float': None, 'neat': None, 'raw': None },
            'clear': None,
            'l': None,
            'w': None,
            's': None,
            'pl': None,
            'pw': None,
            'ps': None,
            'icb': None,
            'ica': None,
            'irb': None,
            'ira': None,
            'dr': None,
            'dc': None,
            'ctextquote': None,
            'cfieldsep': None,
            'g': None,
            'm': None,
            'mclear': None,
            'mshow': None,
            'new': None,
            'rcopy': None,
            'rcopyasis': None,
            'rclear': None,
            'rclearerr': None,
            'rgennums': None,
            'xrecalc': None,
            'xrows': None,
            'xcols': None,
            'xviewraw': None,
            'xviewnormal': None,
            '!': None,
            'q': None,
        }

tc = { 'pos': 0 }

def tab_complete(tc, tree, sIn):
    '''
    Allow crosschecking a given input string against a given tree of possibilities
    and inturn map the input to the nearest match
    if more than one match, then cycle through the matches
    '''
    if len(tc) == 0:
        tc['pos'] = 0
    tokens, types = parse.get_tokens(sIn)
    curDB = tree
    sOut = ""
    for curToken in tokens:
        theList = sorted(curDB.keys())
        filterAll = list(filter(lambda x: x.startswith(curToken), theList))
        if len(filterAll) == 0:
            sOut += "{} ".format(curToken)
            return sOut
        elif len(filterAll) == 1:
            sOut += "{} ".format(filterAll[0])
            curDB = curDB.get(curToken)
            if curDB == None:
                return sOut
            continue
        else:
            tc['pos'] += 1
            tc['pos'] = tc['pos'] % len(filterAll)
            sOut += "{} ".format(filterAll[tc['pos']])
            return sOut
    theList = sorted(curDB.keys())
    tc['pos'] += 1
    tc['pos'] = tc['pos'] % len(theList)
    sOut += "{} ".format(theList[tc['pos']])
    return sOut



# vim: set sts=4 expandtab: #
