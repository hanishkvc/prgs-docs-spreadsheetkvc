/*
 * chelper - A c based module containing helpers to speed up some of the logics used by the python logic.
 * HanishKVC, 2020
 */
#include <Python.h>
#include <stdbool.h>
#include <ctype.h>


#define THEQUOTE '\''
#define THEFIELDSEP ';'
char gTextQuote = THEQUOTE;
char gFieldSep = THEFIELDSEP;

PyDoc_STRVAR(
    config_csvchars_doc,
    "config_csvchars(theFieldSep, theTextQuote)\n"
    "--\n\n"
    "configure the chars to use wrt text quoting and field seperation in the csv files\n");
static PyObject* config_csvchars(PyObject *self, PyObject *args) {
    if (!PyArg_ParseTuple(args, "cc", &gFieldSep, &gTextQuote)) {
        return NULL;
    }
    Py_RETURN_TRUE;
}


// Add a given cell content to the data dictionary
static void dict_add(PyObject *dict, int r, int c, char *s) {
    //printf("%d:%d:%s\n", r, c, s);
    PyObject *k = PyTuple_New(2);
    PyTuple_SetItem(k, 0, PyLong_FromLong(r)); // PyTupSetItem steals PyLong from us, so we dont have to worry
    PyTuple_SetItem(k, 1, PyLong_FromLong(c)); // PyTupSetItem steals PyLong from us, so we dont have to worry
    PyObject *v = PyUnicode_FromString(s); // PyObject_SetItem wont steal this from us, so we have to worry about it, so get a handle to it.
    PyObject_SetItem(dict, k, v); // PyObjSetItem wont steal PyTuple and PyUnicode from us, so we have to handle them
    Py_DECREF(k); // As we no longer require this, so dec refcnt
    Py_DECREF(v); // As we no longer require this, so dec refcnt
}


// Extract the cell contents from the line and add it to the given data dictionary
PyDoc_STRVAR(
    load_line_doc,
    "load_line(dataDict, rowNumber, lineString, lineLen)\n"
    "--\n\n"
    "load the given csv file line into data dictinary for the cells\n"
    "Currently the following limits are there compared to pure python logic\n"
    "\tmax cell content size is 4k\n"
    "\tthe quote is fixed to '\n"
    "\tthe fieldsep is fixed to ;\n");
static PyObject* load_line(PyObject *self, PyObject *args) {
    int r = 0;
    int c = 1;
    int i = 0;
    char sCur[4096];
    int iS = 0;
    bool bInQuote = false;
    int lineLen = 0;
    char *line;
    char t;
    PyObject *dict;

    if (!PyArg_ParseTuple(args, "Oisi", &dict, &r, &line, &lineLen)) {
        return NULL;
    }
    //printf("%d:%d:%s\n", r, lineLen, line);
    if (lineLen == 0)
        return PyLong_FromLong(c);
    // Remove the newline at the end, if any
    if (line[lineLen] == '\n')
        lineLen -= 1;
    while(i < lineLen) {
        t = line[i];
        if (t == gTextQuote) {
            bInQuote = !bInQuote;
            sCur[iS] = t;
            iS += 1;
        } else if (t == gFieldSep) {
            if (bInQuote) {
                sCur[iS] = t;
                iS += 1;
            } else {
                if (iS != 0) {
                    sCur[iS] = 0;
                    dict_add(dict, r, c, sCur);
                    iS = 0;
                }
                c += 1;
            }
        } else {
            sCur[iS] = t;
            iS += 1;
        }
        i += 1;
    }
    if (iS != 0) {
        sCur[iS] = 0;
        dict_add(dict, r, c, sCur);
    }
    return PyLong_FromLong(c);
}


//RE_CAINCR = re.compile("(.*?)([$]?[a-zA-Z]+[$]?[0-9]+[ ]*[:]?)(.*?)")
PyDoc_STRVAR(
    get_celladdrs_incranges_fromre_doc,
    "cellAddrsList = get_celladdrs_incranges_fromre(rawREList)\n"
    "--\n\n"
    "Parse the output of RE_CAINCR and extract cell addresses (including ranges) in them.\n"
    "\n"
    "NOTE: This doesnt ignore contents of quoted text within the string.\n");
static PyObject* get_celladdrs_incranges_fromre(PyObject *self, PyObject *args) {
    PyObject *caList = PyList_New(0);
    PyObject *caRange = NULL;
    //int caListCnt = 0;
    bool bInCARange = false;
    PyObject *rawList;
    long int caLen;
    int iD, iS, j;
    char sCleanCA[32];
    int cCleanCALast;

    if (!PyArg_ParseTuple(args, "O", &rawList)) {
        return NULL;
    }
    int listLen = PyList_Size(rawList);
    //printf("DBUG:GotList ofSize[%d] fromArgs\n", listLen);
    for(int i = 0; i < listLen; i++) {
        PyObject *raw = PyList_GetItem(rawList, i);
        PyObject *ca = PyTuple_GetItem(raw, 1);
        char *sCA = PyUnicode_AsUTF8AndSize(ca, &caLen);
        //printf("DBUG:%d:%s\n", i, sCA);
        // Remove any space in ca
        iD = 0;
        for(iS = 0; iS < caLen; iS++) {
            if (sCA[iS] == ' ')
                continue;
            sCleanCA[iD] = sCA[iS];
            iD += 1;
        }
        sCleanCA[iD] = 0;
        if (iD > 0) {
            cCleanCALast = sCleanCA[iD-1];
            // Remove ':' if any at end
            if (cCleanCALast == ':') {
                iD -= 1;
                sCleanCA[iD] = 0;
            }
        } else {
            cCleanCALast = 0;
        }
        if (bInCARange) {
            PyObject *preCA = PyTuple_GetItem(raw, 0);
            char *sPreCA = PyUnicode_AsUTF8AndSize(preCA, &caLen);
            //printf("DBUG:%d:%s\n", i, sPreCA);
            //Py_DECREF(preCA);
            bool bCellAddrRangeOk = true;
            for(j = 0; j < caLen; j++) {
                if (sPreCA[j] != ' ') {
                    bCellAddrRangeOk = false;
                }
            }
            if (bCellAddrRangeOk) {
                //caList[-1].append(pCA)
                int iEnd = PyList_Size(caList)-1;
                if (iEnd == -1) {
                    caRange = PyList_New(0);
                    PyList_Append(caRange, PyUnicode_FromString(sCleanCA));
                    PyList_Append(caList, caRange);
                } else {
                    caRange = PyList_GetItem(caList, iEnd);
                    PyList_Append(caRange, PyUnicode_FromString(sCleanCA));
                }
            } else {
                caRange = PyList_New(0);
                PyList_Append(caRange, PyUnicode_FromString(sCleanCA));
                PyList_Append(caList, caRange);
            }
            bInCARange = false;
        } else {
            caRange = PyList_New(0);
            PyList_Append(caRange, PyUnicode_FromString(sCleanCA));
            PyList_Append(caList, caRange);
        }
        if (cCleanCALast == ':') {
            PyObject *postCA = PyTuple_GetItem(raw, 2);
            char *sPostCA = PyUnicode_AsUTF8AndSize(postCA, &caLen);
            //Py_DECREF(postCA);
            bool bCellAddrRangeOk = true;
            for(j = 0; j < caLen; j++) {
                if (sPostCA[j] != ' ') {
                    bCellAddrRangeOk = false;
                }
            }
            if (bCellAddrRangeOk)
                bInCARange = true;
        }
        //Py_DECREF(raw);
        //Py_DECREF(ca);
    }
    return caList;
}


PyDoc_STRVAR(
    get_celladdrs_incranges_doc,
    "cellAddrsList = get_celladdrs_incranges(sIn)\n"
    "--\n\n"
    "Parse the given string and extract cell addresses (including ranges) in them.\n"
    "\n"
    "NOTE: This doesnt ignore contents of quoted text within the string, currently.\n");
static PyObject* get_celladdrs_incranges(PyObject *self, PyObject *args) {
    PyObject *caList = PyList_New(0);
    PyObject *caRange = NULL;
    char sCur[32];
    char *sIn;
    int iS, iC;
    int iToken, iCARange;
    int c;

    if (!PyArg_ParseTuple(args, "s", &sIn)) {
        return NULL;
    }
    iS = 0;
    iC = 0;
    iToken = 0; // iToken = 0 (Not in token), 1 ($ found), 2 (alpha part), 3 (num part)
    iCARange = 0; // 0 (Not CARange), 1 (CA inc 1st part of CA Range), 2 (: found)
    while (true) {
        c = sIn[iS];
        if (c == 0) {
            break;
        }
        if (isalpha(c)) {
            if (iToken == 0) {
                iToken = 2;
                iC = 0;
                sCur[iC] = c;
                iC += 1;
            } else if ((iToken == 1) || (iToken == 2)) {
                iToken = 2;
                sCur[iC] = c;
                iC += 1;
            } else { // Cant get alpha after numerals in cell addr
                iToken = 0;
                if (iCARange == 2)
                    iCARange = 0;
            }
        } else if (isdigit(c)) {
            if ((iToken == 2) || (iToken == 3)) {
                iToken = 3;
                sCur[iC] = c;
                iC += 1;
            } else {
                iToken = 0;
                if (iCARange == 2)
                    iCARange = 0;
            }
        } else if (c == '$') {
            if (iToken == 0) {
                iToken = 1;
                iC = 0;
                sCur[iC] = c;
                iC += 1;
            } else {
                iToken = 0;
                if (iCARange == 2)
                    iCARange = 0;
            }
        } else {
            if (iToken == 3) { // Found a cell addr
                sCur[iC] = 0;
                //printf("DBUG:cGetCAIncR:%d:%s\n", iCARange, sCur);
                if (iCARange == 2) {
                    int iEnd = PyList_Size(caList)-1;
                    caRange = PyList_GetItem(caList, iEnd);
                    PyList_Append(caRange, PyUnicode_FromString(sCur));
                    iCARange = 0;
                } else {
                    caRange = PyList_New(0);
                    PyList_Append(caRange, PyUnicode_FromString(sCur));
                    PyList_Append(caList, caRange);
                    iCARange = 1;
                }
            } else if (iToken == 2) {
                if (iCARange == 2)
                    iCARange = 0;
            }
            if (c == ':') {
                if (((iToken == 3) || (iToken == 0)) && (iCARange == 1)) {
                    iCARange = 2;
                }
            }
            iToken = 0;
        }
        iS += 1;
    }
    return caList;
}



static PyMethodDef CSVLoadMethods[] = {
    { "load_line", load_line, METH_VARARGS, load_line_doc },
    { "get_celladdrs_incranges", get_celladdrs_incranges, METH_VARARGS, get_celladdrs_incranges_doc },
    { "config_csvchars", config_csvchars, METH_VARARGS, config_csvchars_doc },
    { "get_celladdrs_incranges_fromre", get_celladdrs_incranges_fromre, METH_VARARGS, get_celladdrs_incranges_fromre_doc },
    { NULL, NULL, 0, NULL}
};


static struct PyModuleDef chelpermodule = {
    PyModuleDef_HEAD_INIT,
    "chelper",
    NULL,
    -1,
    CSVLoadMethods
};


/* One could test this like this
 * import chelper
 * me = dict()
 * ts = "test, me; what else"
 * chelper.load_line(me, 1, ts, len(ts))
 * chelper.get_celladdrs_incranges("string containing cell addresses (including ranges) like AB12 : BC123 + DE12 - 999 /1.5 + MN93:PQ99 / XY1 :YZ1024")
 */
PyMODINIT_FUNC PyInit_chelper(void) {
    return PyModule_Create(&chelpermodule);
}


// vim: set sts=4 expandtab: //
