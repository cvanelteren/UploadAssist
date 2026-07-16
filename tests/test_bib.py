from uploadassist.bib import _entries


def test_bib_parser_handles_nested_braces_and_parentheses():
    content = """
@article{alpha,
  title = {A {nested} title},
}
@book(beta,
  title = {Closing ) inside braces},
)
"""
    entries = _entries(content)
    assert set(entries) == {"alpha", "beta"}
    assert "{nested}" in entries["alpha"]
