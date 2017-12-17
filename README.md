<!-- {{{1 -->

    File        : README.md
    Maintainer  : Felix C. Stegerman <flx@obfusk.net>
    Date        : 2017-12-17

    Copyright   : Copyright (C) 2017  Felix C. Stegerman
    Version     : v0.2.1

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
`playing`, `watched`, `skipped`.

See also the tests in the source code for more examples.

## Help

```bash
$ m --help      # global options & subcommands
$ m ls --help   # subcommand (ls in this case) options & argument(s)
```

## Installing

You can just put `m.py` somewhere on your `$PATH` (in e.g. `~/bin`; I
suggest calling it `m`, but you're free to choose another name).

Alternatively, you can use pip:

```bash
$ pip3 install --user mmm   # for Debian; on other OS's you may need
                            # pip instead of pip3 and/or no --user
```

## Configuration File

You can set some defaults in `~/.obfusk-m/config.json`; for example:

```json
{
  "colour": true,
  "numbers": true,
  "player": "mpv",
  "show_hidden": true
}
```

## TODO

* update README + version + package!
* `ack TODO`
* `m --virtual foo/bar {ls,...}` + `m virt [--update] [--title]*
  [--url]* [--url-template] [--episodes] [--browser]` +
  `VIRTUAL:/foo/bar` + `virt__*.json` + `m {watching,...}
  --include-virtual`?
* `m import-{playing,watched} [--zero]`?
* `m kodi-*-sql`?
* `m kodi-import-* [--replace] [--include] [--exclude]`?
* only use `safe()` when stdout is a tty?
* document `safe()` vs `--zero`
* more file extensions!

<!-- -->

* bash completion?
* `m mv`?
* `--tree` for `playing` etc.?
* `--json`?
* kodi db export/sync?
* sign pypi package?
* fix `.exist()` race conditions?

## License

[GPLv3+](https://www.gnu.org/licenses/gpl-3.0.html).

<!-- vim: set tw=70 sw=2 sts=2 et fdm=marker : -->
