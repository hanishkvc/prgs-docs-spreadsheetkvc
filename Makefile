
run:
	python3 spreadsheetkvc.py

html: README.md
	pandoc --metadata pagetitle="SpreadSheetKVC Readme" -s -o README.html README.md

clean: README.html
	rm README.html

