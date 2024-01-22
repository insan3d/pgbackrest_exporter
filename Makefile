# Usage:
# 
#  make venv    setup fresh Python environment
#  make lint    lint code with PyLint
#  make test    test code with PyTest
#  make image   build Docker image
#  make binary  build PyInstaller binary
#  make clean   cleanup everything
#
# Default target is to build PyInstaller binary.

.PHONY: clean lint tests
.DEFAULT_GOAL := binary

venv:
	python3 -m venv --system-site-packages --prompt pgbackrest_exporter venv
	./venv/bin/python3 -m pip install -r requirements.txt

devdeps: venv
	./venv/bin/python3 -m pip install pyinstaller pylint pytest-aiohttp

lint: devdeps
	./venv/bin/python3 -m pylint pgbackrest_exporter

test: devdeps
	./venv/bin/python3 -m pytest

image:
	DOCKER_CLI_HINTS=false docker build . \
		--tag pgbackrest_exporter:$(shell ./venv/bin/python3 pgbackrest_exporter --version| cut -dv -f2- | tr ' ' '-' | tr '[:upper:]' '[:lower:]')

binary: ./dist/pgbackrest_exporter
./dist/pgbackrest_exporter: lint test
	. ./venv/bin/activate && \
	pyinstaller --noconfirm --onefile --paths $(shell find venv -type d -name site-packages) \
		--name pgbackrest_exporter --strip pgbackrest_exporter/__main__.py

clean:
	rm -rf venv .pytest_cache build dist *.spec
	find . -type d -name __pycache__ | xargs rm -rf
