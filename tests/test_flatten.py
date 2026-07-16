import tarfile
from pathlib import Path

import pytest

from uploadassist.deps import collect, get_deps, strip_comments


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_discovers_only_referenced_local_dependencies(tmp_path):
    main = write(
        tmp_path / "main.tex",
        r"""
        \documentclass{localclass}
        \usepackage{styles/local,styles/second,graphicx}
        \graphicspath{{images/}}
        \input{sections/body}
        \includegraphics[width=1cm]{plot}
        \addbibresource{refs/library.bib}
        """,
    )
    expected = {
        main,
        write(tmp_path / "localclass.cls", "class"),
        write(tmp_path / "styles/local.sty", "style"),
        write(tmp_path / "styles/second.sty", r"\input{helper}"),
        write(tmp_path / "styles/helper.tex", "helper"),
        write(tmp_path / "sections/body.tex", "body"),
        write(tmp_path / "images/plot.png", "image"),
        write(tmp_path / "refs/library.bib", "bib"),
    }
    write(tmp_path / "refs/unused.bib", "unused")

    assert {Path(path) for path in get_deps(str(main))} == expected


def test_flatten_rewrites_references_and_creates_archive(tmp_path):
    main = write(
        tmp_path / "main.tex",
        r"""\graphicspath{{figures/}}
\input{sections/body}
\includegraphics{chart}
\usepackage{styles/local,styles/second}
\bibliography{refs/library}
\bibliographystyle{styles/journal}
""",
    )
    write(tmp_path / "sections/body.tex", "Body % remove me\n")
    write(tmp_path / "figures/chart.pdf", "PDF")
    write(tmp_path / "refs/library.bib", "BIB")
    write(tmp_path / "styles/local.sty", "LOCAL")
    write(tmp_path / "styles/second.sty", "SECOND")
    write(tmp_path / "styles/journal.bst", "BST")
    write(tmp_path / "main.bbl", "BBL")
    output = tmp_path / "submission"

    collected = collect(str(main), str(output), flatten=True)

    assert {Path(path).name for path in collected} == {
        "main.tex",
        "body.tex",
        "chart.pdf",
        "library.bib",
        "local.sty",
        "second.sty",
        "journal.bst",
        "main.bbl",
    }
    flattened = (output / "main.tex").read_text(encoding="utf-8")
    assert r"\input{body}" in flattened
    assert r"\includegraphics{chart}" in flattened
    assert r"\bibliography{library}" in flattened
    assert r"\usepackage{local,second}" in flattened
    assert r"\bibliographystyle{journal}" in flattened
    assert r"\graphicspath" not in flattened
    assert (output / "body.tex").read_text(encoding="utf-8") == "Body\n"
    with tarfile.open(f"{output}.tar.gz") as archive:
        assert "submission/main.tex" in archive.getnames()


def test_preserves_structure_and_replaces_stale_output(tmp_path):
    main = write(tmp_path / "main.tex", r"\input{parts/body}")
    write(tmp_path / "parts/body.tex", "body")
    output = tmp_path / "output"
    write(output / "stale.txt", "stale")

    collect(str(main), str(output), flatten=False, create_archive=False)

    assert (output / "parts/body.tex").is_file()
    assert not (output / "stale.txt").exists()


def test_flatten_rejects_filename_collisions(tmp_path):
    main = write(tmp_path / "main.tex", r"\input{a/same}\input{b/same}")
    write(tmp_path / "a/same.tex", "a")
    write(tmp_path / "b/same.tex", "b")

    with pytest.raises(ValueError, match="same name"):
        collect(str(main), str(tmp_path / "output"), flatten=True, create_archive=False)


def test_missing_explicit_dependency_fails(tmp_path):
    main = write(tmp_path / "main.tex", r"\includegraphics{missing}")

    with pytest.raises(FileNotFoundError, match="Referenced graphics"):
        get_deps(str(main))


def test_discovery_ignores_examples_in_verbatim(tmp_path):
    main = write(
        tmp_path / "main.tex",
        "\\begin{verbatim}\n\\input{not-a-file}\n\\end{verbatim}\n",
    )
    assert {Path(path) for path in get_deps(str(main))} == {main}


def test_output_cannot_be_an_ancestor_of_source(tmp_path):
    project = tmp_path / "project"
    main = write(project / "main.tex", "body")

    with pytest.raises(ValueError, match="must not replace"):
        collect(str(main), str(tmp_path), create_archive=False)


def test_comment_stripping_respects_escaped_percent():
    assert (
        strip_comments("value \\% literal % secret\nnext\n")
        == "value \\% literal\nnext\n"
    )
    assert strip_comments("value \\\\% secret\n") == "value \\\\\n"
    assert strip_comments("\\verb|100%| % secret\n") == "\\verb|100%|\n"
    verbatim = "\\begin{verbatim}\n100% literal\n\\end{verbatim}\n"
    assert strip_comments(verbatim) == verbatim
