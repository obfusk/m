#!/usr/bin/python3
# encoding: utf-8

# TODO: README, LICENSE, ...

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

import hashlib, json, subprocess, sys, urllib

from pathlib import Path

HOME          = Path.home()
CFG           = HOME / ".obfusk-m"
VLCQT         = HOME / ".config/vlc/vlc-qt-interface.conf"

EXTS          = ".avi .mp4 .mkv".split()  # TODO

VLCCMD        = "vlc --fullscreen --play-and-exit".split()
VLCCMD_PLAY   = lambda f: VLCCMD + ["--", f]
VLCCMD_CONT   = lambda t, f: VLCCMD + ["--start-from", int(t), "--", f]

INFOCHAR      = dict(zip("playing done new".split(),">x "))

# TODO: proper parsing etc.
def main(*args):                                                # {{{1
  if not args:
    print("Usage: m { list | next | play <file> | [un]mark <file> }")
    return 1
  f = DISPATCH.get(args[0])
  if not f:
    print("Unknown command:", " ".join(args)); return 1
  do_something(f, args = args[1:])
  return 0
                                                                # }}}1

def do_list_dir(d, db):
  for i, f, t in dir_iter(d, db):
    o = ["["+INFOCHAR(i)+"]", f]
    if t: o.append(format_time(t))
    print(*o)

def do_play_next(d, db):
  f, t = dir_next(d, db)
  if not f:
    print("No files to play."); return
  play_file(db, f, t)

def do_play_file(d, db, filename):
  filename = check_filename(filename, d)
  play_file(db, filename)

def do_mark_file(d, db, filename):
  filename = check_filename(filename, d)
  db_update(d, { filename : True })

def do_unmark_file(d, db, filename):
  filename = check_filename(filename, d)
  db_update(d, { filename : False })

def dir_iter(d, db):                                            # {{{1
  for f in dir_files(d):
    if f in db:
      if isinstance(db[f], int):  yield "playing" , f, f[db]
      else:                       yield "done"    , f, None
    else:                         yield "new"     , f, None
                                                                # }}}1

def dir_next(d, db):                                            # {{{1
  for f in dir_files(d):
    if f in db:
      if isinstance(db[f], int): return f, db[f]
    else:                        return f, None
  return None, None
                                                                # }}}1

def dir_files(dirname):
  return sorted( str(x) for x in dirname.iterdir()
                 if x.is_file() and x.suffix in EXTS )

def db_load(dirname):
  d = db_dir_file(dirname)
  if not d.exists(): return {}
  with d.open() as f: return json.load(f)["files"]

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

# TODO
def check_filename(filename, d):                                # {{{1
  p = (d / Path(filename)).relative_to(d)
  if not p.is_file(): raise ValueError("'{}' is not a file".format(p))
  if len(p.parts) != 1:
    raise ValueError("'{}' is not a file in '{}'".format(p, d))
  return str(p)
                                                                # }}}1

def play_file(db, filename, t = None):
  print("Playing", f, "...")
  if t: print("  from", format_time(t))
  t_ = vlc_play(f, t, db)
  db_update(d, { f : t_ or True })

# TODO: error handling?
def vlc_play(filename, t = None):
  cmd = VLCCMD_CONT(t, filename) if t else VLCCMD_PLAY(filename)
  subprocess.check_call(cmd)
  return vlc_get_times().get(filename)

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
  if d is None: d = Path.cwd()
  return f(d, db_load(d), *args)

# TODO
DISPATCH = dict(
  list = do_list_dir, next = do_play_next, play = do_play_file,
  mark = do_mark_file, unmark = do_unmark_file
)

if __name__ == "__main__":
  sys.exit(main(*sys.argv[1:]))

# vim: set tw=70 sw=2 sts=2 et fdm=marker :
