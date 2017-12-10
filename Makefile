SHELL   := bash
PY      ?= python3
ME      := m.py
PKG     := mmm

.PHONY: test test_verbose coverage clean package publish

test:
	$(PY) $(ME) _test

test_verbose:
	$(PY) $(ME) _test -v

coverage:
	$(PY) -mcoverage run $(ME) _test
	$(PY) -mcoverage html

clean:
	rm -fr .coverage htmlcov/
	rm -fr README.rst build/ dist/ $(PKG).egg-info/
	find -name '*.pyc' -delete
	find -name __pycache__ -delete

%.rst: %.md
	pandoc -o $@ $<

package: README.rst
	$(PY) setup.py sdist bdist_wheel

publish: clean package
	read -r -p "Are you sure? "; \
	[[ "$$REPLY" =~ [Yy]* ]] && twine upload dist/*
