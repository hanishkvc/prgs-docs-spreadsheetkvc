#!/usr/bin/env python3
# Help tab complete based on given completion tree
# HanishKVC, 2020
#


import parsekvc as parse


treeDB = {
            'help': None,
            'calign': { 'left': None, 'right': None, 'default': None },
            'cformat': {
                        'iffloat': { 'ANYNUM': None },
                        'number2float':  { 'yes': None, 'no': None },
                        'neat': None,
                        'raw': None
                        },
            'clear': None,
            'l': None,
            'w': None,
            's': None,
            'pl': None,
            'pw': None,
            'ps': None,
            'icb': { 'ANYNUM': None },
            'ica': { 'ANYNUM': None },
            'irb': { 'ANYNUM': None },
            'ira': { 'ANYNUM': None },
            'dr': { 'ANYNUM': None },
            'dc': { 'ANYNUM': None },
            'ctextquote': { 'ANYCHAR': None },
            'cfieldsep': { 'ANYCHAR': None },
            'g': { 'ANYCELLADDR': None },
            'm': None,
            'mclear': None,
            'mshow': None,
            'new': None,
            'rcopy': { 'ANYCELLRANGE': { 'ANYCELLRANGEorANYCELLADDR': None } },
            'rcopyasis': { 'ANYCELLRANGE': { 'ANYCELLRANGEorANYCELLADDR': None } },
            'rclear': None,
            'rclearerr': None,
            'rgennums': { 'ANYCELLRANGE': { 'ANYNUMStart': { 'ANYNUMDelta': None } } },
            'xrecalc': None,
            'xrows': { 'ANYNUM': None },
            'xcols': { 'ANYNUM': None },
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
    bSpaceAtEnd = (sIn[-1] == ' ')
    tokens, types = parse.get_tokens(sIn, ANAddOn=[':', '@'])
    curDB = tree
    sOut = ""
    for i in range(len(tokens)):
        curToken = tokens[i]
        i += 1
        theList = sorted(curDB.keys())
        if len(theList) == 1:
            if theList[0].startswith('ANY'):
                curDB = curDB.get(theList[0])
                if curDB == None:
                    sOut += "{}".format(curToken)
                    return sOut
                sOut += "{} ".format(curToken)
                continue
        filterAll = list(filter(lambda x: x.startswith(curToken), theList))
        if len(filterAll) == 0:
            sOut += "{}".format(curToken)
            return sOut
        elif len(filterAll) == 1:
            curDB = curDB.get(curToken)
            if curDB == None:
                sOut += "{}".format(filterAll[0])
                return sOut
            sOut += "{} ".format(filterAll[0])
            continue
        else:
            if curToken in filterAll:
                if (i < len(tokens)) or bSpaceAtEnd:
                    curDB = curDB.get(curToken)
                    if curDB == None:
                        sOut += "{}".format(curToken)
                        if bSpaceAtEnd:
                            sOut += ' '
                        return sOut
                    sOut += "{} ".format(curToken)
                    continue
            tc['pos'] += 1
            tc['pos'] = tc['pos'] % len(filterAll)
            sOut += "{}".format(filterAll[tc['pos']])
            return sOut
    theList = sorted(curDB.keys())
    tc['pos'] += 1
    tc['pos'] = tc['pos'] % len(theList)
    sOut += "{}".format(theList[tc['pos']])
    return sOut



# vim: set sts=4 expandtab: #
