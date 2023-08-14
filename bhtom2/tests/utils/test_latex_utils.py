
import unittest
from typing import List, Any
from bhtom2.utils.latex_utils import data_to_latex_table
from pylatex import Document, Tabularx

class TestDataToLatex(unittest.TestCase):
    def test_data_to_latex_table(self):
        data = [["John", "Doe", 30], ["Jane", "Doe", 25]]
        columns = ["first_name", "last_name", "age"]
        filename = "test.tex"
        expected_output = r"""\documentclass{article}%
\usepackage[T1]{fontenc}%
\usepackage[utf8]{inputenc}%
\usepackage{lmodern}%
\usepackage{textcomp}%
\usepackage{lastpage}%
\usepackage{tabularx}%
%
%
%
\begin{document}%
\normalsize%
\begin{tabularx}{\textwidth}{lX lX lX}%
\hline%
first name&last name&age\\%
\hline%
\hline%
John&Doe&30\\%
Jane&Doe&25\\%
\hline%
\hline%
\end{tabularx}%
\end{document}"""

#        print(data_to_latex_table(data, columns, filename))
        self.assertEqual(data_to_latex_table(data, columns, filename), expected_output)
