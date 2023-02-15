import pytest
from ipykernel.comm import Comm
from IPython.core.interactiveshell import InteractiveShell

from sidecar_comms.shell import Shell


@pytest.fixture
def sample_comm() -> Comm:
    return Comm(target_name="test")


@pytest.fixture(autouse=True)
def tmp_ipython() -> InteractiveShell:
    test_shell = InteractiveShell.instance()
    Shell()._instance = test_shell
    yield test_shell
    Shell()._instance = None
