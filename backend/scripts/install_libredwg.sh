#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
prefix="$root/bin/libredwg"
version=0.13.4
sha=7e153ea4dac4cbf3dc9c50b9ef7a5604e09cdd4c5520bcf8017877bbe1422cd5
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cd "$work"
curl --fail --location --proto '=https' --tlsv1.2 --max-time 180 "https://ftp.gnu.org/gnu/libredwg/libredwg-$version.tar.xz" -o source.tar.xz
printf '%s  source.tar.xz\n' "$sha" | sha256sum -c -
tar -xJf source.tar.xz
cd "libredwg-$version"
# Official release, no bindings or documentation generation; standalone CLI.
./configure --prefix="$prefix" --disable-bindings --disable-docs --disable-shared --enable-static
make -j2
make install
test -x "$prefix/bin/dwg2dxf"
test -x "$prefix/bin/dxf2dwg"
"$prefix/bin/dwg2dxf" --version
"$prefix/bin/dxf2dwg" --version
# Preserve upstream license and corresponding source in the installation.
mkdir -p "$prefix/share/source"
cp "$work/source.tar.xz" "$prefix/share/source/libredwg-$version.tar.xz"
cp COPYING "$prefix/share/source/"
