# Always fail shell on all errors
SHELL := /bin/bash -euo pipefail

# BEGIN Disable in-built Makefile rules
MAKEFLAGS += --no-builtin-rules
.SUFFIXES:
# END Disable in-built Makefile rules

BUILD_DIR := build

# Make sure build dir exists
$(shell mkdir -p $(BUILD_DIR))

# Look in build dir for goal files like "wheels" and Docker image
# timestamp files
VPATH=$(BUILD_DIR) dist

VERSION=$(shell cat VERSION.txt)
SPRINGFIELD_WHEEL=springfield-$(VERSION)-py2.py3-none-any.whl


.PHONY: all
all: docs wheel


docs: $(shell find docs ! -path 'docs/_build/*' -type f) _README.rst
	pip install -r docs/requirements.txt
	cd docs && make html


.PHONY: wheel
wheel: $(SPRINGFIELD_WHEEL)
$(SPRINGFIELD_WHEEL): $(shell find src -type f ! -path '*.pyc') setup.py build-requirements.txt
	pip install -r build-requirements.txt
	python setup.py build


# Publish to pypi
publish: $(SPRINGFIELD_WHEEL)
	python setup.py publish


.PHONY: test
test: $(SPRINGFIELD_WHEEL)
	pip install -r test_requirements.txt ./dist/$(SPRINGFIELD_WHEEL)
	cd src && python tests/runtests.py -v


.PHONY: clean
clean:
	rm -Rf dist build