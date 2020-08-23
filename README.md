# SpreadKVC

Author: HanishKVC, 2020
Version: v202008223ST2348

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

## Cell contents and =expressions

One can enter a textual data / string directly into the cell.

However if one wants to enter numeric values or expressions, one requires to prefix them
with = symbol.

example

	=2

	=5+3/6.8*2**32

	= (5+3)/(6.8*2)**32

Few functions are also supported by the program, as mentioned below. These functions can
also be used as part of the =expressions.

Example

	=10-5+sum(B10:C99)

	=cnt(B10:C99)

NOTE that the =expressions are evaluated using pythons eval function. So basic python
expressions can be evaluated as part of =expressions.

## Supported functions

sum

	sum the contents of the specified range of cells

cnt (count)

	get the count of non empty cells in the specified range of cells.

avg (average)

	calculate the average of the values in the range of cells. It doesnt consider
	the empty cells.

min

	the minimum value among the specified range of cells.

max

	the maximum value among the specified range of cells.

## csv file format

The csv file used by this program uses comma [,] to seperate the fields within each row
i.e within each line in the file.

If any field contains the field seperator (i.e ,) with in its content, then the content
is embedded within [`]s and not [']s.


## History

### 20200823IST1829

Implemented as part of the Gauri Ganesh weekend, to scratch a itch I had with need for a
simple commandline spreadsheet package. And also to explore and think randomly a bit and
have some interesting fun on the way.

Vasudhaiva Kutumbakam (the World is One Family)

