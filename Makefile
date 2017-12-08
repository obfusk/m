SHELL   := bash
PY      ?= python3
ME      := m.py

.PHONY: test test_verbose coverage clean_testdata clean

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
	rm -fr .coverage htmlcov/
	find -name '*.pyc' -delete
	find -name __pycache__ -delete
