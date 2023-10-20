from ipykernel.comm import Comm

from sidecar_comms.inbound import handle_msg
from sidecar_comms.shell import get_ipython_shell


def test_rename(sample_comm: Comm):
    """
    Test that a rename_kernel_variable comm message is handled property
    by removing the old variable name from the user namespace and assigning
    the variable to the new variable name.
    """
    old_variable_name = "old_var"
    new_variable_name = "new_var"

    msg = {
        "old_name": old_variable_name,
        "new_name": new_variable_name,
        "msg": "rename_kernel_variable",
    }

    test_variable = "hello, world!"

    shell = get_ipython_shell()
    shell.user_ns[old_variable_name] = test_variable

    handle_msg(msg, sample_comm)

    assert new_variable_name in shell.user_ns.keys()
    assert shell.user_ns[new_variable_name] == test_variable
    assert old_variable_name not in shell.user_ns.keys()


def test_rename_delete(sample_comm: Comm):
    """Test that not providing a new variable name deletes the old variable."""
    old_variable_name = "old_var"
    new_variable_name = ""

    msg = {
        "old_name": old_variable_name,
        "new_name": new_variable_name,
        "msg": "rename_kernel_variable",
    }

    test_variable = "hello, world!"

    shell = get_ipython_shell()
    shell.user_ns[old_variable_name] = test_variable

    handle_msg(msg, sample_comm)

    assert new_variable_name not in shell.user_ns.keys()
    assert old_variable_name not in shell.user_ns.keys()
