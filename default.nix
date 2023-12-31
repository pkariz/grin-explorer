{ pkgs ? import <nixpkgs> {} }:
let
    my-python-pkgs = python-packages: with python-packages; [
      setuptools
    ];
    python3-with-custom-pkgs = pkgs.python38.withPackages my-python-pkgs;
in
pkgs.buildEnv {
  name = "grin-explorer-tools";
  paths = [
    python3-with-custom-pkgs
    pkgs.pipenv
    pkgs.gmp
    pkgs.redis
    pkgs.postgresql
    pkgs.yarn
    pkgs.nodejs-18_x
    # for telnet debugging
    pkgs.inetutils
  ];
}
