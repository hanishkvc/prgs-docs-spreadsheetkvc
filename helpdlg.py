#!/usr/bin/env python3
# Program helpdlg - Show help dialogs
# HanishKVC, 2020
#


import cuikvc as cui


def defaultmode_dlg(scr):
    helpMsgs = [
                "          SpreadsheetKVC - Default Mode    ",
                "",
                "  [arrow keys] Move around the cells",
                "  [i] Insert new content into current cell",
                "  [e] Edit the existing content in the current cell",
                "  [D] Delete the contents of the current cell",
                "  [c] Copy the contents of the current cell",
                "  [C] Cut the contents of the current cell",
                "  [p] Paste previously copied/Cut content into currentCell  ",
                "  [h|?] show help / usage info",
                "  [:] Enter explicit commands mode",
                "",
                "",
                "  Use :help to get more details, including supported funcs  ",
                "******* Look at README.md and help.csv for more info *******",
                ]
    cui.dlg(scr, helpMsgs, 1, 2, border=True)


def explicitcommandmode_dlg(scr):
    helpMsgs = [
                "        SpreadsheetKVC - ExplicitCommand Mode        ",
                "Pressing ':' in defaultMode enters this ExplicitCommand Mode",
                "   [pw passwd file] write encrypted file",
                "   [pl passwd file] load encrypted file",
                "   [w file] write to file;            [l file] load file",
                "   [dr n] delNRows startFrom curRow;  [dc n] del n cols     ",
                "   [irb n] insert n rows before cur;  [ira n] ins after     ",
                "   [icb n] insert n cols before cur;  [ica n] ins after     ",
                "   [g celladdr] goto given cell;      [clear] clear sheet   ",
                "   [new] new spreadsheet in memory;   [help] show help.csv  ",
                "   [!shellCmd args] run shell cmd;    [q] Quits the Prg",
                "[arrow left|right] move cursor to edit inbetween",
                "[Esc] to exit back to default mode",
                "",
                "******* Look at README.md and help.csv for more info *******",
                ]
    cui.dlg(scr, helpMsgs, 1, 2, border=True)


def help_dlg(scr):
    helpMsgs = [
                "   SpreadsheetKVC - a commandline curses based spreadsheet  ",
                "| Default Mode - used for navigating, editing cells and    |",
                "|     for entering other modes; Esc reverts to default     |",
                "| Cell Edit Mode - Entered by pressing 'i' or 'e'          |",
                "|     Arrow keys to move cursor in edit buffer             |",
                "|     Enter key saves edit to memory; Esc discards edit.   |",
                "|     prefix = for numeric or calc expressions             |",
                "|     without = prefix, content treated as text            |",
                "| Explicit Command Mode - Entered by pressing ':'          |",
                "|     [w <file>] to write     [l <file>] to load file      |",
                "|     [pw|pl <passwd> <file>] for encrypted files          |",
                "|     [help] help.csv [new] new spreadsheet [q] quit prg   |",
                "| Esc key reverts to Default from other modes              |",
                "|More info on DefaultMode [press d], ExplicitCmds [press e]|",
                "********Press any other key to get into the program*********",
                ]
    while True:
        got = cui.dlg(scr, helpMsgs, 1, 2, border=True)
        if (got == ord('D')) or (got == ord('d')):
            defaultmode_dlg(scr)
        elif (got == ord('E')) or (got == ord('e')):
            explicitcommandmode_dlg(scr)
        else:
            break



# vim: set sts=4 expandtab: #
