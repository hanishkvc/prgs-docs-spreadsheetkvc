# SpreadSheetKVC

Author: HanishKVC, 2020
Version: v20200823IST2336

spreadsheetkvc is a simple spreadsheet program which runs on the commandline using ncurses and python.

It works with a slightly modified form of csv file.

## Usage

The program supports the following modes command mode, edit/insert mode and explicit command mode.

### command mode (implicit)

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

This mode is entered by pressing : when in the default/implicit command mode.
In this explicit command mode, the user can enter one of the following commands

* w file

	to save the contents of the current spreadsheet into specified file.
	Do note that it will overwrite the file, if it already exists.

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

On pressing the enter key, the specified command will be run and the program reverts
back to implicit command mode.

### edit/insert mode

On pressing 'i', 'e' from the implicit command mode, the user can enter this mode.

In this mode the user either enters a new content for the cell and or edit the existing
content of the cell.

As and when the user presses the enter key, the data entered till that point gets saved
into the cell. If one exits without pressing enter then any data entered after the last
enter key press will be lost.

User can press the ESC key to exit from this mode and go back to the implicit command mode.

NOTE: If user enters a very long line, then it may wrap to next line in the edit / insert
mode, however when escaping back into the command mode, the cell content wont wrap into
next line. The content will overflow into adjacent cells on the same line/row, if those
adjacent cells dont have any content (even empty string is a content) of their own.

	If the cell containing the long text is scrolled beyond the screen, then the
	overflowing text will not be visible. Contents of a cell including its overflowing
	text will be visible only if that cell is currently in the screen.

If you feel there is a empty string in any field and you want to remove it, use the 'd'
command in the command mode, which will delete any content from the current cell, including
empty string.

## Cell contents and =expressions

One can enter a textual data / string directly into the cell.

However if one wants to enter numeric values or expressions, one requires to prefix them
with = symbol.

Example

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

var and varp

	gives the variance assuming the specified range of cells as representing
	either a sample space (var) or a full population (varp)

stdev,stddev and stdevp,stddevp

	gives the standard deviation of the specified range of cells, by assuming them
	to represent a sample space (stdev,stddev) or a full population (stdevp,stddevp)

## csv file format

The csv file used by this program uses comma [,] to seperate the fields within each row
i.e within each line in the file.

If any field contains the field seperator (i.e ,) with in its content, then the content
is embedded within [`]s and not [']s.

To avoid confusing the program, dont use ` char as part of the spreadsheet contents.

## Misc Notes

If you dont want any exception text to appear on the screen and distract from using
the programs, then you can run the program like below to avoid the screen getting
messed up with stderr contents

	spreadsheetkvc.py 2> /tmp/sskvc.stderr

## History

### 20200823IST1829

Implemented as part of the Gauri Ganesh weekend, to scratch a itch I had with need for a
simple commandline spreadsheet package. And also to explore and think randomly a bit and
have some interesting fun on the way.

Vasudhaiva Kutumbakam (the World is One Family)

