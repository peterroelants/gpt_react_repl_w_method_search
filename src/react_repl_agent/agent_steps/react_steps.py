"""
Different steps of the ReAct agent.
"""
import ast
import logging
import re
from collections.abc import Callable
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from react_repl_agent.llm_api import call_model
from react_repl_agent.method_index.doc_utils import get_signature
from react_repl_agent.method_index.utils import (
    extract_method_signature_from_type_error,
)
from react_repl_agent.utils.exceptions import SelfDescriptiveError

from .repl_call_method import ActionTooLong, MethodCallOutput, execute_method

PROMPT_DIR = Path(__file__).resolve().parent / "prompts"

MAX_ACTION_LINES = 30


class ReActFinished(Exception):
    """Raised when the ReAct agent has finished its task."""

    action: Optional[str]
    thought: Optional[str]

    def __init__(
        self,
        message: str,
        action: Optional[str] = None,
        thought: Optional[str] = None,
    ):
        super().__init__(message)
        self.action = action
        self.thought = thought


# ReAct ############################################################
def react_initial_prompt(
    task: str,
    method_search_fun: Callable,
    current_loc_method: Callable,
) -> str:
    """
    Generate a first response to a task description.
    """
    method_search_full_signature = get_signature(method_search_fun)
    jinja_prompt_env = Environment(loader=FileSystemLoader(PROMPT_DIR))
    template = jinja_prompt_env.get_template("react_initial.jinja2")
    prompt = template.render(
        method_search_full_signature=method_search_full_signature,
        method_search_name=method_search_fun.__name__,
        current_loc_method=get_signature(current_loc_method),
        task_description=task,
    )
    return prompt.strip()


def react_step_1(
    task: str,
    method_search_fun: Callable,
    current_loc_method: Callable,
    context_dict: dict,
) -> tuple[str, int]:
    """
    Return the prompt for the first step of the task. Together with the next step index.

    The first step is to search for a method that can be applied to the first step of the task.
    """
    method_search_full_signature = get_signature(method_search_fun)
    # Setup ReAct prompt
    init_prompt = react_initial_prompt(
        task,
        method_search_fun,
        current_loc_method=current_loc_method,
    )
    # First step of the task to get a prompt that aligns more with our goal of executing tasks and method search.
    steps = decompose_task(task)
    first_step = steps[0].strip().strip(".")
    method_search_line = f'{method_search_fun.__name__}("{first_step!s}")'
    method_search_result = execute_method(
        method_call_str=method_search_line,
        context_dict=context_dict,
    )
    methods_str = method_search_result.stdout.strip()
    jinja_prompt_env = Environment(loader=FileSystemLoader(PROMPT_DIR))
    template = jinja_prompt_env.get_template("react_step_1.jinja2")
    steps_str = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
    prompt_step_1 = template.render(
        steps=steps_str,
        first_step=first_step,
        method_search_line=method_search_line,
        method_search_full_signature=method_search_full_signature,
        methods=methods_str,
    )
    step_idx = 2
    prompt = f"{init_prompt.strip()}\n{prompt_step_1.strip()}"
    return prompt, step_idx


# Others ###########################################################
def decompose_task(task: str) -> list:
    """
    Decompose a task description into a list of subtasks.
    """
    jinja_prompt_env = Environment(loader=FileSystemLoader(PROMPT_DIR))
    template = jinja_prompt_env.get_template("task_decomposition.jinja2")
    prompt = template.render(
        task=task.strip().strip(".") + ".",
    )
    steps, _ = call_model(
        prompt=prompt,
        max_tokens=250,
        stop_sequences=["\n\n"],
    )
    steps = steps.strip()
    return extract_ordered_list(steps)


def extract_ordered_list(list_str: str) -> list[str]:
    """
    Extract an ordered list from a string.

    E.g.
    >>> extract_ordered_list("1. First item\\n2. Second item\\n3. Third item")
    ['First item', 'Second item', 'Third item']
    """
    return [
        elem.strip()
        for elem in re.findall(
            r"^(?:\d+)\s*[\.\:\-]?\s*(.*)$", list_str, flags=re.MULTILINE
        )
    ]


# Action & Thought #################################################
def get_react_step(
    prompt_state: str,
    step_idx: int,
    context_dict: dict,
    method_search_fun: Callable,
) -> tuple[str, str, str, str]:
    """
    Single step in the ReAct loop.
    """
    # Get thought and action
    thought, action = get_thought_and_action(
        prompt_state=prompt_state,
        step_idx=step_idx,
    )
    try:
        # Check if the action is valid (not to long, no import)
        action, observation = check_action_nb_lines(action)
        # Check if the action contains an import statement
        action, observation = check_action_no_import(action, method_search_fun)
        # Get observation
        if observation is None:
            action, observation = get_observation(
                action=action,
                context_dict=context_dict,
                method_search_fun=method_search_fun,
            )
        prompt_state = (
            prompt_state.strip()
            + f"\nTHOUGHT {step_idx}:\n{thought}\n"
            + f"ACTION {step_idx}:\n```python\n{action}\n```\n"
            + f"OBSERVATION {step_idx}:\n{observation}\n"
        )
        return thought, action, observation, prompt_state
    except ReActFinished as exc:
        exc.action = action
        exc.thought = thought
        raise exc
    except Exception as exc:
        logging.error(f"Error in get_react_step: {exc!s}")
        logging.error(f"Current thought: '{thought!s}'")
        logging.error(f"Current action: '{action!s}'")
        raise exc


def check_action_nb_lines(action: str) -> tuple[str, Optional[str]]:
    """Check if the action is not too long."""
    observation = None
    lines = action.strip().splitlines()
    if len(lines) > MAX_ACTION_LINES:
        # Make sure we don't have too many lines (agent should take shorter actions)
        lines = lines[:MAX_ACTION_LINES]  # Max lines
        lines.append(
            f"# Code truncated at {MAX_ACTION_LINES} lines! Next time take shorter actions!"
        )
        lines.append("...")
        action = "\n".join(lines)
        exc = ActionTooLong(
            f"Too many lines in action! Only write maximum {MAX_ACTION_LINES} lines per action. Take simpler actions with less lines of code!"
        )
        observation = f"ERROR: {type(exc).__name__}: {exc!s}"
    return action, observation


def check_action_no_import(
    action: str,
    method_search_fun: Callable,
) -> tuple[str, Optional[str]]:
    """Check if the action contains an import statement."""
    method_search_full_signature = get_signature(method_search_fun)
    observation = None
    try:
        ImportAstWalker().visit(ast.parse(action, filename="<test>", mode="exec"))
    except ImportForbidden as exc:
        lines = action.strip().splitlines()
        line_no = exc.lineno
        last_line = exc.end_lineno
        if last_line is None:
            last_line = exc.lineno
        error_lines = "\n".join(lines[line_no - 1 : last_line])
        observation = (
            f"ERROR: ImportError: on line {line_no}: `{error_lines!r}` "
            "The Python `import` statement is disabled! Don't import anything, only use available methods! "
            f"Available methods that don't need to be imported, can be found by running `{method_search_full_signature}`."
        )
        action = "\n".join(lines[:last_line])
    except Exception:
        pass  # Ignore, the error will surface when executing the action
    return action, observation


class ImportForbidden(ImportError, SelfDescriptiveError):
    """Imports in the actions are disabled!"""

    def __init__(self, message, lineno: int, end_lineno: Optional[int] = None):
        super().__init__(message)
        self.lineno = lineno
        self.end_lineno = end_lineno


class ImportAstWalker(ast.NodeVisitor):
    """AST walker to check for imports."""

    def visit_Import(self, node):
        raise ImportForbidden(
            "Import not allowed!", lineno=node.lineno, end_lineno=node.end_lineno
        )

    def visit_ImportFrom(self, node):
        raise ImportForbidden(
            "Import not allowed!", lineno=node.lineno, end_lineno=node.end_lineno
        )


# Observation ######################################################
def get_thought_and_action(prompt_state: str, step_idx: int) -> tuple[str, str]:
    """Get ReAct Thought and Action."""
    thought_prefix = "Based on previous observations, "
    thought_prompt = f"\nTHOUGHT {step_idx}:\n{thought_prefix}"
    prompt_state = prompt_state + thought_prompt
    result, _ = call_model(
        prompt=prompt_state,
        max_tokens=1024,
        stop_sequences=["\nOBSERVATION"],
    )
    thought_and_action = result.strip()
    # Extract thought and action
    re_matches = re.match(
        r"\s*(.*)\s*ACTION [0-9N]+:\s*```(?:python)?(.*)(?:```)?\s*$",
        thought_and_action,
        re.DOTALL,
    )
    assert (
        re_matches
    ), f"Could not extract thought and action from: \n{thought_and_action}\n!"
    thought, action = re_matches.groups()
    thought = thought_prefix + thought
    action = action.strip().strip("`").strip()
    return thought.strip(), action.strip()


def get_observation(
    action: str,
    context_dict: dict,
    method_search_fun: Callable,
) -> tuple[str, str]:
    """Get the observation from running the action."""
    # Execute action
    action_output = execute_method(
        method_call_str=action,
        context_dict=context_dict,
    )
    stdout = action_output.stdout.strip()
    stderr = action_output.stderr.strip()
    observation = stdout
    if stderr:
        observation += f"\nERROR: {stderr!s}"
    # Observation is empty
    if not action_output.has_error and not observation:
        observation = "Action executed successfully! No output in stdout/stderr. Assign values returned by methods to variables and use `print()` to output them in the next observation!"
    # Check if there was an error
    if action_output.has_error:
        observation += handle_observation_error(
            action=action,
            action_output=action_output,
            context_dict=context_dict,
            method_search_fun=method_search_fun,
        )
    return action, observation.strip()


def handle_observation_error(
    action: str,
    action_output: MethodCallOutput,
    context_dict: dict,
    method_search_fun: Callable,
) -> str:
    """Handle errors in the observation by providing custom error messages to nudge the agent in the right direction."""
    method_search_full_signature = get_signature(method_search_fun)
    # Display extra information nudging the agent toward the right direction when an exception occurs
    assert action_output.exception
    assert action_output.exception_lineno
    # Strip action until error
    action = "\n".join(action.splitlines()[: action_output.exception_lineno])
    # Check if the agent wants to stop.
    if isinstance(action_output.exception, ReActFinished):
        # Finish run
        raise action_output.exception
    if isinstance(action_output.exception, SelfDescriptiveError):
        return ""  # Custom exception that contains all information needed
    elif isinstance(action_output.exception, NameError):
        return (
            "\nOnly call available methods and make sure variables are defined!"
            + f"\nTo find new methods, use the `{method_search_full_signature}` method in the next action to search for available methods!"
        )
    elif isinstance(action_output.exception, TypeError):
        method_signature = extract_method_signature_from_type_error(
            action_output.exception, context_dict
        )
        if method_signature:
            return (
                "\nMake sure methods are called correctly by paying attention to the signature!"
                f"\nThe method signature is: `{method_signature}`."
            )
        else:
            return (
                "\nMake sure methods are called correctly by paying attention to the signature!"
                f"\nUse the `{method_search_full_signature}` method in the next action to search for available methods and their signatures!"
            )
    elif isinstance(action_output.exception, AttributeError):
        return (
            "\nThe method or attribute is not available for the object!"
            f"\nUse the `{method_search_full_signature}` method in the next action to search for available methods!"
        )
    elif isinstance(action_output.exception, KeyError):
        return "\nInvalid key! Use `print(var)` on the variable being indexed to output it in the next observation!"
    elif isinstance(action_output.exception, IndexError):
        return "\nUse `print(var)` on the variable being indexed to output it in the next observation!"
    elif isinstance(action_output.exception, LookupError):
        return "\nUse `print(var)` on the variable being accessed to output it in the next observation!"
    elif isinstance(action_output.exception, IndentationError):
        return "\nWrite simple code!"
    else:
        return (
            "\nMake sure methods are called correctly! Print variables to to get their structure!"
            f"\nIf needed, use the `{method_search_full_signature}` method in the next action to search for available methods!"
        )
