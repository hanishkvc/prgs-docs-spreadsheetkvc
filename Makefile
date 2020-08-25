
run:
	python3 spreadsheetkvc.py

pdf: README.md
	pandoc -o README.pdf README.md

clean: README.pdf
	rm README.pdf

