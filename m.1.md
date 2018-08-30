% m(1) v0.3.0 | General Commands Manual
% Felix C. Stegerman <flx@obfusk.net>
% 2018-08-30

# NAME

m - minimalistic media manager

# SYNOPSIS

m \[\<options>] \<command> \[\<command-specific-options>] \[\<args>]

# DESCRIPTION

m keeps track of which files you've played (or are still playing) and
thus allows you to easily continue playing the next file (using vlc or
mpv).

In order to avoid duplication, this man page is rather minimal.  More
help is available using:

    m --help      # global options & subcommands
    m ls --help   # subcommand (ls in this case) options & argument(s)
    m examples    # show some examples (from the tests)

See README.md for additional information and examples.  When installed
as a Debian package this should be available at
_/usr/share/doc/mmm/README.md.gz_.

# COMMANDS

NB: this list is provided here for convenience only.  Use one of the
help commands mentioned under DESCRIPTION for more detailed and
up-to-date information.

| list, l, ls
| list-dirs, ld
| list-all, la
| next, n
| continue, cont, c
| next-new, nn
| play, p
| mark, m
| unmark, u
| skip, s
| index, i
| playing
| watched
| skipped
| todo
| unfinished
| import-watched
| import-playing
| kodi-import-watched
| kodi-import-playing
| examples

# COPYRIGHT

Copyright © 2018 Felix C. Stegerman.  License GPLv3+: GNU GPL version
3 or later <https://gnu.org/licenses/gpl.html>.  This is free software:
you are free to change and redistribute it.   There  is NO WARRANTY,
to the extent permitted by law.
