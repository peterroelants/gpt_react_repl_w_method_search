from react_repl_agent.utils.exceptions import SelfDescriptiveError


class DictWithKeyErrorReference(dict):
    """Dictionary with custom KeyError referencing the dictionary."""

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError as e:
            raise KeyErrorWithDict(key, self) from e


class KeyErrorWithDict(KeyError, SelfDescriptiveError):
    """
    Dictionary key error with dictionary attached.
    """

    def __init__(self, key, dict_):
        super().__init__(key)
        self.dict_ = dict_

    def __str__(self):
        return f"Key `{self.args[0]!r}` does not exist! Available keys are: {list(self.dict_.keys())!r}"
