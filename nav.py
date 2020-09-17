#!/usr/bin/env python3
# Navigation routines
# HanishKVC, 2020
#

import parsekvc as parse

me = None
cdraw = None
cellcur = None


def _goto_cell(stdscr, r, c):
    '''
    Center the specified cell on the screen. It also sets
        the program's current cell info variables as well as
        the cursor libraries cursor position to this cell.
    '''
    tr = r - int(me['dispRows']/2)
    if tr < 1:
        tr = 1
    me['viewRowStart'] = tr
    tc = c - int(me['dispCols']/2)
    if tc < 1:
        tc = 1
    me['viewColStart'] = tc
    me['curRow'] = r
    me['curCol'] = c
    stdscr.clear()
    cdraw(stdscr)
    cellcur(stdscr, r, c)


def goto_cell(stdscr, args):
    bCellAddr, (r,c) = parse.celladdr_valid(args)
    if bCellAddr:
        if r > me['numRows']:
            r = me['numRows']
        if c > me['numCols']:
            c = me['numCols']
        _goto_cell(stdscr, r, c)


def cellcur_left():
    '''
    Move the current cell cursor to the left, if possible.

    It also ensures that the cursor position is 1 or greater.
    It also adjusts the viewport if required.
    '''
    me['curCol'] -= 1
    if (me['curCol'] <= 0):
        me['curCol'] = 1
    if (me['viewColStart'] > me['curCol']):
        me['viewColStart'] = me['curCol']


def cellcur_right():
    '''
    Move the current cell cursor to the right, if possible.

    It also ensures that the cursor position is within the available data cells.
    It also adjusts the viewport as required.
    '''
    me['curCol'] += 1
    if (me['curCol'] > me['numCols']):
        me['curCol'] = me['numCols']
    diff = me['curCol'] - me['viewColStart'] + 1
    if (diff > me['dispCols']):
        me['viewColStart'] = me['curCol'] - me['dispCols'] + 1


def cellcur_up():
    '''
    Move the current cell cursor up, if possible.

    It also ensures that the cursor position is 1 or greater.
    It also adjusts the viewport if required.
    '''
    me['curRow'] -= 1
    if (me['curRow'] < 1):
        me['curRow'] = 1
    if (me['viewRowStart'] > me['curRow']):
        me['viewRowStart'] = me['curRow']


def cellcur_down():
    '''
    Move the current cell cursor down, if possible.

    It also ensures that the cursor position is within the available data cells.
    It also adjusts the viewport as required.
    '''
    me['curRow'] += 1
    if (me['curRow'] > me['numRows']):
        me['curRow'] = me['numRows']
    diff = me['curRow'] - me['viewRowStart'] + 1
    if (diff > me['dispRows']):
        me['viewRowStart'] = me['curRow'] - me['dispRows'] + 1




# vim: set sts=4 expandtab: #
