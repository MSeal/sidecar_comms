import pytest
from ipykernel.comm import Comm
from IPython.core.interactiveshell import InteractiveShell
from IPython.testing import tools


@pytest.fixture
def sample_comm() -> Comm:
    return Comm(target_name="test")


@pytest.fixture
def get_ipython() -> InteractiveShell:
    if InteractiveShell._instance:
        shell = InteractiveShell.instance()
    else:
        config = tools.default_config()
        config.TerminalInteractiveShell.simple_prompt = True
        shell = InteractiveShell.instance(config=config)

    # clear out any lingering variables between tests
    orig_variables = dict(shell.user_ns).copy()

    yield shell

    shell.user_ns = orig_variables
