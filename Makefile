clean:
	rm -rf build
	rm -rf src/clamshack_mv.egg-info
	rm -rf tests/__pycache__

build:
	python -m build

test:
	pytest --disable-warnings --tb=line
