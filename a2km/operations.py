from __future__ import annotations

import copy
import io
import json
import logging
import os
import secrets
import shlex
import shutil
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from subprocess import check_output
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any

from jupyter_core import paths

if TYPE_CHECKING:
    import io

    _PathLike = Path | str

log = logging.getLogger(__name__)


def locate(kernelspec: _PathLike) -> Path:
    """Resolve a kernelspec name to a path"""

    kernelspec_path = Path(kernelspec)
    if kernelspec_path.exists():
        return kernelspec_path

    kernels_path = paths.jupyter_path("kernels")
    for kernels_dir in kernels_path:
        kernelspec_path = Path(kernels_dir) / kernelspec
        if kernelspec_path.exists():
            return kernelspec_path.absolute()

    raise FileNotFoundError(f"No {kernelspec} found on {os.pathsep.join(kernels_path)}")


def show(kernelspec: _PathLike, json_output: bool = False) -> None:
    """Display information about a kernelspec"""
    kernelspec_path = locate(kernelspec)
    kernelspec_json = kernelspec_path / "kernel.json"
    with kernelspec_json.open() as f:
        spec = json.load(f)
    if json_output:
        json.dump(spec, sys.stdout, indent=1)
        return
    print(
        f"Kernel: {kernelspec_path.name} ({spec.get('display_name', '<no display name>')})"
    )
    print(f"  path: {kernelspec_path}")
    print(f"  argv: {shlex.join(spec['argv'])}")


def rename(kernelspec: _PathLike, new_name: str) -> Path:
    """Rename a kernelspec"""
    kernelspec = locate(kernelspec)
    dest = Path(new_name)
    if dest.name == new_name:
        dest = kernelspec.parent / new_name
    else:
        dest = dest.absolute()
    log.info("Renaming %s -> %s", kernelspec, dest)
    kernelspec.rename(dest)
    return dest


@contextmanager
def _atomic_write(path: Path) -> Generator[io.TextIOWrapper]:
    """Open a file for atomic writing

    Completes write to a temporary file before
    overwriting original file

    avoids corrupting files with failed or partial writes
    """
    write_path = path.with_suffix(path.suffix + ".a2km." + secrets.token_urlsafe(3))
    log.debug("Writing  temporary file %s", write_path)
    try:
        with write_path.open("w") as f:
            yield f
        write_path.rename(path)
    finally:
        try:
            log.debug("Removing temporary file %s", write_path)
            write_path.unlink()
        except FileNotFoundError:
            pass


def _write_kernelspec(kernelspec: _PathLike, new_spec: dict) -> None:
    kernel_json_path = locate(kernelspec) / "kernel.json"
    log.info("Updating %s", kernel_json_path)
    with _atomic_write(kernel_json_path) as f:
        # do not sort keys,
        # that way we should _usually_ preserve read order
        json.dump(new_spec, f, sort_keys=False, indent=1)


def _read_kernelspec(kernelspec: _PathLike):
    kernelspec_path = locate(kernelspec)
    kernel_json_path = kernelspec_path / "kernel.json"
    with kernel_json_path.open() as f:
        return json.load(f)


def set(kernelspec: _PathLike, to_set: dict[str, Any]) -> None:
    """Set fields in a kernelspec file"""
    kernelspec = locate(kernelspec)
    spec = _read_kernelspec(kernelspec)
    before = copy.deepcopy(spec)
    spec.update(to_set)
    if spec != before:
        _write_kernelspec(kernelspec, spec)
    else:
        log.info("No change to %s", kernelspec)


def add_env(kernelspec: _PathLike, new_env: dict[str, str]) -> None:
    """Add environment variables to a kernelspec"""
    kernelspec = locate(kernelspec)
    spec = _read_kernelspec(kernelspec)
    if "env" not in spec:
        spec["env"] = {}
    before_env = spec["env"].copy()
    spec["env"].update(new_env)
    if before_env != spec["env"]:
        _write_kernelspec(kernelspec, spec)
    else:
        log.info("No change to %s", kernelspec)


def remove_env(kernelspec: _PathLike, env_keys: list[str]) -> None:
    """Remove environment variables from a kernelspec"""
    kernelspec = locate(kernelspec)
    spec = _read_kernelspec(kernelspec)
    if "env" not in spec:
        log.info("No change to %s", kernelspec)
        return
    env = spec["env"]
    any_removed = False
    for key in env_keys:
        if key in env:
            any_removed = True
            del env[key]

    if any_removed:
        _write_kernelspec(kernelspec, spec)
    else:
        log.info("No change to %s", kernelspec)


def add_argv(kernelspec: _PathLike, to_add: list[str]) -> None:
    """Add cli arguments to a kernelspec"""
    kernelspec = locate(kernelspec)
    spec = _read_kernelspec(kernelspec)
    if "argv" not in spec:
        raise KeyError(f"kernelspec {kernelspec} doesn't have 'argv'")
    spec["argv"].extend(to_add)
    log.info("New argv: %s", shlex.join(spec["argv"]))
    _write_kernelspec(kernelspec, spec)


def remove_argv(kernelspec: _PathLike, to_remove: list[str]) -> None:
    """Remove cli arguments from a kernelspec"""
    kernelspec = locate(kernelspec)
    spec = _read_kernelspec(kernelspec)
    if "argv" not in spec:
        raise KeyError(f"kernelspec {kernelspec} doesn't have 'argv'")
    any_removed = False
    for arg in to_remove:
        try:
            spec["argv"].remove(arg)
        except ValueError:
            pass
        else:
            any_removed = True
    if any_removed:
        log.info("New argv: %s", shlex.join(spec["argv"]))
        _write_kernelspec(kernelspec, spec)
    else:
        log.info("No change to %s", kernelspec)


def remove(kernelspec: _PathLike, force: bool = False) -> None:
    """Remove a kernelspec"""
    kernelspec = locate(kernelspec)
    if not force:
        ans = input(f"Remove {kernelspec} [y/N]? ")
        if not ans.lower().startswith("y"):
            print("Operation cancelled", file=sys.stderr)
            return
    log.info(f"Removing {kernelspec}")
    shutil.rmtree(kernelspec)


def clone(kernelspec: _PathLike, to: _PathLike) -> Path:
    """Clone a kernelspec"""
    kernelspec = locate(kernelspec)
    to = Path(to)
    if str(to) == to.name:
        # default: in the same directory
        # TODO: optionally to --user dir or other
        to = kernelspec.parent / to
    else:
        # if it's a path, use it as one
        to = to.absolute()
    shutil.copytree(kernelspec, to)
    return to


def env_kernel(
    env: _PathLike,
    kind: str,
    kernel_name: str = "",
    install_data_dir: str | Path = "",
    install_prefix: str | Path = "",
):
    """Register a kernel for a conda environment or virtualenv

    install_data_dir is the entry on JUPYTER_PATH,
    whereas install_prefix is the typical install prefix.
    install_prefix="$prefix" is equivalent to
    install_data_dir="$prefix/share/jupyter"
    """

    env = Path(env)

    if kind == "venv":
        # todo: lookup venv by name
        if not env.exists():
            raise FileNotFoundError(
                f"venvs must be resolvable paths, did not find env at {env}"
            )
        python_cmd = [str(env / "bin" / "python3")]
        preamble = ["sh", "-c", '. "${ENV_PREFIX}/bin/activate" && exec "$0" "$@"']

    elif kind == "conda":
        # TODO: support invoking via [micro]mamba
        preamble = ["conda", "run", "--no-capture-output"]
        if env.exists():
            python_cmd = ["conda", "run", "-p", str(env), "python3"]
            preamble += ["--prefix"]
        else:
            python_cmd = ["conda", "run", "-n", str(env), "python3"]
            preamble += ["--name"]
        preamble += [str(env)]

    if install_data_dir and install_prefix:
        raise ValueError(
            "Specify only one of install_data_dir and install_prefix, got {install_data_dir=}, {install_prefix=}"
        )
    if not install_prefix and not install_data_dir:
        install_prefix = "sys-prefix"

    if install_prefix == "user":
        install_data_dir = Path(paths.jupyter_data_dir())
    elif install_prefix == "sys-prefix":
        install_data_dir = Path(sys.prefix) / "share" / "jupyter"
    elif install_prefix:
        install_prefix = Path(install_prefix)
        if not install_prefix.exists():
            raise FileNotFoundError(f"No such prefix: {install_prefix}")
        install_data_dir = Path(install_prefix) / "share" / "jupyter"
    else:
        install_data_dir = Path(install_data_dir)
        if not install_data_dir.exists():
            raise FileNotFoundError(f"No such dir: {install_data_dir}")

    kernels_dir = install_data_dir / "kernels"

    env_name = env.name
    if not kernel_name:
        kernel_name = f"{kind}-{env_name}"

    kernel_dest = kernels_dir / kernel_name
    if kernel_dest.exists():
        sys.exit(f"Kernel already exists at {kernel_dest}")

    log.info("Creating kernelspec for %s at %s", env_name, kernel_dest)

    with TemporaryDirectory() as td:
        envvars = os.environ.copy()
        jupyter_path = Path(td) / "share/jupyter"
        envvars["JUPYTER_PATH"] = str(jupyter_path)
        cmd = python_cmd + [
            "-m",
            "ipykernel",
            "install",
            "--prefix",
            str(td),
            "--name",
            kernel_name,
        ]
        log.debug("Calling %s", shlex.join(cmd))
        check_output(cmd, env=envvars)
        kernel_dir = jupyter_path / "kernels" / kernel_name
        log.debug("Copying %s -> %s", kernel_dir, kernel_dest)
        kernels_dir.mkdir(exist_ok=True, parents=True)
        shutil.copytree(kernel_dir, kernel_dest)

    # rewrite command to include env activation
    spec = _read_kernelspec(kernel_dest)
    if kind == "venv":
        envvars = spec.setdefault("env", {})
        envvars["ENV_PREFIX"] = str(env)
    # strip prefix off of executable
    spec["argv"][0] = Path(spec["argv"][0]).name
    # activate env with preamble
    spec["argv"] = preamble + spec["argv"]
    _write_kernelspec(kernel_dest, spec)
    return kernel_dest
