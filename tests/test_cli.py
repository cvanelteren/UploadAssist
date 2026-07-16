import os
import re
import subprocess
import sys
from pathlib import Path


def run_cli(*args, cwd=None):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parents[1])
    return subprocess.run(
        [sys.executable, "-m", "uploadassist.cli", *map(str, args)],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_packages_and_archives(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    main = project / "main.tex"
    main.write_text("Hello \\% world % private\n", encoding="utf-8")

    result = run_cli(main)

    assert result.returncode == 0, result.stderr
    assert "Packaged 1 files" in result.stdout
    assert (project / "output" / "main.tex").read_text(
        encoding="utf-8"
    ) == "Hello \\% world\n"
    assert (project / "output.tar.gz").is_file()


def test_cli_autodetects_main_and_preserves_structure(tmp_path):
    (tmp_path / "chapter").mkdir()
    (tmp_path / "notes.tex").write_text("unused", encoding="utf-8")
    (tmp_path / "chapter" / "one.tex").write_text("chapter", encoding="utf-8")
    (tmp_path / "main.tex").write_text(r"\input{chapter/one}", encoding="utf-8")

    result = run_cli("--noflatten", "--no-archive", cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "output_no_flatten" / "chapter" / "one.tex").is_file()
    assert not (tmp_path / "output_no_flatten.tar.gz").exists()


def test_cli_rejects_ambiguous_autodetection(tmp_path):
    (tmp_path / "one.tex").write_text("one", encoding="utf-8")
    (tmp_path / "two.tex").write_text("two", encoding="utf-8")

    result = run_cli(cwd=tmp_path)

    assert result.returncode == 1
    assert "Cannot auto-detect" in result.stderr


def test_cli_reports_version():
    result = run_cli("--version")
    assert result.returncode == 0
    assert result.stdout.endswith(" 1.0.0\n")


def test_runtime_and_package_versions_match():
    from uploadassist import __version__

    metadata = (Path(__file__).parents[1] / "pyproject.toml").read_text()
    assert (
        re.search(r'^version = "([^\"]+)"$', metadata, re.MULTILINE).group(1)
        == __version__
    )
