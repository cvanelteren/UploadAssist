# Changelog

All notable changes to UploadAssist are documented here. The project follows [Semantic Versioning](https://semver.org/).

## 1.0.0 - Unreleased

### Added

- Dependency-free recursive discovery of local TeX, graphics, bibliography, class, and style dependencies.
- Flat and structure-preserving submission directories with optional `.tar.gz` archives.
- Automatic main-document detection and additional file/directory inclusion.
- Extraction of cited entries from BibTeX databases.
- Supported Python versions and automated build, test, and publishing workflows.

### Changed

- Flattening is the default behavior for submission compatibility.
- Output directories are rebuilt cleanly so stale files cannot leak into a submission.
- The package version and release workflow are prepared for the `v1.0.0` tag.

### Fixed

- Escaped percent signs are preserved during comment removal.
- Duplicate filenames fail clearly instead of being overwritten during flattening.
- Nested TeX and graphics references are rewritten consistently in flat bundles.
