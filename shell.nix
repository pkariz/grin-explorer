{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "shell-dev";
  buildInputs = [ (import ./default.nix { inherit pkgs; }) ];
  # ignoring engines due to https://github.com/vuejs/vue-cli/issues/7116
  shellHook = ''
    yarn config set ignore-engines true
    yarn global add @vue/cli
    yarn global add @vue/cli-service-global
    export PATH="$(yarn global bin):$PATH"
  '';
}
