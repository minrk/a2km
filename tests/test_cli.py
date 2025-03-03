import sys
from subprocess import check_output


def test_help():
    check_output([sys.executable, "-m", "a2km", "--help"])
