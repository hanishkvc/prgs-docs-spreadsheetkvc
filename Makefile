
run:
	python3 spreadkvc.py 2> /tmp/t.1

pdf: README.md
	pandoc -o README.pdf README.md

clean: README.pdf
	rm README.pdf

