/*
 * csvload - A c based module for use from within python
 * HanishKVC, 2020
 */
#include <Python.h>
#include <stdbool.h>


// TODO: Get these as arguments later
// Currently these are hardcoded
#define THEQUOTE '\''
#define THEFIELDSEP ';'


// Add a given cell content to the data dictionary
static void dict_add(PyObject *dict, int r, int c, char *s) {
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
    if (lineLen == 0)
        return PyLong_FromLong(c);
    // Remove the newline at the end, if any
    if (line[lineLen] == '\n')
        lineLen -= 1;
    while(i < lineLen) {
        t = line[i];
        if (t == THEQUOTE) {
            bInQuote = !bInQuote;
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
    { "load_line", load_line, METH_VARARGS, load_line_doc },
    { NULL, NULL, 0, NULL}
};


static struct PyModuleDef csvloadmodule = {
    PyModuleDef_HEAD_INIT,
    "csvload",
    NULL,
    -1,
    CSVLoadMethods
};


/* One could test this like this
 * import csvload
 * me = dict()
 * ts = "test, me; what else"
 * csvload.load_line(me, 1, ts, len(ts))
 */
PyMODINIT_FUNC PyInit_csvload(void) {
    return PyModule_Create(&csvloadmodule);
}


// vim: set sts=4 expandtab: //
