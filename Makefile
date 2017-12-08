SHELL   := bash
PY      ?= python3
ME      := m.py
PKG     := mmm

.PHONY: test test_verbose coverage clean_testdata clean \
        package publish

test: clean_testdata
	$(PY) $(ME) test

test_verbose: clean_testdata
	$(PY) $(ME) test -v

coverage: clean_testdata
	$(PY) -mcoverage run $(ME) test
	$(PY) -mcoverage html

clean_testdata:
	rm -f test/home/.config/vlc/vlc-qt-interface.conf
	rm -f test/home/.obfusk-m/dir__*.json

clean: clean_testdata
	rm -fr .coverage build/ dist/ htmlcov/ $(PKG).egg-info/
	find -name '*.pyc' -delete
	find -name __pycache__ -delete

package:
	$(PY) setup.py sdist bdist_wheel

publish: clean package
	read -r -p "Are you sure? "; \
	[[ "$$REPLY" =~ [Yy]* ]] && twine upload dist/*
