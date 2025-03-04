import os
import sys
from contextlib import nullcontext
from subprocess import check_output
from unittest import mock

import pytest

from a2km._cli import main


def run(*cmd, **kwargs):
    return check_output([sys.executable, "-m", "a2km"] + list(cmd), **kwargs)


def test_help():
    run("--help")


def test_version():
    run("--version")


def cli_test(args, name, called_with=None):
    if (
        called_with is not None
        and isinstance(called_with, type)
        and issubclass(called_with, BaseException)
    ):
        ctx = pytest.raises(called_with)
        called_with = None
    else:
        ctx = nullcontext()
    with ctx, mock.patch(f"a2km.operations.{name}", autospec=True) as mocked:
        main(args)
    if called_with is not None:
        if (
            len(called_with) == 2
            and isinstance(called_with[0], tuple)
            and isinstance(called_with[1], dict)
        ):
            call_args, call_kwargs = called_with
        else:
            call_args = called_with
            call_kwargs = {}
        mocked.assert_called_with(*call_args, **call_kwargs)
    return mocked


def test_locate():
    cli_test(["locate", "foo"], "locate", ["foo"])


@pytest.mark.parametrize(
    "args, called_with",
    [
        pytest.param(["foo"], ["foo", False], id="default"),
        pytest.param(["foo", "--json"], ["foo", True], id="--json"),
    ],
)
def test_show(args, called_with):
    cli_test(["show"] + args, "show", called_with)


@pytest.mark.parametrize(
    "args, called_with",
    [
        pytest.param(["from", "to"], ["from", "to"], id="basic"),
        pytest.param(["from"], SystemExit, id="missing TO"),
    ],
)
def test_clone(args, called_with):
    cli_test(["clone"] + args, "clone", called_with)


@pytest.mark.parametrize(
    "args, called_with",
    [
        pytest.param(
            ["spec", "display_name", "bar"],
            ("spec", {"display_name": "bar"}),
            id="basic",
        ),
        pytest.param(["spec"], SystemExit, id="no args"),
        pytest.param(["spec", "key"], SystemExit, id="missing value"),
    ],
)
def test_set(args, called_with):
    cli_test(["set"] + args, "set", called_with)


@pytest.mark.parametrize(
    "args, called_with",
    [
        pytest.param(["spec", "key=value"], ("spec", {"key": "value"}), id="basic"),
        pytest.param(
            ["spec", "key=value=double", "from_env"],
            ("spec", {"key": "value=double", "from_env": "found"}),
            id="from env",
        ),
        pytest.param(["spec"], SystemExit, id="no args"),
        pytest.param(["spec", "not_from_env"], SystemExit, id="missing key"),
    ],
)
def test_add_env(args, called_with):
    with mock.patch.dict(os.environ, {"from_env": "found"}):
        cli_test(["add-env"] + args, "add_env", called_with)


@pytest.mark.parametrize(
    "args, called_with",
    [
        pytest.param(["spec", "key", "value"], ("spec", ["key", "value"]), id="basic"),
        pytest.param(["spec"], SystemExit, id="no args"),
    ],
)
def test_rm_env(args, called_with):
    cli_test(["rm-env"] + args, "remove_env", called_with)


@pytest.mark.parametrize(
    "args, called_with",
    [
        pytest.param(["spec", "arg1", "arg2"], ("spec", ["arg1", "arg2"]), id="basic"),
        pytest.param(["spec"], SystemExit, id="no args"),
    ],
)
def test_add_argv(args, called_with):
    cli_test(["add-argv"] + args, "add_argv", called_with)


@pytest.mark.parametrize(
    "args, called_with",
    [
        pytest.param(["spec", "arg1", "arg2"], ("spec", ["arg1", "arg2"]), id="basic"),
        pytest.param(["spec"], SystemExit, id="no args"),
    ],
)
def test_rm_argv(args, called_with):
    cli_test(["rm-argv"] + args, "remove_argv", called_with)


@pytest.mark.parametrize(
    "args, called_with",
    [
        pytest.param(["spec"], ("spec", False), id="default"),
        pytest.param(["spec", "--force"], ("spec", True), id="--force"),
        pytest.param([], SystemExit, id="no args"),
    ],
)
def test_rm(args, called_with):
    cli_test(["rm"] + args, "remove", called_with)


@pytest.mark.parametrize(
    "args, called_with",
    [
        pytest.param(
            ["env"],
            (
                ("env",),
                {
                    "kind": "conda",
                    "kernel_name": "",
                    "install_prefix": "sys-prefix",
                },
            ),
            id="default",
        ),
        pytest.param(
            ["env", "--name=mykernel", "--prefix", "user"],
            (
                ("env",),
                {
                    "kind": "conda",
                    "kernel_name": "mykernel",
                    "install_prefix": "user",
                },
            ),
            id="default",
        ),
        pytest.param([], SystemExit, id="no args"),
    ],
)
def test_env_kernel(args, called_with):
    cli_test(["env-kernel"] + args, "env_kernel", called_with)
