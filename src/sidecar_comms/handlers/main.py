from typing import Any, Optional

from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell


def get_kernel_variables():
    """Returns a list of variables in the kernel."""
    ipython = get_ipython()
    variables = dict(ipython.user_ns)
    variable_types = {name: str(type(value)) for name, value in variables.items()}
    return variable_types


def rename_kernel_variable(
    old_name: str,
    new_name: str,
    ipython_shell: Optional[InteractiveShell] = None,
) -> str:
    """Renames a variable in the kernel."""
    ipython = ipython_shell or get_ipython()
    try:
        if new_name:
            ipython.user_ns[new_name] = ipython.user_ns[old_name]
        del ipython.user_ns[old_name]
        return "success"
    except Exception as e:
        return str(e)


def set_kernel_variable(
    name: str,
    value: Any,
    ipython_shell: Optional[InteractiveShell] = None,
) -> str:
    """Sets a variable in the kernel."""
    ipython = ipython_shell or get_ipython()
    try:
        ipython.user_ns[name] = value
        return "success"
    except Exception as e:
        return str(e)
