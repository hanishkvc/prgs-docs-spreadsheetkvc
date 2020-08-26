# SpreadSheetKVC

Author: HanishKVC, 2020
Version: v20200825IST2235

spreadsheetkvc is a simple spreadsheet program which runs on the commandline using ncurses and python.

It works with a slightly modified form of csv file.

It allows the saved csv file to be encrypted and inturn load such encrypted csv files.

## Usage

### command line arguments

The program supports the following commandline arguments

	--help

		program prints info about the commandline arguments supported by it.

	--fieldsep <seperator>

		By default the program uses ',' i.e comma as the field seperator of the csv files.
		However the user can change this to a different character by using this argument.

		--fieldsep ';'



### program modes

The program supports the following modes

	command mode,

	edit/insert mode and

	explicit command mode.


#### command mode (implicit)

The program by default runs in the implicit command mode. In this mode one can press the following
keys for achieving the specified operations.

* i can be used to insert new content in the current cell.

* e can be used to edit the current cell's content.

* c can be used to copy the current cell's content.

* C can be used to cut the current cell's content.

* p can be used to paste a previously copied/cut cell content into current cell.

* d can be used to delete the contents of the current cell.

* : can be used to enter the explicit command mode.


#### explicit command mode

This mode is entered by pressing : when in the default/implicit command mode.
In this explicit command mode, the user can enter one of the following commands

* w file

	to save the contents of the current spreadsheet into specified file.
	If the file already exists, it asks the user whether to overwrite or not.

* pw passwd file

	to encrypt and save the file.

* l file

	to load the specified spreadsheet.

* pl passwd file

	to decrypt a previously encrypted file and load it.

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

* g(oto) CellAddr

	Center the screen to the specified celladdress.

* q

	is used to quit the program.

	All unsaved changes will be lost. Program does warn about this condition and
	gives the user the chance to abort the quit. Remember to save the data by first
	using :w command explicitly, before quiting, if you want all edits to be saved.

The user can enter the command and its arguments and then press enter key to trigger
the command. The user can use backspace to delete the chars to correct mistakes when
entering the command and the arguments.

On pressing the enter key, the specified command will be run and the program reverts
back to implicit command mode.

#### edit/insert mode

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

NOTE: =expressions can only refer to other =expression cells and not text cells.


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

prod

	product of the contents in the specified range of cells.


## csv file format

### General Info
The csv file used by this program uses comma [,] to seperate the fields within each row
i.e within each line in the file.

If any field contains the field seperator (i.e ,) with in its content, then the content
is embedded within [`]s and not [']s.

To avoid confusing the program, dont use ` char as part of the spreadsheet contents.

User can set a different field seperator from the commandline.

### Encryption support

The program allows the csv file to be encrypted while saving it using a special write
command (pw). And inturn there is a matching pl command to load such encrypted files.

It uses the python cryptography library to do the actual encryption and decryption
logic and inturn uses its standardised recipe layer for the actual encrypt and decrypt
logic, for now. So also saves the encrypted data in the base64 encoded format. This
also keeps the logic for working with normal and encrypted files almost the same wrt
load and save operations.

THere are two passwords that the program uses wrt each file

	P1. A user level password, this is specific to a user and shared for all the
	encrypted files operated by the user. This is stored in users home folder at

		~/.config/spreadsheetkvc/userpass

		If this file is missing, then a default password is used. Not using
		user level password is also the simplest way to share encrypted files
		with others.

		If a user makes use of this, then they should remember to keep its
		access restricted to the user and not share to group or all.

	P2. The file password, this is specific to each file that is encrypted.
	This is specified as part of the pw and pl commands.

If the user is sharing encrypted files with others, then dont specify the user level
password. Only use the file specific password, unless you dont mind sharing your user
level password of this program with others.

A random salt is also used each time a file is saved. This inturn is embedded within
the saved encrypted file.


## Misc


### Notes


#### Esc, Esc, Essscccccccc

If a explicit command seems to get stuck or not do anything, remember to try and
press Esc few times and see that it comes back to default/implicit command mode.

You will know that you are in default/implicit command mode, when you see the
program's name in the top left corner of the terminal (i.e 0,0 cell).


#### =expressions and None

Do keep in mind that =expressions which allow numeric evaluation of the specified
expression in a given cell, expects any cell references|addresses used in them to
inturn (i.e those referenced cells) also contain =expressions and not plain text
data (even if they are numbers). If not the result will be a None.

So if you get a None instead of a numeric value which you were expecting, then
cross check that all cells refered by that cell or any other cell indirectly
referenced through a chain of =expressions, all contain =expressions, even for
simple numeric values like say a number i.e represent it has =number (ex =10).


#### log files, stderr, ...

By default any exception data is written to a named temp file, which is not deleted
on program exit.

All log and error messages are redirected to /dev/null by default.

If by some chance any exception or error message which should have gone into one of
the above mentioned log files, appears on the screen and thus leading to distraction
wrt using the program, then you can run the program like below to avoid the screen
getting messed up with such messages

	spreadsheetkvc.py 2> /tmp/sskvc.stderr


#### Non csv or csv file with wrong fieldsep

Loading a Non csv file and or a csv file with a different field seperator will lead
to the loaded file setting the program's display to a single column view. So also the
content of the file will be clipped from display perspective. One could run the command

	:ira 25

	or so to allow the overflowing text to be visible.


#### Exit code

If the program exits normally then it returns 0.

If the program is exited normally by the user, by ignoring the warning about unsaved
changes, then it returns 1.


### TODO

ncurses cursor is currently not updated/positioned beyond the current cells begining
position. So also the program doesnt allow one to edit anywhere in the middle of the
cell contents, user can only either add to the existing text/content and or delete
the last char using backspace.


## History

### 20200823IST1829

Implemented as part of the Gauri Ganesh weekend, to scratch a itch I had with need for a
simple commandline spreadsheet package, compounded on top by the fact that libreoffice
is a slippery slop trying to run on chromebooks(chrome os). Then there was the need to
storing things securely on the disk, when required. And as mostly always also to explore
and think randomly and or something different for a bit and have some interesting fun
on the way.

A usable at a basic level (nothing fancy, yet;) commandline spreadsheet logic has been
implemented to some extent.

### 20200825IST1220

Make the program more forgiving, by alerting before overwriting as well as before quiting
without saving changes. Also remove implicit command mode Q quiting. Now user has to enter
:q explicit command, to quit the program.

Automatically redirect exception messages to a named temp file.

Add en|de-cryption support for files, so that they can be saved/stored in a secure manner.

Add support for specifying csv fieldseperator from the commandline.

### 20200826IST2304

Added basic logic to adjust cell addresses in =expressions, when rows or cols are added
and or deleted. This is a quick go at it, in the middle of doing other things, and not
tested fully (not that other things have been tested fully ;-), but at a basic level it
should potentially work to some extent if not more.

NOTE: Even thou the token logic checks for $ as part of cell address, it isnt handled in
any other place and will fail, if used.

NOTE: Paste in a copy-cut/paste flow doesnt adjust any cell addresses.

NOTE: While deleting rows or cols, the deleted row or col's address refered in other cells,
is not touched/modified. However subsequent row/col's addresses are udpated suitably.

Set dirty flag in more places, so that program doesnt just silently quit, if user has not
written any possible|potential changes to a file.

## Vasudhaiva Kutumbakam (the World is One Family)

