# SpreadSheetKVC

Author: HanishKVC, 2020
Version: v20200909IST1947

spreadsheetkvc is a spreadsheet program which runs on the commandline using ncurses and python.

It works with csv file. It allows the saved csv file to be optionally encrypted and inturn load such
encrypted csv files. If encrypted file is manipulated, the program will be able to notice the same,
and inturn stop processing the same, because it uses authenticated encryption concept.

Text and Numeric values can be entered into cells as is, unless one wants a numeric value to be
treated as a text, in which case quote it. [One needs to be in edit mode by pressing i or e to
add or edit cell contents].

While expressions/formulas to be evaluated using a combination of values, contents of other cells
and or supported functions, need to be prefixed with = symbol. These are called =expression.

The program will try to make the =expression and numeric cells highlighted compared to Text cell's
to try and make it easy to distinguish between them.


## Features

Some of its features are

* Uses curses to show a visual matrix/table of cells in text terminal.

* Loads and stores csv files. User can change the fieldsep and text quote used if required,
  so that one can work with csv files, with different chars for these.

	* the csv files can inturn be secured using authenticated encryption, if desired.

* Allows inline editing of cell contents. If a text cell content occupies multiple lines,
  program will autoscroll if required to allow user to continue editing/entering content,
  within reasonable limits.

	* [Outside of edit mode, ie default mode] Overflowing cell's content will be shown
	  in place of adjacent cells, provided those adjacent cells are empty.

* Support evaluation of mathematical expressions which inturn can refer to

	* numeric values

	* contents of other cells.

	* a predefined set of useful supported functions.

	* builtin python functions

		* The user can specify cell addresses as arguments to the function.
		  In which case the program will convert the cell address to the
		  value in the specified cell and inturn call the python function.

* The program follows a windowed lazy/defered evaluation with caching strategy for the cells.
  This ensures that large spreadsheets with heavy calculations can be displayed relatively
  quickly without much calculation overhead, in general.

* Written in python, with source available on github, so that anyone can understand, modify|extend
  and or bugfix as required, to meet their needs ;) This also allows arbitrary precision integer
  operations.

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

* the program tries to be simple and sane wrt fieldsep and textquote.

	If fieldsep in cell content, auto protect with text quoting of cell content.

	If text quote at begin or end of cell content, auto insert at the other end, if missing.

	If text quote some where in the middle of cell content, replace with a placeholder char.

* Any Cells having looping in their =expression calculations (backto themselves directly and or
  through a chain of cells) and or involve very very long (1000s) cell-to-cell dependency depth chaining
  will be identified and result in None result or ErrTagging. ErrTagging ensures that those cells
  dont get accounted in subsequent recalculations and thus dont bog down the program.

  User will be able to see if a cell is error tagged, because same is shown as part of cell content.

  Program uses a decent enough effort optimistic multipass evaluation logic with valid result caching
  to try and handle very very deep calc chaining in managable parts in a discrete sliding manner,
  while still allowing looping to be trapped.

* Uses the sparse dictionary data structure to store the cells in memory. So irrespective of the
  size (in terms of number of rows and cols) of the spreadsheet, in memory it occupies only as much
  space as required for cells with contents in them.

	From within the program one could use one of the :xrows or xcols or :irb or :ira or :icb or
	:ica commands to increase the size of the spreadsheet, as needed. Look further down for details.

	NOTE: sparse data structure is useful for having huge spreadsheets with good number of empty
	cells inbetween and not necessarily huge spreadsheets with most of the cells filled up ;)

* support range operations (rcmds) which allow manipulating multiple cells easily using simple commands.

	One can even mark cells so that they dont have to remember the cell address, as well as program
	supports infering destination cell address range from source address range.

* Some additional features like

	* supports a readonly view mode, if required.

	* auto-adjust to terminal window size changes.

	* tab-completion of

		* file path names for load and save operations.

		* predefined parts of the :commands (explicit commands) supported by the program.

			* suggest hint for the command parts that user has to specify.

	* normal or raw display mode.

	* global align left, right or default.

	* global format config for display purposes

		* float precision.

		* integer to float conversion.

		* pre-cooked neat and raw modes

	* search and if required replace support.

	* support markers including implicit ones (@mCUR, @mEND).

	* optional c based loading and cell addrs (including ranges) parsing for spreadsheets with millions of cells with contents.

* Edit (Cut/Paste/Delete/Modify a cell) and Insert/Delete (rows/cols) operations trigger cell recalculations
  only for cells which are directly or indirectly affected by it (propogate the changes across dependent cells).

	Note: the actual recalculation occurs when a affected cell or its dependents become visible. While
	the =expressions are adjusted wrt cell addresses if any in them, as well as depedency lists are
	updated immidiately.

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

	NOTE: program will prompt for user file password once again, to ensure that user doesnt use/key-in a wrong password by mistake.

Inturn to load a password protected file key in the following.

	:pl password pathto/filename<ENTERKEY>



## Usage

### Requirements

The program requires python3, ncurses or equivalent and python-cryptography.

It can run in the terminals of a linux/unix/macosx system. And so also in the linux terminal provided by windows subsystem for linux.

If one wants to speed up the loading and some aspects of working with spreadsheets with millions of filled cells in them by some extent,
then one needs to run sudo python setup.py install to install the c helper extension module.


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

	--creadonly

		The program starts in readonly mode, where user cant modify the loaded spreadsheets.
		That is one cant insert or delete rows/cols. Nor can one edit/insert/cut/delete/paste cells.

		However user can switch to readwrite mode by giving :creadwrite explicit command.

	--calldepth <depth>

		Set the maximum call depth | cell chaining allowed by program to <depth>.

		Default value is 1000. This is not a end user option. It is more for some one developing and
		or debugging the program to trigger and or manipulate things.

	--flypython

		Allow bit more varied set of python expressions to be stored in cells and inturn
		run those python expressions by refering to those cells from other cells

	--usecolor

		Enable color mode of the program. In this mode the program will show alternate
		rows in two different background colors, so that the user can easily identify all
		cells (and their contents) on a given row.

		By default color mode is not enabled, user needs to use this argument.



## program modes

The program supports the following modes

	default command mode,

	edit/insert mode and

	explicit command mode.


### default command mode

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


### explicit command mode

This mode is entered by pressing : when in the default command mode.
In this explicit command mode, the user can enter one of the commands mentioned below.

NOTE: if the program doesnt seem to do anything after you have entered a command and its arguments and inturn pressed <enter> key,
then verify that the arguments given to the command are proper or not. If there is a mistake in the argument, correct it by using
arrow keys and then backspace to remove the wrong characters and keying in the new correct characters. For few commands, the program
will not continue if the arguments are not proper. User can always press <Esc> key and go back to default mode.

##### Tab completion support available for

* file path names for load and save commands (for both normal and password version)

	If you are happy with the dir name suggested by tab completion, then add a '/' at the end so that
	the program will start providing suggestions for the sub directories and or files below it.

* predefined/fixed parts of the commands explained below.

	If you are happy/ok with the full part of the tab completion suggestion you require to add a space to the end,
	so that program will provide completion suggestion for any subsequent predefined parts of the command.

	It also provides hints for the parts of the command that user has to specify (this is done for most commands).

If you are happy with only a part of a suggestion or want to check if there are any matching suggestions for a given
prefix, then enter that prefix and or trim the current suggestion to the prefix you have in mind and then press tab
to see if the program will complete it with some suggestions of its own.

	If there are no matching suggestions the program will either let the user entered part be as it is, or may
	error tag the non-existing part in case of file paths.

If there are multiple matching suggestions, then if user presses tab without editing the suggestion provided by the program,
the program will cycle throught all the suggestions.



#### File operations

* w file

	to save the contents of the current spreadsheet into specified file.
	If the file already exists, it asks the user whether to overwrite or not.

	One could also use

		s file

* pw passwd file

	to encrypt and save the file.

	One could also use

		ps passwd file

	NOTE: program will prompt for user file password once again, to ensure that user
	doesnt use/key-in a wrong password by mistake.

* l file

	to load the specified spreadsheet.
	If the spreadsheet already in memory has unsaved changes, then it alerts
	the user. So user can decide whether to continue with load and lose changes
	in memory and or abort the load.

* pl passwd file

	to decrypt a previously encrypted file and load it.

* new

	create a new spreadsheet in memory.


NOTE: To avoid user overwriting/modifying files unknowingly, the program requires the user
to explicitly specify the file to write to.


#### Insert/Delete operations

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

[devel note] Delete operation is disruptive to dependent cells compared to insert.

#### range operations (rcmds)

* rcopy srcCellAddrRange dstCellAddrRange or rcopy srcCellAddrRange dstCellStartAddr

	Copy a block of cells starting from srcStartAddress to dstStartAddress.
	In the process convert any cell addresses in the copied =expressions,
	as required.

	If srcCellAddrRange doesnt match dstCellAddrRange wrt size,
	then dstCellAddrRange takes precedence in deciding the size.

	If only destination start cell address is given and not the destination end
	cell address, then end cell address will be infered from the source addr range.

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

* rcopyasis srcCellAddrRange dstCellAddrRange or rcopyasis srcCellAddrRange dstCellStartAddr

	This is similar to :rcopy command mentioned above. The main difference is that
	this doesnt modify the cell addresses in the =expressions that are copied.


* rclear cellAddrRange

	Clear the cells in the given address range.

* rclearerr cellAddrRange

	Clear Error tag prefix in the cells in the given address range. This allows such cells
	to be evaluated again.

* rgennums cellAddrRange [start] [delta]

	Generate numbers starting from start (default 1) and incrementing|decrementing (default 1)
	with delta and use it to fill the cells specified in the cellAddrRange.

	Ex: Mutliplication table for 11

		:rgennums A1:A10 11 11

	Ex: Multiplication table of 11, in reverse

		:rgennums B1:B10 110 -11

	Ex: Generate table id starting from 1

		:rgennums C1:C10

	NOTE: Delta can be either positive or negative.

* rsearch cellAddrRange StringToSearch

	Cycles the user through all the cells which contain the string given by the user.

	NOTE: Use single quotes around the string, if you want to search for something containing spaces in them.

	NOTE: Abort a search by pressing <ctrl>+<c> key combination.

* rsearchreplace cellAddrRange StringToSearch ReplaceWithNewString

	Similar to rsearch, but additionally allow the searched string to be replaced with the new string given.


NOTE: In these range operations (rcmds), one can use markers in place of cell addresses, if required.

The marker is specified using the syntax @mMarkerId

	Ex: If marker m1 corresponds to B10 then instead of typing

		:rgennums B10:D20

		one could use

		:rgennums @m1:D20

#### Markers

Markers allow one to identify cell address by using marker ids. THis allows one to work with :r range operations
in a easy | user freindly way.

* mshow

	Show the currently set markers

* mclear

	Clear the current set of markers

* mMarkerId		(OR m MarkerId)

	Set the marker MarkerId to point to current cell. MarkerIds can be AlphaNumeric.

	The AlphaNumeric should ideally only include the characters in a-z, A-Z and 0-9

		Example :m1 :ma :mZZ :mstart and so on

		THese are also equally valid commands to set markers :m 1 :m a :m ZZ :m start and so on

	NOTE: tab-completion only hints the m MarkerId notation.

When using a marker in place of a cell address in any of the range operations, one needs to prefix the MarkerId with @m i.e @mMarkerId

##### Implicit markers

The program provides the following implicit MarkerIds

@mEND - this points to the last cell in the spreadsheet implicitly.

	Useful for :rsearch or :rsearchcopy operation among others

@mCUR - this points to the currently in-focus cell in the spreadsheet implicitly.

	Useful in :rcopy or :rcopyasis or :rgennums and so on

NOTE: User can override these if required, else it will point to a cell determined at the time of use, as defined above.

NOTE: the implicit markers are capitalised so that end user can use lower case or mixed case marker ids with similar name,
without overriding one another, if possible.


#### Config commands

##### Read Write Mode

* cro|creadonly

	switch program to readonly mode, so that user cant modify the contents of the spreadsheet.

* crw|creadwrite

	switch program to readwrite mode, so that user can modify the spreadsheet. This is the default mode.

##### FieldSeperator and TextQuote

* cfs|cfieldsep theFieldSepChar

	set the fieldsep for the csv file.

	Ex: cfs ' (for setting single quote as fieldsep)

	Ex: cfs ; (for setting semicolon as fieldsep)

	Ex: cfs \\t (for setting tab as fieldsep)

	NOTE: If it so happens that the newly defined fieldsep is part of some cell content, then the program
	will autoquote the corresponding content, if it is not already quoted, when saving to file.

* ctq|ctextquote theTextQuoteChar

	set the text quote for the csv file.

	All instance of the new textquote char already in text cells, will get replaced by alt2inbtwquote char [i.e _].

	All instances of old textquote char in text cells, will get replaced by the new textquote.

NOTE: Ensure that fieldsep, textquote and alt2inbtwquote are unique compared to one another.

##### Global Alignment

* calign left

	Align the cell content to the left. Any content that doesnt fit within the cell will overflow into the empty cells on the right.

* calign right

	Align the cell content to the right. Any content that doesnt fit within the cell will overflow into the empty cells on the left.

* calign default (this is the default alignment mode of program)

	Align text cells to left. Align numbers which fit within the cell to right else align to left.
	Any content that doesnt fit within the cell will overflow into empty cells on the right.

##### Global formatting

* cformat iffloat \<floatPrecision|None>

	Configure the precision to be used when showing floating point numbers

	If floatPrecision is provided the precision to be used when showing floating point number is set.

	If None is provided, then floating point numbers are shown as is with no specific display formatting.

	Some examples

		:cformat iffloat 2

		:cformat iffloat None

  User can also trigger the same from with in a spreadsheet by using the following in a cell

	=config(cformat, iffloat, floatPrecision)


  NOTE: Results of any cell with =round() function will inturn be processed according to the cformat iffloat rule, when showing it on the screen.
  However for calculations which depend on such a cell, the results of round function will be used directly.


* cformat number2float \<yes|no>

	Treat all numbers as floats.


* cformat neat OR cformat raw

	neat enables number2float conversion and floating point precision of 2, from displaying numbers perspective.

	raw shows number cell contents as is by disabling number2float conversion and floating point precision adjustment.


NOTE: if using =config(cformat... in a spreadsheet, to have maximum chance of getting triggered, put it in the cells A1 or A2 or B1 or B2

NOTE: the effects of the last cformat formatting rule will persist across files irrespective of if it was triggered explicitly by the user
using :cformat explicit command and or it got set by being part a =config(cformat... expression in one of the spreadsheet that was loaded.

	This effect is purely from a what is shown perspective. And doesnt effect any calculations or so.


#### xtra operations

* xrecalc

	Force clear the calculated results cache, so that all cells get recalculated, as they become visible
	either directly and or indirectly through some other visible cell. As and when a given cell or a some
	other cell which depends on it becomes visible, the cell will be recalculated.

	If you feel that the program has messed up with its recacl limiting optimisations and inturn has not
	recalculated a cell, which it should have. You can use this command to force the program to recalculate
	all cells.

* xrows <numOfRows>

	Use to increase the number of rows in the spreadsheet to the new number specified.

	NOTE: You cant reduce the number of rows using xrows, you need to use dr for it.

* xcols <numOfCols>

	Use to increase the number of cols in the spreadsheet to the new number specified.

	NOTE: You cant reduce the number of cols using xcols, you need to use dc for it.

* xviewraw

	Display the contents of the cell as is, i.e nothing is evaluated, the expressions are shown as is.

* xviewnormal

	This is the normal view, in which the cell contents are evaluated and the results shown to the user.


#### Other operations

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



### edit/insert mode

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

	The program will auto add text quote character to the begin or end of cell content,
	if it finds the text quote character only at the other end of cell content.

	If text quote found somewhere inbetween the cell content, it gets replaced with
	a place holder.

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

In the edit/insert mode one can enter textual or numeric value directly into the cell.

While entering expressions to be evaluated, one requires to prefix them with = symbol.

Example

	A text

	' Another text with space in front'

	123456

	=2

	=5+3/6.8*2**32

	= (5+3)/(6.8*2)**32

	=10-5+sum(B10:C99)

NOTE: If one wants numeric content or =expression to be interpreted as text content,
then one requires to place such numeric or =expression content within the configured
quotes.


### Interpretation of cell contents

If no data (which also includes empty string) then return 0 (where numeric value expected,
else return "" i.e empty string).

If starts with =,  then do the internal =expression evaluation of same.

if starts with numeric or starts with + or - then python eval it for a numeric.

	If user wants to treat it has text, then they need to add textquote.

	No need to prefix numbers with =. (applies for some simple expressions also)

If none of above, return 0 where numeric value expected, else return as is as a string.

	Anything starting with alphabet or space or textquote or anything not matching
	above is treated as text.


### =expressions

These are expressions/formulas which allows one to operate on existing data in the cells
and inturn infer and or generate new data from it.

The =expressions are evaluated using pythons eval function. So basic python arithematic
expressions can be evaluated as part of =expressions.

The program also allows few predefined functions to be used as part of the =expressions.
This allows the user to operate on the data in the cells suitably. The supported functions
are mentioned later in this document.

Example

	=10-5+sum(B10:C99)

	=cnt(B10:C99)

	= 99/(100 + Zz99) * sum(A1:B10)

As can be noticed in the above examples, one can refer to values in other cells directly
by specifying the corresponding cell's address.

=expressions should only refer to other =expression or numeric cells and not text cells.
If a text cell is referenced where numeric value is required, it will be treated as
containing the value 0.


#### evaluation

The program follows a windowed lazy/defered evaluation with caching strategy for the cells.
Prg defers cell [re]evaluation, till the cell becomes visible or some other cell which depends
on it either directly or indirectly becomes visible. This ensures that large spreadsheets
with heavy calculations involving very very long chaining across cells load relatively fast
and can be edited normally in most cases.

Only when cells with heavy chaining become visible, the program will pause to do the calculations
required and inturn show its results.

THe cell evaluation with in the display window, is done in a row major fashion. The calculated
results are cached and reused, when calculating other cells. For optimal performance, especially
for =expressions which have DEEP cell chaining dependencies ideally have cell dependencies such
that they depend on

	cells to their left on the same row and or any cell in the rows to its top.

	This suggestion is mainly for calculations involving very very long chaining of cells.
	FOr normal calculations, the cells could be anywhere in the spreadsheet.

When cell contents are updated/modified by the user, the program clears the cache, and repeats
the windowed defered evaluation with caching as explained above again.

The program maintains a reverse dependency list for each cell, so that when user edits any cell,
only related cells' caches are cleared and thus inturn cells needing reevaluation is limited to
the cell itself and its dependent cells.

NOTE: If the user suspects that the recalculation optimisation logic of the program is at fault,
they can run the :xrecalc command which will clear the calc cache of all cells, so they all get
recalculated as and when required.


#### Looping and Deep chaining.

If =expression in a cell refers back to itself either directly and or through other cell(s) in
the chain of calculations required to find the cell's value, then it is considered to be looped.

The program will trap such invalid looping and Err tag the contents of all cells involved in the
calculation, whose value is impacted by looping. This allows the user to see what and all cells
where involved in that looping. It also allows the program to continue with evaluation of the
other cells, while ignoring these err tagged cells.

The program will also flag the calc loop error tag, for cells whose =expression involves chaining
of cells which refer to one another such that the chain length extends to thousands of cells. IE
where one cell refers to another cell, and that another cell refers to some other cell and so on.

	NOTE: A cell directly refering to say 100 or even 500 cells for that matter is not a issue.
	Similarly using Cell Address Ranges like say sum(A1:ZZ1024) in itself is also not deep cell
	chaining, rather it corresponds to a cell chaining depth of only 1. If any of those cells
	inturn depend on other cells for their calculations, and those other cells inturn dependent
	on even more cells for their value and so on and on and on to a very very deep extent, that
	is when a very very deep cell calculation chaining occurs and only then will this trigger.

	IE cells chain from one cell to another cell and from that another cell to some other cell
	and so on to very very deep extents.

	i.e CellB4[=B1+B2+B3] or CellB4[=sum(B1:ZZ1024]

		is a call depth of only 1

	while CellB4[=B3] CellB3[=B2] CellB2[=B1] CellB1[=10]

		leads to a call depth of 3 as far as CellB4 is concerned.

User will be able to see if a cell is error tagged, because same is shown as part of cell content.
Once user has fixed the looping in calculation and or better organised things. User can run

	:rclearerr cellAddrRange

to clear err tags from the cells in the specified range. So that the program will start accounting
those cells again.

Prg uses a decent enough effort multipass evaluation logic with valid result caching to try and handle
very very deep calc chaining, where the solution is built part by part in small managable chunks, over
multiple passes.

[DevelNote]

If CALCLOOPMAX is reduced to 200 or so, then looping in =expressions and or very long cell-to-cell
dependency chaining will be identified (in this case if the depth crosses 200 or so) and all cells
involved in the chain will also get error tagged.

However by default program is setup to not trigger this in the normal case (by setting CALCLOOPMAX
to a very high value of 1000). Instead the program allows python recursion error to trigger and break
the calculation if it is sufficiently deep to trigger the same. In this case chances are few of the
involved cells' values would have got calculated. Even otherwise, it will continue with calculating
the remaining cells. THis ensures that over a series of passes, the cells starting from the origin of
the calc chain and slowly building up towards the end of the calc chain get calculated and cached.
At each pass all cells with in the recursion limit depth to the last set of calculated cells in the
chain, get calculated. Thus the chain gets resolved automatically through managable parts / blocks,
in a discrete sliding manner from the start to the end of the chain, over a series of passes.

THis allows very deep chains (well most of them any way, in a reasonable time and definitely all,
if one is willing to wait for sufficient time) to be calculated while still trapping loops.


## Supported functions for =expressions

### Native functions

sum(CellAddressRange)

	sum the contents of the specified range of cells

cnt(CellAddressRange), even count can be used in place of cnt

	get the count of non empty cells in the specified range of cells.

avg(CellAddressRange), even average can be used in place of avg

	calculate the average of the values in the range of cells. It doesnt consider
	the empty cells. However text cell if any will be accounted with a val of 0.

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

	* cell address (its numeric value will be used) or

	* cell address range (converted to a list of numeric values belonging to the cells)

		A function argument which is a cell address range, shouldnt contain any other operations.
		While other arguments of the function could even be expressions, which get evaluated to form the final argument value.

		cell address range can be used, provided the underlying python function accepts a list of values.


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
useful, they should ideally take or return only scalar values and or simple 1d lists.
And as mentioned before these scalar or 1d list values could be either direct or from cells
and or output of other functions.


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
than for

	quoting text contents with field seperator in them. AND OR

	if you want to have white space at the beginning and or end of the text contents
	of a cell, put the full cell text content within quotes.

Text QUote char anywhere other than the either ends of cell text content, will get replaced
by [\_] i.e underscore.

NOTE: User can set a different field seperator or quote char from the commandline and or by
using the cfieldsep and ctextquote commands.


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


### Converting CSV files

TO convert a csv file from using one fieldsep character to another.

First set the fieldsep to that used by the csv file currently.

	Ex: :cfieldsep theFieldSepChar

Next load the file

	Ex: :l pathto/file

Set the new fieldsep you want to use while saving

	Ex: :cfieldsep theNewFieldSepChar

Next write the file with the new fiedlsep

	Ex: :w pathto/file



## Misc


### Notes


#### Esc, Esc, Essscccccccc

If a explicit command seems to get stuck or not do anything, remember to try and
press Esc one or more times and see if the program comes back to default command mode.

You will know that you are in default command mode, when you see the program's name
in the top left corner of the terminal (i.e 0,0 cell).


#### FlyPython

If flypython mode is enabled by passing --flypython in the command line to the program,
then a text cell's content can be interpreted as a python expression when that text cell
is refered by a =expression in another cell.

	However there are limits to this like

	a =expression cant directly include module-submodule chaining or module/class functions
	like say os.path.abspath or list.reverse or so. Because =expression evaluation logic
	splits this up thus ending up with only the last part being evaluated as a independent
	function and not the associated class or module name which contains it.

	while having a text cell with the required python expression (which can include calls
	to module, submodule and or class and its functions) and then running it by using
	=TextCellAddress expression in some other cell has the limitation that the cell addresses
	if any in the python expression of the text cell dont get expanded into cell values.

	May unlock these later, not sure for now.


In normal mode

	a text cell, if refered from =expression will be valued as containing
	the numeric value 0.

	while numeric and =expression cells can contain basic python expressions,
	which refer to and operate on basic data type values directly or by fetching
	from cells that contain them directly or through other =expressions, which
	can also use the allowed set of functions by the program.

		But they cant refer to any python variables or modules in general,
		because globals and locals will be empty.


#### =expressions

##### text cell value is 0

Do keep in mind that =expressions which allow numeric evaluation of the specified
expression in a given cell, expects any cell references|addresses used in them to
inturn (i.e those referenced cells) also contain =expressions and or numbers and
not plain text data (numbers in quotes are text).

Any text cell will be treated as containing 0, if refered in a =expression.

If flypython mode is enabled, then things are interpreted differently.

##### None

So if you get a None instead of a numeric value which you were expecting, then
cross check that all cells refered by that cell or any other cell indirectly
referenced through a chain of =expressions, all contain valid expressions and
or valid values.


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
to the loaded file setting the program's display to a single row and or column view,
as the case may (i.e depending on how many lines are there and inturn if any of
those lines have fieldsep char in them or not). So also the content of the file will
be clipped from display perspective. One could run the command

	:xcols 25

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

[DONE] helper commands which work on a range of cells like

	[DONE] rcopy srcRange destRange

	[DONE] rgennums startCell:endCell [startNum] [delta]

	[DONE] rclear

Simple print to text file logic

[DONE] commandline shell

[LATER] =rows, =cols

[DONE] Allow paste to update cell addresses in the =expression.

[DONE] Trap calc loops. Tracks (uni/)multipath calc indirection and crossing of predefined callDepth and or exhausting of sliding recursion limit based block
level windowing logic to flag loops or overly long cell-to-cell chaining.

	[BYPASSED] Opti TrapCalcLoop - Check number of cell addresses across all =expressions and use it to decide, when to break a calc as dead-looped.

	[DONE] ErrTag Cells belonging to a CalcLoop, only if they have =expressions, which refer to i.e include other cell addresses.
	Using multipass evaluation logic with valid result caching and error list helps achieve this.

	[DONE] Maintain a current depth (either recursive or indirections) wrt calls and use it to decide, when to stop.

[DONE] Lazy/Opti recalcs - No need to recalculate unless some field/cell's content is updated.

[DONE] Maintain reverse list of cell depedencies (i.e each cell maintains a list of cells which dependOn/use it) to avoid recalculating cells,
when a given cell is edited. Needly mainly for crazy spreadsheets with overly very very long cell-to-cell chaining, that too in the direction opposite
to the one used for cell calculation by the program.

[DONE] Allow cols beyond ZZ.

[DONE] Tab completion of dir|filenames as well as predefined parts of commands.

[DONE] Change fieldsep and quote from within the program (i.e while it is running).

[PARTIAL] MAYBE treat each cell like a python variable or statement or expression. So also no need for = prefix. All text needs Quotes.

	[DONE] Maybe each cell contains either a Int, Float or String data type.

		Each cell contains either Nothing or =expression or Numeric or Text

	[DONE] Maybe Retain = prefix to trigger eval, while without = interpret as one of the basic data types.

[DONE] Move file related stuff to fileio module.

[DONE] Markers so that it is easier to use rcommands.

[DONE] Dont clip numeric values.

[PARTIAL] CLear statusbar if screen doesnt fill horizontally.

	Done wrt cdata_update processing in a simple and dumb way for now.


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

The existing commandline spreadsheet program sc crashing in few cases, also didnt help.

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

Any looping in the =expression calculations is now trapped, tagged and stopped for simple cases.

Handle quote char if any inbetween (replace with placeholder), or any at the end.


### 20200905IST1212 - OnamPlusTeachersDayRelease

Use a more specific callDepth based calc looping trapping logic. The previous logic would have triggered the maybe calc loop flag even for cells,
which are lets say referenced from a very very huge number of other cells all of which are inturn used or referenced from a single cell using
a cell range in its =expression. This should avoid such false positives.

renamed :readonly and :readwrite to :mreadonly :mreadwrite so that only range based commands start with r for now. And m cleanly maps to mode.

--calldepth cmdline argument.

:rgennums number sequence generator.

Comment out some prints in main display path.

Display cached cell eval data, to make the spreadsheet displaying fast in general, irrespective of the amount of calculations involved in the spreadsheet.
Cell data recalculations occur only when some cell content changes due to user triggered actions like editing/inserting/deleting cells etc.

Trap exception during cell =expression evaluation, so that all cells get evaluated and cache gets updated on a call to cdata_update.

Cells with no data in them maps to 0 for numeric evaluations.

Cells accessed through the supported functions (by being part of their arguments) are now accounted by the CalcLooping trapping logic both wrt
the callDepth as well as cell calcCnt.

:rcopy[asis] and :rgennums now increase the spreadsheet size, if required.

When retrieving numeric value of cells, if their value is already calculated and cached, the same will be reused. At same time, as was already implemented,
any modification to cell content will also clear the cache, ensuring that all cell values will get recalculated.

Fix a oversight, where I was trying to remove the newline char at end of each read line from file, at two different places. This was leading to the last
char of the last field's value, in each row, getting eaten up.

Done while viewing few good movies including Joseph among others.

NValue also updates the cell calculation cache, so that a cell is not recalculated more than once irrespective of in which way the cell dependencies flow.

cdata_update modified to allow long chain(s) of cells based calcs to be handled in a part by part basis over multiple steps/loops.
cdata_update sets error tag on cells which raised exception.

That bit odd missing recursion errors has been identified, I had a try-except in do_func but not logging into ErrFile, but LogFile. So now recrusion error
is pushed up the logic chain. Inturn cdata_update tags Recursion and Exception err cells.

Standardised ErrTag pattern. Added :rclearerr command.

Spead up usage for general case, with partial Cell ReCalculation by default, with full recalculation triggered only if cells in view trigger a recursion error.


### 20200907IST1212 - GauriGaneshaToOnamToTeachersDayRelease

Show a processing status message from \_cdraw\_data before _cdata_update is called. This ensures that if cdata_update is forced to trigger time consuming
calculations, then user sees the processing status message.

Added support for arbitrary number of cols, similar to rows. While trying to test this, noticed that gnumeric and libreoffice potentially seem to have a limit
on the number of columsn allowed (need to verify libreoffice/gnumeric bit more later).

Show processing status message in Non edit modes only.

Rename mreadonly and mreadwrite to creadonly (cro) and creadwrite (crw). This makes way for m based marker commands in future. As also c based cfieldsep
and ctextquote commands in future.

To avoid confusion and to have consistancy and semantic match, have renamed arguments of functions which took cell's row and col info from y,x to r,c.

Added statusbar helper, use for processing status.

Add cfieldsep and ctextquote commands to set fieldsep and textquote from within the program. This will allow one to convert a csv file from using 1 fieldsep
and or quote to a different one. When user requests this change, all existing text cell contents also get the corresponding textquote char in them updated,
if it was a ctextquote command. cfieldsep doesnt update text contents, bcas old fieldsep if any in a text field, has nothing to do with the csv fieldsep.

TODO:THINK WHile saving, will have to check for and handle quotes appropriately. Currently only field sep handled during saving. Note: If loaded csv file
was proper, then when user edits things, program tries to ensure that textquote is handled properly. And also if user changes textquote at runtime.
So also while saving if textquote is not explicitly checked for safe use, things should be fine at one level, in most cases.

While setting textquote using ctextquote, if the new textquote is already part of any cell text contents, then it will get replaced by the alt2inbtwquote char.
This ensures that contents of the csv file wont get misinterpreted later.

Load/Save show statusbar update.

Allow Numeric values to overflow into adjacent empty cells.

### 20200908IST1037 - GauriGaneshaToOnamToTeachersDayRelease

Moved file io logic to fileio module. Need to test it bitmore.

Fix main's dlg/status for multi line messages, which start at 0th row. Note that dlg/status row/col corresponds to data cells and not screen row/cols or screen y/x.

Added marker commands. Rcmds can now use markers in place of cell addresses.

Cleaned up few of the messages. Clear cdata_update processing message.

Moved the edit related logics into edit module (i.e copy/cut/paste/del cell, insert/delete row/col, rcopy/rclear). Even rgennums which edits contents of the cells
also moved into edit module.

For rcmds which require source and destination cell ranges (i.e commands like rcopy and rcopyasis), if user gives only the source cell range and then only the
start cell address wrt the destination, then infer the destination end cell address from the source cell range.

Fixed the odd slow navigation towards right or down direction of very large spreadsheets. This was due to me dumping in those two direction navigation logics.
ALso commented/removed full me print in general.


### 20200909IST0955 - GauriGaneshaToOnamToTeachersDayRelease


Consolidate all cell content evaluations to depend on nvalue_key for the core/highlevel interpretation irrespective of from where cell content needs to be used
i.e be it cdraw_data->value_Key, or be it cdata_update or anywhere else. Inturn a new and potentially simplified from user perspective cell content interpretation
now implemented in nvalue_key.

Also the internal/program evaluation of =expression remains in the nvalue_expr (previous \_nvalue)

Stop python snippets from running in uncontrolled way, if desired. Its also the default.
[DONE] Add a cmdline arg to open up python eval so that bit more varied set of python expressions can be run from a cell.

Dont cache None/Empty cells in calculation cdata cache. Sacrifice bit of processing speed for memory.

[DONE] Expand ~ at begin of path (os.path.expanduser)

[DONE] Move eval/value logics to a seperate file.

[DONE] move navigation related stuff to a seperate file.

[LATER] Maybe use numpy array for calculated cache. (There are equal or more fundamental changes that can help, so so so).

Make rgennums generate direct numbers now instead of =number. Speeds up operations which have to worry about =expressions like insert/delete/edit etc.

[DONE] parse =expressions and mark those which have cell addresses, so that only they get checked during insert/delete as well as during
recalculation of cells, rather than all cells with =expressions. [update] the program also builds a list of forward and reverse dependencies
for each of the cell with =expressions which have cell addresses in them, as noted in other places of this readme and in the code.

[DONE] Progress status for insert/delete

[DONE] cross check password by reentering same before using for save. So that it helps in case user has wrongly typed the password by mistake.

By default avoid overwriting existing file during saves.

Added a basic tab completion of file paths support for file load/save operations including password based ones.
If a partial path name is given, and if basenames within current dirname match it, it will loop thro that list first for n times, before returning to
the generic list for that dirname. [DONE] Need to relook at the code once and reflow things, where possible and or simplify it.


### 20200911IST1120 - GauriGaneshaToOnamToTeachersDayRelease

Made the tab based path completion logic more user-controlled and inturn more constrained and less over-intelligent. In the process also simplifying it
and making its end use more natural. Error tag missing and or non accessible path entries.

Cant forget the interesting docufilms from DW, among others. They were the companions while thinking and coding some of these ;-)

Be discrete with chopping of the last char.

Away in Netflix a interesting watchable series.

Make cell edits/modifications and resultant recalc propogation bit intelligent, rather than the brute force clearing of calc cache of all cells. WHich
forces all cells to be recalculated, as required. Now when a cell is edited, even in spreadsheets with very heavy bunch of calculations, if not many
cells depend on the edited cell, then the calculations finish very fast and user can continue using the spreadsheet immidiately.

	For cells which are towards the root of a long chain of cell-to-cell dependency based calcs, if they are edited, it would lead to all related
	cells getting recalcuated. However the optimisation of not calculating cells which are not visible directly or indirectly limits the load to
	a great extent. However if both the initial and the last few cells in a very very long chaing of cell-to-cell calcs is visible on the screen
	at the same time and inturn if one of the initial cells in the calc-chain is modified, then as the full chain has to be calculated, it will
	lead to some amount of time being required to finish the calcs, before user can continue using the spreadsheet.

	cell content edit/cut/delete/paste now use the efficient syncdCellUpdated logic to clear calc cache.

	clear and new also call syncd.create_links.

	Insert and Delete row/col operations also call syncd.create_links.

		Insert: Move current cdata values as required into new cdata dictionary with updated positions, where required.
		Inturn call syncd.create_links (as it doesnt take much time, instead of trying to adjust the values to account for insert).
		With this the performance is relaively much better.

		Delete: One needs to check for equivalence of =expression, wrt generating same value, before and after delete.
		So for now cells with =expression have their cdata cleared. While other types of cells have their numeric value
		copied from old calc cache to new calc cache. This is better than full cache clearing, but not optimal.

			Also not thinking of adapting fwd/rev links wrt delete, instead links are newly created, as it doesnt
			take much time at one level.

			ALso will have to update the cell address adjust logic to return as to whether the delete involved just
			moving the cell addresses and or reducing the size of cell ranges if any.

			Delete is a WorkInProgress wrt optimising it, rather currently nothing beyond basic done.

			[update:20200917] using revlinks, delete is optimised similar to insert, in that only cells whose values
			get affected by the delete row(s)/col(s) are recalculated now.

	rcmds call syncd.cell_updated as required.

MapTo/Use current directory for completing path using tab completion, if only file part given and there is no directory part given by user.

Added a xrefresh command.


### 20200913IST1530+ - GauriGaneshaToOnamToTeachersDayPlus01Release

DONE: Use color to distinguish between alternate rows, so that easier for user to map content to its corresponding row.

DONE: Add xrows and xcols to increase rows or cols at the end quickly. Instead of using ica, icb, ira or irb which also
process each and every cell wrt its =expression, to see if they need to be updated.

Renamed xrefresh to xrecalc, as it mainly recalculates all the cells as and when they or their dependents become visible.

Center the row and col addresses shown.

DONE: Right align the cell contents, while overflowing towards the left cells which are empty. Indicate clipping of cell contents.

	Add support for xalignleft, xalignright and xaligndefault.
	NOTE: Has been renamed and spaced out to calign left|right|default now.

xviewraw and xviewnormal commands added.

Insert uses fwdLinks to ignore cells with =expressions which dont depend on other cells. This speeds up insert op a lot for spreadhsheets
with lot of (millions)  =expressions which are independent. Similar stratergy also added to delete rows/cols logic.

cformat commands to control how numbers are displayed. Doesnt affect the calculations.

Added support for tab completion of predefined parts of the : commands (i.e explicit commands of the program). Also shows hint for parts that user has to specify.

DONE: cell address ranges as lists, if found as argument to python functions.


### 20200916IST1507+ - GauriGaneshaToOnamToTeachersDayPlus01Release

Make get_token quoted string logic more generic, so that any char can be contained in a quoted string.

Added :rsearch command to search for a given token/string in the cells. Also allow replacing of searched string.

DONE: Handle the 0th row wrt explicit command entry. Dont show cell col header and remember to clear whats previously printed as user goes about editing the cmd.
To help with knowing the current cell so that user can enter it as part of some of the :rcmds which could use them, now colhdr is enabled for :rcmds.

Added implicit markers @mEND, @mCUR


TODO:LATER: Date related functions

DONE: Make delete row/col bit more efficient by clearing calcs of only the dependent cells of the deleted rows/cols (using recursive reverse links lists).
And then creating the new calc cache by copying all the unaffected cell calcs. Previously delete used to clear all =expression cells with cell addresses in them,
whether dependent or not.

Now given that most of the core interconnected logics have been handled in a sufficiently ok manner, and crash tested with shallow (default) recursion limit,
open up the flood gates of performance (relatively speaking) by increasing the python recursion limit from 1K to 5K and also increase the programs core level
trap logic to have depth of 10K. This ensures that chained calculations dont trigger the recursion exception for most normal use cases (rather even the current
chained test files dont trigger this any more, so need to add new even deeper test files), and inturn the calculations occur faster as a whole. And Even python
seems to behave better in general with deeper recursion limit.

	NOTE: THis also means the program will take bit more time to trap loops, because more rope is given for the logics to play around.

Allow user to set tab as fieldsep by passing \\t to :cfieldsep


### 20200923IST1035+ Remembering SPB (SP Balasubramaniam)

Move the getting cell value or nvalue logics into cellval module.

Move handling of each input csv file line (encrypted or other wise) into its own func.

As roughly speaking internally python interpreter runs as a single thread instance, using pure python threads to parallelise a job
to speed it up doesnt really help. As at any given time only bytecode from one of the multiple threads will get interpreted. This
ensures that simple operations on python's native datatypes are atomic (i.e either reading or writing into them, but not both in
same expression/statement).

Time load and cell dependency links building logics.

Added csvload(.load\_line) c extension module. This speeds up parsing of lines from the csv file to create the data dictionary by ~4 times.

	fillednum|expr.csv file's loading part now takes only 1.2 seconds instead of the 4.6+ seconds of the pure python based logic.
	However the forward and reverse dep list creation is still in python and that part still takes few seconds to build, especially
	if there are millions of cells with =expressions.

	Initially though of using ctypes and a pure c logic imported into python to parse a line and return a bytes array containing
	the cell contents like Cell1ContentLen2Bytes + Cell1ContentsNBytes + C2Len+C2Bytes + ... + CNLen0 + CNPLUS1Len + CNPLUS1Bytes + ...
	Then decided against it and decided to implement a c extention module for python, so that the data dictionary is built up, as
	the cell contents are parsed, so that there is no need to parse again in python.

		Also decided to do the extension using the c-api/extending spec directly rather than using any 3rd party tools for extension
		like cython or ..., because one never knows when the 3rd party tool may get dropped. And hopefully the c-api is stable.

Added c based helper logic for getting list of all cell addresses and or ranges in a cell content, because re module of python was taking around
5.5 seconds for a spreadsheet containing ~ 3 million expression filled cells. This new c based logic does the same job in around 1.5 seconds.

Also commented out the timing logic in the cell\_updated, as one round a good enough speedup has been done wrt its and its users logic now.
This inturn helps reduce the time by another 1.5 seconds (as the timing logic was getting triggerd for each cell).

With the 3 updates done i.e 2 wrt using c based helpers for some frequently used logics and the 1 related to commenting out finegrained timing,
now loading of a spreadsheet with around 3 - 4 million expression filled cells has reduced from around 13+ seconds to 4 seconds.

[DONE] Clip the last column in the spreadsheet, if only partially visible and or ... RATHER it was a issue with loadline not removing newline
at the end of the line, which inturn was manifesting with the display of last column because it would have contained this newline.

chelper's csv chars are updated to the latest fieldsep and textquote, before its load\_line is called.




## thoughts behind this program

Wanting a simple commandline program which allows one to store and view roughly structured data including calculations in a secure manner, put differently
a spreadsheet logic.  It should also allow one to identify when corruption occurs and or unauthorised modifications have been done.

Exploring any ideas that may pop up when trying to implement a spreadsheet just like that on the go like

	authenticated encryption.

	sparse data structure based memory storage

	windowed lazy/deffered cached evaluations, triggered when a cell or its dependent cells become visible

	using recursion limit exception to implement a optimistic multipass oppurtunistic eval logic for resolving deep chaining,
	while still error tagging loops.

		optimistic and oppurtunistic - go ahead inspite of exceptions, evaluating what ever can be at any given tiem.

		multiplass - eval cells with deep chaining in steps where required, caching and reusing results as they become available.

	using forward and reverse dependency lists and use same to optimise edit/modify(insert/del) operations on spreadsheet.

	table/matrix view of fixed size cells with overflowing of contents into adjacent cells from display perspective.

	adjust cell addresses in =expressions during copy-paste or insert/delete operations.

	parse tokens and expressions.

	tab completion of file paths and command parts, curses again, escape to shell from within, constrain python functions and allow use of cells, ...

	alignment, raw/normal mode, precision and conversion for display, ...

	speed is not the goal, while still being sufficiently usable, in the middle of exploring/trying out the above

	Using c extension modules in python to speed up often used things if required.

Also scratch my immidiate itch of wanting a sufficiently sane and easy spreadsheet program given that libreoffice was crashing left/right/center on me
on a chromebook and the commandline sc also crashing once in a while, thus setting up the stage and giving me a reason to explore. Having my own cmdline
spreadsheet which I can update/modify as and if required relatively easily, is the icing at the end.



## Vasudhaiva Kutumbakam (the World is One Family)

If you find the program useful, and inturn if you can afford to donate, donating to a local good cause near you, would help those in need.

