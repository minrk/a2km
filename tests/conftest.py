from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest import mock

import pytest


@pytest.fixture
def jupyter_dir(tmp_path: Path):
    jupyter_dir = tmp_path / "jupyter"
    (jupyter_dir / "kernels").mkdir(exist_ok=True, parents=True)
    return jupyter_dir


@pytest.fixture
def jupyter_dir_2(tmp_path: Path):
    jupyter_dir_2 = tmp_path / "jupyter2"
    (jupyter_dir_2 / "kernels").mkdir(exist_ok=True, parents=True)
    return jupyter_dir_2


_kernelspec = {
    "argv": [
        sys.executable,
        "-m",
        "some-kernel",
    ],
    "language": "python",
}


def make_kernelspec(name: str, kernels_dir: Path, extra_spec: dict | None = None):
    kernelspec = _kernelspec.copy()
    kernelspec["display_name"] = f"{name.title()} Kernel"
    if extra_spec:
        kernelspec.update(extra_spec)
    kernel_dir = kernels_dir / name
    kernel_dir.mkdir(exist_ok=True, parents=True)
    kernelspec_file = kernel_dir / "kernel.json"
    with kernelspec_file.open("w") as f:
        json.dump(kernelspec, f)


@pytest.fixture(autouse=True)
def kernelspecs(jupyter_dir: Path, jupyter_dir_2: Path):
    make_kernelspec("test-1", jupyter_dir / "kernels")
    make_kernelspec("test-2", jupyter_dir_2 / "kernels")
    make_kernelspec("in-both", jupyter_dir / "kernels", {"env": {"in": "1"}})
    make_kernelspec("in-both", jupyter_dir_2 / "kernels", {"env": {"in": "2"}})


@pytest.fixture
def kernelspec(jupyter_dir: Path, jupyter_env):
    return "test-1"


@pytest.fixture(autouse=True)
def jupyter_env(jupyter_dir: Path, jupyter_dir_2):
    # make sure we don't inherit the user env
    with (
        mock.patch.dict(
            os.environ,
            {
                "JUPYTER_PATH": f"{jupyter_dir}{os.pathsep}{jupyter_dir_2}",
                "JUPYTER_PLATFORM_DIRS": "1",
            },
        ),
        mock.patch("site.ENABLE_USER_SITE", False),
        mock.patch("jupyter_core.paths.SYSTEM_JUPYTER_PATH", []),
        mock.patch("jupyter_core.paths.ENV_JUPYTER_PATH", []),
    ):
        yield
