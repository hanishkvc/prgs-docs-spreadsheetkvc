
run:
	python3 spreadsheetkvc.py

html: README.md
	pandoc --metadata pagetitle="SpreadSheetKVC Readme" -s -o README.html README.md

cmods: csvload.c
	gcc `pkg-config --cflags python3` csvload.c

setup:
	python3 setup.py build
	python3 setup.py install

clean: README.html
	rm README.html

