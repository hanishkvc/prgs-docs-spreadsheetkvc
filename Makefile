
run:
	python3 spreadsheetkvc.py

html: README.md
	pandoc --metadata pagetitle="SpreadSheetKVC Readme" -s -o README.html README.md

cmods: csvload.c
	gcc `pkg-config --cflags python3` csvload.c

clean: README.html
	rm README.html

