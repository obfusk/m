#!/usr/bin/python3
# encoding: utf-8

# --                                                            ; {{{1
#
# File        : m.py
# Maintainer  : Felix C. Stegerman <flx@obfusk.net>
# Date        : 2017-12-08
#
# Copyright   : Copyright (C) 2017  Felix C. Stegerman
# Version     : v0.1.1
# License     : GPLv3+
#
# --                                                            ; }}}1

                                                                # {{{1
r"""
m - minimalistic media manager

>>> import m
>>> d           = cwd() / "test/media"
>>> m.HOME      = cwd() / "test/home"   # monkey...
>>> m.VLCCMD    = ["true"] + m.VLCCMD
>>> m.prompt_yn = lambda _: True        # ...patch!
>>> x, y, z     = d / "x.mkv", d / "y.mkv", d / "z.mkv"

>>> _ = (m.HOME / m.VLCQT).write_text('''
... [RecentsMRL]
... list=file://{}, file://{}, file://{}
... times=0, 0, 121666
... '''.format(x, y, z))
>>> m.vlc_get_times() == { str(x): 0, str(y): 0, str(z): 121 }
True

>>> def t_main(a, d = d): m.main("-d", str(d), *a.split())

>>> t_main("ls")
[ ] x.mkv
[ ] y.mkv
[ ] z.mkv
>>> t_main("mark x.mkv")
>>> t_main("skip y.mkv")
>>> t_main("ls")
[x] x.mkv
[*] y.mkv
[ ] z.mkv
>>> t_main("next") # doctest: +ELLIPSIS
Playing z.mkv ...
RUN true vlc --fullscreen --play-and-exit -- .../test/media/z.mkv
>>> t_main("ls")
[x] x.mkv
[*] y.mkv
[>] z.mkv 0:02:01
>>> t_main("next") # doctest: +ELLIPSIS
Playing z.mkv from 0:02:01 ...
RUN true vlc --fullscreen --play-and-exit --start-time 116 -- .../test/media/z.mkv
>>> t_main("play y.mkv") # doctest: +ELLIPSIS
Playing y.mkv ...
RUN true vlc --fullscreen --play-and-exit -- .../test/media/y.mkv
>>> t_main("ls")
[x] x.mkv
[x] y.mkv
[>] z.mkv 0:02:01
>>> t_main("mark z.mkv")
>>> t_main("next")
No files to play.
>>> t_main("unmark x.mkv")
>>> t_main("unmark y.mkv")
>>> t_main("ls")
[ ] x.mkv
[ ] y.mkv
[x] z.mkv

>>> t_main("ld")
(      ) more
>>> t_main("index", d = d / "more")
>>> t_main("ld")
( 0> 2!) more
>>> t_main("ls", d = d / "more")
[ ] a.mkv
[ ] b.mkv
>>> t_main("mark a.mkv", d = d / "more")
>>> t_main("la")
( 0> 1!) more
[ ] x.mkv
[ ] y.mkv
[x] z.mkv
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

EXTS          = ".avi .mp4 .mkv".split()  # TODO
CONT_BACK     = 5                         # TODO

VLCCMD        = "vlc --fullscreen --play-and-exit".split()
VLCCONT       = lambda t: ["--start-time", str(int(t))]

INFOS, INFOC  = "skip done playing new".split(), "*x> "
INFOCHAR      = dict(zip(INFOS, INFOC))

def main(*args):                                                # {{{1
  p = _argument_parser(); n = p.parse_args(args)
  a = [n.file] if hasattr(n, "file") else []
  if n.subcommand == "test":
    import doctest
    failures, tests = doctest.testmod(verbose = n.verbose)
    return 0 if failures == 0 else 1
  return do_something(n.f, Path(n.dir) if n.dir else cwd(), a) or 0
                                                                # }}}1

def _argument_parser():                                         # {{{1
  p = argparse.ArgumentParser(description = DESC)
  p.add_argument("--version", action = "version",
                 version = "%(prog)s {}".format(__version__))
  p.add_argument("--dir", "-d", metavar = "DIR",
                 help = "use DIR instead of $PWD")

  s = p.add_subparsers(title = "subcommands", dest = "subcommand")
  s.required = True           # https://bugs.python.org/issue9253

  p_list    = s.add_parser("list"       , aliases = "l ls".split())
  p_list_d  = s.add_parser("list-dirs"  , aliases = ["ld"])
  p_list_a  = s.add_parser("list-all"   , aliases = ["la"])
  p_next    = s.add_parser("next"       , aliases = ["n"])
  p_play    = s.add_parser("play"       , aliases = ["p"])
  p_mark    = s.add_parser("mark"       , aliases = ["m"])
  p_unmark  = s.add_parser("unmark"     , aliases = ["u"])
  p_skip    = s.add_parser("skip"       , aliases = ["s"])
  p_index   = s.add_parser("index"      , aliases = ["i"])
  p_kodi_w  = s.add_parser("kodi-import-watched")
  p_kodi_p  = s.add_parser("kodi-import-playing")

  p_test    = s.add_parser("test")
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

def do_list_dir_files(d, fs):
  for state, f in dir_iter(d, fs):
    o, t = ["["+INFOCHAR[state]+"]", f], db_t(fs, f)
    if t: o.append(fmt_time(t))
    print(*o)

def do_list_dir_dirs(d, _fs):
  for sd, pla, new in dir_iter_dirs(d):
    p = "{:2}>".format(pla) if pla is not None else " "*3
    n = "{:2}!".format(new) if new is not None else " "*3
    print("(" + p + n + ")", sd)

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

# TODO
def check_filename(d, f):                                       # {{{1
  p = d / Path(f); r = p.relative_to(d)
  if not p.is_file():
    raise ValueError("'{}' is not a file".format(p))
  if len(r.parts) != 1:
    raise ValueError("'{}' is not a file in '{}'".format(p, d))
  return p.name
                                                                # }}}1

def play_file(d, fs, f):
  t = db_t(fs, f)
  print("Playing", f, ("from "+fmt_time(t)+" " if t else "") + "...")
  t_ = vlc_play(d, f, t)
  db_update(d, { f: t_ })

# TODO: error handling? --noprompt?!
# NB: we unfortunately can't tell the difference between a file that
# has played completely and one that has played very little, so we
# need to prompt :(
def vlc_play(d, f, t = None):                                   # {{{1
  t_  = max(0, t - CONT_BACK) if t else 0
  cmd = VLCCMD + (VLCCONT(t_) if t_ else []) + ["--", str(d / f)]
  print("RUN", *cmd); subprocess.run(cmd, check = True)
  t2  = vlc_get_times().get(str(d / f)) or True
  return False if t2 == True and not prompt_yn("Done") else t2
                                                                # }}}1

# TODO: cleanup
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

def fmt_time(secs):
  return str(datetime.timedelta(seconds = secs))

def do_something(f, d, args):
  return f(d, db_load(d)["files"], *args)

# NB: use $PWD instead of Path.cwd() since we might be in a symlinked
# directory in the shell we've been run from.  We could follow the
# symlinks instead but that creates other issues.  For now, make sure
# the cwd we see and the one in the shell (prompt) are the same.  That
# should work for most cases, and prevent issues when moving the
# symlink targets.  It's also consistent w/ kodi.
def cwd(): return Path(os.environ["PWD"])

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

if sys.version_info.major >= 3:
  def prompt(s): return input(s + "? ")

def prompt_yn(s):
  return not prompt(s + " [Yn]").lower().startswith("n")

def main_():
  """Entry point for main program."""
  return main(*sys.argv[1:])

if __name__ == "__main__":
  sys.exit(main_())

# vim: set tw=70 sw=2 sts=2 et fdm=marker :
