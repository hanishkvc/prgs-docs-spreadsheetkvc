
run:
	python3 spreadsheetkvc.py

html: README.md
	pandoc --metadata pagetitle="SpreadSheetKVC Readme" -s -o README.html README.md

cmods: load.c
	gcc `pkg-config --cflags python3` load.c

clean: README.html
	rm README.html

