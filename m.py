#!/usr/bin/python3
# encoding: utf-8

# --                                                            ; {{{1
#
# File        : m.py
# Maintainer  : Felix C. Stegerman <flx@obfusk.net>
# Date        : 2018-08-31
#
# Copyright   : Copyright (C) 2018  Felix C. Stegerman
# Version     : v0.4.1
# License     : GPLv3+
#
# --                                                            ; }}}1

                                                                # {{{1
r"""
m - minimalistic media manager

See README.md for additional information and examples.

Examples
========

First, set up some test data
----------------------------

NB: tests must be run from _test()!  Otherwise the temporary directory
and monkey-patching are not available.

>>> def abort(): raise KeyboardInterrupt("*** ABORT ***")
>>> if "TEST_DIR" not in globals(): abort()

>>> d             = TEST_DIR / "media"
>>> x, y, z, a, b = d / "x.mkv", d / "y.mkv", d / "z.mkv", \
...                 d / "more/a.mkv", d / "more/b.mkv"

>>> for _d in [d, d / "more", d / "More_", FAKE_HOME, FAKE_HOME / CFG]:
...   _d.mkdir()
>>> for _f in [x, y, z, a, b]: _f.touch()
>>> (FAKE_HOME / VLCQT).parent.mkdir(parents = True)

>>> (d / ".dotfile.mkv").touch()
>>> (d / ".dotdir").mkdir()

>>> _ = (FAKE_HOME / VLCQT).write_text(_VLC_TEST_CFG.format(x, y, z, a))
>>> vlc_get_times() == { str(x): 0, str(y): 0, str(z): 121,
...                      str(a): 246 }
True

>>> _clr = { True: "--colour", False: "--no-colour", None: "" }
>>> def run(a, d = d, c = False, x = []):
...   main("-d", str(d), *((_clr[c]+" "+a).split() + list(map(str, x))))
>>> def runI(s, *a, **k):
...   with stdin_from(s): run(*a, **k)
>>> def runO(*a, **k):
...   f = io.StringIO()
...   with contextlib.redirect_stdout(f): run(*a, **k)
...   return f.getvalue()
>>> def runE(*a, **k):
...   with contextlib.redirect_stderr(sys.stdout): run(*a, **k)
>>> def runH(*a, **k):
...   argv0, sys.argv[0] = sys.argv[0], "m"
...   try: run(*a, **k)
...   except SystemExit: pass
...   finally: sys.argv[0] = argv0


Now, run some examples
----------------------

NB: coloured output escapes are replaced by RED, NON etc. during test.

>>> run("ls")
[ ] x.mkv
[ ] y.mkv
[ ] z.mkv
>>> runE("mark x.mkv")
>>> runE("skip y.mkv")
>>> run("ls")
[x] x.mkv
[*] y.mkv
[ ] z.mkv
>>> run("next") # doctest: +ELLIPSIS
Playing z.mkv ...
RUN true vlc --fullscreen --play-and-exit -- .../media/z.mkv
>>> run("ls")
[x] x.mkv
[*] y.mkv
[>] z.mkv 0:02:01
>>> run("next-new")
No files to play.
>>> run("ls", c = True)
[GRNxNON] x.mkv
[CYA*NON] y.mkv
[RED>NON] z.mkv 0:02:01
>>> run("next") # doctest: +ELLIPSIS
Playing z.mkv from 0:02:01 ...
RUN true vlc --fullscreen --play-and-exit --start-time 116 -- .../media/z.mkv
>>> run("play y.mkv") # doctest: +ELLIPSIS
Playing y.mkv ...
RUN true vlc --fullscreen --play-and-exit -- .../media/y.mkv
>>> run("ls")
[x] x.mkv
[x] y.mkv
[>] z.mkv 0:02:01

>>> run("ls --numbers")
  1 [x] x.mkv
  2 [x] y.mkv
  3 [>] z.mkv 0:02:01
>>> runE("unmark 1-2")
>>> run("ls -n")
  1 [ ] x.mkv
  2 [ ] y.mkv
  3 [>] z.mkv 0:02:01
>>> runE("mark playing")
>>> run("ls -n")
  1 [ ] x.mkv
  2 [ ] y.mkv
  3 [x] z.mkv
>>> runE("skip all")
>>> run("ls -n")
  1 [*] x.mkv
  2 [*] y.mkv
  3 [*] z.mkv
>>> runE("mark 1,3")
>>> run("ls -n")
  1 [x] x.mkv
  2 [*] y.mkv
  3 [x] z.mkv
>>> runE("mark 4")
Error: out of range: '4'
>>> runE("mark oops")
Error: not a valid file name or number: 'oops'
>>> run("play 2,3") # doctest: +ELLIPSIS
Playing y.mkv ...
RUN true vlc --fullscreen --play-and-exit -- .../media/y.mkv
Playing z.mkv ...
RUN true vlc --fullscreen --play-and-exit -- .../media/z.mkv

>>> run("playing") # doctest: +ELLIPSIS
/.../media:
  z.mkv 0:02:01
>>> run("playing --only-files") # doctest: +ELLIPSIS
/.../media:
  z.mkv
>>> run("watched") # doctest: +ELLIPSIS
/.../media:
  x.mkv
  y.mkv
>>> run("watched --flat") # doctest: +ELLIPSIS
/.../media/x.mkv
/.../media/y.mkv
>>> runE("skip x.mkv")
>>> runE("skip y.mkv")
>>> runO("skipped --zero") # doctest: +ELLIPSIS
'/.../media/x.mkv\x00/.../media/y.mkv\x00'
>>> runO("playing --zero") # doctest: +ELLIPSIS
'/.../media/z.mkv 0:02:01\x00'
>>> runO("playing --zero --only-files") # doctest: +ELLIPSIS
'/.../media/z.mkv\x00'
>>> runE("mark z.mkv")
>>> run("next")
No files to play.
>>> runE("unmark y.mkv")
>>> run("ls")
[*] x.mkv
[ ] y.mkv
[x] z.mkv

>>> run("ld")
(     ) More_
(     ) more
>>> runE("index", d = d / "more")
>>> run("-i ld")
(   2!) more
(     ) More_
>>> run("ls", d = d / "more")
[ ] a.mkv
[ ] b.mkv
>>> run("play a.mkv", d = d / "more") # doctest: +ELLIPSIS
Playing a.mkv ...
RUN true vlc --fullscreen --play-and-exit -- .../media/more/a.mkv
>>> runE("mark b.mkv", d = d / "more")
>>> run("-i la")
(1> 0!) more
(     ) More_
[*] x.mkv
[ ] y.mkv
[x] z.mkv
>>> run("ld", c = True)
(     ) More_
(RED1NON>YLL 0NON!) more
>>> runE("unmark b.mkv", d = d / "more")
>>> run("ld", c = True)
(     ) More_
(RED1NON>BLU 1NON!) more
>>> run("ls", d = d / "more")
[>] a.mkv 0:04:06
[ ] b.mkv
>>> run("next-new", d = d / "more") # doctest: +ELLIPSIS
Playing b.mkv ...
RUN true vlc --fullscreen --play-and-exit -- .../media/more/b.mkv

>>> run("ld")
(     ) More_
(1> 0!) more
>>> run("ld -x")
(1> 0!) more
>>> runE("index", d = d / "More_")
>>> run("ld")
(   0!) More_
(1> 0!) more
>>> run("ld --todo")
(1> 0!) more
>>> run("todo") # doctest: +ELLIPSIS
(   1!) /.../media
(1> 0!) /.../media/more
>>> run("todo --only-dirs") # doctest: +ELLIPSIS
/.../media
/.../media/more

>>> run("--show-hidden ls -n")
  1 [ ] .dotfile.mkv
  2 [*] x.mkv
  3 [ ] y.mkv
  4 [x] z.mkv
>>> run("--show-hidden -i ld")
(     ) .dotdir
(1> 0!) more
(   0!) More_
>>> run("--show-hidden ld --only-indexed")
(   0!) More_
(1> 0!) more

>>> run("next --mpv") # doctest: +ELLIPSIS
Playing y.mkv ...
RUN true mpv --fullscreen -- .../media/y.mkv
>>> run("next --mpv") # doctest: +ELLIPSIS
Playing y.mkv from 0:01:01 ...
RUN true mpv --fullscreen --start=56 -- .../media/y.mkv
>>> run("ls")
[*] x.mkv
[>] y.mkv 0:01:01
[x] z.mkv
>>> run("next") # doctest: +ELLIPSIS
Playing y.mkv from 0:01:01 ...
RUN true vlc --fullscreen --play-and-exit --start-time 56 -- .../media/y.mkv

>>> run("db-file") # doctest: +ELLIPSIS
/.../home/.obfusk-m/dir__...|media__....json


Now, test w/ config.json
------------------------

>>> cfg = dict(colour = True, ignorecase = True, numbers = True,
...            only_indexed = True, player = "mpv", show_hidden = True,
...            exts = [".mkv"], add_exts = [".mp3"])
>>> _   = (FAKE_HOME / CFG / CFGFILE).write_text(json.dumps(cfg))
>>> for _f in [d / "hidden.mp4", d / "shown.mp3"]: _f.touch()

>>> run("ls", c = None)
  1 [ ] .dotfile.mkv
  2 [ ] shown.mp3
  3 [CYA*NON] x.mkv
  4 [GRNxNON] y.mkv
  5 [GRNxNON] z.mkv
>>> run("play y.mkv") # doctest: +ELLIPSIS
Playing y.mkv ...
RUN true mpv --fullscreen -- .../media/y.mkv
>>> run("play --vlc y.mkv") # doctest: +ELLIPSIS
Playing y.mkv from 0:01:01 ...
RUN true vlc --fullscreen --play-and-exit --start-time 56 -- .../media/y.mkv
>>> run("--no-show-hidden --no-colour ls --no-numbers", c = None)
[ ] shown.mp3
[*] x.mkv
[x] y.mkv
[x] z.mkv
>>> run("ld")
(1> 0!) more
(   0!) More_

>>> for _f in [d / "hidden.mp4", d / "shown.mp3"]: _f.unlink()
>>> _   = (FAKE_HOME / CFG / CFGFILE).write_text(json.dumps({}))


Now, test sorting
-----------------

>>> (d / "Y_.mkv").touch()

>>> run("ls --numbers")
  1 [ ] Y_.mkv
  2 [*] x.mkv
  3 [x] y.mkv
  4 [x] z.mkv
>>> runE("unmark 3")
>>> run("-i ls --numbers")
  1 [*] x.mkv
  2 [ ] y.mkv
  3 [ ] Y_.mkv
  4 [x] z.mkv
>>> runE("-i mark 1,3")
>>> run("-i ls --numbers")
  1 [x] x.mkv
  2 [ ] y.mkv
  3 [x] Y_.mkv
  4 [x] z.mkv

>>> numeric_tests = [ d / "NUM 42 TEST {}.mkv".format(x)
...                   for x in "1 2 03 10".split() ]
>>> for _f in numeric_tests: _f.touch()

>>> run("ls")
[ ] NUM 42 TEST 03.mkv
[ ] NUM 42 TEST 1.mkv
[ ] NUM 42 TEST 10.mkv
[ ] NUM 42 TEST 2.mkv
[x] Y_.mkv
[x] x.mkv
[ ] y.mkv
[x] z.mkv
>>> run("-N ls")
[ ] NUM 42 TEST 1.mkv
[ ] NUM 42 TEST 2.mkv
[ ] NUM 42 TEST 03.mkv
[ ] NUM 42 TEST 10.mkv
[x] Y_.mkv
[x] x.mkv
[ ] y.mkv
[x] z.mkv
>>> run("-N -i ls")
[ ] NUM 42 TEST 1.mkv
[ ] NUM 42 TEST 2.mkv
[ ] NUM 42 TEST 03.mkv
[ ] NUM 42 TEST 10.mkv
[x] x.mkv
[ ] y.mkv
[x] Y_.mkv
[x] z.mkv

>>> for _f in numeric_tests: _f.unlink()


Now, test w/ "unsafe" file & dir
--------------------------------

>>> (d / "un\033safe\x01file.mkv").touch()
>>> (d / "unsafe\ndir").mkdir()

>>> run("ls")
[x] Y_.mkv
[ ] un?safe?file.mkv
[x] x.mkv
[ ] y.mkv
[x] z.mkv
>>> run("ld")
(   0!) More_
(1> 0!) more
(     ) unsafe?dir
>>> run("play un\033safe\x01file.mkv") # doctest: +ELLIPSIS
Playing un?safe?file.mkv ...
RUN true vlc --fullscreen --play-and-exit -- .../media/un?safe?file.mkv


Now, test aliases
-----------------

>>> (d / "link").symlink_to(d / "more")

>>> db_load(d / "more")["dir"] # doctest: +ELLIPSIS
'/.../media/more'
>>> db_load(d / "link")["dir"] # doctest: +ELLIPSIS
'/.../media/link'

>>> run("ls", d = d / "link")
[ ] a.mkv
[ ] b.mkv
>>> run("alias", d = d / "link", x = [d / "more"]) # doctest: +ELLIPSIS
/.../.obfusk-m/dir__|...|media|link__....json -> dir__|...|media|more__....json
>>> run("ls", d = d / "link")
[>] a.mkv 0:04:06
[x] b.mkv

>>> run("unmark 2", d = d / "link")
>>> run("ls", d = d / "more")
[>] a.mkv 0:04:06
[ ] b.mkv

>>> db_load(d / "more")["dir"] # doctest: +ELLIPSIS
'/.../media/more'

>>> run("mark 2", d = d / "more")
>>> run("ls", d = d / "link")
[>] a.mkv 0:04:06
[x] b.mkv

>>> db_load(d / "link")["dir"] # doctest: +ELLIPSIS
'/.../media/more'


Now, check some errors
----------------------

>>> runE("mark /foo/bar/baz.mkv") # doctest: +ELLIPSIS
Error: '/foo/bar/baz.mkv' does not start with '/.../media'
>>> runE("mark nonexistent.mkv") # doctest: +ELLIPSIS
Error: '/.../nonexistent.mkv' is not a file
>>> runE("unmark nonexistent.mkv")
Ignoring unknown file 'nonexistent.mkv'.
>>> runE("unmark nonexistent.mkv --quiet")
>>> runE("mark more/a.mkv") # doctest: +ELLIPSIS
Error: '/.../more/a.mkv' is not a file in '/.../media'
>>> runE("unmark foo/bar.mkv") # doctest: +ELLIPSIS
Error: '/.../bar.mkv' is not a file in '/.../media'

>>> current_dir = str(cwd()); os.chdir(str(d))

>>> runE("alias more")
Error: 'more' is a relative path

>>> try: os.chdir(current_dir)
... except: abort()

>>> runE("alias /tmp") # doctest: +ELLIPSIS
Error: '/.../media' and '/tmp' do not resolve to the same path
>>> runE("alias", d = d / "link", x = [d / "more"]) # doctest: +ELLIPSIS
Error: '/.../.obfusk-m/dir__|...|media|link__....json' already exists

>>> (d / "one_more").mkdir()
>>> (d / "link2").symlink_to(d / "one_more")

>>> runE("alias", d = d / "link2", x = [d / "one_more"]) # doctest: +ELLIPSIS
Error: '/.../.obfusk-m/dir__|...|media|one_more__....json' does not exist


Now, check importing
--------------------

>>> watched = '''
... /some/watched/file/1.mkv
... /some/watched/file/2.mkv
... /some/other/watched/file/foo.mkv
... /some/old/dir/some/file/a.mp4
... /some/old/dir/some/file/b.mp4
... '''.strip("\n")
>>> playing = '''
... /some/file/to_skip/x.mkv 404
... /some/playing/file/1.mkv 0:01:01
... /some/playing/file/2.mkv 0:02:01
... /some/other/playing/file/bar.mkv 101
... '''.lstrip("\n").replace("\n", "\0")
>>> playing # doctest: +ELLIPSIS
'/some/file/to_skip/x.mkv 404\x00...bar.mkv 101\x00'

>>> runI(watched, r"import-watched --replace (?<=\A/some/)old(?=/dir/) new --replace foo bar")
Imported 5 file(s) in 3 dir(s).
>>> run("watched") # doctest: +ELLIPSIS
/some/new/dir/some/file:
  a.mp4
  b.mp4
/some/other/watched/file:
  bar.mkv
/some/watched/file:
  1.mkv
  2.mkv
/.../media:
  Y_.mkv
  un?safe?file.mkv
  x.mkv
  z.mkv
/.../media/more:
  b.mkv
>>> runI(playing, "import-playing --zero --exclude /to_skip/")
Imported 3 file(s) in 2 dir(s).
>>> run("playing") # doctest: +ELLIPSIS
/some/other/playing/file:
  bar.mkv 0:01:41
/some/playing/file:
  1.mkv 0:01:01
  2.mkv 0:02:01
/.../media/more:
  a.mkv 0:04:06
>>> runE("todo") # doctest: +ELLIPSIS
Ignoring nonexistent directory '/some/new/dir/some/file'.
Ignoring nonexistent directory '/some/other/playing/file'.
Ignoring nonexistent directory '/some/other/watched/file'.
Ignoring nonexistent directory '/some/playing/file'.
Ignoring nonexistent directory '/some/watched/file'.
(   1!) /.../media
(1> 0!) /.../media/more
>>> runE("todo --quiet") # doctest: +ELLIPSIS
(   1!) /.../media
(1> 0!) /.../media/more


Now, check --help
-----------------

>>> runH("--help") # doctest: +ELLIPSIS
usage: m [-h] [--version] [--dir DIR] [--show-hidden | --no-show-hidden]
         [--colour | --no-colour | --auto-colour]
         [--ignorecase | --no-ignorecase] [--numeric-sort | --no-numeric-sort]
         {list,l,ls,...}
         ...
<BLANKLINE>
m - minimalistic media manager
<BLANKLINE>
optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --dir DIR, -d DIR     use DIR instead of $PWD
  --show-hidden         show hidden (i.e. starting with .) files & dirs
  --no-show-hidden
  --colour              use coloured output (the default when stdout is a tty)
  --no-colour
  --auto-colour
  --ignorecase, -i      ignore case when sorting files & dirs
  --no-ignorecase
  --numeric-sort, -N    sort files & dirs numerically
  --no-numeric-sort
<BLANKLINE>
subcommands:
  {list,l,ls,...,_test}
    list (l, ls)        list files
    list-dirs (ld)      list directories
    list-all (la)       list directories & files
    next (n, continue, cont, c)
                        play (or continue) next (playing/new) file
    next-new (nn)       play next new file
    play (p)            play FILE
    mark (m)            mark FILE as done
    unmark (u)          mark FILE as new
    skip (s)            mark FILE as skip
    index (i)           index current directory
    alias               alias directory
    playing             list files marked as playing
    watched             list files marked as done
    skipped             list files marked as skip
    todo (unfinished)   list directories with files marked as playing or new
    db-file             print path to DB file
    import-watched      import watched data from stdin: each line is a file
                        path
    import-playing      import playing data from stdin: each line is a file
                        path (+ separator) + time
    kodi-import-watched
                        import watched data from kodi
    kodi-import-playing
                        import playing data from kodi
    kodi-watched-sql    print SQL for getting watched data from kodi
    kodi-playing-sql    print SQL for getting playing data from kodi
    examples            show some examples from the tests
<BLANKLINE>
NB: FILE is a file name, state or number(s);
e.g. '1', '1-5', '1,4-7', 'playing', 'new' or 'all'.
<BLANKLINE>
NB: file numbers may change when --ignorecase or --numeric-sort is used;
please use the same sort order when listing and using numbers.
<BLANKLINE>
See README.md for additional information and examples.

>>> runH("ls --help")
usage: m list [-h] [--numbers | --no-numbers]
<BLANKLINE>
list files
<BLANKLINE>
optional arguments:
  -h, --help     show this help message and exit
  --numbers, -n  show numbers (which can be used for mark etc.)
  --no-numbers

>>> runH("p --help")
usage: m play [-h] [--mpv | --vlc] FILE
<BLANKLINE>
play FILE
<BLANKLINE>
positional arguments:
  FILE
<BLANKLINE>
optional arguments:
  -h, --help  show this help message and exit
  --mpv       play using mpv
  --vlc       play using vlc (the default)

>>> runH("playing --help")
usage: m playing [-h] [--flat] [--zero] [--only-files]
<BLANKLINE>
list files marked as playing
<BLANKLINE>
optional arguments:
  -h, --help    show this help message and exit
  --flat        flat list of files instead of grouped by directory
  --zero        zero-delimited (implies --flat) output (for e.g. xargs -0)
  --only-files  only print files, not times


Now, check errors running commands
----------------------------------

>>> VLCCMD[0] = "false"
>>> runE("play x.mkv") # doctest: +ELLIPSIS
Playing x.mkv ...
RUN false vlc --fullscreen --play-and-exit -- .../media/x.mkv
Error: could not play file 'x.mkv': Command ... returned non-zero exit status 1...
>>> VLCCMD[0] = "does-not-exist"
>>> runE("play x.mkv") # doctest: +ELLIPSIS
Playing x.mkv ...
RUN does-not-exist vlc --fullscreen --play-and-exit -- .../media/x.mkv
Error: could not play file 'x.mkv': No such file or directory: 'does-not-exist'

>>> MPVCMD[0] = "false"
>>> runE("play --mpv x.mkv") # doctest: +ELLIPSIS
Playing x.mkv ...
RUN false mpv --fullscreen -- .../media/x.mkv
Error: could not play file 'x.mkv': Command ... returned non-zero exit status 1...
>>> MPVCMD[0] = "does-not-exist"
>>> runE("play --mpv x.mkv") # doctest: +ELLIPSIS
Playing x.mkv ...
RUN does-not-exist mpv --fullscreen -- .../media/x.mkv
Error: could not play file 'x.mkv': No such file or directory: 'does-not-exist'


Tests
=====

Check some _assert()s
---------------------

>>> def dbc(**db): _db_check(Path("x.json"), "/some/dir", db)
>>> dbc()
Traceback (most recent call last):
  ...
MError: x.json has wrong key(s)
>>> dbc(dir = None, files = None, oops = 1)
Traceback (most recent call last):
  ...
MError: x.json has wrong key(s)
>>> dbc(dir = "/some/other/dir", files = None)
Traceback (most recent call last):
  ...
MError: x.json has wrong dir
>>> dbc(dir = "/some/dir", files = { "/some/file": 0 })
Traceback (most recent call last):
  ...
MError: x.json has wrong files value(s)
>>> dbc(dir = "/some/dir", files = { "/some/file": -7 })
Traceback (most recent call last):
  ...
MError: x.json has wrong files value(s)
>>> dbc(dir = "/some/dir", files = { "/some/file": False })
Traceback (most recent call last):
  ...
MError: x.json has wrong files value(s)
>>> dbc(dir = "/some/dir", files = { "/some/file": None })
Traceback (most recent call last):
  ...
MError: x.json has wrong files value(s)

>>> _cfg_check(dict(x = 99))
Traceback (most recent call last):
  ...
MError: config.json has unexpected key(s)
>>> _cfg_check(dict(show_hidden = 1))
Traceback (most recent call last):
  ...
MError: config.json has unexpected value(s)
>>> _cfg_check(dict(player = "oops"))
Traceback (most recent call last):
  ...
MError: config.json has unexpected value(s)


Check some Python weirdness
---------------------------

>>> _state_in_db(SKIP)
'skip'
>>> _state_in_db(DONE)
'done'
>>> _state_in_db(42)
'playing'
>>> _state_in_db(1)
'playing'

>>> db_t({}, "foo") is None
True
>>> db_t(dict(foo = SKIP), "foo") is None
True
>>> db_t(dict(foo = DONE), "foo") is None
True
>>> db_t(dict(foo = 42), "foo")
42
>>> db_t(dict(foo = 1), "foo")
1
"""
                                                                # }}}1

import argparse, contextlib, datetime, errno, functools, inspect, \
       hashlib, io, json, pty, os, re, subprocess, sys, textwrap, \
       urllib

from collections import defaultdict
from pathlib import Path

__version__   = "0.4.1"

DESC          = "m - minimalistic media manager"

HOME          = Path.home()                                     # dyn
CFG           = ".obfusk-m"                     # use git?! -> sync?!
CFGFILE       = "config.json"
VLCQT         = ".config/vlc/vlc-qt-interface.conf"
KODIDB        = ".kodi/userdata/Database/MyVideos107.db"

EXTS          = ".avi .m4v .mkv .mp4 .ogv .webm".split()        # TODO
CONT_BACK     = 5                                               # TODO
END_SECS      = 5                                               # TODO
PLAYER        = "vlc"

NOFILES       = "No files to play."
IMPORTED      = "Imported {} file(s) in {} dir(s)."
IGNORE_UNK    = "Ignoring unknown file '{}'."
IGNORE_NODIR  = "Ignoring nonexistent directory '{}'."

VLCCMD        = "vlc --fullscreen --play-and-exit".split()      # dyn
VLCCONT       = lambda t: ["--start-time", str(int(t))]

MPVCMD        = "mpv --fullscreen".split()                      # dyn
MPVCONT       = lambda t: ["--start=" + str(int(t))]

STATES        = "skip done playing new".split()
INFOCH        = "*x> "
INFOCO        = "cya grn red blu".split()
INFOCHAR      = dict(zip(STATES, INFOCH))
INFOCHAR_L    = dict(INFOCHAR, new = "!")
INFOCOLOUR_L  = dict(zip(STATES, INFOCO))
INFOCOLOUR    = dict(INFOCOLOUR_L, new = None)

FILESPEC      = re.compile(r"all|(\d+(-\d+)?,)*(\d+(-\d+)?)")

STDOUT_TTY    = sys.stdout.isatty()
USE_SAFE      = STDOUT_TTY                                      # dyn

SHOW_HIDDEN   = False                 # NB: dyn by --[no-]show-hidden
USE_COLOUR    = STDOUT_TTY            # NB: dyn by --[no-]colour
IGNORECASE    = False                 # NB: dyn by --[no-]ignorecase
NUMERICSORT   = False                 # NB: dyn by --[no-]numeric-sort

STDERR        = sys.stderr

SKIP, DONE, UNMARK = -1, True, False  # NB: True == 1

EPILOG = textwrap.dedent("""
  NB: FILE is a file name, state or number(s);
  e.g. '1', '1-5', '1,4-7', 'playing', 'new' or 'all'.

  NB: file numbers may change when --ignorecase or --numeric-sort is used;
  please use the same sort order when listing and using numbers.

  See README.md for additional information and examples.
""")

RX_EPILOG = textwrap.dedent("""
  See https://docs.python.org/3/library/re.html#regular-expression-syntax
  for the Python regular expression syntax.

  NB: --replace and --replace-all can be used multiple times to do
  multiple substitutions; choose your substitutions carefully so they
  don't inadvertently affect each other; each --replace runs before
  each --replace-all.
""")

ALIAS = textwrap.dedent("""
  Make the current directory an alias for another DIR already in the
  DB; use this when you want to share the same database entry for
  different paths that resolve to the same canonical path (e.g. via
  symlinks).
""")

class MError(RuntimeError): pass

def handle_broken_pipe(f):                                      # {{{1
  @functools.wraps(f)
  def g(*a, **k):
    try:
      return f(*a, **k)
    except BrokenPipeError:
      sys.exit(0)
  return g
                                                                # }}}1

# === main & related functions ===

# NB: dyn SHOW_HIDDEN, USE_COLOUR, IGNORECASE, NUMERICSORT, EXTS
# TODO: use threading.local?
def main(*args):                                                # {{{1
  d = db_cfg(); p = _argument_parser(d); n = p.parse_args(args)
  if n.subcommand == "_test": return _test(n.verbose)
  exts = set(d.get("exts", EXTS)); exts.update(d.get("add_exts", ()))
  with dyn(globals(), SHOW_HIDDEN = n.show_hidden,
           USE_COLOUR = n.colour, IGNORECASE = n.ignorecase,
           NUMERICSORT = n.numeric_sort, EXTS = exts):
    dpath = cwd() / Path(n.dir) if n.dir else cwd()
    try:
      return do_something(n.f, dpath, n) or 0
    except MError as e:
      puts("Error:", str(e), file = sys.stderr)
      return 1
                                                                # }}}1

DO_ARGS   = "numbers only_indexed todo player filename target " \
            "flat zero only_files only_dirs quiet " \
            "sep replace replace_all include exclude".split()
CFG_ARGS  = dict(show_hidden = bool, colour = bool, ignorecase = bool,
                 numeric_sort = bool, numbers = bool,
                 only_indexed = bool, player = None,
                 exts = list, add_exts = list)
          # player --> PLAYERS.keys()

# NB: uses SHOW_HIDDEN, USE_COLOUR, IGNORECASE, NUMERICSORT as defaults
def _argument_parser(d = {}):                                   # {{{1
  p = argparse.ArgumentParser(description = DESC, epilog = EPILOG,
        formatter_class = argparse.RawDescriptionHelpFormatter)
  p.add_argument("--version", action = "version",
                 version = "%(prog)s {}".format(__version__))
  p.add_argument("--dir", "-d", metavar = "DIR",
                 help = "use DIR instead of $PWD")

  g1 = p.add_mutually_exclusive_group()
  g1.set_defaults(show_hidden = d.get("show_hidden", SHOW_HIDDEN))
  g1.add_argument("--show-hidden", action = "store_true",
                  help = "show hidden (i.e. starting with .) "
                         "files & dirs")
  g1.add_argument("--no-show-hidden", action = "store_false",
                  dest = "show_hidden")

  c  = d.get("colour"); colour = c if c is not None else USE_COLOUR
  g2 = p.add_mutually_exclusive_group()
  g2.set_defaults(colour = colour)
  g2.add_argument("--colour", action = "store_true",
                  help = "use coloured output "
                         "(the default when stdout is a tty)")
  g2.add_argument("--no-colour", action = "store_false",
                  dest = "colour")
  g2.add_argument("--auto-colour", action = "store_const",
                  dest = "colour", const = None)

  g3 = p.add_mutually_exclusive_group()
  g3.set_defaults(ignorecase = d.get("ignorecase", IGNORECASE))
  g3.add_argument("--ignorecase", "-i", action = "store_true",
                  help = "ignore case when sorting files & dirs")
  g3.add_argument("--no-ignorecase", action = "store_false",
                  dest = "ignorecase")

  g4 = p.add_mutually_exclusive_group()
  g4.set_defaults(numeric_sort = d.get("numeric_sort", NUMERICSORT))
  g4.add_argument("--numeric-sort", "-N", action = "store_true",
                  help = "sort files & dirs numerically")
  g4.add_argument("--no-numeric-sort", action = "store_false",
                  dest = "numeric_sort")

  s = p.add_subparsers(title = "subcommands", dest = "subcommand")
  s.required = True           # https://bugs.python.org/issue9253

  p_list    = _subcommand(s, "list l ls"    , "list files",
                          do_list_dir_files)
  p_list_d  = _subcommand(s, "list-dirs ld" , "list directories",
                          do_list_dir_dirs)
  p_list_a  = _subcommand(s, "list-all la",
                          "list directories & files",
                          do_list_dir_all)

  p_next    = _subcommand(s, "next n continue cont c",
                          "play (or continue) next (playing/new) file",
                          do_play_next)
  p_next_n  = _subcommand(s, "next-new nn", "play next new file",
                          do_play_next_new)
  p_play    = _subcommand(s, "play p"     , "play FILE",
                          do_play_file)

  p_mark    = _subcommand(s, "mark m"     , "mark FILE as done",
                          do_mark_file)
  p_unmark  = _subcommand(s, "unmark u"   , "mark FILE as new",
                          do_unmark_file)
  p_skip    = _subcommand(s, "skip s"     , "mark FILE as skip",
                          do_skip_file)

  easteregg = " 禁書目録" if os.environ.get("EASTEREGG") else ""
  p_index   = _subcommand(s, "index i" + easteregg,
                          "index current directory",
                          do_index_dir)
  p_alias   = _subcommand(s, "alias", "alias directory", do_alias_dir)

  p_playing = _subcommand(s, "playing", "list files marked as playing",
                          do_playing_files)
  p_watched = _subcommand(s, "watched", "list files marked as done",
                          do_watched_files)
  p_skipped = _subcommand(s, "skipped", "list files marked as skip",
                          do_skipped_files)

  p_todo    = _subcommand(s, "todo unfinished",
                          "list directories with files marked as "
                          "playing or new",
                          do_todo_dirs)

  p_dbfile  = _subcommand(s, "db-file", "print path to DB file",
                          do_dbfile)

  p_imp_w   = _subcommand(s, "import-watched",
                          "import watched data from stdin: "
                          "each line is a file path",
                          do_import_watched)
  p_imp_p   = _subcommand(s, "import-playing",
                          "import playing data from stdin: each line "
                          "is a file path (+ separator) + time",
                          do_import_playing)
  p_kodi_w  = _subcommand(s, "kodi-import-watched",
                          "import watched data from kodi",
                          do_kodi_import_watched)
  p_kodi_p  = _subcommand(s, "kodi-import-playing",
                          "import playing data from kodi",
                          do_kodi_import_playing)
  p_kodi_ws = _subcommand(s, "kodi-watched-sql",
                          "print SQL for getting watched data from kodi",
                          do_kodi_watched_sql)
  p_kodi_ps = _subcommand(s, "kodi-playing-sql",
                          "print SQL for getting playing data from kodi",
                          do_kodi_playing_sql)

  p_ex      = _subcommand(s, "examples",
                          "show some examples from the tests",
                          do_examples)

  p_test    = s.add_parser("_test")
  p_test.add_argument("--verbose", "-v", action = "store_true")

  for x in [p_list, p_list_a]:
    g = x.add_mutually_exclusive_group()
    g.set_defaults(numbers = d.get("numbers"))
    g.add_argument("--numbers", "-n", action = "store_true",
      help = "show numbers (which can be used for mark etc.)")
    g.add_argument("--no-numbers", action = "store_false",
                   dest = "numbers")
  for x in [p_list_d, p_list_a]:
    g = x.add_mutually_exclusive_group()
    g.set_defaults(only_indexed = d.get("only_indexed"))
    g.add_argument("--only-indexed", "-x", action = "store_true",
                   help = "only show indexed directories")
    g.add_argument("--no-only-indexed", action = "store_false",
                   dest = "only_indexed")
    if x is p_list_d:
      g.add_argument("--todo", "-t", action = "store_true",
                     help = "only show indexed directories with "
                            "files marked as playing or new")

  for x in [p_next, p_next_n, p_play]:
    g = x.add_mutually_exclusive_group()
    g.set_defaults(player = d.get("player", PLAYER))
    g.add_argument("--mpv", action = "store_const", dest = "player",
      const = "mpv", help = "play using mpv")
    g.add_argument("--vlc", action = "store_const", dest = "player",
      const = "vlc", help = "play using vlc (the default)")
  for x in [p_play, p_mark, p_unmark, p_skip]:
    x.add_argument("filename", metavar = "FILE")
  p_alias.add_argument("target", metavar = "DIR")
  for x in [p_playing, p_watched, p_skipped]:
    x.add_argument("--flat", action = "store_true",
      help = "flat list of files instead of grouped by directory")
    x.add_argument("--zero", action = "store_true",
      help = "zero-delimited (implies --flat) output "
             "(for e.g. xargs -0)")
  p_playing.add_argument("--only-files", action = "store_true",
                         help = "only print files, not times")
  p_todo.add_argument("--only-dirs", action = "store_true",
                      help = "only print directories, no info")
  p_unmark.add_argument("--quiet", "-q", action = "store_true",
    help = "do not print info about unknown files to stderr")
  p_todo  .add_argument("--quiet", "-q", action = "store_true",
    help = "do not print info about missing directories to stderr")

  for x in [p_imp_w, p_imp_p]:
    x.add_argument("--zero", action = "store_true",
      help = "zero-delimited input (from e.g. find -print0)")
  p_imp_p.set_defaults(sep = " ")
  p_imp_p.add_argument("--sep",
    help = "use SEP to separate path from time (instead of ' ')")
  for x in [p_kodi_w, p_kodi_p]:
    x.add_argument("--from", dest = "filename", metavar = "FILE",
                   help = "import from FILE (instead of ~/{})"
                          .format(KODIDB))
  for x in [p_imp_w, p_imp_p, p_kodi_w, p_kodi_p]:
    repl_help, repl_meta = """
      rename files: substitute the first occurence of REGEX in each
      file path with REPLACEMENT; NB: renaming is done after filtering
      (i.e. --include or --exclude)
    """, ("REGEX", "REPLACEMENT")
    g1 = x.add_mutually_exclusive_group()
    g1.set_defaults(replace = [], replace_all = [])
    g1.add_argument("--replace", nargs = 2, action = "append",
                    metavar = repl_meta, help = repl_help)
    g1.add_argument("--replace-all", nargs = 2, action = "append",
                    metavar = repl_meta,
      help = "rename file like --replace, but replace all occurences")
    g2 = x.add_mutually_exclusive_group()
    g2.add_argument("--include", metavar = "REGEX",
      help = "ignore files whose path does not match REGEX")
    g2.add_argument("--exclude", metavar = "REGEX",
      help = "ignore files whose path matches REGEX")

  return p
                                                                # }}}1

def _subcommand(s, names, desc, f, **kw):                       # {{{1
  name, *aliases = names.split(); help = desc
  if "import" in name:
    kw.update(epilog = RX_EPILOG,
              formatter_class = argparse.RawDescriptionHelpFormatter)
  if "alias" in name: desc = ALIAS
  p = s.add_parser(name, aliases = aliases, help = help,
                   description = desc, **kw)
  p.set_defaults(f = f)
  return p
                                                                # }}}1

# NB: dyn HOME, VLCCMD, MPVCMD, prompt_yn, COLOURS, USE_SAFE
def _test(verbose = False):                                     # {{{1
  global TEST_DIR, FAKE_HOME
  import doctest, tempfile
  m = None if __name__ == "__main__" else sys.modules[__name__]
  with tempfile.TemporaryDirectory() as tdir:
    TEST_DIR = Path(tdir); FAKE_HOME = TEST_DIR / "home"
    with dyn(globals(), HOME = FAKE_HOME, VLCCMD = ["true"] + VLCCMD,
             MPVCMD = ["true"] + MPVCMD, prompt_yn = lambda _: True,
             COLOURS = { k:k.upper() for k in COLOURS },
             USE_SAFE = True):
      failures, _tests = doctest.testmod(m, verbose = verbose)
      return 0 if failures == 0 else 1
                                                                # }}}1

def do_something(f, dpath, ns):                                 # {{{1
  if not dpath.is_dir():
    raise MError("'{}' is not an (existing) directory".format(dpath))
  params  = inspect.signature(f).parameters
  kw      = { k:v for k,v in vars(ns).items()
                  if k in DO_ARGS and k in params }
  fs      = db_load(dpath)["files"] \
            if not list(params)[1].startswith("_") else None
  return f(dpath, fs, **kw)
                                                                # }}}1

# === do_* ===

@handle_broken_pipe
def do_list_dir_files(dpath, fs, numbers):                      # {{{1
  for i, (st, fn) in enumerate(dir_iter(dpath, fs)):
    infochar = clr(INFOCOLOUR[st], INFOCHAR[st])
    o, t     = ["["+infochar+"]", safe(fn)], db_t(fs, fn)
    if numbers: o = ["{:3d}".format(i+1)] + o
    if t      : o = o + [fmt_time(t)]
    print(*o)
                                                                # }}}1

def do_list_dir_dirs(dpath, _fs, only_indexed, todo = False):
  _list_dir_dirs(dir_iter_dirs(dpath), only_indexed, todo)

@handle_broken_pipe
def _list_dir_dirs(it, only_indexed = False, todo = False):     # {{{1
  for sd, p, n in it:
    if (only_indexed or todo) and None in [p, n]: continue
    if todo and not p+n: continue
    pl = _linfo(p, "playing", 1, p)
    ne = _linfo(n, "new"    , 2, n is not None)
    print("(" + pl + ne + ")", safe(sd))
                                                                # }}}1

def _linfo(n, st, w, c):
  if not c: return " "*(w+1)
  return clr(INFOCOLOUR_L[st] if n else "yll", str(n).rjust(w)) + \
         INFOCHAR_L[st]

def do_list_dir_all(dpath, fs, numbers, only_indexed):
  do_list_dir_dirs (dpath, fs, only_indexed)
  do_list_dir_files(dpath, fs, numbers)

def do_play_next(dpath, fs, player):
  fn = dir_next(dpath, fs)
  _play_file_if(dpath, fs, fn, player)

def do_play_next_new(dpath, fs, player):
  fn = dir_next(dpath, fs, skip = "skip done playing".split())
  _play_file_if(dpath, fs, fn, player)

def _play_file_if(dpath, fs, fn, player):
  if fn: play_file(dpath, fs, fn, player)
  else: print(NOFILES)

def do_play_file(dpath, fs, filename, player):
  for fn in _files_from_spec(dpath, fs, filename):
    play_file(dpath, fs, fn, player)

def do_mark_file(dpath, fs, filename):
  files = _files_from_spec(dpath, fs, filename)
  db_update(dpath, { fn: DONE for fn in files })

def do_unmark_file(dpath, fs, filename, quiet):                 # {{{1
  files   = _files_from_spec(dpath, fs, filename, must_exist = False)
  files_  = [ fn for fn in files if fn in fs ]
  if not quiet:
    for fn in sorted_(set(files) - set(files_)):
      puts(IGNORE_UNK.format(fn), file = sys.stderr)
  db_update(dpath, { fn: UNMARK for fn in files_ })
                                                                # }}}1

def do_skip_file(dpath, fs, filename):
  files = _files_from_spec(dpath, fs, filename)
  db_update(dpath, { fn: SKIP for fn in files })

def _files_from_spec(dpath, fs, spec, must_exist = True):       # {{{1
  if any( spec.lower().endswith(ext) for ext in EXTS ):
    return [check_filename(dpath, spec, must_exist)]
  elif spec in STATES or re.fullmatch(FILESPEC, spec):
    files = dir_files(dpath)
    if spec == "all": return files
    elif spec in STATES:
      return [ fn for fn in files if _state(fn, fs) == spec ]
    else:
      ret = set()
      for pt in spec.split(","):
        a, b = map(int, pt.split("-") if "-" in pt else [pt, pt])
        for x in [a, b]:
          if not 1 <= x <= len(files):
            raise MError("out of range: '{}'".format(x))
        ret |= set(files[a-1:b])
      return sorted_(ret)
  else:
    raise MError("not a valid file name or number: '{}'".format(spec))
                                                                # }}}1

def do_index_dir(dpath, _fs):
  db_update(dpath, {})

def do_alias_dir(dpath, _fs, target):                           # {{{1
  tpath       = Path(target)
  df_a, df_t  = db_dir_file(dpath), db_dir_file(tpath)
  if not tpath.is_dir():
    raise MError("'{}' is not an (existing) directory".format(tpath))
  if not tpath.is_absolute():
    raise MError("'{}' is a relative path".format(tpath))
  if dpath.resolve() != tpath.resolve():
    raise MError("'{}' and '{}' do not resolve to the same path"
                 .format(dpath, tpath))
  if     df_a.exists(): raise MError("'{}' already exists".format(df_a))
  if not df_t.exists(): raise MError("'{}' does not exist".format(df_t))
  df_a.symlink_to(df_t.name)
  puts(str(df_a), "->", str(df_t.name))
                                                                # }}}1

def do_playing_files(_dpath, _fs, flat, zero, only_files):
  _print_files_with_state("playing", flat, zero, not only_files)

def do_watched_files(_dpath, _fs, flat, zero):
  _print_files_with_state("done", flat, zero)

def do_skipped_files(_dpath, _fs, flat, zero):
  _print_files_with_state("skip", flat, zero)

@handle_broken_pipe
def _print_files_with_state(st, flat, zero, w_t = False):       # {{{1
  data = _files_with_state(st)
  for dpath_s in sorted_(data):
    if not (flat or zero): puts(dpath_s + ":")
    for fn, what in sorted_(data[dpath_s], key = lambda x: x[0]):
      x = str(Path(dpath_s) / fn) if flat or zero else "  " + fn
      s = safe(x) if not zero else x
      t = " " + fmt_time(what) if w_t else ""
      print(s + t, end = "\0" if zero else "\n")
                                                                # }}}1

def _files_with_state(st):                                      # {{{1
  data = defaultdict(list)
  for dpath_s, fs in db_dirs():
    for fn, what in fs.items():
      if _state_in_db(what) == st: data[dpath_s].append((fn, what))
  return data
                                                                # }}}1

@handle_broken_pipe
def do_todo_dirs(_dpath, _fs, only_dirs, quiet):                # {{{1
  data, nodir = {}, []
  for dpath_s, fs in db_dirs():
    dpath = Path(dpath_s)
    if not dpath.exists():
      nodir.append(dpath_s); continue
    count = _dir_count(dir_iter(dpath, fs))
    if count["playing"] + count["new"]:
      data[dpath_s] = (count["playing"], count["new"])
  if not quiet:
    for dpath_s in sorted_(nodir):
      puts(IGNORE_NODIR.format(dpath_s), file = sys.stderr)
  if only_dirs:
    for d in sorted_(data): puts(d)
  else:
    _list_dir_dirs( (d, *data[d]) for d in sorted_(data) )
                                                                # }}}1

def do_dbfile(dpath, _fs):
  puts(str(db_dir_file(dpath)))

def do_import_watched(_dpath, _fs, zero, replace, replace_all,
                      include, exclude):
  _import(replace, replace_all, include, exclude,
          map(Path, zlines(osep = "") if zero else _lines()))

def do_import_playing(_dpath, _fs, zero, sep, replace, replace_all,
                      include, exclude):
  _import(replace, replace_all, include, exclude,
          ( _time_line(line, sep)
            for line in (zlines(osep = "") if zero else _lines()) ))

def _lines(): return ( line.rstrip("\n") for line in sys.stdin )

def _time_line(line, sep):
  p, t = line.rsplit(sep, maxsplit = 1)
  return Path(p), s2secs(t) if ":" in t else int(t)

def _import(repl, repl_all, incl, excl, it, state = DONE):      # {{{1
  assert all( len(x) == 2 for x in repl     )
  assert all( len(x) == 2 for x in repl_all )
  data = defaultdict(dict)
  for x in it:
    if isinstance(x, Path):
      fp_, st = x, state
    else:
      fp_, t = x; st = int(t)
    assert isinstance(fp_, Path)
    fp_s = str(fp_)
    if incl and not re.search(incl, fp_s): continue
    if excl and     re.search(excl, fp_s): continue
    for rx, rp in repl:     fp_s = re.sub(rx, rp, fp_s, 1)      # !!!
    for rx, rp in repl_all: fp_s = re.sub(rx, rp, fp_s)
    fp = Path(fp_s); data[fp.parent][fp.name] = st
  for dpath, fs in data.items(): db_update(dpath, fs)
  print(IMPORTED.format(sum(map(len, data.values())), len(data)))
                                                                # }}}1

def do_kodi_import_watched(_dpath, _fs, filename, replace,
                           replace_all, include, exclude):
  _import(replace, replace_all, include, exclude,
          kodi_path_query(KODI_WATCHED_SQL, filename))

def do_kodi_import_playing(_dpath, _fs, filename, replace,
                           replace_all, include, exclude):
  _import(replace, replace_all, include, exclude,
          kodi_path_query(KODI_PLAYING_SQL, filename))

def do_kodi_watched_sql(_dpath, _fs):
  print(KODI_WATCHED_SQL.strip("\n"))

def do_kodi_playing_sql(_dpath, _fs):
  print(KODI_PLAYING_SQL.strip("\n"))

@handle_broken_pipe
def do_examples(_dpath, _fs):
  print(EXAMPLES)

# === dir_* ===

def dir_iter(dpath, fs):
  if fs is None: fs = db_load(dpath)["files"]
  for fn in dir_files(dpath): yield _state(fn, fs), fn

def _state(fn, fs):
  return _state_in_db(fs[fn]) if fn in fs else "new"

# NB: True == 1
def _state_in_db(what):
  return "playing" if type(what) is int and what > 0 \
    else { SKIP: "skip", DONE: "done" }[what]

def dir_iter_dirs(dpath):                                       # {{{1
  for sd in dir_dirs(dpath):
    if db_dir_file(dpath / sd).exists():
      count = _dir_count(dir_iter(dpath / sd, None))
      yield sd, count["playing"], count["new"]
    else:
      yield sd, None, None
                                                                # }}}1

def _dir_count(it):
  count = dict(playing = 0, new = 0)
  for st, _ in it:
    if st in count: count[st] += 1
  return count

def dir_next(dpath, fs, skip = "skip done".split()):
  for fn in dir_files(dpath):
    if _state(fn, fs) not in skip: return fn
  return None

def dir_dirs(dpath):
  return sorted_( x.name for x in _iterdir(dpath) if x.is_dir() )

def dir_files(dpath):
  return sorted_( x.name for x in _iterdir(dpath)
                  if x.is_file() and x.suffix.lower() in EXTS )

def _iterdir(dpath):
  return ( x for x in dpath.iterdir()
           if SHOW_HIDDEN or not x.name.startswith(".") )

# === db_* ===

def db_cfg():
  cf = HOME / CFG / CFGFILE
  if not cf.exists(): return {}
  with cf.open() as f: return _cfg_check(json.load(f))

def _cfg_check(cfg):                                            # {{{1
  _assert(CFGFILE + " has unexpected key(s)",
          set(cfg.keys()) <= set(CFG_ARGS.keys()))
  _assert(CFGFILE + " has unexpected value(s)",
          all( cfg[k] in v if isinstance(v, (tuple, list))
                           else type(cfg[k]) is v
               for k,v in CFG_ARGS.items() if k in cfg ))
  return cfg
                                                                # }}}1

# NB: files map to
#   * True      (done)
#   * int (>0)  (playing, seconds)
#   * int (-1)  (skip)
def db_load(dpath):
  df = db_dir_file(dpath)
  if not df.exists(): return dict(dir = str(dpath), files = {})
  with df.open() as f: return _db_check(df, dpath, json.load(f))

# TODO: use flock? backup?
def db_update(dpath, files):                                    # {{{1
  (HOME / CFG).mkdir(exist_ok = True)
  db  = db_load(dpath); dpath_, fs = Path(db["dir"]), db["files"]
  df  = db_dir_file(dpath_)
  fs_ = { k:v for k,v in {**fs, **files}.items() if v != UNMARK }
  db_ = _db_check(df, dpath_, dict(dir = str(dpath_), files = fs_))
  with df.open("w") as f:
    json.dump(db_, f, indent = 2, sort_keys = True)
    f.write("\n")
                                                                # }}}1

# NB: True == 1
def _db_check(df, dpath, db):                                   # {{{1
  _assert(str(df) + " has wrong key(s)",
          sorted(db.keys()) == "dir files".split())
  _assert(str(df) + " has wrong dir",
          db["dir"] == str(dpath) or
          (df.is_symlink() and df.resolve().name ==
                               db_dir_file(db["dir"]).name))
  _assert(str(df) + " has wrong files value(s)",
          all( x > 0 or x == SKIP if type(x) is int else x is DONE
               for x in db["files"].values() ))
  return db
                                                                # }}}1

# NB: max filename len = 255 > 5 + 200 + 2 + 40 + 5 = 252
def db_dir_file(dpath):
  d   = str(dpath)
  fn  = "dir__" + d.replace("/", "|")[:200] + "__" + \
        hashlib.sha1(d.encode()).hexdigest() + ".json"
  return HOME / CFG / fn

# NB: True == 1
def db_t(fs, fn):
  t = fs.get(fn)
  return t if type(t) is int and t > 0 else None

def db_dirs():
  for df in (HOME / CFG).glob("dir__*.json"):
    if df.is_symlink(): continue
    with df.open() as f: db = json.load(f)
    yield db["dir"], db["files"]

# === playing & vlc & mpv ===

# TODO
def play_file(dpath, fs, fn, player = None):                    # {{{1
  t     = db_t(fs, fn); t_ = max(0, t - CONT_BACK) if t else 0
  etc   = "from " + fmt_time(t) + " " if t else ""
  puts("Playing", fn, etc + "...")
  try:
    t2 = PLAYERS[player or PLAYER](str(dpath / fn), t_)
  except (subprocess.CalledProcessError, FileNotFoundError) as e:
    msg = e.strerror if hasattr(e, "strerror") else str(e)
    raise MError("could not play file '{}': {}".format(fn, msg))
  db_update(dpath, { fn: t2 })
                                                                # }}}1

# TODO: error handling? --no-prompt?!
# NB: we unfortunately can't tell the difference between a file that
# has played completely and one that has played very little, so we
# need to prompt :(
# NB: True == 1
def vlc_play(fp, t = None):
  cmd = VLCCMD + (VLCCONT(t) if t else []) + ["--", fp]
  puts("RUN", *cmd); subprocess.run(cmd, check = True)
  t_  = vlc_get_times().get(fp) or DONE
  return UNMARK if t_ is DONE and not prompt_yn("Done") else t_


# TODO: cleanup?
def vlc_get_times():                                            # {{{1
  if not (HOME / VLCQT).exists(): return {}
  with (HOME / VLCQT).open() as f:
    rec, l, t = False, None, None
    for line in ( line.strip() for line in f ):
      if line == "[RecentsMRL]": rec = True
      elif rec:
        if not line: break
        elif line.startswith("list="):
          l = [ urllib.parse.unquote(x[7:])
                for x in line[5:].split(", ")
                if x.startswith("file://") ]
        elif line.startswith("times="):
          t = [ max(0, int(x) // 1000) for x in line[6:].split(", ") ]
    if l is None or t is None: return {}
    return dict(zip(l, t))
                                                                # }}}1

_VLC_TEST_CFG = """
[RecentsMRL]
list=file://{}, file://{}, file://{}, file://{}
times=0, 0, 121666, 246135
"""

# TODO: error handling? no TEST_DIR?
# NB: currently tests for TEST_DIR to see if we're testing so it can
# suppress and replace output.
def mpv_play(fp, t = None):                                     # {{{1
  cmd     = MPVCMD + (MPVCONT(t) if t else []) + ["--", fp]
  testing = "TEST_DIR" in globals()   # oh well
  puts("RUN", *cmd)
  b       = _pty_run(cmd, testing)[0]
  if testing: b = _MPV_TEST_OUT.format(fp).encode()
  x       = b[b.rindex(b"AV:"):b.rindex(b"A-V:")][4:-1]
  a, b    = x.split(b" / "); c = b.split()[0]
  t_, tot = s2secs(a.decode()), s2secs(c.decode())
  return t_ or UNMARK if t_ + END_SECS < tot else DONE
                                                                # }}}1

def _pty_run(cmd, testing = False, bufsize = 1024):             # {{{1
  buf, pid = b"", os.getpid()
  def read(fd):
    nonlocal buf
    data = os.read(fd, 1024); buf = (buf + data)[-bufsize:]
    return data if not testing else b"\r"
  try:
    retcodesig = pty.spawn(cmd, read)
  except OSError as e:
    if os.getpid() != pid:
      print("*** CHILD exec() FAILED ***", file = STDERR)
      print(e.__class__.__name__, e, file = STDERR)
      os._exit(127)
    else: raise
  retcode, signal = retcodesig >> 8, retcodesig & 0xff
  if retcode == 127 and b"*** CHILD exec() FAILED ***" in buf \
                    and b"FileNotFoundError" in buf:
    e = FileNotFoundError(errno.ENOENT,
          "No such file or directory: '{}'".format(cmd[0]))
    e.filename = cmd[0]
    raise e
  if retcode: raise subprocess.CalledProcessError(retcode, cmd)
  return buf, -signal or retcode
                                                                # }}}1

_MPV_TEST_OUT = """
Playing: {}
 (+) Video --vid=1 (*) (h264 1920x1080 23.810fps)
 (+) Audio --aid=1 --alang=jpn (*) (aac 2ch 44100Hz)
 (+) Subs  --sid=1 --slang=eng (*) (ass)
AO: [pulse] 44100Hz stereo 2ch float
VO: [opengl] 1920x1080 yuv420p
AV: 00:01:01 / 00:15:47 (6%) A-V:  0.000 Cache: 10s+56MB


Exiting... (Quit)
"""

PLAYERS             = dict(mpv = mpv_play, vlc = vlc_play)
CFG_ARGS["player"]  = tuple(PLAYERS.keys())

# === miscellaneous helpers ===

# TODO
def check_filename(dpath, fn, must_exist = True):               # {{{1
  p = dpath / Path(fn)
  try:
    r = p.relative_to(dpath)
  except ValueError as e:
    raise MError(*e.args)
  if len(r.parts) != 1:
    raise MError("'{}' is not a file in '{}'".format(p, dpath))
  if (must_exist or p.exists()) and not p.is_file():
    raise MError("'{}' is not a file".format(p))
  return p.name
                                                                # }}}1

def fmt_time(secs): return str(datetime.timedelta(seconds = secs))

# NB: use $PWD instead of Path.cwd() since we might be in a symlinked
# directory in the shell we've been run from.  We could follow the
# symlinks instead but that creates other issues.  For now, make sure
# the cwd we see and the one in the shell (prompt) are the same.  That
# should work for most cases, and prevent issues when moving the
# symlink targets.  It's also consistent w/ kodi.
def cwd(): return Path(os.environ["PWD"])

def safe(s):
  return "".join( c if c.isprintable() else "?" for c in s ) \
    if USE_SAFE else s

def puts(*ss, **kw): print(*map(safe, ss), **kw)

def _assert(msg, cond):
  if not cond: raise MError(msg)

def compose(f, g): return lambda x: f(g(x))
def idf(x): return x

def sorted_(xs, key = idf, **kw):
  k = idf
  if IGNORECASE:  k = compose(lambda s: s.lower(), k)
  if NUMERICSORT: k = compose(_num_key, k)
  return sorted(xs, key = compose(lambda x: (k(x), x), key), **kw)

def _num_key(s): return [ float(x) if re.fullmatch(NUMRX, x) else x
                          for x in re.split(NUMRX, s) ]

NUMRX = re.compile(r"(\d+(?:\.\d+)?)")

def s2dt(s): return datetime.datetime.strptime(s, "%H:%M:%S")
def s2secs(s): return (s2dt(s) - s2dt("00:00:00")).seconds

# === kodi ===

def kodi_query(sql, filename = None):                           # {{{1
  import sqlite3
  conn = sqlite3.connect(filename or str(HOME / KODIDB))
  try:
    c = conn.cursor(); c.execute(sql)
    for row in c: yield row
  finally:
    conn.close()
                                                                # }}}1

# NB: first element in row must be a path
def kodi_path_query(sql, filename = None):
  for row in kodi_query(sql, filename):
    p = Path(row[0])
    yield p if len(row) == 1 else (p, *row[1:])

KODI_WATCHED_SQL = """
select p.strPath || f.strFileName as fp
  from files f
  join path p on p.idPath = f.idPath
  where playCount > 0
  order by fp;
"""

KODI_PLAYING_SQL = """
select p.strPath || f.strFileName as fp, b.timeInSeconds
  from bookmark b
  join files f on f.idFile = b.idFile
  join path p on p.idPath = f.idPath
  where b.type = 1 -- resume
  order by fp;
"""

# === colours ===

COLOURS = dict(                                                 # dyn
  non = "\033[0m"   , red = "\033[0;31m", grn = "\033[0;32m",
  yll = "\033[1;33m", blu = "\033[0;34m", pur = "\033[0;35m",
  cya = "\033[0;36m", whi = "\033[1;37m"
)

def clr(c, s):
  return COLOURS[c]+s+COLOURS["non"] if USE_COLOUR and c else s

# === prompting ===

if sys.version_info.major >= 3:
  def prompt(s): return input(s + "? ")

def prompt_yn(s):                                               # dyn
  return not prompt(s + " [Yn]").lower().startswith("n")

# === dynamic vars ===

@contextlib.contextmanager
def dyn(d, **kw):                                               # {{{1
  """
  Pseudo-dynamic variables.

  >>> SOME_VAR = 42
  >>> with dyn(vars(), SOME_VAR = 37): SOME_VAR
  37
  >>> SOME_VAR
  42

  >>> import threading
  >>> D = threading.local()
  >>> D.x, D.y = 1, 2
  >>> with dyn(vars(D), x = 3, y = 4): (D.x, D.y)
  (3, 4)
  >>> (D.x, D.y)
  (1, 2)
  """

  old = { k:d[k] for k in kw }
  try:
    d.update(kw)
    yield
  finally:
    d.update(old)
                                                                # }}}1

# === null-byte-separated files ===

def zlines(f = None, sep = "\0", osep = None, size = 8192):     # {{{1
  """File iterator that uses alternative line terminators."""
  if f is None: f = sys.stdin
  if osep is None: osep = sep
  buf = ""
  while True:
    chars = f.read(size)
    if not chars: break
    buf += chars; lines = buf.split(sep); buf = lines.pop()
    for line in lines: yield line + osep
  if buf: yield buf
                                                                # }}}1

# === stdio ===

@contextlib.contextmanager
def stdin_from(f):                                              # {{{1
  if isinstance(f, str): f = io.StringIO(f)
  old_stdin, sys.stdin = sys.stdin, f
  try:
    yield
  finally:
    sys.stdin = old_stdin
                                                                # }}}1

# === examples s/// ===

_EXAMPLES_REPL = [                                              # {{{1
  (r'\s*# doctest:.*'                     , ""                      ),
  (r'(>>> runO.*)'                        , r"\1 # > string"        ),
  (r'>>> runI\(([^,]*), r?"([^"]*)"\)'    , r"$ m \2 # < \1"        ),
  (r'>>> run\w*\("([^"]*)"(?:, (.*))?\)'  , r"$ m \1 # \2"          ),
  (r'\$ m (.*) # d = d / "([^"]*)"'       , r"$ m -d \2 \1"         ),
  (r'\$ m (.*), x = \[d / "([^"]*)"\]'    , r"$ m \1 /.../\2"       ),
  (r'\$ m (.*) # c = True'                , r"$ m --colour \1"      ),
  (r'\$ m (.*) # c = None'                , r"$ m --colour-auto \1" ),
  (r'\s*#\s*$'                            , ""                      ),
  (r'\s*#  #'                             , " #"                    ),
  (r'<BLANKLINE>'                         , ""                      ),
  (r'(--replace) (\S+) (\S+)'             , r"\1 '\2' '\3'"         ),
  (r'RUN true'                            , "RUN"                   ),
]                                                               # }}}1

def _examples():                                                # {{{1
  s = __doc__
  i = s.index("First, set up some test data")
  j = s.index("Now, run some examples")
  s = s[:i] + s[j:]
  k = s.index("Tests\n=====")
  s = s[:k]
  for rx, rp in _EXAMPLES_REPL: s = re.sub(rx, rp, s, flags = re.M)
  return s.strip("\n")
                                                                # }}}1

EXAMPLES = _examples()

# === entry point ===

def main_():
  """Entry point for main program."""
  return main(*sys.argv[1:])

if __name__ == "__main__":
  sys.exit(main_())

# vim: set tw=70 sw=2 sts=2 et fdm=marker :
