# Tools

Project tools to help format and test code.

Run formatting, linting, and unit tests:

```
./tools/run_all.sh
```

## Tools used:

* Standardized code formatting: [`black`](https://black.readthedocs.io/en/stable/)
* Static analysis / linting / style guide enforcement/ formatting: [`ruff`](https://beta.ruff.rs/)
* Static type checking: [`mypy`](http://mypy-lang.org/)


###Git pre-commit hooks

This repository uses the [pre-commit](https://pre-commit.com/) library to setup [Git Hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks). The pre-commit scripts can be setup by running:

```
conda run -n react_repl_agent pre-commit install
```
