import re

from IPython.display import Markdown, display


class MdLogger:
    """Logger that displays Markdown strings."""

    def __init__(self):
        self.log = ""

    def display(self, s: str):
        self.log += "\n" + s
        display(Markdown(str(s)))

    def display_react(self, s: str):
        self.display(react_to_md(s))


def react_to_md(s: str) -> str:
    """Convert ReAct output to Markdown."""
    # Add extra newlines before sections
    s = re.sub(r"\nTHOUGHT", r"\n\nTHOUGHT", s.strip())
    s = re.sub(r"\nACTION", r"\n\nACTION", s.strip())
    s = re.sub(r"\nOBSERVATION", r"\n\nOBSERVATION", s.strip())
    return s
