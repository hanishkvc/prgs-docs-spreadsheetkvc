#!/usr/bin/env python3
# Program helpdlg - Show help dialogs
# HanishKVC, 2020
#


import cuikvc as cui


def defaultmode_dlg(scr):
    helpMsgs = [
                "          SpreadsheetKVC - Default Mode    ",
                "",
                " [arrow keys] Move around the cells",
                " [i] Insert new content  into current cell",
                " [e] Edit the existing content in the current cell",
                " [d] Delete the contents of the current cell",
                " [c] Copy the contents of the current cell",
                " [C] Cut the contents of the current cell",
                " [p] Paste a previously copied/cut content into current cell ",
                " [h|?] show help / usage info",
                " [:] Enter explicit commands mode",
                ]
    cui.dlg(scr, helpMsgs, 1, 2, border=True)


def explicitcommandmode_dlg(scr):
    helpMsgs = [
                "    SpreadsheetKVC - ExplicitCommand Mode    ",
                "Pressing ':' enters this ExplicitCommand Mode",
                " [w file] write current spreadsheet to file",
                " [l file] load specified file",
                " [pw passwd file] write encrypted file",
                " [pl passwd file] load encrypted file",
                " [dr] delete cur row; [dc] del cur column",
                " [irb n] insert n rows before cur; [ira n] ins after",
                " [icb n] insert n cols before cur; [ica n] ins after",
                " [q] to quit program; [g celladdr] goto given cell",
                "[arrow left|right] move cursor to edit inbetween",
                "[Esc] to exit back to default mode",
                ]
    cui.dlg(scr, helpMsgs, 1, 2, border=True)


def help_dlg(scr):
    helpMsgs = [
                "   SpreadsheetKVC - a commandline curses based spreadsheet  ",
                "| Default Mode - used for navigating, editing across cells |",
                "|     and for entering other modes; Esc reverts to default |",
                "| Cell Edit Mode - Entered by pressing 'i' or 'e'          |",
                "|     Arrow keys to move cursor in edit buffer             |",
                "|     Enter key to save edit till now                      |",
                "|     prefix = for numeric or calc expressions             |",
                "|     without = prefix, content treated as text            |",
                "| Explicit Command Mode - Entered by pressing ':'          |",
                "|     w <file> to write; l <file> to load file             |",
                "|     pw|pl <passwd> <file> for encrypted files            |",
                "|     q to quit prg                                        |",
                "| Esc key reverts to Default from other modes              |",
                "|More info on DefaultMode [press d], ExplicitCmds [press e]|",
                "********Press any other key to get into the program*********",
                ]
    while True:
        got = cui.dlg(scr, helpMsgs, 1, 2, border=True)
        got = chr(got).upper()
        if got == 'D':
            defaultmode_dlg(scr)
        elif got == 'E':
            explicitcommandmode_dlg(scr)
        else:
            break



# vim: set sts=4 expandtab: #
