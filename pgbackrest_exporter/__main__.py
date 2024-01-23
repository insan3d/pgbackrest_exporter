#!/usr/bin/env python3
# pylint: disable=wrong-import-position

"""
Executes provided commands, interprets output as pgBackRest JSON
status information and provides Prometheus-compatible
(application/openmetrics-text) metrics.
"""

__prog__ = "pgbackrest_exporter"
__version__ = "1.0.0"
__status__ = "Release"
__author__ = "Alexander Pozlevich"
__email__ = "a.pozlevich@big3.ru"

import pathlib
import sys

# Add program's path to PYTHONPATH to allow absolute imports from subdir in dev environment
sys.path.append(str(object=pathlib.Path(__file__).parent.parent.resolve()))


from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, ArgumentTypeError, Namespace
from contextlib import suppress
from logging import INFO, WARNING, Formatter, Logger, StreamHandler, getLogger

from aiohttp.web import run_app  # type: ignore
from aiohttp.web import Application, get
from prometheus_client import Info

from pgbackrest_exporter.server import serve_landing, serve_metrics, status_mw, timed_mw

logger: Logger = getLogger()

# Prepare own version metric
_info_labels: dict[str, str] = {"status": __status__, "version": __version__}
_info_labels.update(dict(zip(("major", "minor", "patchlevel"), __version__.split(sep="."))))
Info(name=f"{__prog__}", documentation=f"{__prog__} information").info(val=_info_labels)


def key_value(value: str) -> tuple[str, str]:
    """
    Validate `argparse` key-value pair argument.

    Args:
        value: raw value

    Returns:
        Tuple with key and value separated from input value by equals sign.
    """

    try:
        arg_key, arg_value = value.split(sep="=", maxsplit=1)

    except ValueError as exc:
        raise ArgumentTypeError("not a valid key-value pair") from exc

    return arg_key, arg_value


def make_argparser() -> ArgumentParser:
    """`argparse.ArgumentParser` factory for program."""

    parser = ArgumentParser(
        prog=__prog__,
        description=__doc__,
        epilog=f"Written by {__author__} <{__email__}>. (c) 2024 Big3.ru",
        formatter_class=lambda prog: ArgumentDefaultsHelpFormatter(prog=prog, max_help_position=33),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{__prog__} v{__version__} {__status__}",
    )
    parser.add_argument(
        "-V",
        "--verbose",
        action="store_true",
        help="produce verbose output",
    )

    server_args = parser.add_argument_group(title="server options")
    server_args.add_argument(
        "-H",
        "--host",
        metavar="host",
        default="0.0.0.0",
        help="specify host to bind to",
    )
    server_args.add_argument(
        "-P",
        "--port",
        metavar="port",
        type=int,
        default=8080,
        help="specify port to bind to",
    )
    server_args.add_argument(
        "-U",
        "--path",
        metavar="path",
        default="/metrics",
        help="specify path to serve metrics on",
    )

    exporter_args = parser.add_argument_group(
        title="exporter options",
        description="Arguments --command and --file receives key=value "
        "pair and can be repeated multiple times.",
    )
    exporter_args.add_argument(
        "-c",
        "--command",
        action="append",
        metavar="command",
        type=key_value,
        default=[],
        help="name of command and command to execute",
    )
    exporter_args.add_argument(
        "-f",
        "--file",
        action="append",
        metavar="file",
        type=key_value,
        default=[],
        help="name of command and file with command to execute",
    )

    return parser


def make_app(title: str, path: str, commands_dict: dict[str, str]) -> Application:
    """`aiohttp.web.Application` factory for program."""

    app = Application(logger=logger, middlewares=(status_mw, timed_mw))

    # Pass variables into app so they can be accessible via Request interface
    app["insan3d.pgbackrest_exporter.html.title"] = title
    app["insan3d.pgbackrest_exporter.html.metrics_path"] = path
    app["instan3d.pgbackrest_exporter.commands"] = commands_dict

    # Bind routes
    app.add_routes(
        routes=[get(path="/", handler=serve_landing), get(path=path, handler=serve_metrics)]
    )

    return app


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        # Prepare CLI argument parser
        argparser: ArgumentParser = make_argparser()
        args: Namespace = argparser.parse_args()

        # Build commands list from direct CLI args
        commands: dict[str, str] = {}
        for name, command in args.command:
            commands[name] = command

        # Build commands list from files
        for name, file in args.file:
            with open(file=file, mode="r", encoding="utf-8") as reader:
                commands[name] = reader.read().strip()

        # Assert at least one command provided
        if not commands:
            argparser.error(message="at least one --command or --file needed")

        # Prepare logger
        stdout_handler = StreamHandler()
        formatter = Formatter(
            fmt=r"%(asctime)s.%(msecs)d [%(levelname)s]: %(message)s", datefmt=r"%Y.%m.%d %H:%M:%S"
        )
        stdout_handler.setFormatter(fmt=formatter)
        logger.addHandler(hdlr=stdout_handler)
        logger.setLevel(level=INFO if args.verbose else WARNING)

        # Prepare application
        exporter: Application = make_app(title=__prog__, path=args.path, commands_dict=commands)

        # Run application
        logger.info("Exporting metrics on %s:%d%s", args.host, args.port, args.path)
        run_app(app=exporter, print=None)  # type: ignore
