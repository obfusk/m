#!/usr/bin/python3
# encoding: utf-8

# --                                                            ; {{{1
#
# File        : m.py
# Maintainer  : Felix C. Stegerman <flx@obfusk.net>
# Date        : 2017-12-09
#
# Copyright   : Copyright (C) 2017  Felix C. Stegerman
# Version     : v0.1.1
# License     : GPLv3+
#
# --                                                            ; }}}1

                                                                # {{{1
r"""
m - minimalistic media manager

See README.md for a description and some examples.

Examples
========

First, set up some test data
----------------------------

NB: tests must be run from _test()!  Otherwise the temporary directory
and monkey-patching are not available.

>>> if "TEST_DIR" not in globals():
...   raise KeyboardInterrupt("*** ABORT ***")

>>> d             = TEST_DIR / "media"
>>> x, y, z, a, b = d / "x.mkv", d / "y.mkv", d / "z.mkv", \
...                 d / "more/a.mkv", d / "more/b.mkv"

>>> for _d in [d, d / "more", FAKE_HOME, FAKE_HOME / CFG]: _d.mkdir()
>>> for _f in [x, y, z, a, b]: _f.touch()
>>> (FAKE_HOME / VLCQT).parent.mkdir(parents = True)

>>> _ = (FAKE_HOME / VLCQT).write_text('''
... [RecentsMRL]
... list=file://{}, file://{}, file://{}, file://{}
... times=0, 0, 121666, 246135
... '''.format(x, y, z, a))
>>> vlc_get_times() == { str(x): 0, str(y): 0, str(z): 121,
...                      str(a): 246 }
True


Now, run some examples
----------------------

NB: coloured output escapes are replaced by RED, NON etc. during test.

>>> def run(a, d = d, c = False):
...   main("--colour" if c else "--no-colour", "-d", str(d), *a.split())

>>> run("ls")
[ ] x.mkv
[ ] y.mkv
[ ] z.mkv
>>> run("mark x.mkv")
>>> run("skip y.mkv")
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
>>> run("mark z.mkv")
>>> run("next")
No files to play.
>>> run("unmark x.mkv")
>>> run("unmark y.mkv")
>>> run("ls")
[ ] x.mkv
[ ] y.mkv
[x] z.mkv

>>> run("ld")
(     ) more
>>> run("index", d = d / "more")
>>> run("ld")
(   2!) more
>>> run("ls", d = d / "more")
[ ] a.mkv
[ ] b.mkv
>>> run("play a.mkv", d = d / "more") # doctest: +ELLIPSIS
Playing a.mkv ...
RUN true vlc --fullscreen --play-and-exit -- .../media/more/a.mkv
>>> run("mark b.mkv", d = d / "more")
>>> run("la")
(1> 0!) more
[ ] x.mkv
[ ] y.mkv
[x] z.mkv
>>> run("ld", c = True)
(RED1NON>WHI 0NON!) more
>>> run("unmark b.mkv", d = d / "more")
>>> run("ld", c = True)
(RED1NON>YLL 1NON!) more

>>> (d / "un\033safe\x01file.mkv").touch()
>>> (d / "unsafe\ndir").mkdir()

>>> run("ls")
[ ] un?safe?file.mkv
[ ] x.mkv
[ ] y.mkv
[x] z.mkv
>>> run("ld")
(1> 1!) more
(     ) unsafe?dir
>>> run("play un\033safe\x01file.mkv") # doctest: +ELLIPSIS
Playing un?safe?file.mkv ...
RUN true vlc --fullscreen --play-and-exit -- .../media/un?safe?file.mkv
"""
                                                                # }}}1

import argparse, datetime, hashlib, json, os, subprocess, sys, urllib

from collections import defaultdict
from pathlib import Path

__version__   = "0.1.1"

DESC          = "m - minimalistic media manager"

HOME          = Path.home()
CFG           = ".obfusk-m"                     # use git?! -> sync?!
VLCQT         = ".config/vlc/vlc-qt-interface.conf"
KODIDB        = ".kodi/userdata/Database/MyVideos107.db"

EXTS          = ".avi .m4v .mkv .mp3 .mp4 .ogg .ogv".split()    # TODO
CONT_BACK     = 5                                               # TODO

VLCCMD        = "vlc --fullscreen --play-and-exit".split()
VLCCONT       = lambda t: ["--start-time", str(int(t))]

INFOS, INFOCH = "skip done playing new".split(), "*x> "
INFOCO        = "cya grn red yll".split()
INFOCHAR      = dict(zip(INFOS, INFOCH))
INFOCHAR_L    = dict(INFOCHAR, new = "!")
INFOCOLOUR_L  = dict(zip(INFOS, INFOCO))
INFOCOLOUR    = dict(INFOCOLOUR_L, new = None)

# === main & related functions ===

# NB: sets USE_COLOUR
def main(*args):                                                # {{{1
  global USE_COLOUR
  p = _argument_parser(); n = p.parse_args(args)
  a = [n.file] if hasattr(n, "file") else []
  if n.subcommand == "_test": return _test(n.verbose)
  if n.colour is not None: USE_COLOUR = n.colour
  return do_something(n.f, Path(n.dir) if n.dir else cwd(), a) or 0
                                                                # }}}1

def _argument_parser():                                         # {{{1
  p = argparse.ArgumentParser(description = DESC)
  p.add_argument("--version", action = "version",
                 version = "%(prog)s {}".format(__version__))
  p.add_argument("--dir", "-d", metavar = "DIR",
                 help = "use DIR instead of $PWD")

  g = p.add_mutually_exclusive_group()
  p.set_defaults(colour = None)
  g.add_argument("--colour", action = "store_true",
                 help = "use coloured output "
                        "(the default when stdout is a tty)")
  g.add_argument("--no-colour", "--nocolour",
                 action = "store_false", dest = "colour",
                 help = "do not use coloured output")

  s = p.add_subparsers(title = "subcommands", dest = "subcommand")
  s.required = True           # https://bugs.python.org/issue9253

  p_list    = s.add_parser("list", aliases = "l ls".split(),
                           help = "list files")
  p_list_d  = s.add_parser("list-dirs", aliases = ["ld"],
                           help = "list directories")
  p_list_a  = s.add_parser("list-all", aliases = ["la"],
                           help = "list directories & files")
  p_next    = s.add_parser("next", aliases = ["n"],
                           help = "play next file")
  p_play    = s.add_parser("play", aliases = ["p"],
                           help = "play FILE")
  p_mark    = s.add_parser("mark", aliases = ["m"],
                           help = "mark FILE as done")
  p_unmark  = s.add_parser("unmark", aliases = ["u"],
                           help = "mark FILE as new")
  p_skip    = s.add_parser("skip", aliases = ["s"],
                           help = "mark FILE as skip")
  p_index   = s.add_parser("index", aliases = ["i"],
                           help = "index current directory")
  p_kodi_w  = s.add_parser("kodi-import-watched",
                           help = "import watched data from kodi")
  p_kodi_p  = s.add_parser("kodi-import-playing",
                           help = "import playing data from kodi")

  p_test    = s.add_parser("_test")
  p_test.add_argument("--verbose", "-v", action = "store_true")

  p_list    .set_defaults(f = do_list_dir_files)
  p_list_d  .set_defaults(f = do_list_dir_dirs)
  p_list_a  .set_defaults(f = do_list_dir_all)
  p_next    .set_defaults(f = do_play_next)
  p_play    .set_defaults(f = do_play_file)
  p_mark    .set_defaults(f = do_mark_file)
  p_unmark  .set_defaults(f = do_unmark_file)
  p_skip    .set_defaults(f = do_skip_file)
  p_index   .set_defaults(f = do_index_dir)
  p_kodi_w  .set_defaults(f = do_kodi_import_watched)
  p_kodi_p  .set_defaults(f = do_kodi_import_playing)

  for x in [p_play, p_mark, p_unmark, p_skip]:
    x.add_argument("file", metavar = "FILE")

  return p
                                                                # }}}1

# NB: monkey-patches HOME, VLCCMD, prompt_yn, COLOURS!
def _test(verbose = False):                                     # {{{1
  import doctest, tempfile
  global FAKE_HOME, TEST_DIR, HOME, VLCCMD, prompt_yn, COLOURS
  old = HOME, VLCCMD, prompt_yn, COLOURS
  try:
    with tempfile.TemporaryDirectory() as tdir:
      TEST_DIR  = Path(tdir)
      FAKE_HOME = HOME = TEST_DIR / "home"
      VLCCMD    = ["true"] + VLCCMD
      prompt_yn = lambda _: True
      COLOURS   = { k: k.upper() for k in COLOURS }
      m = None if __name__ == "__main__" else sys.modules[__name__]
      failures, _tests = doctest.testmod(m, verbose = verbose)
  finally:
    HOME, VLCCMD, prompt_yn, COLOURS = old
  return 0 if failures == 0 else 1
                                                                # }}}1

def do_something(f, d, args):
  return f(d, db_load(d)["files"], *args)

# === do_* ===

def do_list_dir_files(d, fs):                                   # {{{1
  for st, f in dir_iter(d, fs):
    infochar = clr(INFOCOLOUR[st], INFOCHAR[st])
    o, t     = ["["+infochar+"]", safe(f)], db_t(fs, f)
    if t: o.append(fmt_time(t))
    print(*o)
                                                                # }}}1

def do_list_dir_dirs(d, _fs):
  for sd, p, n in dir_iter_dirs(d):
    pl = _linfo(p, "playing", 1, p)
    ne = _linfo(n, "new"    , 2, n is not None)
    print("(" + pl + ne + ")", safe(sd))

def _linfo(n, st, w, c):
  if not c: return " "*(w+1)
  return clr(INFOCOLOUR_L[st] if n else "whi", str(n).rjust(w)) + \
         INFOCHAR_L[st]

def do_list_dir_all(d, fs):
  do_list_dir_dirs(d, fs)
  do_list_dir_files(d, fs)

def do_play_next(d, fs):
  f = dir_next(d, fs)
  if f: play_file(d, fs, f)
  else: print("No files to play.")

def do_play_file(d, fs, filename):
  f = check_filename(d, filename)
  play_file(d, fs, f)

def do_mark_file(d, _fs, filename):
  f = check_filename(d, filename)
  db_update(d, { f: True })

def do_unmark_file(d, _fs, filename):
  f = check_filename(d, filename)
  db_update(d, { f: False })

def do_skip_file(d, _fs, filename):
  f = check_filename(d, filename)
  db_update(d, { f: -1 })

def do_index_dir(d, _fs):
  db_update(d, {})

def do_kodi_import_watched(_d, _fs):
  data = defaultdict(dict)
  for p, name in kodi_path_query(KODI_WATCHED_SQL):
    data[p][name] = True
  for d, fs in data.items(): db_update(d, fs)

def do_kodi_import_playing(_d, _fs):
  data = defaultdict(dict)
  for p, name, t in kodi_path_query(KODI_PLAYING_SQL):
    data[p][name] = int(t)
  for d, fs in data.items(): db_update(d, fs)

# === dir_* ===

def dir_iter(d, fs = None):
  if fs is None: fs = db_load(d)["files"]
  info = { True: "done", -1: "skip" }
  for f in dir_files(d):
    yield info.get(fs[f], "playing") if f in fs else "new", f

def dir_iter_dirs(d):                                           # {{{1
  for sd in dir_dirs(d):
    if db_dir_file(d / sd).exists():
      info = dict(playing = 0, new = 0)
      for x,_ in dir_iter(d / sd):
        if x in info: info[x] += 1
      yield sd, info["playing"], info["new"]
    else:
      yield sd, None, None
                                                                # }}}1

def dir_next(d, fs):
  for f in dir_files(d):
    if f not in fs or fs[f] not in [True, -1]: return f
  return None

def dir_dirs(dirname):
  return sorted( x.name for x in dirname.iterdir() if x.is_dir() )

def dir_files(dirname):
  return sorted( x.name for x in dirname.iterdir()
                 if x.is_file() and x.suffix.lower() in EXTS )

# === db_* ===

# NB: files map to
#   * True      (done)
#   * int (>0)  (playing, seconds)
#   * int (-1)  (skip)
def db_load(dirname):
  d = db_dir_file(dirname)
  if not d.exists(): return dict(dir = str(dirname), files = {})
  with d.open() as f: return _db_check(dirname, json.load(f))

# TODO: use flock? backup?
def db_update(dirname, files):                                  # {{{1
  (HOME / CFG).mkdir(exist_ok = True)
  fs  = db_load(dirname)["files"]
  fs_ = { k:v for k,v in {**fs, **files}.items() if v != False }
  db  = _db_check(dirname, dict(dir = str(dirname), files = fs_))
  with db_dir_file(dirname).open("w") as f:
    json.dump(db, f, indent = 2, sort_keys = True)
    f.write("\n")
                                                                # }}}1

def _db_check(dirname, db):                                     # {{{1
  assert sorted(db.keys()) == "dir files".split()
  assert db["dir"] == str(dirname)
  assert all( x == True or type(x) == int and (x > 0 or x == -1)
              for x in db["files"].values() )
  return db
                                                                # }}}1

# NB: max filename len = 255 > 5 + 200 + 2 + 40 + 5 = 252
def db_dir_file(dirname):
  d = str(dirname)
  x = "dir__" + d.replace("/", "|")[:200] + "__" + \
      hashlib.sha1(d.encode()).hexdigest() + ".json"
  return HOME / CFG / x

def db_t(fs, f):
  t = fs.get(f)
  return None if t in [True, -1] else t

# === playing & vlc ===

def play_file(d, fs, f):
  t = db_t(fs, f); etc = "from " + fmt_time(t) + " " if t else ""
  print("Playing", safe(f), etc + "...")
  t_ = vlc_play(d, f, t)
  db_update(d, { f: t_ })

# TODO: error handling? --noprompt?!
# NB: we unfortunately can't tell the difference between a file that
# has played completely and one that has played very little, so we
# need to prompt :(
def vlc_play(d, f, t = None):                                   # {{{1
  t_  = max(0, t - CONT_BACK) if t else 0
  cmd = VLCCMD + (VLCCONT(t_) if t_ else []) + ["--", str(d / f)]
  print("RUN", *map(safe, cmd)); subprocess.run(cmd, check = True)
  t2  = vlc_get_times().get(str(d / f)) or True
  return False if t2 == True and not prompt_yn("Done") else t2
                                                                # }}}1

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
    return dict(zip(l,t))
                                                                # }}}1

# === miscellaneous helpers ===

# TODO
def check_filename(d, f):                                       # {{{1
  p = d / Path(f); r = p.relative_to(d)
  if not p.is_file():
    raise ValueError("'{}' is not a file".format(p))
  if len(r.parts) != 1:
    raise ValueError("'{}' is not a file in '{}'".format(p, d))
  return p.name
                                                                # }}}1

def fmt_time(secs):
  return str(datetime.timedelta(seconds = secs))

# NB: use $PWD instead of Path.cwd() since we might be in a symlinked
# directory in the shell we've been run from.  We could follow the
# symlinks instead but that creates other issues.  For now, make sure
# the cwd we see and the one in the shell (prompt) are the same.  That
# should work for most cases, and prevent issues when moving the
# symlink targets.  It's also consistent w/ kodi.
def cwd(): return Path(os.environ["PWD"])

def safe(s):
  return "".join( c if c.isprintable() else "?" for c in s )

# === kodi ===

def kodi_query(sql):                                            # {{{1
  import sqlite3
  conn = sqlite3.connect(str(HOME / KODIDB))
  try:
    c = conn.cursor(); c.execute(sql)
    for row in c: yield row
  finally:
    conn.close()
                                                                # }}}1

# NB: first element in row must be a path
def kodi_path_query(sql):
  for row in kodi_query(sql):
    f = Path(row[0]); p, name = f.parent, f.name
    yield(p, name, *row[1:])

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

COLOURS = dict(
  non = "\033[0m"   , red = "\033[1;31m", grn = "\033[1;32m",
  yll = "\033[1;33m", blu = "\033[1;34m", pur = "\033[1;35m",
  cya = "\033[1;36m", whi = "\033[1;37m"
)

# NB: modified by --[no-]colour
# TODO: make dynamically scoped somehow?
USE_COLOUR = sys.stdout.isatty()

def clr(c, s):
  return COLOURS[c]+s+COLOURS["non"] if USE_COLOUR and c else s

# === prompting ===

if sys.version_info.major >= 3:
  def prompt(s): return input(s + "? ")

def prompt_yn(s):
  return not prompt(s + " [Yn]").lower().startswith("n")

# === entry point ===

def main_():
  """Entry point for main program."""
  return main(*sys.argv[1:])

if __name__ == "__main__":
  sys.exit(main_())

# vim: set tw=70 sw=2 sts=2 et fdm=marker :
