import shutil
import sys
import tempfile
from pathlib import Path
from subprocess import check_call

import pytest
from jupyter_client.manager import KernelManager

from a2km.operations import env_kernel


@pytest.fixture(scope="session")
def conda_env():
    if not shutil.which("conda"):
        pytest.skip("Needs conda on $PATH")
    if not shutil.which("mamba"):
        pytest.skip("Needs mamba on $PATH")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        env_prefix = td / "conda_env"
        check_call(
            ["mamba", "create", "-y", "-p", str(env_prefix), "python=3.12", "ipykernel"]
        )

        yield env_prefix


@pytest.fixture(scope="session")
def venv():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        env_prefix = td / "venv"
        check_call([sys.executable, "-m", "venv", str(env_prefix)])
        check_call([str(env_prefix / "bin" / "pip"), "install", "ipykernel"])

        yield env_prefix


def check_kernel_prefix(kernel_name, prefix):
    km = KernelManager(kernel_name=kernel_name)
    km.start_kernel()
    kc = km.blocking_client()
    try:
        kc.wait_for_ready(timeout=60)
        msg_id = kc.execute("import sys", user_expressions={"prefix": "sys.prefix"})
        reply = kc.get_shell_msg(timeout=60)
        while reply.get("parent_header", {}).get("msg_id") != msg_id:
            reply = kc.get_shell_msg(timeout=60)
        assert reply["content"]["status"] == "ok"
        prefix_display = reply["content"]["user_expressions"]["prefix"]
        assert prefix_display["status"] == "ok"
        assert prefix_display.get("data", {}).get("text/plain") == repr(str(prefix))
    finally:
        kc.stop_channels()
        km.shutdown_kernel()


def test_conda_env_kernel(conda_env, jupyter_dir):
    kernelspec = env_kernel(conda_env, kind="conda", install_data_dir=jupyter_dir)
    check_kernel_prefix(kernelspec.name, conda_env)


def test_venv_kernel(venv, jupyter_dir):
    kernelspec = env_kernel(venv, kind="venv", install_data_dir=jupyter_dir)
    check_kernel_prefix(kernelspec.name, venv)
