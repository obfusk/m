#!/usr/bin/python3
# encoding: utf-8

# --                                                            ; {{{1
#
# File        : m.py
# Maintainer  : Felix C. Stegerman <flx@obfusk.net>
# Date        : 2017-12-07
#
# Copyright   : Copyright (C) 2017  Felix C. Stegerman
# Version     : v0.0.1
# License     : GPLv3+
#
# --                                                            ; }}}1

                                                                # {{{1
r"""
... TODO ...
"""
                                                                # }}}1

import argparse, hashlib, json, os, subprocess, sys, urllib

from collections import defaultdict
from pathlib import Path

__version__   = "0.0.1"

HOME          = Path.home()
CFG           = HOME / ".obfusk-m"        # use git?! -> sync?!
VLCQT         = HOME / ".config/vlc/vlc-qt-interface.conf"
KODIDB        = HOME / ".kodi/userdata/Database/MyVideos107.db"

EXTS          = ".avi .mp4 .mkv".split()  # TODO
CONT_BACK     = 5                         # TODO

VLCCMD        = "vlc --fullscreen --play-and-exit".split()
VLCCONT       = lambda t: ["--start-time", str(int(t))]

INFOCHAR      = dict(zip("playing done new skip".split(),">x *"))

def main(*args):
  p = _argument_parser(); n = p.parse_args(args)
  a = [n.file] if hasattr(n, "file") else []
  return do_something(n.f, args = a) or 0

def _argument_parser():                                         # {{{1
  p = argparse.ArgumentParser(description = "m")
  p.add_argument("--version", action = "version",
                 version = "%(prog)s {}".format(__version__))

  s = p.add_subparsers(title = "subcommands", dest = "subcommand")
  s.required = True           # https://bugs.python.org/issue9253

  p_list    = s.add_parser("list"   , aliases = "l ls".split())
  p_next    = s.add_parser("next"   , aliases = ["n"])
  p_play    = s.add_parser("play"   , aliases = ["p"])
  p_mark    = s.add_parser("mark"   , aliases = ["m"])
  p_unmark  = s.add_parser("unmark" , aliases = ["u"])
  p_skip    = s.add_parser("skip"   , aliases = ["s"])
  p_kodi_w  = s.add_parser("kodi-import-watched")
  p_kodi_p  = s.add_parser("kodi-import-playing")

  p_list    .set_defaults(f = do_list_dir)
  p_next    .set_defaults(f = do_play_next)
  p_play    .set_defaults(f = do_play_file)
  p_mark    .set_defaults(f = do_mark_file)
  p_unmark  .set_defaults(f = do_unmark_file)
  p_skip    .set_defaults(f = do_skip_file)
  p_kodi_w  .set_defaults(f = do_kodi_import_watched)
  p_kodi_p  .set_defaults(f = do_kodi_import_playing)

  for x in [p_play, p_mark, p_unmark, p_skip]:
    x.add_argument("file", metavar = "FILE")

  return p
                                                                # }}}1

def do_list_dir(d, fs):
  for state, f in dir_iter(d, fs):
    o, t = ["["+INFOCHAR[state]+"]", f], db_t(fs, f)
    if t: o.append(format_time(t))
    print(*o)

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

def dir_iter(d, fs):
  info = { True: "done", -1: "skip" }
  for f in dir_files(d):
    yield info.get(fs[f], "playing") if f in fs else "new", f

def dir_next(d, fs):
  for f in dir_files(d):
    if f not in fs or fs[f] not in [True, -1]: return f
  return None

def dir_files(dirname):
  return sorted( x.name for x in dirname.iterdir()
                 if x.is_file() and x.suffix in EXTS )

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
  CFG.mkdir(exist_ok = True)
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
  return CFG / x

def db_t(fs, f):
  t = fs.get(f)
  return None if t in [True, -1] else t

# TODO
def check_filename(d, f):                                       # {{{1
  p = (d / Path(f)).relative_to(d)
  if not p.is_file():
    raise ValueError("'{}' is not a file".format(p))
  if len(p.parts) != 1:
    raise ValueError("'{}' is not a file in '{}'".format(p, d))
  return str(p)
                                                                # }}}1

def play_file(d, fs, f):
  t = db_t(fs, f)
  print("Playing", f, ("from " + format_time(t) if t else "") + "...")
  t_ = vlc_play(d, f, t)
  db_update(d, { f: t_ })

# TODO: error handling?
# NB: we unfortunately can't tell the difference between a file that
# has played completely and one that has played very little, so we
# need to prompt :(
def vlc_play(d, f, t = None):                                   # {{{1
  t_  = max(0, t - CONT_BACK) if t else 0
  cmd = VLCCMD + VLCCONT(t_) if t_ else VLCCMD
  subprocess.run(cmd + ["--", f], check = True)
  t2  = vlc_get_times().get(str(d / f)) or True
  return False if t2 == True and not prompt_yn("Done") else t2
                                                                # }}}1

# TODO: cleanup
def vlc_get_times():                                            # {{{1
  if not VLCQT.exists(): return {}
  with VLCQT.open() as f:
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

def format_time(secs):
  s = secs % 60; m = secs // 60 % 60; h = secs // 60 // 60
  return "{:02d}:{:02d}:{:02d}".format(h,m,s)

def do_something(f, args = (), d = None):
  if d is None: d = cwd()
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
  conn = sqlite3.connect(str(KODIDB))
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

if __name__ == "__main__":
  sys.exit(main(*sys.argv[1:]))

# vim: set tw=70 sw=2 sts=2 et fdm=marker :
