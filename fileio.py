#!/usr/bin/env python3
# fileio support routines
# HanishKVC, 2020
#

import os, sys
import traceback
import base64
import cryptography, secrets
import seckvc as sec
import nav
import cuikvc as cui


# Entities from main logic
GLOGFILE = None
GERRFILE = None
dlg = None
status = None
cstatusbar = None
THEQUOTE = None
THEFIELDSEP = None


# Whether to use internal or cryptography libraries AuthenticatedEncryption
# Both use similar concepts, but bitstreams are not directly interchangable
bInternalEncDec = True


def _save_file(me, scr, sFile, filePass=None):
    '''
    Save file in a csv format.

    If the cell data contains the field seperator in it, then
    the cell content is protected within single quotes.

    If successfully saved, then Clear the dirty bit.

    If filePass is provided then encrypt the file.
    '''
    f = open(sFile,"w+")
    if filePass != None:
        salt = secrets.token_bytes(16)
        userKey, fileKey = sec.get_basekeys(filePass, salt)
        salt = base64.urlsafe_b64encode(salt).decode()
        print("{}\n".format(salt), end="", file=f)
    for r in range(1, me['numRows']+1):
        curRow = ""
        for c in range(1, me['numCols']+1):
            data = me['data'].get((r,c))
            if (data != None):
                if data.find(THEFIELDSEP) != -1:
                    if not data.startswith(THEQUOTE):
                        data = "{}{}".format(THEQUOTE, data)
                    if not data.endswith(THEQUOTE):
                        data = "{}{}".format(data, THEQUOTE)
            else:
                data = ""
            curRow += "{}{}".format(data,THEFIELDSEP)
        curRow = curRow[:-1] # Remove the unwanted fieldsep at the end
        if filePass != None:
            lineKey = sec.get_linekey(r, userKey, fileKey)
            if bInternalEncDec:
                curRow = sec.aes_cbc_enc_b64(base64.urlsafe_b64decode(lineKey), curRow).decode()
            else:
                sym = cryptography.fernet.Fernet(lineKey)
                curRow = sym.encrypt(curRow.encode()).decode()
            #status(scr, ["saving line {}".format(r)],y=1)
        print("{}\n".format(curRow), end="", file=f)
    f.close()
    me['dirty'] = False
    print("savefile:{}".format(sFile), file=GLOGFILE)


def save_file(me, scr, sFile, filePass=None):
    '''
    save current spreadsheet in memory into specified file.

    If the file already exists, then alert the user about same.
    '''
    sFile = os.path.expanduser(sFile)
    if (os.path.exists(sFile)):
        got = dlg(scr, ["File:{}:exists overwrite? [y/N]".format(sFile)])
        if chr(got).upper() != "Y":
            cstatusbar(scr, ["[Saving is aborted]"])
            return
    if not verify_pass(scr, filePass):
        return
    try:
        cstatusbar(scr, ['[Saving file...]'])
        _save_file(me, scr, sFile, filePass)
    except:
        a,b,c = sys.exc_info()
        print("savefile:exception:{}:{}".format((a,b,c), sFile), file=GLOGFILE)
        traceback.print_exc(file=GERRFILE)
        dlg(scr, ["savefile:exception:{}:{}".format(a, sFile), "Press any key to continue"])


def _load_file(me, sFile, filePass=None):
    '''
    Load the specified csv file
    '''
    f = open(sFile)
    if filePass != None:
        line = f.readline()
        salt = base64.urlsafe_b64decode(line.encode())
        userKey, fileKey = sec.get_basekeys(filePass, salt)
    print("loadfile:{}".format(sFile), file=GLOGFILE)
    me['data'] = dict()
    r = 0
    for line in f:
        r += 1
        if filePass != None:
            lineKey = sec.get_linekey(r, userKey, fileKey)
            if bInternalEncDec:
                line = sec.aes_cbc_dec_b64(base64.urlsafe_b64decode(lineKey), line.encode()).decode()
            else:
                sym = cryptography.fernet.Fernet(lineKey)
                line = sym.decrypt(line.encode()).decode()
        c = 1
        i = 0
        sCur = ""
        bInQuote = False
        while i < (len(line)-1): # Remove the newline at the end
            t = line[i]
            if t == THEQUOTE:
                bInQuote = not bInQuote
                sCur += t
            elif t == THEFIELDSEP:
                if bInQuote:
                    sCur += t
                else:
                    if sCur != "":
                        me['data'][(r,c)] = sCur
                        sCur = ""
                    c += 1
            else:
                sCur += t
            i += 1
        if sCur != "":
            me['data'][(r,c)] = sCur
            sCur = ""
    f.close()
    me['numRows'] = r
    me['numCols'] = c


def load_file(me, scr, sFile, filePass=None):
    '''
    load the specified spreadsheet into memory.

    It checks if there is a dirty spreadsheet in memory, in which case, it gives option
    to user to abort the load_file operation.

    As a user could come out of help mode by using load_file, so it reverts from help mode,
    if that is the case.

    It clears the dirty flag.
    It clears the screen as well as repositions to A1 cell, if _load_file succeeds.
    '''
    if me['dirty']:
        got = dlg(scr, ["Spreadsheet not saved, discard and load new file? [y/N]".format(sFile)])
        if chr(got).upper() != "Y":
            cstatusbar(scr, ["Canceled loading of {}".format(sFile)])
            return False
    #if not verify_pass(scr, filePass):
    #    return
    try:
        sFile = os.path.expanduser(sFile)
        cstatusbar(scr, ['[Loading file...]'])
        me['cdataUpdate'] = True
        scr.clear()
        _load_file(me, sFile, filePass)
        me['dirty'] = False
        revertfrom_help_ifneeded(me)
        nav.goto_cell(scr, "A1")
        print("\033]2; {} [{}] \007".format("SpreadsheetKVC", sFile), file=sys.stdout)
        return True
    except:
        a,b,c = sys.exc_info()
        print("loadfile:exception:{}:{}".format((a,b,c), sFile), file=GLOGFILE)
        traceback.print_exc(file=GERRFILE)
        dlg(scr, ["loadfile:exception:{}:{}".format((a,b), sFile), "Press any key to continue"])
        return False


def load_help(me, scr):
    '''
    load help.csv file in readonly mode.

    If already in help mode, dont do anything other than repositioning to A1 cell.
    '''
    if me['helpModeSavedReadOnly'] != None:
        nav.goto_cell(scr, "A1")
        return
    if load_file(me, scr, "{}/help.csv".format(sys.path[0])):
        me['helpModeSavedReadOnly'] = me['readOnly']
        me['readOnly'] = True
    else:
        dlg(scr, ["loadhelp: save current spreadsheet or allow discarding of changes",
                  "for loading the help file                                        ",
                  "Press any key to continue...                                     "])



def revertfrom_help_ifneeded(me):
    '''
    Revert from help mode, if already in help mode.
    '''
    if me['helpModeSavedReadOnly'] != None:
        me['readOnly'] = me['helpModeSavedReadOnly']
        me['helpModeSavedReadOnly'] = None


def new_file(me, scr):
    '''
    Create a new spreadsheet in memory.

    It checks if there is a dirty spreadsheet in memory, in which case, it gives option
    to user to abort the new_file operation.

    As a user could come out of help mode by using new_file, so it reverts from help mode,
    if that is the case.
    '''
    if me['dirty']:
        got = dlg(scr, ["Spreadsheet not saved, discard and create new? [y/N]"])
        if chr(got).upper() == "Y":
            status(scr, ["Creating new spreadsheet in memory"])
        else:
            status(scr, ["Canceled new spreadsheet creation"])
            return False
    revertfrom_help_ifneeded(me)
    nav.goto_cell(scr, "A1")
    me['data'] = dict()
    me['dirty'] = False
    me['cdataUpdate'] = True


def verify_pass(scr, thePass):
    '''
    If thePass is not None, then check if user enters the same once again or not.
    '''
    if (thePass != None):
        got = cui.dlg(scr, ["*** Verfiy file password ***"], getString="Enter passwd:", clearInput="                    ")
        if got != thePass:
            dlg(scr, ["File pass not matching, aborting..."])
            return False
    return True


def _path_completion_update_lists(fpc, sDirName, sBaseName):
    if (len(fpc) == 0):
        fpc['pos'] = 0
        fpc['list'] = []
        fpc['prev'] = ""
        fpc['posSub'] = 0
        fpc['listSub'] = []
        fpc['prevBaseName'] = ""
    if (fpc['prev'] != sDirName):
        fpc['posSub'] = 0
        fpc['listSub'] = []
        fpc['prevBaseName'] = ""
        fpc['pos'] = 0
        try:
            fpc['list'] = sorted(os.listdir(sDirName))
            fpc['prev'] = sDirName
        except:
            fpc['list'] = []
            fpc['prev'] = ""
            return os.path.join(sDirName, sBaseName)
    if (fpc['prevBaseName'] != sBaseName):
        fpc['posSub'] = 0
        if (len(fpc['list']) > 0) and (sBaseName != ""):
            try:
                fpc['listSub'] = sorted(filter(lambda x: x.startswith(sBaseName), fpc['list']))
                fpc['prevBaseName'] = sBaseName
                if (len(fpc['listSub']) > 0):
                    return os.path.join(sDirName, fpc['listSub'][fpc['posSub']])
                else:
                    return os.path.join(sDirName, sBaseName)
            except:
                fpc['listSub'] = []
                fpc['prevBaseName'] = ""
        else:
            fpc['listSub'] = []
            fpc['prevBaseName'] = ""
    if (len(fpc['list']) > 0):
        return os.path.join(sDirName, fpc['list'][fpc['pos']])
    return os.path.join(sDirName, sBaseName)


def path_completion(fpc, sCur):
    '''
    Handle file system path completion.

    fpc maintains the context wrt path completion.

    sCur is the current path, which needs to be completed.
    '''
    sDirName = os.path.dirname(sCur)
    sBaseName = os.path.basename(sCur)
    if (len(fpc) > 0) and (fpc['prev'] == sDirName) and (len(fpc['list']) > 0):
        if (sBaseName != ""):
            if  (sBaseName == fpc['prevBaseName']) and (len(fpc['listSub']) > 0):
                fpc['posSub'] += 1
                fpc['posSub'] = fpc['posSub']%len(fpc['listSub'])
                return os.path.join(sDirName, fpc['listSub'][fpc['posSub']])
            else:
                return _path_completion_update_lists(fpc, sDirName, sBaseName)
        fpc['pos'] += 1
        fpc['pos'] = fpc['pos']%len(fpc['list'])
        return os.path.join(sDirName, fpc['list'][fpc['pos']])
    return _path_completion_update_lists(fpc, sDirName, sBaseName)



# vim: set sts=4 expandtab: #
