# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Also, at the bottom of this file there is a [TODO list](#todo) with planned future changes.

## [v2.0.1] - 2025-12-03

### Fixed

- `backup-apks`: Improved support for Android firmwares for which `adb shell pm list packages` fails or does not list all the installed packages by running it with an additional `--user 0` argument.

- `backup`, `backup-apks`: Should work properly on Windows.

## [v2.0.0] - 2025-03-30

### Added

- Introduced `backup`, `backup-apks`, and `restore-apks` subcommands.

  I.e. `hoardy-adb` gained a front-end to the `adb` utility, inspired by [Adebar](https://codeberg.org/izzy/Adebar).

### Changed

- Reworked most of the internals and switched to using `kisstdlib`.

  This makes the code much smaller and produces a nicer TTY UI.

- Improved documentation.

## [v1.2.0] - 2025-01-22

### Changed

- Formatted code using `black`.
- Fixed minor issues found by `pylint`.
- Improved error handling.
- Greatly improved documentation.

### Added

- Added `./test-cli.sh` with tests for all commands.

## [v1.1.3] - 2024-09-04

### Changed

- Renamed to `hoardy-adb`.
- Improved documentation.

## [v1.1.2] - 2024-05-11

### Changed

- Improved documentation.

## [v1.1.1] - 2024-03-22

### Changed

- Improved documentation.

## [v1.1.0] - 2024-03-06

### Added

- Implemented output encryption support.

### Changed

- Improved documentation.

## [v1.0.0] - 2024-02-01

### Added

- Initial public release.

[v2.0.1]: https://github.com/Own-Data-Privateer/hoardy-adb/compare/v2.0.0...v2.0.1
[v2.0.0]: https://github.com/Own-Data-Privateer/hoardy-adb/compare/v1.2.0...v2.0.0
[v1.2.0]: https://github.com/Own-Data-Privateer/hoardy-adb/compare/v1.1.3...v1.2.0
[v1.1.3]: https://github.com/Own-Data-Privateer/hoardy-adb/compare/v1.1.2...v1.1.3
[v1.1.2]: https://github.com/Own-Data-Privateer/hoardy-adb/compare/v1.1.1...v1.1.2
[v1.1.1]: https://github.com/Own-Data-Privateer/hoardy-adb/compare/v1.1.0...v1.1.1
[v1.1.0]: https://github.com/Own-Data-Privateer/hoardy-adb/compare/v1.0.0...v1.1.0
[v1.0.0]: https://github.com/Own-Data-Privateer/hoardy-adb/releases/tag/v1.0.0

# TODO

Currently empty.
