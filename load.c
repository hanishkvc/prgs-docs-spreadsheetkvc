
#include <Python.h>
#include <stdbool.h>

#define THEQUOTE '\''
#define THEFIELDSEP ';'


// Add a given cell content to the data dictionary
void dict_add(PyObject *dict, int r, int c, char *s) {
    PyObject *k = PyTuple_New(2);
    PyTuple_SetItem(k, 0, PyLong_FromLong(r));
    PyTuple_SetItem(k, 1, PyLong_FromLong(c));
    PyObject_SetItem(dict, k, PyBytes_FromString(s));
}


// Extract the cell contents from the line and add it to the given data dictionary
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
    if (lineLen == 0)
        return PyLong_FromLong(c);
    // Remove the newline at the end, if any
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
        dict_add(dict, r, c, sCur);
    }
    return PyLong_FromLong(c);
}


static PyMethodDef CSVLoadMethods[] = {
    { "load_line", load_line, METH_VARARGS, "load a csv file line" },
    { NULL, NULL, 0, NULL}
};


static struct PyModuleDef csvloadmodule = {
    PyModuleDef_HEAD_INIT,
    "csvload",
    -1,
    CSVLoadMethods
};


// vim: set sts=4 expandtab: //
