# Introduction

Archive old .deb packages from http://dl.google.com/linux/chrome/deb/ as GitHub
releases.

[browser-matrix.yml](browser-matrix.yml) is the list of latest package version belong to each major version.

CI will run daily to check for new package version and create a new release if there is a new version.

Both `amd64` and `arm64` `.deb` packages are archived into each release. Each
architecture is downloaded, tested and uploaded on a matching native GitHub
runner (`ubuntu-latest` for `amd64`, `ubuntu-24.04-arm` for `arm64`). Older
Chrome versions that Google never shipped for `arm64` are skipped automatically,
so only the `amd64` package is archived for them.

[![Releases downloads](https://img.shields.io/github/downloads/NDViet/google-chrome-stable/total.svg)](https://github.com/NDViet/google-chrome-stable/releases)
