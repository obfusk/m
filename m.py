#!/usr/bin/python3
# encoding: utf-8

# TODO: README, LICENSE, tests, ...
# WISHLIST: kodi db <->

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

import hashlib, json, os, subprocess, sys, urllib

from pathlib import Path

HOME          = Path.home()
CFG           = HOME / ".obfusk-m"
VLCQT         = HOME / ".config/vlc/vlc-qt-interface.conf"

EXTS          = ".avi .mp4 .mkv".split()  # TODO
CONT_BACK     = 5                         # TODO

VLCCMD        = "vlc --fullscreen --play-and-exit".split()
VLCCONT       = lambda t: ["--start-time", str(int(t))]

INFOCHAR      = dict(zip("playing done new".split(),">x "))

if sys.version_info.major >= 3:
  def prompt(s): return input(s + "? ")
  def prompt_yn(s):
    return not prompt(s + " [Yn]").lower().startswith("n")

# TODO: proper parsing (argparse) etc.
def main(*args):                                                # {{{1
  if not args:
    print("Usage: m { list | next | play <file> | [un]mark <file> }")
    return 1
  f = DISPATCH.get(args[0])
  if not f:
    print("Unknown command:", " ".join(args))
    return 1
  do_something(f, args = args[1:])
  return 0
                                                                # }}}1

def do_list_dir(d, db):
  for state, f in dir_iter(d, db):
    o, t = ["["+INFOCHAR[state]+"]", f], db_t(db, f)
    if t: o.append(format_time(t))
    print(*o)

def do_play_next(d, db):
  f = dir_next(d, db)
  if not f:
    print("No files to play."); return
  play_file(d, db, f, db_t(db, f))

def do_play_file(d, db, filename):
  f = check_filename(d, filename)
  play_file(d, db, f, db_t(db, f))

def do_mark_file(d, db, filename):
  f = check_filename(d, filename)
  db_update(d, { f: True })

def do_unmark_file(d, db, filename):
  f = check_filename(d, filename)
  db_update(d, { f: False })

def dir_iter(d, db):
  for f in dir_files(d):
    if f in db: yield ("done" if db[f] == True else "playing"), f
    else:       yield "new", f

def dir_next(d, db):
  for f in dir_files(d):
    if f not in db or db[f] != True: return f
  return None

def dir_files(dirname):
  return sorted( x.name for x in dirname.iterdir()
                 if x.is_file() and x.suffix in EXTS )

def db_load(dirname):                                           # {{{1
  d = db_dir_file(dirname)
  if not d.exists(): return {}
  with d.open() as f:
    fs = json.load(f)["files"]
    assert all( x == True or type(x) == int for x in fs.values() )
    return fs
                                                                # }}}1

# TODO: use flock?
def db_update(dirname, files):                                  # {{{1
  CFG.mkdir(exist_ok = True)
  fs  = { k:v for k,v in {**db_load(dirname), **files}.items()
          if v != False }
  dat = dict(dir = str(dirname), files = fs)
  with db_dir_file(dirname).open("w") as f:
    json.dump(dat, f, indent = 2, sort_keys = True)
    f.write("\n")
                                                                # }}}1

def db_dir_file(dirname):
  d = str(dirname)
  x = "dir__" + d.replace("/", "|") + "__" + \
      hashlib.sha1(d.encode()).hexdigest() + ".json"
  return CFG / x

def db_t(db, f):
  t = db.get(f)
  return None if t == True else t

# TODO
def check_filename(d, f):                                       # {{{1
  p = (d / Path(f)).relative_to(d)
  if not p.is_file():
    raise ValueError("'{}' is not a file".format(p))
  if len(p.parts) != 1:
    raise ValueError("'{}' is not a file in '{}'".format(p, d))
  return str(p)
                                                                # }}}1

def play_file(d, db, f, t = None):
  print("Playing", f, "...")
  if t: print("  from", format_time(t))
  t_ = vlc_play(d, f, t)
  db_update(d, { f: t_ })

# TODO: error handling?
# NB: we unfortunately can't tell the difference between a file that
# has played completely and one that has played very little, so we
# need to prompt :(
def vlc_play(d, f, t = None):                                   # {{{1
  t_  = max(0, t - CONT_BACK) if t else 0
  cmd = VLCCMD + VLCCONT(t_) if t_ else VLCCMD
  subprocess.check_call(cmd + ["--", f])
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
          l = [ urllib.parse.unquote(x[7:] if x.startswith("file://")
                  else x) for x in line[5:].split(", ") ]
        elif line.startswith("times="):
          t = [ int(x) // 1000 for x in line[6:].split(", ") ]
    if l is None or t is None: return {}
    return dict(zip(l,t))
                                                                # }}}1

def format_time(secs):
  s = secs % 60; m = secs // 60 % 60; h = secs // 60 // 60
  return "{:02d}:{:02d}:{:02d}".format(h,m,s)

def do_something(f, args = (), d = None):
  if d is None: d = cwd()
  return f(d, db_load(d), *args)

# NB: use $PWD instead of Path.cwd() since we might be in a symlinked
# directory in the shell we've been run from.  We could follow the
# symlinks instead but that creates other issues.  For now, make sure
# the cwd we see and the one in the shell (prompt) are the same.  That
# should work for most cases, and prevent issues when moving the
# symlink targets.  It's also consistent w/ kodi.
def cwd(): return Path(os.environ["PWD"])

# TODO
DISPATCH = dict(
  list = do_list_dir, next = do_play_next, play = do_play_file,
  mark = do_mark_file, unmark = do_unmark_file
)

if __name__ == "__main__":
  sys.exit(main(*sys.argv[1:]))

# vim: set tw=70 sw=2 sts=2 et fdm=marker :
