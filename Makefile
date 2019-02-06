
all:
	python3 setup.py build

install:
	python3 setup.py install

test:
	python3 tests/test.py

.PHONY: clean

clean:
	rm -rf build
