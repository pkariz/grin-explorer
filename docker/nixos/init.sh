#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset
set -o xtrace

nix-shell --run "yarn install; yarn build"
