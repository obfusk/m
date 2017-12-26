SHELL     := bash
PY        ?= python3
ME        := m.py
PKG       := mmm

.PHONY: test test_verbose coverage clean cleanup install package \
        publish _dch

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

cleanup: clean
	rm -fr debian/.debhelper debian/files debian/mmm*

install:
	test -d "$(DESTDIR)"
	mkdir -p "$(DESTDIR)"/usr/bin
	cp -i m.py "$(DESTDIR)"/usr/bin/m

%.rst: %.md
	grep -Ev '^\s*<!--.*-->\s*$$' $< \
	  | pandoc --from=markdown -o $@
	! grep -q raw:: $@

package: README.rst
	$(PY) setup.py sdist bdist_wheel

publish: clean package
	read -r -p "Are you sure? "; \
	[[ "$$REPLY" == [Yy]* ]] && twine upload dist/*

_dch:
	export DEBEMAIL="$$( git config --get user.email )"; \
	dch -v $(NEWVERSION) --release-heuristic log && \
	gbp dch --since v$(OLDVERSION)
