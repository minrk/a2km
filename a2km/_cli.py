from __future__ import annotations

import argparse
import logging
import os
import sys
from functools import wraps
from subprocess import CalledProcessError

import a2km
from a2km import operations


def _quieter_errors(f):
    # quieter messages for expected errors
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except (OSError, CalledProcessError) as e:
            sys.exit(str(e))

    return wrapped


def _subcommand(subparsers, name: str, method_name: str | None = None):
    """Add a subcommand"""
    if method_name is None:
        method_name = name.replace("-", "_")
    op = getattr(operations, method_name)
    parser = subparsers.add_parser(name, help=op.__doc__)
    parser.set_defaults(operation=op)
    return parser


def _kernelspec_arg(
    parser: argparse.ArgumentParser, help: str = "A kernelspec name or path"
) -> None:
    parser.add_argument("kernelspec", type=str, help=help)


@_quieter_errors
def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser("a2km")
    parser.add_argument("--version", action="version", version=a2km.__version__)
    parser.add_argument("--debug", action="store_true")
    parser.set_defaults(operation=None)
    subparsers = parser.add_subparsers(
        title="commands",
        description="available commands",  # , required=True
    )

    locate = _subcommand(subparsers, "locate")
    _kernelspec_arg(locate)

    show = _subcommand(subparsers, "show")
    _kernelspec_arg(show)
    show.add_argument(
        "--json", action="store_true", help="Output the kernelspec as JSON"
    )

    clone = _subcommand(subparsers, "clone")
    _kernelspec_arg(clone, help="The kernelspec to clone")
    clone.add_argument("to", help="The name (or full path) to clone KERNELSPEC to")

    set_cmd = _subcommand(subparsers, "set")
    _kernelspec_arg(set_cmd)
    set_cmd.add_argument("key", type=str, help="field to set (e.g. 'display_name')")
    set_cmd.add_argument("value", type=str, help="value to set (e.g. 'My Kernel')")

    add_env = _subcommand(subparsers, "add-env")
    _kernelspec_arg(add_env)
    add_env.add_argument(
        "env",
        nargs="+",
        help="env vars to add. Of the form `env=value` or `env` to inherit from current env.",
    )

    rm_env = _subcommand(subparsers, "rm-env", "remove_env")
    _kernelspec_arg(rm_env)
    rm_env.add_argument(
        "env",
        nargs="+",
        help="env vars to remove.",
    )

    add_argv = _subcommand(subparsers, "add-argv")
    _kernelspec_arg(add_argv)
    add_argv.add_argument(
        "args",
        nargs="+",
        help="cli args to add.",
    )

    rm_argv = _subcommand(subparsers, "rm-argv", "remove_argv")
    _kernelspec_arg(rm_argv)
    rm_argv.add_argument(
        "args",
        nargs="+",
        help="cli args to remove.",
    )

    env_kernel = _subcommand(subparsers, "env-kernel")
    env_kernel.add_argument("env", help="Path or name of an environment")
    env_kernel.add_argument(
        "--kind",
        choices={"conda", "venv"},
        default="conda",
        help="The kind of environment",
    )
    env_kernel.add_argument("--name", default="", help="The kernel name to register")
    env_kernel.add_argument(
        "--prefix",
        default="sys-prefix",
        help="The install prefix. Can be 'user' for a per-user install 'sys-prefix' for the same installation prefix as the a2km tool (default), or a path to an installation prefix.",
    )

    rm = _subcommand(subparsers, "rm", "remove")
    _kernelspec_arg(rm)
    rm.add_argument(
        "--force", action="store_true", help="Skip confirmation before removal."
    )

    options = parser.parse_args(argv)
    if options.debug:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(level=level, format="%(message)s")

    op = options.operation
    if op is operations.locate:
        print(operations.locate(options.kernelspec))
    elif op is operations.show:
        operations.show(options.kernelspec, options.json)
    elif op is operations.clone:
        operations.clone(options.kernelspec, options.to)
    elif op is operations.set:
        operations.set(options.kernelspec, {options.key: options.value})
    elif op is operations.add_env:
        new_env = {}
        for assignment in options.env:
            key, sep, value = assignment.partition("=")
            if not sep:
                try:
                    value = os.environ[key]
                except KeyError:
                    sys.exit(f"No such env set: {key}")
            new_env[key] = value
        operations.add_env(options.kernelspec, new_env)
    elif op is operations.remove_env:
        operations.remove_env(options.kernelspec, options.env)
    elif op is operations.add_argv:
        operations.add_argv(options.kernelspec, options.args)
    elif op is operations.remove_argv:
        operations.remove_argv(options.kernelspec, options.args)
    elif op is operations.env_kernel:
        operations.env_kernel(
            options.env,
            kind=options.kind,
            kernel_name=options.name,
            install_prefix=options.prefix,
        )
    elif op is operations.remove:
        operations.remove(options.kernelspec, options.force)
    else:
        sys.exit(f"Specify an operation, one of: {', '.join(subparsers.choices)}")


if __name__ == "__main__":
    main()
