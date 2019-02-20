
all:
	python3 setup.py build

install:
	python3 setup.py install

upload:
	python3 setup.py sdist
	twine upload dist/*

test:
	python3 tests/test.py

.PHONY: clean

clean:
	rm -rf build
	rm -rf dist
