
#include <Python.h>
#include <stdbool.h>

#define THEQUOTE '\''
#define THEFIELDSEP ';'

PyObject * load_line(PyObject *self, PyObject *args) {
    int c = 1;
    int i = 0;
    char sCur[4096];
    int iS = 0;
    bool bInQuote = false;
    int lineLen = 0;
    char *line;
    char t;

    if (!PyArg_ParseTuple(args, "is", &lineLen, &line)) {
        return NULL;
    }
    if (lineLen == 0)
        return PyLong_FromLong(c);
    // Remove the newline at the end
    if (line[lineLen] == '\n')
        lineLen -= 1;
    while(i < lineLen) {
        t = line[i];
        if (t == THEQUOTE) {
            bInQuote = ~ bInQuote;
            sCur[iS] = t;
            iS += 1;
        } else if (t == THEFIELDSEP) {
            if (bInQuote) {
                sCur[iS] = t;
                iS += 1;
            } else {
                if (iS != 0) {
                    sCur[iS] = 0;
                    //me['data'][(r,c)] = sCur
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
        //me['data'][(r,c)] = sCur
    }
    return PyLong_FromLong(c);
}


// vim: set sts=4 expandtab: //
