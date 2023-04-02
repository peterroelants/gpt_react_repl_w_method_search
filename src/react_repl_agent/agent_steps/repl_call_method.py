"""
Execute python code in a REPL environment.
"""
import contextlib
import io
import traceback
from typing import NamedTuple, Optional

from react_repl_agent.utils.exceptions import SelfDescriptiveError


class ActionTooLong(SelfDescriptiveError):
    """Action (Python code) is too long"""


class MethodCallOutput(NamedTuple):
    """Output of running code in a REPL environment."""

    stdout: str
    stderr: str
    has_error: bool
    exception: Optional[Exception]
    exception_lineno: Optional[int]


def execute_method(
    method_call_str: str,
    context_dict: dict,
) -> MethodCallOutput:
    """
    Run code and collect output, any exceptions, and variable assignment.
    """
    # `method_call_str` needs to have a variable assignment on the last line,
    # This can be enforced with `enforce_assignment_last_line`, however don't do that here atm
    # because we want the code change to be part of the prompt
    method_call_str = method_call_str.strip()
    has_error = False
    exception = None
    exception_lineno = None
    with contextlib.redirect_stdout(io.StringIO()) as stdout:
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            try:
                exec(method_call_str, context_dict)
            except Exception as exc:
                has_error = True
                exception = exc
                # This only prints exception type and message, not full stacktrace
                # Get line number of index 1 in traceback, which is the line where the exception occurred in the action executed in `exec`
                exception_lineno = traceback.extract_tb(exc.__traceback__)[1].lineno
                assert isinstance(exception_lineno, int)  # For mypy
                exc_type = type(exc).__name__
                error_line = method_call_str.splitlines()[exception_lineno - 1].strip()
                exc_error_description = (
                    f"{exc_type} on line {exception_lineno}: `{error_line}`: {exc!s}"
                )
                print(exc_error_description, file=stderr)
    exec_stdout = stdout.getvalue()
    exec_stderr = stderr.getvalue()
    return MethodCallOutput(
        stdout=exec_stdout,
        stderr=exec_stderr,
        has_error=has_error,
        exception=exception,
        exception_lineno=exception_lineno,
    )
