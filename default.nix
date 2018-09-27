{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication rec {
  pname         = "mmm";
  version       = "0.4.2";
  src           = builtins.path {
    name        = "m";
    path        = ./.;
    filter      = pkgs.lib.cleanSourceFilter;
  };
  buildInputs   = [ pkgs.pandoc ];
  preConfigure  = "make README.rst";
  meta          = {
    description = "minimalistic media manager";
    homepage    = "https://github.com/obfusk/m";
    license     = pkgs.stdenv.lib.licenses.gpl3Plus;
  };
}
