<!-- {{{1 -->

    File        : README.md
    Maintainer  : Felix C. Stegerman <flx@obfusk.net>
    Date        : 2017-12-26

    Copyright   : Copyright (C) 2017  Felix C. Stegerman
    Version     : v0.3.0

<!-- }}}1 -->

[![PyPI Version](https://img.shields.io/pypi/v/mmm.svg)](https://pypi.python.org/pypi/mmm)
[![Build Status](https://travis-ci.org/obfusk/m.svg?branch=master)](https://travis-ci.org/obfusk/m)

## Description

m - minimalistic media manager

m keeps track of which files you've played (or are still playing) and
thus allows you to easily continue playing the next file (using vlc or
mpv).

* Supports importing existing playing/watched data from Kodi.
* Stores its data in JSON files (one per directory) in `~/.obfusk-m`;
  you can put this directory in git if you want a changelog :)

NB: extracting the timestamp from the vlc config and mpv output is a
little hacky :(

NB: m uses `$PWD` to make sure it sees the current path the same as
the shell it is run from (i.e. it does not resolve the path by
following symlinks, allowing the link targets to be relocated);
unfortunately, this means that it *does not* see two directories as
identical if they are accessed using different paths, even if the
resolved path is the same.  So you may want to avoid using different
paths to the same directory (and `--dir`).

## Examples

```bash
$ cd /some/media/dir
$ m ls    # list files ([*] = skip, [x] = done, [>] = playing, [ ] = new)
[x] Something - 01.mkv
[x] Something - 02.mkv
[x] Something - 03.mkv
[x] Something - 04.mkv
[x] Something - 05.mkv
[x] Something - 06.mkv
[>] Something - 07.mkv 0:04:04
[ ] Something - 08.mkv
[ ] Something - 09.mkv
$ m next  # plays current/next episode (i.e. #7) w/ vlc
```

```bash
$ m ld    # list dirs (shows #playing, #new for indexed subdirectories)
(   2!) Dir A
(     ) Dir B
(1> 0!) Dir C
(   0!) Dir D
```

Commands include: `list`/`ls`, `list-dirs`/`ld`, `list-all`/`la`,
`next`, `play FILE`, `mark FILE`, `unmark FILE`, `skip FILE`, `index`,
`playing`, `watched`, `skipped`, `todo`.

See also the tests in the source code (also available as `m examples`)
for more examples.

## Help

```bash
$ m --help      # global options & subcommands
$ m ls --help   # subcommand (ls in this case) options & argument(s)
$ m examples    # show some examples from the tests
```

## Requirements

Python >= 3.5.

## Installing

You can just put `m.py` somewhere on your `$PATH` (in e.g. `~/bin`; I
suggest calling it `m`, but you're free to choose another name).

You may want to clone the repository instead of just downloading
`m.py` to be able to get new versions easily.

Alternatively, you can install m using pip (the Python package
manager) or build and install a Debian package.

NB: the pip and Debian packages are called `mmm` instead of `m`.

### Using git

```bash
$ cd /some/convenient/dir
$ git clone https://github.com/obfusk/m.git obfusk-m
$ cd ~/bin                  # or some other dir on your $PATH
$ ln -s /some/convenient/dir/obfusk-m/m.py m
```

Updating:

```bash
$ cd /some/convenient/dir/obfusk-m
$ git pull
```

### Using pip

```bash
$ pip3 install --user mmm   # for Debian; on other OS's you may need
                            # pip instead of pip3 and/or no --user
```

### Building a Debian package

```bash
$ sudo apt install debhelper dh-python    # install build dependencies
$ cd /some/convenient/dir
$ git clone https://github.com/obfusk/m.git obfusk-m
$ cd obfusk-m
$ dpkg-buildpackage
$ sudo dpkg -i ../mmm_*_all.deb
```

## Configuration File

You can set some defaults in `~/.obfusk-m/config.json`; for example:

```json
{
  "colour": true,
  "ignorecase": true,
  "numbers": true,
  "only_indexed": true,
  "player": "mpv",
  "show_hidden": true
}
```

## TODO

* update README + version + package!
* `ack TODO`

<!-- -->

* more file extensions!
* document `safe()` vs `--zero`
* `_pty_run`: also minimize output if not a tty?

### Maybe

* `m --virtual foo/bar {ls,...}` + `m virt [--update] [--title]*
  [--url]* [--url-template] [--episodes] [--browser]` +
  `VIRTUAL:/foo/bar` + `virt__*.json` + `m {watching,...}
  --include-virtual`?

<!-- -->

* test edge cases/failures?
* `--config-dir`?
* test `END_SECS`?
* note usage of dyn vars?

<!-- -->

* bash completion?
* `m mv`?
* `--tree` for `playing` etc.?
* `--json`?
* kodi db export/sync?
* sign pypi package?
* fix `.exist()` race conditions?
* use `locale.strcoll` vs `--ignorecase`?

## License

[GPLv3+](https://www.gnu.org/licenses/gpl-3.0.html).

<!-- vim: set tw=70 sw=2 sts=2 et fdm=marker : -->
