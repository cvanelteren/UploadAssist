# Releasing UploadAssist

The GitHub release workflow builds one source distribution and one universal wheel, checks them, publishes to TestPyPI, and then publishes non-prereleases to PyPI.

## One-time publisher setup

Configure trusted publishers for the `uploadassist` project on both PyPI and TestPyPI:

- Owner: `cvanelteren`
- Repository: `UploadAssist`
- Workflow: `publish.yml`
- PyPI environment: `prod`

TestPyPI is a separate service and needs its own trusted-publisher entry. Its environment value must match the workflow configuration, if one is required by the publisher entry.

## Release checklist

1. Merge the release commit into `main` and confirm the Tests workflow passes.
2. Confirm the final `assets/logo.svg` renders correctly beside the title in the README.
3. Replace `Unreleased` in `CHANGELOG.md` with the release date.
4. Confirm `pyproject.toml` and `uploadassist/_version.py` both contain `1.0.0`.
5. Create and push the annotated tag `v1.0.0` on that commit.
6. Create a GitHub release from `v1.0.0` and publish it as a normal (not prerelease) release.
7. Watch the Publish Python Package workflow. It will refuse to publish if the tag and wheel versions differ.
8. Verify the public install in a clean environment:

   ```console
   python -m venv /tmp/uploadassist-smoke
   /tmp/uploadassist-smoke/bin/python -m pip install uploadassist==1.0.0
   /tmp/uploadassist-smoke/bin/uploadassist --version
   ```

PyPI does not allow replacing a file or reusing a published version. If publishing partially fails after either index accepts `1.0.0`, diagnose the failed job before changing the version or creating another release.
