import json
from unittest import mock

import pytest

from a2km.operations import (
    _read_kernelspec,
    add_argv,
    add_env,
    clone,
    locate,
    remove,
    remove_argv,
    remove_env,
    rename,
    set,
    show,
)


def test_locate(jupyter_dir, jupyter_dir_2):
    result = locate("test-1")
    assert result == jupyter_dir / "kernels" / "test-1"
    result = locate("test-2")
    assert result == jupyter_dir_2 / "kernels" / "test-2"
    result = locate("in-both")
    assert result == jupyter_dir / "kernels" / "in-both"
    with pytest.raises(FileNotFoundError):
        locate("nosuchkernel")


def test_show(jupyter_dir, capsys):
    show("test-1")
    captured = capsys.readouterr()
    assert "Kernel: test-1 (Test-1 Kernel)" in captured.out
    assert f"  path: {jupyter_dir / 'kernels/test-1'}" in captured.out
    assert "argv:" in captured.out


def test_show_json(kernelspec, capsys):
    show(kernelspec, True)
    captured = capsys.readouterr()
    spec = _read_kernelspec(kernelspec)
    out_spec = json.loads(captured.out)
    assert spec == out_spec


def test_set(kernelspec):
    set(kernelspec, {"key": "value"})
    after = _read_kernelspec(kernelspec)
    assert after["key"] == "value"


def test_add_remove_env(kernelspec, jupyter_dir):
    before = _read_kernelspec(kernelspec)
    assert "env" not in before
    remove_env("test-1", "nosuch")
    add_env("test-1", {"key": "value"})
    after = _read_kernelspec(kernelspec)
    assert after["env"] == {"key": "value"}
    add_env("test-1", {"key2": "value2"})
    after = _read_kernelspec(kernelspec)
    assert after["env"] == {
        "key": "value",
        "key2": "value2",
    }
    add_env("test-1", {"key2": "value3"})
    after = _read_kernelspec(kernelspec)
    assert after["env"] == {
        "key": "value",
        "key2": "value3",
    }
    remove_env(kernelspec, ["key2"])
    after = _read_kernelspec(kernelspec)
    assert after["env"] == {"key": "value"}
    remove_env(kernelspec, ["key2", "key"])
    after = _read_kernelspec(kernelspec)
    assert after["env"] == {}


def test_rename(kernelspec):
    kernelspec_path = locate(kernelspec)
    before = _read_kernelspec(kernelspec)
    rename(kernelspec, "other")
    other_path = locate("other")
    after = _read_kernelspec("other")
    assert other_path.exists()
    assert not kernelspec_path.exists()
    assert other_path.parent == kernelspec_path.parent
    assert after == before


def test_add_remove_argv(kernelspec, jupyter_dir):
    before = _read_kernelspec(kernelspec)
    argv = before["argv"]
    add_argv(kernelspec, ["--debug"])
    after = _read_kernelspec(kernelspec)
    assert after["argv"] == argv + ["--debug"]
    add_argv(kernelspec, ["a", "b"])
    after = _read_kernelspec(kernelspec)
    assert after["argv"] == argv + ["--debug", "a", "b"]
    remove_argv(kernelspec, ["a"])
    after = _read_kernelspec(kernelspec)
    assert after["argv"] == argv + ["--debug", "b"]
    remove_argv(kernelspec, ["b", "--debug", "nosucharg"])
    after = _read_kernelspec(kernelspec)
    assert after["argv"] == argv
    remove_argv(kernelspec, ["nosucharg"])
    after = _read_kernelspec(kernelspec)
    assert after["argv"] == argv


def test_clone(kernelspec, tmp_path):
    cloned = clone(kernelspec, "clone")
    assert cloned.exists()
    assert cloned.parent == locate(kernelspec).parent
    before = _read_kernelspec(kernelspec)
    after = _read_kernelspec("clone")
    assert before == after
    # clone to path
    clone2_dest = tmp_path / "cloned"
    clone2 = clone(kernelspec, str(clone2_dest))
    assert clone2.exists()
    assert clone2 == clone2_dest
    before = _read_kernelspec(kernelspec)
    after = _read_kernelspec(clone2)
    assert before == after


def test_remove(kernelspec):
    remove(kernelspec, force=True)
    with pytest.raises(FileNotFoundError):
        locate(kernelspec)


def test_remove_prompt(kernelspec):
    with mock.patch("builtins.input", return_value="n") as mock_input:
        remove(kernelspec)
    assert mock_input.call_count == 1
    assert locate(kernelspec).exists()

    with mock.patch("builtins.input", return_value="Y") as mock_input:
        remove(kernelspec)
    assert mock_input.call_count == 1
    with pytest.raises(FileNotFoundError):
        locate(kernelspec)
