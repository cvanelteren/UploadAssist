import unittest
import tempfile
import shutil
import os
from pathlib import Path

from uploadassist.deps import collect, flatten_tex_paths


class TestFlatten(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for each test
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove temporary directories after each test
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.output_dir)

    def write_file(self, rel_path, content):
        file_path = Path(self.test_dir) / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return str(file_path)

    def read_output(self, filename):
        with open(Path(self.output_dir) / filename, "r", encoding="utf-8") as f:
            return f.read()

    def test_single_tex_flatten(self):
        # Single .tex file, no includes
        tex_content = r"""
        \documentclass{article}
        \begin{document}
        Hello, world!
        \end{document}
        """
        main_tex = self.write_file("main.tex", tex_content)
        collect(main_tex, self.output_dir, flatten=True)
        output = self.read_output("main.tex")
        self.assertIn("Hello, world!", output)

    def test_input_appendix_flatten(self):
        # main.tex includes appendix.tex
        appendix_content = r"""
        \section{Appendix}
        This is the appendix.
        """
        main_content = r"""
        \documentclass{article}
        \begin{document}
        Main content.
        \input{appendix/appendix.tex}
        \end{document}
        """
        self.write_file("appendix/appendix.tex", appendix_content)
        main_tex = self.write_file("main.tex", main_content)
        collect(main_tex, self.output_dir, flatten=True)
        # Check that appendix.tex is copied and path is updated in main.tex
        output = self.read_output("main.tex")
        self.assertIn(r"\input{appendix.tex}", output)
        appendix_out = self.read_output("appendix.tex")
        self.assertIn("This is the appendix.", appendix_out)

    def test_nested_figure_flatten(self):
        # main.tex includes a figure from a nested directory
        figure_content = "FAKEPNGDATA"
        main_content = r"""
        \documentclass{article}
        \usepackage{graphicx}
        \begin{document}
        \includegraphics{figures/nested/figure1.png}
        \end{document}
        """
        self.write_file("figures/nested/figure1.png", figure_content)
        main_tex = self.write_file("main.tex", main_content)
        collect(main_tex, self.output_dir, flatten=True)
        # Check that figure is copied and path is updated in main.tex
        output = self.read_output("main.tex")
        self.assertIn(r"\includegraphics{figure1.png}", output)
        figure_out_path = Path(self.output_dir) / "figure1.png"
        self.assertTrue(figure_out_path.exists())
        with open(figure_out_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), figure_content)


if __name__ == "__main__":
    unittest.main()
