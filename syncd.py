#!/usr/bin/env python3
# Help keep cells in sync
# HanishKVC, 2020
#


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
    '''
    origCellFwdLink = me['fwdLinks'].get(cellKey)
    cellFwdLink = set()
    # Handle the new content of the cell
    if sContent.strip().startswith('='):
        lCellAddrs = parse.get_celladdrs_incranges(sContent)
    else:
        lCellAddrs = []
    for cellAddrPlus in lCellAddrs:
        if (len(cellAddrPlus) == 1):
            bCellAddr, key = _celladdr_valid(cellAddrPlus[0])
            if not bCellAddr:
                print("WARN:syncdCellUpdated:{}:{}".format(sContent, key), file=GERRFILE)
                continue
            cellFwdLink.add(key)
            cell_revlink_add(key, cellKey)
        elif (len(cellAddrPlus) == 2):
            bCellAddr, key1 = _celladdr_valid(cellAddrPlus[0])
            if not bCellAddr:
                print("WARN:syncdCellUpdated:{}:{}".format(sContent, key), file=GERRFILE)
                continue
            bCellAddr, key2 = _celladdr_valid(cellAddrPlus[1])
            if not bCellAddr:
                print("WARN:syncdCellUpdated:{}:{}".format(sContent, key), file=GERRFILE)
                continue
            for r in range(key1[0], key2[0]+1):
                for c in range(key1[1], key2[1]+1):
                    cellFwdLink.add((r,c))
                    cell_revlink_add((r,c), cellKey)
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


def create_links():
    '''
    Create fwd and rev Links freshly for all cells in the spreadsheet in memory.

    NOTE: Normally when/where create_links is called, even full calc cache update would be
    triggered by setting cdataUpdate flag to true before or after calling create_links,
    so the call to cell_updated from create_links can set clearCache to False.
    '''
    init()
    clearedSet = set()
    for key in me['data']:
        cell_updated(key, me['data'][key], clearedSet)




# vim: set sts=4 expandtab: #
