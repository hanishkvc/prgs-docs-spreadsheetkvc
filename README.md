# SpreadSheetKVC

Author: HanishKVC, 2020
Version: v20200903IST2314

spreadsheetkvc is a simple spreadsheet program which runs on the commandline using ncurses and python.

It works with csv file. It allows the saved csv file to be optionally encrypted and inturn load such
encrypted csv files. If encrypted file is manipulated, the program will be able to notice the same,
and inturn stop processing the same, because it uses authenticated encryption concept.

Remember that a cell containing a number or expression|forumula to be evaluated/calculated should
prefix it's contents with '=' ie equal. Else it will be treated as text content cell. The program
will try to make the =expression (which includes numeric also) cells more highlighted compared to
Text cell's to try and make it easy to distinguish between them.

Some of its features are

* Uses curses to show a cell matrix/table in text terminal.

* Loads and stores csv files. User can change the fieldsep and text quote used if required,
  so that one can work with csv files, with different chars for these.

	* the csv files can inturn be secured using authenticated encryption, if desired.

* Allows inline editing of cell contents. If a text cell content occupies multiple lines,
  program will autoscroll if required to allow user to continue editing/entering content,
  within reasonable limits.

	* Overflowing cell's content will be shown in place of adjacent cells, provided
	  those adjacent cells are empty.

* Support evaluation of mathematical expressions which inturn can refer to

	* numeric values

	* contents of other cells.

	* a predefined set of useful supported functions.

	* builtin python functions

		* The user could even specify a cell addresses as arguments to the
		  function. In which case the program will convert the cell address
		  to the value in the specified cell and inturn call the python
		  function.

* Written in python, with source available on github, so that anyone can understand, modify
  and or bugfix as required, to meet their needs ;)

* insertion and deletion of rows or cols, auto adjusts cell addresses refered in expressions,
  where possible. THis includes all cell addresses, i.e including those which have the $-prefix.

	* If refered cell is deleted, then it tags the corresponding cell address reference
	  in the expression with a Err tag. However if user continues to insert or delete other
	  rows/cols, then it will continue to adjust such Err tagged cell addresses, if possible.
	  Do keep this in mind.

* copy/cut-paste operation adjusts cell addresses in =expressions, when pasting into a cell.

	However at same time it also respects $-prefixed fixed celladdress parts notation.
	So such cell address parts which are $-prefixed will not be changed.

	NOTE: If 'P' (capital P) is used for pasting, then it wont adjust the cell addresses.

* supports a readonly view mode, if required.

* adjust to terminal window size changes.

for more details refer to the documentation below.


## Sample usage session

After program is up and running. Press Esc key to be sure that we are in default mode.

Key in the following command to load the help.csv file with basic usage help.

	:help<ENTERKEY>

NOTE: You can exit this help mode by either

	(a) creating a new spreadsheet in memory by using new command i.e

		:new<ENTERKEY>

	(b) Or by loading a existing file into memory

		:l pathto/filename<ENTERKEY>

Key in following command to load a file named filename from path pathto.

	:l pathto/filename<ENTERKEY>

Use arrow keys to move around the cells in the spreadsheet.

To editExisting|insertNew content into a cell, use arrow keys to highlight the required cell.
Press 'i' key to insert new cell content. OR else press 'e' key to edit existing cell content.

	key in the required content into the cell.

	press Enter key to save the changes in the edit buffer into memory and return to default mode.

	press Esc key to discard changes in edit buffer and return back to the default mode.

	NOTE: The editing occurs in the edit mode.

To save changes to the spreadsheet key in the following explicit command.

	:w pathto/filename<ENTERKEY>

Instead if you want to save the spreadsheet into a password protected file, key in the following.

	:pw password pathto/filename<ENTERKEY>

Inturn to load a password protected file key in the following.

	:pl password pathto/filename<ENTERKEY>



## Usage

### command line arguments

The program supports the following commandline arguments

	--help

		program prints info about the commandline arguments supported by it.

	--fieldsep <seperator>

		By default the program uses [;] i.e semicolon as the field seperator of the csv files.
		However the user can change this to a different character by using this argument.

		--fieldsep ','

	--quote <textquote>

		By default program uses ['] i.e single quote, if required, as the field text quote in the
		csv files.  However user can change this to a different character by using this argument.

		--quote '`'

	--startnohelp

		To avoid showing the help dialog on program start.

	--readonly

		The program starts in readonly mode, where user cant modify the loaded spreadsheets.
		That is one cant insert or delete rows/cols. Nor can one edit/insert/cut/delete/paste cells.

		However user can switch to readwrite mode by giving :readwrite explicit command.



### program modes

The program supports the following modes

	default command mode,

	edit/insert mode and

	explicit command mode.


#### default command mode

The program by default runs in the default command mode. In this mode one can press the following
keys for achieving the specified operations.

* i can be used to insert new content in the current cell.

* e can be used to edit the current cell's content.

* c can be used to copy the current cell's content.

* C can be used to cut the current cell's content.

* p can be used to paste a previously copied/cut cell content into current cell. This also adjusts the cell addresses as required.

* P can be used to paste a previously copied/cut cell content into current cell. This pastes the content as is. NOTE: This is capital P.

* D can be used to delete the contents of the current cell.

* : can be used to enter the explicit command mode.

* h or ? can be used to show a help/usage dialog.


#### explicit command mode

This mode is entered by pressing : when in the default command mode.
In this explicit command mode, the user can enter one of the following commands

##### File operations

* w file

	to save the contents of the current spreadsheet into specified file.
	If the file already exists, it asks the user whether to overwrite or not.

	One could also use

		s file

* pw passwd file

	to encrypt and save the file.

	One could also use

		ps passwd file

* l file

	to load the specified spreadsheet.
	If the spreadsheet already in memory has unsaved changes, then it alerts
	the user. So user can decide whether to continue with load and lose changes
	in memory and or abort the load.

* pl passwd file

	to decrypt a previously encrypted file and load it.

* new

	create a new spreadsheet in memory.

##### Insert/Delete operations

* dr [numOfRows]

	used to delete n number of rows starting from current row.
	If numOfRows not specified, it defaults to 1.

* dc [numOfCols]

	used to delete n number of cols starting from current column.
	If numOfCols not specified, it defaults to 1.

* irb [numOfRows]

	insert n rows before current row.
	If numOfRows not specified, it defaults to 1.

* ira [numOfRows]

	insert n rows after current row.
	If numOfRows not specified, it defaults to 1.

* icb [numOfCols]

	insert n columns before current column.
	If numOfCols not specified, it defaults to 1.

* ica [numOfCols]

	insert n columns after current column.
	If numOfCols not specified, it defaults to 1.

##### range operations

* rcopy srcCellAddrRange dstCellAddrRange

	Copy a block of cells starting from srcStartAddress to dstStartAddress

	If srcCellAddrRange doesnt match dstCellAddrRange wrt size,
	then dstCellAddrRange takes precedence in deciding the size.

	The srcBlock will be duplicated as required to fill dstBlock, if the
	srcBlock is smaller than the dstBlock.

		:rcopy A1:A1 A10:B19

		The value in cell A1 will be duplicated across the 20 cells.

		:rcopy A1:B2 A10:B19

		The values in the square of cells at A1 will be duplicated across
		the rectangular 20 cells starting at A10.

		NOTE: Its not necessary that the dstBlockSize is a multiple of
		the srcBlockSize. If not a multiple, then only a partial set of
		values will be copied if that is the case based on the sizes.

	If the srcBlock is larger than the dstBlock, then only that part of the
	srcBlock which can fit in the dstBlock size specified, will be copied.

	src|dstCellAddrRange consists of startAddress:endAddress


* rclear cellAddrRange

	Clear the cells in the given address range.


##### Other operations

* e file (in future)

	to export the current spreadsheet into a file.

* g(oto) CellAddr

	Center the screen to the specified celladdress.

* clear

	clear the contents of the current spreadsheet.

* !shellCmd arguments

	Execute shell command. When shell command finishes/exits, show a input prompt
	so that the user has a chance to see the output of the shell command.

	If the shell command you are running can generate multi page output, better pipe
	it to more or less i.e for example like what is shown in brackets below.

		[:!ps ax | less]

	NOTE: There is no space between ! and the shell command to run.

* help

	show help.csv file. User can either create a new spreadsheet or load an
	existing spreadsheet to exit out of help.

* q

	is used to quit the program.

	All unsaved changes will be lost. Program does warn about this condition and
	gives the user the chance to abort the quit. Remember to save the data by first
	using :w command explicitly, before quiting, if you want all edits to be saved.

The user can enter the command and its arguments and then press enter key to trigger
the command. The user can use backspace to delete the chars to correct mistakes when
entering the command and the arguments.

On pressing the enter key, the specified command will be run and the program will return
back to default command mode.

If Esc key is pressed, the program will discard any command in the edit buffer and then
return back to default command mode.

#### edit/insert mode

On pressing 'i', 'e' from the default command mode, the user can enter this mode.

In this mode the user either enters a new content for the cell and or edits the existing
content of the cell.

As and when the user presses the Enter key, the cell data entered till that point gets
saved into spreadsheet in memory and the program will return back to default command mode.

	This also triggers the logic to remove any white space at the begining and end
	of the current edit buffer, as it gets saved into the cell. So use the currently
	configured quote char at the begining and end of the cell content being edited,
	if you have white space at the begin or end of the current cell content, which
	inturn you want to save as part of the cell.

	The program will auto add text quote character to the end of the cell content,
	if it finds the text quote character at the begining of cell content.

User can discard the changes in the edit buffer and return back to default command mode,
by pressing the Esc key. The original content of the cell is retained in this case.

NOTE: If user enters a very long line, then it may wrap to next line in the edit / insert
mode, however once the program returns back to default command mode, the cell content wont
wrap into next line. In default command mode the cell content will overflow into adjacent
cells on the same line/row, only if those adjacent cells dont have any content (even empty
string is a content) of their own.

If one scrolls the cell containing a long text line too far beyond the currently visible
screen viewport, then the overflowing text may not be visible, beyond a point.

	[DevelNote] THis is to keep the screen refresh relatively fast. User can modify
	the source, to change the amount of scroll allowed while still continuing to show
	the overflowing text from a given cell. One needs to Modify DATACOLSTART_OVERSCAN
	to control this.

If you feel there is a empty string in any field and you want to remove it, use the 'D'
command in the default command mode, which will delete any content from the current cell,
including empty string.

[DevelNote] If gbEnterExitsEditMode is set to False, then pressing enter key in edit mode,
will only save the current edit buffer into a backup buffer. Also program will continue
to remain in edit mode. The user will have to press the Esc key to save any backed-up
edit buffer into spreadsheet in memory and return back to default mode. This was also the
original behaviour of this program previously.


## Cell contents and =expressions

In the edit/insert mode one can enter textual data / string directly into the cell.

However if one wants to enter numeric values or expressions, one requires to prefix them
with = symbol.

Example

	=2

	=5+3/6.8*2**32

	= (5+3)/(6.8*2)**32

The program also allows few predefined functions to be used to operate on the data in the
cells, as mentioned below. These functions needs to be used as part of the =expressions.

Example

	=10-5+sum(B10:C99)

	=cnt(B10:C99)

NOTE that the =expressions are evaluated using pythons eval function. So basic python
expressions can be evaluated as part of =expressions.

NOTE: =expressions should only refer to other =expression cells and not text cells.


## Supported functions for =expressions

### Native functions

sum(CellAddressRange)

	sum the contents of the specified range of cells

cnt(CellAddressRange), even count can be used in place of cnt

	get the count of non empty cells in the specified range of cells.

avg(CellAddressRange), even average can be used in place of avg

	calculate the average of the values in the range of cells. It doesnt consider
	the empty cells.

min(CellAddressRange)

	the minimum value among the specified range of cells.

max(CellAddressRange)

	the maximum value among the specified range of cells.

var(CellAddressRange) and varp(CellAddressRange)

	gives the variance assuming the specified range of cells as representing
	either a sample space (var) or a full population (varp)

stdev(CellAddressRange),
stddev(CellAddressRange), and
stdevp(CellAddressRange),
stddevp(CellAddressRange)

	gives the standard deviation of the specified range of cells, by assuming them
	to represent a sample space (stdev,stddev) or a full population (stdevp,stddevp)

prod(CellAddressRange)

	product of the contents in the specified range of cells.


### Python builtin functions

#### Generic note

The arguments of python functions could be specified either as a

	* numeric value or

	* function which returns a numeric value or

	* cell address (but not a cell address range)


#### python functions

round(number, precision)

	round the specified number to have the specified number of digits following dot.

pow(base, exponent)

	calculate base raised to exponent


int(numeric)

	convert the numeric value to be a integer

float(numeric)

	convert to float value


NOTE: Most of the math functions in python math module are also supported. However to be
useful, they should ideally take only scalar values and return scalar value.


## CellAddress And Ranges

The Cols addressed starting from A to ZZ

The Rows are addressed starting from 1 to ...

So the Cell is addressed as ColRowAddr like for example A1 or D55 or DC999 or so ...

To specify a range of cells use startCellAddress:endCellAddress like

	=A1:A10

	=A1:Z1

	= ZA22:ZZ62

	=sum(AB57:CD60)

	= prod (HO99 : WO100 )

One can prefix the row and or col address part with $. In which case during insertion
and deletion of rows or cols, such addresses are not modified automatically.

	= B12 * $DO34 + ( $A$10 - Z$99)


## csv file format

### General Info

The csv file used by this program uses semicolon [;] to seperate the fields within each row
i.e within each line in the file.

If any field contains the field seperator with in its content, then the field content is
embedded within ['] ie single quotes.

To avoid confusing the program, dont use ' char as part of the spreadsheet contents, other
than for quoting text contents with field seperator in them.

Also if you want to have white space at the beginning and or end of the text contents of a cell,
put the full cell text content within quotes.

NOTE: User can set a different field seperator or quote char from the commandline.

### Encryption support

The program allows the csv file to be encrypted while saving it using a special write
command (pw). And inturn there is a matching pl command to load such encrypted files.

It uses the python cryptography library for the actual low level security algorithms.
In turn it can either use the standardised recipe layer provided by the cryptography
library OR use its own internal recipe layer (this is the default) for doing the actual
encryption and decryption of the encryption protected files.

[DevelNote: Even thou both the internal and cryptography library's recipe layers use
similar concepts, the bitstreams are not compatible between them, so dont intermix
them between saving and loading, as it will fail].

It uses authenticated encrytion mechanism so that any tampering of the encrypted content
can be identified. The encrypted data is stored in the base64 url safe encoding format.

[DevelNote: This also keeps the logic for working with normal and encrypted files almost
the same wrt load and save operations.]

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

NOTE: If user enables the use of external i.e cryptography library's AE recipe, then
the system date and time info of when the encryption was carried out, is stored as
part of its aead logic, where the date time is stored in a unencrypted but base64
encoded format, while at same time the same is accounted as part of the mac maintained
for the encrypted message.


## Misc


### Notes


#### Esc, Esc, Essscccccccc

If a explicit command seems to get stuck or not do anything, remember to try and
press Esc one or more times and see if the program comes back to default command mode.

You will know that you are in default command mode, when you see the program's name
in the top left corner of the terminal (i.e 0,0 cell).


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
on program exit. Such files have a sskvc\_ prefix.

All log and error messages are redirected to /dev/null by default.

If by some chance any exception or error message which should have gone into one of
the above mentioned log files, appears on the screen and thus leading to distraction
wrt using the program, then you can run the program like below to avoid the screen
getting messed up with such messages

	spreadsheetkvc.py 2> /tmp/sskvc.stderr


#### Non csv or csv file with wrong fieldsep

Loading a Non csv file and or a csv file with a different field seperator can lead
to the loaded file setting the program's display to a single column view. So also the
content of the file will be clipped from display perspective. One could run the command

	:ira 25

	or so to allow the overflowing text to be visible.


#### Exit code

If the program exits normally then it returns 0.

If the program is exited normally by the user, by ignoring the warning about unsaved
changes, then it returns 1.


#### Cell Address adjustment and Operations

##### Row(s)/Col(s) Insert/Delete operations

When rows or cols are inserted or deleted, the program tries to adjust cell addresses
if any in =expressions, as required.

NOTE: If the cell address that is explicitly referenced in the =expression, is deleted,
then a Err tag is prefixed to that cell address.

##### Paste operation

If 'paste with cell address adjustment' is triggered (i.e small p), then cell addresses,
if any in the =expression being pasted will be auto adjusted as required.

However if the cell address parts are $-prefixed, then those parts wont be adjusted.

During auto adjusting if the adjusted cell address refers to outside the spreadsheet,
then it will be Err tagged.


### TODO/DONE

[DONE] ncurses cursor is currently not updated/positioned beyond the current cells
begining position. So also the program doesnt allow one to edit anywhere in the middle
of the cell contents, user can only either add to the existing text/content and or
delete the last char using backspace.

	This has been implemented now and the user can edit any part of the cell's
	content. One needs to use the left and right arrow keys to move the text
	cursor around in the edit/insert mode so that one can modify any part of
	the cell content.

[DONE] Allow Multi Row/Col delete.

[DONE] If Row/Col is deleted, then corresponding cell address references should be flagged.

[DONE] Refresh screen draw as part of file load operation.

[DONE] Change delete default mode command from 'd' to 'D', so that user doesnt unknownling trigger it.

[DONE] Show overflowing content of cells beyond what is currently visible, by maintaining a larger
content viewport than the display viewport.

[DONE] Add a View only mode.

[DONE] :help loads help.csv in readonly mode.

helper commands like

	[DONE] rcopy srcRange destRange

	rgennums startCell endCell [startNum] [delta]

	[DONE] rclear

Simple print to text file logic

[DONE] commandline shell

=rows, =cols

[DONE] Allow paste to update cell addresses in the =expression.



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

### 20200827IST2322

Added logic to show text cursor in edit and explicit command mode. While in default/implicit
command mode it doesnt show any cursor, because one cant edit any text buffer in this mode.

On entering edit (including insert) mode, the blinking text cursor is not shown till user
presses some key. Using arrow key will trigger the showing of text cursor, while at same time
ignoring the arrow key press in the edit mode.

NOTE: arrow keys allow moving across cells in default/implicit command mode. While they are
ignored in edit/explicit command mode currently. In future may allow user to edit somewhere
other than the end of the edit buffer, in which case the arrow keys will be used to position
the cursor as required within the edit buffer.

Set dirty flag if required, when entering insert edit mode.

Trap exception from curses, when editing long lines which go beyond the visible screen and
need to dip(wrap around) into next line during editing.

	When using backspace to remove characters from end of such long wrapped line and the
	line comes back to fit with in the current line, there could be few chars belonging
	to the line visible on the screen on the right edge in some cases, as I dont clear
	the full screen in the middle of a edit, while at same time if a new cell cant fully
	fit within the available screen space, then the extra space at right edge is not
	used normally. Such space will get used only during such wrapping long line edits
	and this leads to those chars remaining at right edge of the screen, even after
	backspacing them. However if user inputs new characters to reach that area of the
	screen again, the previous char will get overwritten properly in the screen.

	Parallely it doesnt affect data in any way, and also user should be able to see whats
	happening in a relatively straight way, when it occurs so not forcing a screen refresh
	for now.

#### editAnywhere Branch

Allow editing anywhere in the edit buffer, in the editplus mode i.e edit(inc insert) and
explicit command modes. One can delete characters from anywhere in the current cell as
well as characters to anywhere in the current cell. Rather the logic works on the current
edit buffer, so it could be a cell's edit/insert mode data or explicit command and its args.

TODO: If a long line overflows/wraps into the next line, then the cursor wont be visible,
if it goes into this wrapped around line. i.e edit cursor will be visible only if it is in
the original line itself or at the end of the wrapped around line. Need to update cellcur
to update the row passed to move if required, along with the adjusted new col position also.

TODO: If such long lines wrap beyond the screen space vertically, then curses addstr will
raise a exception. Need to handle this situation appropriately. NOTE that this creates a
problem only in edit mode. In normal mode as line is not allowed to wrap into next line,
this situation doesnt occur.

UPDATE: These todos have been implemented, in a proper way.

### 20200828IST2057

Allow one to modify any location in the edit buffer in editplus mode i.e edit/insert or explicit
command mode. Even if the edit buffer/line overflows into multiple lines it is handled properly.

Logic which protects cell text content with field seperator in it, works in a more controlled
manner by adding the protecting QUOTE only when required wrt the both ends of the text content.

If edit buffer overflows beyond the screen vertically, then the view is scrolled down by few
lines, so that the user can continue to edit the overflowing edit buffer, as it will be with in
the screen now.

Merge editAnywhere branch into master branch, as the edit anywhere in the edit buffer related
logic has been handled reasonably now. This also brings in few of the other updates/cleanups/
fixes mentioned before into the main branch now.

### 20200829IST1619

Added a new secFromPrimitives branch which implements a form of authenticated encryption on its
own using the primitives in the cryptography.hazmat package, rather than depending on cryptograpy
fernet recipe.

Spreadsheet package updated to use this new internal implementation as part of its password
protected save (pw) and load (pl) commands, by default. User can change bInternalEncDec var to
switch between internal and fernet logics.

NOTE: The internal and external AE implementations are not bitstream compatible with one another,
even thou both are potentially following similar concept to some extent. So a password protected
file saved using one ae implementation cant be loaded by the other implementation.

Merge secFromPrimitives into master branch

Add a Basic HelpDialog which is shown on startup.

### 20200830IST1537

Let program use full text screen, i.e even a partial cell column is now shown at the right edge
of screen. Useful on small terminal screens like 80x24 or so...

Handle exception during cell data printing so that user still can see and trigger explicit
commands if required.

Adapt to terminal window size changes automatically.

Clear command to clear current spread sheet.

Show help dialogs by pressing h or ? in default mode or by giving :help explicit command.

Updated dr and dc explicit commands to delete n rows/cols.

If the deleted rows or cols is explicitly referenced in a =expression as a celladdress reference,
then it will be tagged with a Err tag and that address will not be adjusted.

	TODO: In future check if the explicit cell address reference is part of a range and if so
	see if it can be adjusted to a shorter range. However the current logic is also sufficient
	at a basic level to alert the user that things have changed after a delete and the user
	should adjust the affected =expressions as required by them.

### 20200831IST1347

Changed the text quoting char from ` to ' to avoid confusion to end users.

Strip white space from begin and end of edit buffer before saving into cell. So user will need to
put the full cell content inside quotes,  to protect such white space, if required.

THis was started on the Gowri/Ganesh festival weekend and now being updated/cleanedup in the Onam
festival weekend.

### 20200901IST0234 - OnamRelease

Now one can call builtin python functions as part of =expressions.

Updated to a new \_nvalue and associated logic, which is more flexible and allows =expressions to be
more complex, including calling functions within functions i.e a function's argument can inturn be
a function call. Also it evaluates the parts of a =expression in a more structured way. Also it no
longer forces the result of the evaluation to be a float.


	This allows round and int python functions to be used as part of =expressions in a more
	flexible manner.

Added new parse module and the same is used for many parts of the parsing logic of the program now.
This is a cleaner, simpler and at same time flexible logic.

Base and Line key logic moved into sec module.

Functions logic moved into funcs module.

Differentiate between text and numeric(=expression) cells.

Default mode delete command changed from 'd' to 'D' key press.

Alert user, if trying to load a file, while unsaved changes are in memory.

Clear screen when loading a file.

Make sure that not just a text cell, but also a =expression cell blocks overflowing text from
adjacent cell that is towards it's left.

Have a larger data viewport compared to display viewport, so that any overflowing text from
adjacent cells which are no longer in the display viewport is still displayed. However to keep
the processing load of drawing of cell matrix efficient, the data viewport is bigger to display
viewport by 20 cells to the left side (because cells on left is what can overflow into current
or more cells). User can modify this if required by updating the source. Power To SOURCE ;)

Avoid exception cornercase by converting char to int, rather than int to char. Because getch
can send crazy value if a terminal window size change occurs.

Set terminal title when a file is successfully loaded.

readonly, readwrite explicit commands. In readonly mode one cant change the spreadsheet contents.
Also readonly commandline option.


### 20200902IST0147 - OnamRelease

:help explicit command loads help.csv file in readonly mode. This uses the new load_help logic.
Previously it was loading the helpdlg.

Cell content delete command sets dirty flag, if there was content to delete.

Added the explicit command new, to create a new spreadsheet in memory, this allows the user to
come out of the help mode. A user could also load a existing file to come out of the help mode.

Adjust numeric and text cell attributes based on curses attributes available.

Reposition to A1 cell, when file is loaded.

s and ps as aliases to w and pw explicit commands.

Pressing enter key in edit mode, saves edit buffer and returns to default command mode.

Avoid stray/unwanted newline and fieldsep wrt load and save file logics.

celladdr related get_token moved to parsekvc and updated to use its routines.

Fix some oversights.

TOdays updates done in between watching a bunch of good malayalam movies Savaari, Chalakkudykkaran Changathy
and Ayalum Njanum Thammil, among others.

### 20200903IST1235 - OnamRelease

parsing helper routines made more powerful and flexible while still keeping it simpler. Inturn get_celladdr
has been simplified while parallely being better at its job.

Handle request from user to keep cell address parts fixed by using $ prefix for such parts.

	While copy/pasting =expressions, the $-prefixed fixed address request is respected.
	However during row/col insertion/deletion operations, all cell addresses are auto-adjusted in existing =expressions.

Added a explicit command (:!) to execute shell commands.

So while entering text content to a cell, which needs to be protected with quotes (bcas whitespace at begin
or end and or bcas there is fieldsep in the content), user can just add quote at the beginining, while program
will automatically add it to the end.

paste operation adjusts =expression cell addresses as required.

### 20200904IST1018 - OnamRelease

insert mode saves the original content if any into backupEdit, so if user doesnt commit his new cell content by pressing enter key,
ie if the user presses Esc key to discard his new edit, the program will revert the cell to its original content.

Handle exiting editMode with empty edit buffer and or edit buffer with a single single qoute.

FIx a oversight with hardcoding of old text quote char in the save_file logic.

'P' pastes data without adjusting cell addresses.

:new resets display viewport to A1

If :g celladdr has celladdr beyond spreadsheet, adjust to nearest valid cell.

Filter python functions by default, so only whitelisted functions can be used in =expressions.

Fixed possible corner cases with empty/no arg for function and empty cell content copy situations.

:rcopy which copies a block along with adjusting of the cell addresses in =expressions, if any, logic implemented.

:rcopyasis which copies a block of cells as is, ie dont change cell addresses in =expressions, implemented.

:rclear clears the contents of the cells specified.




## Vasudhaiva Kutumbakam (the World is One Family)

If you find the program useful, and inturn if you can afford to donate, donating to a local good cause near you, would help those in need.

