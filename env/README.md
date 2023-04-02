# Python Environment

## Conda environment

The provided conda environment at `react_repl_agent.yml` can be built and activated locally if you have [mamba](https://mamba.readthedocs.io/en/latest/) or [conda](https://docs.conda.io/en/latest/) installed (in replace `mamba` by `conda` in that case), by running the following from the project root:
```
mamba env create --file ./env/react_repl_agent.yml
conda activate react_repl_agent
```

And can be cleaned up afterwards with:
```
conda deactivate && conda remove --yes --name react_repl_agent --all
```

More info how to work with conda/mamba:
* [Conda Cheatsheet](https://docs.conda.io/projects/conda/en/latest/_downloads/843d9e0198f2a193a3484886fa28163c/conda-cheatsheet.pdf)


### Local package

The local package at `./src/react_repl_agent` can be installed with `pip install --editable .`, this makes all the packages importable and editable while preventing any issues with mis-specified PythonPath variables.


## Pre-commit hooks
[Pre-commit](https://pre-commit.com/) [hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks) can be setup using:
```
conda run -n react_repl_agent pre-commit install
```
