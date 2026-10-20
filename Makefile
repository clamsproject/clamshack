clean:
	rm -rf build
	rm -rf src/*.egg-info
	rm -rf src/shack/__pycache__
	rm -rf tests/__pycache__

build:
	make clean
	python -m build

test:
	make clean
	pytest --disable-warnings --tb=line
