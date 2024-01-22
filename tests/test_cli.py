"""Tests for CLI interface."""

from argparse import ArgumentParser, ArgumentTypeError

import pytest

from pgbackrest_exporter import __main__ as main

EXPECTED: dict[str, str | int | list[tuple[str, str]]] = {
    "host": "0.0.0.0",
    "port": 8080,
    "path": "/mertics",
    "command": [("cfoo", "cbar"), ("cbar", "cbaz")],
    "file": [("ffoo", "fbar"), ("fbar", "fbaz")],
}


def test_kv_validation_valid() -> None:
    """Test argument validator on valid value."""

    test_k, test_v = main.key_value(value="k=v")
    assert test_k == "k" and test_v == "v"


def test_kv_validattion_invalid() -> None:
    """Test argument validator on invalid value."""

    with pytest.raises(expected_exception=ArgumentTypeError):
        main.key_value(value="kv")


def test_short_args() -> None:
    """Test short arguments form."""

    parser: ArgumentParser = main.make_argparser()
    args = "-H 0.0.0.0 -P 8080 -U /mertics -c cfoo=cbar -c cbar=cbaz -f ffoo=fbar -f fbar=fbaz"

    parsed: dict[str, str | int | list[tuple[str, str]]] = vars(parser.parse_args(args=args.split(sep=" ")))
    for key, value in EXPECTED.items():
        assert parsed[key] == value


def test_long_args() -> None:
    """Test long arguments form."""

    parser: ArgumentParser = main.make_argparser()
    args = "--host 0.0.0.0 --port 8080 --path /mertics --command cfoo=cbar --command cbar=cbaz --file ffoo=fbar --file fbar=fbaz"

    parsed: dict[str, str | int | list[tuple[str, str]]] = vars(parser.parse_args(args=args.split(sep=" ")))
    for key, value in EXPECTED.items():
        assert parsed[key] == value
