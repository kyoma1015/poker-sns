#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
py="${POKERID_PYTHON:-python3}"
inc="$($py -c 'import sysconfig;print(sysconfig.get_paths()["include"])')"
ext="$($py -c 'import sysconfig;print(sysconfig.get_config_var("EXT_SUFFIX"))')"
out="${POKERID_G12_DISK_MODULE_DIR:-$(pwd)/build_g12_disk}"
mkdir -p "$out"
flags=()
if [[ "$(uname -s)" == Darwin ]]; then flags=(-undefined dynamic_lookup); fi
"${CXX:-c++}" -O2 -std=c++20 -fno-fast-math -ffp-contract=off -fPIC -shared \
  g12_solver_disk.cc patched/open_spiel/abseil-cpp/absl/random/discrete_distribution.cc \
  -Ipatched/pybind11/include -Ipatched -Ipatched/open_spiel/abseil-cpp -I"$inc" \
  -o "$out/pokerid_g12$ext" "${flags[@]}"
printf 'Built experimental disk-backed G12 module: %s\n' "$out/pokerid_g12$ext"
