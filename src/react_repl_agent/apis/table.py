import re

import duckdb
import pandas as pd

from react_repl_agent.utils.exceptions import SelfDescriptiveError

from .dict_keyerror_reference import DictWithKeyErrorReference


class SQLError(ValueError, SelfDescriptiveError):
    """SQL Error."""


class TableAttributeError(AttributeError, SelfDescriptiveError):
    """Invalid table attribute access."""


class TableIndexTypeError(TypeError, SelfDescriptiveError):
    """Invalid type in table indexing."""


class Table:
    """Custom table class. Interact with table via SQL queries."""

    _df: pd.DataFrame

    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df

    def __len__(self) -> int:
        return len(self._df)

    @property
    def columns(self) -> list[str]:
        return self._df.columns.values.tolist()

    def __repr__(self):
        columns = self.columns
        types = [str(d) for d in self._df.dtypes.tolist()]
        columns_with_types = [f"{c}: {t}" for c, t in zip(columns, types)]
        return f"<Table columns={columns_with_types!r}, len={len(self)})>"

    def __getattr__(self, name):
        raise TableAttributeError(
            f"`Table.{name}` does not exist! Only use `Table` as a parameter in other methods. "
            " Use `run_sql_query(table: Table, sql: str) -> Table` to execute a SQL query against the table, e.g. to select a column. Use `get_table_row(table: Table, row: int) -> dict` to select a row."
        )

    def __getitem__(self, idx: int):
        if not isinstance(idx, int):
            raise TableIndexTypeError(
                "Table indexing selects a row by its integer position."
                f" The index needs to be an int, got {type(idx).__name__!s} instead!"
                " If needed, use SQL queries via `run_sql_query(table: Table, sql: str) -> Table` to query, filter, select, or sort by, a specific column first!"
            )
        else:
            if idx < 0:
                raise IndexError("Table index needs to be a positive integer!")
            if len(self) == 0:
                raise IndexError("Table is empty!")
            if idx >= len(self):
                raise IndexError(f"Table index out of range! 0 <= idx < {len(self)}.")
            return DictWithKeyErrorReference(self._df.iloc[idx].to_dict())


def get_table_row(table: Table, row: int) -> dict:
    """
    Extract (select) the row at the given row index from the given table.

    Args:
        table (Table): Table to run SQL query against.
        row (int): Row index.

    Returns:
        Selected row as a dictionary.
    """
    return table[row]


def run_sql_query(table: Table, sql: str) -> Table:
    """
    Execute the given SQL query against the given table and return the resulting data as a new table. Use this to filter the table or select (extract) a specific column.

    Args:
        table (Table): Table to run SQL query against.
        sql_query (str): SQL to execute against the table.

    Returns:
        Result of running the SQL query as a new table.
    """
    if "datetime.now()" in sql or "timedelta(" in sql or "TIMEDELTA(" in sql:
        raise SQLError(
            r"Do not use `datetime` or `timedelta` directly in a SQL Query! Call them first and format the query string using the results! `.strftime('%Y-%m-%d %H:%M:%S')` can be used to format a datetime object. Make sure to pre-format all variables in the query string and use quotes if needed. No interpolation of any variables is done here."
        )
    if "relativedelta(" in sql or "RELATIVEDELTA(" in sql:
        raise SQLError(
            r"Do not use `relativedelta` directly in a SQL Query! Call python `datetime` or `timedelta` first and format the query string using the results! `.strftime('%Y-%m-%d %H:%M:%S')` can be used to format a datetime object. Make sure to pre-format all variables in the query string and use quotes if needed. No interpolation of any variables is done here."
        )
    sql = re.sub(r"FROM\s+\w+", r"FROM tbl", sql, flags=re.IGNORECASE).strip()
    tbl = table._df  # Make sure DataFrame is available at "tbl" for duckdb query
    assert isinstance(tbl, pd.DataFrame), "`tbl` is not a dataframe!"
    try:
        result_df = duckdb.query(sql).to_df()
    except duckdb.BinderException as exc:
        raise SQLError(
            f"Error Running SQL Query: {sql!r}!"
            f"\n{type(exc).__name__}: {exc!s}."
            "\nMake sure the `sql_query` string is preformatted in Python! Use `.strftime('%Y-%m-%d %H:%M:%S')` to format datetime objects if needed."
        ) from exc
    except duckdb.CatalogException as exc:
        if "datetime" in sql.lower() or "timedelta" in sql.lower():
            raise SQLError(
                f"Error Running SQL Query: {sql!r}!"
                f"\n{type(exc).__name__}: {exc!s}.\n"
                r"Do not use `datetime` or `timedelta` directly in a SQL Query! Call them first and format the query string using the results! `.strftime('%Y-%m-%d %H:%M:%S')` can be used to format a datetime object. Make sure to pre-format all variables in the query string and use quotes if needed. No interpolation of any variables is done here."
            ) from exc
        raise SQLError(
            f"Error Running SQL Query: {sql!r}!"
            f"\n{type(exc).__name__}: {exc!s}."
            "\nMake sure the SQL query is correct! Pre-format all variables in the query string and use quotes if needed."
        ) from exc
    except (duckdb.Error, ValueError) as exc:
        raise SQLError(
            f"Error Running SQL Query: {sql!r}!"
            f"\n{type(exc).__name__}: {exc!s}."
            "\nMake sure the SQL query is correct! Pre-format all variables in the query string and use quotes if needed."
        ) from exc
    return Table(result_df)

