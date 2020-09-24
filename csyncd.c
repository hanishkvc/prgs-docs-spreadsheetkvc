/*
 * C helpers for keeping cells in sync
 * HanishKVC, 2020
 */


#include <Python.h>


PyDoc_SetStr(
    cdata_clear_revlinks_doc,
    "cdata_clear_revlinks(cellKey, clearedSet=None, depth=0)\n"
    "--\n\n"
    "cdata_clear_revlinks(meCData, cellKey, meRevLinks, clearedSet=None, depth=0)\n"
    "Clear cdata cache entry of a cell and all its revLinks.\n"
    "\n"
    "When a cell is updated, it and all other cells which depend on this\n"
    "cell either directly or indirectly require to be cleared from calc\n"
    "cache, this logic helps with same.\n" );
static void cdata_clear_revlinks(PyObject *self, PyObject *args) {
    //print("DBUG:syncdCdataClearRevLinks:{}:cell[{}]".format(depth, cellKey), file=GERRFILE)
    PyObject *meCData;
    PyObject *cellKey;
    PyObject *meRevLinks;
    PyList *clearedSet = NULL;
    int depth = 0;

    if (!PyArg_ParseTuple(args, "OOO|Oi", &meCData, &cellKey, &meRevLinks, &clearedSet, &depth)) {
        return;
    }
    if (PyDict_Contains(meCData, cellKey) == 1) {
        PyDict_DelItem(meCData, cellKey);
    }
    if ((clearedSet != Py_None) && (clearedSet != NULL)) {
        PySet_Add(clearedSet, cellKey)
    }
    if (PyDict_Contains(meRevLinks, cellKey) != 1) {
        return;
    }
    PyList *revLinks = PyDict_GetItem(meRevLinks, cellKey);
    if (revLinks == NULL)
        return;
    int listLen = PyList_Size(revLinks);
    if (clearedSet == Py_None)
        clearedSet = NULL;
    for(i = 0; i < listLen; i++) {
        PyObject *cell = PyList_GetItem(revLinks, i);
        if ((clearedSet != NULL) && (PySet_Contains(clearedSet, cell) == 1)) {
            continue;
        }
        cdata_clear_revlinks(meCData, cell, meRevLinks, clearedSet, depth+1)
    }
}


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
            bCellAddr, key = parse.celladdr_valid(cellAddrPlus[0])
            if not bCellAddr:
                print("WARN:syncdCellUpdated:{}:{}={}".format(sContent, cellAddrPlus[0], key), file=GERRFILE)
                continue
            cellFwdLink.add(key)
            cell_revlink_add(key, cellKey)
        elif (len(cellAddrPlus) == 2):
            bCellAddr, key1 = parse.celladdr_valid(cellAddrPlus[0])
            if not bCellAddr:
                print("WARN:syncdCellUpdated:{}:{}={}".format(sContent, cellAddrPlus[0], key1), file=GERRFILE)
                continue
            bCellAddr, key2 = parse.celladdr_valid(cellAddrPlus[1])
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

    As create links doesnt touch the calc cache, so remember to either

        force clear the full calc cache by using cdataUpdate

        OR adjust calc cache suitably in the context from where create_links is called.
    '''
    init()
    clearedSet = set()
    cell_updated_time_init()
    for key in me['data']:
        cell_updated(key, me['data'][key], clearCache=False, clearedSet=clearedSet)
    print("DBUG:T1:{}, T2:{}, T3:{}, CAs:{}".format(TIMECAP1, TIMECAP2, TIMECAP3, TOKENCAP1), file=GERRFILE)




# vim: set sts=4 expandtab: #
