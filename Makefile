clean:
	rm -rf build
	rm -rf src/*.egg-info
	rm -rf tests/__pycache__

build:
	make clean
	python -m build

test:
	pytest --disable-warnings --tb=line
