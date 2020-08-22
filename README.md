# SpreadKVC

Author: HanishKVC, 2020
Version: v20200822IST2348

spreadkvc is a simple spreadsheet program which runs on the commandline using ncurses and python.

It works with a slightly modified form of csv file.

## Usage

The program supports the following modes command mode, edit/insert mode and explicit command mode.

### command mode

The program by default runs in the implicit command mode. In this mode one can press the following
keys for achieving the specified operations.

* i can be used to insert new content in the current cell.

* e can be used to edit the current cell's content.

* c can be used to copy the current cell's content.

* C can be used to cut the current cell's content.

* p can be used to paste a previously copied/cut cell content into current cell.

* d can be used to delete the contents of the current cell.

* : can be used to enter the explicit command mode.

### explicit command mode

In the explicit command mode, the user can enter one of the following commands

* w file

	to save the contents of the current spreadsheet into specified file.

* l file

	to load the specified spreadsheet.

* dr

	used to delete the current row.
* dc

	used to delete the current column.

* irb num_of_rows

	insert n rows before current row.

* ira num_of_rows

	insert n rows after current row.

* icb num_of_cols

	insert n columns before current column.

* ica num_of_cols

	insert n columns after current column.

* e file (in future)

	to export the current spreadsheet into a file.

The user can enter the command and its arguments and then press enter key to trigger
the command. The user can use backspace to delete the chars to correct mistakes when
entering the command and the arguments.

### edit/insert mode

On pressing 'i', 'e' from the command mode, the user can enter this mode.

In this mode the user either enters a new content for the cell and or edit the existing
content of the cell.

As and when the user presses the enter key, the data entered till that point gets saved
into the cell. If one exits without pressing enter then any data entered after the last
enter key press will be lost.

User can press the ESC key to exit from this mode into the command mode.

