import ast
import inspect
import re
from typing import Callable, NamedTuple


class MethodDoc(NamedTuple):
    """Documentation of a method."""

    method: Callable
    name: str
    signature: str
    description: str
    doc: str


def get_signature(method: Callable) -> str:
    """Get method signature as a string."""
    method_def = ast.parse(inspect.getsource(method).strip()).body[0]
    # Clear body to keep only the signature
    method_def.body = []  # type: ignore
    signature = str(ast.unparse(method_def))
    signature = signature.removeprefix("def").rstrip(":").strip()
    return signature


def get_doc_str(method):
    """Get docstring of given method."""
    return inspect.getdoc(method).strip()


def get_method_description(method: Callable) -> str:
    """Get method description (first line of docstring)."""
    docstr = get_doc_str(method)
    return parse_method_description(docstr)


def parse_method_description(docstr):
    return re.sub("\n(?:Args:|Returns:).*", "", docstr, flags=re.DOTALL).strip()


def get_full_doc(method: Callable) -> MethodDoc:
    """
    Get documentation of given method.

    Alternatives:
    - pydoc.render_doc
    - help()
    """
    # assert method.example_queries
    method_name = method.__name__
    full_signature = get_signature(method)
    docstr = get_doc_str(method)
    description = parse_method_description(docstr)
    return MethodDoc(
        method=method,
        name=method_name,
        signature=full_signature,
        description=description,
        doc=docstr,
    )
