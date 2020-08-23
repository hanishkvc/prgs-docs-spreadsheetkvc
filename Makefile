
run:
	python3 spreadsheetkvc.py 2> /tmp/t.1

pdf: README.md
	pandoc -o README.pdf README.md

clean: README.pdf
	rm README.pdf

