from typing import Any, List
from pylatex import Document
from pylatex.table import Tabularx


def data_to_latex_table(data: List[List[Any]], columns: List[str], filename: str) -> str:
    doc: Document = Document(filename)

    # Generate column format string based on number of columns
    col_format = " ".join(["lX"] * len(columns))

    with doc.create(Tabularx(col_format, width=len(columns))) as table:
        table.add_hline()
        table.add_row([col.replace('_', ' ') for col in columns])
        table.add_hline()
        table.add_hline()

        for datum in data:
            table.add_row(datum)

        table.add_hline()
        table.add_hline()

    return doc.dumps()
