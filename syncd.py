#!/usr/bin/env python3
# Help keep cells in sync
# HanishKVC, 2020
#


import time
import parsekvc as parse


me = None
GERRFILE = None
GLOGFILE = None
_celladdr_valid = None


'''
Sync module maintains a list of both forward and reverse links.

Forward links can be used during insert and delete of rows/cols
to decide whether the =expressions in cells require updating.

    Any cells removed from the forward link of a given cell,
    should inturn have their revlinks updated such that the
    given cell is no longer part of it.

Reverse links tell as to which and all cells require their calcs
to be updated because a given cell has been updated.

    In turn each of those cells' revlink lists need to be checked
    as to which other cells inturn require their calcs also to be
    redone. Walk this revlink path, till there is no more revlinks
    to work on in the chain.

    Without revLinks, one will have to go through the forward links
    of all the cells, to see if they are dependent on the cell being
    updated/modified/edited/...

NOTE: Clearing the cached data of a cell, will automatically force
it to get recalculated.
'''


def init():
    me['fwdLinks'] = dict()
    me['revLinks'] = dict()


def cell_revlink_add(cell, revLink):
    '''
    Update the revLinks of a cell, to include the cell named by revLink.
    '''
    cellRevLink = me['revLinks'].get(cell)
    if cellRevLink == None:
        cellRevLink = set()
        me['revLinks'][cell] = cellRevLink
    cellRevLink.add(revLink)


def cell_revlink_discard(cell, revLink):
    '''
    Update the revLinks of a cell, by removing the cell named by revLink.
    '''
    cellRevLink = me['revLinks'].get(cell)
    if cellRevLink != None:
        cellRevLink.discard(revLink)
    else:
        print("WARN:syncdCellRevLinkDiscard:cell[{}] revLinkToRemove[{}]".format(cell, revLink), file=GERRFILE)


def cdata_clear_revlinks(cellKey, clearedSet=None, depth=0):
    '''
    Clear cdata cache entry of a cell and all its revLinks.

    When a cell is updated, it and all other cells which depend on this
    cell either directly or indirectly require to be cleared from calc
    cache, this logic helps with same.

    If clearedSet is provided, it is kept uptodate wrt all cells that have been
    cleared from calc cache, by this series of clear_revlinks calls. So for
    calc cell-to-cell chains involving lot of interconnections and deep chains,
    the logic will efficiently handle the situation. Without clearedSet it can
    take long time for deeply interconnected chains of calcs.
    '''
    #print("DBUG:syncdCdataClearRevLinks:{}:cell[{}]".format(depth, cellKey), file=GERRFILE)
    me['cdata'].pop(cellKey, None)
    if clearedSet != None:
        clearedSet.add(cellKey)
    revLinks = me['revLinks'].get(cellKey)
    if revLinks == None:
        revLinks = []
    for cell in revLinks:
        if (clearedSet != None) and (cell in clearedSet):
            continue
        cdata_clear_revlinks(cell, clearedSet, depth+1)


TIMECAP1 = 0
TIMECAP2 = 0
TIMECAP3 = 0
TOKENCAP1 = 0
def cell_updated_time_init():
    global TIMECAP1, TIMECAP2, TIMECAP3, TOKENCAP1
    TIMECAP1 = 0
    TIMECAP2 = 0
    TIMECAP3 = 0
    TOKENCAP1 = 0


def cell_updated(cellKey, sContent, clearCache=True, clearedSet=None):
    '''
    Update the fw and reverse links associated with each cell

    NOTE: For now it maintains a expanded list of cells. TO keep the
    logic which depends on this at other places simple and stupid.

    clearedSet can be used to ensure that calc cache clearing can be done
    efficiently for spreadsheets involving very-very-long chains of
    cell-to-cell interdependencies. Also when a bunch of cells are
    updated from the same context like say during insert / delete of
    rows / cols, the clearedSet helps to avoid trying to clear calc cache
    of same dependent cells more than once, across multiple calls to
    cell_updated.

    In normal use one should call cell_updated with a empty clearedSet.
    Think carefully before using cell_updated without clearedSet.
    '''
    global TIMECAP1, TIMECAP2, TIMECAP3, TOKENCAP1
    origCellFwdLink = me['fwdLinks'].get(cellKey)
    cellFwdLink = set()
    # Handle the new content of the cell
    T1 = time.time()
    if sContent == None:
        sContent = ""
    if sContent.strip().startswith('='):
        lCellAddrs = parse.get_celladdrs_incranges(sContent)
        #lCellAddrs = parse.get_celladdrs_incranges_internal(sContent)
        #print(lCellAddrs, file=GERRFILE)
    else:
        lCellAddrs = []
    TOKENCAP1 += len(lCellAddrs)
    T2 = time.time()
    TIMECAP1 += (T2-T1)
    for cellAddrPlus in lCellAddrs:
        if (len(cellAddrPlus) == 1):
            bCellAddr, key = _celladdr_valid(cellAddrPlus[0])
            if not bCellAddr:
                print("WARN:syncdCellUpdated:{}:{}={}".format(sContent, cellAddrPlus[0], key), file=GERRFILE)
                continue
            cellFwdLink.add(key)
            cell_revlink_add(key, cellKey)
        elif (len(cellAddrPlus) == 2):
            bCellAddr, key1 = _celladdr_valid(cellAddrPlus[0])
            if not bCellAddr:
                print("WARN:syncdCellUpdated:{}:{}={}".format(sContent, cellAddrPlus[0], key1), file=GERRFILE)
                continue
            bCellAddr, key2 = _celladdr_valid(cellAddrPlus[1])
            if not bCellAddr:
                print("WARN:syncdCellUpdated:{}:{}={}".format(sContent, cellAddrPlus[1], key2), file=GERRFILE)
                continue
            for r in range(key1[0], key2[0]+1):
                for c in range(key1[1], key2[1]+1):
                    cellFwdLink.add((r,c))
                    cell_revlink_add((r,c), cellKey)
    T3 = time.time()
    TIMECAP2 += (T3-T2)
    # Handle cells removed from the =expression
    if origCellFwdLink != None:
        droppedCells = origCellFwdLink.difference(cellFwdLink)
    else:
        droppedCells = set()
    if len(cellFwdLink) > 0:
        me['fwdLinks'][cellKey] = cellFwdLink
    else:
        if origCellFwdLink != None:
            me['fwdLinks'].pop(cellKey)
    for cell in droppedCells:
        cell_revlink_discard(cell, cellKey)
    # Clear cell calc cache for all dependents
    if clearCache:
        cdata_clear_revlinks(cellKey, clearedSet)
    T4 = time.time()
    TIMECAP3 += (T4-T3)


def create_links():
    '''
    Create fwd and rev Links freshly for all cells in the spreadsheet in memory.

    NOTE: Normally when/where create_links is called, even full calc cache update would be
    triggered by setting cdataUpdate flag to true before or after calling create_links,
    so the call to cell_updated from create_links can set clearCache to False.
    '''
    init()
    clearedSet = set()
    cell_updated_time_init()
    for key in me['data']:
        cell_updated(key, me['data'][key], clearCache=False, clearedSet=clearedSet)
    print("DBUG:T1:{}, T2:{}, T3:{}, CAs:{}".format(TIMECAP1, TIMECAP2, TIMECAP3, TOKENCAP1), file=GERRFILE)




# vim: set sts=4 expandtab: #
