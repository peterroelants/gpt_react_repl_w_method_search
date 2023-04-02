import logging
from datetime import datetime, timedelta, timezone
from typing import Callable

from react_repl_agent.agent_steps.react_steps import ReActFinished
from react_repl_agent.apis.discord import send_message_discord
from react_repl_agent.apis.image import download_image, shrink_image
from react_repl_agent.apis.location import (
    get_user_location,
    search_location_geocoordinates,
)
from react_repl_agent.apis.nasa import get_nasa_astronomy_picture_of_the_day
from react_repl_agent.apis.open_meteo import (
    get_current_weather,
    get_daily_weather_forecast,
)
from react_repl_agent.apis.slack import (
    get_slack_channel_id,
    send_slack_image,
    send_slack_message,
)
from react_repl_agent.apis.stock_prices import get_weekly_stock_price
from react_repl_agent.apis.table import (
    get_table_row,
    run_sql_query,
)
from react_repl_agent.method_index.doc_utils import (
    MethodDoc,
    get_full_doc,
)
from react_repl_agent.method_index.index_methods import MethodsVectorIndex


def get_method_index() -> tuple[Callable[[str], None], dict]:
    """Method search function, and REPL context."""
    # Index methods
    method_docs = [
        # open_meteo
        get_full_doc(get_current_weather),
        get_full_doc(get_daily_weather_forecast),
        # Location
        get_full_doc(search_location_geocoordinates),
        get_full_doc(get_user_location),
        # Slack
        get_full_doc(get_slack_channel_id),
        get_full_doc(send_slack_message),
        get_full_doc(send_slack_image),
        # Discord
        get_full_doc(send_message_discord),
        # NASA
        get_full_doc(get_nasa_astronomy_picture_of_the_day),
        # Image
        get_full_doc(download_image),
        get_full_doc(shrink_image),
        # Table
        get_full_doc(run_sql_query),
        get_full_doc(get_table_row),
        # Stock prices
        get_full_doc(get_weekly_stock_price),
        # Date (Also injected into context)
        MethodDoc(
            method=datetime.now,
            name="datetime.now",
            signature="datetime.now() -> datetime",
            description="Return a datetime object representing the current date and time.",
            doc="",
        ),
        MethodDoc(
            method=datetime,
            name="datetime",
            signature="datetime(year, month, day[, hour[, minute[, second[, microsecond[,tzinfo]]]]])",
            description="Return a datetime object representing given date and time.",
            doc="",
        ),
        MethodDoc(
            method=datetime.strftime,
            name="datetime.strftime",
            signature="datetime.strftime(format)",
            description="Return a string representing the date and time.",
            doc="",
        ),
        MethodDoc(
            method=timedelta,
            name="timedelta",
            signature="timedelta(**kwargs) -> timedelta",
            description="Represent the difference between two datetime objects.",
            doc="",
        ),
        # Stop
        get_full_doc(stop),
    ]
    logging.info(f"Create index with {len(method_docs)} methods.")
    # Create index
    method_search = get_method_search(method_docs)
    # Create context dictionary for the REPL
    context_dict = {m.name: m.method for m in method_docs}
    context_dict["datetime"] = datetime
    context_dict["timezone"] = timezone
    context_dict["method_search"] = method_search
    # overwrite some builtins
    context_dict["open"] = open_disabled
    context_dict["exec"] = exec_disabled
    context_dict["breakpoint"] = breakpoint_disabled
    context_dict["eval"] = eval_disabled
    context_dict["compile"] = compile_disabled
    context_dict["input"] = input_disabled
    return method_search, context_dict


def open_disabled(*args, **kwargs):
    raise NameError("open() is disabled!")


def exec_disabled(*args, **kwargs):
    raise NameError("exec() is disabled!")


def breakpoint_disabled(*args, **kwargs):
    raise NameError("breakpoint() is disabled!")


def eval_disabled(*args, **kwargs):
    raise NameError("eval() is disabled!")


def compile_disabled(*args, **kwargs):
    raise NameError("compile() is disabled!")


def input_disabled(*args, **kwargs):
    raise NameError("input() is disabled!")


def get_method_search(method_docs: list[MethodDoc]) -> Callable[[str], None]:
    """Create method search function."""
    index = MethodsVectorIndex(method_docs)

    def method_search(description: str):
        topk = 3
        docs, _, _ = index.search(description, topk=topk)
        signature_and_descriptions = [
            f"`{d.signature}`: {d.description.strip('.')}." for d in docs
        ]
        assert len(signature_and_descriptions) == topk
        # Print to StdOut of REPL for agent to read
        print("\n".join(signature_and_descriptions))

    return method_search


def stop():
    """Task has been finished completely."""
    raise ReActFinished("ReAct Agent has finished the task! `stop()` called by agent.")
