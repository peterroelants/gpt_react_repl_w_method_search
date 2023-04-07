# ReAct REPL Agent

Large-language model based "agent" that can can execute small tasks by using a Python REPL and pre-implemented methods. The "agent loop" is based on [ReAct](https://arxiv.org/abs/2210.03629).

The agent can look up methods using a `method_search()` method that uses semantic search on the indexed Python methods. Methods are indexed using OpenAI embedding of their signatures and descriptions.

More details in the blogpost at https://peterroelants.github.io/posts/react-repl-agent/

## Run yourself

There are 2 notebooks to run the agent:
- Run on single task [notebooks/react_repl_agent.ipynb](notebooks/react_repl_agent.ipynb)
- Uses [Papermill](https://papermill.readthedocs.io/en/latest/) to run a batch of tasks [notebooks/run_batch.ipynb](notebooks/run_batch.ipynb)

### Environment

A conda/mamba environment is provided at [env/](env/).

Certain libraries (such as the [openai library](https://platform.openai.com/docs/libraries)) need a secret key to use them. These should be added to the [secrets/](secrets/) directory.


## Contribute

If you want to contribute, please do so via pull requests.

### Tools
To run all code formatting and linters before pushing a commit run:
```
./tools/run_all.sh
```
