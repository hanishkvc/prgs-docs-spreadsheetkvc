#!/usr/bin/env python3
# Program helpdlg - Show help dialogs
# HanishKVC, 2020
#


import cuikvc as cui


def defaultmode_dlg(scr):
    helpMsgs = [ "SpreadsheetKVC - Default Mode",
                "",
                "\t\t[arrow keys] Move around the cells",
                "\t\t[i] Insert new content  into current cell",
                "\t\t[e] Edit the existing content in the current cell",
                "\t\t[d] Delete the contents of the current cell",
                "\t\t[c] Copy the contents of the current cell",
                "\t\t[C] Cut the contents of the current cell",
                "\t\t[p] Paste a previously copied/cut content into current cell",
                "\t\t[:] Enter explicit commands mode",
                ]
    cui.dlg(scr, helpMsgs, 2, 3, border=True)


def explicitcommandmode_dlg(scr):
    helpMsgs = [ "SpreadsheetKVC - Default Mode",
                "",
                "\t\t[arrow keys] Move around the cells",
                "\t\t[i] Insert new content  into current cell",
                "\t\t[e] Edit the existing content in the current cell",
                "\t\t[d] Delete the contents of the current cell",
                "\t\t[c] Copy the contents of the current cell",
                "\t\t[C] Cut the contents of the current cell",
                "\t\t[p] Paste a previously copied/cut content into current cell",
                "\t\t[:] Enter explicit commands mode",
                ]
    cui.dlg(scr, helpMsgs, 2, 3, border=True)


def help_dlg(scr):
    helpMsgs = [ "SpreadsheetKVC - a commandline curses based spreadsheet",
                "",
                " The program supports 3 modes",
                "\t Default Mode - used for navigating,",
                "\t\t editing across cells, entering other modes",
                "\t\t Esc key reverts to Default from other modes",
                "\t\t [press d] to get additional info",
                "\t Cell Edit Mode - Entered by pressing i or e",
                "\t\t Arrow keys to move cursor in edit buffer",
                "\t\t Enter key to save edit till now",
                "\t\t prefix = for numeric or calc expressions",
                "\t\t without = prefix, content treated as text",
                "\t Explicit Command Mode - : to enter this mode",
                "\t\t w <file> to write; l <file> to load file",
                "\t\t pw <passwd> <file> encrypt to file",
                "\t\t q to quit prg",
                "\t\t [press e] to get additional info",
                ]
    while True:
        got = cui.dlg(scr, helpMsgs, 2, 3, border=True)
        got = chr(got).upper()
        if got == 'D':
            defaultmode_dlg(scr)
        elif got == 'E':
            explicitcommandmode_dlg(scr)
        else:
            break



# vim: set sts=4 expandtab: #
