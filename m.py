#!/usr/bin/python3
# encoding: utf-8

# --                                                            ; {{{1
#
# File        : m.py
# Maintainer  : Felix C. Stegerman <flx@obfusk.net>
# Date        : 2017-12-16
#
# Copyright   : Copyright (C) 2017  Felix C. Stegerman
# Version     : v0.2.1
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

>>> (d / ".dotfile.mkv").touch()
>>> (d / ".dotdir").mkdir()

>>> _ = (FAKE_HOME / VLCQT).write_text('''
... [RecentsMRL]
... list=file://{}, file://{}, file://{}, file://{}
... times=0, 0, 121666, 246135
... '''.format(x, y, z, a))
>>> vlc_get_times() == { str(x): 0, str(y): 0, str(z): 121,
...                      str(a): 246 }
True

>>> import io
>>> def run(a, d = d, c = False):
...   main("--colour" if c else "--no-colour", "-d", str(d), *a.split())
>>> def run_(*a, **k):
...   f = io.StringIO()
...   with contextlib.redirect_stdout(f): run(*a, **k)
...   return f.getvalue()
>>> def run2(*a, **k):
...   with contextlib.redirect_stderr(sys.stdout): run(*a, **k)


Now, run some examples
----------------------

NB: coloured output escapes are replaced by RED, NON etc. during test.

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
>>> run("skip x.mkv")
>>> run("skip y.mkv")
>>> run_("skipped --zero") # doctest: +ELLIPSIS
'/.../media/x.mkv\x00/.../media/y.mkv\x00'
>>> run_("playing --zero") # doctest: +ELLIPSIS
'/.../media/z.mkv 0:02:01\x00'
>>> run_("playing --zero --only-files") # doctest: +ELLIPSIS
'/.../media/z.mkv\x00'
>>> run("mark z.mkv")
>>> run("next")
No files to play.
>>> run("unmark y.mkv")
>>> run("ls")
[*] x.mkv
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
[*] x.mkv
[ ] y.mkv
[x] z.mkv
>>> run("ld", c = True)
(RED1NON>YLL 0NON!) more
>>> run("unmark b.mkv", d = d / "more")
>>> run("ld", c = True)
(RED1NON>BLU 1NON!) more

>>> run("--show-hidden ls")
[ ] .dotfile.mkv
[*] x.mkv
[ ] y.mkv
[x] z.mkv
>>> run("--show-hidden ld")
(     ) .dotdir
(1> 1!) more

>>> (d / "un\033safe\x01file.mkv").touch()
>>> (d / "unsafe\ndir").mkdir()

>>> run("ls")
[ ] un?safe?file.mkv
[*] x.mkv
[ ] y.mkv
[x] z.mkv
>>> run("ld")
(1> 1!) more
(     ) unsafe?dir
>>> run("play un\033safe\x01file.mkv") # doctest: +ELLIPSIS
Playing un?safe?file.mkv ...
RUN true vlc --fullscreen --play-and-exit -- .../media/un?safe?file.mkv

>>> run2("mark /foo/bar/baz.mkv") # doctest: +ELLIPSIS
Error: '/foo/bar/baz.mkv' does not start with '/.../media'
>>> run2("mark nonexistent.mkv") # doctest: +ELLIPSIS
Error: '/.../nonexistent.mkv' is not a file
>>> run2("unmark nonexistent.mkv")
>>> run2("mark more/a.mkv") # doctest: +ELLIPSIS
Error: '/.../more/a.mkv' is not a file in '/.../media'
>>> run2("unmark foo/bar.mkv") # doctest: +ELLIPSIS
Error: '/.../bar.mkv' is not a file in '/.../media'
"""
                                                                # }}}1

import argparse, contextlib, datetime, hashlib, json, os, subprocess,\
       sys, urllib

from collections import defaultdict
from pathlib import Path

__version__   = "0.2.1"

DESC          = "m - minimalistic media manager"

HOME          = Path.home()                                     # dyn
CFG           = ".obfusk-m"                     # use git?! -> sync?!
VLCQT         = ".config/vlc/vlc-qt-interface.conf"
KODIDB        = ".kodi/userdata/Database/MyVideos107.db"

EXTS          = ".avi .m4v .mkv .mp3 .mp4 .ogg .ogv".split()    # TODO
CONT_BACK     = 5                                               # TODO

VLCCMD        = "vlc --fullscreen --play-and-exit".split()      # dyn
VLCCONT       = lambda t: ["--start-time", str(int(t))]

INFOS, INFOCH = "skip done playing new".split(), "*x> "
INFOCO        = "cya grn red blu".split()
INFOCHAR      = dict(zip(INFOS, INFOCH))
INFOCHAR_L    = dict(INFOCHAR, new = "!")
INFOCOLOUR_L  = dict(zip(INFOS, INFOCO))
INFOCOLOUR    = dict(INFOCOLOUR_L, new = None)

SKIP          = -1

USE_COLOUR    = sys.stdout.isatty()   # NB: dyn by --[no-]colour
SHOW_HIDDEN   = False                 # NB: dyn by --show-hidden

class MError(RuntimeError): pass

# === main & related functions ===

# NB: dyn USE_COLOUR, SHOW_HIDDEN
# TODO: use threading.local?
def main(*args):                                                # {{{1
  p = _argument_parser(); n = p.parse_args(args)
  c = n.colour if n.colour is not None else USE_COLOUR
  if n.subcommand == "_test": return _test(n.verbose)
  with dyn(globals(), USE_COLOUR = c, SHOW_HIDDEN = n.show_hidden):
    dpath = cwd() / Path(n.dir) if n.dir else cwd()
    try:
      return do_something(n.f, dpath, n) or 0
    except MError as e:
      print("Error:", *e.args, file = sys.stderr)
      return 1
                                                                # }}}1

def _argument_parser():                                         # {{{1
  p = argparse.ArgumentParser(description = DESC)
  p.add_argument("--version", action = "version",
                 version = "%(prog)s {}".format(__version__))
  p.add_argument("--dir", "-d", metavar = "DIR",
                 help = "use DIR instead of $PWD")
  p.add_argument("--show-hidden", action = "store_true",
                 help = "show hidden (i.e. starting with .) "
                        "files & dirs")

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

  p_list    = _subcommand(s, "list l ls"    , "list files",
                          do_list_dir_files)
  p_list_d  = _subcommand(s, "list-dirs ld" , "list directories",
                          do_list_dir_dirs)
  p_list_a  = _subcommand(s, "list-all la",
                          "list directories & files",
                          do_list_dir_all)
  p_next    = _subcommand(s, "next n"       , "play next file",
                          do_play_next)
  p_play    = _subcommand(s, "play p"       , "play FILE",
                          do_play_file)
  p_mark    = _subcommand(s, "mark m"       , "mark FILE as done",
                          do_mark_file)
  p_unmark  = _subcommand(s, "unmark u"     , "mark FILE as new",
                          do_unmark_file)
  p_skip    = _subcommand(s, "skip s"       , "mark FILE as skip",
                          do_skip_file)
  p_index   = _subcommand(s, "index i",
                          "index current directory",
                          do_index_dir)
  p_playing = _subcommand(s, "playing",
                          "list files marked as playing",
                          do_playing_files)
  p_watched = _subcommand(s, "watched",
                          "list files marked as done",
                          do_watched_files)
  p_skipped = _subcommand(s, "skipped",
                          "list files marked as skip",
                          do_skipped_files)
  p_kodi_w  = _subcommand(s, "kodi-import-watched",
                          "import watched data from kodi",
                          do_kodi_import_watched)
  p_kodi_p  = _subcommand(s, "kodi-import-playing",
                          "import playing data from kodi",
                          do_kodi_import_playing)

  p_test    = s.add_parser("_test")
  p_test.add_argument("--verbose", "-v", action = "store_true")

  for x in [p_play, p_mark, p_unmark, p_skip]:
    x.add_argument("filename", metavar = "FILE")
  for x in [p_playing, p_watched, p_skipped]:
    x.add_argument("--flat", action = "store_true",
      help = "flat list of files instead of grouped by directory")
    x.add_argument("--zero", action = "store_true",
      help = "zero-delimited (implies --flat) output "
             "(for e.g. xargs -0)")
  p_playing.add_argument("--only-files", action = "store_true",
      help = "only print files, not times")

  return p
                                                                # }}}1

def _subcommand(s, names, desc, f):                             # {{{1
  name, *aliases = names.split()
  p = s.add_parser(name, aliases = aliases, help = desc,
                   description = desc)
  p.set_defaults(f = f)
  return p
                                                                # }}}1

# NB: dyn HOME, VLCCMD, prompt_yn, COLOURS
def _test(verbose = False):                                     # {{{1
  global TEST_DIR, FAKE_HOME
  import doctest, tempfile
  m = None if __name__ == "__main__" else sys.modules[__name__]
  with tempfile.TemporaryDirectory() as tdir:
    TEST_DIR = Path(tdir); FAKE_HOME = TEST_DIR / "home"
    with dyn(globals(), HOME = FAKE_HOME, VLCCMD = ["true"] + VLCCMD,
             prompt_yn = lambda _: True,
             COLOURS   = { k:k.upper() for k in COLOURS }):
      failures, _tests = doctest.testmod(m, verbose = verbose)
      return 0 if failures == 0 else 1
                                                                # }}}1

def do_something(f, dpath, ns):
  kw = { k:v for k,v in vars(ns).items()
         if k in "filename zero flat only_files".split() }
  return f(dpath, db_load(dpath)["files"], **kw)

# === do_* ===

def do_list_dir_files(dpath, fs):                               # {{{1
  for st, fn in dir_iter(dpath, fs):
    infochar = clr(INFOCOLOUR[st], INFOCHAR[st])
    o, t     = ["["+infochar+"]", safe(fn)], db_t(fs, fn)
    if t: o.append(fmt_time(t))
    print(*o)
                                                                # }}}1

def do_list_dir_dirs(dpath, _fs):
  for sd, p, n in dir_iter_dirs(dpath):
    pl = _linfo(p, "playing", 1, p)
    ne = _linfo(n, "new"    , 2, n is not None)
    print("(" + pl + ne + ")", safe(sd))

def _linfo(n, st, w, c):
  if not c: return " "*(w+1)
  return clr(INFOCOLOUR_L[st] if n else "yll", str(n).rjust(w)) + \
         INFOCHAR_L[st]

def do_list_dir_all(dpath, fs):
  do_list_dir_dirs(dpath, fs)
  do_list_dir_files(dpath, fs)

def do_play_next(dpath, fs):
  fn = dir_next(dpath, fs)
  if fn: play_file(dpath, fs, fn)
  else: print("No files to play.")

def do_play_file(dpath, fs, filename):
  fn = check_filename(dpath, filename)
  play_file(dpath, fs, fn)

def do_mark_file(dpath, _fs, filename):
  _fupd(dpath, filename, True)

def do_unmark_file(dpath, _fs, filename):
  _fupd(dpath, filename, False, False)

def do_skip_file(dpath, _fs, filename):
  _fupd(dpath, filename, SKIP)

def _fupd(dpath, filename, what, must_exist = True):
  fn = check_filename(dpath, filename, must_exist)
  db_update(dpath, { fn: what })

def do_index_dir(dpath, _fs):
  db_update(dpath, {})

def do_playing_files(_dpath, _fs, flat, zero, only_files):
  _print_files_with_state("playing", flat, zero, not only_files)

def do_watched_files(_dpath, _fs, flat, zero):
  _print_files_with_state("done", flat, zero)

def do_skipped_files(_dpath, _fs, flat, zero):
  _print_files_with_state("skip", flat, zero)

def _print_files_with_state(st, flat, zero, w_t = False):       # {{{1
  data = _files_with_state(st)
  for dpath_s in sorted(data):
    if not (flat or zero): print(safe(dpath_s) + ":")
    for fn, what in sorted(data[dpath_s]):
      x = str(Path(dpath_s) / fn) if flat or zero else "  " + fn
      s = safe(x) if not zero else x
      t = " " + fmt_time(what) if w_t else ""
      print(s + t, end = "\0" if zero else "\n")
                                                                # }}}1

def _files_with_state(st):                                      # {{{1
  data = defaultdict(list)
  for df in (HOME / CFG).glob("dir__*.json"):
    with df.open() as f:
      db = json.load(f); dpath_s, fs = db["dir"], db["files"]
      for fn, what in fs.items():
        if _state_in_db(what) == st: data[dpath_s].append((fn, what))
  return data
                                                                # }}}1

def do_kodi_import_watched(_dpath, _fs):
  data = defaultdict(dict)
  for p, name in kodi_path_query(KODI_WATCHED_SQL):
    data[p][name] = True
  for dpath, fs in data.items(): db_update(dpath, fs)

def do_kodi_import_playing(_dpath, _fs):
  data = defaultdict(dict)
  for p, name, t in kodi_path_query(KODI_PLAYING_SQL):
    data[p][name] = int(t)
  for dpath, fs in data.items(): db_update(dpath, fs)

# === dir_* ===

def dir_iter(dpath, fs = None):
  if fs is None: fs = db_load(dpath)["files"]
  for fn in dir_files(dpath): yield _state(fn, fs), fn

def _state(fn, fs):
  return _state_in_db(fs[fn]) if fn in fs else "new"

def _state_in_db(what):
  return { True: "done", SKIP: "skip" }.get(what, "playing")

def dir_iter_dirs(dpath):                                       # {{{1
  for sd in dir_dirs(dpath):
    if db_dir_file(dpath / sd).exists():
      info = dict(playing = 0, new = 0)
      for st, _ in dir_iter(dpath / sd):
        if st in info: info[st] += 1
      yield sd, info["playing"], info["new"]
    else:
      yield sd, None, None
                                                                # }}}1

def dir_next(dpath, fs):
  for fn in dir_files(dpath):
    if fn not in fs or fs[fn] not in [True, SKIP]: return fn
  return None

def dir_dirs(dpath):
  return sorted( x.name for x in _iterdir(dpath) if x.is_dir() )

def dir_files(dpath):
  return sorted( x.name for x in _iterdir(dpath)
                 if x.is_file() and x.suffix.lower() in EXTS )

def _iterdir(dpath):
  return ( x for x in dpath.iterdir()
           if SHOW_HIDDEN or not x.name.startswith(".") )

# === db_* ===

# NB: files map to
#   * True      (done)
#   * int (>0)  (playing, seconds)
#   * int (-1)  (skip)
def db_load(dpath):
  df = db_dir_file(dpath)
  if not df.exists(): return dict(dir = str(dpath), files = {})
  with df.open() as f: return _db_check(dpath, json.load(f))

# TODO: use flock? backup?
def db_update(dpath, files):                                    # {{{1
  (HOME / CFG).mkdir(exist_ok = True)
  fs  = db_load(dpath)["files"]
  fs_ = { k:v for k,v in {**fs, **files}.items() if v != False }
  db  = _db_check(dpath, dict(dir = str(dpath), files = fs_))
  with db_dir_file(dpath).open("w") as f:
    json.dump(db, f, indent = 2, sort_keys = True)
    f.write("\n")
                                                                # }}}1

def _db_check(dpath, db):                                       # {{{1
  assert sorted(db.keys()) == "dir files".split()
  assert db["dir"] == str(dpath)
  assert all( x == True or type(x) == int and (x > 0 or x == SKIP)
              for x in db["files"].values() )
  return db
                                                                # }}}1

# NB: max filename len = 255 > 5 + 200 + 2 + 40 + 5 = 252
def db_dir_file(dpath):
  d   = str(dpath)
  fn  = "dir__" + d.replace("/", "|")[:200] + "__" + \
        hashlib.sha1(d.encode()).hexdigest() + ".json"
  return HOME / CFG / fn

def db_t(fs, fn):
  t = fs.get(fn)
  return None if t in [True, SKIP] else t

# === playing & vlc ===

def play_file(dpath, fs, fn):
  t = db_t(fs, fn); etc = "from " + fmt_time(t) + " " if t else ""
  print("Playing", safe(fn), etc + "...")
  t_ = vlc_play(dpath, fn, t)
  db_update(dpath, { fn: t_ })

# TODO: error handling? --noprompt?!
# NB: we unfortunately can't tell the difference between a file that
# has played completely and one that has played very little, so we
# need to prompt :(
def vlc_play(dpath, fn, t = None):                              # {{{1
  fp, t_  = str(dpath / fn), max(0, t - CONT_BACK) if t else 0
  cmd     = VLCCMD + (VLCCONT(t_) if t_ else []) + ["--", fp]
  print("RUN", *map(safe, cmd)); subprocess.run(cmd, check = True)
  t2      = vlc_get_times().get(fp) or True
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
    return dict(zip(l, t))
                                                                # }}}1

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
    p = Path(row[0])
    yield(p.parent, p.name, *row[1:])

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

# === entry point ===

def main_():
  """Entry point for main program."""
  return main(*sys.argv[1:])

if __name__ == "__main__":
  sys.exit(main_())

# vim: set tw=70 sw=2 sts=2 et fdm=marker :
