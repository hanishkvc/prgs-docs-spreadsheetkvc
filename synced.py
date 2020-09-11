#!/usr/bin/env python3
# Help keep cells in sync
# HanishKVC, 2020
#


import parsekvc as parse


me = None


'''
Sync module maintains a list of both forward and reverse links.
'''


def init():
    me['fwdLinks'] = dict()
    me['revLinks'] = dict()


def cell_update_revlink(cell, revLink):
    cellRevLink = me['revLinks'].get(cell)
    if cellRevLink == None:
        cellRevLink = []
        me['revLinks'][cell] = cellRevLink
    cellRevLink.append(revLink)


def cell_updated(cellKey, sContent):
    '''
    Update the fw and reverse links associated with each cell

    NOTE: For now it maintains a expanded list of cells. TO keep the
    logic which depends on this at other places simple and stupid.
    '''
    cellFwdLink = me['fwdLinks'].get(cellKey)
    if cellFwdLink == None:
        cellFwdLink = []
        me['fwdLink'][cellKey] = cellFwdLink
    lCellAddrs = parse.get_celladdrs_incranges(sContent)
    for cellAddrPlus in lCellAddrs:
        if (len(cellAddrPlus) == 1):
            bCellAddr, key = _celladdr_valid(cellAddrPlus[0])
            if not bCellAddr:
                print("sync.cellUpdated:WARN:{}:{}".format(sContent, key))
                continue
            cellFwdLink.append(key)
            cell_update_revlink(key, cellKey)
        elif (len(cellAddrPlus) == 2):
            bCellAddr, key1 = _celladdr_valid(cellAddrPlus[0])
            if not bCellAddr:
                print("sync.cellUpdated:WARN:{}:{}".format(sContent, key))
                continue
            bCellAddr, key2 = _celladdr_valid(cellAddrPlus[1])
            if not bCellAddr:
                print("sync.cellUpdated:WARN:{}:{}".format(sContent, key))
                continue
            for r in range(key1[0], key2[0]+1):
                for c in range(key1[1], key2[1]+1):
                    cellFwdLink.append((r,c))
                    cell_update_revlink((r,c), cellKey)




# vim: set sts=4 expandtab: #
